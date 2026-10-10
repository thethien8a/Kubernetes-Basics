# Sau buổi 09 - Secret

**Ngày học:** 2026-10-09 và 2026-10-10, giờ Việt Nam. **Ngày hoàn thành:** 2026-10-10. **Tiến độ sau review:** 9/28.

[Challenge gốc](../roadmap/buoi-hoc/09-secret.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Deployment](../app-buoi9.yaml)

> Secret dành cho dữ liệu nhạy cảm, nhưng base64 không phải mã hóa bảo mật. Phải phân biệt resource chứa dữ liệu, cách container nhận dữ liệu và quyền ai được đọc resource đó.

## 1. Challenge và phạm vi

Học viên tự tạo Secret và triển khai app demo để nhận credential qua env, không gán giá trị vào Deployment/image và không in credential ra logs. Yêu cầu chỉ dùng dữ liệu giả, không dùng tài khoản của dịch vụ thật.

- Context `orbstack`, namespace `default`.
- Secret Opaque `app-secret-buoi9`, bốn key POSTGRES_USER, POSTGRES_PASSWORD, MINIO_ACCESS_KEY, MINIO_SECRET_KEY.
- Deployment `app-buoi9`, một replica, container `app`, image `busybox:1.36`.
- App dùng shell kiểm tra biến tồn tại và không rỗng, chỉ in dấu `present` mỗi 30 giây.
- Không dựng PostgreSQL/MinIO, Service, Ingress hoặc PVC cho bài; không thay app/ConfigMap Buổi 08.
- Mentor tự đọc manifest và kiểm tra live bằng công cụ chỉ đọc; không tạo Secret, sửa manifest workload, apply hoặc restart thay học viên.

Mentor không đọc giá trị credential để xác minh nội dung. Minh chứng chỉ xác nhận đúng tên key, không rỗng, nguồn env và kết quả marker; không lưu Secret YAML/data hoặc giá trị credential vào tổng kết.

## 2. Secret và ConfigMap

| Nội dung | ConfigMap | Secret |
|---|---|---|
| Mục đích | Config không nhạy cảm như endpoint, log level. | Dữ liệu nhạy cảm như password, access key, token. |
| Nguồn env từng key | `valueFrom.configMapKeyRef`. | `valueFrom.secretKeyRef`. |
| Nguồn env cả resource | `envFrom.configMapRef`. | `envFrom.secretRef`. |
| Quyền đọc | Có quyền phù hợp thì đọc được config. | Có quyền phù hợp thì đọc được credential; không mặc nhiên bí mật tuyệt đối. |

Secret là API object, không phải Pod, database hoặc Secret manager tự vận hành mọi bước bảo mật. Tạo Secret không tự đưa dữ liệu vào mọi container; Pod phải tham chiếu nguồn và app phải đọc env/file tương ứng.

- `metadata.name` định danh Secret; Secret phải cùng namespace với Pod tham chiếu.
- `type: Opaque` dành cho dữ liệu tùy ý do người dùng định nghĩa.
- `data` biểu diễn giá trị bằng base64; `stringData` nhận chuỗi đầu vào để API xử lý. Cả hai không phải cách làm credential an toàn để commit vào Git.
- Secret nằm trong datastore của control plane; etcd là datastore thường gặp trong kiến trúc Kubernetes. Bài không kiểm tra backend lưu trữ hoặc encryption at rest thực tế của OrbStack.

## 3. envFrom và secretKeyRef

### Cấu hình đã triển khai

Trong container `app` của Pod template:

```yaml
envFrom:
  - secretRef:
      name: app-secret-buoi9
```

Kubelet lấy dữ liệu nguồn để cấp env khi khởi tạo container. Trong cấu hình này, tên key trở thành tên biến; app nhận cả bốn key hiện có. Không có prefix hoặc env override.

**Trade-off:** envFrom ngắn gọn nhưng lấy mọi key. Nếu Secret sau này chứa thêm credential cho app khác, container mới cũng nhận key đó. secretKeyRef dài hơn nhưng chọn từng key và có thể đặt tên biến đích khác key nguồn. Với Secret riêng chứa đúng bốn key cho demo này, giữ envFrom là hợp lệ; khi cần chọn lọc/đổi tên, dùng secretKeyRef.

### Ví dụ đổi tên đã review, chưa triển khai

App giả định cần biến DB_PASSWORD, trong khi Secret vẫn giữ key POSTGRES_PASSWORD:

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: app-secret-buoi9
        key: POSTGRES_PASSWORD
```

| Field | Vai trò |
|---|---|
| `env[].name` | Tên biến mà app đọc: DB_PASSWORD trong ví dụ. |
| `secretKeyRef.name` | Tên Secret nguồn: app-secret-buoi9. |
| `secretKeyRef.key` | Key lấy từ Secret: POSTGRES_PASSWORD, không phải tên biến đích. |

Học viên chọn đúng secretKeyRef nhưng ví dụ ban đầu vẫn để tên biến POSTGRES_PASSWORD. Mentor bổ sung mapping tên đích/key nguồn. Không đổi tên key Secret hoặc env runtime của app demo để giải tình huống này. envFrom mặc định không mapping tên từng key; prefix chỉ thêm tiền tố chung, không thay thế mapping riêng.

## 4. Cập nhật nguồn Secret không đồng nghĩa app đã cập nhật

| Cách cấp | Khi Secret đổi | Điều app/vận hành cần làm | Minh chứng Buổi 09 |
|---|---|---|---|
| Env, qua envFrom hoặc secretKeyRef | Container đang chạy không tự nhận env mới. | Với Deployment trong bài, tạo Pod mới qua rollout để cấp lại env từ nguồn hiện tại. | Đã thực hành inject env ban đầu; chưa đổi Secret/rollout để thử rotation. |
| Secret volume | Projected file cập nhật theo đồng bộ của kubelet, có độ trễ. | App phải đọc lại/poll/reload file; chỉ đọc lúc startup thì file đổi chưa làm app dùng giá trị mới. | Chỉ giải thích, chưa mount Secret volume. |

Mount file là đổi cách cấp/đọc cấu hình, không làm env cũ tự đổi. Secret mount bằng `subPath` không nhận cập nhật tự động như volume thông thường. Không cần PVC/PV/StorageClass cho riêng Secret volume.

Kiến thức file/reload nối với thí nghiệm ConfigMap Buổi 08, nhưng không coi thực hành ConfigMap là đã thực hành Secret volume hoặc credential rotation.

## 5. Base64, quyền API và giới hạn bảo mật

- Base64 là biểu diễn dữ liệu, không phải mã hóa bảo mật. Người đọc được Secret qua API có thể đọc dữ liệu sau decode; không cần truy cập trực tiếp datastore.
- Quyền `get` một Secret cho phép đọc nội dung của Secret đó, không tự mở rộng sang mọi Secret hoặc namespace.
- RBAC có thể giới hạn theo namespace, tên resource và verb. Một user chỉ được get `app-secret-buoi9` trong default, không có quyền khác, không tự đọc được Secret khác trong default hoặc namespace analytics.
- Encryption at rest bảo vệ dữ liệu lưu trữ, không thay thế kiểm soát quyền đọc qua API. Quyền list/watch hoặc quyền tạo workload có thể làm rộng khả năng tiếp cận Secret; đây là lưu ý bảo mật, chưa audit trong lab.
- Không commit credential, xuất toàn bộ env, decode Secret để gửi mentor hoặc in credential vào logs. Lệnh tạo Secret bằng `--from-literal` đã cung cấp chỉ dành cho ví dụ giả công khai; credential thật có nguy cơ lọt vào shell history.

Không suy ra lab đã an toàn production từ việc dùng kind Secret. Chưa kiểm tra RBAC/encryption/datastore hoặc triển khai Secret manager/KMS; phạm vi quyền ở trên là tình huống review, không phải role đã được tạo/kiểm thử.

## 6. Minh chứng thực hành

Snapshot được mentor kiểm tra ngày 2026-10-10, không phải giá trị bảo đảm giữ nguyên về sau:

| Phần kiểm tra | Kết quả |
|---|---|
| Secret lúc 11:47 giờ Việt Nam | Opaque, DATA=4, đúng bốn tên key, đều có dấu không rỗng; không xuất giá trị. |
| File, Deployment và Pod lúc 13:08 | Cùng nguồn envFrom.secretRef tới app-secret-buoi9; một container, không env literal/override. |
| Deployment | Generation/observedGeneration 1; replicas/ready/available 1. |
| Pod | `app-buoi9-5bfb85cf5-pb6bf`, UID `60a13417-1251-4269-8044-40e4eda09b12`, owner ReplicaSet `app-buoi9-5bfb85cf5`; Running/Ready 1/1, RESTARTS=0. |
| Container | Khởi động `2026-10-10T06:06:02Z`, tức 13:06:02 giờ Việt Nam; image busybox:1.36, digest `sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662`. |
| Logs 13:09:02–13:11:02 giờ Việt Nam | Năm dòng gần nhất đều đủ bốn dấu present; timestamp UTC tương ứng 06:09:02Z–06:11:02Z. |
| Env hiện tại | Exec chỉ xuất marker xác nhận cả bốn biến tồn tại và không rỗng. |

Trước khi đọc logs, mentor đối chiếu script trong file, Deployment và Pod với script chỉ in `${VAR:+present}`. So sánh độc lập xác nhận từng dòng logs đủ bốn marker, không coi Pod Ready là đủ minh chứng inject.

Marker chứng minh app nhận biến không rỗng, không chứng minh credential đúng với PostgreSQL/MinIO, có thể đăng nhập hoặc được cấp quyền tại dịch vụ đích. Digest hiện tại cùng baseline image lab; không chứng minh tag bất biến mãi mãi.

## 7. Review và bổ sung của mentor

| Câu review | Câu trả lời / đánh giá |
|---|---|
| App cần DB_PASSWORD, Secret có POSTGRES_PASSWORD. | Học viên nêu envFrom không tự đổi tên, chọn secretKeyRef đúng cơ chế. Ví dụ chưa đổi env.name; mentor bổ sung DB_PASSWORD là tên đích, POSTGRES_PASSWORD là key nguồn. Không ghi là học viên đã tự triển khai mapping này. |
| Chỉ đổi Secret thì env hiện tại có tự nhận không? | Học viên trả lời không, cần restart Pod hoặc mount file. Đạt ý chính env; mentor chuẩn hóa rollout tạo Pod mới và bổ sung file/reload/subPath, không ghi đã thử rotation/mounted Secret. |
| Có quyền get Secret có đọc dữ liệu được không? | Học viên trả lời có; mentor bổ sung base64 không mã hóa, API access không cần đọc datastore trực tiếp và cần phân biệt dữ liệu một Secret với mọi Secret trong cluster. |
| Chỉ get app-secret-buoi9 trong default có đọc Secret khác/namespace khác không? | Học viên trả lời không vì không có quyền ở Secret/namespace khác. Review phạm vi quyền đạt; đây là tình huống lý thuyết, không phải kiểm thử RBAC live. |

**Kết quả:** thực hành và concept chính Secret đạt sau review ngày 2026-10-10. Mapping tên biến và điều kiện cập nhật file là phần mentor bổ sung; không ghi thành phần học viên tự triển khai hoặc audit bảo mật đã hoàn thành.

Trong buổi, học viên yêu cầu mentor tự kiểm tra output có thể truy cập. Đã thêm mục 1.5 vào quy tắc mentor, AGENTS.md và prompt bàn giao: tự đọc manifest/kiểm tra live bằng công cụ chỉ đọc, chỉ xin phần output tối thiểu đã loại dữ liệu nhạy cảm khi không thể tự kiểm tra. Kiểm tra runtime không thay thế câu hỏi concept.

## 8. Command để ôn và cách debug an toàn

Các lệnh dưới đây không xuất nội dung Secret. Logs chỉ được đọc sau khi xác nhận app vẫn dùng script chỉ in marker:

```bash
kubectl --context=orbstack -n default get secret app-secret-buoi9
kubectl --context=orbstack -n default get deployment app-buoi9
kubectl --context=orbstack -n default get pods -l app=app-buoi9 -o wide
kubectl --context=orbstack -n default logs deployment/app-buoi9 -c app \
  --tail=5 --timestamps=true
kubectl --context=orbstack -n default exec deployment/app-buoi9 -c app -- sh -c \
  'printf "POSTGRES_USER=%s POSTGRES_PASSWORD=%s MINIO_ACCESS_KEY=%s MINIO_SECRET_KEY=%s\n" "${POSTGRES_USER:+present}" "${POSTGRES_PASSWORD:+present}" "${MINIO_ACCESS_KEY:+present}" "${MINIO_SECRET_KEY:+present}"'
```

Không dùng get Secret với `-o yaml/-o json` hoặc dump `printenv/env` vào output để review. Khi cần tên key/dấu hiện diện, chỉ trích phần cần thiết, không in giá trị.

Thứ tự debug tham khảo: kiểm tra tên/namespace/type/số key của Secret, tham chiếu env trong Pod spec, trạng thái/Events của Pod, rồi marker và tên biến app đọc. Nếu Pod chưa chạy hoặc thiếu key bắt buộc, inspect Events để tìm bằng chứng; không đoán lỗi image/network hoặc sửa hạ tầng khi chưa kiểm tra. Đây là hướng debug tham khảo; buổi không có lỗi runtime cần học viên sửa được ghi nhận.

## 9. OrbStack và ngoài lab

Secret env/volume là cơ chế Kubernetes chuẩn, không cần domain wildcard, truy cập ClusterIP từ Mac, LoadBalancer hoặc provisioner local-path của OrbStack.

- Control plane cung cấp API Secret và kiểm soát quyền truy cập; Pod spec khai báo nguồn dữ liệu cần dùng.
- Kubelet trên node cấp env lúc khởi tạo container và đồng bộ projected file nếu dùng Secret volume.
- App chịu trách nhiệm đọc tên biến/path và reload nếu dùng file.
- Trên cluster tự quản lý, người vận hành cấu hình/kiểm tra RBAC và encryption at rest của control plane. Trên managed Kubernetes, kiểm tra chính sách/quyền và thiết lập mã hóa mà provider cung cấp, không mặc định cấu hình lab hoặc cloud đã an toàn.

**Giới hạn:** thực hành chỉ trên OrbStack; ví dụ RBAC, encryption, mounted Secret, rename và rotation chỉ là giải thích/review, chưa triển khai hoặc kiểm chứng trên cluster ngoài lab. Không dựng production để giải thích những khác biệt này.

## 10. Liên hệ Data Engineering và phần cần ôn

- App ingestion/PostgreSQL và Spark/MinIO có thể giữ image, cấp credential phù hợp môi trường chạy thay vì hard-code vào code/image.
- ConfigMap giữ endpoint/log-level không nhạy cảm; Secret giữ credential. Tách hai loại không đồng nghĩa hệ thống đã có access control đúng.
- Cấp riêng những key/container cần dùng, tránh Secret chung làm app nhận credential không cần thiết. Không log password hoặc access key để chứng minh Spark/app nhận config.
- Rotation có hai phần: cập nhật nguồn credential và bảo đảm app dùng giá trị mới; env không tự reload, file chỉ hữu ích khi app đọc lại.
- Cần nhớ quan hệ env.name ↔ tên app đọc, secretKeyRef.key ↔ key nguồn; không cần học thuộc YAML hoặc command.

**Buổi 09 hoàn thành, tiến độ 9/28.** Chờ bắt đầu [Buổi 10 - CPU và Memory](../roadmap/buoi-hoc/10-cpu-va-memory.md); chưa triển khai challenge resources mới.

## Tài liệu tham khảo

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/).
- [Distribute Credentials Securely Using Secrets](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/).
- [Secrets Good Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/).
- [Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/).
