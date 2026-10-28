# Bài 29 — PostgreSQL và hợp đồng lưu trữ

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](28-debug-va-observability.md) · [Tiếp](30-spark-native.md)

**Đầu vào:** storage, Secret, Service, NetworkPolicy và backup. **Đầu ra:** từ nhu cầu database, viết được yêu cầu nền tảng và kiểm persistence/restore thật.

## 1. Khối kiến thức

- Chọn DB trong cluster cho lab để thấy PVC/identity/lifecycle. DB managed hoặc ngoài cluster giảm phần vận hành trong Kubernetes nhưng vẫn cần network, credential, TLS và hợp đồng backup; không coi tự chạy DB luôn tốt hơn.
- Một instance PostgreSQL trên StatefulSet là lab persistence, không phải HA. Scale replicas không tự tạo primary/replica; HA cần cơ chế database/operator được thiết kế riêng.
- Dữ liệu phải nằm tại PGDATA bên trong mount persistent. Path/entrypoint/init env phụ thuộc image/version; không copy cấu hình image Bitnami sang image khác theo tên biến đoán trước.
- Init database lần đầu, migration schema, thay credential và backup/restore là các hoạt động khác nhau. `pg_isready` hoặc TCP connect không thay SQL functional check.

## 2. Đọc cấu hình

| Khối cấu hình | Quan hệ cần kiểm |
|---|---|
| StatefulSet, claim template và PGDATA/mount | Một instance/claim mới, không dùng PVC của khóa cũ; kiểm path theo image đã pin. |
| Service internal và app connection config | Name/namespace/port/database/user; không expose DB qua HTTP Ingress. |
| Secret refs / mechanism nạp credential | Cách server init và client đọc, không ghi password/URI có password vào Git hoặc argv. |
| Resources, probes và NetworkPolicy | Budget có headroom, readiness phù hợp, chỉ client cần thiết được vào. |
| Backup job/tool config | Đích tách nguồn, quyền backup/restore phù hợp, version tool tương thích server. |

## 3. Kiểm tra hiểu trước lab

1. PostgreSQL Pod đã thay và dữ liệu còn trên local-path. Đã chứng minh chịu mất node chưa? **A.** Rồi. **B.** Chưa. **C.** Rồi nếu dùng StatefulSet.
2. Đổi Secret init password trên database đã có dữ liệu có tự ALTER ROLE không? **A.** Có. **B.** Chỉ cần xóa Pod. **C.** Không được giả định; cần thao tác rotation đúng image/database.

## 4. Thực hành và bằng chứng

1. Học viên đọc và tự triển khai DB mới, client ở node khác khi placement cho phép; tạo fixture giả gồm hai order `(17, 12.50)` và `(42, 7.25)` với kiểu số thập phân, tổng kỳ vọng 19.75. Credential do học viên chuẩn bị theo quy trình an toàn.
2. Học viên thay chỉ DB Pod, giữ claim; truy vấn từ connection mới để xác nhận hai IDs/amounts và tổng. Mentor kiểm owner/UID, PGDATA/mount, claim/PV giữ nguyên và kết quả đã lọc.
3. Học viên dùng logical backup phù hợp, restore vào database/instance đích mới, giữ nguồn nguyên vẹn. Truy vấn đối chiếu schema, IDs, số dòng và tổng; ghi thời gian và vị trí bản sao. Không copy thô PGDATA đang chạy làm backup.

**Đạt khi:** persistence và restore được kiểm riêng; hợp đồng nêu rõ storage topology, downtime chấp nhận được, backup owner/RPO/RTO và phần HA chưa có. Không cần dựng PostgreSQL replication cluster.

## 5. Cần DevOps và giới hạn lab

- Cần xác nhận lựa chọn managed/in-cluster, class/IOPS/topology, network/TLS, cơ chế credential, backup/restore và quy trình nâng cấp DB. DE cung cấp dung lượng/tăng trưởng và patterns đọc/ghi.
- Đã restore hai dòng không là benchmark, PITR hoặc disaster recovery độc lập host. Chỉ báo đúng sự kiện đã thử và dữ liệu đã đối chiếu.

**Nguồn:** [PostgreSQL SQL dump](https://www.postgresql.org/docs/current/backup-dump.html), [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/).
