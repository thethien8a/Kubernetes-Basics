# Bài 07 — Job, CronJob và retry

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](06-rollout-va-shutdown.md) · [Tiếp](08-resources.md)

**Đầu vào:** chọn loại workload và theo dõi UID/owner. **Đầu ra:** không đồng nhất Job Complete với kết quả nghiệp vụ đúng hoặc exactly-once.

## 1. Khối kiến thức

- Job quản lý Pod attempts để hoàn thành tác vụ. Retry có thể chạy lại code đã thực hiện một phần side effect; chương trình cần idempotency hoặc cơ chế commit/dedup phù hợp.
- `restartPolicy: Never` làm lỗi container kết thúc Pod; Job vẫn có thể tạo Pod khác nếu còn retry budget. Retry của ứng dụng, container và Job là các tầng khác nhau.
- CronJob tạo Jobs theo lịch; concurrency policy chỉ áp dụng các Jobs do cùng CronJob quản lý, không khóa mọi writer trong hệ thống. Scheduling không phải bảo đảm exactly-once.
- `suspend` ngừng các lượt lịch tiếp theo, không mặc định dừng Job đã chạy. History/TTL dọn object khác với retention của dữ liệu/log bên ngoài.

## 2. Đọc cấu hình

| Field | Ý nghĩa/lựa chọn |
|---|---|
| Job `spec.backoffLimit`, `activeDeadlineSeconds` | Giới hạn retry và thời gian Job; dùng budget nhỏ cho tác vụ giả, không thay điều tra lỗi gốc. |
| Job `spec.template.spec.restartPolicy` | Chọn `Never` ban đầu để dễ phân biệt Pod attempts. |
| Job `spec.ttlSecondsAfterFinished` | Để chưa khai báo trong lúc cần giữ evidence; không dùng TTL như cơ chế xóa dữ liệu output. |
| CronJob `spec.schedule`, `timeZone` | Giờ/lịch theo timezone được chỉ rõ và API hỗ trợ; tránh nhầm giờ cluster với giờ Việt Nam. |
| CronJob `spec.concurrencyPolicy`, `suspend` | `Forbid` tránh overlap theo CronJob đó; suspend dùng để dừng bài an toàn. |

## 3. Kiểm tra hiểu trước lab

1. Pod của Job dùng `Never` thoát lỗi, `backoffLimit` vẫn còn. Điều nào có thể xảy ra? **A.** Job tạo Pod attempt mới. **B.** Chắc chắn không retry. **C.** Chuyển thành Deployment.
2. `Forbid` có ngăn một Job thủ công ghi cùng dữ liệu không? **A.** Có. **B.** Chỉ khi cùng image. **C.** Không, cần cơ chế phối hợp ở phạm vi dữ liệu.

## 4. Thực hành và bằng chứng

1. Chạy Job tính tổng dãy 1–10, kỳ vọng độc lập là 55; kiểm đúng Job UID, Pod owner, exit code và kết quả.
2. Chạy Job giả thoát lỗi với retry/deadline hữu hạn; quan sát attempts và status, không dùng số lần tuyệt đối làm hợp đồng trong mọi điều kiện lỗi.
3. Sau review Job, chạy CronJob ngắn hạn có task lâu hơn chu kỳ để quan sát `Forbid`; học viên tự suspend và kiểm không tạo lượt mới ngoài khoảng quan sát, vẫn phân biệt Job đang chạy. Không kết nối dữ liệu thật.

**Đạt khi:** có bằng chứng đúng lượt chạy, hiểu ba tầng retry và giải thích cách thiết kế output khi chạy lại. Giữ evidence tới review rồi mới thống nhất dọn.

## 5. Cần DevOps và giới hạn lab

- Cần namespace/quota, deadline/retention policy, log access và cách xử lý missed schedules; DE chịu trách nhiệm tính an toàn của phép ghi khi rerun.
- K3s cung cấp controller chuẩn; nó không tự biết checkpoint dữ liệu của pipeline. Lịch chạy được vài phút chưa chứng minh SLA hoặc exactly-once.

**Nguồn:** [Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/).
