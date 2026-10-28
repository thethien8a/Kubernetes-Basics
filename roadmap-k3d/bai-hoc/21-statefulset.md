# Bài 21 — StatefulSet và danh tính dữ liệu

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](20-storage-multi-node.md) · [Tiếp](22-backup-va-reclaim.md)

**Đầu vào:** Service/DNS, PVC và topology. **Đầu ra:** hiểu stable identity/storage association, không xem StatefulSet là database HA tự động.

## 1. Khối kiến thức

- StatefulSet duy trì ordinal/name ổn định cho member và gắn member với claim tương ứng khi dùng volumeClaimTemplates. Pod được tạo lại có UID mới, không phục hồi process memory cũ.
- Headless Service không cấp ClusterIP thông thường; DNS có thể trả địa chỉ member phù hợp. `serviceName`, selector và readiness ảnh hưởng discovery; tên ổn định không có nghĩa IP bất biến.
- `volumeClaimTemplates` tạo claim riêng theo member, không một thư mục tự nhân bản. Hai PostgreSQL độc lập không thành replication cluster chỉ bằng `replicas: 2`.
- Thứ tự tạo/cập nhật và retention của PVC phải đọc từ policy/version; không mặc định xóa StatefulSet hoặc scale-down sẽ xóa mọi claim.

## 2. Đọc cấu hình

| Field | Ý nghĩa/lựa chọn |
|---|---|
| StatefulSet `spec.serviceName`, `selector`, `template.metadata.labels` | Nối governing Service và nhóm Pod. |
| Service `spec.clusterIP: None`, `selector` | Headless discovery; không nhầm với Service không tồn tại. |
| StatefulSet `spec.volumeClaimTemplates[]` | Template claim cho từng member; volumeMount name cần khớp tên template. |
| `spec.podManagementPolicy`, `updateStrategy` | Đọc defaults và trình tự, không tùy tiện chuyển Parallel để chữa readiness sai. |
| `spec.persistentVolumeClaimRetentionPolicy` | Đọc hỗ trợ và lựa chọn Retain/Delete cho scale/delete; không thử Delete lên data cần giữ. |

## 3. Kiểm tra hiểu trước lab

1. Hai member có hai PVC riêng. Dữ liệu ghi ở member 0 có tự xuất hiện ở member 1 không? **A.** Có vì cùng StatefulSet. **B.** Không nếu ứng dụng/backend không có cơ chế đồng bộ. **C.** Chỉ cần cùng mountPath.
2. Member được tạo lại cùng tên nhưng IP thay đổi có phá vỡ khái niệm stable identity không? **A.** Có. **B.** IP không thể đổi. **C.** Không, cần phân biệt tên/discovery với địa chỉ Pod.

## 4. Thực hành và bằng chứng

1. Dùng hai member ứng dụng marker nhẹ, không dùng database để tránh ngầm tạo hai writer. Học viên kiểm từng Pod/PVC/PV và ghi marker riêng cho mỗi member.
2. Học viên thay một Pod, giữ StatefulSet/claims; kiểm tên member giữ, UID đổi, claim vẫn đúng và marker cũ còn. Kiểm DNS từ client mới, cân nhắc cache khi quan sát.
3. So marker của member còn lại để chứng minh hai nguồn độc lập. Đọc retention policy và dự đoán scale-down, chưa bắt xóa claim.

**Đạt khi:** giải thích được identity, discovery và storage association bằng evidence; bác bỏ giả định “hai replicas = database HA”.

## 5. Cần DevOps và giới hạn lab

- Cần class/topology phù hợp, DNS, policy giữ/xóa claim và nếu dùng database cluster thì cơ chế replication/failover/operator được hỗ trợ.
- StatefulSet là controller Kubernetes; consistency, leader election và backup là hợp đồng khác. Local-path không trở thành shared storage chỉ vì được dùng trong StatefulSet.

**Nguồn:** [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/), [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/).
