# STM32-Based Lemon Sorting System

Hệ thống phân loại chất lượng quả chanh tự động trên băng chuyền sử dụng **YOLOv8s**, **OpenCV** và **STM32F103C6T6**.

Webcam thu nhận hình ảnh quả chanh theo thời gian thực. Máy tính sử dụng YOLOv8s để phát hiện và phân loại sản phẩm thành hai lớp `Good` và `Bad`. Kết quả phân loại được truyền đến STM32 thông qua UART để điều khiển cảm biến, servo và cập nhật thông tin trên LCD.

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

<!-- Thêm ảnh hệ thống sau -->
<!-- ![System Overview](docs/system/system_overview.jpg) -->

<!-- Thêm sơ đồ kiến trúc sau -->
<!-- ![System Architecture](docs/system/architecture.png) -->

---

## Main Features

- Real-time lemon detection using YOLOv8s
- Classification into `Good` and `Bad`
- Object tracking to avoid duplicate classification
- Sorting-line based trigger logic
- UART communication between PC and STM32
- FIFO queue for classification commands
- Two IR sensors for product position detection
- Two servo motors for sorting
- LCD 16x2 for displaying product counters
- Real-time FPS and system status display

---

## Hardware

| Component | Function |
|---|---|
| STM32F103C6T6 | Main embedded controller |
| USB Webcam | Captures lemon images |
| CH340 USB-to-UART | Communication between PC and STM32 |
| 2 × MG90S Servo | Sorting mechanism |
| 2 × IR Sensor | Detects lemons at sorting positions |
| LCD 16x2 + I2C | Displays system information |
| DC Motor | Drives conveyor belt |
| PWM Speed Controller | Controls conveyor speed |
| XL4015 | Provides 5 V supply for peripheral devices |
| Conveyor Belt | Transports lemons |

---

## Software & Technologies

| Technology | Usage |
|---|---|
| Python | Computer vision application |
| OpenCV | Webcam capture and image processing |
| YOLOv8s | Lemon detection and classification |
| Ultralytics | YOLO training and inference |
| PySerial | UART communication |
| STM32CubeIDE | STM32 firmware development |
| STM32 HAL | Peripheral control |
| Roboflow | Dataset management and annotation |
| Kaggle | YOLOv8s training and evaluation |

---

## YOLOv8s Model

The model was trained to detect two lemon quality classes:

```text
0 - Good
1 - Bad
```

Main dataset:

| Information | Value |
|---|---:|
| Images | 2,524 |
| Objects | 3,353 |
| Classes | 2 |
| Train | 2,030 images |
| Validation | 246 images |
| Test | 248 images |

The main generalization evaluation was performed using an independent test dataset containing 243 test images.

| Metric | Result |
|---|---:|
| Precision | 95.32% |
| Recall | 92.90% |
| mAP@0.5 | 95.76% |
| mAP@0.5:0.95 | 82.12% |

More details are available in:

[`docs/training/`](docs/training/)

---

## Real-Time Deployment

The real-time vision application uses:

```text
Model: YOLOv8s
Input size: 320
Confidence threshold: 0.60
Camera: USB Webcam
```

Observed display speed during system testing:

```text
30.2 - 31.4 FPS
```

---

## STM32 Responsibilities

STM32F103C6T6 is responsible for:

- Receiving classification results from the PC through UART
- Storing classification commands in a FIFO queue
- Reading two IR sensors
- Generating PWM signals for two servo motors
- Executing the Good / Bad sorting sequence
- Updating Good / Bad counters
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
- Stabilizing the predicted class
- Detecting when an object crosses the sorting line
- Preventing duplicate UART commands
- Sending `Good` / `Bad` classification commands to STM32
- Reading STM32 status
- Displaying detection results and FPS

More details:

[`vision/`](vision/)

---

## Communication Flow

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

## UART Commands

The PC sends classification results to STM32 using UART:

| Command | Classification |
|---|---|
| `1` | Good |
| `2` | Bad |

UART configuration:

```text
Baud rate : 9600 bps
Data bits : 8
Parity    : None
Stop bits : 1
```

---

## STM32 Pin Configuration

| Peripheral | STM32 Pin | Function |
|---|---|---|
| USART1 TX | PA9 | STM32 → CH340 |
| USART1 RX | PA10 | CH340 → STM32 |
| Servo 1 | PA0 | Good sorting |
| Servo 2 | PA1 | Bad sorting |
| IR Sensor 1 | PB0 | Good position |
| IR Sensor 2 | PB1 | Bad position |
| I2C SCL | PB6 | LCD clock |
| I2C SDA | PB7 | LCD data |

---

## Repository Structure

```text
stm32-lemon-sorting/
│
├── README.md
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

Demo video:

[Watch Demo Video](YOUR_DEMO_VIDEO_LINK)

---

## How It Works

1. The webcam captures a lemon moving on the conveyor.
2. YOLOv8s detects the lemon and predicts `Good` or `Bad`.
3. The program tracks the lemon between video frames.
4. The predicted class must remain stable before being accepted.
5. When the lemon crosses the sorting line, the PC sends the classification result through UART.
6. STM32 stores the received result in a FIFO queue.
7. The corresponding IR sensor detects the lemon near the sorting mechanism.
8. STM32 activates the appropriate servo.
9. The lemon is pushed into the corresponding sorting area.
10. The Good / Bad counter is updated on the LCD.

---

## Project Purpose

This project was developed as a graduation project combining:

**Computer Vision + Embedded Firmware + UART Communication + Sensor/Actuator Control**

The project demonstrates the integration of a real-time object detection model with an STM32-based embedded control system.
