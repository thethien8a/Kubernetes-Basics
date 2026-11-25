# Tổng kết Bài 27 — Helm values và resource được render

[Bài học gốc](../bai-hoc/27-helm.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Scaffold](../thuc-hanh/27-helm/)

**Hoàn thành đầy đủ ngày 2026-11-25, giờ Việt Nam.** Học viên tự render A/B, cài A và upgrade cùng release sang B. Cả học viên và mentor đều kiểm được HTTP marker trước/sau. Review cuối `B` đúng: kết quả sau upgrade không chứng minh không gián đoạn trong rollout.

## 1. Cách đọc một chart

| Nguồn | Điều cần nối |
| --- | --- |
| `Chart.yaml`, `values.yaml`, `templates/` | Metadata và dependency của gói → giá trị mặc định/ghi đè → manifest. Values không phải object để `kubectl apply`. Key mà template không đọc có thể không làm gì dù schema không từ chối; phải nhìn field render. |
| `Chart.yaml.version`, `appVersion`, Deployment `spec.template.spec.containers[].image` | Phiên bản gói, metadata phiên bản app và image reference là ba thông tin khác nhau. `appVersion` chỉ ảnh hưởng image nếu template dùng nó. Pull được image không chứng minh `command`, `args` và đường dẫn config còn tương thích. |
| Release và revision | Release có tên trong namespace. Upgrade cấu hình có thể ghi revision mới trong khi giữ nguyên chart và image. Render cục bộ không tạo release hay xác nhận admission/runtime. |
| `serviceAccount.enabled` của Podinfo, `spec.template.spec.serviceAccountName` | Đọc đúng key của chart, không suy từ ví dụ `create` của chart khác. Nếu chart tham chiếu SA có sẵn thì SA phải tồn tại đúng namespace của Pod; danh tính không tự cấp quyền RBAC. Lab dùng SA `default`, không tạo SA riêng. |
| Tham chiếu Secret/PVC/Ingress ở chart khác | Đối chiếu tên/key mà Pod tham chiếu và nơi cấp Secret, chỉ kiểm metadata/key, không đọc giá trị. Lần Pod volume → PVC → `spec.storageClassName`; class chỉ đích danh không tự chuyển sang class mặc định. Với Ingress, kiểm class/controller thực thi, không suy có đường vào chỉ từ manifest. |
| Podinfo `ui.message`, Deployment `spec.template.spec.containers[].env` | Template đặt `PODINFO_UI_MESSAGE` khi chuỗi không rỗng. Đổi env trong Pod template tạo rollout; tiến trình trong Pod cũ không tự cập nhật env. Podinfo đọc biến khi chạy và trả `message` ở `GET /api/info`. |

## 2. Hook và migration — chỉ học lý thuyết

- `metadata.annotations["helm.sh/hook"]` trên Job cho Helm biết thời điểm gửi Job; Kubernetes Job controller vẫn quản lý Pod làm việc. `pre-upgrade` chờ Job thành công trước khi cập nhật resource thường. Job thường không tự chặn rollout, còn init container chuẩn chạy theo từng Pod, không phải một lần cho cả release.
- Học viên nói chưa hiểu vì sao Job và Deployment liên quan dù đã trả lời các câu thứ tự. Đã tách ví dụ: Pod của Job **thêm** cột `processed_at`, Pod web v2 **đọc** cột đó. Hai resource không quản lý nhau; phụ thuộc là trạng thái PostgreSQL. Nếu DBA thêm đúng cột từ trước, web không cần thấy Job `Complete`.
- Sau khi hiểu quan hệ đó, học viên chốt `B`: với `post-upgrade` và `--wait` trong ví dụ Helm 4.3.0, Helm cập nhật Deployment rồi chờ workload sẵn sàng trước khi tạo hook Job. Nếu web chỉ Ready khi cột có sẵn, Job chưa được tạo; tăng timeout không sửa phụ thuộc vòng.
- Học viên chốt `A`: rollback release chọn manifest cũ làm đích và ghi revision mới; đổi image về v1 không hoàn tác schema hay dữ liệu đã commit. Migration thật cần thiết kế tương thích giữa hai phiên bản và kế hoạch phục hồi DB đã kiểm chứng như Bài 22. Không triển khai PostgreSQL, hook migration hay chạy rollback trong lab này.

## 3. Phạm vi và phiên bản lab

- Context `k3d-de-k3d`, kubeconfig `~/.kube/config`, namespace `lesson27-helm`, release `lesson27-podinfo`. Client `/usr/local/bin/kubectl` `v1.33.9`, API server `v1.33.6+k3s1`. Preflight namespace trả `NotFound`; học viên tạo nó bằng lần `helm install --create-namespace`.
- Gói chính thức [podinfo-6.17.0.tgz](https://stefanprodan.github.io/podinfo/podinfo-6.17.0.tgz), SHA-256 `d3d67f460f9f94bb6d10950315fc0953799efc0ee60332e3c475e755e99c0e04` khớp index. Chart version và `appVersion` đều `6.17.0`, yêu cầu `kubeVersion: '>=1.23.0-0'`. Image `ghcr.io/stefanprodan/podinfo:6.17.0` có manifest `linux/arm64` đã đối chiếu qua registry.
- Helm trên `PATH` là `v4.3.0+gbec5b06`, ngoài dải hỗ trợ cho API server 1.33. Render ban đầu bằng bản này vẫn là phép kiểm cục bộ. Học viên tải Helm Darwin ARM64 `v4.2.4+g3900f43` riêng tại `~/.local/share/k8s-practice/lesson27/helm-v4.2.4/darwin-arm64/helm`; checksum chính thức đạt `OK`, mentor đối chiếu binary khớp archive và dùng đúng bản để kiểm. Không thay `PATH`, cấu hình mặc định hay nâng cluster. `--kube-version 1.33.6` chỉ là input của render, không sửa version skew.
- Inventory render mặc định: một Deployment một replica, Service `ClusterIP` có cổng `http:9898` và `grpc:9999`, ba Pod có `helm.sh/hook: test-success` (alias hook test), không được tạo ở lần install thường. `/data` là `emptyDir`, không có PVC. Không cấu hình Secret ứng dụng, Redis, Ingress hay cổng host; inventory manifest không tính object Helm dùng lưu lịch sử release.

## 4. Thực hành A/B và minh chứng

[A](../thuc-hanh/27-helm/01-values-a.yaml) và [B](../thuc-hanh/27-helm/02-values-b.yaml) chỉ khác `ui.message`: `lesson27-a` → `lesson27-b`. So đúng Deployment render, tránh đem tên động của Pod test vào phép so. Cả hai bên đã tự thấy `name: PODINFO_UI_MESSAGE` giữ nguyên và `value` chuyển A → B.

Từ gốc repo, lệnh tái quan sát chỉ đọc (đổi `values_file` để xem B):

```bash
helmbin="$HOME/.local/share/k8s-practice/lesson27/helm-v4.2.4/darwin-arm64/helm"
chart=https://stefanprodan.github.io/podinfo/podinfo-6.17.0.tgz
values_file=roadmap-k3d/thuc-hanh/27-helm/01-values-a.yaml

"$helmbin" template lesson27-podinfo "$chart" \
  --namespace lesson27-helm --kube-version 1.33.6 \
  --show-only templates/deployment.yaml -f "$values_file" \
  | grep -A 1 -F 'name: PODINFO_UI_MESSAGE'
```

| Giờ Việt Nam | Bằng chứng nghiệm thu |
| --- | --- |
| **13:51:54 — Cài A** | Học viên cài chart bằng `01-values-a.yaml`, `--create-namespace --wait --timeout 3m`; thấy Deployment `READY 1/1`, Service `ClusterIP:9898`. Mentor xác nhận release revision 1 `deployed`, Deployment generation 1/env A, Pod A Ready. Học viên và mentor đều thấy `lesson27-a` khi gọi endpoint thật qua API proxy. |
| **14:07:27 — Upgrade B** | Học viên dùng `helm upgrade` cùng release/chart/namespace, chỉ đổi file sang `02-values-b.yaml` và giữ `--wait --timeout 3m`. Học viên thấy revision 2 `deployed`, Deployment `READY=1/1`, `PODINFO_UI_MESSAGE=lesson27-b`, HTTP `lesson27-b`. Mentor kiểm độc lập: revision 1 `superseded`, revision 2 `deployed`, cùng `CHART=podinfo-6.17.0` và `APP VERSION=6.17.0`. Deployment giữ UID, generation `1 → 2`; ReplicaSet cũ về `0`, Pod B mới Ready, EndpointSlice chuyển backend từ A sang B. Service giữ UID/ClusterIP. |
| **14:33:53 — Snapshot chốt** | Namespace `Active`; revision 2 và marker B giữ nguyên. Deployment generation/observedGeneration `2/2`, desired/updated/ready/available đều `1`. Pod B chạy trên `server-0`, `Ready=True`, restart `0`, không deletionTimestamp; cả ba node báo `Ready`. Không thấy Job/PVC/Ingress hay Pod test trong inventory namespace. Mentor GET lại ứng dụng và thấy B. |

Các mốc thời gian 13:51:54 và 14:07:27 là thời điểm lưu trong lịch sử release; không phải phép đo uptime hoặc thời điểm của mọi request. Không chạy lại `install`/`upgrade` để tái hiện snapshot.

Lệnh HTTP giống nhau cho A và B; chỉ đọc trường `message` đã biết:

```bash
/usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" \
  --context k3d-de-k3d --request-timeout=8s \
  get --raw '/api/v1/namespaces/lesson27-helm/services/lesson27-podinfo:http/proxy/api/info' \
  | jq -er '.message | select(. == "lesson27-a" or . == "lesson27-b")'
```

| Object | UID và thay đổi |
| --- | --- |
| Namespace `lesson27-helm` | `b0b888a3-eb58-4893-9a17-5f5c2140fd86` |
| Deployment `lesson27-podinfo` | `8645353a-fd6a-4f05-ba77-cc1ad929e507`, giữ nguyên |
| Service `lesson27-podinfo` | `2cdf4b9d-3639-406b-974d-9abe979ff145`, giữ `10.43.172.30` |
| ReplicaSet A → B | `4ba2584e-4bf7-4ecd-8843-f30e11c4ce48` → `37021e99-f9ea-4caa-ab6f-e63229bcd69b` |
| Pod A → B | `lesson27-podinfo-856fb75d97-5wl6c` / `d8716ed8-97ad-4293-b02b-24f889d4e677` → `lesson27-podinfo-967db9d96-p49tt` / `63e619f9-849d-43c4-8068-8e4d943b3a76`. Cả hai được quan sát trên `server-0` với cùng runtime imageID digest `sha256:fa2f27c1a8561097e5144bfc0853eba6054d743b68b03de4cad4675616ddefb0`. |
| EndpointSlice `lesson27-podinfo-4hjzv` | `e3a98b46-7c89-4aac-a518-e3a2427e1c3d`, giữ UID và trỏ đúng Pod B Ready tại snapshot chốt |

## 5. Đem ra ngoài lab

- **Mặc định cần đánh giá:** chart đặt `spec.strategy.rollingUpdate.maxUnavailable: 1` với `spec.replicas: 1`. Có thể có lúc không còn replica Available trong rollout; không khẳng định lần thử đã gián đoạn. Học viên chọn `B` đúng ở review cuối: `deployed`, `1/1` và một HTTP marker sau rollout chỉ chứng minh trạng thái sau cùng, không đo request trong lúc chuyển phiên bản.
- **Cần DevOps xác nhận:** nguồn/phiên bản chart và image registry được duyệt, client tương thích API, namespace/quyền cài và quản lý release, quota/admission; controller/class, Secret/SA ngoài chart và quyền tương ứng nếu có. Với chart dữ liệu, kiểm retention/PVC và kế hoạch migration/backup/restore trước upgrade hoặc uninstall. Không suy `local-path` của K3s là mặc định ở cluster khác; lab này không dùng nó.
- **Giới hạn của HTTP lab:** dùng API proxy của Kubernetes và quyền `get` trên `services/proxy`, không dùng port mapping của k3d/OrbStack hay mở listener trên Mac. Ngoài lab, quyền proxy có thể không được cấp; kiểm từ client được phép theo đường thực tế (DNS Service/NetworkPolicy, hoặc ingress/LB/DNS/TLS nếu có yêu cầu). Phép thử này không xác nhận các đường đó, HA hay tương thích policy ở cluster công ty.
- Giữ namespace và release revision 2, Deployment, Service, ReplicaSets, Pod B và hai file values. Không có recovery/cleanup bắt buộc; không chạy test hook, rollback, uninstall hoặc đụng workload bài khác để chốt.

Nguồn: [Helm values](https://helm.sh/docs/chart_template_guide/values_files/), [Helm hooks](https://helm.sh/docs/topics/charts_hooks/), [thứ tự upgrade Helm v4.3.0](https://github.com/helm/helm/blob/v4.3.0/pkg/action/upgrade.go#L481-L512), [bảng tương thích Helm](https://helm.sh/docs/topics/version_skew/), [chart Podinfo](https://github.com/stefanprodan/podinfo/tree/6.17.0/charts/podinfo), [Podinfo HTTP info handler](https://github.com/stefanprodan/podinfo/blob/6.17.0/pkg/api/http/info.go).
