# Huấn luyện mô hình YOLOv8s

Thư mục này trình bày quá trình xây dựng bộ dữ liệu, cấu hình huấn luyện và đánh giá mô hình **YOLOv8s** sử dụng trong hệ thống phân loại chất lượng quả chanh.

Mô hình thực hiện bài toán **Object Detection** với hai lớp:

- `Good`: chanh tốt
- `Bad`: chanh hỏng

Sau khi huấn luyện, trọng số tốt nhất `best.pt` được sử dụng trong chương trình Python để nhận diện chanh theo thời gian thực từ webcam.

---

## 1. Tổng quan

| Thông tin | Chi tiết |
|---|---|
| Bài toán | Object Detection |
| Mô hình | YOLOv8s |
| Framework | Ultralytics |
| Dataset | Roboflow v7 |
| Số lớp | 2 |
| Classes | Good / Bad |
| Tổng số ảnh | 2.524 |
| Tổng số đối tượng | 3.353 |
| Good | 1.884 đối tượng |
| Bad | 1.469 đối tượng |
| Môi trường huấn luyện | Kaggle |
| GPU | NVIDIA Tesla T4 |
| Trọng số tốt nhất | `best.pt` |

---

## 2. Bộ dữ liệu

Bộ dữ liệu được xây dựng để nhận diện và phân loại quả chanh thành hai nhóm chất lượng `Good` và `Bad`.

Mỗi quả chanh trong ảnh được gán nhãn bằng **bounding box** và class tương ứng.

### Thống kê đối tượng

| Class | Số đối tượng |
|---|---:|
| Good | 1.884 |
| Bad | 1.469 |
| **Tổng cộng** | **3.353** |

### Phân chia dữ liệu

Bộ dữ liệu Roboflow phiên bản v7 gồm tổng cộng **2.524 ảnh** và được chia thành:

| Dataset | Tỷ lệ | Số ảnh |
|---|---:|---:|
| Train | 80% | 2.030 |
| Validation | 10% | 246 |
| Test | 10% | 248 |
| **Tổng cộng** | **100%** | **2.524** |

Dữ liệu trên Roboflow được tiền xử lý bằng:

- Auto-Orient
- Resize về kích thước `640 × 640`
- Không tạo thêm ảnh augmentation cố định trên Roboflow

Các phép tăng cường dữ liệu được Ultralytics áp dụng trực tuyến trong quá trình huấn luyện.

---

## 3. Phân bố dữ liệu huấn luyện

Riêng tập Train có tổng cộng **2.723 đối tượng**:

| Class | Số đối tượng |
|---|---:|
| Good | 1.543 |
| Bad | 1.180 |
| **Tổng cộng** | **2.723** |

Số lượng đối tượng Good cao hơn Bad nhưng cả hai lớp đều có hơn 1.000 mẫu để mô hình học các đặc trưng.

<!-- Thêm ảnh thống kê dataset nếu có -->
![Dataset Distribution](images/dataset_distribution.png)

---

## 4. Cấu hình huấn luyện

Mô hình `yolov8s.pt` đã được pretrained được sử dụng làm trọng số khởi tạo.

Quá trình huấn luyện được thực hiện trên **Kaggle** với GPU **NVIDIA Tesla T4**.

| Tham số | Giá trị |
|---|---|
| Model | `yolov8s.pt` |
| Task | Detection |
| Epoch tối đa | 120 |
| Epoch thực tế | 118 |
| Early Stopping | `patience=25` |
| Batch Size | 16 |
| Image Size | `640 × 640` |
| Optimizer | `auto` |
| Seed | 42 |
| Device | NVIDIA Tesla T4 (`device=0`) |
| AMP | `True` |
| Validation | `True` |

Mô hình được đánh giá trên tập Validation sau mỗi epoch.

Giá trị **fitness tốt nhất xuất hiện tại epoch 93**. Sau 25 epoch tiếp theo không có cải thiện, cơ chế Early Stopping kết thúc quá trình huấn luyện tại epoch 118.

Trọng số tại epoch tốt nhất được Ultralytics lưu thành:

```text
best.pt
```

---

## 5. Data Augmentation

Trong quá trình huấn luyện, Ultralytics áp dụng augmentation trực tuyến cho dữ liệu Train.

| Augmentation | Giá trị |
|---|---|
| Hue | `hsv_h=0.015` |
| Saturation | `hsv_s=0.7` |
| Value | `hsv_v=0.4` |
| Translation | `translate=0.1` |
| Scale | `scale=0.5` |
| Horizontal Flip | `fliplr=0.5` |
| Vertical Flip | `flipud=0.0` |
| Mosaic | `mosaic=1.0` |
| Close Mosaic | `close_mosaic=10` |

Mosaic được sử dụng trong quá trình huấn luyện và được tắt trong **10 epoch cuối**.

`MixUp` và `CutMix` không được sử dụng.

Các phép augmentation chỉ được áp dụng cho tập Train và không được áp dụng cho Validation hoặc Test.

---

## 6. Kết quả huấn luyện

Các đường cong huấn luyện cho thấy sự thay đổi của:

- Box Loss
- Classification Loss
- Distribution Focal Loss
- Precision
- Recall
- mAP@0.5
- mAP@0.5:0.95

trong quá trình huấn luyện YOLOv8s.

![Training Results](images/results.png)

Trọng số có kết quả tốt nhất được ghi nhận tại **epoch 93**.

---

## 7. Kết quả trên tập Validation

Kết quả của mô hình trên tập Validation:

| Metric | Kết quả |
|---|---:|
| Precision | 98,66% |
| Recall | 96,54% |
| mAP@0.5 | 99,39% |
| mAP@0.5:0.95 | 92,15% |

### Precision-Recall Curve

![Validation PR Curve](images/pr_curve_validation.png)

### Confusion Matrix

![Validation Confusion Matrix](images/confusion_matrix_validation.png)

Kết quả Validation cho thấy mô hình có khả năng nhận diện tốt hai lớp Good và Bad trên dữ liệu được sử dụng trong quá trình phát triển mô hình.

---

## 8. Kết quả trên tập Test Roboflow v7

Sau khi hoàn thành huấn luyện, trọng số tốt nhất `best.pt` được đánh giá trên **248 ảnh Test** của bộ dữ liệu Roboflow v7.

| Metric | Kết quả |
|---|---:|
| Precision | 98,53% |
| Recall | 96,88% |
| mAP@0.5 | 98,67% |
| mAP@0.5:0.95 | 90,80% |

AP@0.5 theo từng lớp:

| Class | AP@0.5 |
|---|---:|
| Bad | 98,4% |
| Good | 98,9% |

### Precision-Recall Curve

![Roboflow Test PR Curve](images/pr_curve_test_v7.png)

### Confusion Matrix

![Roboflow Test Confusion Matrix](images/confusion_matrix_test_v7.png)

> **Lưu ý:** Bộ dữ liệu Roboflow v7 được phân chia theo ảnh. Một số ảnh chụp ở các góc khác nhau của cùng một quả chanh có thể xuất hiện ở cả tập Train và Test. Vì vậy, kết quả trên tập Test v7 được sử dụng như kết quả tham khảo và không được chọn làm kết quả chính để đánh giá khả năng tổng quát hóa.

---

## 9. Kiểm thử trên bộ dữ liệu độc lập

Để đánh giá khả năng tổng quát hóa tốt hơn, mô hình được kiểm tra thêm trên một bộ dữ liệu độc lập được thu thập riêng và không sử dụng trong quá trình huấn luyện.

Bộ dữ liệu độc lập phiên bản v4 gồm:

- 246 ảnh tổng cộng
- 243 ảnh Test
- 3 ảnh Validation
- 268 đối tượng được gán nhãn
- Không có ảnh Training

Kết quả dưới đây được tính trên **243 ảnh Test chứa 265 đối tượng**.

| Class | Số đối tượng |
|---|---:|
| Bad | 220 |
| Good | 45 |
| **Tổng cộng** | **265** |

### Kết quả đánh giá

| Metric | Kết quả |
|---|---:|
| Precision | **95,32%** |
| Recall | **92,90%** |
| mAP@0.5 | **95,76%** |
| mAP@0.5:0.95 | **82,12%** |

AP@0.5 theo từng lớp:

| Class | AP@0.5 |
|---|---:|
| Bad | 93,2% |
| Good | 98,4% |

### Precision-Recall Curve

![Independent Test PR Curve](images/pr_curve_independent.png)

### Confusion Matrix

![Independent Test Confusion Matrix](images/confusion_matrix_independent.png)

Kết quả trên bộ dữ liệu độc lập được sử dụng làm **kết quả chính** để đánh giá khả năng tổng quát hóa của mô hình vì các ảnh này không được sử dụng trong quá trình huấn luyện hoặc lựa chọn mô hình.

---

## 10. So sánh kết quả

| Dataset | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|
| Validation | 98,66% | 96,54% | 99,39% | 92,15% |
| Roboflow v7 Test | 98,53% | 96,88% | 98,67% | 90,80% |
| **Independent Test** | **95,32%** | **92,90%** | **95,76%** | **82,12%** |

Kết quả trên bộ dữ liệu độc lập thấp hơn so với Validation và Test v7, nhưng vẫn cho thấy mô hình có khả năng nhận diện hai lớp Good và Bad trên dữ liệu chưa được sử dụng trong quá trình huấn luyện.

---

## 11. Cấu hình đánh giá

Các lần đánh giá ngoại tuyến sử dụng trọng số tốt nhất `best.pt` với cấu hình:

| Tham số | Giá trị |
|---|---|
| Weights | `best.pt` |
| Method | `model.val()` |
| Split | `test` |
| Image Size | `640 × 640` |
| Batch Size | 16 |
| Device | NVIDIA Tesla T4 |
| Plots | `True` |
| Ultralytics | 8.4.132 |

Lệnh đánh giá:

```python
results = model.val(
    data=DATA_YAML,
    split="test",
    imgsz=640,
    batch=16,
    device=0,
    plots=True
)
```

---

## 12. Triển khai mô hình

Cấu hình huấn luyện và đánh giá sử dụng:

```text
imgsz=640
```

Khi triển khai nhận diện theo thời gian thực từ webcam, hệ thống sử dụng:

```text
imgsz=320
confidence=0.60
```

Kích thước ảnh nhỏ hơn được sử dụng nhằm giảm khối lượng tính toán và duy trì tốc độ xử lý gần thời gian thực.

Trong thử nghiệm thực tế, tốc độ hiển thị của hệ thống đạt khoảng:

```text
30.2 – 31.4 FPS
```

---

## 13. Luồng xử lý mô hình

```text
Lemon Dataset
      │
      ▼
Data Annotation
      │
      ▼
Train / Validation / Test
      │
      ▼
YOLOv8s Pretrained Model
      │
      ▼
Model Training
      │
      ▼
Validation
      │
      ▼
best.pt
      │
      ├──────────────► Roboflow v7 Test
      │
      └──────────────► Independent Test
                              │
                              ▼
                     Model Evaluation
                              │
                              ▼
                     Real-time Deployment
```

---

## 14. Ứng dụng trong hệ thống

Sau khi huấn luyện và đánh giá, file trọng số:

```text
best.pt
```

được sử dụng trong chương trình Python để xử lý hình ảnh từ **USB webcam**.

Luồng hoạt động khi triển khai:

```text
USB Webcam
     │
     ▼
OpenCV
     │
     ▼
YOLOv8s (best.pt)
     │
     ▼
Good / Bad Detection
     │
     ▼
Sorting Logic
     │
     ▼
UART
     │
     ▼
STM32F103C6T6
     │
     ▼
Servo Sorting Mechanism
```

Máy tính đảm nhiệm xử lý ảnh và chạy YOLOv8s, trong khi STM32F103C6T6 nhận kết quả phân loại qua UART và điều khiển phần cứng của hệ thống.

---

## 15. Kết luận

Mô hình YOLOv8s được huấn luyện trên bộ dữ liệu gồm **2.524 ảnh và 3.353 đối tượng** thuộc hai lớp Good và Bad.

Kết quả chính trên bộ dữ liệu kiểm thử độc lập gồm 243 ảnh đạt:

- **Precision: 95,32%**
- **Recall: 92,90%**
- **mAP@0.5: 95,76%**
- **mAP@0.5:0.95: 82,12%**

Sau khi đánh giá, trọng số tốt nhất `best.pt` được tích hợp vào chương trình Python để thực hiện nhận diện quả chanh theo thời gian thực và truyền kết quả phân loại đến STM32F103C6T6 thông qua UART.

---

## Files

```text
training/
├── README.md
└── images/
    ├── dataset_distribution.png
    ├── results.png
    ├── pr_curve_validation.png
    ├── confusion_matrix_validation.png
    ├── pr_curve_test_v7.png
    ├── confusion_matrix_test_v7.png
    ├── pr_curve_independent.png
    └── confusion_matrix_independent.png
```
