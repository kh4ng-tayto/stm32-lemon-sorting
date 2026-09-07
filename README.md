# STM32-Based Lemon Sorting System

An automatic lemon quality sorting system using **YOLOv8s**, **OpenCV**, and **STM32F103C6T6**.

A USB webcam captures lemons moving on a conveyor belt. The PC processes the camera stream using YOLOv8s and classifies each lemon as `Good` or `Bad`. The classification result is then transmitted to the STM32 through UART. The STM32 handles IR sensors, servo motors, product counting, and LCD display.

---

## System Overview

```text
                  USB Webcam
                       │
                       ▼
              Python + OpenCV
                       │
                       ▼
                   YOLOv8s
                       │
                  Good / Bad
                       │
                       ▼
                UART via CH340
                       │
                       ▼
                STM32F103C6T6
                 │     │     │
                 │     │     │
                IR    LCD   Servo
             Sensors         Motors
                 │              │
                 └──────┬───────┘
                        ▼
                  Lemon Sorting
```

<!-- Add a real system image later -->
<!-- ![System Overview](docs/system/system_overview.jpg) -->

<!-- Add a system architecture diagram later -->
<!-- ![System Architecture](docs/system/architecture.png) -->

---

## Main Features

- Real-time lemon detection using YOLOv8s
- Lemon quality classification into `Good` and `Bad`
- Object tracking across consecutive frames
- Stable-class verification before sending a result
- Sorting-line based trigger logic
- Duplicate UART command prevention
- UART communication between PC and STM32
- FIFO queue for classification commands
- Two IR sensors for detecting lemons at sorting positions
- Two servo motors for physical sorting
- LCD 16x2 for displaying product counters
- Real-time FPS and system status display

---

## Hardware

| Component | Function |
|---|---|
| STM32F103C6T6 | Main embedded controller |
| USB Webcam | Captures lemon images |
| CH340 USB-to-UART | Communication between PC and STM32 |
| 2 × MG90S Servo | Physical sorting mechanism |
| 2 × IR Sensor | Detects lemons at sorting positions |
| LCD 16x2 + I2C Module | Displays system information |
| DC Motor | Drives the conveyor belt |
| PWM Speed Controller | Adjusts conveyor speed |
| XL4015 | Provides a regulated 5 V supply |
| Conveyor Belt | Transports lemons |

---

## Software and Technologies

| Technology | Usage |
|---|---|
| Python | Main computer vision application |
| OpenCV | Webcam capture and image processing |
| YOLOv8s | Lemon detection and classification |
| Ultralytics | YOLO training and inference |
| PySerial | UART communication |
| STM32CubeIDE | STM32 firmware development |
| STM32 HAL | STM32 peripheral control |
| Roboflow | Dataset annotation and management |
| Kaggle | YOLOv8s training and evaluation |

---

## YOLOv8s Model

The YOLOv8s model detects two lemon quality classes:

```text
0 - Good
1 - Bad
```

### Dataset

| Information | Value |
|---|---:|
| Total Images | 2,524 |
| Total Objects | 3,353 |
| Classes | 2 |
| Training Images | 2,030 |
| Validation Images | 246 |
| Test Images | 248 |

The main generalization evaluation was performed on an independent test dataset containing **243 test images**.

### Independent Test Results

| Metric | Result |
|---|---:|
| Precision | 95.32% |
| Recall | 92.90% |
| mAP@0.5 | 95.76% |
| mAP@0.5:0.95 | 82.12% |

More training and evaluation details are available in:

[`docs/training/`](docs/training/)

---

## Real-Time Deployment

The real-time vision application uses the following configuration:

```text
Model                : YOLOv8s
Inference Image Size : 320
Confidence Threshold : 0.60
Camera               : USB Webcam
```

The observed display speed during system testing was approximately:

```text
30.2 - 31.4 FPS
```

---

## STM32 Responsibilities

The STM32F103C6T6 is responsible for:

- Receiving classification results from the PC through UART
- Storing classification commands in a FIFO queue
- Reading two IR sensors
- Generating PWM signals for two servo motors
- Executing the `Good` / `Bad` sorting sequence
- Updating Good and Bad product counters
- Displaying information on the LCD
- Sending status information back to the PC

More details:

[`firmware/`](firmware/)

---

## PC / Vision Responsibilities

The PC application is responsible for:

- Capturing frames from the USB webcam
- Running YOLOv8s inference
- Detecting and tracking lemons
- Stabilizing predicted classes
- Detecting when an object crosses the sorting line
- Preventing duplicate UART commands
- Sending classification commands to STM32
- Reading STM32 status messages
- Displaying detection results and FPS

More details:

[`vision/`](vision/)

---

## System Processing Flow

```text
Webcam
   │
   ▼
YOLOv8s Detection
   │
   ▼
Object Tracking
   │
   ▼
Class Stabilization
   │
   ▼
Sorting Line
   │
   ▼
Good / Bad
   │
   ▼
UART Command
   │
   ▼
STM32 FIFO Queue
   │
   ▼
IR Sensor Trigger
   │
   ▼
Servo Actuation
   │
   ▼
LCD Counter Update
```

---

## UART Communication

The PC sends classification results to STM32 using single-character UART commands.

| Command | Classification |
|---|---|
| `1` | Good |
| `2` | Bad |

UART configuration:

```text
Baud Rate : 9600 bps
Data Bits : 8
Parity    : None
Stop Bits : 1
```

---

## STM32 Pin Configuration

| Peripheral | STM32 Pin | Function |
|---|---|---|
| USART1 TX | PA9 | STM32 → CH340 |
| USART1 RX | PA10 | CH340 → STM32 |
| Servo 1 | PA0 | Good sorting mechanism |
| Servo 2 | PA1 | Bad sorting mechanism |
| IR Sensor 1 | PB0 | Good sorting position |
| IR Sensor 2 | PB1 | Bad sorting position |
| I2C SCL | PB6 | LCD clock |
| I2C SDA | PB7 | LCD data |

---

## Repository Structure

```text
stm32-lemon-sorting/
│
├── README.md
│
├── requirements.txt
│
├── .gitignore
│
├── docs/
│   ├── datasets/
│   │   ├── README.md
│   │   └── data.yaml
│   │
│   ├── training/
│   │   ├── README.md
│   │   └── images/
│   │
│   ├── hardware/
│   │   ├── README.md
│   │   ├── components.md
│   │   ├── wiring.md
│   │   └── images/
│   │
│   └── system/
│       ├── architecture.png
│       └── system_overview.jpg
│
├── firmware/
│   ├── README.md
│   └── main.c
│
└── vision/
    ├── README.md
    ├── lemon_sorting_vertical_optimized.py
    └── best.pt
```

---

## Demo

[Watch Demo Video](https://drive.google.com/file/d/1tyYr8zXwPygE4yLUJ9bT8ScqUixk7lFU/view?usp=sharing)

---

## How It Works

1. The USB webcam captures a lemon moving on the conveyor belt.
2. YOLOv8s detects the lemon and predicts its class as `Good` or `Bad`.
3. The application tracks the lemon across consecutive frames.
4. The predicted class must remain stable before it is accepted.
5. When the lemon reaches the sorting line, the PC sends the classification result through UART.
6. STM32 stores the received result in a FIFO queue.
7. The corresponding IR sensor detects the lemon near the sorting mechanism.
8. STM32 activates the appropriate servo motor.
9. The lemon is pushed into the corresponding sorting area.
10. The Good or Bad counter is updated on the LCD.

---

## Project Purpose

This project was developed as a graduation project combining:

**Computer Vision + Embedded Firmware + UART Communication + Sensor/Actuator Control**

The project demonstrates the integration of a real-time computer vision system with an STM32-based embedded controller for automatic product sorting.
