# Bài 04 — Pod, controller và loại workload

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](03-doc-manifest.md) · [Tiếp](05-probes.md)

**Đầu vào:** đọc được Pod template/owner. **Đầu ra:** chọn loại workload theo vòng đời và phân biệt restart container với tạo Pod mới.

## 1. Khối kiến thức

- Pod là đơn vị scheduling; các container trong cùng Pod cùng node, chia sẻ mạng Pod và có thể chia sẻ volumes. Hai container trong một Pod không được phân sang hai nodes.
- Kubelet có thể restart container trong Pod theo policy. Controller như ReplicaSet tạo Pod thay thế để giữ desired state; Pod đơn lẻ bị xóa không có controller tự tạo lại.
- Deployment phù hợp các replicas thay thế được; StatefulSet phục vụ stable identity/storage association; Job quản lý tác vụ tới hoàn thành; CronJob tạo Jobs theo lịch; DaemonSet đặt Pod trên các node đủ điều kiện. Không loại nào tự hiểu nghiệp vụ hoặc bảo đảm dữ liệu đúng.
- Init container thông thường phải hoàn thành trước app containers. “Ứng dụng đang chờ dependency” khác “scheduler chưa tìm được node”.

## 2. Đọc cấu hình

| Field | Hành vi cần hiểu |
|---|---|
| PodSpec `containers[]`, `initContainers[]` | Đơn vị tiến trình và thứ tự init; thêm container không thêm node. |
| PodSpec `restartPolicy` | Chính sách restart container; Deployment dùng `Always`, Job cần `Never` hoặc `OnFailure`. |
| Deployment `spec.replicas` | Controller giữ số replicas, không tự tạo HA cho database. |
| Pod `metadata.ownerReferences` | Bằng chứng ai quản lý Pod; không suy chỉ từ tên. |
| Container `command`, `args` | Tiến trình và tham số; lệnh kết thúc trong Deployment có thể dẫn tới restart lặp. |

## 3. Kiểm tra hiểu trước lab

1. Tác vụ tính tổng chạy xong rồi thoát thành công nên ưu tiên loại nào? **A.** Job. **B.** DaemonSet. **C.** Deployment chỉ để luôn có Pod Running.
2. Xóa Pod do ReplicaSet quản lý, Pod bù có UID mới. Đây là gì? **A.** Container restart trong Pod cũ. **B.** Kubernetes phục hồi RAM của tiến trình cũ. **C.** Controller tạo object mới theo template.

## 4. Thực hành và bằng chứng

1. Dùng một Pod đơn lẻ và một Deployment nhỏ với image đã kiểm ARM64. Học viên dự đoán rồi tự xóa từng Pod trong phạm vi bài.
2. So danh sách object/UID/owner trước và sau; Deployment có Pod thay thế, Pod đơn lẻ không tự trở lại. Giữ dữ liệu hoàn toàn disposable, chưa có PVC.
3. Phân loại bốn yêu cầu: HTTP API, batch transform, lịch chạy hằng ngày, agent trên nodes. StatefulSet mới đọc định hướng, chưa triển khai database.

**Đạt khi:** chứng minh khác biệt Pod replacement/restart và chọn workload có lý do; không dùng một snapshot Running để suy đã có recovery.

## 5. Cần DevOps và giới hạn lab

- Cần biết loại workload/namespace nào được phép, node pool nào dùng cho batch/service và có giới hạn thời gian chạy không.
- Controller là cơ chế Kubernetes, không đặc quyền OrbStack. Controller tạo Pod mới không bảo đảm capacity, dependency, state hay exactly-once của ứng dụng.

**Nguồn:** [Workload management](https://kubernetes.io/docs/concepts/workloads/controllers/), [Pod lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/).
