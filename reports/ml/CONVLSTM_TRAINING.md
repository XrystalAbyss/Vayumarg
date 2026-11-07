# VAYUMARG Deep Learning Satellite Vision: ConvLSTM Spatiotemporal Forecaster Report

## 1. Executive Summary

This report documents the design, spatiotemporal sequence engineering, training dynamics, benchmark comparison, and operational limitations of the Convolutional Long Short-Term Memory (ConvLSTM) satellite forecasting model for Project VAYUMARG.

The objective is to capture physical convective motion, cloud canopy expansion, and eye-wall eyewall evolutions across chronological sequences of geostationary satellite frames to simultaneously predict:
1. Future tropical cyclone intensity (maximum sustained wind speed in knots).
2. Spatiotemporal frame reconstruction of the subsequent satellite infrared observation.

- **Model Architecture**: 2-Layer ConvLSTM ($32 \to 64$ hidden channels) with convolutional next-frame decoder and fully connected intensity regression head.
- **Model Parameters**: 360,578 trainable parameters.
- **Input Dimensions**: Sequence of $T = 3$ consecutive infrared satellite frames at $64 \times 64$ spatial resolution.
- **Dataset Sequences**: 2,425 chronological sequences constructed across 25 tropical cyclones.
- **Partitioning Strategy**: Strictly storm-disjoint splits (1,574 train sequences, 452 validation sequences, 399 held-out test sequences).
- **Execution Hardware**: NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM).
- **Training Time**: 182.08 seconds (12 epochs).
- **Held-Out Test Results**:
  - Intensity Forecast MAE: **17.20 knots** (RMSE: **23.72 knots**, Pearson $r$: **0.5571**).
  - Next-Frame Reconstruction MSE: **0.01084** (normalized pixel variance $\le 1.1\%$).
- **Benchmark Evaluation**: Compared directly against the operational Persistence Baseline and Single-Frame CNN.

---

## 2. Spatiotemporal Sequence Engineering

Satellite infrared observations exhibit high temporal autocorrelation over short intervals (1 to 3 hours). Effective sequence learning requires chronologically valid frame histories without mixing disparate cyclones or temporal discontinuities.

### 2.1 Sequence Generation Protocol
- Consecutive frames were grouped by unique `storm_id`.
- Frames were sorted chronologically using ISO-8601 acquisition timestamps.
- Sliding windows of length $T+1 = 4$ were generated:
  - Input: Past 3 consecutive frames ($\mathbf{X}_{t-2}, \mathbf{X}_{t-1}, \mathbf{X}_t$).
  - Targets: Future frame $\mathbf{X}_{t+1}$ and future wind intensity $y_{t+1}$.
- Spatial downsampling to $64 \times 64$ pixels with bilinear interpolation to allow efficient recurrent backpropagation through time (BPTT) within GPU memory constraints.

### 2.2 Sequence Manifest Distribution

| Partition | Unique Storms | Chronological Sequences ($T=3$) | Target Intensity Range |
| :--- | :--- | :--- | :--- |
| **Train Set** | 15 storms | 1,574 sequences | 20.0 kt to 150.0 kt |
| **Validation Set** | 5 storms | 452 sequences | 25.0 kt to 135.0 kt |
| **Held-Out Test Set** | 5 storms | 399 sequences | 20.0 kt to 125.0 kt |
| **Total** | **25 storms** | **2,425 sequences** | Clean temporal sequences |

- Sequence Manifest: `data/processed/satellite/nasa_cyclone/sequences_manifest.json`

---

## 3. ConvLSTM Architecture & Dual-Objective Formulation

Unlike standard LSTMs that flatten spatial features into 1D vectors (destroying cyclone spiral rainband geometry), ConvLSTM replaces matrix multiplications within recurrent cell gates with 2D convolution operators.

### 3.1 Recurrent Gating Mechanism
For each time step $t \in \{1, 2, 3\}$:
$$\mathbf{i}_t = \sigma(\mathbf{W}_{xi} * \mathbf{X}_t + \mathbf{W}_{hi} * \mathbf{H}_{t-1} + \mathbf{b}_i)$$
$$\mathbf{f}_t = \sigma(\mathbf{W}_{xf} * \mathbf{X}_t + \mathbf{W}_{hf} * \mathbf{H}_{t-1} + \mathbf{b}_f)$$
$$\mathbf{c}_t = \mathbf{f}_t \odot \mathbf{c}_{t-1} + \mathbf{i}_t \odot \tanh(\mathbf{W}_{xc} * \mathbf{X}_t + \mathbf{W}_{hc} * \mathbf{H}_{t-1} + \mathbf{b}_c)$$
$$\mathbf{o}_t = \sigma(\mathbf{W}_{xo} * \mathbf{X}_t + \mathbf{W}_{ho} * \mathbf{H}_{t-1} + \mathbf{b}_o)$$
$$\mathbf{H}_t = \mathbf{o}_t \odot \tanh(\mathbf{c}_t)$$

where $*$ denotes 2D spatial convolution and $\odot$ denotes the Hadamard elementwise product.

### 3.2 Dual Head Architecture
- **Layer 1**: `ConvLSTMCell(in_channels=1, hidden_channels=32, kernel_size=3)`
- **Layer 2**: `ConvLSTMCell(in_channels=32, hidden_channels=64, kernel_size=3)`
- **Intensity Head**: `AdaptiveAvgPool2d((1, 1))` on final state $\mathbf{H}_T \to \text{Dropout}(0.25) \to \text{Linear}(64, 1)$.
- **Reconstruction Head**: Convolutional decoder projecting $\mathbf{H}_T$ from 64 channels to 1 channel via `Conv2d(64, 32, 3, padding=1) -> ReLU -> Conv2d(32, 1, 1) -> Sigmoid`.

### 3.3 Loss Function
$$\mathcal{L}_{\text{total}} = \text{SmoothL1}(v_{\text{pred}}, v_{\text{target}}) + 25.0 \cdot \text{MSE}(\hat{\mathbf{X}}_{t+1}, \mathbf{X}_{t+1})$$

The scaling factor of $25.0$ balances the magnitude of normalized pixel MSE ($\sim 0.01$) against knot-scale Huber residuals ($\sim 10.0$).

---

## 4. Training Progression

Training was executed over 12 epochs with AdamW, mixed precision autocast, and Cosine Annealing learning rate scheduling.

```
Epoch [01/12] | Train Loss: 47.950 | Val MAE: 50.54 kt | Val RMSE: 59.58 kt | Frame MSE: 0.02535 | r: -0.5334
Epoch [02/12] | Train Loss: 34.244 | Val MAE: 27.87 kt | Val RMSE: 37.56 kt | Frame MSE: 0.01920 | r: -0.4719
Epoch [03/12] | Train Loss: 18.941 | Val MAE: 22.12 kt | Val RMSE: 29.82 kt | Frame MSE: 0.01420 | r:  0.5664
Epoch [04/12] | Train Loss: 16.958 | Val MAE: 19.02 kt | Val RMSE: 26.19 kt | Frame MSE: 0.01429 | r:  0.6128
Epoch [05/12] | Train Loss: 16.093 | Val MAE: 18.32 kt | Val RMSE: 24.27 kt | Frame MSE: 0.01191 | r:  0.6599
Epoch [06/12] | Train Loss: 15.409 | Val MAE: 17.31 kt | Val RMSE: 22.51 kt | Frame MSE: 0.01161 | r:  0.6867
Epoch [07/12] | Train Loss: 14.657 | Val MAE: 20.62 kt | Val RMSE: 29.45 kt | Frame MSE: 0.01159 | r:  0.6719
Epoch [08/12] | Train Loss: 14.411 | Val MAE: 17.67 kt | Val RMSE: 23.42 kt | Frame MSE: 0.01156 | r:  0.6702
Epoch [09/12] | Train Loss: 14.378 | Val MAE: 19.83 kt | Val RMSE: 23.71 kt | Frame MSE: 0.01144 | r:  0.6658
Epoch [10/12] | Train Loss: 14.080 | Val MAE: 17.16 kt | Val RMSE: 23.47 kt | Frame MSE: 0.01138 | r:  0.6675
Epoch [11/12] | Train Loss: 13.642 | Val MAE: 17.57 kt | Val RMSE: 24.98 kt | Frame MSE: 0.01136 | r:  0.6608
Epoch [12/12] | Train Loss: 13.570 | Val MAE: 16.70 kt | Val RMSE: 23.68 kt | Frame MSE: 0.01134 | r:  0.6876
```

- Best validation checkpoint: **Epoch 12** (Validation MAE = **16.70 kt**, Frame MSE = **0.01134**, $r = 0.6876$).
- Saved checkpoint path: `models/vayumarg/vision/satellite_convlstm_best.pt` (1.4 MB).

---

## 5. Comparative Benchmark Analysis

A critical principle in operational meteorology is benchmarking complex deep neural networks against simpler baseline heuristics. Here, ConvLSTM is benchmarked directly against the **Persistence Baseline** ($\hat{y}_{t+1} = y_t$) and the **ResNet-18 Single-Frame CNN**.

| Model / Baseline | Input Modality | Train MAE (kt) | Val MAE (kt) | Test MAE (kt) | Test RMSE (kt) | Pearson $r$ | Next-Frame MSE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Persistence Baseline** | Scalar $y_t$ | **1.41 kt** | **1.56 kt** | **1.90 kt** | **3.23 kt** | 0.992 | N/A |
| **Single-Frame CNN (ResNet-18)** | 1 IR Frame ($224 \times 224$) | 5.77 kt | 8.61 kt | 10.00 kt | 14.26 kt | 0.864 | N/A |
| **ConvLSTM Forecaster** | 3 IR Frames ($64 \times 64$) | 13.93 kt | 16.70 kt | 17.20 kt | 23.72 kt | 0.557 | **0.01084** |

### 5.1 Scientific Interpretation of the Benchmarks
1. **The Persistence Dominance Phenomenon**: Over short time steps ($\Delta t \approx 1\text{ to }3$ hours), tropical cyclone physical intensity changes slowly ($\sim 1\text{ to }2$ kt/hour except during rapid intensification). Consequently, a naive persistence model that simply predicts the previous observation achieves an extremely low MAE of **1.90 kt**.
2. **ConvLSTM vs Single-Frame CNN**: The single-frame ResNet-18 performs significantly better on absolute intensity estimation (10.00 kt vs 17.20 kt). This occurs because ResNet-18 evaluates higher spatial resolution ($224 \times 224$ vs $64 \times 64$), resolving finer cloud convective features such as the central dense overcast (CDO) boundary and eye definition.
3. **Spatiotemporal Visual Dynamics**: While ConvLSTM exhibits higher intensity regression variance, it successfully learns cloud advection and convective growth patterns, achieving a very low next-frame reconstruction MSE of **0.01084** on completely unseen storms.

---

## 6. Integration API Contract

Both models are served via `vayumarg.ml.vision.inference.SatelliteInferenceEngine`.

### 6.1 Programmatic Invocation Example

```python
from vayumarg.ml.vision.inference import SatelliteInferenceEngine
from PIL import Image

# Initialize engine (loads checkpoints to GPU automatically)
engine = SatelliteInferenceEngine()

# 1. Single-Frame ResNet-18 Intensity Prediction
image = Image.open("data/raw/satellite/nasa_cyclone/images/xtd_001.png")
result = engine.predict_image(image)
print(f"Predicted Wind: {result['predicted_max_sustained_wind_knots']} kt")
print(f"Category: {result['predicted_category_label']}")
print(f"Latency: {result['inference_latency_ms']} ms")

# 2. ConvLSTM Spatiotemporal Sequence Forecast
past_frames = [
    Image.open("data/raw/satellite/nasa_cyclone/images/xtd_001.png"),
    Image.open("data/raw/satellite/nasa_cyclone/images/xtd_002.png"),
    Image.open("data/raw/satellite/nasa_cyclone/images/xtd_003.png"),
]
forecast = engine.predict_sequence(past_frames, lead_time_hours=3.0)
print(f"Forecast Future Wind: {forecast['predicted_future_wind_kt']} kt")

# 3. Authentic INSAT-3DR/3DS Zero-Shot Transfer
insat_eval = engine.evaluate_insat_crop("BIPARJOY", channel="TIR-1")
print(f"BIPARJOY Zero-Shot Wind: {insat_eval['predicted_max_sustained_wind_knots']} kt")
```

---

## 7. Conclusions and Operational Recommendations

1. **Production Deployment Recommendation**: For real-time cyclone intensity classification and wind speed estimation, deploy the **ResNet-18 Single-Frame CNN** as the primary vision estimator. Its 10.00 kt held-out error and sub-5 ms latency provide high operational utility.
2. **Temporal Guidance**: The ConvLSTM should be utilized primarily for next-frame cloud advection extrapolation and visual sequence sanity verification rather than standalone intensity prediction.
3. **INSAT Multi-Frame Sequences**: To extend ConvLSTM to operational INSAT imagery, multi-temporal sequential granules from MOSDAC must be acquired at consistent 30-minute intervals and co-registered prior to sequence training.

