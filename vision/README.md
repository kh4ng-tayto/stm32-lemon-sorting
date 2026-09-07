# YOLOv8s Real-Time Vision Application

Python application for real-time lemon detection and quality classification using a **USB webcam** and **YOLOv8s**.

The application classifies lemons as `Good` or `Bad` and sends the classification result to the STM32F103C6T6 through UART.

---

## Main Functions

The vision application performs:

- USB webcam capture
- YOLOv8s inference
- Good / Bad classification
- Object tracking
- Stable-class verification
- Sorting-line detection
- Duplicate-send prevention
- UART communication with STM32
- STM32 queue/status monitoring
- Real-time FPS display

---

## Vision Processing Flow

```text
USB Webcam
     │
     ▼
OpenCV Capture
     │
     ▼
YOLOv8s
     │
     ▼
Object Detection
     │
     ▼
Good / Bad Prediction
     │
     ▼
Object Tracking
     │
     ▼
Stable Classification
     │
     ▼
Sorting Line Detection
     │
     ▼
UART Condition Check
     │
     ▼
Send '1' / '2'
     │
     ▼
STM32F103C6T6
```

---

## Model Configuration

```text
Model                : YOLOv8s
Weights              : best.pt
Classes              : Good / Bad
Inference Image Size : 320
Confidence Threshold : 0.60
```

For each valid detection, the model provides:

```text
Bounding Box
Class
Confidence Score
```

Detections with a confidence score below `0.60` are ignored.

---

## Object Tracking

Each detected lemon is associated with a:

```text
track_id
```

Tracking allows the program to associate the same lemon across consecutive video frames.

This is important because a lemon can appear in many frames while moving through the camera view.

The `track_id` is also used to prevent the same lemon from generating multiple UART classification commands.

---

## Stable Classification

A single YOLOv8 prediction is not immediately transmitted to STM32.

For each tracked object, the predicted class must remain consistent for at least:

```text
3 matched frames
```

The program uses a stability counter:

```text
stable_frames
```

If the same class continues to be predicted, the counter increases.

If the predicted class changes, the stability counter is reset.

This reduces the possibility of transmitting a classification result based on a temporary prediction.

---

## Sorting Line

The program uses a horizontal sorting line at:

```text
y = 160
```

with an activation range of:

```text
±18 pixels
```

The center point of the detected bounding box is used to determine whether a lemon has reached or crossed the sorting line.

```text
Camera Frame

y = 0
│
│
│
├────────────────── y = 160
│                   Sorting Line
│
│       Lemon
│         ●
│    Bounding Box
│       Center
│
▼
Direction of Movement
```

When an object reaches or crosses the sorting line, its `track_id` is remembered so that the event is not lost if another sending condition is temporarily unavailable.

---

## UART Sending Conditions

A classification result is transmitted only when all required conditions are satisfied.

```text
Object Detected
       │
       ▼
Confidence >= 0.60
       │
       ▼
Valid Track ID
       │
       ▼
Class Is Stable
       │
       ▼
Sorting Line Crossed
       │
       ▼
Track ID Has Not Been Sent
       │
       ▼
UART Cooldown Satisfied
       │
       ▼
STM32 Queue Ready
       │
       ▼
Send UART Command
```

The minimum interval between classification commands is:

```text
0.65 seconds
```

---

## UART Commands

Classification results are transmitted as single ASCII characters.

| Class | UART Command |
|---|---|
| Good | `1` |
| Bad | `2` |

For a Good lemon:

```text
YOLOv8s
   │
   ▼
 Good
   │
   ▼
Send '1'
   │
   ▼
 STM32
```

For a Bad lemon:

```text
YOLOv8s
   │
   ▼
  Bad
   │
   ▼
Send '2'
   │
   ▼
 STM32
```

After successful transmission, the object's `track_id` is added to the set of already-sent IDs.

This prevents the same lemon from generating another classification command in later frames.

---

## Communication with STM32

The Python application communicates with STM32 using a CH340 USB-to-UART converter.

```text
Python Application
       │
       │ Serial Port
       ▼
      CH340
       │
       │ UART
       ▼
STM32F103C6T6
```

UART configuration:

```text
Baud Rate : 9600 bps
Data Bits : 8
Parity    : None
Stop Bits : 1
```

The Python application also reads ACK and status information returned by STM32 to determine the current controller and queue state.

---

## Real-Time Parameters

| Parameter | Value |
|---|---:|
| Inference Image Size | 320 |
| Confidence Threshold | 0.60 |
| Stable Frames | 3 |
| Sorting Line | `y = 160` |
| Trigger Range | ±18 pixels |
| UART Cooldown | 0.65 s |

During system testing, the observed display speed was approximately:

```text
30.2 - 31.4 FPS
```

---

## Requirements

Main Python packages:

```text
ultralytics
opencv-python
pyserial
numpy
```

Install the dependencies from the repository root:

```bash
pip install -r requirements.txt
```

---

## Files

```text
vision/
├── README.md
├── best.pt
└── lemon_sorting_vertical_optimized.py
```

### `best.pt`

The best YOLOv8s weights obtained during model training.

### `lemon_sorting_vertical_optimized.py`

Main real-time application responsible for:

```text
Webcam Capture
      │
      ▼
YOLOv8s Inference
      │
      ▼
Object Tracking
      │
      ▼
Stable Classification
      │
      ▼
Sorting Line
      │
      ▼
UART Transmission
      │
      ▼
STM32
```

---

## Running the Application

Before running the program:

1. Connect the USB webcam.
2. Connect the STM32 through the CH340 USB-to-UART converter.
3. Check the COM port assigned to the CH340.
4. Make sure `best.pt` is available in the expected path.
5. Install the required Python packages.

Run the application:

```bash
python lemon_sorting_vertical_optimized.py
```

---

## System Integration

The vision application determines the lemon class and the correct transmission timing.

The physical sorting operation is handled by the STM32.

```text
Python / YOLOv8s
       │
       │  '1' = Good
       │  '2' = Bad
       ▼
   STM32 FIFO
       │
       ▼
   IR Sensor
       │
       ▼
     Servo
       │
       ▼
Physical Sorting
```

This architecture separates computer vision processing from embedded hardware control.
