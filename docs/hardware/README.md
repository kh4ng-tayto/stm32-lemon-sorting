# Phần cứng hệ thống phân loại sản phẩm tự động

Thư mục này mô tả toàn bộ phần cứng của **Hệ thống phân loại sản phẩm tự động trên băng chuyền sử dụng thị giác máy tính và cơ cấu gạt**.

## Tổng quan hệ thống

Hệ thống bao gồm:
- **Webcam** thu nhận hình ảnh quả chanh trên băng tải
- **Máy tính** chạy YOLOv8s + OpenCV để nhận diện & phân loại (Good / Bad)
- **STM32F103C6T6** nhận kết quả qua UART, điều khiển servo gạt và hiển thị trên LCD
- **Băng tải** chạy bằng động cơ DC + mạch điều tốc
- **2 cảm biến hồng ngoại** phát hiện vị trí gạt
- **2 servo MG90S** thực hiện cơ cấu gạt

## Cấu trúc thư mục
hardware/
├── README.md          ← File này
├── components.md      ← Danh sách linh kiện chi tiết
├── wiring.md          ← Sơ đồ kết nối & chân pin
└── images/
└── hardware.jpg   ← Ảnh tổng thể mô hình


## Tài liệu liên quan

- [Danh sách linh kiện](components.md)
- [Sơ đồ kết nối chi tiết](wiring.md)
- Ảnh thực tế mô hình: [hardware/images](images)

## Lưu ý quan trọng

- Nguồn động lực (động cơ DC) và nguồn điều khiển (5V cho servo, IR, LCD) được tách riêng.
- STM32 được cấp nguồn riêng qua USB.
- Tốc độ băng tải điều chỉnh bằng núm chiết áp trên mạch PWM (không qua STM32).
