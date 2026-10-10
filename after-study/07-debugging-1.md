# Sau buổi 07 - Debugging Challenge #1

**Ngày học và hoàn thành:** 2026-10-09, giờ Việt Nam. **Tiến độ sau review:** 7/28.

[Challenge gốc](../roadmap/buoi-hoc/07-debugging-1.md) · [Tiến độ học tập](../roadmap/tien-do-hoc-tap.md) · [Manifest đã sửa](../nginx-buoi7-debug.yaml) · [Buổi 06](06-truy-cap-tu-macos.md)

> Điểm cốt lõi: bắt đầu từ trạng thái và bằng chứng, sửa đúng lớp đang lỗi, rồi kiểm tra lại endpoint người dùng cần. Pod Ready không tự chứng minh Service hoặc Ingress đã hoạt động.

## 1. Challenge và kết quả

Tự triển khai một manifest cố ý có lỗi trong context `orbstack`, namespace `default`. Không sửa hoặc xóa workload các buổi trước để giải bài.

Yêu cầu:

1. Deployment `nginx-buoi7` có hai Pod Ready.
2. Service `nginx-buoi7` dùng ClusterIP, client gọi cổng 8080.
3. Ingress class `traefik`, host `debug.k8s.orb.local`, path `/` đưa request tới ứng dụng; curl trả HTTP 200 và browser thấy trang nginx.
4. Giải thích được symptom, bằng chứng, nguyên nhân, field đã sửa và cách kiểm tra lại.

**Kết quả:** cấu hình, runtime và review concept đạt. Mentor không triển khai, patch, xóa workload hoặc sửa manifest thay học viên; chỉ đọc cluster, kiểm tra HTTP/browser và lưu tài liệu học tập.

## 2. Quá trình debug do học viên mô tả

1. Dùng `kubectl get pod`, thấy Pod của challenge bị `ImagePullBackOff`.
2. `describe` một Pod, đọc Events báo không tìm thấy image; đổi image trong manifest và apply lại, thấy Pod chạy.
3. Inspect Service; `describe` không có Endpoints. So sánh selector với nhãn Pod, phát hiện `nginx-buoi07` không khớp `nginx-buoi7`.
4. Kiểm tra tiếp targetPort, sửa cổng đích thành 80 để khớp nginx trong bài.
5. Apply cấu hình đã sửa và báo kết quả đúng; mentor kiểm tra độc lập xác nhận API, HTTP và browser.

Đây là mô tả của học viên, không phải transcript terminal trước khi sửa. Không ghi rằng học viên đã gửi raw output cho từng bước hoặc đã dùng `logs` trong quá trình điều tra; logs ở lượt review được mentor đọc.

## 3. Ba lỗi và cấu hình đã sửa

| Phần | Cấu hình ban đầu | Sau sửa | Bằng chứng và ý nghĩa |
|---|---|---|---|
| Image | `nginx:stable-alpnie` | `nginx` | Events còn thông báo image không tìm thấy, `ErrImagePull` và `ImagePullBackOff`; sau sửa pull thành công và container khởi động. |
| Service selector | `app=nginx-buoi07` | `app=nginx-buoi7` | Học viên mô tả Endpoints rỗng trước sửa; API sau sửa xác nhận selector khớp nhãn và có đúng hai backend Ready. |
| Service targetPort | `8080` | `80` | nginx của bài nghe cổng 80; API hiện có backend cổng 80, HTTP qua Service và Ingress trả 200. Không có raw HTTP trước sửa để gán một status lỗi cụ thể. |

Những phần giữ nguyên: hai replicas, Service ClusterIP/cổng 8080, Ingress class `traefik`, hostname, Prefix `/` và backend Service port 8080.

## 4. Minh chứng kiểm tra độc lập

Snapshot ngày 2026-10-09; địa chỉ và tên Pod chỉ là giá trị của lab, không phải giá trị dùng chung.

| Kiểm tra | Kết quả |
|---|---|
| Deployment | `nginx-buoi7`, revision 2, READY=2/2, UP-TO-DATE=2, AVAILABLE=2. |
| Pod thứ nhất | `nginx-buoi7-57658cb977-7cbxp`, IP `192.168.194.18`, Running, READY=1/1, RESTARTS=0. |
| Pod thứ hai | `nginx-buoi7-57658cb977-nb4sg`, IP `192.168.194.19`, Running, READY=1/1, RESTARTS=0. |
| Service | ClusterIP `192.168.194.185`, selector `app=nginx-buoi7`, port 8080, targetPort 80. |
| EndpointSlice | `nginx-buoi7-6qprs`, đúng hai Pod ở trên; ready/serving true, terminating false; port 80. |
| Ingress | Class `traefik`, host `debug.k8s.orb.local`, Prefix `/`, backend `nginx-buoi7:8080`. |
| Curl qua Service | `http://192.168.194.185:8080/` trả HTTP 200 và trang nginx lúc 10:52:06 giờ Việt Nam. |
| Curl qua Ingress | `http://debug.k8s.orb.local/` trả HTTP 200 và trang nginx cùng thời điểm. |
| Browser của mentor | URL hostname Ingress, title/heading `Welcome to nginx!` lúc 10:52:11 giờ Việt Nam. |
| Logs | Hai container khởi động; có GET `/` trả 200. |
| Workload cũ | Deployment `nginx-buoi3` vẫn 3/3; Service `nginx-buoi4` và Ingress `nginx-buoi6` vẫn tồn tại với cấu hình đã học. |

Events còn ghi lỗi image ban đầu và rollout phục hồi. ReplicaSet mới `nginx-buoi7-57658cb977` có hai replicas; ReplicaSet cũ `nginx-buoi7-7dbd95bd4d` giữ 0 replicas. Image sai còn trong ReplicaSet cũ không có nghĩa Pod hiện tại vẫn dùng image sai.

Browser console có 404 cho `/favicon.ico`; nginx log xác nhận file favicon không tồn tại. GET `/` vẫn trả 200, nên đây không phải lỗi trang chủ hoặc bằng chứng host routing chưa hoạt động.

**Giới hạn:** HTTP/browser là kiểm tra của mentor, không phải output browser do học viên gửi. Chưa tạo client Pod mới, thử LAN/Internet, đo phân phối đều request, tính liên tục khi thay Pod hoặc triển khai hệ thống cloud/on-prem. Snapshot không chứng minh chưa từng có thay đổi tạm thời giữa các lần quan sát.

## 5. Field và mental model quan trọng

| Field | Điều cần hiểu |
|---|---|
| Deployment `spec.replicas` | Desired state là hai Pod; không phải số tiến trình nginx trong container. |
| `spec.template.spec.containers[].image` | Chọn image cho container; không tìm được image thì cần đọc Events trước khi tìm lỗi ứng dụng. |
| `spec.template.metadata.labels` | Nhãn của Pod được tạo từ template. |
| Service `spec.selector` | Chọn Pod theo nhãn trong cùng namespace, không theo tên Deployment. |
| Service `spec.ports[].port` | Cổng endpoint Service mà client hoặc Ingress backend tham chiếu: 8080. |
| Service `spec.ports[].targetPort` | Cổng đích ứng dụng đang lắng nghe trên backend Pod: 80 trong bài. |
| Container `ports[].containerPort` | Khai báo cổng container; không tự cấu hình nginx mở cổng đó. |
| Ingress `backend.service.port.number` | Tham chiếu Service port 8080, không phải Pod port 80. |
| Ingress `rules[].host` | Rule HTTP host, không phải thao tác tạo bản ghi DNS. |

Cấu hình Service đã dùng, trích từ manifest sau sửa:

```yaml
spec:
  type: ClusterIP
  selector:
    app: nginx-buoi7
  ports:
    - name: http
      port: 8080
      targetPort: 80
```

Luồng trách nhiệm: browser tìm đường vào controller; Traefik đối chiếu host/path và backend Service port; backend ứng dụng nhận request ở cổng lắng nghe. Không khẳng định controller phải chuyển mọi request qua ClusterIP như một hop vật lý.

**Lưu ý image:** `image: nginx` không có tag tương đương dùng tag `latest`. Chấp nhận trong challenge này nhưng chưa ghim image. Tag cụ thể dễ đọc và theo dõi phiên bản; digest ghim nội dung chặt hơn. Với cấu hình cần tính lặp lại, nên ghim image đã kiểm tra phù hợp. `imagePullPolicy: Always` không có nghĩa luôn tải lại mọi layer đã cache; runtime phân giải image và dùng cache khi phù hợp. Không đổi image thay học viên trong review.

## 6. Review đã thực hiện

| Câu review | Câu trả lời và kết quả |
|---|---|
| Đã debug theo thứ tự nào, dùng bằng chứng gì? | Học viên mô tả get Pod, describe/Events lỗi image, apply lại, describe Service/Endpoints rỗng, đối chiếu selector và targetPort. Đạt; mô tả khớp cấu hình sửa và Events còn lại. |
| nginx đã thực sự đổi sang cổng 9000, Service vẫn cổng 8080 thì sửa gì? | Sửa targetPort của Service; không đổi backend port Ingress hoặc URL browser vì Service port vẫn 8080. Đạt; cổng 9000 chỉ là scenario, không đổi cấu hình thật. |
| Ngoài OrbStack, thêm Ingress đã đủ để máy khác vào bằng hostname chưa? | Ban đầu học viên nêu LoadBalancer/MetalLB và check EXTERNAL-IP. Đúng phần cấp endpoint nhưng thiếu DNS/reachability; mentor tách vai trò và giải thích MetalLB là triển khai LoadBalancer. |
| Đường vào với đúng HTTP Host đã trả 200, hostname lại không phân giải thì xử lý lớp nào? | Học viên nêu DNS resolution, hostname trỏ tới IP LoadBalancer. Đạt ý chính; chưa nhớ cấu hình ở đâu và cách kiểm tra, mentor bổ sung ở mục 7, không ghi là học viên tự nêu đầy đủ. |

Không yêu cầu học thuộc syntax hoặc command. Những nội dung mentor bổ sung được lưu để tra lại; không coi ví dụ ngoài lab là đã thực hành.

## 7. OrbStack làm giúp và cấu hình ngoài lab

### Trong lab

OrbStack hỗ trợ Mac truy cập ClusterIP và domain wildcard `*.k8s.orb.local`; hỗ trợ đường vào cho Service LoadBalancer. Traefik đã được cài riêng ở Buổi 06, không phải controller do OrbStack cài mặc định.

Kiểm tra resolver macOS cho `debug.k8s.orb.local` trả IPv4 `192.168.138.4` và IPv6 của tích hợp local. Địa chỉ DNS này khác status Ingress `192.168.139.2`; không suy đoán tất cả hop/proxy nội bộ hoặc buộc chúng phải trùng số.

### Ngoài lab: thành phần và cấu hình

| Phần | Cần chuẩn bị, cấu hình và kiểm tra |
|---|---|
| Cloud có tích hợp LB | Service controller có `type: LoadBalancer`; tích hợp/provider và quyền cấp LB hoạt động, lựa chọn mạng private/public và quy tắc truy cập phù hợp. Kiểm tra Service status/events và hạ tầng LB của provider. Không mặc định có IP public. |
| On-prem với MetalLB | MetalLB là một triển khai Service LoadBalancer. Trong ví dụ L2, `IPAddressPool.spec.addresses` chọn dải IP được dành riêng, không trùng thiết bị/DHCP; `L2Advertisement.spec.ipAddressPools` chọn pool để công bố trên mạng phù hợp. Kiểm tra resource/config, Service status và logs controller khi cấp/công bố IP không đúng. Đây là tham khảo, không cài vào OrbStack. |
| Đường mạng | Máy khách phải có route tới frontend và firewall cho phép cổng HTTP 80 của ví dụ; controller phải nhận traffic và tới được backend. IP trong EXTERNAL-IP chỉ là một bằng chứng cấp endpoint, không thay thế kiểm tra kết nối. |
| HTTP routing | Controller Ready, `ingressClassName` phù hợp, host/path và backend Service/port đúng. DNS không chọn Pod hoặc tự sửa rule. |
| DNS hostname | Tạo bản ghi tại DNS quản lý tên đó và được client sử dụng; DNS không tự có chỉ vì tạo Ingress. Hostname DNS và HTTP host rule phải phù hợp với đường truy cập dự kiến. |

Các lựa chọn đường vào: cloud LB thuận tiện nhưng phụ thuộc provider/chi phí; on-prem MetalLB cần chuẩn bị mạng và dải IP; NodePort có thể giảm phụ thuộc LB nhưng phải quản lý Node IP/nodePort và route/firewall. Port-forward phù hợp debug cá nhân, không thay thế endpoint chia sẻ hoặc kiểm chứng Ingress.

**Khuyến nghị trong khóa học:** giữ OrbStack và Traefik hiện có để học/debug; chỉ tra cấu hình ngoài lab khi cần, không dựng production để vượt challenge.

### DNS: cấu hình gì và ở đâu?

Với ví dụ giả định `ui.example.com`, cấu hình tại DNS quản lý zone `example.com`, không phải field `host` trong Ingress:

- Nếu frontend có IPv4, dùng bản ghi **A** cho hostname, giá trị là IPv4 frontend mà client có thể truy cập.
- Nếu frontend có IPv6, dùng bản ghi **AAAA** với IPv6 phù hợp.
- Nếu provider công bố frontend bằng hostname, có thể dùng **CNAME** cho subdomain tới hostname frontend đó.
- Tên nội bộ cần bản ghi trong hệ thống DNS nội bộ mà client thực sự dùng. Tạo bản ghi public tới IP private không tạo thêm routing/VPN hoặc mở firewall.

Ví dụ nếu zone do Cloudflare quản lý: chọn domain, vào **DNS > Records > Add record**, nhập type/name/content phù hợp và lưu. Với ví dụ chỉ phân giải trực tiếp tới frontend, dùng chế độ **DNS only**; tính năng proxy là một lớp khác. Đây là ví dụ giao diện tham khảo, không khẳng định học viên đang dùng Cloudflare hoặc đã tạo bản ghi thật.

Kiểm tra trên máy client xem hostname trả địa chỉ dự kiến; kiểm tra HTTP qua hostname sau khi đường mạng đã sẵn sàng. Có thể kiểm tra resolver hệ điều hành trên Mac hoặc tra bản ghi A/AAAA qua DNS phù hợp. Nếu một request tới frontend kèm đúng HTTP Host đã thành công nhưng hostname không phân giải, điều tra DNS trước, không sửa backend chỉ vì browser báo lỗi tên.

## 8. Command để ôn lại

Các lệnh cluster dưới đây chỉ đọc; không cần chạy lại để được tính hoàn thành:

```bash
kubectl --context=orbstack -n default get deployment,replicaset,pod,service,ingress \
  -l app=nginx-buoi7 -o wide
kubectl --context=orbstack -n default describe deployment/nginx-buoi7 \
  service/nginx-buoi7 ingress/nginx-buoi7
kubectl --context=orbstack -n default get endpointslices \
  -l kubernetes.io/service-name=nginx-buoi7 -o yaml
kubectl --context=orbstack -n default get events --sort-by=.metadata.creationTimestamp
kubectl --context=orbstack -n default logs -l app=nginx-buoi7 --prefix=true --tail=35
curl -i --max-time 10 http://debug.k8s.orb.local/
dscacheutil -q host -a name debug.k8s.orb.local
```

Ví dụ tra DNS cho hostname giả định bên ngoài, chưa chạy hoặc cấu hình trong bài:

```bash
dig A ui.example.com +short
dig AAAA ui.example.com +short
```

Để tách DNS khỏi HTTP routing, có thể tham khảo `curl --resolve` ở [tổng kết Buổi 06](06-truy-cap-tu-macos.md). Không coi một override DNS dùng khi debug là bản ghi DNS đã được cấu hình đúng.

## 9. Liên hệ Data Engineering và bước tiếp theo

- Khi Spark Worker không tìm được Master hoặc UI không mở được, tách trạng thái Pod, service discovery, Service/backend và đường vào từ client thay vì đoán một lỗi networking chung.
- Khi sửa cổng MinIO API hoặc Spark UI, đối chiếu cổng client gọi, Service port và cổng ứng dụng; không đồng nhất chúng.
- Lỗi lấy image xảy ra trước khi ứng dụng khởi động; Events có thể là bằng chứng quan trọng hơn logs ứng dụng ở giai đoạn đó.

**Buổi 07 hoàn thành, tiến độ 7/28.** Chờ bắt đầu [Buổi 08 - ConfigMap](../roadmap/buoi-hoc/08-configmap.md); chưa bắt đầu hoặc triển khai challenge mới.

## Tài liệu tham khảo

- [Kubernetes - Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/).
- [Kubernetes - Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/).
- [Kubernetes - Images](https://kubernetes.io/docs/concepts/containers/images/).
- [Kubernetes - Service](https://kubernetes.io/docs/concepts/services-networking/service/).
- [Kubernetes - Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/).
- [OrbStack - Kubernetes](https://docs.orbstack.dev/kubernetes/).
- [MetalLB - Configuration](https://metallb.io/configuration/).
- [Cloudflare - Manage DNS Records](https://developers.cloudflare.com/dns/manage-dns-records/how-to/create-dns-records/).
- [Cloudflare - DNS Record Fields](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/partials/dns/dns-record-steps.mdx).
- [Cloudflare - Inspect DNS with dig](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/tunnel/troubleshooting/https-origins.mdx).
