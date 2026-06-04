---
name: sota-kinematic-skeleton
description: Master protocol for high-fidelity MuJoCo/MyoSuite gait restoration and CPG orchestration.
---
# SOTA Kinematic Skeleton Protocol

## 1. Cinematic Environment & Physics
- **Floor**: Expand mjGEOM_PLANE to [100, 100, 1]. HD 1920x1080 resolution.
- **Anatomy**: geomgroup[1]=1 (Skeleton), geomgroup[3]=1 (Muscles). mjVIS_TRANSPARENT=1.
- **Camera**: Anchor cam.lookat[0] to qpos[0]. lookat[2]=0.5. Distance 1.6m. Azimuth 105, Elevation -12.

## 2. Matsuoka CPG Orchestration
- **Constants**: w=2.0, b=2.5, tau=0.12, tau_a=0.3.
- **State**: u=[0.1, 0.0], v=[0.0, 0.0].
- **Drive**: 1.8 (Active), 0.0 (Freeze).

## 3. Joint-to-Oscillator Mapping (myoSarcLegWalk-v0)
- **Right Leg**: Hip(q7)=0.35*osc, Knee(q12)=0.7*max(0,osc), Ankle(q15)=-0.1*osc.
- **Left Leg**: Hip(q21)=-0.35*osc, Knee(q26)=0.7*max(0,-osc), Ankle(q29)=0.1*osc.
- **COM Rhythm**: q2 = 0.94 + 0.015*abs(osc).
- **Speed**: Forward progress root_x += dt * 0.45 * drive * abs(osc).

## 4. Execution Timing
- **10:1 Protocol**: Run 3-4 physics steps (dt=0.01) per render frame (30 FPS).
- **Post-Process**: Sharpen with ImageEnhance.Sharpness(img).enhance(1.5).

## Overview & Scope
Cinematic gait restoration in MuJoCo.

## Execution Protocol
Follow the physics and mapping protocol for bit-perfect movement.

## Requirements & Dependencies
Requires MuJoCo and MyoSuite.

## Few-Shot Examples
See skeletal visualization scripts in the MuJoCo simulation environment.


