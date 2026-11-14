# Temporal Stability Observation

This directory contains supplementary observations from a recorded screen video of the YOLOv8s–STM32 lemon-sorting prototype.

## Data Source

- Source: deployment-screen recording containing rendered detection boxes, labels, stability counters, and transmission notifications.
- Recording frame rate: 30 FPS.
- Runtime configuration: YOLOv8s, confidence 0.60, image size 320, three consecutive class confirmations, and 0.65-second transmission cooldown.
- Inspection: manually selected screen observations, generally sampled at 0.1-second intervals.

## Observed Sequences

| Segment | Prediction | Stability count at visible SENT notification |
|---|---|---:|
| 03 | Bad | 5 |
| 05 | Bad | 10 |
| 06 | Good, after transient class changes | 9 |

## Limitations

The footage contains rendered detections rather than raw inference logs. Screen-recording frames must not be interpreted as individual YOLO inference events.

The observations demonstrate the implemented stability-counter behavior but do not establish comparative accuracy or latency for confirmation thresholds of 1, 2, 3, and 5, tracking ON/OFF, or different cooldown intervals.

No new physical sorting trials were conducted for these observations.
