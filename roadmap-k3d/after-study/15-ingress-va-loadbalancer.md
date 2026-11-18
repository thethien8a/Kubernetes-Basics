# Tổng kết Bài 15 — Ingress và LoadBalancer

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/15-ingress-va-loadbalancer.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/16-dns-tls.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-09**, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phạm vi:** context `k3d-de-k3d`, kubeconfig `~/.kube/config`; Ingress và backend ở `de-lab`, controller/ServiceLB ở `kube-system`.
- **Kết quả:** **8/8 câu trắc nghiệm đúng**; Host match trả HTTP 200 và đúng marker ứng dụng, Host không match trả 404, Service nội bộ vẫn trả 200/marker.
- **Kiểm chứng đóng bài:** mentor kiểm tra độc lập **22:38:02–22:38:03 ngày 09/11**; Ingress khớp scaffold, backend Ready, ba node Ready, Traefik 1/1 và ServiceLB 3/3.
- **Ranh giới:** mentor chỉ tạo scaffold local, kiểm tra chỉ đọc và lưu tài liệu khi chốt bài; không apply/patch/delete/restart workload hoặc node. Học viên xác nhận đã đổi setting OrbStack và đã sửa sự cố agent; phương pháp sửa node cụ thể không được suy từ snapshot.
- **Giữ tài nguyên:** Ingress và backend tiếp tục tồn tại; không cleanup, không có recovery hoặc câu review còn chờ. Chưa mở Bài 16.

## 1. Phiên bản và thành phần đã xác nhận

| Thành phần | Phiên bản/cấu hình trong lượt học |
|---|---|
| k3d | `v5.8.3` |
| Kubernetes/K3s API server | `v1.33.6+k3s1`; API `networking.k8s.io/v1` hỗ trợ Ingress |
| kubectl | `/usr/local/bin/kubectl` `v1.33.9`; không dùng bản mới trên PATH hoặc nâng cấp tool |
| Nodes | Một server, hai agent, tất cả `arm64` |
| Traefik | `rancher/mirrored-library-traefik:3.5.1` |
| Chart Traefik do K3s cung cấp | `traefik-37.1.1+up37.1.0.tgz`, đối chiếu HelmChart live và manifest K3s đúng tag |
| ServiceLB | `rancher/klipper-lb:v0.4.13`, host ports 80/443 |
| Ứng dụng test | Dùng lại BusyBox/backend Bài 14; không tạo Deployment, Service hoặc image mới |

Image backend giữ nguyên:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

Image live và runtime imageID khớp pin. Đây là backend hiện có chạy trên node ARM64, không phải một lượt kiểm chứng pull mới trên mọi node.

## 2. Concept và đường đi đã học

### Service type không thay thế hạ tầng thực thi

- **ClusterIP:** frontend ổn định cho client có đường mạng tới Service; không tự cấp đường truy cập từ Mac/LAN/Internet.
- **NodePort:** thêm đường truy cập qua cổng trên địa chỉ node, theo implementation/config; node-container trong k3d không tự trở thành `localhost` trên Mac.
- **LoadBalancer:** yêu cầu implementation/controller và hạ tầng cung cấp frontend; không tự bảo đảm có public IP hoặc firewall cho phép.
- **Ingress:** rule HTTP(S) chọn backend theo Host/path; cần controller xử lý class và đường tới frontend. Không dùng nguyên rule HTTP này cho PostgreSQL hoặc Spark RPC.

| Thành phần trong lab | Trách nhiệm |
|---|---|
| k3d serverlb | Proxy container bên ngoài Kubernetes, đưa traffic từ cổng publish tới node-container; không chọn ứng dụng theo HTTP Host/path. |
| K3s ServiceLB | Thực thi Service `type: LoadBalancer` bằng host ports khả dụng trên node; không phải Ingress controller. |
| Traefik | Theo dõi Ingress qua Kubernetes provider và thực thi reverse proxy HTTP(S); dùng rule Host/path để chọn backend. |

Đường logic của phép thử:

```text
Mac 127.0.0.1:8085
  -> cổng 80 của k3d serverlb
  -> node:80 / đường LoadBalancer của K3s
  -> Traefik áp rule Host/path
  -> backend được tham chiếu bởi service-dns-svc:80
  -> Pod 10.42.0.44:8080
```

Đây là mô hình logic dựa trên config/inventory và HTTP, không phải packet capture. Traefik có thể lấy địa chỉ backend và gọi Pod trực tiếp; không khẳng định traffic bắt buộc đi xuyên ClusterIP hoặc object Ingress/EndpointSlice.

Ingress backend là **tham chiếu**, không phải quan hệ sở hữu Service/Pod. Trong cấu hình này, chỉ xóa Ingress không xóa Service/Pod theo; client trong cluster vẫn có thể gọi Service nếu các điều kiện khác giữ nguyên. Đây là tình huống review, không thực nghiệm xóa Ingress.

## 3. Scaffold và các field quan trọng

File mới duy nhất của lab: [01-ingress.yaml](../thuc-hanh/15-ingress-va-loadbalancer/01-ingress.yaml).

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lesson15-web
  namespace: de-lab
  labels:
    team: data
    environment: lab
    lesson: "15"
    app: ingress-demo
spec:
  ingressClassName: traefik
  rules:
    - host: lesson15.test
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: service-dns-svc
                port:
                  number: 80
```

| Resource/field | Ý nghĩa, liên kết và lỗi dễ nhầm |
|---|---|
| Ingress `metadata.namespace: de-lab` | Backend Service phải cùng namespace; không trỏ trực tiếp sang Service namespace khác bằng field này. |
| Ingress labels | Dùng phân loại/inventory; không phải selector chọn backend Pod. |
| `spec.ingressClassName: traefik` | Tham chiếu class tồn tại, có `spec.controller: traefik.io/ingress-controller`; đặt tên tùy ý không tự cài controller. |
| `spec.rules[].host: lesson15.test` | Match hostname HTTP; không tạo DNS record và không xác thực danh tính người gọi. |
| `http.paths[].path: /`, `pathType: Prefix` | Match các đường dẫn từ gốc `/` khi Host phù hợp; không tự rewrite path hoặc bảo đảm ứng dụng có nội dung ở mọi path. |
| `backend.service.name: service-dns-svc` | Tham chiếu Service, không phải Deployment/Pod name. |
| `backend.service.port.number: 80` | Cổng Service; không phải cổng Mac 8085, NodePort hoặc cổng Pod 8080. |
| Service `port: 80`, `targetPort: http` | Named targetPort resolve tới cổng Pod `http:8080`; Service vẫn là ClusterIP. |
| k3d `ports[].port: 8085:80`, `nodeFilters: [loadbalancer]` | Host port -> container port trên k3d serverlb; đây là cấu hình k3d, không phải manifest Ingress. |

Scaffold đã qua `create --dry-run=client --validate=strict`; Ingress live khớp toàn bộ spec. Dry-run chỉ là kiểm tra cấu hình, không thay runtime. Không thêm annotation, TLS, middleware hoặc controller mới.

## 4. Lệnh quan sát và bằng chứng

Chạy từ `roadmap-k3d/`, dùng helper đã giao:

```bash
k15() {
  /usr/local/bin/kubectl \
    --kubeconfig="$HOME/.kube/config" \
    --context=k3d-de-k3d --request-timeout=10s "$@"
}
```

Trước mỗi nhóm kiểm tra live, mentor xác nhận context và namespace Active. Có thể tự tái quan sát:

```bash
k15 config get-contexts k3d-de-k3d
k15 get namespaces de-lab kube-system \
  -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase'
```

Context được kiểm là `k3d-de-k3d`; hai namespace đều `Active`. Docker context `orbstack` chỉ chọn engine chạy k3d, không phải cluster Kubernetes `orbstack`.

### 4.1 Resource và tham chiếu

Lệnh đã giao để học viên tự triển khai, **không cần chạy lại để review**:

```bash
k15 -n de-lab apply \
  -f thuc-hanh/15-ingress-va-loadbalancer/01-ingress.yaml
```

Lệnh chỉ đọc:

```bash
k15 -n de-lab get ingress lesson15-web \
  -o 'custom-columns=NAME:.metadata.name,CLASS:.spec.ingressClassName,HOST:.spec.rules[*].host,SERVICE:.spec.rules[*].http.paths[*].backend.service.name,PORT:.spec.rules[*].http.paths[*].backend.service.port.number'
```

Snapshot mentor, custom columns:

```text
NAME           CLASS     HOST            SERVICE           PORT
lesson15-web   traefik   lesson15.test   service-dns-svc   80
```

Nhìn CLASS/HOST/SERVICE/PORT để kiểm tham chiếu; object tồn tại chưa chứng minh đường HTTP hoạt động. Metadata ghi thời điểm tạo **21:44:34 ngày 09/11**, generation 1. Mentor quan sát Ingress đã tồn tại lúc 22:24, không suy thứ tự mọi lệnh học viên chạy từ metadata.

### 4.2 Host đúng và Host sai: chỉ thay một điều kiện

Host đúng:

```bash
curl --noproxy '*' --connect-timeout 3 --max-time 5 -sS \
  -H 'Host: lesson15.test' \
  -w '\nHTTP %{http_code}\n' http://127.0.0.1:8085/
```

Kết quả mentor kiểm độc lập lúc 22:24 và chạy lại trong snapshot đóng bài 22:38, rút gọn:

```text
lesson14-service-dns-ok
HTTP 200
```

Giữ URL, chỉ đổi Host:

```bash
curl --noproxy '*' --connect-timeout 3 --max-time 5 -sS \
  -H 'Host: other.test' \
  -w '\nHTTP %{http_code}\n' http://127.0.0.1:8085/
```

Kết quả thực tế:

```text
404 page not found
HTTP 404
```

- URL quyết định địa chỉ/cổng kết nối; `-H` đặt hostname HTTP để controller match rule, không sửa DNS.
- Đọc cả HTTP status và marker; 200 của một trang mặc định khác không đủ nghiệm thu.
- Marker vẫn mang tên Bài 14 vì dùng lại ứng dụng đó.
- Cả hai lệnh curl có exit code 0 trong lượt kiểm tra; nhận 404 không tự khiến curl mặc định thoát lỗi.
- Đây là kết quả mentor tự kiểm tra và đã trình bày lệnh/output trong chat; không ghi thành học viên đã gửi hoặc xác nhận nhìn thấy mọi output.

### 4.3 Đối chiếu với Service nội bộ

```bash
k15 -n de-lab exec service-dns-server-758b6cd595-j52cl -c http -- \
  wget -Y off -S -T 3 -O - http://service-dns-svc:80/
```

Mentor kiểm lúc 22:27 và chạy lại trong snapshot 22:38; phần liên quan:

```text
HTTP/1.1 200 OK
lesson14-service-dns-ok
```

Trước exec đã đối chiếu image/command/script của fixture và không có declared env/envFrom hoặc volume. Nguồn của phép thử này là **backend Pod hiện tại**, không phải client khác namespace hoặc máy LAN; không dùng nó làm bằng chứng cross-node. Service vẫn cùng UID/ClusterIP của Bài 14.

## 5. An toàn frontend và sự cố nền trong lượt học

### OrbStack LAN policy

Mapping Docker thực tế vẫn là `0.0.0.0:8085` và `[::]:8085` -> container port 80. API giữ `127.0.0.1:6445` -> 6443. Gọi loopback thành công không chứng minh cổng chỉ mở local.

Học viên chọn phương án tắt LAN forwarding cho **toàn bộ Docker trên OrbStack**, được giải thích phạm vi trước khi thao tác:

```bash
orb config set docker.expose_ports_to_lan false
```

Mentor tự kiểm bằng lệnh chỉ đọc:

```bash
orb config get docker.expose_ports_to_lan
```

Kết quả sau học viên báo xong và khi đóng bài:

```text
false
```

Đây là policy forwarding của OrbStack, không phải đổi port binding Docker thành loopback hoặc sửa `k3d-config.yaml`. Theo tài liệu OrbStack, tắt setting giới hạn forwarded ports về Mac; chưa có phép thử độc lập từ máy LAN, không ghi thành đã kiểm chứng mọi đường truy cập mạng.

Đã đối chiếu CLI và mã nguồn **k3d v5.8.3**: `--port-add` chỉ thêm/bỏ qua binding trùng, không xóa wildcard binding cũ; thêm loopback binding không phải cách loại bỏ wildcard. Không chạy node edit, tạo lại proxy hoặc tạo lại cluster.

### Sự cố agent: không quy nguyên nhân khi thiếu bằng chứng

- Lúc 17:28–17:29, hai agent `Ready=Unknown/NodeStatusUnknown`, Lease dừng cập nhật và có taint unreachable. Docker container còn running nhưng process list chỉ có docker-init, k3d-entrypoint và sleep, không thấy K3s.
- Backend cũ của Bài 14 trên agent-0 có deletionTimestamp; backend mới `j52cl` trên server đã Ready. Không coi phase Running hoặc container-status cũ trên node mất liên lạc là bằng chứng ứng dụng còn hoạt động.
- Học viên sau đó báo đã sửa; mentor xác minh 21:14 ba node Ready, Lease mới, không taint/cordon/pressure; snapshot đóng bài 22:38 vẫn đạt.
- Không có bằng chứng đủ để quy lỗi cho setting LAN, xác định ai/cơ chế nào restart node-container hoặc khẳng định đã sửa tận gốc. Không suy ra lệnh sửa node cụ thể mà học viên đã dùng.
- Đây là sự cố preflight thực tế của Bài 15, không mở lại phần mô phỏng node failure đã bỏ qua của Bài 12. Mentor không restart hoặc sửa node.

## 6. Đối chiếu lab với thực tế và hợp đồng DE–platform

Học viên hỏi vì sao thực tế ít thấy URL dùng cổng 8085. Đây là thắc mắc về tính chuyển giao kiến thức, **không phải đáp án sai**.

- `8085` là cổng host được chọn cho mapping local, không phải yêu cầu của Ingress/Kubernetes. Cổng tùy chỉnh vẫn có thể dùng thực tế; với web UI người dùng thường thấy HTTPS 443 và không cần ghi cổng.
- Giữ 8085 giúp kiểm routing mà không phải đổi môi trường. Chỉ đổi thành 80/443 làm URL giống thực tế hơn, không tự có LB, DNS, TLS hoặc HA. Khuyến nghị giữ cổng lab và đối chiếu vai trò từng thành phần.
- Ví dụ thực tế đã giải thích: DNS `ui.data.example.com` -> endpoint LB; client -> LB:443 -> Traefik HTTPS -> backend Service:80 -> Pod:8080. Giả định LB chuyển TCP 443, TLS kết thúc tại Traefik; LB có thể private qua mạng công ty/VPN.
- Với mô hình Traefik sau LB, trích đoạn Service phía trước controller có `spec.type: LoadBalancer`, `ports[].port: 443`, `targetPort: websecure`, giả định Pod controller có cổng tên đó. Đây là cấu hình tham khảo, không apply trong lab; không phải Helm values dùng chung mọi chart.
- On-prem cần implementation LB/VIP hoặc frontend cùng address/routing/firewall. Cloud cần controller tích hợp và hạ tầng/quyền/subnet phù hợp; `type: LoadBalancer` không tự quyết định private/public.
- Không phải mọi controller đều là proxy trong data path. Ví dụ AWS Load Balancer Controller cấu hình ALB; traffic qua ALB tới targets, không chạy xuyên Pod controller. Ví dụ AWS chỉ học lý thuyết, không provision cloud.

**DE cần yêu cầu/xác nhận với platform:**

1. UI/API nào cần expose, namespace/chủ sở hữu, nhóm client và phạm vi private/public.
2. Controller/IngressClass được cấp; endpoint/frontend, listener/ports và route/firewall cho phép nguồn truy cập.
3. Hostname/DNS record trỏ tới endpoint nào; certificate/TLS termination, gia hạn và cơ chế authentication/authorization do ai quản lý.
4. Backend Service name/port, endpoints Ready và listener ứng dụng; không đổi backend port thành 443 chỉ vì frontend dùng HTTPS.
5. Bằng chứng/debug từ đúng nguồn: resolver nếu dùng DNS -> kết nối frontend/TLS nếu có -> class/Host/path -> Service port -> EndpointSlices/Pod readiness -> listener/application. Không chữa app port khi host port chưa được publish.

## 7. Review và giới hạn minh chứng

| Khối | Đáp án học viên | Nội dung đã kiểm tra |
|---|---|---|
| NodePort/LoadBalancer | `1B, 2C` | NodePort không tự publish ra Mac; LoadBalancer cần implementation và chưa chắc public. |
| Ingress/class/backend/Host | `1C, 2A, 3B` | Object không thay controller; tham chiếu Service port; Host sai không match rule. |
| Phạm vi local | `B` | Gọi loopback thành công không chứng minh dịch vụ bị giới hạn ở local. |
| Review chốt | `1B, 2C` | Chỉ xóa Ingress không xóa Service/Pod; Host matching không phải xác thực người dùng. |

Tổng **8/8 đúng**, không có câu sai hoặc đang chờ. Hai câu chốt là tình huống giả định; không thực nghiệm xóa Ingress hoặc triển khai authentication.

Các request test không có credential mà Host đúng vẫn được route. Host có thể do client tự đặt, không phải mật khẩu. Chưa kiểm chứng DNS OS/public/private DNS, HTTPS/SNI/certificate, authentication/authorization, client LAN/Internet, cloud LB, NodePort runtime, failover/HA, hiệu năng hoặc packet flow. Không coi Ingress status có địa chỉ là bằng chứng endpoint public hoặc Mac/LAN route được tới địa chỉ đó. Các node vẫn chung host vật lý.

## 8. Snapshot giữ lại khi đóng bài

Thời điểm **22:38:02–22:38:03 ngày 2026-11-09**, context `k3d-de-k3d`; `de-lab`, `kube-system`, `kube-node-lease` Active:

| Resource | Identity và trạng thái |
|---|---|
| Ingress `de-lab/lesson15-web` | UID `ca30a22b-6466-4808-b31a-53b18c726cbc`, generation 1, không deletionTimestamp; spec khớp scaffold. |
| Service `de-lab/service-dns-svc` | UID `290cea51-38e4-47ed-8044-845f06fd10b1`, ClusterIP `10.43.62.113`, port 80 -> named targetPort http. |
| Deployment `de-lab/service-dns-server` | UID `5269a553-0ac4-4328-97e7-07cf81ced00d`, generation 1, desired/ready/available 1. |
| Backend Pod `service-dns-server-758b6cd595-j52cl` | UID `edb615d0-460b-45e3-a962-ec2748c8584b`, IP `10.42.0.44`, server-0, Running/Ready/restart 0, không deletionTimestamp. Owner ReplicaSet UID `8cf96dde-01de-4286-8917-401473701806`. |
| EndpointSlice `service-dns-svc-hnbtr` | UID `bb6a1e0d-15c1-4c92-aa16-56d19ab50865`, đúng backend UID/IP:8080, ready/serving=true, terminating=false. |
| IngressClass `traefik` | UID `689ae1a6-bdb5-4f5f-9842-5ef3b17ccc72`, controller `traefik.io/ingress-controller`. |
| Deployment `kube-system/traefik` | UID `5c6eeb18-6090-49a4-b874-ff1c3917ad8d`, desired/ready 1. |
| DaemonSet `svclb-traefik-0e8ce95e` | UID `7d217c4e-52c7-4017-b0eb-a05292d91f61`, desired/ready 3, host ports 80/443. |

Ba node Ready, UID giữ nguyên, không taint/unschedulable, Memory/Disk/PIDPressure=False và Lease còn mới. Hai GET local và GET Service nội bộ đều được chạy lại trong lượt snapshot này. Giữ Ingress/scaffold/backend và setting `docker.expose_ports_to_lan=false`; không cleanup hoặc bật LAN lại.

Backend hiện tại **khác Pod 9zlq8 trong snapshot đóng Bài 14**; snapshot Bài 14 vẫn là lịch sử đúng thời điểm, không dùng UID/IP cũ như identity hiện tại. Lượt này không kiểm lại các client Bài 14 hoặc mọi workload bài trước.

**Bài 15 Hoàn thành đầy đủ.** Tổng học xong **15/32**, nghiệm thu đầy đủ **13/32** (01–07, 09–11 và 13–15); giữ nguyên phạm vi đã chốt của Bài 08/12. Chờ **Bài 16 — DNS và TLS**, chưa giảng/tạo scaffold. Đây là lượt lưu tổng kết và tiến độ gộp khi toàn bài đạt; không commit/push.

## Nguồn đã đối chiếu

- [Ingress — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/ingress/) và [Ingress API v1](https://v1-33.docs.kubernetes.io/docs/reference/kubernetes-api/service-resources/ingress-v1/).
- [Service — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/service/).
- [k3d v5.8.3 — exposing services](https://k3d.io/v5.8.3/usage/exposing_services/) và [config files](https://k3d.io/v5.8.3/usage/configfile/).
- [k3d v5.8.3 NodeEdit/NodeReplace](https://github.com/k3d-io/k3d/blob/v5.8.3/pkg/client/node.go#L937-L1057) và [CLI node edit đúng tag](https://github.com/k3d-io/k3d/blob/v5.8.3/cmd/node/nodeEdit.go).
- [Manifest Traefik của K3s v1.33.6+k3s1](https://raw.githubusercontent.com/k3s-io/k3s/v1.33.6%2Bk3s1/manifests/traefik.yaml).
- [K3s networking services/ServiceLB](https://docs.k3s.io/networking/networking-services); không dùng ví dụ Helm values của chart mới để thay cấu hình chart 37 đã pin.
- [Traefik v3.5.1 Kubernetes Ingress provider](https://raw.githubusercontent.com/traefik/traefik/v3.5.1/docs/content/providers/kubernetes-ingress.md).
- [OrbStack Docker port forwarding](https://docs.orbstack.dev/docker/network#port-forwarding).
- [AWS EKS ALB Ingress](https://docs.aws.amazon.com/eks/latest/userguide/alb-ingress.html), dùng để đối chiếu kiến trúc, không phải môi trường lab đã triển khai.
