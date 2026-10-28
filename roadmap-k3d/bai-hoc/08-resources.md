# Bài 08 — Requests, limits và sức chứa

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](07-job-cronjob.md) · [Tiếp](09-node-affinity.md)

**Đầu vào:** lifecycle và Pod template. **Đầu ra:** phân biệt scheduling, runtime enforcement và đo tài nguyên thực tế.

## 1. Khối kiến thức

- Scheduler xét requests và các ràng buộc để chọn một node phù hợp; không gom RAM rảnh của nhiều node để chạy một Pod lớn. Allocatable khác capacity và khác RAM đang rảnh.
- CPU request không phải CPU usage hoặc giới hạn tối đa. CPU limit có thể gây throttling; memory limit vượt quá có thể dẫn tới OOM kill. Không diễn giải mọi restart thành thiếu RAM.
- Requests/limits thường đặt theo container; phải tính các container/init/sidecar và overhead có liên quan khi đánh giá Pod. Không cộng limit rồi gọi đó là mức dùng hiện tại.
- Metrics API cung cấp số đo tại thời điểm/khoảng quan sát; không có metrics không nghĩa usage bằng 0. Trên k3d, nhiều node cùng chia sẻ ngân sách runtime/host.

## 2. Đọc cấu hình

| Field hoặc dữ liệu quan sát | Ý nghĩa/cạm bẫy |
|---|---|
| Container `resources.requests.cpu`, `memory` | `250m` là 0,25 CPU; `512Mi` là lượng bộ nhớ, không phải 512 MB thập phân. |
| Container `resources.limits.cpu`, `memory` | Cần phân biệt giới hạn với request và với heap của JVM. |
| Node `status.allocatable` | Ngân sách scheduler nhìn thấy; node-container không tạo thêm tài nguyên vật lý. |
| Pod conditions/Events và container `lastState` | Phân biệt `FailedScheduling`, termination reason và exit code. |

## 3. Kiểm tra hiểu trước lab

1. Hai node mỗi node còn đủ 2Gi theo requests; Pod đơn cần 3Gi. Có ghép thành 4Gi để schedule không? **A.** Có. **B.** Không. **C.** Có nếu dùng Deployment.
2. Pod Pending vì `Insufficient memory`, chưa có container chạy. Giảm CPU limit có trực tiếp sửa nguyên nhân này không? **A.** Luôn có. **B.** Chỉ trên ARM64. **C.** Không, phải xem memory request và node khả dụng.

## 4. Thực hành và bằng chứng

1. Lập bảng allocatable, requests đã khai báo và usage nếu có; ghi rõ các cột không tương đương nhau.
2. Học viên tạo workload giả có memory request lớn hơn khả năng từng node nhưng còn đúng schema; quan sát FailedScheduling. Không chạy chương trình ăn hết RAM để tạo tình huống.
3. Học viên chỉnh request có lý do và tạo/rollout lại, kiểm Pod được gán node và Ready. Với throttling/OOM, đọc ca mẫu trước; thử tải giới hạn chỉ khi đã có budget an toàn, không bắt buộc để đạt bài.

**Đạt khi:** nối được cấu hình request với bằng chứng Pending/recovery và giải thích vì sao metrics, heap và limit khác nhau.

## 5. Cần DevOps và giới hạn lab

- Cần node sizes/pools, allocatable, quota, resource defaults và Metrics API hoặc nơi xem usage; DE cung cấp đặc tính tải, concurrency và peak đã đo.
- Kubernetes không suy request tối ưu cho pipeline. Lab nhỏ không benchmark production; số CPU/RAM cộng từ các k3d nodes không là capacity vật lý độc lập.

**Nguồn:** [Resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/).
