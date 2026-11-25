# Tổng kết Bài 23 — ConfigMap, Secret và thay đổi cấu hình

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/23-config-secret.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/24-serviceaccount-rbac.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-20** giờ Việt Nam (`Asia/Ho_Chi_Minh`); lab thực hành tối 19/11, review cuối chọn **C** đúng.
- **Challenge:** Dùng cùng một key ConfigMap qua env và file, đổi giá trị mà giữ container cũ, rồi đối chứng bằng Pod mới. Dùng Secret giả riêng và xác nhận app nạp được mà không in giá trị.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab` Active, UID `6d2e69f9-ada2-4699-af0d-2c98a3974710`. Học viên tự thao tác workload. Mentor chỉ chuẩn bị scaffold, thử client dry-run, thử script riêng và kiểm tra live chỉ đọc.

## 1. Mental model và cấu hình

| Resource / field | Điều cần nhớ |
|---|---|
| ConfigMap `data` / Secret `type` và các key | ConfigMap dành cho cấu hình không nhạy cảm. URL chứa credential phải được xử lý như Secret dù tên biến không có chữ `password`. `Opaque` chứa dữ liệu tùy ý; base64 là cách biểu diễn, không phải mã hóa. |
| `env[].name` → `valueFrom.configMapKeyRef` / `secretKeyRef` | `env[].name` là tên biến app đọc; `name` trong ref là tên resource cùng namespace; `key` chọn mục trong resource. Nếu tên/key bắt buộc sai, kiểm ref trước khi debug đăng nhập. `envFrom` đưa nhiều key vào env; dùng ref từng key khi container chỉ cần một giá trị. |
| Pod `spec.volumes[].configMap.name`, `items[].key/path` và container `volumeMounts[]` | `lesson23-etl-settings` → key `batch-size` → file `batch-size.txt`; volume `settings` nối vào mount `/etc/etl`, nên app đọc `/etc/etl/batch-size.txt`. `readOnly: true` ngăn app ghi qua mount, không ngăn kubelet cập nhật file. Volume cấu hình không cần PVC hay StorageClass. Với Secret dạng file, nguồn là `volumes[].secret.secretName`. |
| Vòng đời env, file và giá trị app dùng | Kubelet cấp env khi khởi động container. Mount cả thư mục có thể nhận cập nhật sau đồng bộ; app phải mở lại và áp dụng giá trị mới. App cache config đọc lúc startup vẫn có thể dùng giá trị cũ. Mount file bằng `subPath` không tự nhận cập nhật. Đổi riêng ConfigMap hay Secret không tự làm Deployment rollout. |
| Nạp credential ≠ xác thực | `credential_loaded=true` chỉ cho biết biến không rỗng; không xác định phiên bản credential, kết nối DB hay quyền SQL. API Secret không thay đổi mật khẩu ở dịch vụ đích. |

## 2. Scaffold và thiết kế đối chứng

| Scaffold | Vai trò |
|---|---|
| [01-configmap.yaml](../thuc-hanh/23-config-secret/01-configmap.yaml) | `lesson23-etl-settings`, giữ `data.batch-size: "500"` trong file để tái hiện mốc đầu. Học viên chỉ patch object live sang `"800"`. |
| [02-config-reader.yaml](../thuc-hanh/23-config-secret/02-config-reader.yaml) | Pod độc lập `lesson23-config-reader`. Cùng key cấp cho env `BATCH_SIZE` và file; script mở lại file mỗi 5 giây, chỉ log ở lần đầu hoặc khi file đổi. Thay Pod từ đúng file này, không tạo lại ConfigMap. |
| [03-secret-reader.yaml](../thuc-hanh/23-config-secret/03-secret-reader.yaml) | Pod độc lập `lesson23-secret-reader`: `lesson23-etl-db` → key `password` → env `DB_PASSWORD`. Script dùng `[ -n ... ]` để kiểm biến không rỗng, chỉ in boolean rồi thoát; biến rỗng thì exit `1`. Không mount Secret dưới dạng file trong lab. |

Hai Pod dùng `restartPolicy: Never`, không tự mount ServiceAccount token, requests `25m/32Mi`, limits `100m/64Mi`. Client `/usr/local/bin/kubectl` v1.33.9, server v1.33.6+k3s1; BusyBox `1.37.0` ghim index `sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec`, registry xác nhận `linux/arm64/v8`. Cả ba scaffold qua client dry-run; vòng lặp được thử riêng với file giả đổi `500 → 800`; script Secret thử cả nhánh có và không có input. Đây là kiểm tra chuẩn bị, không phải bằng chứng kubelet đã cập nhật volume hay nạp Secret.

## 3. Bằng chứng thực hành

| Mốc (giờ Việt Nam) | Quan sát |
|---|---|
| **23:36:20 ngày 19/11** — baseline | Học viên và mentor cùng thấy `env=500 file=500`. Pod UID `0c8012f8-6771-45d2-b341-994de85bf0bc`, container `b152c11e…`, Ready/restart `0` trên `agent-1`. ConfigMap UID `a8d7dafa-624a-4b47-b9ba-8a25fae281d1`, `resourceVersion=781271`. |
| **23:44:46 ngày 19/11** — chỉ đổi ConfigMap live | Học viên dùng merge patch đổi `data.batch-size` sang `"800"`; API trả `800`, log mới `env=500 file=800`. Mentor xác nhận cùng ConfigMap UID (`resourceVersion=781746`), cùng Pod UID, container ID và thời điểm khởi động; restart `0`. Log mới mang thời điểm **23:43:47**. Không đo thời gian từ lúc patch tới lúc kubelet projection đổi. |
| **23:48:22 ngày 19/11** — thay đúng Pod, giữ ConfigMap | Học viên kiểm UID cũ và mốc API `800`, tự xóa đúng Pod rồi `create` lại từ file `02`. Học viên và mentor thấy Pod cùng tên nhưng UID mới `08538e0e-446a-49ae-bd7a-8582499e2ce5`, container `e6139c36…` khởi động **23:46:19**, Ready/restart `0` trên `agent-1`; log `env=800 file=800`. ConfigMap giữ UID, `resourceVersion` và giá trị. |
| **23:54:27 ngày 19/11** — Secret giả | Học viên truyền input giả sinh bằng `openssl rand -hex 24` qua pipe tới `--from-file=password=/dev/stdin`; không điền giá trị vào YAML, argv hay log. Kiểm type `Opaque` và tên key `password`; Pod UID `3f6ab64b-2fc0-4a7f-bae7-d4a8792d6183` `Succeeded`, exit `0`, restart `0`, chỉ log `credential_loaded=true`. Mentor xác nhận ref, metadata và boolean độc lập. Secret UID `76b8e62c-57a2-4bcd-a2ca-99ce9996cb09`. |
| **00:04:16 ngày 20/11** — kiểm chốt | ConfigMap live vẫn `800`; file `01` vẫn `500`. Cùng hai Pod UID trên `agent-1`: config reader `Running`/Ready/restart `0`, Secret reader `Succeeded`/exit `0`/restart `0`. Spec khớp scaffold; Secret cùng UID/type/tên key, hai log đã lọc lần lượt `env=800 file=800` và `credential_loaded=true`. |

Ba log ConfigMap thuộc hai container khác nhau. UID của Pod mới khác còn UID của ConfigMap giữ nguyên; chỉ nhìn tên Pod hoặc `Ready` không đủ phân biệt. Snapshot chốt không phải audit đầy đủ thứ tự lệnh và không còn log của Pod cũ qua tên hiện tại.

## 4. Tái quan sát chỉ đọc

```bash
lab23() {
  /usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
    --context=k3d-de-k3d --namespace=de-lab "$@"
}
lab23 get configmap/lesson23-etl-settings -o 'jsonpath={.data.batch-size}{"\n"}'
lab23 get pod lesson23-config-reader \
  -o 'custom-columns=UID:.metadata.uid,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount'
lab23 logs pod/lesson23-config-reader -c reader --tail=5
```

Kết quả chốt, UID rút gọn: API `800`, Pod `08538e0e…` / `READY=true` / `RESTARTS=0`, log `env=800 file=800`. Dòng API chỉ là cấu hình nguồn; log xác nhận container mới đọc được cả hai nguồn.

```bash
lab23 get secret lesson23-etl-db \
  -o 'go-template=type={{.type}}{{range $key, $_ := .data}} key={{$key}}{{end}}{{"\n"}}'
lab23 get pod lesson23-secret-reader \
  -o 'custom-columns=PHASE:.status.phase,ENV:.spec.containers[0].env[0].name,REF:.spec.containers[0].env[0].valueFrom.secretKeyRef.name,KEY:.spec.containers[0].env[0].valueFrom.secretKeyRef.key'
lab23 logs pod/lesson23-secret-reader -c reader --tail=5
```

Nhìn `type=Opaque key=password`, các cột `PHASE=Succeeded`, `ENV=DB_PASSWORD`, `REF=lesson23-etl-db`, `KEY=password`, và log `credential_loaded=true`. Chỉ đọc các field trên, không dump Secret hay env, không in giá trị hoặc hash credential.

## 5. Review, DevOps và giới hạn

- **Review:** Ba checkpoint `1B, 2C`; `1C, 2A`; `1A, 2B` đều đúng. Review cuối **C**: khi Pod cũ còn dùng được kết nối trong pool nhưng thất bại ở kết nối mới, không suy cả hai Pod có credential cùng phiên bản từ boolean. Đối chiếu ref/key và thời điểm khởi động, thay Pod cũ có kiểm soát, nghiệm thu bằng kết nối mới.
- **Rotation ở hệ thống thật:** Khi dịch vụ đích cho hai credential cùng hiệu lực, cấp bản mới ở đích → cập nhật nguồn Secret → chuyển client (rollout nếu dùng env, reload/reconnect nếu dùng file) → kiểm kết nối mới và quyền cần dùng → thu hồi bản cũ. Nếu đích chỉ chấp nhận một giá trị, phải phối hợp thời điểm chuyển và xử lý gián đoạn. Kết nối cũ trong pool không thay phép thử này.
- **Lab và ngoài lab:** k3d/K3s cung cấp cụm local, API server và kubelet để quan sát; ConfigMap/Secret và mount là cơ chế Kubernetes chuẩn, không dùng `local-path` hay add-on đồng bộ Secret cho bài này. Ngoài lab, xác nhận namespace, quyền giới hạn, mã hóa lúc lưu trữ, tên/key, chủ sở hữu credential và quy trình rollout. Nếu dùng secret manager bên ngoài, DevOps phải cấu hình controller/provider, danh tính và mapping tới Secret hoặc file; kiểm trạng thái đồng bộ trước, rồi ref, thời điểm khởi động/reload và kết nối mới. Nếu GitOps quản lý config, đổi nguồn khai báo thay vì patch live như thí nghiệm.
- **Chưa thực nghiệm:** mount `subPath`, mount Secret dạng file, app giữ config trong RAM, rollout Deployment, đăng nhập/rotation DB thật, đồng bộ secret manager hoặc mã hóa lúc lưu trữ. Các phần đó chỉ là giải thích/tình huống review, không phải thực hành bù.

Giữ ba scaffold, ConfigMap live `800`, Secret giả và hai Pod test. Không có cleanup hay câu review bắt buộc còn chờ; **không chạy lại lệnh đổi hoặc xóa theo mốc cũ**. Chờ Bài 24, chưa mở lab mới.

[Kubernetes v1.33 — ConfigMap](https://v1-33.docs.kubernetes.io/docs/concepts/configuration/configmap/) · [Secret](https://v1-33.docs.kubernetes.io/docs/concepts/configuration/secret/)
