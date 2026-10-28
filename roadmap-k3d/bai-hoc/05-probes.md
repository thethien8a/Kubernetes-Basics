# Bài 05 — Startup, readiness và liveness

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](04-pod-va-controller.md) · [Tiếp](06-rollout-va-shutdown.md)

**Đầu vào:** vòng đời Pod/container. **Đầu ra:** không đồng nhất Running, Ready và “ứng dụng xử lý đúng”.

## 1. Khối kiến thức

- Startup probe cho ứng dụng thời gian khởi động; khi có startup probe, readiness/liveness chưa bắt đầu cho tới khi startup thành công. Vượt ngưỡng lỗi startup có thể gây restart container.
- Readiness trả lời “có nên nhận traffic không”; thất bại làm Pod không Ready, thông thường loại khỏi backend Ready của Service. Nó không tự restart container và không nhất thiết ngắt các kết nối đang tồn tại.
- Liveness phát hiện trạng thái cần restart container. Trỏ liveness vào dependency đang lỗi có thể tạo restart loop trong khi restart không sửa dependency.
- Probe là hợp đồng ứng dụng–nền tảng: endpoint trả 200 không tự chứng minh batch output hoặc database transaction đúng.

## 2. Đọc cấu hình

| Container field | Lý do/cách thay đổi hành vi |
|---|---|
| `startupProbe.httpGet.path`, `port` | Endpoint khởi động do ứng dụng phục vụ; phải đúng listener/port. |
| `readinessProbe.httpGet` | Điều kiện nhận traffic; endpoint không tồn tại sẽ giữ Pod không Ready. |
| `livenessProbe.httpGet` | Chỉ chọn lỗi mà restart có ích; không mặc định dùng cùng tiêu chí readiness. |
| Probe `periodSeconds`, `timeoutSeconds`, `failureThreshold` | Tần suất/timeout/ngưỡng; không xem phép nhân đơn giản là thời điểm restart chính xác tuyệt đối. |

## 3. Kiểm tra hiểu trước lab

1. Readiness fail nhưng liveness pass. Điều nào đúng? **A.** Bắt buộc restart container. **B.** Có thể Running nhưng không Ready. **C.** Xóa Deployment.
2. Database ngoài đang gián đoạn; API restart không sửa được DB. Đưa kiểm DB vào liveness có rủi ro gì? **A.** Tạo restart lặp không giải quyết gốc lỗi. **B.** Tự phục hồi DB. **C.** Tự tăng quota.

## 4. Thực hành và bằng chứng

1. Chuẩn bị app test có endpoint health điều khiển được, không credential; đọc code/endpoint trước khi dùng. Chạy baseline startup/readiness/liveness đạt.
2. Học viên tạo biến thể readiness sai path, giữ liveness đúng; quan sát Running/Ready/restart count. Sau đó sửa lại đúng và quan sát Ready phục hồi.
3. Ở lượt riêng, thử liveness sai với ngưỡng hữu hạn rồi khôi phục; thu lastState/restart count/Events. Không áp dụng thử nghiệm lên dịch vụ DE có dữ liệu.

**Đạt khi:** hai trường hợp cho bằng chứng khác nhau đúng như dự đoán và giải thích được vì sao. Chưa cần gọi Service; tác động traffic sẽ kiểm ở Bài 14.

## 5. Cần DevOps và giới hạn lab

- DE cung cấp ý nghĩa health endpoint, startup time và shutdown behavior; DevOps xác nhận chuẩn probes và cách quan sát rollout/restarts. Không yêu cầu họ đoán readiness từ cổng mở.
- Kubelet thực hiện probes trong lab và ngoài lab. Probe thành công không thay functional test, SLO hoặc xác nhận có dữ liệu đúng.

**Nguồn:** [Configure probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).
