# Dataset - Lemon Sorting

Dataset này được tự thu thập và gán nhãn, dùng để huấn luyện mô hình YOLOv8 cho dự án "Hệ thống phân loại sản phẩm tự động trên băng chuyền". 

## 📊 Thông tin chi tiết (Phiên bản v7)
* **Tổng số lượng:** 2.524 ảnh thực tế với nhiều bối cảnh, góc chụp và điều kiện ánh sáng khác nhau.
* **Số lượng đối tượng:** 3.353 đối tượng đã được gán nhãn (Bounding Box).
* **Phân bổ lớp (Class):**
  * `Good` (Chanh tốt): 1.884 đối tượng.
  * `Bad` (Chanh hỏng): 1.469 đối tượng.
* **Tỷ lệ phân chia:** Train (2.030 ảnh) - Validation (246 ảnh) - Test (248 ảnh).

## 📥 Tải Dataset đầy đủ
Do số lượng file `images` và `labels` rất lớn, toàn bộ bộ dữ liệu đã được đưa lên nền tảng Roboflow để tiện quản lý và tối ưu dung lượng cho repository.
* **Định dạng:** YOLOv8
* **Link tải trực tiếp:** [Truy cập Dataset trên Roboflow](https://app.roboflow.com/ds/HdPQOiaHjQ?key=vDJt2PBLZN)

*(Lưu ý: Để sử dụng, hãy tải dataset từ link trên và cấu hình lại đường dẫn trong file `data.yaml` cho phù hợp với máy tính của bạn).*
