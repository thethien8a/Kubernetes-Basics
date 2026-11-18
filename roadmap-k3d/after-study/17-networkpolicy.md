# Tổng kết Bài 17 — NetworkPolicy và egress

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/17-networkpolicy.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/18-vong-doi-du-lieu.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-17**, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Thực hành chính:** ngày **2026-11-16**; review cuối đạt `1B, 2C, 3A` ngày 17/11.
- **Kiểm chốt độc lập:** **14:03:27–14:03:30 ngày 17/11/2026**; DNS và toàn bộ ma trận HTTP vẫn đạt.
- **Phạm vi:** context `k3d-de-k3d`, namespace riêng `lesson17-netpol`; chỉ đọc thông tin DNS hệ thống trong `kube-system`.
- **Kết quả:** chứng minh baseline, deny/allow ingress, deny egress, mở riêng DNS rồi mở đúng backend. A được phép; B vẫn bị chặn ở ingress server.
- **Ranh giới:** học viên tự apply tài nguyên. Mentor giải thích, chuẩn bị scaffold, client dry-run và kiểm tra chỉ đọc; không apply live, xóa/restart workload, sửa node, cấu hình DNS hệ thống hoặc đọc credential thay học viên.
- **Khi đóng bài:** giữ namespace, ba Pod, một Service, một EndpointSlice và năm NetworkPolicy; không thực hiện hoặc ghi nhận đã cleanup. Bài gốc không yêu cầu xóa fixture.

## 1. Challenge và đầu ra

Tạo server và hai client có nhãn khác nhau trong namespace riêng. Kiểm chứng bằng kết nối mới có timeout:

1. Chưa có NetworkPolicy trong namespace test: cả A và B gọi server được.
2. Cô lập ingress server: cả hai bị chặn; ứng dụng không bị dừng.
3. Thêm allow ingress chỉ cho client hợp lệ: A được phép, B vẫn bị chặn.
4. Tạo Service và kiểm DNS/HTTP riêng biệt.
5. Cô lập egress A: A mất DNS và HTTP trực tiếp tới Pod IP; B vẫn resolve được.
6. Mở riêng DNS cho A: resolve phục hồi nhưng HTTP vẫn bị chặn.
7. Mở đúng backend cho A: HTTP qua cả Pod IP và tên Service phục hồi; B vẫn bị chặn.

Tất cả dữ liệu là marker giả `lesson17-netpol-ok`. Không triển khai database, external API, auth hoặc production platform để làm bài.

## 2. Mental model đã học

### 2.1 Resource không tự thực thi việc lọc traffic

`NetworkPolicy` là khai báo Kubernetes API. Networking implementation phải hỗ trợ và thực thi nó; API nhận YAML hoặc object tồn tại chưa chứng minh có cách ly.

Theo tài liệu K3s, bản phân phối có controller NetworkPolicy tích hợp dựa trên thư viện netpol của kube-router. Trong bài, bằng chứng enforcement là kết quả allow/deny có đối chứng trong lab K3s, không phải suy từ tên một Pod/controller hoặc chỉ từ tài liệu mặc định. Không kiểm tra cơ chế iptables/drop/reject bằng packet capture.

Namespace khác nhau không tự tạo tường lửa. Service, DNS, TLS và quyền ứng dụng cũng không thay thế NetworkPolicy.

### 2.2 Hai phía của một kết nối

```text
Client Pod → Egress phía nguồn → Ingress phía đích → Server Pod
```

- Khi hai phía bị isolate, kết nối mới cần được cả hai phía cho phép.
- Một Pod bị isolate theo một chiều khi có policy chọn nó cho chiều đó; không cần policy mang một tên đặc biệt như `default-deny`.
- Các quyền allow cùng áp dụng được cộng hợp. Không ưu tiên theo thứ tự tạo hoặc độ cụ thể.
- `ingress: []` / `egress: []` không đóng góp quyền allow; không phải rule deny ưu tiên cao phủ quyết policy khác.
- Hai rule cho `A → TCP/8080` và `B → TCP/9090` chỉ mở hai cặp đó, không tự mở mọi nguồn tới mọi cổng.
- Phản hồi thuộc kết nối được phép được ngầm cho phép. Server chủ động mở kết nối mới tới client là luồng khác; đây là concept đã review, không có thí nghiệm reverse connection riêng.

Chữ `Ingress` trong `policyTypes` là chiều kết nối đi vào Pod, không phải resource `kind: Ingress` hay rule HTTP Host/path.

### 2.3 Phạm vi selector và AND/OR

- `spec.podSelector`: chọn Pod chịu policy trong namespace của policy.
- `podSelector: {}` ở vị trí này chọn mọi Pod trong namespace đó, không phải toàn cluster.
- Peer `podSelector` đứng riêng trong `from`/`to`: chọn Pod cùng namespace với policy.
- Một peer có cả `namespaceSelector` và `podSelector`: kết hợp **AND**.
- Hai peer entries riêng: kết hợp **OR**.

Hai đoạn dưới là ví dụ đã giảng, không triển khai namespace `analytics` hoặc policy OR rộng này:

```yaml
from:
  - namespaceSelector:
      matchLabels:
        kubernetes.io/metadata.name: analytics
    podSelector:
      matchLabels:
        access: allowed
```

Chọn Pod `access=allowed` trong `analytics`. Nếu tách thành:

```yaml
from:
  - namespaceSelector:
      matchLabels:
        kubernetes.io/metadata.name: analytics
  - podSelector:
      matchLabels:
        access: allowed
```

thì cho mọi Pod trong `analytics` **hoặc** Pod `access=allowed` trong namespace của policy. Không có nghĩa chọn label đó trên toàn cluster.

### 2.4 DNS và kết nối ứng dụng là hai quyền riêng

```text
Client → DNS:53                 Phân giải tên
Client → backend TCP/8080       Gọi ứng dụng
```

Mở backend không tự mở DNS. Mở DNS không tự cho phép gọi các IP DNS trả về. NetworkPolicy chuẩn không tự làm allow-list tên miền tùy ý, cấp quyền SQL/IAM hoặc thực hiện HTTP authorization.

## 3. Scaffold, phiên bản và cấu hình

Mười scaffold được tạo đúng lúc sau giải thích, không tạo trước cả khóa:

| File | Resource / vai trò |
|---|---|
| [00-namespace.yaml](../thuc-hanh/17-networkpolicy/00-namespace.yaml) | Namespace `lesson17-netpol`, tách khỏi workload các bài trước. |
| [01-server.yaml](../thuc-hanh/17-networkpolicy/01-server.yaml) | Naked Pod `netpol-server`, `app=server`, `lesson=17`; HTTP `0.0.0.0:8080`. |
| [02-client-a.yaml](../thuc-hanh/17-networkpolicy/02-client-a.yaml) | Naked Pod `netpol-client-a`, `app=client`, `access=allowed`. |
| [03-client-b.yaml](../thuc-hanh/17-networkpolicy/03-client-b.yaml) | Naked Pod `netpol-client-b`, `app=client`, `access=denied`. |
| [04-deny-server-ingress.yaml](../thuc-hanh/17-networkpolicy/04-deny-server-ingress.yaml) | `isolate-server-ingress`: chọn server, `Ingress`, không có allow rule. |
| [05-allow-approved-client.yaml](../thuc-hanh/17-networkpolicy/05-allow-approved-client.yaml) | `allow-approved-client`: mở ingress server từ client hợp lệ cùng namespace, TCP/8080. |
| [06-server-service.yaml](../thuc-hanh/17-networkpolicy/06-server-service.yaml) | ClusterIP Service `netpol-server`, TCP 80 → 8080. |
| [07-deny-client-a-egress.yaml](../thuc-hanh/17-networkpolicy/07-deny-client-a-egress.yaml) | `isolate-client-a-egress`: chọn client hợp lệ, `Egress`, không có allow rule. |
| [08-allow-client-a-dns.yaml](../thuc-hanh/17-networkpolicy/08-allow-client-a-dns.yaml) | `allow-client-a-dns`: mở tới Pod DNS trong `kube-system`, UDP/TCP 53. |
| [09-allow-client-a-server.yaml](../thuc-hanh/17-networkpolicy/09-allow-client-a-server.yaml) | `allow-client-a-server`: mở tới Pod server cùng namespace, TCP/8080. |

### Công cụ và image đã kiểm

- `/usr/local/bin/kubectl` **v1.33.9**, API server **v1.33.6+k3s1**; kiểm lại ngày 17/11. Không nâng cấp tool/cluster hoặc đổi context mặc định.
- API NetworkPolicy `networking.k8s.io/v1`; Namespace/Pod/Service `v1`, EndpointSlice `discovery.k8s.io/v1`.
- Ba node ARM64. Registry manifest được đọc ngày 16/11, xác nhận `linux/arm64/v8` cho image pin:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

- DNS inventory ngày 16/11: `kube-system/kube-dns`, ClusterIP `10.43.0.10`, UDP/TCP 53, selector `k8s-app=kube-dns`; CoreDNS Ready, image `rancher/mirrored-coredns-coredns:1.13.1`. Không đổi image/chart DNS.
- Resolver thực tế trong client A có nameserver `10.43.0.10`, search prefix `lesson17-netpol.svc.cluster.local`; không coi đây là cấu hình mặc định của mọi cluster.
- Usage `nslookup -type=A`, `timeout` được kiểm trong client dùng image pin. Mười scaffold qua client dry-run/schema; script server qua `/bin/sh -n`, không thực thi script trên Mac. Validation không thay bằng chứng runtime.

### Field và quan hệ quan trọng

| Resource/field | Giá trị và ý nghĩa trong lab |
|---|---|
| Policy `metadata.namespace` | `lesson17-netpol`, kể cả rule cho đi tới DNS ở namespace khác. Không đặt deny lên `kube-system`. |
| Policy `spec.podSelector` | Chọn server cho ingress; chọn `app=client` AND `access=allowed` cho egress. Tên policy không chọn Pod. |
| `spec.policyTypes` | Khai tường minh `Ingress` hoặc `Egress`, không tự coi một chiều là cả hai. |
| `spec.ingress[].from[]` | Nguồn phải là Pod có cả `app=client`, `access=allowed`, cùng namespace. |
| `spec.egress[].to[]` của DNS | Cùng một peer: namespace có `kubernetes.io/metadata.name=kube-system` AND Pod có `k8s-app=kube-dns`. |
| DNS rule `ports` | UDP/53 hoặc TCP/53, không mở cổng 53 tới mọi đích. |
| Backend egress `to.podSelector` | `app=server` AND `lesson=17`, trong cùng namespace với policy. Không tham chiếu Service bằng tên trong NetworkPolicy. |
| Backend rule `ports` | TCP/8080 ở Pod backend; Service frontend là TCP/80. Kiểm cả hai đường trên implementation của lab. |
| Service `spec.selector` | `app=server` AND `lesson=17`, khớp Pod; metadata labels của Service không tự chọn backend. |
| Pod `nodeSelector` | Server chọn hostname agent-0; hai client chọn agent-1. Sai hostname hoặc agent không khả dụng có thể làm Pending. |
| Pod network / inputs | `hostNetwork=false`, `ClusterFirst`, không declared env/envFrom hoặc volume; không mount API token, không bật Service env links. |
| Container resources | Mỗi Pod request `25m/32Mi`, limit `100m/64Mi`; không phải số đo usage hoặc dung lượng vật lý cộng dồn của các node container. |
| Server command / readiness | Tạo marker và `/ready`, chạy `httpd` foreground; readiness không thay kiểm kết nối từ client. |
| Client command / restart | `sleep 86400`, `restartPolicy: Always`; chương trình HTTP/DNS thử chạy bằng exec trong client, không phát từ Mac. |

Chọn thêm Service thay vì chỉ lookup một tên hệ thống có sẵn: thêm một resource nhỏ nhưng kiểm được tên của chính ứng dụng. Không dùng port-forward, Ingress, LB hoặc TLS cho bài này.

## 4. Bằng chứng theo pha

Đây là các lượt mentor tự kiểm tra sau khi học viên thực hiện và gửi kết quả. Tất cả giờ dưới là giờ Việt Nam. Không suy toàn bộ thứ tự thao tác từ một snapshot đơn lẻ.

| Ngày / giờ mentor kiểm | Pha | DNS | HTTP |
|---|---|---|---|
| 16/11, 10:32:02 | Baseline ba Pod, namespace chưa có NetworkPolicy | Chưa thử ở pha này | A/B → Pod IP đều 200, marker đúng, exit 0. |
| 16/11, 10:56:48–10:56:50 | Thêm deny ingress server | Không lặp ở pha này | A/B đều refused/exit 1; server vẫn LISTEN 8080, HTTP loopback trong server trả 200. |
| 16/11, 14:07:54–14:07:56 | Thêm allow ingress cho A | Chưa thử lookup ứng dụng | A → Pod IP 200/marker/exit 0; B refused/exit 1. |
| 16/11, 14:19:00–14:19:01 | Service/DNS baseline | A/B trả `10.43.112.218`, exit 0 | Qua tên Service: A 200/marker/exit 0, B refused/exit 1. |
| 16/11, 15:56:19–15:56:25 | Thêm deny egress cho A | A exit 1, không resolve; B vẫn đúng IP/exit 0 | A → Pod IP exit 1, không HTTP/marker; không lặp HTTP B ở pha này. |
| 16/11, 16:17:01–16:17:02 | Chỉ mở DNS cho A | A/B đúng IP/exit 0 | A → Pod IP vẫn exit 1; không lặp HTTP B ở pha này. |
| 16/11, 16:25:38–16:25:41 | Mở backend TCP/8080 cho A | A/B đúng IP/exit 0 | A 200/marker/exit 0 qua cả Pod IP và Service; B exit 1 qua cả hai đường. |
| 17/11, 14:03:27–14:03:30 | Kiểm chốt sau review | A/B đúng IP/exit 0 | Lặp đầy đủ ma trận cuối vẫn đạt; identity và policy spec ổn định. |

`Connection refused` trong các lượt deny là đối chứng mong đợi, không phải yêu cầu chữa ứng dụng. Học viên đã chủ động nhắc giữ đúng phạm vi thí nghiệm; mentor không chuyển sang sửa CNI/node hoặc workload bài cũ. Không ghi mọi thất bại thành timeout, cũng không suy cơ chế reject cụ thể chỉ từ thông báo lỗi.

## 5. Lệnh tái quan sát, output và cách đọc

Các lệnh này là tham chiếu chỉ đọc cho fixture đang giữ, không phải yêu cầu chạy lại các thao tác deny/allow. IP có thể thay đổi về sau; luôn lấy lại giá trị hiện tại.

### 5.1 Đúng context/namespace và trạng thái Pod

Từ thư mục `roadmap-k3d`, dùng cấu hình truy cập sẵn có và khóa context:

```bash
K=/usr/local/bin/kubectl
CTX=k3d-de-k3d
NS=lesson17-netpol
FQDN=netpol-server.lesson17-netpol.svc.cluster.local

"$K" config current-context
"$K" --context "$CTX" get namespace "$NS"

"$K" --context "$CTX" -n "$NS" get pods \
  -o 'custom-columns=NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,RESTARTS:.status.containerStatuses[*].restartCount,IP:.status.podIP,NODE:.spec.nodeName'
```

Chỉ tiếp tục live khi đúng `k3d-de-k3d` và namespace `Active`. Output custom columns ở snapshot ngày 17/11:

```text
NAME              READY   RESTARTS   IP           NODE
netpol-client-a   True    1          10.42.1.58   k3d-de-k3d-agent-1
netpol-client-b   True    1          10.42.1.59   k3d-de-k3d-agent-1
netpol-server     True    0          10.42.3.76   k3d-de-k3d-agent-0
```

Nhìn `READY` và `NODE` để kiểm trạng thái/placement, không dùng chúng thay request. Đây không phải bộ cột mặc định của `get pods`.

Hai client tăng restart count từ 0 ngày 16/11 lên 1 khi chốt ngày 17/11, nhưng Pod UID giữ nguyên. Mentor đọc metadata lần chạy trước: exit `0`, reason `Completed`, từ `03:28:06Z ngày 16/11` tới `03:28:06Z ngày 17/11`, đúng 24 giờ; container mới chạy từ `03:28:07Z ngày 17/11`. Kết quả phù hợp `sleep 86400` kết thúc rồi `Always` chạy container lại; không ghi thành NetworkPolicy làm crash hoặc mentor restart Pod.

### 5.2 Kiểm policy, Service và EndpointSlice

```bash
"$K" --context "$CTX" -n "$NS" get networkpolicy \
  -o 'custom-columns=NAME:.metadata.name,TYPES:.spec.policyTypes[*]'

"$K" --context "$CTX" -n "$NS" get service netpol-server \
  -o 'custom-columns=NAME:.metadata.name,IP:.spec.clusterIP,PORT:.spec.ports[*].port,TARGET:.spec.ports[*].targetPort'

"$K" --context "$CTX" -n "$NS" get endpointslice \
  -l kubernetes.io/service-name=netpol-server \
  -o 'custom-columns=ADDRESS:.endpoints[*].addresses[*],READY:.endpoints[*].conditions.ready,PORT:.ports[*].port'
```

Kết quả mentor kiểm ở snapshot chốt:

- Năm policy: hai `Ingress`, ba `Egress`; tên/UID/spec khớp bảng identity bên dưới.
- Service: `10.43.112.218`, port `80`, target `8080`.
- Slice: address `10.42.3.76`, ready `true`, port `8080`; targetRef UID đúng Pod server.

Object/policy count chỉ xác nhận cấu hình tồn tại, không thay ma trận request.

### 5.3 DNS từ hai client

```bash
for CLIENT in netpol-client-a netpol-client-b; do
  printf '\n%s DNS\n' "$CLIENT"
  "$K" --context "$CTX" -n "$NS" exec "$CLIENT" -- \
    timeout 8 nslookup -type=A "$FQDN"
  printf 'dns_exit=%s\n' "$?"
done
```

Ở snapshot chốt, cả hai trả lời tên `netpol-server.lesson17-netpol.svc.cluster.local` bằng `10.43.112.218`, `dns_exit=0`. Nhìn địa chỉ dưới khối `Name`, không nhầm địa chỉ DNS resolver phía trên với IP Service ứng dụng.

`-type=A` hỏi IPv4. `timeout 8` giới hạn chương trình trong Pod, không phải hạn chính xác cho toàn bộ thao tác API/exec.

### 5.4 HTTP qua Pod IP và tên Service

```bash
SERVER_IP=$("$K" --context "$CTX" -n "$NS" get pod netpol-server \
  -o jsonpath='{.status.podIP}')

for CLIENT in netpol-client-a netpol-client-b; do
  for URL in "http://${SERVER_IP}:8080/" "http://${FQDN}:80/"; do
    printf '\n%s %s\n' "$CLIENT" "$URL"
    "$K" --context "$CTX" -n "$NS" exec "$CLIENT" -- \
      timeout 8 wget -Y off -S -T 3 -O - "$URL"
    printf 'http_exit=%s\n' "$?"
  done
done
```

`-Y off` không dùng HTTP proxy; `-S` hiện HTTP status/header; `-O -` hiện body; `-T 3` đặt network read timeout. Mỗi lượt khởi tạo request mới từ mạng của client Pod, không dùng phiên mở trước khi đổi policy.

Kết quả **mentor đã kiểm lúc 14:03:28–14:03:30 ngày 17/11**, không phải output kỳ vọng:

| Nguồn → đích | HTTP status | Body marker | Exit |
|---|---|---|---|
| A → Pod IP:8080 | 200 | `lesson17-netpol-ok` | 0 |
| A → tên Service:80 | 200 | `lesson17-netpol-ok` | 0 |
| B → Pod IP:8080 | Không nhận HTTP status | Không nhận marker | 1, có lỗi từ wget |
| B → tên Service:80 | Không nhận HTTP status | Không nhận marker | 1, có lỗi từ wget |

Học viên đã gửi ba phép thử HTTP cuối ngày 16/11 với cùng kết quả tương ứng; mentor còn lặp B → Pod IP và DNS hai nguồn. Không coi output tool của mentor là màn hình học viên. Lỗi API/exec không được tính thành bằng chứng policy chặn HTTP.

## 6. Identity và tài nguyên giữ lại khi đóng bài

Snapshot ngày **17/11/2026, 14:03**; ba node Ready/ARM64, không cordon hoặc taint. Cả ba Pod Running/Ready, không deletionTimestamp hoặc controller owner. Các UID dưới giữ nguyên qua những pha liên quan:

| Resource | UID | Thông tin |
|---|---|---|
| Namespace `lesson17-netpol` | `15647eb7-051f-466e-9e3e-f6ac5e63bf22` | Active. |
| Pod `netpol-server` | `823bde91-87b3-4468-80bf-bf0b40bccdd7` | `10.42.3.76`, agent-0, restart 0. |
| Pod `netpol-client-a` | `71d82dbd-783a-44c0-9ff3-2d01e2f81d51` | `10.42.1.58`, agent-1, restart 1. |
| Pod `netpol-client-b` | `fbc2e439-f144-4ae1-b29f-421a15c67c21` | `10.42.1.59`, agent-1, restart 1. |
| Service `netpol-server` | `34dbf9b7-ddb2-4918-8ca6-3e1f2921940d` | ClusterIP `10.43.112.218`, TCP 80 → 8080. |
| EndpointSlice `netpol-server-cgdns` | `e0dc21c4-bb41-41ad-bbba-ddcf75fc37ae` | Backend đúng server UID, ready, TCP/8080. |
| Policy `isolate-server-ingress` | `a37c3ca7-2306-4a3e-92ff-4f1afc741c3b` | Generation 1. |
| Policy `allow-approved-client` | `4107c233-5aca-461c-b63c-228b96bc4585` | Generation 1. |
| Policy `isolate-client-a-egress` | `74299468-425e-4acd-a62a-fe47369b8caa` | Generation 1. |
| Policy `allow-client-a-dns` | `459a85f8-853b-41cf-95c2-469f6e13dbfe` | Generation 1. |
| Policy `allow-client-a-server` | `18703a20-353c-4649-88cb-5ba1803544ef` | Generation 1. |

Giữ toàn bộ fixture và mười scaffold, không xóa namespace/Pod/policy hoặc thêm cleanup thành bài bù. Recovery đã chứng minh việc khôi phục **luồng cần thiết**, không phải đưa egress A trở lại allow-all.

## 7. Checkpoint, nhầm lẫn đã sửa và review

| Khối | Học viên trả lời | Kết quả |
|---|---|---|
| API/enforcement, selector và chiều ingress | `1B, 2C` | Đúng cả hai. |
| Allow ingress, cộng hợp và phạm vi peer | `1B, 2B` | Câu 1 sai: đáp án A, policy rộng vẫn cấp quyền cho cả A/B; câu 2 đúng. |
| Tái giảng cộng hợp | `C` | Đúng: A/8080 và B/9090 là hai cặp riêng, không ghép mọi nguồn với mọi cổng. |
| AND/OR namespace và Pod selectors | `1B, 2C` | Đúng cả hai. |
| Egress nguồn + ingress đích, reply traffic | `1C, 2A` | Đúng cả hai. |
| DNS không cấp quyền HTTPS tới IP trả về | `B` | Đúng. |
| Review cuối ngày 17/11 | `1B, 2C, 3A` | Đúng 3/3. |

Tổng cộng **13 lựa chọn**, một lựa chọn sai ban đầu đã được giải thích và sửa; không ghi thành 13/13 đúng ngay từ đầu. Không dùng điểm quiz thay bằng chứng runtime.

Review cuối đã xác nhận:

1. Giả sử bỏ riêng policy deny egress nhưng vẫn giữ hai allow Egress chọn A, A không tự thành allow-all. Đây là giả định, không thực hiện xóa policy.
2. Sang platform managed/NodeLocal DNS khác phải kiểm resolver, đường DNS, selectors, cổng và enforcement thực tế, không chỉ dựa API nhận YAML.
3. HTTP 403 ở API thuộc bài toán xác thực/phân quyền tầng ứng dụng, không được chữa bằng mở rộng egress tùy tiện. Không gọi API ngoài hoặc triển khai auth để thử case này.

Không còn câu đang chờ hoặc điểm nhầm cần làm bù.

## 8. Lab làm giúp và hợp đồng với platform

| Khả năng | Trong lab đã dùng/kiểm | Ngoài lab cần xác nhận |
|---|---|---|
| Enforcement | K3s có implementation tích hợp; ma trận có đối chứng chứng minh hành vi trong fixture này. | CNI/networking solution và chức năng enforcement thực sự được bật; inventory baseline policies trước khi mở luồng. Có mạng Pod không tự đồng nghĩa có policy enforcement. |
| Quyền và phạm vi | Identity sandbox được tạo namespace, Pod/policy và exec; policy chỉ ở `lesson17-netpol`. | Namespace/quy trình cấp quyền do platform quy định; không coi quyền lab là quyền DE mặc định. |
| DNS | Resolver và DNS Service đã được inventory, peer labels dùng giá trị thực tế, DNS A lookup được thử riêng. | CoreDNS hay NodeLocal DNSCache, resolver trong Pod, namespace/labels/địa chỉ/cổng và policy hai phía. Không mặc định copy peer selector của lab là đủ. |
| Service/backend | ClusterIP TCP/80 chuyển tới Pod TCP/8080, kiểm Slice và cả hai đường kết nối. | Selector/endpoints, Service dataplane và hành vi NAT/identity của implementation; kiểm từ đúng nhóm client. |
| Egress external/FQDN | Chỉ review khái niệm; không mở Internet. | Nguồn → đích, protocol/port, mục đích, DNS, route/proxy/NAT nếu có và quy trình mở luồng. Yêu cầu khả năng FQDN/proxy phù hợp nếu IP thay đổi, không tự bịa field API. |
| Quyền dữ liệu | Chỉ HTTP marker giả, không có credential hoặc dữ liệu thật. | TLS, IAM S3, quyền SQL/API và owner xử lý auth riêng; NetworkPolicy không cấp các quyền này. |

Thông tin DE cần đưa khi yêu cầu mở luồng: namespace/nhóm Pod nguồn, đích và vai trò của nó, protocol/cổng đích, nhu cầu DNS, mục đích nghiệp vụ, đối chứng hiện có và phạm vi quyền cần cấp. Không yêu cầu “allow all” thay cho hợp đồng kết nối.

## 9. Giới hạn minh chứng

- Đây là Pod network thông thường trên các node container chung một Mac/runtime; không chứng minh HA vật lý, bảo mật toàn cluster hoặc performance/scale.
- Đã thử NetworkPolicy trong namespace test; không nghiệm thu mọi policy/plugin/provider, hostNetwork hoặc host traffic.
- Rule DNS khai UDP/TCP 53, nhưng các lookup không được phân tách để chứng minh từng transport/TCP fallback; không tuyên bố đã kiểm đủ mọi tình huống DNS.
- AND/OR được giảng/review; chỉ variant AND của rule DNS được triển khai, không dựng namespace `analytics` hoặc biến thể OR rộng.
- Không thử `ipBlock`, CIDR external, FQDN policy, egress Internet, IPv6/SCTP/ICMP hoặc packet capture. Không suy NetworkPolicy chuẩn có khả năng FQDN tùy ý.
- Chỉ dùng kết nối mới; chưa kiểm cách implementation xử lý kết nối đã mở trước thay đổi policy.
- Không mở TLS/auth/SQL/S3, không in Secret/token/kubeconfig credential/raw env hoặc logs nhạy cảm.
- Không sửa workload các bài trước, đổi CNI/firewall/node hoặc chạm cluster Kubernetes `orbstack`. Docker context `orbstack` chỉ được dùng để đọc image manifest; không phải Kubernetes context của khóa.

## 10. Điểm tiếp tục

**Chờ Bài 18 — Vòng đời dữ liệu**, chưa giảng hoặc tạo scaffold. Giữ fixture Bài 17; kiểm lại context/namespace/identity trước khi tái dùng, không coi IP trong tổng kết là cố định.

Không mở lại bài hoặc chạy lại deny/allow chỉ để có thêm minh chứng. Khi học bài mới, vẫn dạy concept/cấu hình trước và kiểm tra hiểu rồi học viên tự thực hành.

## Nguồn đã đối chiếu

- [NetworkPolicy — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/network-policies/).
- [Debugging DNS — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/).
- [NodeLocal DNSCache — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/).
- [K3s networking services / embedded network policy controller](https://docs.k3s.io/networking/networking-services).
- [BusyBox official image](https://hub.docker.com/_/busybox); manifest index đọc bằng `docker buildx imagetools inspect` ngày 16/11, usage các applet kiểm trong container image pin.
