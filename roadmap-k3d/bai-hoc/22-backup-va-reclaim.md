# Bài 22 — Reclaim, mở rộng và backup/restore

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](21-statefulset.md) · [Tiếp](23-config-secret.md)

**Đầu vào:** volume lifecycle/topology; chỉ dùng dữ liệu giả. **Đầu ra:** mô tả được mất dữ liệu chấp nhận được, nơi lưu bản sao và cách kiểm restore.

## 1. Khối kiến thức

- `Delete`/`Retain` là reclaim behavior sau khi claim được giải phóng, tùy loại volume/provisioner. Retain giữ nguồn storage để quản lý tiếp, không tạo thêm bản sao và không chống lỗi disk nguồn.
- Expansion cần class cho phép và driver/backend hỗ trợ; tăng số yêu cầu không chắc disk/filesystem đã mở rộng. Không xem giảm size claim là cách thu nhỏ volume an toàn.
- Backup cần dữ liệu nhất quán, nơi lưu, retention, quyền và kiểm restore. Snapshot volume không mặc định là application-consistent hoặc bản sao ở failure domain khác.
- RPO/RTO là mục tiêu được thỏa thuận. Có file backup chưa đủ; restore vào đích mới và đối chiếu nội dung mới chứng minh được một phần khả năng phục hồi.

## 2. Đọc cấu hình

| Field/config | Điều cần hiểu |
|---|---|
| StorageClass `reclaimPolicy` → PV `spec.persistentVolumeReclaimPolicy` | PV động nhận policy khi provision; đổi class không tự cập nhật mọi PV cũ. |
| StorageClass `allowVolumeExpansion` | Một điều kiện, chưa đủ nếu driver không hỗ trợ. |
| PVC `spec.resources.requests.storage`, `status.capacity`, conditions | Desired size khác capacity/status đã quan sát; còn kiểm filesystem khi có expansion. |
| Backup schedule/destination/retention | Cấu hình của công cụ/ứng dụng; không có field PVC phổ quát tự giải quyết mọi backup. |

## 3. Kiểm tra hiểu trước lab

1. PV Retain nhưng disk chứa dữ liệu hỏng. Retain có bản sao độc lập để phục hồi không? **A.** Có. **B.** Không chỉ nhờ policy đó. **C.** Có nếu StatefulSet có hai replicas.
2. Copy trực tiếp thư mục của database đang ghi có chắc là backup nhất quán không? **A.** Chắc chắn. **B.** Chỉ cần đổi tên file. **C.** Không, cần cơ chế backup/quiesce phù hợp ứng dụng.

## 4. Thực hành và bằng chứng

1. Đọc policy của volume lab và lập bảng hậu quả khi xóa Pod, PVC, node container hoặc host disk. Những tình huống chưa thử ghi rõ là dự đoán, không thực hiện xóa dữ liệu để đủ bảng.
2. Với bộ file tĩnh giả, học viên dừng writer, tạo bản backup ở vị trí tách khỏi volume nguồn và khôi phục vào claim/đường đích mới. Giữ nguồn nguyên vẹn; so tên file, bytes/checksum và nội dung kỳ vọng.
3. Ghi thời điểm backup/restore, nơi bản sao nằm và failure domain chung còn lại. Expansion chỉ đọc khả năng class hiện có; nếu không hỗ trợ, bài không yêu cầu cài CSI mới. Backup database thật sẽ kiểm ở Bài 29.

**Đạt khi:** restore bộ dữ liệu tĩnh đúng vào đích khác, nêu được giới hạn consistency và vị trí backup. Không gọi bản sao trên cùng Mac là disaster recovery cho mất Mac.

## 5. Cần DevOps và giới hạn lab

- Cần reclaim/expansion policy, backup mechanism/destination, retention, encryption/access, RPO/RTO, người kiểm restore và trách nhiệm ứng dụng trong quiesce/backup.
- Với managed storage phải hỏi snapshot được lưu ở đâu và bảo vệ trước lỗi nào; với on-prem cũng không suy “storage có replication” nghĩa đã có backup chống xóa nhầm.

**Nguồn:** [PV reclaim và expansion](https://kubernetes.io/docs/concepts/storage/persistent-volumes/), [Volume snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/).
