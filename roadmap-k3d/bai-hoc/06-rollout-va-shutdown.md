# Bài 06 — Rollout và dừng ứng dụng

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](05-probes.md) · [Tiếp](07-job-cronjob.md)

**Đầu vào:** Deployment và probes. **Đầu ra:** giải thích rollout bị kẹt và giới hạn “zero downtime”.

## 1. Khối kiến thức

- Đổi Pod template của Deployment tạo rollout/ReplicaSet mới; đổi riêng metadata ngoài template không đồng nghĩa thay mọi Pod. Scale replicas khác cập nhật phiên bản.
- RollingUpdate dùng `maxSurge` và `maxUnavailable` để cân bằng số Pod thêm và số Pod không available. Surge đòi capacity/quota; readiness mới fail có thể làm rollout dừng tiến triển.
- Khi kết thúc Pod, ứng dụng cần xử lý tín hiệu dừng, hoàn tất hoặc hủy công việc an toàn trong grace period. `preStop` dùng chung ngân sách grace period, không phải thời gian thưởng độc lập.
- Rollback Pod template không đảo ngược database migration hoặc dữ liệu mà phiên bản mới đã ghi. Không tuyên bố zero downtime chỉ từ rollout success.

## 2. Đọc cấu hình

| Field | Ý nghĩa/cạm bẫy |
|---|---|
| Deployment `spec.strategy.type` | `RollingUpdate` khác `Recreate`; chọn theo khả năng các phiên bản cùng tồn tại. |
| `spec.strategy.rollingUpdate.maxSurge`, `maxUnavailable` | Với 2 replicas, dùng số nguyên 1/0 để đọc rõ ngân sách trước khi học phần trăm. |
| `spec.progressDeadlineSeconds` | Báo rollout không tiến triển; không tự rollback ứng dụng. |
| PodSpec `terminationGracePeriodSeconds` | Cửa sổ shutdown; ứng dụng có thể bị buộc dừng khi hết hạn. |
| Container `lifecycle.preStop` | Hook trước stop signal; không đặt sleep dài rồi suy request chắc chắn không mất. |

## 3. Kiểm tra hiểu trước lab

1. `maxSurge=1`, `maxUnavailable=0`, Pod phiên bản mới không Ready. Vì sao rollout có thể chờ? **A.** Cần giữ số available cũ trong khi bản mới chưa đạt. **B.** Deployment không hỗ trợ đổi image. **C.** DNS chắc chắn hỏng.
2. Rollback image có tự khôi phục bảng đã bị migration xóa không? **A.** Có. **B.** Không. **C.** Có nếu tăng grace period.

## 4. Thực hành và bằng chứng

1. Học viên chạy app giả hai replicas, đổi một marker phiên bản trong Pod template; quan sát old/new ReplicaSets và available replicas theo thời gian.
2. Tạo bản rollout lỗi readiness có chủ đích, kiểm conditions/Events và phần cấu hình liên quan; học viên tự khôi phục template đúng. Không dùng lỗi image kéo dài để trộn nhiều nguyên nhân.
3. Với app test có xử lý SIGTERM, quan sát mốc bắt đầu/kết thúc shutdown trên đúng Pod. Không ghi “không mất request” nếu chưa có traffic test.

**Đạt khi:** nhận diện được rollout đang chờ ở bước nào, giải thích capacity cho surge và đưa ra yêu cầu shutdown cho một API hoặc worker DE.

## 5. Cần DevOps và giới hạn lab

- Cần quota/headroom cho rollout, policy deployment, cửa sổ bảo trì và trách nhiệm migration/rollback dữ liệu. DE cần nêu phiên bản có tương thích ngược không.
- Lab kiểm controller/probes/shutdown, chưa chứng minh availability dưới tải, connection draining của LB hoặc an toàn migration thực tế.

**Nguồn:** [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), [Pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/).
