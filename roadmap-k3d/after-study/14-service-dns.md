# Tổng kết Bài 14 — Service, EndpointSlice và DNS

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/14-service-dns.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/15-ingress-va-loadbalancer.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-09**, giờ Việt Nam (`Asia/Ho_Chi_Minh`). Lý thuyết/scaffold bắt đầu ngày 08/11; thực hành và review chốt ngày 09/11.
- **Phạm vi:** context `k3d-de-k3d`, kubeconfig `~/.kube/config`; backend/Service/client cùng namespace ở `de-lab`, client khác namespace ở `de-client`.
- **Phiên bản đã đối chiếu:** `/usr/local/bin/kubectl` `v1.33.9`, API server `v1.33.6+k3s1`, nodes ARM64. Không dùng kubectl mới trên PATH hoặc đổi cluster/tool.
- **Kết quả:** DNS/HTTP cùng và khác namespace đạt; selector sai và recovery đạt; thay backend Pod nhưng giữ Service đạt; readiness thất bại và recovery không restart/thay Pod đạt; **12/12 câu trắc nghiệm đúng**.
- **Kiểm chứng cuối:** DNS/HTTP từ cả hai client và `/ready` đạt lúc **15:01:25 ngày 09/11**; snapshot đóng bài lúc **15:22:02** xác nhận ba Pod vẫn Running/Ready, restart `0`, cùng UID/IP và backend Ready trong EndpointSlice.
- **Ranh giới:** học viên tự apply, sửa selector, xóa đúng một backend Pod và thay file tín hiệu readiness. Mentor chỉ chuẩn bị scaffold, kiểm tra chỉ đọc và lưu tài liệu; không apply/patch/delete/restart workload, thay DNS/networking hoặc đọc credential. Giữ tài nguyên, không cleanup.

## 1. Bài toán và mental model

Pod IP phù hợp để chẩn đoán một backend cụ thể, nhưng không nên trở thành cấu hình kết nối lâu dài của client. Service tách địa chỉ client gọi khỏi identity/IP của từng Pod.

Luồng logic đã kiểm chứng sau khi thay Pod:

```text
Tên Service trong DNS cluster
    -> ClusterIP 10.43.62.113, cổng TCP 80
    -> backend Pod 10.42.3.42, cổng TCP 8080
    -> HTTP 200 + lesson14-service-dns-ok
```

Đây là mô hình logic, không phải packet capture. HTTP không chạy xuyên qua object EndpointSlice.

| Thành phần | Trách nhiệm và giới hạn |
|---|---|
| Service kiểu ClusterIP | Khai báo frontend IP/ports và selector. IP ổn định trong vòng đời Service; không tạo Pod, listener hoặc endpoint public. Xóa/tạo lại Service không được bảo đảm giữ cùng IP. |
| EndpointSlice controller | Theo dõi Service selector cùng Pod labels/trạng thái để cập nhật backend. Một Service có thể có nhiều slice; cần tìm tất cả theo label liên kết. |
| EndpointSlice | Chứa địa chỉ, cổng, trạng thái và tham chiếu backend; là dữ liệu cho thành phần thực thi Service, không tự chuyển gói tin. |
| Service dataplane | Thực thi đường chuyển traffic dựa trên thông tin Service/backend. kube-proxy là ví dụ; bài này không kiểm chứng mode/rules cụ thể hoặc thay implementation. |
| DNS cluster | Với ClusterIP Service thông thường trong bài, trả ClusterIP khi tìm tên Service. Phân giải thành công không chứng minh backend Ready hoặc HTTP đúng. |
| Deployment/ReplicaSet | Duy trì replica theo Pod template. ReplicaSet tạo Pod thay thế; Service không chịu trách nhiệm này. |
| Kubelet/readiness probe | Kiểm tra điều kiện sẵn sàng của container. Readiness thất bại không tự restart container; không bảo đảm mọi kết nối cũ lập tức bị ngắt. |

Các lựa chọn đã so sánh: Pod IP trực tiếp dễ khoanh vùng một backend nhưng dễ lỗi khi Pod đổi; Service phù hợp cấu hình client ổn định. `targetPort` dạng số trực tiếp hơn; dạng tên thêm quan hệ tham chiếu nhưng cho phép số cổng backend thay đổi theo Pod mà giữ frontend Service.

## 2. Scaffold và cấu hình đã chọn

| File | Resource/phạm vi |
|---|---|
| [01-server-deployment.yaml](../thuc-hanh/14-service-dns/01-server-deployment.yaml) | Deployment `service-dns-server`, `de-lab`, một replica HTTP server. |
| [02-service.yaml](../thuc-hanh/14-service-dns/02-service.yaml) | Service `service-dns-svc`, `de-lab`, ClusterIP; file cuối đã khôi phục selector `role: server`. |
| [03-client-same-namespace.yaml](../thuc-hanh/14-service-dns/03-client-same-namespace.yaml) | Naked Pod `service-dns-client`, `de-lab`. |
| [04-client-namespace.yaml](../thuc-hanh/14-service-dns/04-client-namespace.yaml) | Namespace `de-client`, tạo mới cho bước client khác namespace. Namespace là resource cấp cluster. |
| [05-client-cross-namespace.yaml](../thuc-hanh/14-service-dns/05-client-cross-namespace.yaml) | Naked Pod `service-dns-client-cross`, `de-client`. |

Image pin trên cả ba Pod:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

Metadata Docker Hub được đối chiếu ngày 08/11 có `linux/arm64/v8`, manifest digest `sha256:d82c2ab94640ded77cf76514ce6a84870761105058a4a9e51b05a8a79be97a6c`. Image reference và runtime imageID đã được kiểm tra trong lab. `IfNotPresent` có thể dùng cache từng node; không chứng minh mọi lượt đều pull mới hoặc image trên Mac tự có trong node.

Server chạy `/bin/sh -ec` với script:

```sh
mkdir -p /www
printf '%s\n' 'lesson14-service-dns-ok' > /www/index.html
printf '%s\n' 'ready' > /www/ready
exec httpd -f -p 0.0.0.0:8080 -h /www
```

`/` đọc `/www/index.html`; URL `/ready` đọc file `/www/ready`. Đây là dữ liệu giả trong filesystem container, không có PVC hoặc cam kết persistence. File `/www/ready` chỉ là fixture điều khiển lab, không đại diện health check production.

| Resource/đường dẫn field | Ý nghĩa, lựa chọn và quan hệ |
|---|---|
| Deployment `spec.replicas: 1` | Dễ quan sát replacement và readiness, tiết kiệm tài nguyên; không bảo đảm HA hoặc không gián đoạn. |
| Deployment `spec.selector.matchLabels` | Match `lesson="14"`, `app=service-dns`, `role=server` trên Pod template. |
| Deployment `spec.template.metadata.labels` | Labels thực sự được gắn lên Pod; khác `metadata.labels` của Deployment. |
| Service `metadata.namespace: de-lab` | Selector của Service chỉ chọn Pod cùng namespace. Namespace khác vẫn có thể gọi Service nếu DNS/mạng/policy cho phép. |
| Service `spec.selector` | Cùng ba labels của backend; cố ý đổi riêng `role` sang `missing` rồi khôi phục `server`. Không đổi labels Pod. |
| Service `spec.ports[].name: web` | Tên cổng phía Service, không bắt buộc trùng tên cổng Pod hoặc tên container. |
| Service `spec.ports[].port: 80` | Cổng client gọi trên Service. |
| Service `spec.ports[].targetPort: http` | Tham chiếu tên cổng Pod, không phải DNS hostname hoặc cơ chế tự dò listener. |
| Pod container `ports[].name: http`, `containerPort: 8080`, `protocol: TCP` | Resolve named targetPort tới 8080/TCP. Khai báo cổng không tự tạo hoặc đổi listener ứng dụng. |
| Pod container `readinessProbe.httpGet.path: /ready`, `port: http` | Kubelet gọi đường HTTP này trực tiếp tại Pod, không qua Service. |
| Readiness `periodSeconds: 2`, `timeoutSeconds: 1`, `failureThreshold: 1`, `successThreshold: 1` | Chu kỳ cấu hình 2 giây, timeout 1 giây; một lần fail/pass quyết định chuyển trạng thái tương ứng. Probe và cập nhật EndpointSlice không đồng bộ tức thời. Không cấu hình liveness/startup trong lab này. |
| EndpointSlice `metadata.labels.kubernetes.io/service-name` | Liên kết slice với Service; không đoán tên sinh tự động của slice. |
| EndpointSlice `endpoints[].addresses`, `endpoints[].conditions.ready`, `endpoints[].targetRef.uid`, `ports[].port` | Đọc đồng thời đích IP/cổng, khả năng nhận kết nối mới và identity Pod được tham chiếu. Chỉ thấy IP chưa đủ. |
| PodSpec `dnsPolicy: ClusterFirst` | Dùng DNS cluster cho Service; truy vấn tên bên ngoài có thể được DNS cluster forward tới upstream. Không khai field thì mặc định là ClusterFirst, không phải giá trị tên Default. |
| PodSpec `dnsPolicy: Default` — chỉ học tình huống | Kế thừa DNS node; không bảo đảm resolver đó biết Service names. Không thực hành đổi policy này. Với Deployment, field tương ứng nằm tại `spec.template.spec.dnsPolicy`. |
| PodSpec `automountServiceAccountToken: false`, `enableServiceLinks: false`, `hostNetwork: false` | Test không cần API credential, dùng DNS thay Service env links, giữ mạng Pod. |
| Container image/resources | `IfNotPresent`; mỗi container requests `25m/32Mi`, limits `100m/64Mi`. Đây không phải số đo usage hoặc sizing production. |
| Client command / PodSpec | `sleep 86400`, `restartPolicy: Always`, thời gian dừng mềm 5 giây. Client có thể restart container khi sleep kết thúc; naked Pod không tự được tạo lại sau khi xóa Pod object. |

Schema/client dry-run và shell syntax đã đạt trước khi giao thao tác. Chúng không được dùng thay bằng chứng runtime. Ví dụ Service tên `pod-net-svc` ban đầu chỉ là YAML minh họa; resource thực hành là `service-dns-svc`.

## 3. Lệnh quan sát và bằng chứng DNS/HTTP

Helper đã dùng từ thư mục gốc repo; khóa binary/kubeconfig/context nhưng ghi namespace ở từng lệnh:

```bash
k14x() {
  /usr/local/bin/kubectl \
    --kubeconfig="$HOME/.kube/config" \
    --context=k3d-de-k3d --request-timeout=10s "$@"
}
```

Trước mỗi nhóm kiểm tra live, mentor kiểm context và namespace Active. Không dump kubeconfig hoặc credential. Các lệnh quan sát dưới có thể chạy lại; các thao tác gây lỗi/xóa Pod được ghi ở mục sau là **lịch sử thí nghiệm, không phải yêu cầu chạy lại**.

### 3.1 Resolver và namespace

```bash
k14x -n de-client exec service-dns-client-cross -c client -- \
  cat /etc/resolv.conf
```

Snapshot mentor lúc 09:06 ngày 09/11, rút gọn:

```text
search de-client.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.43.0.10
```

Nhìn `nameserver` để biết DNS Pod hỏi; `search` cho thấy suffix namespace của client. Client trong `de-lab` đã được đọc resolver riêng, có suffix đầu `de-lab.svc.cluster.local`. Cluster domain thực tế ở lab là `cluster.local`, không hard-code cho mọi cluster.

- `service-dns-svc`: tên ngắn, phụ thuộc namespace/search path của client.
- `service-dns-svc.de-lab`: chỉ rõ namespace Service đích; phù hợp client ở namespace khác.
- `service-dns-svc.de-lab.svc.cluster.local.`: tên đầy đủ tuyệt đối trong lab, dấu chấm cuối tránh thêm search suffix.
- `-n de-client` trong lệnh exec chọn nơi chạy client, không chuyển namespace của Service đích.

Không thực hành đối chứng tên ngắn thất bại trong `de-client`; phần này được học qua lý thuyết và quiz. Tên ngắn ở namespace khác còn có thể tìm một Service cùng tên khác, không luôn đồng nghĩa NXDOMAIN.

### 3.2 DNS trả ClusterIP, không phải Pod IP

```bash
k14x -n de-client exec service-dns-client-cross -c client -- \
  nslookup service-dns-svc.de-lab.svc.cluster.local.
```

Output đã được học viên gửi và mentor tự kiểm tra độc lập; phần liên quan:

```text
Server:         10.43.0.10
Address:        10.43.0.10:53

Name:   service-dns-svc.de-lab.svc.cluster.local
Address: 10.43.62.113
```

Khối Server/Address đầu là DNS server; Address trong khối Name cuối là ClusterIP Service. DNS vẫn trả IP này ở hai ca backend lỗi được kiểm chứng tại mục 4. Snapshot đó không chứng minh ứng dụng đang nhận traffic.

### 3.3 HTTP từ đúng nguồn

Client cùng namespace:

```bash
k14x -n de-lab exec service-dns-client -c client -- \
  wget -Y off -S -T 3 -O - http://service-dns-svc:80/
```

Client khác namespace:

```bash
k14x -n de-client exec service-dns-client-cross -c client -- \
  wget -Y off -S -T 3 -O - http://service-dns-svc.de-lab:80/
```

Mentor kiểm chứng lại cả hai nguồn lúc **15:01:25**, đều exit `0`, trích header/body:

```text
HTTP/1.1 200 OK
lesson14-service-dns-ok
```

Phải đọc cả status và marker. `wget` chạy trong client Pod, không phải mạng Mac. `-Y off` không dùng proxy; `-S` hiện headers; `-O -` in body; `-T 3` là timeout đọc mạng, không cam kết toàn bộ lệnh kết thúc đúng ba giây. Headers/stderr và body/stdout có thể xen thứ tự, không phải lỗi HTTP.

## 4. Các đối chứng, recovery và nguồn minh chứng

Các mốc dưới là **giờ Việt Nam ngày 2026-11-09**. Snapshot mentor không phải audit toàn bộ thứ tự lệnh; nơi học viên đã gửi output được ghi riêng, không coi tool output mentor là màn hình học viên.

| Mốc kiểm tra mentor | Quan sát thực tế |
|---|---|
| 00:14–00:16 | Baseline: backend cũ `lm5h4`, client cùng namespace Running/Ready, restart 0; DNS và HTTP qua Service thành công. Học viên sau đó xác nhận đã quan sát. |
| 09:06 | Client khác namespace có search suffix `de-client`; DNS/HTTP thành công. Học viên đã gửi HTTP 200/marker với HTTP Date tương ứng 09:01:35 và kết quả DNS riêng. |
| 09:26:55–09:26:57 | File/live Service có `role=missing`; EndpointSlice không có endpoint/cổng, DNS vẫn trả ClusterIP, HTTP qua Service refused/exit 1; backend cũ vẫn Ready/restart 0. |
| 09:45:52–09:45:53 | Selector khôi phục `server`; cùng backend cũ và Service UID/IP; DNS/HTTP thành công trở lại. Học viên cũng gửi HTTP thành công với cả tên có namespace và tên đầy đủ. |
| 13:58 | Preflight trước thay Pod: backend cũ đúng UID, owner ReplicaSet, một replica Ready, không volume; HTTP baseline 200/marker. |
| 14:14:16–14:14:17 | Sau output xóa/watch của học viên: Pod cũ absent, Pod mới UID/IP khác, cùng ReplicaSet; Service UID/IP giữ nguyên; `/` và `/ready` đều 200. Học viên đã gọi lại Service thành công lúc 14:09:55 theo HTTP Date. |
| 14:35:31–14:35:33 | Sau học viên xóa file readiness: cùng Pod mới Running/NotReady/restart 0; slice giữ địa chỉ nhưng ready=false; DNS còn ClusterIP, Service refused/exit 1, trực tiếp Pod `/` 200/marker; mentor kiểm riêng `/ready` nhận 404. |
| 15:01:25 | Recovery readiness đạt: Pod/slice Ready, cùng UID/IP/restart 0; hai client đều DNS/HTTP thành công; `/ready` trả 200/body `ready`. Học viên đã gửi HTTP recovery lúc 14:58:35 theo HTTP Date. |
| 15:22:02 | Snapshot đóng bài: controller/Service/slice và ba Pod giữ identity, Running/Ready/restart 0; không cleanup. Đây là kiểm metadata/status sau phép thử HTTP 15:01, không trình bày như một GET mới lúc 15:22. |

### 4.1 Selector sai: mất backend nhưng DNS không mất Service

Học viên tự đổi duy nhất Service `spec.selector.role: server -> missing`, apply riêng file 02; giữ nguyên Pod labels, ports và DNS. Không có Pod nào match bộ selector sai trong lượt kiểm tra.

Lệnh quan sát:

```bash
k14x -n de-lab get endpointslices \
  -l kubernetes.io/service-name=service-dns-svc \
  -o 'custom-columns=NAME:.metadata.name,ADDRESS:.endpoints[*].addresses[*],READY:.endpoints[*].conditions.ready,PORT:.ports[*].port'
```

Output thực tế ở ca lỗi, custom columns:

```text
NAME                    ADDRESS   READY    PORT
service-dns-svc-hnbtr   <none>    <none>   <none>
```

API trả `endpoints: null`, `ports: null` trong slice lúc đó; không suy object slice phải bị xóa. Cùng truy vấn DNS tại mục 3 vẫn trả `10.43.62.113`; cùng lệnh HTTP qua Service trả:

```text
wget: can't connect to remote host (10.43.62.113): Connection refused
command terminated with exit code 1
```

Đây là refused thực tế, không ghi thành timeout. Học viên đổi riêng role về `server`, apply lại file 02; backend cũ `10.42.3.36`, ready=true, port 8080 quay lại và HTTP thành công. Service vẫn UID `290cea51-38e4-47ed-8044-845f06fd10b1`, IP `10.43.62.113`.

### 4.2 Thay Pod, không đổi Service

Học viên tự đọc UID cũ trước khi xóa đúng một Pod test:

```bash
k14x -n de-lab delete pod service-dns-server-758b6cd595-lm5h4 \
  --wait=true --timeout=60s
```

Đây là **lệnh lịch sử, không chạy lại để review**. Kiểm UID trước lệnh là guard quan sát, không phải DeleteOptions UID precondition atomic. Không dùng force, xóa theo selector rộng, rollout restart hoặc thay template. ReplicaSet tạo Pod mới để duy trì một replica.

| Identity | Trước | Sau/đang giữ |
|---|---|---|
| Pod name | `service-dns-server-758b6cd595-lm5h4` | `service-dns-server-758b6cd595-9zlq8` |
| Pod UID | `069ea0d0-975f-4d05-8b90-a2169b4a86b5` | `65140d0c-6e6d-4062-b2b0-8e604f3dc695` |
| Pod IP | `10.42.3.36` | `10.42.3.42` |
| ReplicaSet UID | `8cf96dde-01de-4286-8917-401473701806` | Giữ nguyên |
| Deployment UID/generation | `5269a553-0ac4-4328-97e7-07cf81ced00d`, generation 1 | Giữ nguyên |
| Service UID/IP | `290cea51-38e4-47ed-8044-845f06fd10b1` / `10.43.62.113` | Giữ nguyên |

UID mới chứng minh object Pod mới. IP thực tế đã đổi trong lab; trường hợp IP được tái sử dụng chỉ được review bằng tình huống, không thực nghiệm ép tái sử dụng IP.

Học viên dùng watch với request-timeout=0 rồi Ctrl+C khi container Ready; Ctrl+C chỉ dừng quan sát. `deleted` hoặc cột RESTARTS không thay bằng chứng UID mới/Ready. Sau thay Pod, URL client không đổi vẫn trả 200/marker. Không có chuỗi đo liên tục để kết luận không gián đoạn; một replica có thể có khoảng không backend Ready.

### 4.3 NotReady: địa chỉ còn nhưng không nhận kết nối mới qua Service

Thao tác lịch sử của học viên, chỉ với fixture lab trên Pod mới:

```bash
k14x -n de-lab exec service-dns-server-758b6cd595-9zlq8 -c http -- rm /www/ready
```

Lệnh quan sát Pod:

```bash
k14x -n de-lab get pod service-dns-server-758b6cd595-9zlq8 \
  -o 'custom-columns=UID:.metadata.uid,IP:.status.podIP,PHASE:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount'
```

Snapshot âm đã được học viên gửi và mentor kiểm tra lại:

```text
UID                                    IP           PHASE     READY   RESTARTS
65140d0c-6e6d-4062-b2b0-8e604f3dc695   10.42.3.42   Running   false   0
```

READY ở đây là boolean container status do custom columns chọn, không phải cột READY mặc định `1/1`. UID/IP và restart count không đổi; đây không phải Pod replacement hoặc container restart.

```bash
k14x -n de-lab get endpointslices \
  -l kubernetes.io/service-name=service-dns-svc \
  -o 'custom-columns=POD_UID:.endpoints[*].targetRef.uid,ADDRESS:.endpoints[*].addresses[*],READY:.endpoints[*].conditions.ready,PORT:.ports[*].port'
```

Output thực tế âm:

```text
POD_UID                                ADDRESS      READY   PORT
65140d0c-6e6d-4062-b2b0-8e604f3dc695   10.42.3.42   false   8080
```

Khác selector sai: slice vẫn chứa địa chỉ/cổng và `targetRef.uid` đúng Pod, nhưng `conditions.ready=false`; mentor còn đọc `serving=false`, `terminating=false`.

Cùng nguồn `service-dns-client-cross` ở `de-client`, đổi riêng URL đích để đối chiếu:

```bash
k14x -n de-client exec service-dns-client-cross -c client -- \
  wget -Y off -S -T 3 -O - http://service-dns-svc.de-lab:80/

k14x -n de-client exec service-dns-client-cross -c client -- \
  wget -Y off -S -T 3 -O - http://10.42.3.42:8080/

k14x -n de-client exec service-dns-client-cross -c client -- \
  wget -Y off -S -T 3 -O - http://10.42.3.42:8080/ready
```

| Đích | Kết quả thực tế | Nguồn |
|---|---|---|
| Service `/` | Connection refused, exit 1 | Học viên và mentor độc lập |
| Pod IP `/` | HTTP 200, marker đúng, exit 0 | Học viên và mentor độc lập |
| Pod IP `/ready` | HTTP 404 Not Found, exit 1 | Mentor tự kiểm tra chỉ đọc |

Pod IP chỉ dùng chẩn đoán và phải kiểm identity/IP trước khi tái dùng; không trở thành cấu hình client lâu dài. Kết quả này phân biệt app còn phục vụ `/` với điều kiện readiness tại `/ready`, không chứng minh mọi lỗi refused đều có cùng nguyên nhân.

Học viên phục hồi đúng file trong container hiện tại:

```bash
k14x -n de-lab exec service-dns-server-758b6cd595-9zlq8 -c http -- \
  /bin/sh -ec 'printf "%s\n" ready > /www/ready'
```

Đoạn redirect nằm trong chuỗi shell chạy ở container, không ghi file trên Mac. Không xóa/restart Pod, không đổi manifest. Kết quả học viên và mentor đều xác nhận: Pod/slice Ready trở lại, UID/IP giữ nguyên, restart 0; Service HTTP trả 200/marker, `/ready` trả 200/body `ready`. Apply lại Deployment với template không đổi không phải cách yêu cầu chạy lại startup script để phục hồi file runtime.

## 5. Review hiểu biết và các bẫy đã làm rõ

Học viên trả lời đúng **12/12**, không có câu đang chờ:

| Khối | Đáp án | Điểm đã kiểm tra |
|---|---|---|
| Service | `1B, 2C, 3A` | Client giữ địa chỉ Service khi Pod đổi; Service port khác backend port; selector chỉ xét labels, không tự dò HTTP server. |
| EndpointSlice | `1B, 2C` | Controller cập nhật backend; ready=false ảnh hưởng lựa chọn kết nối mới, không đồng nghĩa cắt mọi kết nối cũ. |
| DNS | `1C, 2A` | Tên/namespace/search path trước khi sửa DNS toàn cluster; DNS đúng chưa chứng minh ứng dụng hoạt động. |
| Named targetPort | `B` | Đổi tên cổng Pod mà giữ tham chiếu cũ làm lệch mapping; không có cơ chế tự dò listener để chữa. |
| dnsPolicy | `C` | Default kế thừa node DNS; dùng ClusterFirst phù hợp để client tìm Service trong tình huống đã nêu. |
| Identity | `B` | UID khác là Pod khác dù IP có thể được tái sử dụng; không suy replacement từ restart count. |
| Review chốt | `1C, 2B` | Readiness hợp lệ phản ánh DB chưa sẵn sàng thì điều tra dependency, không bỏ probe; client ngoài cluster cần endpoint/DNS/đường mạng được platform cung cấp. |

Hai review cuối là **tình huống giả định**, không triển khai database hoặc client ngoài cluster. Giả định `/ready` trả 503 phản ánh đúng hợp đồng ứng dụng; không suy mọi HTTP 503 đều do DB hoặc probe luôn được cấu hình đúng.

Không có đáp án trắc nghiệm sai. Selector `missing` và xóa file readiness là đối chứng có chủ đích, không ghi thành lỗi vô ý của học viên. Đã giải thích body/headers xen kẽ do stdout/stderr, và dấu nối dòng khiến shell chờ tiếp không phải lỗi Kubernetes. Không dùng việc đọc output mentor thay cho xác nhận học viên đã quan sát.

## 6. Lab làm giúp gì, ngoài lab cần gì?

| Trong lab | Ngoài lab và cấu hình cần xác nhận |
|---|---|
| K3s triển khai CoreDNS; Pod thực tế có nameserver `10.43.0.10`, search domain `cluster.local`. | Cluster tự quản lý phải có DNS provider/Service và kubelet `clusterDNS`/`clusterDomain` phù hợp; Pod dùng dnsPolicy thích hợp. Managed Kubernetes thường cung cấp DNS sẵn nhưng vẫn phải xác nhận domain, upstream và policy. Bài này đọc effective resolver, không đọc trực tiếp kubelet args. |
| Service/EndpointSlice controller và mạng hiện có phục vụ ClusterIP. | Platform cung cấp Service dataplane cùng mạng Pod/node phù hợp, dải IP/route không xung đột. Service resource tồn tại không chứng minh đường chuyển traffic đang tốt. Không mặc định mọi CNI có cùng cách thực thi Service. |
| Client trong cả hai namespace kết nối được; các lượt inventory ghi không có NetworkPolicy objects ở hai namespace. | Namespace tách phạm vi API, không tự là firewall. Xác nhận luồng DNS UDP/TCP 53 và client -> Service TCP 80 -> backend TCP 8080 theo implementation/policy. Không dùng kết nối thành công khi không có policy làm bằng chứng policy enforcement. |
| Không cần Traefik, k3d serverlb hoặc port mapping cho các phép thử Pod -> ClusterIP. | Client ngoài cluster cần endpoint phù hợp, resolver và đường mạng/quyền truy cập được cấp. Tên `*.svc.cluster.local` không tự được Mac/LAN biết hoặc route tới. Các cách triển khai đường vào thuộc bài sau, chưa thực hành ở đây. |
| Identity lab có quyền tạo namespace, workload, exec và xóa Pod. | DE yêu cầu namespace/identity và quyền theo phạm vi công việc; không lấy admin sandbox làm mô hình quyền mặc định. Tạo namespace là thao tác cấp cluster. |
| Image pin có ARM64, có thể dùng cache từng node. | Platform cung cấp registry/mirror, kiến trúc và quyền pull/trust phù hợp; không dùng image local trên Mac như bằng chứng node khác có image. |

### Hợp đồng kết nối cho Data Engineer

- Nêu nguồn `namespace/Pod` -> Service `namespace/name`, DNS name, protocol/port và dependency thực tế; trong lab là hai client -> `de-lab/service-dns-svc:80` -> backend TCP 8080.
- DE kiểm tên/search path/dnsPolicy, Service selector/ports, tất cả EndpointSlices, Pod readiness/listener và response trong quyền được cấp.
- Khi báo platform, kèm context/namespace, thời điểm, Service/Pod UID/IP, query DNS, endpoint ready/port và lỗi đã lọc; không gửi Secret/env/credential.
- Thứ tự khoanh vùng: đúng nguồn -> tên/resolver -> Service IP/ports/selector -> EndpointSlices/address/ready/target UID -> listener/health ứng dụng -> networking/policy/dataplane nếu các tầng trước đã đúng. Không đổi mọi tầng hoặc sửa CoreDNS để chữa typo.
- Liên hệ DE: Airflow task hoặc Spark component gọi một backend nên dùng endpoint được cấp, không hard-code Pod IP. Nếu readiness phản ánh đúng dependency chưa sẵn sàng, xử lý dependency thay vì ép nhận việc. Đây là liên hệ lý thuyết, chưa triển khai Airflow/Spark/DB trong bài.

## 7. Trạng thái giữ lại và giới hạn

Snapshot đóng bài **15:22:02 ngày 2026-11-09**:

| Resource | Namespace | Identity/IP |
|---|---|---|
| Deployment `service-dns-server` | de-lab | UID `5269a553-0ac4-4328-97e7-07cf81ced00d`, generation 1, desired/ready/available 1 |
| ReplicaSet `service-dns-server-758b6cd595` | de-lab | UID `8cf96dde-01de-4286-8917-401473701806` |
| Service `service-dns-svc` | de-lab | UID `290cea51-38e4-47ed-8044-845f06fd10b1`, ClusterIP `10.43.62.113` |
| EndpointSlice `service-dns-svc-hnbtr` | de-lab | UID `bb6a1e0d-15c1-4c92-aa16-56d19ab50865`, owner đúng Service; backend UID 65140d0c... / `10.42.3.42:8080`, ready/serving=true, terminating=false |
| Pod `service-dns-server-758b6cd595-9zlq8` | de-lab | UID `65140d0c-6e6d-4062-b2b0-8e604f3dc695`, IP `10.42.3.42`, agent-0 |
| Pod `service-dns-client` | de-lab | UID `37882a99-2706-4f5b-82df-0021b0663b64`, IP `10.42.3.37`, agent-0 |
| Pod `service-dns-client-cross` | de-client | UID `3e500459-d527-4759-80ce-da77a2402024`, IP `10.42.1.29`, agent-1 |

Hai namespace Active; ba Pod Running/Ready, restart 0, không deletionTimestamp. Giữ năm scaffold và các resource này. Không yêu cầu cleanup để chốt bài và không ghi là đã xóa. Client sleep 86400 có thể restart về sau mà không đổi Pod UID.

Chưa thực hành targetPort sai, đổi named port, dnsPolicy Default, headless Service, NetworkPolicy enforcement, Ingress/LoadBalancer, DNS ngoài cluster hoặc TLS. Không đo HA, mất node/host, packet flow hoặc hiệu năng; node-container vẫn chung host. Không chứng minh client ngoài cluster kết nối được, mọi namespace đều được phép, hoặc kết nối không gián đoạn trong replacement. Tài nguyên Bài 13 không được dùng làm target sửa/xóa trong lab này.

**Bài 14 Hoàn thành đầy đủ.** Tổng học xong **14/32**, nghiệm thu đầy đủ **12/32** (01–07, 09–11 và 13–14). Bài 08/12 giữ nguyên phạm vi đã chốt, không giao làm bù. Chờ **Bài 15 — Ingress và LoadBalancer**, chưa giảng/tạo scaffold bài mới. Đây là lượt cập nhật tài liệu gộp khi toàn bài đạt, không ghi checkpoint giữa bài hoặc commit/push.

## Nguồn đã đối chiếu

- [Service — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/service/), gồm named targetPort.
- [EndpointSlices — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/endpoint-slices/).
- [DNS for Services and Pods — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/dns-pod-service/).
- [Configure probes — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).
- [Pod lifecycle](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) và [Object names/UIDs](https://v1-33.docs.kubernetes.io/docs/concepts/overview/working-with-objects/names/).
- [K3s networking services/CoreDNS](https://docs.k3s.io/networking/networking-services#coredns).
- [Docker Hub metadata busybox:1.37.0](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0), đối chiếu ARM64/digest ngày 2026-11-08; không dùng metadata registry thay bằng chứng runtime.
