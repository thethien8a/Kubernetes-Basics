# Sau buổi 13 - PostgreSQL trên Kubernetes

**Bắt đầu:** 2026-10-12. **Hoàn thành sau review:** 2026-10-13, giờ Việt Nam. **Tiến độ sau buổi:** 13/28.

[Challenge gốc](../roadmap/buoi-hoc/13-postgresql.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Database/PVC/Service](../postgres-buoi13.yaml) · [Client](../postgres-client-buoi13.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a12eeb-5fb1-745b-a701-931bdcd487ab)

> ReplicaSet tạo Pod thay thế; PostgreSQL đọc lại dữ liệu trên nguồn persistent đã mount. Giữ PVC/PV và ghi đúng nơi giúp dữ liệu tồn tại qua thay Pod trong thí nghiệm này, không tự bảo đảm HA, backup hoặc chịu mất node/disk.

## 1. Challenge và phạm vi

Nối kiến thức Secret, Service, resources và PVC vào một PostgreSQL instance thật:

1. Có user/password, không hard-code password trong image hoặc manifest.
2. Client ở Pod khác kết nối qua endpoint ổn định trong cluster, không dùng Pod IP.
3. Tạo bảng `public.orders`, ghi hai dòng giả và commit để lưu baseline.
4. Thay chỉ Pod database; giữ Deployment, Service, client và storage, không tạo lại bảng/dữ liệu test.
5. Đọc đúng hai dòng cũ từ client qua Service sau khi Pod mới Ready.

Context `orbstack`, namespace `default`, một node `orbstack`. Học viên chọn Secret mount file, Service ClusterIP và PVC; mentor cung cấp scaffold/commands, học viên tự triển khai và ghi SQL. Mentor tự đọc manifest/API, mount và truy vấn READ ONLY, không apply/delete/restart workload, ghi dữ liệu hoặc xuất credential thay học viên.

| Thành phần | Cấu hình thực hành |
|---|---|
| Database | Deployment `postgres-buoi13`, một replica, strategy `Recreate`, image `postgres:16-alpine`. |
| Credential | Secret Opaque `postgres-secret-buoi13`, hai key `username`/`password`, mount read-only. |
| Storage | PVC riêng `data-postgres-buoi13`, `local-path`, `ReadWriteOnce`, request `1Gi`. Không dùng PVC Buổi 12. |
| Endpoint | Service `postgres-buoi13`, ClusterIP, port 5432, targetPort tên `postgres`. |
| Client | Pod `postgres-client-buoi13`, cùng image để dùng psql; script chuẩn bị password file rồi sleep, không chạy database hoặc mount PVC data. |
| Resources database | CPU request/limit 100m/500m; RAM 256Mi/512Mi. |
| Resources client | CPU request/limit 10m/100m; RAM 16Mi/64Mi. |

Image đã được đối chiếu hỗ trợ Linux ARM64/v8; logs khởi tạo ghi PostgreSQL 16.15/aarch64. Image digest trong các snapshot: `sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea`. Đây là phiên bản đã quan sát, không phải tuyên bố về phiên bản PostgreSQL mới nhất. Đổi major image phải kiểm tra contract đường dẫn data và migration, không thay `latest` tùy tiện.

## 2. Ba đường cấu hình phải phân biệt

### Credential: Secret file và contract của ứng dụng

- Kubernetes đưa các key Secret thành file tại `/run/secrets/postgres/username` và `/run/secrets/postgres/password`; mount ứng dụng là read-only.
- Server dùng `POSTGRES_USER_FILE` và `POSTGRES_PASSWORD_FILE` trỏ tới các file đó. Chính entrypoint PostgreSQL Docker Official Image đọc file; không phải mọi ứng dụng tự biết dùng Secret khi được mount.
- `POSTGRES_DB=labdb` là config không nhạy cảm. User do biến POSTGRES_USER khởi tạo là superuser cho lab, không phải mẫu quyền app production tối thiểu.
- Các biến khởi tạo không tự đổi user/password trong database đã có. Đổi Secret không đồng nghĩa đã rotate password PostgreSQL.
- Mount file không bảo đảm password không bao giờ đi qua env nội bộ của entrypoint, cũng không thay thế RBAC/encryption hoặc kiểm soát quyền đọc trong Pod.

Client override command bằng shell nên không dùng cơ chế khởi tạo server. psql/libpq cần contract riêng:

| Field/config client | Vai trò |
|---|---|
| `PGHOST: postgres-buoi13` | DNS Service trong cùng namespace. |
| `PGPORT: 5432` | Cổng Service. |
| `PGDATABASE: labdb` | Database cần kết nối. |
| `PGPASSFILE` trỏ `/tmp/pgpass` | Password file của libpq, không phải biến POSTGRES_PASSWORD_FILE. |
| `PGCONNECT_TIMEOUT: 5` | Giới hạn chờ thiết lập kết nối. |

Script client chuyển file Secret sang định dạng `host:port:database:username:password`, escape dấu `:` và `\`, dùng `umask 077` rồi unset biến shell chứa credential. File pgpass có mode 600 trong baseline; libpq trên Unix bỏ qua password file nếu group/others có quyền truy cập. Không lưu nội dung file vào tài liệu hoặc dump env để kiểm tra.

Chọn pgpass thay PGPASSWORD theo hướng file của học viên và khuyến nghị libpq về nguy cơ lộ password qua process env. Đổi lại phải đúng format/permission; scaffold chỉ dựng bản pgpass lúc client khởi động, không tự regenerate khi mounted Secret được cập nhật. Không thực hành rotation trong buổi này.

`psql -X` không đọc startup file psql; `-w` không hỏi password, **không tắt authentication**; `ON_ERROR_STOP=1` dừng khi SQL lỗi. Username được chương trình đọc từ mounted file, password do libpq đọc từ pgpass; mentor không xuất các giá trị này.

### Kết nối: DNS Service, ClusterIP và backend

```diagram
Client Pod ──DNS tên Service──▶ ClusterIP:5432 ──▶ PostgreSQL Pod:5432
```

DNS cho Service ClusterIP thông thường phân giải tên Service tới ClusterIP ổn định, không phải cần đổi tên theo Pod IP. Selector `app=postgres-buoi13` khớp label Pod; EndpointSlice cập nhật backend Ready khi Pod được thay. Cơ chế networking/Service của cluster chuyển traffic tới backend.

- `Service.spec.ports[].port` là cổng phía client; `targetPort: postgres` trỏ named container port 5432.
- Client không mount data volume, chỉ truy vấn server qua mạng. Exec psql ngay trong server với Unix socket không thay thế phép thử app khác kết nối qua Service.
- Readiness TCP chỉ chứng minh cổng lắng nghe, không chứng minh password đúng, database/bảng tồn tại hoặc SELECT trả dữ liệu đúng.
- Không dùng domain Mac OrbStack, Ingress, NodePort hoặc LoadBalancer để expose database trong bài.

### Storage: claim, mountPath và PGDATA phải khớp

| Chủ sở hữu | Field/path thực hành | Ý nghĩa |
|---|---|---|
| PVC | `storageClassName: local-path`, RWO, request 1Gi | Yêu cầu storage theo class; không tự là nơi lưu byte database. |
| Pod | `volumes[].persistentVolumeClaim.claimName: data-postgres-buoi13` | Chọn đúng PVC trong namespace. |
| Container | Volume `data` mount tại `/var/lib/postgresql/data` | Đưa nguồn volume vào filesystem container. |
| PostgreSQL | `PGDATA=/var/lib/postgresql/data/pgdata` | Nơi database dùng để lưu data, nằm bên trong mount. |
| PV | `local.path`, `nodeAffinity`, `claimRef` | Mô tả backend local trên node và binding tới PVC. |

```diagram
Deployment ──▶ ReplicaSet ──▶ Pod PostgreSQL
                                │ tham chiếu volume
                                ▼
                               PVC ↔ PV ──▶ storage trên node
```

Mũi tên PVC/PV là quan hệ tham chiếu/binding, không phải dữ liệu được lưu hoặc truyền qua API object. Kubelet/runtime thực hiện mount; ứng dụng phải ghi đúng đường dẫn.

Pod mới có filesystem container mới, nhưng dùng lại cùng nguồn persistent còn tồn tại. PostgreSQL đọc lại các file database tại PGDATA; ReplicaSet không tạo lại bảng orders. Nếu PVC vẫn mount đường dẫn cũ mà PGDATA chuyển sang `/tmp/pgdata` không có persistent mount, dữ liệu mới ghi ở đó không được PVC này bảo vệ. **Đổi PGDATA không tự xóa hay chuyển dữ liệu cũ trên PVC**, nhưng server trỏ tới nơi khác.

Class lab dùng `WaitForFirstConsumer` và reclaim Delete; PV được cấp sau consumer có Events provisioning/binding. RWO giới hạn mount đọc/ghi theo một node, không phải khóa theo một Pod hoặc bảo đảm hai PostgreSQL instances cùng ghi một directory an toàn. Request 1Gi trong local-path không chứng minh đã reserve/quota đủ dung lượng; không thử ghi đầy disk hoặc reclaim.

## 3. Minh chứng runtime và trước/sau

### Khởi tạo ngày 2026-10-12

- Metadata lúc 16:27:47 và mount lúc 16:32:10: một database Pod Ready, RESTARTS=0; PVC/PV riêng Bound, Service có backend đúng Pod.
- Secret chỉ kiểm tra type/key/tham chiếu/dấu hiện diện; không giải mã hoặc lưu nội dung.
- Logs image chuẩn có listen 5432 và `database system is ready to accept connections`. Shutdown/server stopped trong pha khởi tạo rồi server chính chạy không tự là bằng chứng container crash; restartCount lúc kiểm tra là 0.

### Baseline SQL ngày 2026-10-13, kết thúc 08:55:26

Client đã Running/Ready, RESTARTS=0, không PVC database. Session mới từ client qua DNS Service đọc `labdb` trên server `.35`:

- `public.orders` có ba cột: order_id integer PRIMARY KEY, customer text NOT NULL, amount integer NOT NULL; cả ba NOT NULL.
- Đúng hai dòng đã commit: `(101, An, 120000)` và `(205, Binh, 85000)`.
- Transaction kiểm tra READ ONLY, kết thúc ROLLBACK; đọc từ session mới phân biệt với dữ liệu chỉ có trong transaction chưa commit của người tạo.
- Kết nối dùng pgpass thành công; đối chứng không cung cấp password bị từ chối với `no password supplied`. Đây là kiểm tra đường kết nối đã thử, không phải audit mọi pg_hba rule, RBAC, encryption hoặc quyền production.

### Sau thay chỉ Pod, kiểm tra kết thúc 10:05:22

Các mốc dưới đây là giờ Việt Nam ngày 2026-10-13.

| Đối chiếu | Baseline 08:55:26 | Sau thay Pod 10:05:22 |
|---|---|---|
| Server Pod | postgres-buoi13-566fb4b99c-v7sqx | postgres-buoi13-566fb4b99c-4nnm6 |
| Server UID | `b58058ac-d6c1-4767-b0ee-9a2e397a824a` | `f0365165-bab7-4963-b98f-b450799389e2` |
| Pod IP / node | 192.168.194.35 / orbstack | 192.168.194.37 / orbstack |
| Runtime | Running/Ready, RESTARTS=0 | Running/Ready, RESTARTS=0; Pod cũ không còn |
| PVC UID | `52bbd1e9-90c9-4bc7-874d-04375ff258c1` | Giữ nguyên, Bound |
| PV UID | `a0575825-f2fe-4bfd-9133-491008dc2686` | Giữ nguyên, Bound/claimRef đúng PVC |
| Service UID | `5295b58a-ff6e-4e0a-bb72-e4ab79410ba7` | Giữ nguyên |
| Service endpoint | ClusterIP 192.168.194.177:5432, backend `.35` | Cùng ClusterIP/port, backend Ready `.37`, targetRef UID mới |
| Client UID | `f3ddb84c-66ea-45e2-b7ad-1313c32274bf` | Giữ nguyên, cùng containerID/PGHOST, Ready, RESTARTS=0 |
| SELECT từ session mới | Hai dòng baseline | Chính xác cùng hai dòng, count 2 |

Pod mới tạo lúc 09:10:55. OwnerReferences trỏ ReplicaSet `postgres-buoi13-566fb4b99c`, UID `cebcafc8-4c22-40e0-9bfe-04aff09c50ef`, tạo ngày 2026-10-12. ReplicaSet thuộc Deployment giữ UID `ee4f47d2-6d68-4260-a599-bb2d74cd611f`, generation/observedGeneration 1, replicas/updated/ready/available 1. Không thấy Event SuccessfulCreate cho Pod mới ở snapshot, không suy ra chưa từng có Event.

PV `pvc-52bbd1e9-90c9-4bc7-874d-04375ff258c1` trỏ nguồn trên node:

```text
/var/lib/rancher/k3s/storage/pvc-52bbd1e9-90c9-4bc7-874d-04375ff258c1_default_data-postgres-buoi13
```

Node affinity yêu cầu hostname orbstack, reclaim Delete. Mountinfo trước/sau có data mount `/var/lib/postgresql/data` type btrfs/source `/dev/vdb1`, filesystem root `/k8s/default/k3s/storage/pvc-52bbd1e9-90c9-4bc7-874d-04375ff258c1_default_data-postgres-buoi13`; root container overlay. SQL trong Pod mới xác nhận data_directory `/var/lib/postgresql/data/pgdata`. Đây là mount quan sát từ container, không phải đường dẫn trực tiếp trên Mac hoặc kiểm tra trực tiếp toàn bộ node/backend.

**Mốc chốt lúc 10:44:26:** kiểm tra metadata và SELECT READ ONLY vẫn cùng Pod mới/client/PVC/PV/Service, hai Pod Ready/RESTARTS=0, hai dòng đúng và data_directory như trên. API sau các phép đọc giữ identity. Không đọc lại mountinfo ở mốc này; dùng minh chứng mount lúc 10:05:22.

**Kết luận đã kiểm chứng:** dữ liệu tồn tại qua Pod mới dùng lại cùng storage trên cùng node, client kết nối qua Service ổn định. Không dùng Ready riêng lẻ làm minh chứng; snapshot không audit mọi command, thứ tự thao tác hoặc thay đổi dữ liệu từ bên ngoài.

## 4. Review và trade-off

| Chủ đề | Câu trả lời/kết quả và phần mentor chuẩn hóa |
|---|---|
| Lựa chọn resource | Học viên chọn Secret mount file, ClusterIP và PVC. Đạt. Wiring _FILE/pgpass, volume/PGDATA và Recreate là scaffold/giải thích của mentor, không ghi là học viên tự đề xuất toàn bộ. |
| Ai tạo Pod thay thế | Học viên trả lời ReplicaSet. Đúng; Deployment quản lý ReplicaSet, không lưu database hoặc tái tạo bảng. |
| PGDATA ngoài mount | Học viên trả lời không persist khi đường dẫn data và mount không khớp. Đạt ý chính; cách nói đổi mount được chuẩn hóa: scenario chỉ đổi PGDATA, mount vẫn giữ nguyên. Dữ liệu mới ở /tmp/pgdata không được PVC bảo vệ; dữ liệu cũ trên PVC không tự bị xóa bởi đổi config. |
| Client khi Pod IP đổi | Học viên trả lời không cần đổi địa chỉ vì DNS nội bộ và Service chọn Pod bằng label/selector. Đạt. Mentor làm rõ DNS Service thông thường trả ClusterIP ổn định; backend/EndpointSlice cập nhật Pod IP mới, không phải DNS bắt client dùng Pod IP. |
| Node local mất disk | Học viên trả lời không khôi phục chỉ nhờ object PV/PVC, nêu PV trỏ node/disk tương ứng. Đạt trong lab dùng PV local; không khái quát mọi PV đều node-local. Nếu mất byte trên disk và không có nguồn phục hồi khác, các object không tái dựng database; chưa thử node failure/restore thật. |

Deployment một replica được phép trong Buổi 13. Recreate tránh RollingUpdate chồng instance khi cập nhật Deployment trên cùng data directory, đổi lại downtime; không bảo đảm mọi tình huống manual delete Pod đều không chồng lấn. Chưa đo thời gian gián đoạn. Tăng replicas không tự tạo PostgreSQL replication/HA; không tăng replica để thử hai database dùng chung directory. StatefulSet để Buổi 14, không chuyển workload trong lượt chốt này.

## 5. SQL và commands để ôn

SQL sau là **setup baseline lần đầu đã giao học viên**, không phải script reset hoặc startup. Bảng hiện đã có, không chạy lại CREATE/INSERT trong phép thử persistence:

```sql
BEGIN;
CREATE TABLE public.orders (
  order_id INTEGER PRIMARY KEY,
  customer TEXT NOT NULL,
  amount INTEGER NOT NULL
);
INSERT INTO public.orders (order_id, customer, amount)
VALUES (101, 'An', 120000), (205, 'Binh', 85000);
COMMIT;
SELECT order_id, customer, amount FROM public.orders ORDER BY order_id;
```

Commands chỉ đọc để xem trạng thái/identity và dữ liệu giả hiện có:

```bash
kubectl --context=orbstack -n default get deployment postgres-buoi13
kubectl --context=orbstack -n default get pods -l app=postgres-buoi13 \
  -o custom-columns='NAME:.metadata.name,UID:.metadata.uid,IP:.status.podIP,NODE:.spec.nodeName'
kubectl --context=orbstack -n default get pvc data-postgres-buoi13
kubectl --context=orbstack get pv pvc-52bbd1e9-90c9-4bc7-874d-04375ff258c1
kubectl --context=orbstack -n default get service postgres-buoi13
kubectl --context=orbstack -n default get endpointslice \
  -l kubernetes.io/service-name=postgres-buoi13
kubectl --context=orbstack -n default exec postgres-client-buoi13 -- \
  sh -c 'exec psql -X -w -v ON_ERROR_STOP=1 \
    -U "$(cat /run/secrets/postgres/username)" \
    -c "SELECT order_id, customer, amount FROM public.orders ORDER BY order_id;"'
```

Trong thí nghiệm, sau lưu baseline học viên được giao delete đúng Pod server cũ với wait, watch Pod replacement tới Ready rồi chỉ SELECT từ client. Không apply lại, thêm init SQL, xóa/sửa PVC/PV hoặc chạy lại lệnh ghi. Dừng watch bằng Ctrl+C không dừng Pod; không chỉ dựa vào rollout status cũ hoặc Ready để kết luận persistence. Hai manifest đầu tài liệu là tham khảo cấu hình, không phải yêu cầu mentor triển khai lại.

Nếu lỗi, điều tra từ PGHOST/namespace/port → Service selector/labels và EndpointSlice → DNS/network → authentication → database/schema/query; storage từ PVC Events/class/controller tới PV source/node affinity, Pod mount và PGDATA/backend. Kiểm tra đúng context/default, không dump env, Secret, password file, token hoặc logs có thể chứa dữ liệu nhạy cảm. Chỉ đọc bảng dữ liệu giả đã biết.

## 6. OrbStack làm giúp, ngoài lab và liên hệ DE

- **Trong lab:** cluster/node/runtime, CoreDNS và local-path provisioner/backend filesystem đã sẵn. PVC/StorageClass khai báo không tự tạo disk/directory nếu thiếu controller/backend. Provisioner cấp storage/PV; app vẫn phải mount và ghi đúng nơi.
- **Storage tự quản lý/on-prem:** cần chuẩn bị backend + controller/provisioner/CSI phù hợp, StorageClass.provisioner/parameters/volumeBindingMode/reclaimPolicy, quyền backend và topology. Local đơn giản, phù hợp lab nhỏ nhưng gắn node; backend remote/replicated có thêm hạ tầng/vận hành và không tự thay thế database HA/backup. Không dựng storage platform khác chỉ để chốt bài.
- **Cloud/managed:** nhà cung cấp có thể chuẩn bị driver/default class, nhưng phải kiểm tra driver, parameters/quyền và topology thực tế; không copy tên local-path rồi mặc định có cloud disk hoặc volume dùng được từ mọi node.
- **Networking:** cần DNS cluster, kubelet clusterDNS/clusterDomain, Pod dnsPolicy phù hợp và cơ chế networking/Service hoạt động. Service cần selector/port/targetPort đúng và backend Ready. Đây là DNS/kết nối trong Pod, không phải tiện ích truy cập ClusterIP/domain trên Mac của OrbStack; chưa cấu hình cluster ngoài lab.
- **Node/disk hỏng:** PV local bài này có node affinity orbstack, không tự chuyển các byte sang node khác. Giữ API object không tái dựng dữ liệu mất; replication, attach/mount volume khác, backup/restore và failover cần thiết kế/kiểm thử riêng. Chưa kiểm chứng những cơ chế này.
- **Data Engineering:** PostgreSQL có thể làm relational/metadata backend cho ứng dụng như Airflow ở bài sau. Workload được tạo lại, endpoint ổn định, credential đúng và data bền vững là các trách nhiệm khác nhau; chỉ một SELECT thành công hoặc một Pod Ready không chứng minh toàn bộ platform phù hợp production.

**Đã thực hành:** Secret file wiring server/client, PostgreSQL Ready, PVC riêng/mount, client qua DNS Service/authentication, schema/dữ liệu commit và persistence qua thay Pod trên cùng node. **Chỉ giải thích/review:** PGDATA sai đường dẫn, node mất disk, rotation, RWO/concurrent writers, Recreate/downtime, HA/backup và cấu hình ngoài lab. **Chưa làm:** xóa PVC/PV/data, thử mất node, restore backup, rotation credential, nhiều DB replicas, StatefulSet hoặc triển khai ngoài lab.

**Buổi 13 Hoàn thành, tổng 13/28.** Đang chờ [Buổi 14 - StatefulSet](../roadmap/buoi-hoc/14-statefulset.md), chưa bắt đầu. Giữ nguyên tài nguyên demo; lưu tổng kết không phải thao tác dọn, chuyển controller, commit/push hoặc triển khai workload.

## Tài liệu tham khảo

- [PostgreSQL Docker Official Image](https://hub.docker.com/_/postgres) và [tài liệu nguồn](https://github.com/docker-library/docs/blob/master/postgres/README.md).
- [libpq environment variables v16](https://www.postgresql.org/docs/16/libpq-envars.html).
- [Password file v16](https://www.postgresql.org/docs/16/libpq-pgpass.html).
- [psql v16](https://www.postgresql.org/docs/16/app-psql.html).
- [PV/PVC và StorageClass đã học ở Buổi 12](12-pv-pvc-storageclass.md), có nguồn Kubernetes v1.35 và local-path-provisioner v0.0.36 đã đối chiếu.
