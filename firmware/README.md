# STM32 Firmware

Firmware for the lemon sorting system based on the **STM32F103C6T6** microcontroller.

The STM32 does not perform computer vision processing. Lemon detection and classification are performed on the PC using YOLOv8s. The STM32 receives classification results through UART and controls the physical sorting hardware.

---

## Microcontroller

```text
MCU                    : STM32F103C6T6
Core                   : ARM Cortex-M3
Development Environment: STM32CubeIDE
Framework               : STM32 HAL
```

---

## Firmware Responsibilities

The STM32 firmware is responsible for:

- Receiving classification results from the PC through USART1
- Storing incoming classification commands in a FIFO queue
- Reading two IR sensors
- Determining which sorting mechanism should be activated
- Generating PWM signals for two MG90S servo motors
- Executing the physical sorting sequence
- Updating Good and Bad counters
- Displaying system information on the LCD
- Sending status information back to the PC

---

## Peripheral Configuration

| Peripheral | Function |
|---|---|
| USART1 | Communication with the PC |
| GPIO | IR sensor inputs |
| Timer / PWM | Servo motor control |
| I2C1 | LCD 16x2 communication |
| SWD | Programming and debugging |

---

## Pin Configuration

| Device | Signal | STM32 Pin | Function |
|---|---|---|---|
| CH340 | RXD | PA9 / USART1 TX | STM32 → PC |
| CH340 | TXD | PA10 / USART1 RX | PC → STM32 |
| Servo 1 | PWM | PA0 | Good sorting |
| Servo 2 | PWM | PA1 | Bad sorting |
| IR Sensor 1 | OUT | PB0 | Good sorting position |
| IR Sensor 2 | OUT | PB1 | Bad sorting position |
| LCD I2C | SCL | PB6 | I2C clock |
| LCD I2C | SDA | PB7 | I2C data |

UART wiring:

```text
CH340 TXD ─────► PA10 (USART1 RX)

CH340 RXD ◄───── PA9  (USART1 TX)

CH340 GND ────── STM32 GND
```

---

## UART Configuration

```text
Baud Rate : 9600 bps
Data Bits : 8
Parity    : None
Stop Bits : 1
```

### Commands Received from the PC

| UART Command | Classification |
|---|---|
| `1` | Good |
| `2` | Bad |

The PC sends a classification command only after the detection and transmission conditions have been satisfied.

---

## FIFO Classification Queue

The STM32 uses a **FIFO queue** to store classification results received from the PC.

```text
PC
 │
 │ UART
 ▼
┌───────────────┐
│ STM32 USART1  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  FIFO Queue   │
└───────┬───────┘
        │
        ▼
 Wait for IR Sensor
        │
        ▼
   Servo Control
```

The FIFO structure preserves the classification order of lemons moving through the system.

---

## Good Sorting Sequence

When STM32 receives:

```text
'1'
```

the command represents a `Good` lemon.

```text
Receive '1'
     │
     ▼
Store in FIFO
     │
     ▼
Wait for IR1
     │
     ▼
IR1 Falling Edge
     │
     ▼
Debounce
     │
     ▼
Delay Before Sorting
     │
     ▼
Activate Servo 1
     │
     ▼
Return Servo
     │
     ▼
Good Counter +1
     │
     ▼
Update LCD
```

Related hardware:

```text
IR1     → PB0
Servo 1 → PA0
```

---

## Bad Sorting Sequence

When STM32 receives:

```text
'2'
```

the command represents a `Bad` lemon.

```text
Receive '2'
     │
     ▼
Store in FIFO
     │
     ▼
Wait for IR2
     │
     ▼
IR2 Falling Edge
     │
     ▼
Debounce
     │
     ▼
Delay Before Sorting
     │
     ▼
Activate Servo 2
     │
     ▼
Return Servo
     │
     ▼
Bad Counter +1
     │
     ▼
Update LCD
```

Related hardware:

```text
IR2     → PB1
Servo 2 → PA1
```

---

## Timing Logic

Main timing parameters used by the sorting sequence:

| Parameter | Value |
|---|---:|
| IR Sensor Debounce | 300 ms |
| Delay Before Servo Activation | 400 ms |
| Servo Open Time | 400 ms |

After the corresponding IR sensor detects a lemon, the STM32 waits for the configured delay before activating the servo so that the lemon reaches the correct sorting position.

---

## IR Sensors

Two IR sensors are used to determine when a lemon reaches each sorting mechanism.

```text
IR Sensor 1 → PB0 → Good sorting position

IR Sensor 2 → PB1 → Bad sorting position
```

The classification result is received first through UART. STM32 then waits for the corresponding IR sensor before activating the servo.

---

## Servo Control

Two MG90S servo motors are controlled using PWM signals.

```text
PA0 ─────► Servo 1 ─────► Good

PA1 ─────► Servo 2 ─────► Bad
```

The servo motors use an external 5 V power supply instead of drawing their operating current directly from the STM32.

The servo power supply and STM32 must share a common GND so that the PWM signals use the same voltage reference.

---

## LCD

The LCD 16x2 uses I2C communication.

```text
STM32 PB6 (SCL) ─────► LCD SCL

STM32 PB7 (SDA) ─────► LCD SDA
```

The LCD is used to display system status and the accumulated number of classified lemons.

---

## Firmware Flow

```text
System Start
     │
     ▼
Initialize Peripherals
     │
     ├── GPIO
     ├── USART1
     ├── PWM
     ├── I2C
     └── LCD
     │
     ▼
Wait for UART Command
     │
     ▼
Receive '1' / '2'
     │
     ▼
Push Command to FIFO
     │
     ▼
Read Queue
     │
     ▼
Wait for Corresponding IR Sensor
     │
     ▼
Activate Corresponding Servo
     │
     ▼
Update Product Counter
     │
     ▼
Update LCD
     │
     ▼
Return to Idle
```

---

## PC vs STM32 Responsibilities

| PC / Python | STM32F103C6T6 |
|---|---|
| Webcam capture | UART reception |
| YOLOv8s inference | FIFO queue management |
| Object tracking | IR sensor reading |
| Good / Bad classification | PWM generation |
| Sorting-line detection | Servo control |
| Duplicate-send prevention | LCD control |
| UART command transmission | Product counting |

This architecture allows computationally intensive computer vision tasks to run on the PC while the STM32 focuses on deterministic hardware control.
