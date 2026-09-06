# Danh sách linh kiện phần cứng

## 1. Vi điều khiển & giao tiếp

| Linh kiện | Số lượng | Vai trò | Ghi chú |
|-----------|----------|---------|---------|
| STM32F103C6T6 (Blue Pill) | 1 | Bộ điều khiển trung tâm | Nhận UART, điều khiển servo, đọc IR, hiển thị LCD |
| Mạch USB-to-UART CH340 | 1 | Chuyển đổi USB ↔ UART | Giao tiếp giữa máy tính và STM32 |
| ST-LINK V2 | 1 | Nạp chương trình & debug | Chỉ dùng khi nạp firmware |

## 2. Thị giác máy tính

| Linh kiện | Số lượng | Vai trò | Ghi chú |
|-----------|----------|---------|---------|
| Webcam SWC-02 | 1 | Thu nhận hình ảnh | Độ phân giải 640×480, kết nối USB |

## 3. Cơ cấu chấp hành

| Linh kiện | Số lượng | Vai trò | Ghi chú |
|-----------|----------|---------|---------|
| Động cơ servo MG90S | 2 | Cơ cấu gạt sản phẩm | Servo 1: chanh tốt (Good)<br>Servo 2: chanh hỏng (Bad) |
| Động cơ DC 12–24V | 1 | Kéo băng tải | Không điều khiển trực tiếp bởi STM32 |
| Mạch điều tốc PWM 5A | 1 | Điều chỉnh tốc độ băng tải | Điều chỉnh bằng núm chiết áp |

## 4. Cảm biến

| Linh kiện | Số lượng | Vai trò | Ghi chú |
|-----------|----------|---------|---------|
| Cảm biến hồng ngoại FC-51 | 2 | Phát hiện sản phẩm đến vị trí gạt | IR1 → PB0 (Good)<br>IR2 → PB1 (Bad) |

## 5. Hiển thị

| Linh kiện | Số lượng | Vai trò | Ghi chú |
|-----------|----------|---------|---------|
| LCD 16x2 + module I²C | 1 | Hiển thị số lượng Good/Bad | Giao tiếp I²C (SDA, SCL) |

## 6. Nguồn điện

| Linh kiện | Số lượng | Vai trò | Ghi chú |
|-----------|----------|---------|---------|
| Pin Li-ion Makita 5S1P (18–21V) | 1 | Nguồn chính động lực | Cấp cho động cơ DC qua mạch điều tốc |
| Module hạ áp XL4015 5A | 1 | Hạ áp 18–21V → 5V | Cấp nguồn cho servo, IR, LCD |
| Nguồn USB từ máy tính | - | Cấp nguồn STM32, Webcam, CH340 | Tách biệt hoàn toàn với nguồn động lực |

## 7. Cơ khí

| Linh kiện | Số lượng | Vai trò |
|-----------|----------|---------|
| Băng tải (khung nhôm + dây PVC) | 1 | Vận chuyển sản phẩm |
| Khay chứa sản phẩm Good / Bad | 2 | Nhận sản phẩm sau khi gạt |
