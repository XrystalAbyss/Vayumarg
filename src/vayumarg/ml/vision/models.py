"""Deep Learning Satellite Vision Models for VAYUMARG.

Implements:
1. `CycloneCNNRegressor`: Deep Convolutional Intensity Regression Network for single-channel
   satellite infrared imagery, predicting maximum sustained surface wind speed (knots).
2. `CycloneConvLSTM`: Spatiotemporal Recurrent Convolutional Network for chronological
   satellite image sequences, forecasting future wind intensity and next-frame imagery.
"""

import torch
import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18


class CycloneCNNRegressor(nn.Module):
    """Deep CNN for tropical cyclone intensity estimation from single-channel infrared satellite imagery.

    Architecture:
    - Modified ResNet-18 backbone with single-channel IR input layer (366x366 or 128x128).
    - Global Adaptive Average Pooling.
    - Multi-layer perceptron regression head with dropout regularization.
    - Auxiliary meteorological category head (0: Depression, 1: Deep Depression/TS,
      2: Cyclonic Storm, 3: Severe Cyclonic Storm, 4: Very Severe, 5: Extremely Severe / Super Cyclone).
    """

    def __init__(self, pretrained_backbone: bool = True, dropout: float = 0.2):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained_backbone else None
        base = resnet18(weights=weights)

        # Replace first conv layer for single-channel infrared input (IR 11 µm)
        self.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        if pretrained_backbone and base.conv1.weight is not None:
            # Average RGB pretrained weights across color channels for single IR channel
            with torch.no_grad():
                self.conv1.weight.copy_(base.conv1.weight.mean(dim=1, keepdim=True))

        self.bn1 = base.bn1
        self.relu = base.relu
        self.maxpool = base.maxpool

        self.layer1 = base.layer1
        self.layer2 = base.layer2
        self.layer3 = base.layer3
        self.layer4 = base.layer4

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))

        # Primary Wind Intensity Regression Head (knots)
        self.regressor = nn.Sequential(
            nn.Linear(512, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(128, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 1),
        )

        # Auxiliary Meteorological Category Head (6 classes)
        self.classifier = nn.Sequential(
            nn.Linear(512, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(64, 6),
        )

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract 512-dimensional spatiotemporal feature representation."""
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return x

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Args:
            x: Input satellite tensor of shape (B, 1, H, W).

        Returns:
            wind_speed: Predicted maximum sustained wind speed in knots of shape (B, 1).
            category_logits: Auxiliary category logits of shape (B, 6).
        """
        feats = self.extract_features(x)
        wind_speed = self.regressor(feats)
        category_logits = self.classifier(feats)
        return wind_speed, category_logits


class ConvLSTMCell(nn.Module):
    """2D Convolutional LSTM memory cell for spatiotemporal representation learning."""

    def __init__(self, in_channels: int, hidden_channels: int, kernel_size: int = 3):
        super().__init__()
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.padding = kernel_size // 2

        # Combined convolution for all 4 gates (input, forget, cell candidate, output)
        self.conv = nn.Conv2d(
            in_channels=in_channels + hidden_channels,
            out_channels=4 * hidden_channels,
            kernel_size=kernel_size,
            padding=self.padding,
            bias=True,
        )

    def forward(
        self, x: torch.Tensor, state: tuple[torch.Tensor, torch.Tensor] | None = None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Step forward.

        Args:
            x: Input frame of shape (B, in_channels, H, W).
            state: Tuple (h_prev, c_prev) each of shape (B, hidden_channels, H, W).

        Returns:
            Tuple (h_next, c_next).
        """
        batch_size, _, height, width = x.size()

        if state is None:
            h_prev = torch.zeros(
                batch_size, self.hidden_channels, height, width, device=x.device, dtype=x.dtype
            )
            c_prev = torch.zeros(
                batch_size, self.hidden_channels, height, width, device=x.device, dtype=x.dtype
            )
        else:
            h_prev, c_prev = state

        combined = torch.cat([x, h_prev], dim=1)
        gates = self.conv(combined)

        i_gate, f_gate, c_cand, o_gate = torch.split(gates, self.hidden_channels, dim=1)

        i = torch.sigmoid(i_gate)
        f = torch.sigmoid(f_gate)
        c = f * c_prev + i * torch.tanh(c_cand)
        o = torch.sigmoid(o_gate)
        h = o * torch.tanh(c)

        return h, c


class CycloneConvLSTM(nn.Module):
    """Spatiotemporal ConvLSTM network for sequential cyclone intensity forecasting and frame extrapolation.

    Processes sequences of consecutive satellite frames (e.g., T=3 past observations)
    and predicts future intensity (wind speed in knots) and optionally next-frame satellite imagery.
    """

    def __init__(
        self,
        in_channels: int = 1,
        hidden_dims: tuple[int, ...] = (32, 64),
        kernel_size: int = 3,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.hidden_dims = hidden_dims
        self.num_layers = len(hidden_dims)

        cells = []
        for i in range(self.num_layers):
            cur_in = in_channels if i == 0 else hidden_dims[i - 1]
            cells.append(ConvLSTMCell(cur_in, hidden_dims[i], kernel_size=kernel_size))
        self.cells = nn.ModuleList(cells)

        # Spatial dimensionality reduction before pooling
        self.head_conv = nn.Sequential(
            nn.Conv2d(hidden_dims[-1], 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        # Intensity Regression Head
        self.intensity_regressor = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(64, 1),
        )

        # Next-Frame Reconstruction Head (Generates future IR patch of shape (B, 1, H, W))
        self.frame_decoder = nn.Sequential(
            nn.Conv2d(hidden_dims[-1], 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, in_channels, kernel_size=1),
            nn.Sigmoid(),  # Normalized [0, 1] reflectance/Kelvin scale
        )

    def forward(self, seq: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass over sequence of past frames.

        Args:
            seq: Tensor of shape (B, T, C, H, W) where T is the sequence length.

        Returns:
            future_wind: Predicted wind speed at t+1 of shape (B, 1).
            next_frame: Predicted next satellite observation of shape (B, C, H, W).
        """
        batch_size, seq_len, _, height, width = seq.size()

        # Initialize hidden states
        states = [None] * self.num_layers

        for t in range(seq_len):
            x_t = seq[:, t, :, :, :]
            for layer_idx, cell in enumerate(self.cells):
                h_t, c_t = cell(x_t, states[layer_idx])
                states[layer_idx] = (h_t, c_t)
                x_t = h_t  # Input to next ConvLSTM layer

        # Final hidden state from top layer
        final_h = states[-1][0]  # Shape: (B, hidden_dims[-1], H, W)

        # Intensity regression
        pooled = self.head_conv(final_h)
        pooled = torch.flatten(pooled, 1)
        future_wind = self.intensity_regressor(pooled)

        # Next-frame visual prediction
        next_frame = self.frame_decoder(final_h)

        return future_wind, next_frame
