# Tổng kết buổi 15 — MinIO-compatible object storage

**Ngày bắt đầu/chốt:** 2026-10-13–2026-10-14, giờ Việt Nam. **Trạng thái:** Hoàn thành; đã bổ sung và kiểm chứng Ingress cho Console. **Tiến độ:** 15/28.

[Challenge gốc](../roadmap/buoi-hoc/15-minio.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Manifest](../minio-buoi15.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a137fb-78ee-765a-9fdd-2e78befcfdac)

> Lab cuối dùng SILO — fork cộng đồng tương thích MinIO — thay cho image `quay.io/minio/minio:latest` bị registry trả `401 UNAUTHORIZED`. SILO gần giao diện/hành vi MinIO hơn một implementation S3 độc lập, nhưng không phải bản phân phối MinIO chính thức và không bảo đảm parity tuyệt đối. Kết quả ở đây xác nhận các thao tác đã thử trên SILO, không phải mọi hành vi của MinIO.

> Credential được học viên cập nhật qua Secret. Mentor chỉ kiểm tra metadata/key names và tham chiếu Secret, không đọc, giải mã hoặc lưu giá trị. Không lưu tên/key/nội dung của object Markdown đã upload.

## 1. Mục tiêu và kết quả

Buổi học yêu cầu một object store có persistent storage, S3 API và Console; phân biệt endpoint trong cluster với cách truy cập từ Mac. Học viên triển khai manifest, cập nhật credential, đăng nhập Console, upload một file Markdown nhỏ, xóa Pod MinIO rồi xác nhận bucket/file vẫn hiện trong Console. Sau review, học viên giải thích được vai trò của ReplicaSet, PVC/PV, anonymous `403` và phạm vi phép thử. Phần truy cập Console được mở rộng bằng Ingress `minio-console`, host `silo.pro.thien`; kiểm tra chỉ đọc xác nhận Traefik route tới Service `minio:9001` và GET trả `HTTP 200 text/html`.

Học viên báo file vẫn còn sau khi Pod được tạo lại. Mentor tự đối chiếu Pod/PVC/PV/Service trước-sau; API Kubernetes không liệt kê object S3, nên nội dung object và việc file hiện trong Console được ghi đúng là kết quả học viên quan sát, không giả vờ đã đọc object bằng một client có credential.

## 2. Cấu hình và luồng dữ liệu

| Thành phần | Cấu hình/ý nghĩa |
|---|---|
| PVC | `minio-data`, `local-path`, `ReadWriteOnce`, request `1Gi`; PVC là claim tách biệt với vòng đời Pod. |
| Deployment | `minio`, một replica, strategy `Recreate`; Deployment quản lý ReplicaSet, ReplicaSet tạo Pod thay thế. |
| SILO process | Image `docker.io/pgsty/silo:RELEASE.2026-09-16T00-00-00Z@sha256:635197cb9f36d01bee221d34d1c7d7960f6a95c48b0b6c01d99cd13bdae51a46`; command `/usr/bin/silo`, args `server /data --console-address :9001`. |
| Volume | Deployment template tham chiếu PVC `minio-data`; container mount PVC tại `/data`, đúng với data path truyền cho server. PVC/PV giữ cùng identity qua phép thay Pod. |
| Secret | `minio-credentials`, type `Opaque`, keys `root-user` và `root-password`; `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` lấy lần lượt qua `secretKeyRef`. Không lưu credential. |
| Service | `minio`, `ClusterIP`, port `9000` tới S3 API, port `9001` tới Console; selector trỏ Pod `app=minio`. ClusterIP là endpoint ổn định, còn Pod IP có thể thay đổi. |
| Ingress | [Manifest](../minio-buoi15-ingress.yaml) dùng class `traefik`, host `silo.pro.thien`, path `/` và backend Service `minio:9001`. Ingress address `192.168.139.2`; GET tới hostname trả `HTTP 200 text/html`. |

```diagram
┌──────────────┐  DNS: minio:9000  ┌───────────────┐       ┌─────────────┐
│ Spark Pod    │──────────────────▶│ Service :9000 │──────▶│ S3 API      │
└──────────────┘                   └───────────────┘       └──────┬──────┘
                                                                  │ writes /data
┌──────────────┐  HTTP silo.pro.thien ┌──────────────────┐        │
│ Mac browser  │─────────────────────▶│ Traefik Ingress  │        │
└──────────────┘                      └────────┬─────────┘        │
                                                │ Service :9001    │
                                                ▼                  ▼
                                           ┌──────────┐  ┌────────────────┐
                                           │ Console  │  │ PVC → PV       │
                                           └──────────┘  │ local-path     │
                                                         └────────────────┘
```

Trong cùng namespace, client như Spark dùng `http://minio:9000`; từ namespace khác có thể dùng FQDN `minio.default.svc.cluster.local:9000`. Console là UI ở cổng 9001, không phải S3 API. Mac không dùng Kubernetes Service DNS ở luồng này: browser gửi request tới hostname Ingress, Traefik chuyển tới Service `minio:9001`. `kubectl port-forward` vẫn hữu ích như một tunnel debug tạm thời; Ingress là đường truy cập đã kiểm chứng ở cuối buổi.

### Cập nhật Secret

Secret object hiện có hai key và Deployment tham chiếu đúng cả hai. Credential ở dạng environment variable được đọc khi container khởi động; sửa Secret không tự thay giá trị trong process đang chạy, nên cần tạo Pod mới/restart rollout. Base64 trong trường Secret `data` chỉ là encoding, không phải mã hóa. Không ghi credential vào lệnh literal, logs, Git hoặc hội thoại; hệ thống thật còn cần RBAC phù hợp, encryption at rest hoặc secret-management workflow của tổ chức.

## 3. Minh chứng runtime trước/sau

Các snapshot chỉ đọc ở context `orbstack`, namespace `default`:

| Đối tượng | Trước thay Pod | Sau thay Pod |
|---|---|---|
| Pod | `minio-74b899c57c-bbg2f`, UID `d0b501dd-efa3-4b8d-88ee-cdadaec9c7b6`; endpoint IP `192.168.194.57`. | `minio-74b899c57c-ms76j`, UID `269f7688-66df-4585-b5fc-a6c032e8ffc5`, `Running/Ready`, 0 restarts; endpoint IP `192.168.194.58`. |
| Deployment | Một replica. | Generation/observedGeneration 2, một replica Ready/Updated. |
| PVC | `minio-data`, UID `b2a30bfb-11ea-4d05-a447-82ddc1fddce9`, `Bound`. | Cùng UID, volume binding và `local-path` class. |
| PV | `pvc-b2a30bfb-11ea-4d05-a447-82ddc1fddce9`, UID `b36af023-98d5-45a9-8c4c-776b3687231e`. | Cùng UID/source; reclaim policy `Delete`, node affinity `orbstack`. |
| Service | `minio`, ClusterIP `192.168.194.229`, cổng `9000`/`9001`. | Cùng UID, ClusterIP và ports; EndpointSlice trỏ Pod mới, Ready. |
| Data | Học viên upload một file Markdown nhỏ qua Console. | Học viên refresh Console sau thay Pod và báo bucket/file vẫn còn. Đây là báo cáo quan sát UI; không lưu nội dung object. |

PV `local.path` trong lab là `/var/lib/rancher/k3s/storage/pvc-b2a30bfb-11ea-4d05-a447-82ddc1fddce9_default_minio-data`, node affinity `orbstack`. Khớp cùng lúc `args: server /data`, `volumeMount.mountPath: /data`, claimName, PVC/PV identity và object vẫn thấy sau Pod mới là bằng chứng cho persistence qua Pod replacement trong scenario này.

Từ môi trường kiểm tra, GET `/` qua cổng Console trả `HTTP 200`, `text/html`. GET `/` tới cổng S3 API không gửi xác thực và trả `HTTP 403`, XML `AccessDenied`, `Server: Silo`. Điều đó chứng minh endpoint S3 có phản hồi và từ chối request ẩn danh; không chứng minh credential sai, cũng không tự chứng minh request có xác thực thành công. Upload qua Console và file còn sau Pod replacement là kết quả thao tác do học viên báo.

## 4. Review và giới hạn

- **Controller và storage:** Học viên xác định đúng ReplicaSet tạo Pod thay thế; PVC/PV có identity độc lập với Pod, và Deployment template tham chiếu volume/mount. Nói chính xác hơn, Deployment quản lý ReplicaSet, còn ReplicaSet trực tiếp tạo Pod. PVC/PV không làm dữ liệu bất tử: claim phải còn, policy/backend phải giữ dữ liệu.
- **PVC/PV retention:** Trong lab này PV dùng reclaim `Delete`; xóa PVC có thể làm provisioner xóa PV và backing data. Không khái quát điều này sang PV `Retain` hoặc mọi storage driver.
- **Anonymous `403`:** Học viên sửa cách diễn đạt thành request curl không có xác thực. API đã trả một S3 `AccessDenied`; đó khác với server không lắng nghe. Một request ẩn danh không kiểm tra credential đã cập nhật.
- **Persistence:** File còn sau khi Pod UID đổi là minh chứng theo quan sát UI của học viên. Lượt kiểm tra của mentor xác nhận Pod mới Ready, PVC/PV giữ identity và Service endpoint đổi sang Pod mới; không truy vấn bucket/object bằng credential và không đọc nội dung object.

**Chỉ kiểm chứng:** Console truy cập được, S3 endpoint trả lời, một upload theo quan sát học viên còn qua một lần thay Pod trên cùng node, cùng PV local. **Chưa kiểm chứng:** mất node/disk, backup/restore, HA/replication, nhiều replica MinIO, Spark client gọi API, hoặc một request S3 có chữ ký được kiểm tra độc lập bằng SDK/CLI. Bài chạy SILO, không chứng nhận tương thích tuyệt đối với MinIO chính thức.

## 5. OrbStack làm giúp ↔ hệ thống ngoài lab

**Trong lab:** Kubernetes cung cấp Service ClusterIP và service discovery trong cluster; môi trường đã chuẩn bị CoreDNS và local-path provisioner/backing filesystem. OrbStack cung cấp wildcard `*.k8s.orb.local` cho Ingress/LoadBalancer; hostname tùy chọn `silo.pro.thien` hiện cũng được Mac phân giải thành `192.168.139.2`, nhưng lượt kiểm tra này không xác định ánh xạ đến từ `/etc/hosts` hay DNS resolver nào. `kubectl port-forward` là tunnel debug cục bộ, không phải IP public hoặc một Service LoadBalancer. Local PV bị ràng buộc với node `orbstack`; phép thử chỉ thay Pod trên cùng node.

**Ngoài lab:** Cluster tự quản lý cần CoreDNS/cluster DNS và Service selector/endpoints đúng; managed cluster có thể cài sẵn nhưng cần xác nhận health/domain. Truy cập từ ngoài cluster thực tế thường cần LoadBalancer do cloud controller hoặc on-prem LB (ví dụ MetalLB), hoặc Ingress/Gateway phù hợp, cộng routing, DNS, firewall và TLS. Port-forward vẫn là công cụ debug, không phải endpoint production.

Storage ngoài lab cần backend và provisioner/CSI tương ứng, StorageClass parameters, topology/permissions, reclaim policy và kiểm tra mount/data path. Cloud có thể cung cấp CSI/network block storage; on-prem có thể dùng storage platform/network backend phù hợp. Dù PVC/PV Bound và dữ liệu còn khi thay Pod, local-path không chứng minh phục hồi khi node/disk mất, cũng không thay backup hoặc replication. Với object storage dùng thật cần thiết kế durability/capacity/access control riêng, không suy ra từ bài một Pod/1Gi.

## 6. Liên hệ Data Engineering và bước tiếp theo

Spark trong cùng namespace sẽ dùng S3 API qua Service `minio:9000`; credential Spark cần được cấu hình riêng và đổi theo khi credential được rotate. Console ở `9001` dành cho thao tác/quan sát bằng trình duyệt. Ingress `silo.pro.thien` chỉ route tới Console qua Service `minio:9001`; S3 API không được expose bởi Ingress này. Thực hành Spark đọc/ghi object chưa nằm trong Buổi 15; đó là nội dung Buổi 20.

Buổi 15 đã review đạt ngày 2026-10-14. Kiểm tra live cuối buổi xác nhận `Ingress/minio-console` dùng class `traefik`, host `silo.pro.thien`, backend `minio:9001` và GET trả `HTTP 200 text/html`; Mac resolver trả `192.168.139.2`. Bước tiếp theo là [Buổi 16 — Spark Standalone](../roadmap/buoi-hoc/16-spark-standalone.md); chưa triển khai Spark workload trong Buổi 15.

## Tài liệu tham khảo

- [SILO compatibility/migration](https://silo.pgsty.com/compatibility/migration/).
- [SILO pinned release](https://github.com/pgsty/silo/releases/tag/RELEASE.2026-09-16T00-00-00Z).
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/).
- [Kubernetes port-forward](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/).
