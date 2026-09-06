# Sơ đồ kết nối phần cứng

## 1. Kết nối máy tính ↔ STM32 (UART qua CH340)

| CH340 | STM32F103C6T6 | Ghi chú |
|-------|---------------|---------|
| TXD   | PA10 (RX)     | Chéo TX–RX |
| RXD   | PA9 (TX)      | |
| GND   | GND           | Bắt buộc nối chung |
| 5V    | *không dùng*  | STM32 cấp nguồn riêng qua USB |

> **Baud rate**: 115200 (cấu hình giống nhau ở cả Python và STM32)

## 2. Kết nối ST-LINK V2 (chỉ dùng khi nạp chương trình)

| ST-LINK V2 | STM32F103C6T6 |
|------------|---------------|
| SWDIO      | PA13          |
| SWCLK      | PA14          |
| GND        | GND           |
| 3.3V       | *không dùng*  | (STM32 đã có nguồn USB) |

## 3. Kết nối LCD 16x2 (I²C)

| Module I²C LCD | STM32F103C6T6 |
|----------------|---------------|
| SDA            | PB7           |
| SCL            | PB6           |
| VCC            | 5V            |
| GND            | GND           |

## 4. Kết nối 2 Servo MG90S

| Servo | Chân tín hiệu | STM32 | Nguồn |
|-------|---------------|-------|-------|
| Servo 1 (Good) | Signal | PA0 | 5V + GND chung |
| Servo 2 (Bad)  | Signal | PA1 | 5V + GND chung |

## 5. Kết nối 2 cảm biến hồng ngoại

| Cảm biến | Chân OUT | STM32 | Nguồn |
|----------|----------|-------|-------|
| IR1 (Good) | OUT | PB0 | 5V + GND |
| IR2 (Bad)  | OUT | PB1 | 5V + GND |
## 6. Kết nối động cơ DC + mạch điều tốc
Pin Makita 18–21V → Mạch điều tốc PWM 5A → Động cơ DC 12–24V


- Tốc độ điều chỉnh bằng **núm chiết áp** trên mạch điều tốc.
- **Không** kết nối với STM32 (hoạt động độc lập).

## 7. Phân phối nguồn 5V (sau module XL4015)
Pin Makita → XL4015 (hạ áp) → 5V
├── Servo 1 & 2
├── IR Sensor 1 & 2
├── LCD 16x2

> **Quan trọng**: Tất cả GND phải được nối chung (common ground) giữa STM32, 5V và các thiết bị ngoại vi.

## 8. Sơ đồ chân STM32F103C6T6 sử dụng

| Chân STM32 | Chức năng |
|------------|-----------|
| PA9        | UART TX   |
| PA10       | UART RX   |
| PA0        | PWM Servo 1 (Good) |
| PA1        | PWM Servo 2 (Bad)  |
| PB0        | IR1 (Good) |
| PB1        | IR2 (Bad)  |
| PB6        | I²C SCL    |
| PB7        | I²C SDA    |
| PA13       | SWDIO (nạp chương trình) |
| PA14       | SWCLK (nạp chương trình) |
