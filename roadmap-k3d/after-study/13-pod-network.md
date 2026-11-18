# Tổng kết Bài 13 — Mạng Pod qua nhiều node

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/13-pod-network.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/14-service-dns.md)

- **Ngày hoàn thành:** 2026-11-08, giờ Việt Nam (`Asia/Ho_Chi_Minh`); mentor kiểm tra kết thúc lúc **15:19:41**.
- **Phạm vi:** context `k3d-de-k3d`, API endpoint `https://127.0.0.1:6445`, namespace `de-lab` Active; hai naked Pod có nhãn `lesson="13"` trên hai agent khác nhau.
- **Phiên bản đã kiểm tra trong preflight Bài 13:** client `/usr/local/bin/kubectl` `v1.33.9`, API server `v1.33.6+k3s1`, ba node ARM64. Không đổi tool, context mặc định hoặc cấu hình cluster.
- **Kết quả:** request từ client trên agent-1 tới Pod IP server trên agent-0, TCP 8080, nhận `HTTP/1.1 200 OK` và marker `lesson13-cross-node-ok`; cùng nguồn/đích nhưng TCP 9090 nhận `Connection refused`, exit code 1. Bảy câu trắc nghiệm đã trả lời đúng.
- **Ranh giới:** mentor chuẩn bị scaffold, kiểm tra chỉ đọc và lưu tài liệu; không apply/patch/delete/restart workload hoặc sửa networking. Bài gốc không yêu cầu cleanup/recovery; giữ hai Pod, không ghi là đã dọn hoặc tự thêm bước xóa để chốt bài.

## 1. Bài toán và mental model

Trước khi thêm Service hoặc DNS, phải biết ứng dụng có listener nào và Pod nguồn có kết nối được tới Pod đích trên node khác hay không.

```text
pod-net-client: 10.42.1.28, agent-1
                  |
                  | HTTP GET tới 10.42.3.35:8080
                  v
Mạng Pod + đường mạng giữa các node
                  |
                  v
pod-net-server: 10.42.3.35, agent-0
                  |
                  v
httpd bind 0.0.0.0:8080 -> /www/index.html
```

Đây là sơ đồ logic của request đã kiểm chứng, không phải packet capture hay bằng chứng mọi gói đã được quan sát trên từng interface.

| Khái niệm | Cách hiểu đã học |
|---|---|
| Network namespace của Pod | Với `hostNetwork: false`, các container cùng Pod chia sẻ IP, không gian cổng và loopback. Đây không phải Kubernetes namespace `de-lab`. |
| `localhost` / `127.0.0.1` | Trỏ về loopback của chính Pod thực hiện request; không trỏ sang Pod khác hoặc Mac. Container khác cùng Pod có thể dùng loopback để gọi ứng dụng. |
| Bind `127.0.0.1:8080` | Listener chỉ nhận qua loopback của Pod, không nhận tại Pod IP chỉ vì đã khai `containerPort`. |
| Bind `0.0.0.0:8080` | Nhận trên các địa chỉ IPv4 cục bộ của Pod, gồm loopback và Pod IP. Đây là wildcard bind, không phải địa chỉ đích để quảng bá cho client. Không tự public ra Internet. |
| `containerPort` | Khai báo cổng dự kiến; không tạo listener, đổi cổng ứng dụng, mở firewall hoặc tự publish cổng Mac/node. Không khai field này cũng không tự chặn listener. |
| CNI và networking implementation | CNI là giao diện tích hợp mạng container. Runtime phối hợp thiết lập mạng Pod; implementation như Flannel cùng mạng node thực thi đường đi. Không phải một loại Service. |
| Đường trực tiếp Pod IP | Không cần Service, DNS, Traefik, host port mapping hoặc k3d `serverlb` để hai Pod trong cluster gọi nhau. API server không proxy từng HTTP request giữa hai ứng dụng. |

`kubectl exec` được gọi từ Mac nhưng chương trình `wget` chạy bên trong client Pod. API phục vụ thao tác exec và truyền output; kết nối HTTP tới server xuất phát từ mạng của client Pod.

## 2. Scaffold và cấu hình ứng dụng

| File | Resource và lựa chọn |
|---|---|
| [01-server.yaml](../thuc-hanh/13-pod-network/01-server.yaml) | Pod `pod-net-server`, container `http`, node selector hostname agent-0; tạo marker và chạy BusyBox `httpd`. |
| [02-client.yaml](../thuc-hanh/13-pod-network/02-client.yaml) | Pod `pod-net-client`, container `client`, node selector hostname agent-1; chạy `sleep 3600` để có nơi thực hiện request bằng `wget`. |

Cả hai dùng image pin:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

Docker Hub Tag API đã xác nhận bản `linux/arm64/v8`, manifest digest `sha256:d82c2ab94640ded77cf76514ce6a84870761105058a4a9e51b05a8a79be97a6c`. Đây là metadata registry; runtime imageID sau đó được kiểm tra trên cả hai Pod. `IfNotPresent` có thể dùng cache của từng node, không chứng minh vừa pull mới từ registry hoặc image trên Mac tự có ở mọi node.

Khối ứng dụng server, chạy bằng `/bin/sh -ec`:

```sh
mkdir -p /www
printf '%s\n' 'lesson13-cross-node-ok' > /www/index.html
exec httpd -f -p 0.0.0.0:8080 -h /www
```

- Shell thực hiện script; trong khối này, lỗi chuẩn bị thư mục/file sẽ làm script dừng thay vì tiếp tục khởi động server.
- `exec` thay shell bằng tiến trình HTTP server; `-f` giữ server chạy foreground.
- `-p 0.0.0.0:8080` thiết lập listener thật; thay đổi `containerPort` không thay thế cấu hình này.
- `-h /www` chọn document root. Request `/` với cấu hình này đọc `/www/index.html`.
- Marker là dữ liệu giả trong filesystem container, không dùng PVC và không có cam kết persistence.

### Các field đã đọc

| Vị trí trong Pod | Ý nghĩa, lý do và cạm bẫy |
|---|---|
| `metadata.name`, `metadata.namespace`, `metadata.labels` | Đặt tên/phạm vi `de-lab`; `lesson="13"`, `app=pod-net`, `role=server/client` giúp lọc đúng hai Pod. Label không tự tạo kết nối. |
| `spec.nodeSelector.kubernetes.io/hostname` | Server chọn `k3d-de-k3d-agent-0`, client chọn `k3d-de-k3d-agent-1`. Match sai hoặc node không khả dụng có thể làm Pending; không tự bỏ điều kiện để chạy trên server node. |
| `spec.hostNetwork: false` | Dùng mạng Pod; không bật chia sẻ mạng node để lách lỗi. |
| `spec.automountServiceAccountToken: false` | Ứng dụng test không cần credential gọi Kubernetes API. |
| `spec.enableServiceLinks: false` | Không bơm thông tin Service vào env; lab này dùng Pod IP trực tiếp. |
| `spec.restartPolicy: Always` | Có thể restart container khi nó thoát; không tạo lại naked Pod sau khi xóa Pod object. Client sleep một giờ có thể kết thúc rồi restart bình thường. |
| `spec.terminationGracePeriodSeconds: 5` | Budget dừng mềm đã chọn cho lab; không phải bằng chứng đã thử shutdown trong bài này. |
| `spec.containers[].image`, `imagePullPolicy` | Pin version/digest, `IfNotPresent`; node cần cache hoặc truy cập registry phù hợp kiến trúc. |
| `spec.containers[].command`, `args` | Cấu hình thực thi ứng dụng; server chạy script/httpd, client giữ container sống. |
| `spec.containers[].ports[]` | Server khai `name=http`, `containerPort=8080`, `protocol=TCP`, khớp listener. Tên cổng không tự bật HTTP. |
| `spec.containers[].resources` | Mỗi container requests CPU `25m`, memory `32Mi`; limits CPU `100m`, memory `64Mi`, đủ nhỏ cho workload test. Đây không phải số đo usage hoặc sizing DE production. |
| `spec.nodeName` | Node thực tế đã được gán; đọc để kiểm placement, không dùng field này thay scheduler trong bài. |
| `status.podIP`, `status.hostIP` | Pod IP khác IP node. Đây là kết quả hệ thống báo lại, không phải nơi khai địa chỉ mong muốn. |

Client dry-run/schema và kiểm tra cú pháp shell đã đạt trước khi giao triển khai. Các kiểm tra đó không được dùng thay bằng chứng runtime bên dưới.

## 3. Bằng chứng runtime và cách tự quan sát

Các lệnh chạy từ thư mục gốc repo, dùng đúng binary/context/namespace. IP, tuổi Pod và restart count có thể khác khi chạy lại; kiểm tra identity/IP trước khi tái dùng URL.

### 3.1 Placement và identity

```bash
/usr/local/bin/kubectl --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab get pods -l lesson=13 -o wide
```

Snapshot mentor trước phép thử HTTP, rút gọn các cột động/không liên quan:

```text
NAME             READY   STATUS    IP           NODE
pod-net-client   1/1     Running   10.42.1.28   k3d-de-k3d-agent-1
pod-net-server   1/1     Running   10.42.3.35   k3d-de-k3d-agent-0
```

Nhìn `NODE` để chứng minh khác node, `IP` để lấy đích trực tiếp, `READY/STATUS` để kiểm trạng thái. Do manifest không có readiness probe HTTP, `Ready` không tự chứng minh response HTTP đúng.

| Pod | UID | Pod IP / Host IP | Thời điểm tạo, giờ Việt Nam |
|---|---|---|---|
| `pod-net-server` | `c11ae52d-9e72-44e9-8519-16894bb5a3a1` | `10.42.3.35` / `192.168.155.4` | 2026-11-08 15:00:23 |
| `pod-net-client` | `b832041f-0ed0-41e2-b85e-5af225eec884` | `10.42.1.28` / `192.168.155.5` | 2026-11-08 15:00:24 |

Lượt kiểm tra trước khi mentor thử HTTP lúc **15:17:49** xác nhận hai UID trên, Running/Ready, restart 0, không owner/deletionTimestamp. Image/command/args/placement/resources khớp scaffold; `hostNetwork=false`, token automount tắt, không declared env/envFrom, volume, init hoặc ephemeral container. Không đọc/giải mã credential hoặc dump env.

### 3.2 HTTP thành công từ đúng client

```bash
/usr/local/bin/kubectl --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab exec pod-net-client -c client -- \
  wget -Y off -S -T 3 -O - http://10.42.3.35:8080/
```

- `-c client`: chọn container của Pod client; `--` ngăn cách tùy chọn kubectl với chương trình chạy trong container.
- `-Y off`: không dùng proxy, gọi đích trực tiếp.
- `-S`: hiển thị response headers; `-O -`: in body ra stdout, không lưu file.
- `-T 3`: network read timeout ba giây, không cam kết toàn bộ lệnh luôn kết thúc trong ba giây. Cú pháp đã được đối chiếu với source 1.37.0 và `wget --help` trong client Pod.

Hai phần output cần nhìn, trích rút gọn từ kết quả thực tế:

```text
HTTP/1.1 200 OK
lesson13-cross-node-ok
```

Phải kiểm cả status và marker, không chỉ thấy lệnh thoát thành công. Headers/stderr và body/stdout có thể xen thứ tự hiển thị.

**Nguồn minh chứng:**

- Học viên đã gửi terminal output của chính lệnh trên, có `200 OK`, marker và HTTP Date `2026-11-08 08:09:43 GMT` (15:09:43 giờ Việt Nam).
- Mentor tự chạy phép kiểm tra chỉ đọc riêng, cũng nhận `200 OK`, marker và HTTP Date `2026-11-08 08:18:04 GMT` (15:18:04 Việt Nam), exit code 0.
- Đây là hai quan sát khác nhau, không coi output tool mentor là màn hình học viên hoặc suy toàn bộ lịch sử lệnh từ snapshot.

### 3.3 Đối chứng cổng sai

```bash
/usr/local/bin/kubectl --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab exec pod-net-client -c client -- \
  wget -Y off -S -T 3 -O - http://10.42.3.35:9090/
```

Output học viên đã quan sát và mentor tự kiểm tra lại đều có:

```text
wget: can't connect to remote host (10.42.3.35): Connection refused
command terminated with exit code 1
```

Exit 1 là đối chứng thất bại có chủ đích, không phải yêu cầu sửa cluster. Giữ nguồn/đích nhưng đổi cổng; không có bằng chứng timeout ở lượt này và không ghi `Connection refused` thành timeout.

### 3.4 Đối chiếu listener thật

Mentor kiểm tra chỉ đọc; học viên có thể tự tái quan sát bằng:

```bash
/usr/local/bin/kubectl --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab exec pod-net-server -c http -- netstat -lnt
```

Output mentor thực tế:

```text
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN
```

Nhìn **`Local Address`** và **`State`**: listener TCP tại `0.0.0.0:8080`, không có listener TCP 9090 trong bảng được đọc. Kết hợp cấu hình, listener và hai phép thử cho thấy đối chứng phù hợp với sai cổng, không có cơ sở đổi CNI. Không suy mọi lỗi refused/timeout ở hệ thống khác đều có cùng nguyên nhân.

Kiểm tra cuối lúc **15:19:41** xác nhận hai Pod vẫn cùng UID/IP/node như bảng trên, Running/Ready, restart 0 và không deletionTimestamp. Không có thao tác thay đổi workload trong lượt review.

## 4. Lab làm giúp gì và ngoài lab cần gì?

Các Node của lab báo cấu hình sau; đây là snapshot metadata, không phải packet capture:

| Node | `spec.podCIDR` | Annotation `flannel.alpha.coreos.com/backend-type` |
|---|---|---|
| `k3d-de-k3d-agent-0` | `10.42.3.0/24` | `vxlan` |
| `k3d-de-k3d-agent-1` | `10.42.1.0/24` | `vxlan` |
| `k3d-de-k3d-server-0` | `10.42.0.0/24` | `vxlan` |

Ba Node Ready tại lượt kiểm tra cuối; UID giữ nguyên so với các snapshot trước: agent-0 `4ea95101-66d2-4a51-bf3e-c3d47602425d`, agent-1 `09b5909c-9cf8-4432-95c6-bda7167922f3`, server-0 `15152848-8931-45f4-a706-a61e4f1e87db`.

| Trong lab | Ngoài lab cần cung cấp/xác nhận |
|---|---|
| k3d tạo node-container và mạng kết nối chúng; K3s tích hợp Flannel. | Node có thể là VM hoặc máy vật lý. Cluster tự quản lý cần networking implementation và cấu hình node network; managed Kubernetes thường tích hợp một phần nhưng vẫn phải xác nhận thực tế. |
| Node có Pod CIDR riêng và báo backend VXLAN. | Chuẩn bị dải Pod/Service/node không xung đột với nhau hoặc mạng VPN/LAN, cùng route/firewall phù hợp implementation/backend. Không giả định mọi plugin dùng cùng IPAM hoặc phụ thuộc `Node.spec.podCIDR` như lab này. |
| VXLAN đóng gói traffic mạng Pod để đi trên mạng node. | Với **K3s + Flannel VXLAN**, cho phép UDP 8472 giữa các node tin cậy, không public ra Internet. Đây không phải cổng app TCP 8080, cũng không phải yêu cầu chung của mọi CNI. |
| Có quyền exec để chạy wget/netstat trên workload test. | Platform cần cấp quyền debug phù hợp, ví dụ quyền exec; admin của lab không phải mô hình quyền DE mặc định. |

Giữ implementation hiện có là lựa chọn phù hợp bài này: mục tiêu kiểm chứng đường kết nối, không thay CNI hoặc triển khai production chỉ để minh họa.

**Thứ tự debug đã học:** đúng client/context/namespace -> Pod IP/cổng đích -> cấu hình và listener -> placement -> networking/policy và đường node-node. Mac truy cập được qua port mapping không chứng minh client Pod có cùng route/policy. Một timeout đơn lẻ không đủ kết luận CNI hỏng.

### Hợp đồng nền tảng cho một kết nối DE

- Nêu nguồn -> đích, protocol/port, namespace, node và mốc thời gian; trong lab là client agent-1 -> server agent-0, TCP 8080.
- DE kiểm cấu hình ứng dụng, địa chỉ, listener và response/marker trong quyền được cấp. Khi cần thay networking/backend, route hoặc firewall node, chuyển platform/DevOps cùng bằng chứng thay vì bật `hostNetwork` để lách lỗi.
- Ngoài lab xác nhận networking implementation, dải IP và đường node-node; kiểm từ đúng nguồn, không chỉ từ browser trên Mac.
- Liên hệ Airflow/Spark: task Pod gọi Driver ở Pod khác không dùng localhost; listener của Driver và địa chỉ client dùng phải phù hợp, networking platform phải cho phép đường kết nối. Đây là liên hệ lý thuyết, chưa triển khai Airflow/Spark trong bài.

## 5. Review hiểu biết đã đạt

Học viên trả lời đúng **7/7**, không có câu đang chờ; không hỏi lại chỉ để đủ số:

| Khối / đáp án | Điều đã kiểm tra |
|---|---|
| 1 — `1B` | Localhost của client Pod không trỏ tới server Pod khác node. |
| 1 — `2B` | Chọn Pod IP, không chọn Host IP hoặc localhost để gọi trực tiếp Pod đích. |
| 2 — `1B` | App bind loopback có thể được gọi từ trong Pod nhưng không nhận tại Pod IP chỉ vì khai containerPort. |
| 2 — `2C` | App chỉ listen 9090 thì listener vẫn là 9090 dù YAML ghi containerPort 8080. |
| 3 — `1B` | Networking implementation và mạng node thực thi đường giữa hai Pod, không phải API server hay containerPort. |
| 3 — `2A` | Mac gọi được không thay phép thử từ đúng client Pod; cần khoanh vùng listener/IP/cổng rồi đường mạng/policy. |
| 4 — `B` | HTTP 404 khi đổi document root sang thư mục rỗng là phản hồi ứng dụng, cần kiểm file/root chứ không tự quy CNI. |

Ca bind loopback, mismatch cổng khai báo/listener và HTTP 404 được học/review bằng tình huống; **không triển khai biến thể bind loopback, đổi server sang 9090 hoặc đổi document root**. Đối chứng runtime thực tế chỉ đổi cổng trong URL client sang 9090. Bài gốc cho phép chỉ đọc ca loopback, không bắt chạy biến thể.

Không ghi các bẫy vừa giải thích thành lỗi học viên đã mắc: các đáp án Bài 13 đều đúng. Phân biệt runtime thành công với hiểu concept; ở đây có cả các checkpoint trước thực hành và bằng chứng live.

## 6. Giới hạn, trạng thái giữ lại và bài tiếp theo

- Chỉ kiểm chứng HTTP từ một client tới một server khác node tại các thời điểm nêu trên; không suy mọi Pod/cổng/namespace đều kết nối được.
- Chưa thực hành Service/DNS/Ingress/TLS hoặc NetworkPolicy enforcement. Không dùng lab này làm bằng chứng truy cập từ Mac/LAN/Internet.
- Không thử node/host failure, HA, performance, packet loss, MTU hoặc đường cloud thật. Hai agent vẫn chung host/runtime local.
- Giữ hai Pod và hai scaffold; không có recovery cần làm và bài gốc không yêu cầu cleanup. Không tự xóa để chốt bài, không ghi đã dọn. Client có thể restart sau mỗi lần sleep 3600 kết thúc; restart về sau không tự chứng minh Pod replacement hay lỗi mạng.
- Bài 12 và workload của nó không bị sửa/xóa trong bài này.
- **Bài 13 Hoàn thành đầy đủ.** Tiến độ học xong **13/32**, nghiệm thu đầy đủ **11/32** (01–07, 09–11 và 13); Bài 08/12 giữ nguyên phạm vi đã chốt.
- Chờ **Bài 14 — Service, EndpointSlice và DNS**, chưa giảng hoặc tạo scaffold bài mới. Vấn đề nối tiếp: Pod IP có thể đổi, nên client cần endpoint ổn định hơn.

## Nguồn đã đối chiếu

- [Pods / Pod networking — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/#pod-networking).
- [Pod API — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/).
- [Networking model — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/).
- [Container ports — source Kubernetes v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/staging/src/k8s.io/api/core/v1/types.go).
- [K3s basic network options](https://docs.k3s.io/networking/basic-network-options) và [network requirements](https://docs.k3s.io/installation/requirements#networking).
- [BusyBox 1.37.0 source archive](https://busybox.net/downloads/busybox-1.37.0.tar.bz2), đã đọc usage của `networking/httpd.c` và `networking/wget.c`; đối chiếu thêm wget help trong container thực tế.
- [Docker Hub metadata busybox:1.37.0](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0), đọc ngày 2026-11-08.
- [Linux IPv4 bind addresses](https://man7.org/linux/man-pages/man7/ip.7.html).
