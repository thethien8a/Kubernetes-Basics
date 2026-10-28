# Định hướng và cách học

[Mục lục](README.md) · [Tiến độ](tien-do-hoc-tap.md) · [Lab và hợp đồng nền tảng](lab-va-hop-dong-nen-tang.md)

## Yêu cầu đã chốt với học viên

- Đã học lộ trình Kubernetes cơ bản; muốn dùng k3d để quan sát nhiều node và hiểu sâu hơn.
- Là Data Engineer sử dụng nền tảng do DevOps/platform cung cấp, không học để trở thành người quản trị cluster.
- Không yêu cầu tự viết YAML từ trí nhớ; phải đọc hiểu cấu hình và biết cần yêu cầu thêm khả năng nào của cluster.
- Không deadline. Chia nhỏ và học đến khi hiểu, không chạy theo số buổi.
- Giữ khóa này là nơi duy nhất ghi tiến độ; lộ trình OrbStack cũ đã học xong và được xoá, tiến độ, scaffold và tổng kết mới nằm riêng trong `roadmap-k3d/`.

## Tiêu chuẩn đầu ra

Một dịch vụ không chỉ cần YAML hợp lệ. Người học phải nối được chuỗi:

```diagram
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│ Nhu cầu ứng dụng     │───▶│ Cấu hình/resource    │───▶│ Nền tảng thực thi    │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘

Bằng chứng/debug → Yêu cầu DevOps còn thiếu
```

Ví dụ: “cần PostgreSQL giữ dữ liệu” → đường PGDATA nằm trong volume → PVC chọn class phù hợp → provisioner/backend thực sự cấp storage → kiểm claim, mount và dữ liệu → làm rõ mất node, backup và restore với DevOps.

Phân công thực tế tùy tổ chức. Các mục “Cần DevOps” là khả năng cần được cung cấp hoặc xác nhận, không khẳng định DevOps phải tự làm mọi thao tác hay DE luôn có quyền triển khai.

## Một bài được chia thành nhiều khối

1. **Nêu tình huống và đầu ra:** chỉ chọn một vấn đề đang cần hiểu.
2. **Giảng lý thuyết:** vai trò, quan hệ, vòng đời và giới hạn; ôn kiến thức nền có liên quan mà không bắt học lại cả khóa cũ.
3. **Đọc cấu hình:** chỉ ra resource, đường dẫn field, giá trị lựa chọn, dependency và hành vi khi đổi/sai. Mentor có thể sinh skeleton; học viên giải thích chứ không chép thuộc.
4. **Kiểm tra hiểu:** dùng 2–4 câu trắc nghiệm tình huống. Hai câu trong mỗi file là bộ khởi đầu, không phải toàn bộ bài giảng. Chờ trả lời, giải thích chỗ chưa chắc và không hỏi lặp phần đã đạt.
5. **Thực hành:** học viên tự chạy từng bước sau khi hiểu phạm vi, dự đoán và cách phục hồi. Mentor không triển khai hoặc sửa workload thay.
6. **Kiểm chứng:** mentor tự đọc file và live bằng công cụ chỉ đọc nếu có quyền; không bắt gửi output có thể tự xem. Snapshot hiện tại không chứng minh lịch sử thí nghiệm chưa được lưu.
7. **Bàn giao kiến thức:** ghi “tôi tự cấu hình gì”, “cần DevOps gì”, “lab chưa chứng minh gì”; cập nhật tiến độ và tổng kết khi đạt.

Khi bị lỗi, dùng Hint Ladder trong [quy tắc mentor](huong-dan-hoc-va-mentor.md). Không dùng việc “tự debug” để bỏ qua lý thuyết/cấu hình cần học trước.

## Quy ước đọc cấu hình

- Bảng field ghi loại resource và đường dẫn. `[]` chỉ phần tử trong danh sách, không phải ký tự phải chép vào YAML.
- Trong bài, **PodSpec** là phần `spec` của Pod; ở Deployment/StatefulSet/Job nó thường nằm dưới `spec.template.spec`, ở CronJob dưới `spec.jobTemplate.spec.template.spec`.
- **Container** là phần tử `containers[]` bên trong PodSpec. **Pod template labels** khác `metadata.labels` của controller.
- Helm values phụ thuộc chart và version; không suy tên values từ tên field Kubernetes. Phải kiểm resource render thực tế.
- Config ứng dụng như `spark.*` hoặc Airflow `[core]` không phải field Kubernetes, dù được đưa vào container qua args/env/file.
- Schema/dry-run thành công chỉ chứng minh một phần tính hợp lệ, không chứng minh image kéo được, ứng dụng sẵn sàng hoặc dữ liệu đúng.

## Tiêu chí đạt một bài

| Mặt cần đạt | Bằng chứng |
|---|---|
| Hiểu khái niệm | Giải thích được quan hệ và một tình huống đổi/sai cấu hình bằng lời của mình. |
| Đọc cấu hình | Chỉ đúng resource/field/ref tạo ra hành vi; không chỉ nói “YAML này chạy được”. |
| Thực hành | Có kết quả đúng của lab cùng đối chứng được yêu cầu, gắn context/namespace/identity/thời điểm. |
| Làm việc với DevOps | Nêu dependency, quyền/phạm vi, cách kiểm tra và người cần hỗ trợ. |
| Hiểu giới hạn | Nêu điều không thể suy ra từ lab, nhất là HA, backup, bảo mật và hiệu năng. |

Mỗi bài có tiêu chí riêng. Bài 01 chưa cần cluster, bằng chứng là phân loại trách nhiệm; Bài 02 cần runtime của cluster mới. Phần ghi rõ “đọc/giả định” không bắt triển khai để đạt và không được ghi thành đã thực hành. Nếu lab bắt buộc chưa chạy được thì giữ trạng thái `Bị kẹt` hoặc `Đang học`, không dùng lý thuyết để thay bằng chứng runtime.

## Ghi chép sau bài

Chỉ tạo `after-study/NN-ten-bai.md` bên trong khóa mới khi có nội dung thật. Bản tổng kết gồm: điều đã hiểu, bảng field quan trọng, cấu hình đã chọn và lý do, expected/observed, lỗi đã xử lý, câu hỏi đã đạt/còn vướng, yêu cầu DevOps và giới hạn. Chèn link tới bài và tiến độ. Không tạo 32 bản tổng kết rỗng hoặc đánh dấu hoàn thành trước.

Tài liệu hiện là kế hoạch có nguồn tham chiếu. Trước thực hành, mentor chọn và kiểm phiên bản tương thích, giải thích scaffold rồi mới giao lệnh; không lấy việc tài liệu đã được soạn làm bằng chứng lab chạy được.
