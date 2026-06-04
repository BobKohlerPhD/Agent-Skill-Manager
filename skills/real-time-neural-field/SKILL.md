---
name: real-time-neural-field
description: A generalized framework for creating vibrant, "Always-Alive" neural connectivity animations for EEG, fMRI, or Connectomics.
---
# Real-Time Neural Field Visualizer

## 1. The "Always-Alive" Normalization Framework
To prevent "flickering" or "blackouts" in real-time brain data, you MUST use a stabilized dynamic range:
- **Dynamic Percentiles**: Every frame, calculate `p99.9` (vmax) and `p0.1` (vmin) of the active neural field.
- **EMA Stabilization**: Apply an Exponential Moving Average (alpha=0.15) to these limits: `v_stab = (0.15 * v_current) + (0.85 * v_prev)`. This ensures the color intensity "breathes" rather than flashes.

## 2. Spatial Mapping & Weighting
- **Gaussian Kernel**: Map sensor data to cortical meshes using `weights = exp(-dist**2 / (2 * sigma**2))`. For high-fidelity EEG, use `sigma=0.12`.
- **Mesh Subset**: Stride your surface mesh (e.g., fsLR) by `[::15]` to maintain real-time responsiveness without losing topographic detail.

## 3. Connectivity Aesthetics (Broadband Flow)
- **The Electric Graph**: Connect nodes with streamlines. Line `alpha` and `linewidth` must be proportional to the average activation of the connected nodes.
- **Colors**: Use high-contrast pairings (e.g., `Magma` heatmap with `Cyan (#00f2ff)` electric streamlines).
- **Dual-Layer Halo**: Apply a scatter layer with `s=350` (Primary) and `s=600` (Glow/Halo) at `alpha=0.3` to simulate cortical depth.

## 4. Clinical State Indicators
- **The Halo Alert**: Implement a state-aware boundary. When a biomarker threshold is hit, shift the boundary halo to high-intensity Red (`#ff0000`) with `alpha=0.5` and `linewidth=10`.

## Trigger Criteria & Bounds
*   **Use Cases**: General framework for real-time brain data viz (EEG/fMRI).
*   **Anti-Patterns (Do NOT Use)**: Do not use for static image plots or offline reports that do not require real-time processing loops.

## Execution Protocol
*   **Pre-conditions**: Surface mesh and sensor coordinate files must be parsed and loaded.
*   **Step-by-Step Instructions**:
    1. Parse incoming brain sensor streams.
    2. Apply EMA limits and Gaussian weights to ensure "Always-Alive" fluidity.
*   **Error Handling**: If a frame times out, log a dropped-frame warning and reuse the previous frame EMA state.

## Requirements & Environment
*   **System Dependencies**: Graphic drivers supporting hardware acceleration.
*   **Runtime Packages**: Nilearn, Matplotlib, PIL.
*   **API Keys / Environment Variables**: None.

## Few-Shot Cognitive Examples
### Example 1: Streamline Flow Initialization
*   **Input**:
    ```json
    { "frame_rate": 30, "sensors": 64 }
    ```
*   **Agent Thought (CoT)**: I need to set up a real-time brain connectivity field with stabilized dynamic range using Nilearn and Matplotlib.
*   **Action**: Run Python script initializing dynamic limits.
*   **Output**:
    ```json
    { "status": "active", "v_stabilized": 0.15 }
    ```


