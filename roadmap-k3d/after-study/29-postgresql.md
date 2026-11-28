# Tổng kết Bài 29 — PostgreSQL và hợp đồng lưu trữ

[Bài học gốc](../bai-hoc/29-postgresql.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Scaffold](../thuc-hanh/29-postgresql/) · [Bài tiếp theo](../bai-hoc/30-spark-native.md)

**Đã học xong theo xác nhận/phạm vi học viên chọn ngày 2026-11-27, giờ Việt Nam (`Asia/Ho_Chi_Minh`).** Triển khai DB + client khác node, thay Pod DB giữ PVC và toàn bộ 10/10 câu kiểm tra hiểu/review cuối đều đạt. Ở Bước 3, bản dump `pg_dump -Fc` đã tạo và kiểm TOC/SHA-256 thành công, `pg-target` đã dựng tách biệt nguồn, nhưng học viên chọn dừng sau khi nắm ý tưởng để sang chốt hợp đồng nền tảng và review cuối — chưa chạy `pg_restore` hoàn tất và truy vấn xác nhận bảng trên `orders_restored`. Vì vậy Bài 29 không tích checkbox nghiệm thu đầy đủ và không giao phần restore còn lại thành việc phải làm bù.

## 1. Lý thuyết trọng tâm và nhóm `pg_*`

- **Managed DB vs tự chạy in-cluster:** chạy PostgreSQL trên `StatefulSet` trong lab giúp quan sát trực tiếp PVC, `PGDATA` và vòng đời Pod; ngoài thực tế không mặc định tự chạy DB luôn tốt hơn Managed DB (RDS, Cloud SQL…). Dù chọn Managed DB, DE và DevOps vẫn phải xử lý đường mạng/NetworkPolicy egress, DNS, TLS/CA trust, cơ chế cấp/rotate credential và hợp đồng backup/restore.
- **`StatefulSet` đơn lẻ ≠ HA:** `StatefulSet` cấp tên Pod ổn định và PVC riêng theo ordinal (`pg-source-0` → `pgdata-pg-source-0`), không tự tạo streaming replication, bầu Primary hay failover. Tăng `spec.replicas: 2` trên `StatefulSet` PostgreSQL thông thường chỉ tạo hai instance độc lập trên hai volume rời nhau.
- **`PGDATA` và đường dẫn mount theo image/version:** dữ liệu chỉ bền vững qua thay Pod khi `PGDATA` nằm bên trong `volumeMount` gắn với PVC. Không đoán tên biến hoặc đường dẫn từ chart/image khác (như Bitnami `POSTGRESQL_*`). Theo tài liệu official image `postgres`, bản **17 trở xuống** mặc định `PGDATA` và `VOLUME` ở `/var/lib/postgresql/data` (mount ở `/var/lib/postgresql` sẽ rơi vào anonymous volume), còn bản **18 trở lên** đổi `PGDATA` mặc định thành `/var/lib/postgresql/<major>/docker` và `VOLUME` sang `/var/lib/postgresql`. Trong lab `17.12-alpine`, đặt `PGDATA=/var/lib/postgresql/data/pgdata` bên trong mount `/var/lib/postgresql/data` để tránh xung đột `lost+found` ở gốc mount khi `initdb` chạy.
- **Tách bốn hoạt động vận hành:**
  1. **Init lần đầu (`initdb`):** `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` chỉ chạy khi `PGDATA` đang trống; sửa `Secret` khi PVC đã có dữ liệu không tự `ALTER ROLE`.
  2. **Migration schema:** thay đổi bảng/cột trên DB sống; rollback image không hoàn tác dữ liệu đã commit.
  3. **Rotation credential:** phải cập nhật mật khẩu trong PostgreSQL đồng bộ với `Secret` và rollout/reconnect client.
  4. **Backup/restore & kiểm tra sức khỏe:** cấm `tar`/`cp` thô thư mục `PGDATA` đang chạy vì dễ lệch thời điểm giữa file bảng (`base/`) và nhật ký giao dịch (`pg_wal/`). `pg_isready` chỉ kiểm listener cổng `5432`, không kiểm bảng hay kết quả truy vấn SQL.

| Nhóm `pg_*` (đã tách theo câu hỏi học viên) | Thành phần cụ thể | Vai trò chính |
|---|---|---|
| **CLI trong image `postgres`** | `psql`, `pg_isready`, `pg_dump`, `pg_restore`, `pg_dumpall`, `pg_basebackup` | `psql` chạy SQL; `pg_isready` ping cổng DB (probe); `pg_dump` xuất 1 DB; `pg_restore` nạp file `-Fc`; `pg_dumpall` xuất cả cluster/roles và `pg_basebackup` sao lưu vật lý an toàn (chỉ học khái niệm). |
| **Thư mục / biến đĩa** | `PGDATA`, `base/`, `pg_wal/` | Thư mục gốc dữ liệu, file lưu bảng và sổ nhật ký Write-Ahead Log; chụp không đồng bộ hai phần này làm hỏng bản sao. |
| **Tên tự đặt trong lab** | `pg-source`, `pg-target`, `pg-svc`, `pg-headless`, `pg-client` | Tên resource Kubernetes đặt trong manifest, đổi tên vẫn chạy tương tự nếu giữ đúng selector/ref. |

## 2. Cấu hình và liên kết resource đã đọc

| Khối cấu hình | Field / giá trị chính | Quan hệ và hành vi khi đổi/sai |
|---|---|---|
| `StatefulSet` `pg-source` & `pg-target` | `serviceName`, `replicas: 1`, `terminationGracePeriodSeconds: 30`, `nodeSelector: k3d-de-k3d-agent-0`, `volumeClaimTemplates: pgdata` (`256Mi`, `local-path`, `ReadWriteOnce`) | Ghim DB trên `agent-0` tách với `pg-client` trên `agent-1`; `terminationGracePeriodSeconds: 30` giúp PostgreSQL shutdown sạch khi thay Pod. Sai `mountPath`/`PGDATA` làm mất dữ liệu khi thay Pod. |
| `Secret` refs server vs client | Server dùng `POSTGRES_PASSWORD`; client `libpq` dùng `PGPASSWORD` cùng trỏ `lesson29-pg-auth` key `password` | Official `postgres` chỉ bật `trust` cho `localhost` trong cùng container, bắt buộc mật khẩu từ Pod khác. Đặt nhầm `POSTGRES_PASSWORD` cho `pg-client` sẽ không tự xác thực được. Tắt `automountServiceAccountToken` và `enableServiceLinks` trên cả DB lẫn client. |
| `Service` nội bộ | `pg-headless` (`clusterIP: None`), `pg-svc` (`ClusterIP: 5432`), tách cặp `pg-target-headless` / `pg-target-svc` (`role: db-target`) | Không dùng HTTP `Ingress` cho giao thức TCP `5432` của PostgreSQL. Nếu `pg-target` dùng trùng nhãn `role: db`, `pg-svc` sẽ gộp cả nguồn lẫn đích vào chung `EndpointSlice`. |
| Probes & Resources | `startupProbe` (`12 × 5s`), `readinessProbe` (`5s`), `livenessProbe` (`10s`) chạy `pg_isready -h 127.0.0.1 -p 5432`; DB `100m/128Mi` → `500m/256Mi`, client `25m/32Mi` → `100m/64Mi` | `startupProbe` ngăn kubelet kill Pod giữa lúc `initdb`. `pg_isready` vẫn xanh dù bảng `orders` bị xóa. |
| `NetworkPolicy` | `allow-pg-client-only` (`role: db`), `allow-pg-target-client-only` (`role: db-target`), `policyTypes: [Ingress]`, chỉ nhận `role: client` trên `TCP/5432` | Khóa truy cập DB trong cùng namespace; nếu client ở namespace khác cần ghép `namespaceSelector` + `podSelector` trong **cùng một phần tử `from`** (AND) và mở egress tương ứng phía client nếu client bị isolate egress. |

## 3. Thực hành, bằng chứng runtime và sự cố đã xử lý

- **Phạm vi & phiên bản:** context `k3d-de-k3d`, namespace `lesson29-pg` (`cb93f2a3-a849-4e4f-98d4-4ae8ca1e8141`, `Active`), client `/usr/local/bin/kubectl` `v1.33.9`, server `v1.33.6+k3s1`, 3 node `arm64` đều `Ready`, `local-path` (`Delete`, `WaitForFirstConsumer`, `allowVolumeExpansion=false`). Image chốt `postgres:17.12-alpine@sha256:f9cf3e1f0066f0eb0c48707d864f0ac5941e9ff454a072077d97a4d278d07d73` (đối chiếu ARM64 qua Docker Hub API); 6 file [scaffold](../thuc-hanh/29-postgresql/) qua strict client dry-run. Credential sinh qua `openssl rand -hex 16 | tr -d '\n'` nạp qua `/dev/stdin`, không lưu vào Git hoặc argv.

| Mốc (giờ Việt Nam) | Bằng chứng đã đối chiếu |
|---|---|
| **10:32:57 ngày 26/11** — Bước 1 baseline | `pg-source-0` (`bf2318da-b954-4f1a-b82d-849cc7d0d15c`, `10.42.3.118`) trên `agent-0` và `pg-client` (`1375721b-378e-4942-a47e-a784f4ec2d8a`, `10.42.1.116`) trên `agent-1` đều `Running`/`Ready`, `restarts=0`. `PG_VERSION=17`, `/var/lib/postgresql/data` mount `rw` từ `PVC/pgdata-pg-source-0` → `PV/pvc-38b36a34…` (`affinity=agent-0`). Truy vấn từ `pg-client` tạo và đọc bảng `orders` (`id integer`, `amount numeric(10,2)`): `(17, 12.50)`, `(42, 7.25)`, `row_count=2`, `total_amount=19.75`. |
| **10:40:57 ngày 26/11** — Bước 2 thay Pod DB | Học viên xóa riêng `pod/pg-source-0` (không `--force`, giữ PVC). Pod mới khởi động `2026-11-26T03:38:50Z`, UID mới `de8cf324-615a-4a33-8117-51850e74156c`, IP mới `10.42.3.119`, `OWNER_UID` giữ `StatefulSet/pg-source`, `RESTARTS=0`. Log ghi nhận shutdown sạch `03:38:49 UTC` và `Skipping initialization`. `PVC`/`PV` và `pg-svc` giữ nguyên UID; `EndpointSlice` tự cập nhật sang `10.42.3.119`/`de8cf324…`. Connection mới từ `pg-client` vẫn đọc `(17, 12.50)`, `(42, 7.25)`, `row_count=2`, `total_amount=19.75`. |
| **23:37–23:40 ngày 26/11**, kiểm lại **08:46:11 & 09:44:52 ngày 27/11** — Bước 3.1–3.2 & kiểm chốt | Tại `~/.local/share/k8s-practice/lesson29/backup/` (ngoài Git): `orders_db.dump` (`1622` byte, SHA-256 `dfc3ed6f2974a5b236e68fc32b975182a6ed859e2dd598a089764dc8182f01c6`, `shasum -a 256 -c` trả `OK`), `backup_started=2026-11-26T23:37:07+0700`, `backup_verified=2026-11-26T23:37:08+0700`. `pg_restore -l` xác nhận `Format: CUSTOM`, `gzip`, `17.12`, gồm `TABLE public orders`, `TABLE DATA public orders`, `CONSTRAINT public orders orders_pkey`. `pg-target-0` (`b241a665…`, `10.42.3.121`, `agent-0`) `Ready=True`/`RESTARTS=0`, `PG_VERSION=17`, PVC/PV/Service/EndpointSlice/NetworkPolicy riêng biệt nguồn. |
| **Chưa hoàn tất (theo phạm vi học viên chọn)** — Bước 3.3–3.4 | `restore-times.txt` mới ghi `restore_started=2026-11-26T23:40:11+0700` (chưa có `restore_verified`). Kiểm tra SQL chỉ đọc lúc **09:44:52 ngày 27/11** trên `pg-target-svc / orders_restored` báo `Did not find any relations.` / `relation "orders" does not exist`. Nguồn `pg-svc / orders_db` còn nguyên vẹn (`17 \| 12.50`, `42 \| 7.25`, `row_count=2`, `total_amount=19.75`). |

| Tài nguyên giữ lại | UID / liên kết đã đối chiếu tại snapshot chốt 27/11 |
|---|---|
| Secret `lesson29-pg-auth` | `3ee49e03-be43-4231-920e-070df4e51d1a`, `Opaque`, `key=password` (không đọc giá trị) |
| StatefulSet `pg-source` / Pod `pg-source-0` | `e2a6c112-0d1f-4ec1-8313-053c94635d58` / `de8cf324-615a-4a33-8117-51850e74156c` (`10.42.3.119`, `agent-0`) |
| PVC `pgdata-pg-source-0` → PV `pvc-38b36a34…` | PVC `38b36a34-a123-4764-a004-fcefd719b75c` → PV `c8a9d59e-e887-4b3a-9efb-00b650859287` (`Delete`, `agent-0`) |
| Service `pg-svc` / `pg-headless` / Slice `pg-svc-wbxs4` | `33f548a7…` (`10.43.75.178`) / `1413f761…` (`None`) / `87819847…` (`10.42.3.119`, `READY=true`) |
| StatefulSet `pg-target` / Pod `pg-target-0` | `8bee4fc1-8391-4577-9433-67b319a77051` / `b241a665-4576-4846-8504-671c4bbf2239` (`10.42.3.121`, `agent-0`) |
| PVC `pgdata-pg-target-0` → PV `pvc-30171239…` | PVC `30171239-3ff6-4fed-baf8-b03dc52e05c7` → PV `f8b07d55-91cb-48d2-b619-74814256be8a` (`Delete`, `agent-0`) |
| Service `pg-target-svc` / `pg-target-headless` / Slice `pg-target-svc-p9fjk` | `d1bc91eb…` (`10.43.255.233`) / `e7ceea29…` (`None`) / `96f19f73…` (`10.42.3.121`, `READY=true`) |
| NetworkPolicy `allow-pg-client-only` / `allow-pg-target-client-only` | `4c468198-d003-4c76-bac1-47a3eee5bda7` / `5b49b112-908e-4d0b-9f53-b7d2985d2277` |
| Pod `pg-client` | `1375721b-378e-4942-a47e-a784f4ec2d8a` (`10.42.1.116`, `agent-1`, `restartPolicy: Never`, `sleep 86400`) |

- **Sự cố shell đã xử lý trong lab:** hai lần dán lệnh có khoảng trắng sau dấu `\` khiến `k29 apply \ ` bị ngắt dòng, và hàm `k29()` bị rớt `"$@"` thành `k29:3: command not found: pg-client` kèm text `kubectl controls...` lọt vào `orders_db.dump.part`. Cơ chế ghi `.part` + `set -e` đã chặn không cho đổi tên thành `orders_db.dump`; sửa bằng hàm `k29()` một dòng và chạy lại trong `roadmap-k3d`.

## 4. Tái quan sát chỉ đọc

Các lệnh kiểm tra không làm thay đổi workload hay dữ liệu; **không** in giá trị `Secret` và không chạy lại lệnh xóa Pod hoặc restore để review. Lưu ý `pg-client` dùng `sleep 86400` nên có thể chuyển `Succeeded` sau 24 giờ kể từ lúc tạo.

```bash
k29() { /usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" --context k3d-de-k3d --namespace lesson29-pg --request-timeout=8s "$@"; }

k29 get pods,pvc -o wide
k29 get endpointslices -l 'kubernetes.io/service-name in (pg-svc,pg-target-svc)' \
  -o 'custom-columns=SVC:.metadata.labels.kubernetes\.io/service-name,NAME:.metadata.name,ADDR:.endpoints[*].addresses[*],READY:.endpoints[*].conditions.ready,TARGET_UID:.endpoints[*].targetRef.uid'
k29 get secret lesson29-pg-auth -o 'go-template=type={{.type}}{{range $k, $_ := .data}} key={{$k}}{{end}}{{"\n"}}'
(cd "$HOME/.local/share/k8s-practice/lesson29/backup" && shasum -a 256 -c orders_db.dump.sha256 && cat backup-times.txt restore-times.txt)
```

Nhìn `READY=true` và hai `TARGET_UID` tách biệt trên `pg-svc` vs `pg-target-svc`, `type=Opaque key=password`, và `orders_db.dump: OK`. Khi `pg-client` đang `Running`, có thể đọc lại nguồn bằng `k29 exec pg-client -c psql -- psql -h pg-svc -p 5432 -U de_app -d orders_db -X -c 'SELECT id, amount FROM orders ORDER BY id;'` (kỳ vọng `(17, 12.50)`, `(42, 7.25)`).

## 5. Review, hợp đồng nền tảng PostgreSQL và giới hạn

- **Checkpoint & review đạt 10/10:** Khối 1 (`1B, 2C, 3B`), Khối 2 (`1B, 2B, 3B`), Khối 3 (`1B, 2A`), Review cuối (`1B, 2B`: ưu tiên Managed PostgreSQL khi cần Multi-AZ + PITR + RPO ≤ 5 phút và chưa có người vận hành Operator, vẫn phải trao đổi NetworkPolicy/TLS/credential/RPO-RTO; báo cáo trung thực ranh giới giữa persistence thay Pod đã chạy với backup/restore, node loss, HA, PITR và DR chưa chứng minh).

| Hạng mục hợp đồng | DE cung cấp / tự kiểm | Cần DevOps cung cấp / xác nhận |
|---|---|---|
| **Mô hình & HA** | Môi trường, namespace client, downtime chấp nhận được. | Chọn Managed DB hay in-cluster Operator; thiết kế Multi-AZ, replication, failover và PDB. |
| **Dung lượng & hiệu năng** | Kích thước hiện tại, tốc độ tăng trưởng, pattern đọc/ghi, requests/limits. | Node pool, quota, StorageClass hỗ trợ IOPS/throughput và `allowVolumeExpansion`. |
| **Lưu trữ & topology** | Khớp `PGDATA` với persistent mount theo đúng image/version. | `StorageClass`, CSI driver, giới hạn topology (local vs Zone), `reclaimPolicy` (`Retain` cho prod). |
| **Mạng, DNS & TLS** | Gọi qua `Service`/FQDN `TCP/5432` (không dùng HTTP `Ingress`), mở ingress tối thiểu từ client. | DNS, VPC/firewall, enforcement của `NetworkPolicy` (ingress/egress) và TLS/CA trust. |
| **Credential & quyền** | Không lưu password/URI vào Git/argv; tách `POSTGRES_PASSWORD` (init) vs `PGPASSWORD` (client). | Secret manager, mã hóa lúc lưu trữ, quy trình rotate mật khẩu (`ALTER ROLE` đồng bộ client) và phân quyền role SQL. |
| **Backup, PITR & nâng cấp** | Mục tiêu RPO/RTO, schema migration tương thích hai phiên bản, kiểm tra SQL sau restore. | Backup owner, lưu bản sao tách miền lỗi, WAL archiving (PITR), lịch diễn tập restore và quy trình nâng cấp DB. |

- **Lab làm giúp & giới hạn minh chứng:** K3s cung cấp `local-path` gắn chặt một Docker container node trên cùng đĩa Mac và `kube-router` thực thi `NetworkPolicy`. Ngoài lab tự quản lý cần CSI bền vững hoặc Managed DB; đã chứng minh persistence qua thay Pod DB trên cùng node, kết nối cross-node qua Service/NetworkPolicy/Secret và tạo/kiểm tra artifact `pg_dump -Fc`; **chưa** chứng minh restore SQL hoàn tất vào `orders_restored`, chịu mất node, HA/failover, PITR, benchmark IOPS hay DR độc lập host. Không cleanup fixture `lesson29-pg` hay bản dump ngoài Git.

Nguồn: [PostgreSQL Official Image](https://hub.docker.com/_/postgres/) · [PostgreSQL SQL Dump](https://www.postgresql.org/docs/current/backup-dump.html) · [Kubernetes StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/).
