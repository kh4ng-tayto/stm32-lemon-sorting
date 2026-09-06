# Huấn luyện mô hình YOLOv8s

Thư mục này mô tả quá trình xây dựng bộ dữ liệu, huấn luyện và đánh giá mô hình **YOLOv8s** dùng để phân loại quả chanh (Good / Bad).

## Tổng quan

| Thông tin | Chi tiết |
|---------|----------|
| Mô hình | YOLOv8s |
| Framework | Ultralytics |
| Dataset | Roboflow v7 |
| Số ảnh | 2.524 ảnh |
| Số đối tượng | 3.353 (Good: 1.884 – Bad: 1.469) |
| Kích thước suy luận | `imgsz=320` |
| Confidence threshold | 0.60 |

## Kết quả chính (tập kiểm thử độc lập)

| Metric | Giá trị |
|--------|---------|
| Precision | 95.32% |
| Recall | 92.90% |
| mAP@0.5 | 95.76% |
| mAP@0.5:0.95 | 82.12% |

> Kết quả trên tập Roboflow v7 chỉ mang tính tham khảo do có nguy cơ trùng đối tượng giữa train/val/test.
