# Tổng kết Bài 16 — DNS bên ngoài và TLS

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/16-dns-tls.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/17-networkpolicy.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-10**, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phạm vi:** kubeconfig `~/.kube/config`, context `k3d-de-k3d`; Ingress/Secret/backend ở `de-lab`, Traefik ở `kube-system`.
- **Kết quả:** HTTPS với CA tin cậy tường minh trả `HTTP 200` và marker; bỏ CA lab thì curl từ chối certificate. Certificate frontend phục vụ khớp file public đã tạo.
- **HTTPS cuối trước cleanup:** mentor kiểm tra độc lập lúc **22:24:41 ngày 10/11**; không dùng `-k`.
- **Snapshot chốt và cleanup:** **22:37:04 ngày 10/11**; không còn listener `8445`, Ingress/Secret và backend vẫn giữ nguyên.
- **Ranh giới:** học viên tự chạy script sinh certificate/key, tạo Secret/Ingress và port-forward. Mentor chỉ chuẩn bị scaffold, kiểm tra chỉ đọc và lưu tài liệu khi toàn bài đạt; không đọc private key, dump Secret, sửa trust store hay thao tác workload thay học viên.

## 1. Challenge và đầu ra

Dùng lại backend Bài 14 và controller Bài 15 để phục vụ hostname `lesson16.test` qua HTTPS. Client phải xác minh certificate bằng CA test riêng, không bỏ xác minh. Có đối chứng client không tin CA và phân biệt bằng chứng DNS với TLS.

Chọn **port-forward tạm thời** thay vì thêm HTTPS port mapping vào k3d: ít thay đổi hạ tầng, đủ kiểm TLS/route, nhưng không nghiệm thu frontend LoadBalancer. Đường web thông thường qua k3d serverlb/ServiceLB không được kiểm bằng phép thử này.

## 2. Mental model đã học

### Bốn lớp không thay thế nhau

| Lớp | Câu hỏi cần trả lời | Không tự làm giúp |
|---|---|---|
| DNS/phân giải tên | Client dùng IP nào cho hostname? | Không cấp LB, mở cổng hoặc tạo certificate. |
| TLS | Client có xác minh đúng server và bảo vệ kết nối không? | Không tự tạo đăng nhập/phân quyền UI. |
| HTTP routing | Host/path này đi tới backend nào? | Ingress `host` không đăng ký DNS. |
| Authentication/authorization | Người dùng là ai, được làm gì? | Không được bảo đảm chỉ vì HTTPS trả 200. |

Client gửi **SNI trong quá trình thiết lập TLS**, server trình bày certificate và client xác minh. Sau đó HTTP Host/path được xét bên trong kết nối TLS. Với curl, hostname trong URL quyết định SNI và tên cần xác minh; chỉ đổi header `Host` không đổi chúng. `--resolve` chỉ đổi địa chỉ kết nối cho cặp hostname/cổng, giữ hostname trong URL.

Các kiểm tra certificate trọng tâm: hostname được SAN bao phủ, thời hạn hợp lệ và chuỗi chữ ký dẫn tới CA client tin. Certificate đúng tên/còn hạn vẫn có thể bị từ chối nếu client không tin bên cấp.

### Hai vai trò, hai bộ certificate/private key

| File ngoài Git | Vai trò | Ai cần dùng? |
|---|---|---|
| `ca.crt` | Certificate công khai của CA test, chứa public key kiểm chữ ký bên cấp | Client chọn tin qua `--cacert`. |
| `ca.key` | Private key dùng ký certificate server | Nơi cấp certificate; không đưa cho Traefik. |
| `server.crt` | Certificate công khai cho `lesson16.test`, chứa public key server | Traefik trình bày cho client. |
| `server.key` | Private key tương ứng của server | Traefik dùng trong TLS; phải giữ kín. |

Copy certificate không đủ để giả làm server: TLS còn yêu cầu chứng minh sở hữu private key tương ứng mà không gửi private key cho client. Chữ ký CA và bằng chứng sở hữu khóa của server là hai việc khác nhau. Đây là xác minh server, không phải đăng nhập người dùng UI.

## 3. Scaffold và cấu hình đã chọn

Trong repository chỉ chuẩn bị các scaffold công khai:

- [ca.cnf](../thuc-hanh/16-dns-tls/ca.cnf).
- [server.cnf](../thuc-hanh/16-dns-tls/server.cnf).
- [01-create-test-certificates.sh](../thuc-hanh/16-dns-tls/01-create-test-certificates.sh).
- [02-ingress-tls.yaml](../thuc-hanh/16-dns-tls/02-ingress-tls.yaml).

### Cấu hình công cụ mật mã, không phải Kubernetes

| Field/khối | Ý nghĩa và lý do |
|---|---|
| `[req]`, `prompt=no`, `distinguished_name` | Đọc section định danh, không hỏi tương tác. |
| `CN` trong `ca_dn`/`server_dn` | Đặt tên định danh; hostname server vẫn được khai tường minh trong SAN. |
| `x509_extensions=v3_ca`, `CA:TRUE`, `pathlen:0` | Cấu hình CA test ký trực tiếp leaf; lab không dựng CA trung gian. |
| CA `keyUsage=keyCertSign,cRLSign` | Khả năng ký certificate/danh sách thu hồi; không có dịch vụ thu hồi được triển khai trong bài. |
| `req_extensions=server_req` | Đưa SAN vào CSR, tức yêu cầu cấp certificate; CSR không phải private key. |
| `v3_server`, `CA:FALSE`, `extendedKeyUsage=serverAuth` | Certificate phục vụ TLS server, không mang vai trò CA. |
| Server `keyUsage=digitalSignature,keyEncipherment` | Mục đích sử dụng khóa server RSA trong cấu hình lab. |
| `subjectAltName=@alt_names`, `DNS.1=lesson16.test` | Tên certificate bao phủ; dùng nhất quán với URL và Ingress. |
| `subjectKeyIdentifier`, `authorityKeyIdentifier` | Nhận diện khóa/issuer; không thay SAN hoặc niềm tin của client. |

Script dùng `/usr/bin/openssl` đã kiểm là **LibreSSL 3.3.6**, RSA 2048 bit, SHA-256; CA 7 ngày, certificate server 2 ngày. Lệnh ký leaf dùng `-extfile server.cnf -extensions v3_server`, không chỉ để SAN nằm trong CSR.

Mọi artifact sinh ra nằm ở `~/.local/share/k8s-practice/lesson16-tls/`, ngoài repository. Script dùng `umask 077`, thư mục `700`, từ chối ghi đè đường dẫn đã tồn tại. Key không có passphrase chỉ dành cho dữ liệu lab giả, không là mẫu vận hành CA production. Không chạy lại script để review hoặc tự xóa thư mục khi gặp lỗi.

### Kubernetes và controller

| Resource/field | Quan hệ và hành vi |
|---|---|
| Secret `de-lab/lesson16-tls`, type `kubernetes.io/tls` | Đóng gói certificate/key server đã có; không cấp/gia hạn certificate. |
| Secret key `tls.crt` / `tls.key` | Nhận `server.crt` / `server.key`; không chứa `ca.key`. Tên key khác với nội dung private key. |
| Ingress `metadata.name=lesson16-web` | Resource mới, không sửa `lesson15-web`. |
| Ingress `metadata.namespace=de-lab` | TLS Secret và backend Service được tham chiếu ở cùng namespace. |
| `spec.ingressClassName=traefik` | Chọn class/controller đã có; không tự cài Traefik. |
| `spec.tls[].hosts`, `spec.rules[].host` | Cùng dùng `lesson16.test`, nhất quán với SAN. Không tạo DNS hoặc sửa nội dung certificate. |
| `spec.tls[].secretName=lesson16-tls` | Tham chiếu Secret, không phải đường dẫn file trên Mac. |
| Annotation `traefik.ingress.kubernetes.io/router.entrypoints=websecure` | Chọn listener HTTPS đã có của Traefik; không mở cổng Mac. |
| Annotation `traefik.ingress.kubernetes.io/router.tls="true"` | Bật TLS tường minh cho router; là cấu hình riêng của Traefik, không phải field dùng chung mọi controller. |
| Path `/`, `pathType=Prefix` | Rule HTTP được xét sau khi xử lý TLS. |
| `backend.service.name=service-dns-svc`, `port.number=80` | Tham chiếu cổng Service HTTP; không đổi thành 443 chỉ vì client dùng HTTPS. |

Traefik live là `rancher/mirrored-library-traefik:3.5.1`; entrypoint `websecure` nghe Pod port `8443`, Service Traefik port `443` trỏ tới named targetPort `websecure`. K3s đã chuẩn bị controller/listener này; đó không phải tính năng tự có từ object Ingress. Client `/usr/local/bin/kubectl` **v1.33.9**, API server **v1.33.6+k3s1**; không nâng cấp tool/cluster.

## 4. Certificate thực tế và trách nhiệm renewal

Metadata public được mentor kiểm tại file và đối chiếu với certificate frontend phục vụ:

| Mục | Kết quả |
|---|---|
| Leaf subject | `CN=lesson16.test` |
| Leaf SAN | `DNS:lesson16.test` |
| Issuer | `CN=lesson16-test-ca` |
| Bắt đầu hiệu lực | `Nov 10 09:33:19 2026 GMT` = **16:33:19 ngày 10/11/2026**, giờ Việt Nam |
| Leaf hết hạn | `Nov 12 09:33:19 2026 GMT` = **16:33:19 ngày 12/11/2026**, giờ Việt Nam |
| CA hết hạn | `Nov 17 09:33:19 2026 GMT` = **16:33:19 ngày 17/11/2026**, giờ Việt Nam |

Fingerprint SHA-256 của certificate server, là metadata công khai:

```text
63:A3:4C:38:22:A2:6D:1F:51:D4:17:94:31:F3:C7:FD:57:A6:89:09:55:B7:50:1E:D1:9F:5C:C1:73:F5:22:99
```

**Renewal owner trong lab: học viên, bằng quy trình thủ công.** Nếu còn dùng HTTPS sau thời hạn trên, cần cấp certificate mới, cập nhật Secret rồi xác minh certificate frontend thực sự phục vụ; chỉ có file mới hoặc Ingress/Secret còn tồn tại không đủ. Không yêu cầu thực hành renewal để hoàn thành bài này.

Ngoài lab phải xác nhận owner/issuer/quy trình cập nhật và theo dõi hạn với platform/PKI. Cấp thủ công ít thành phần nhưng phải tự theo dõi; cert-manager có thể tự động hóa khi controller/issuer được cấu hình phù hợp. Không cài/cấu hình cert-manager hoặc issuer tự động trong bài; khai `spec.tls` không tự thiết lập renewal.

## 5. Lệnh đã giao, kết quả và cách đọc

Các lệnh dưới ghi lại thực hành, không phải yêu cầu chạy lại khi đọc tổng kết. **Tunnel đã dừng khi chốt bài**; không kỳ vọng curl tới `8445` còn thành công.

### 5.1 Học viên tạo certificate ngoài Git

Từ thư mục repository:

```bash
bash roadmap-k3d/thuc-hanh/16-dns-tls/01-create-test-certificates.sh
```

Học viên gửi output script: kiểm chuỗi thành công, đúng subject/issuer/ngày hiệu lực và `SAN=DNS:lesson16.test`. Mentor tự kiểm tra public metadata và quyền file lúc **16:34:55**. Thư mục `700`, bốn file chính `600`, cùng owner hiện tại; kiểm lại lúc chốt vẫn giữ như vậy. Không đọc private key.

`Getting CA Private Key` là thông báo công cụ sử dụng khóa CA để ký, không phải đang in private key. Các dòng tiến trình sinh RSA không là lỗi.

Lệnh chỉ đọc để xem lại thời hạn:

```bash
/usr/bin/openssl x509 \
  -in "$HOME/.local/share/k8s-practice/lesson16-tls/server.crt" \
  -noout -dates
```

Output đã kiểm:

```text
notBefore=Nov 10 09:33:19 2026 GMT
notAfter=Nov 12 09:33:19 2026 GMT
```

Nhìn `notAfter`, chú ý GMT khác giờ Việt Nam. Kiểm file local chưa chứng minh frontend đang phục vụ certificate đó; mentor kiểm certificate frontend riêng lúc 22:24:41.

### 5.2 Học viên tạo TLS Secret

```bash
/usr/local/bin/kubectl \
  --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab create secret tls lesson16-tls \
  --cert="$HOME/.local/share/k8s-practice/lesson16-tls/server.crt" \
  --key="$HOME/.local/share/k8s-practice/lesson16-tls/server.key"
```

Học viên gửi `secret/lesson16-tls created`, rồi chạy:

```bash
/usr/local/bin/kubectl \
  --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab describe secret lesson16-tls
```

Output học viên đã gửi, rút gọn:

```text
Name:         lesson16-tls
Namespace:    de-lab
Type:  kubernetes.io/tls

Data
====
tls.crt:  1196 bytes
tls.key:  1675 bytes
```

Nhìn namespace/type và hai tên key. Với Secret TLS này, Data của describe hiển thị số byte, không phải giá trị; không suy mọi loại Secret đều an toàn khi describe. Mentor chỉ kiểm metadata/tên key; không dump YAML/data hoặc giải mã Secret. Secret có chứa private key server, nên quyền truy cập và mã hóa at rest phải do nền tảng cấu hình, không tự bảo đảm bởi tên gọi Secret.

### 5.3 Học viên tạo Ingress

```bash
/usr/local/bin/kubectl \
  --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab apply \
  -f roadmap-k3d/thuc-hanh/16-dns-tls/02-ingress-tls.yaml
```

Trước khi giao apply, mentor đã strict client dry-run; đó chỉ kiểm cấu hình, không thay runtime. Học viên gửi `ingress.networking.k8s.io/lesson16-web created` và kết quả quan sát:

```bash
/usr/local/bin/kubectl \
  --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d --request-timeout=10s \
  -n de-lab get ingress lesson16-web \
  -o 'custom-columns=NAME:.metadata.name,HOST:.spec.rules[*].host,TLS_SECRET:.spec.tls[*].secretName'
```

```text
NAME           HOST            TLS_SECRET
lesson16-web   lesson16.test   lesson16-tls
```

Đây là custom columns, không phải cột mặc định. HOST/TLS_SECRET cho biết tham chiếu; object tồn tại không chứng minh đường HTTPS mở. Mentor đối chiếu live spec, annotations và labels khớp manifest, kể cả snapshot đóng bài.

### 5.4 Học viên mở port-forward trên Terminal A

```bash
/usr/local/bin/kubectl \
  --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d --request-timeout=0 \
  -n kube-system port-forward \
  --address=127.0.0.1 \
  service/traefik 8445:443
```

Học viên gửi:

```text
Forwarding from 127.0.0.1:8445 -> 8443
```

`kube-system` là namespace của Service/controller, không phải yêu cầu chuyển Secret sang đó. Service port `443` được kubectl resolve tới Pod port `8443`; Service dùng để chọn Pod/cổng, không phải đường traffic qua Service VIP. Terminal phải giữ chạy; `Handling connection for 8445` chỉ báo có kết nối.

Mentor đọc listener là `kubectl`, PID `18717`, chỉ bind `127.0.0.1:8445`. Quyền port-forward đã kiểm trong lab, không là quyền DE mặc định. Đường logic:

```text
Mac 127.0.0.1:8445
  -> tunnel kubectl/API server
  -> Traefik Pod:8443, TLS kết thúc tại Traefik
  -> HTTP backend được tham chiếu bởi service-dns-svc:80
  -> Pod ứng dụng:8080
```

Không khẳng định request bắt buộc đi xuyên ClusterIP: Traefik có thể gọi endpoint Pod trực tiếp. Tunnel vẫn phụ thuộc kết nối API; phép thử không kiểm đường web HTTPS thông thường qua k3d serverlb/ServiceLB.

### 5.5 HTTPS với CA tin cậy trên Terminal B

```bash
curl -q --noproxy '*' --connect-timeout 3 --max-time 8 -sS \
  --cacert "$HOME/.local/share/k8s-practice/lesson16-tls/ca.crt" \
  --resolve lesson16.test:8445:127.0.0.1 \
  -w '\nHTTP %{http_code}\n' \
  https://lesson16.test:8445/
```

Mentor kiểm độc lập bằng lệnh này ở **22:19:11** và **22:24:41**; output thực tế:

```text
lesson14-service-dns-ok

HTTP 200
```

- URL giữ hostname cho SNI/xác minh certificate và HTTP Host.
- `--resolve` ánh xạ riêng cho đúng cặp tên/cổng `8445`; không tạo DNS record, không chứng minh DNS OS/browser.
- `--cacert` chọn CA test để tin, không phải credential đăng nhập ứng dụng.
- `-q` bỏ config curl mặc định; `--noproxy '*'` tránh proxy; không có `-k`.
- Nhìn cả marker và HTTP 200; marker Bài 14 đúng vì dùng lại ứng dụng đó.

Học viên báo đã chạy thành công, nhưng không gửi raw output của phép thử này. Kết quả chi tiết ở trên là mentor tự kiểm tra, không ghi thành học viên đã xác nhận quan sát mọi field.

### 5.6 Đối chứng không tin CA lab

Giữ cùng URL/resolve/tunnel, chỉ bỏ `--cacert`:

```bash
curl -q --noproxy '*' --connect-timeout 3 --max-time 8 -sS \
  --resolve lesson16.test:8445:127.0.0.1 \
  -w '\nHTTP %{http_code}\n' \
  https://lesson16.test:8445/
```

Mentor kiểm độc lập lúc **22:19:11** và **22:24:41**; exit code **60**, stderr/stdout trích rút gọn:

```text
curl: (60) SSL certificate problem: unable to get local issuer certificate
...
HTTP 000
```

Đây là đối chứng đúng, không sửa Secret/Ingress hoặc thêm `-k`. `60` là mã lỗi curl; `HTTP 000` nghĩa là chưa có HTTP response, không phải server trả status 000. Client từ chối ở TLS trước khi gửi request HTTP tới ứng dụng. Học viên báo tiếp tục sau khi được giao đối chứng, không gửi raw output; bằng chứng runtime chi tiết là mentor kiểm tra.

Ở **22:24:41**, mentor chỉ lấy public certificate từ TLS handshake để đọc subject/issuer/dates/fingerprint: khớp fingerprint file `server.crt` ở mục 4. Không xuất raw TLS session hoặc private key.

## 6. Review concept và phần phải giảng lại

Có **16 lựa chọn trắc nghiệm đúng**, gồm các lượt tái giảng, không có câu đang chờ:

| Khối | Đáp án học viên | Điểm đã kiểm tra |
|---|---|---|
| DNS/đường frontend | `1B, 2C` | DNS đúng chưa chứng minh cổng mở; resolve override không là DNS hệ thống. |
| TLS cơ bản | `1B, 2C, 3A` | Hostname, xác minh certificate, HTTPS không thay auth. |
| SNI/Host và Secret namespace | `1C, 2A` | Host header không đổi tên xác minh TLS; Secret cùng namespace. |
| File server và renewal | `1B, 2C` | Cặp server cho TLS Secret; renewal thủ công phải cập nhật và kiểm frontend. |
| Tái giảng CA trust | `B` | Certificate do CA client chưa tin phải bị từ chối. |
| Tái giảng private key server | `A` | Copy certificate không đủ chứng minh sở hữu khóa. |
| Tái giảng vai trò CA | `B` | Không chép `ca.key` cho Traefik. |
| Đưa file vào cluster | `A` | TLS Secret, không trỏ đường file Mac để Traefik tự đọc. |
| TLS termination/backend | `B` | Frontend HTTPS không buộc backend HTTP đổi sang 443. |
| Giới hạn port-forward | `A` | Tunnel thành công chưa nghiệm thu đường LB/serverlb hoặc máy khác. |
| Review cuối HTTP 404 | `B` | TLS đã xác minh thì ưu tiên Host/path/routing/backend, không tạo lại CA hoặc thêm `-k`. |

**Điểm quan trọng về nhịp học:** dù 9 câu đầu chọn đúng, học viên nói phần certificate khó hiểu và bị loạn. Mentor đã tạm dừng lab, bỏ chi tiết OpenSSL/CSR khỏi lượt giải thích, lần lượt dựng lại CA trust → certificate/public key/private key server → vai trò `ca.key`, rồi mới quay lại thao tác nhỏ. Không coi điểm trắc nghiệm ban đầu là bằng chứng đã hiểu sâu, không yêu cầu nhớ thuật toán hoặc cú pháp OpenSSL. Các bước sau tiếp tục theo lệnh → output → cách đọc, mỗi lượt một việc.

## 7. Lab làm giúp và cấu hình ngoài lab

| Phần | Lab đã kiểm | Ngoài lab cần cung cấp/xác nhận |
|---|---|---|
| Đường vào | Port-forward loopback qua API tới Pod Traefik | On-prem cần frontend/VIP/LB và đường mạng; cloud cần tích hợp/controller LB phù hợp. Xác nhận private/public, nguồn client, listener/firewall/route. |
| Controller | K3s đã cài Traefik và HTTPS entrypoint; class `traefik` có thật | Controller/class và listener phải được platform cung cấp; annotation phụ thuộc controller. |
| Cổng | Mac `8445`, Service controller `443`, Pod controller `8443`; backend Service `80`/Pod `8080` | Ví dụ Traefik sau LB: frontend 443 → Service controller port 443 → targetPort/listener phù hợp. Đây là mô hình tham khảo, không cấu hình production đã chạy. |
| Tên | `--resolve` cho curl và `.test` | A/AAAA tới IP thích hợp hoặc CNAME tới hostname frontend khi phù hợp; DNS không chứa cổng HTTP trong bản ghi A/AAAA. |
| Trust | CA test theo request bằng file `ca.crt` | Public/private CA, chuỗi certificate và cơ chế phân phối trust đúng nhóm client. Không cài CA lab vào trust store toàn máy. |
| Renewal | Học viên theo dõi/cấp thủ công | Owner/issuer, tự động hóa nếu có, cập nhật Secret và quan sát hạn/certificate frontend. |
| Quyền/auth | Identity lab tạo Secret/Ingress và port-forward được | Namespace/RBAC/Secret mechanism và auth/access policy cho UI; không mặc định DE có quyền vào `kube-system`. |

Thứ tự debug: phân giải tên → đường kết nối frontend/tunnel → TLS hostname/chain/thời hạn → Host/path/class → Service port/endpoints/readiness → ứng dụng. HTTP 404 sau TLS thành công khác với curl 60 trước HTTP. Không chữa sai tầng bằng tăng replicas, tạo lại CA hoặc bỏ verify.

Port-forward tạm thời được chọn để giảm thay đổi; thêm HTTPS mapping vào k3d là phương án khác đã nêu trade-off nhưng **không thực hiện**. Docker serverlb vẫn chỉ có API `127.0.0.1:6445` và HTTP `8085:80` trên wildcard; không thêm mapping 443. OrbStack LAN policy đọc lại lúc chốt vẫn `false`, không phải bằng chứng kiểm từ LAN hoặc thay binding Docker thành loopback.

## 8. Snapshot tài nguyên giữ lại khi đóng bài

Mentor kiểm **22:37:04 ngày 2026-11-10**, đúng `k3d-de-k3d`; `de-lab`/`kube-system` Active:

| Resource | Identity/trạng thái |
|---|---|
| Ingress `de-lab/lesson16-web` | UID `53608c99-541d-4ce9-afba-a2af6e3699d2`, generation 1; spec/annotations/labels khớp scaffold, không deletionTimestamp. |
| Secret `de-lab/lesson16-tls` | UID `a1a7f641-3e09-4f32-87c8-a24d35e028df`, type `kubernetes.io/tls`, tên key `tls.crt`/`tls.key`; không xem giá trị. |
| Ingress `de-lab/lesson15-web` | Vẫn UID `ca30a22b-6466-4808-b31a-53b18c726cbc`, generation 1, không deletionTimestamp. |
| Service `de-lab/service-dns-svc` | UID `290cea51-38e4-47ed-8044-845f06fd10b1`, ClusterIP `10.43.62.113`, port 80 → named targetPort `http`. |
| Deployment `de-lab/service-dns-server` | UID `5269a553-0ac4-4328-97e7-07cf81ced00d`, generation 1, desired/ready/available 1. |
| Backend Pod `service-dns-server-758b6cd595-j52cl` | UID `edb615d0-460b-45e3-a962-ec2748c8584b`, `10.42.0.44`, server-0, Running/Ready, restart 0, không deletionTimestamp. |
| EndpointSlice `service-dns-svc-hnbtr` | UID `bb6a1e0d-15c1-4c92-aa16-56d19ab50865`, generation 16; đúng target UID/IP:8080, ready/serving=true, terminating=false. |
| Deployment `kube-system/traefik` | UID `5c6eeb18-6090-49a4-b874-ff1c3917ad8d`, generation 1, desired/ready 1; image 3.5.1. |

Snapshot metadata sau cleanup không được ghi thành HTTPS GET mới; các HTTPS GET cuối ở 22:24:41 trước khi dừng tunnel. Không kiểm lại toàn bộ workload/node/Lease các bài cũ trong lượt này, không suy HA hoặc mở lại Bài 08/12.

## 9. Cleanup và giới hạn minh chứng

Học viên được giao `Ctrl+C` trên Terminal A và báo xong. Mentor kiểm chỉ đọc:

```bash
lsof -nP -iTCP:8445 -sTCP:LISTEN
```

**Kết quả sau cleanup:** không có output; lúc kiểm lại **22:37:04**, exit 1 vì không thấy listener. Mentor không kill process hoặc dừng tunnel thay học viên. Snapshot không chứng minh chính xác lịch sử phím bấm, nhưng đủ xác nhận cổng không còn listener tại thời điểm chốt.

Giữ Ingress/Secret/backend/scaffold và thư mục certificate ngoài Git. Chỉ dừng tunnel, không xóa resource, không restart node/controller hoặc thay trust store. Không lưu private key, giá trị Secret/token/kubeconfig hoặc raw TLS session vào tài liệu.

Chưa kiểm: DNS OS/browser/public DNS; HTTPS qua frontend k3d serverlb/ServiceLB hoặc cloud/on-prem LB; LAN/Internet reachability; public CA trust; auth/SSO/mTLS; renewal runtime; HA, hiệu năng hoặc bảo mật production. Đối chứng âm là **CA không được tin**; không ghi đã thực nghiệm lỗi hostname hoặc certificate hết hạn.

## 10. Liên hệ Data Engineering và bước tiếp

Khi yêu cầu expose Airflow UI hoặc Spark UI, DE cần nêu nhóm client, hostname, frontend, TLS termination, backend port, issuer/trust/renewal owner và auth/access policy riêng. UI trả 200 qua HTTPS không chứng minh người không có quyền đã bị chặn. Đây là liên hệ thiết kế, chưa triển khai Airflow/Spark hoặc SSO trong bài.

**Bài 16 Hoàn thành.** Tổng học xong **16/32**, nghiệm thu đầy đủ **14/32** (01–07, 09–11 và 13–16). Giữ nguyên phạm vi đã chốt của Bài 08/12. Chờ **Bài 17 — NetworkPolicy**, chưa giảng/tạo scaffold. Đây là lượt lưu gộp duy nhất khi toàn bài đạt; không commit/push.

## Nguồn đã đối chiếu

- [Ingress TLS — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/ingress/#tls).
- [TLS Secrets — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/configuration/secret/#tls-secrets).
- [Port-forward — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/).
- [curl — hostname, SNI và resolve override](https://everything.curl.dev/usingcurl/connections/name.html).
- [curl — TLS Certificate Verification](https://curl.se/docs/sslcerts.html).
- [Traefik v3.5.1 — Kubernetes Ingress](https://raw.githubusercontent.com/traefik/traefik/v3.5.1/docs/content/routing/providers/kubernetes-ingress.md).
- [kubectl v1.33.9 — Secret describer](https://github.com/kubernetes/kubernetes/blob/v1.33.9/staging/src/k8s.io/kubectl/pkg/describe/describe.go).
