"""PyTorch Neural Network Architectures for Vayumarg Track and Wind Forecasting.

Implements VayumargTrackGRU, a recurrent spatiotemporal architecture for
cyclone trajectory and multi-horizon displacement prediction (+6h, +12h, +24h).
"""

import torch
import torch.nn as nn


class VayumargTrackGRU(nn.Module):
    """Bidirectional/recurrent gated recurrent unit for cyclone track & wind forecasting.

    Inputs:
        sequence of historical observation features of shape [batch, seq_len, in_features]

    Outputs:
        dictionary containing:
        - 'displacement_km': predicted (dx, dy) in km for horizons [+6h, +12h, +24h], shape [batch, 3, 2]
        - 'future_wind_kt': predicted wind speed in kt for horizons [+6h, +12h, +24h], shape [batch, 3]
    """

    def __init__(
        self,
        in_features: int = 10,
        hidden_size: int = 96,
        num_layers: int = 2,
        dropout: float = 0.15,
        horizons: tuple[int, ...] = (6, 12, 24),
    ):
        super().__init__()
        self.in_features = in_features
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.horizons = horizons
        self.num_horizons = len(horizons)

        # Feature normalization / input projection
        self.input_layer = nn.Sequential(
            nn.Linear(in_features, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Recurrent core
        self.gru = nn.GRU(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Self-attention / pooling over sequence
        self.temporal_attn = nn.Sequential(
            nn.Linear(hidden_size, 1),
            nn.Softmax(dim=1),
        )

        # Multi-horizon trajectory displacement head (dx, dy in km per horizon)
        self.displacement_head = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, self.num_horizons * 2),
        )

        # Multi-horizon wind intensity head (knots per horizon)
        self.wind_head = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, self.num_horizons),
        )

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        # x shape: [B, T, in_features]
        b = x.size(0)

        # 1. Project input features
        h_proj = self.input_layer(x)  # [B, T, H]

        # 2. Recurrent pass
        gru_out, _ = self.gru(h_proj)  # [B, T, H]

        # 3. Last hidden state + temporal attention context
        last_hidden = gru_out[:, -1, :]  # [B, H]
        attn_weights = self.temporal_attn(gru_out)  # [B, T, 1]
        context = torch.sum(attn_weights * gru_out, dim=1)  # [B, H]

        combined = torch.cat([last_hidden, context], dim=1)  # [B, 2*H]

        # 4. Predict displacement & wind
        disp_flat = self.displacement_head(combined)  # [B, num_horizons * 2]
        displacement = disp_flat.view(b, self.num_horizons, 2)  # [B, 3, 2] (dx, dy in km)

        wind = self.wind_head(combined)  # [B, 3] (wind in kt)

        return {
            "displacement_km": displacement,
            "future_wind_kt": wind,
        }


class VayumargHybridTrackModel(nn.Module):
    """Hybrid Recurrent Forecaster: Geodesic Extrapolation + Bounded Neural Residual.

    Prediction(t+h) = Geodesic(t+h) + tanh(Residual_head) * Max_Correction(h)
    """

    def __init__(
        self,
        in_features: int = 10,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.15,
        horizons: tuple[int, ...] = (6, 12, 24),
    ):
        super().__init__()
        self.horizons = horizons
        self.gru = nn.GRU(
            input_size=in_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.attention = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.Tanh(),
            nn.Linear(32, 1),
        )

        # Bounded residual limits (km): 6h (+/-45 km), 12h (+/-90 km), 24h (+/-200 km)
        self.max_corrections = nn.Parameter(
            torch.tensor([[45.0, 45.0], [90.0, 90.0], [200.0, 200.0]], dtype=torch.float32),
            requires_grad=False,
        )

        self.residual_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, 32),
                nn.ReLU(),
                nn.Linear(32, 2),
            )
            for _ in horizons
        ])

        self.wind_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, len(horizons)),
        )

        for head in self.residual_heads:
            nn.init.uniform_(head[-1].weight, -0.01, 0.01)
            nn.init.zeros_(head[-1].bias)

    def forward(
        self, x: torch.Tensor, baseline_geodesic_disp: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        out, _ = self.gru(x)
        attn_weights = torch.softmax(self.attention(out), dim=1)
        ctx = torch.sum(out * attn_weights, dim=1)

        residuals = []
        for i, head in enumerate(self.residual_heads):
            raw = head(ctx)
            bounded_residual = torch.tanh(raw) * self.max_corrections[i]
            residuals.append(bounded_residual.unsqueeze(1))

        residuals_cat = torch.cat(residuals, dim=1)
        final_disp = baseline_geodesic_disp + residuals_cat
        future_wind = self.wind_head(ctx)

        return {
            "final_disp_km": final_disp,
            "residual_km": residuals_cat,
            "future_wind_kt": future_wind,
        }
