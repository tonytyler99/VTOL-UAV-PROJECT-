# PID Tuning Guide

This guide explains how to tune the PID controller for optimal tracking performance.

## Parameters

The tracking system uses a **PD controller** (Proportional-Derivative) for yaw control:

```
speed_x = Kp * error + Kd * (error - prev_error)
```

| Parameter | Config Key | Effect |
|-----------|-----------|--------|
| **Kp** (Proportional) | `PID_KP` | Higher = faster response, but may overshoot |
| **Kd** (Derivative) | `PID_KD` | Higher = more damping, reduces oscillation |

## Tuning Steps

1. **Start with low values:** Set `PID_KP = 0.2` and `PID_KD = 0.1`
2. **Increase Kp** until the drone turns toward the target quickly but starts oscillating
3. **Increase Kd** to dampen the oscillation
4. **Repeat** until tracking is smooth and responsive

## Distance Control

Forward/backward movement is controlled by face area thresholds:

- `FB_RANGE_MIN = 3000` — face area below this triggers forward movement
- `FB_RANGE_MAX = 5000` — face area above this triggers backward movement
- `FB_SPEED = 25` — movement speed in cm/s

If the drone gets too close or too far, adjust these thresholds based on your environment and the target's typical distance.

## Common Issues

| Symptom | Fix |
|---------|-----|
| Drone oscillates left/right | Decrease `PID_KP` or increase `PID_KD` |
| Drone responds too slowly | Increase `PID_KP` |
| Drone overshoots target | Increase `PID_KD` |
| Drone too close/far | Adjust `FB_RANGE_MIN` / `FB_RANGE_MAX` |
