# Sau buổi 06 — Truy cập từ macOS, LoadBalancer và Ingress

**Ngày học:** 2026-10-07 đến 2026-10-09. **Hoàn thành thực hành và review:** 2026-10-09, giờ Việt Nam.

[Challenge gốc](../roadmap/buoi-hoc/06-truy-cap-tu-macos.md) · [Tiến độ học tập](../roadmap/tien-do-hoc-tap.md) · [Manifest Ingress](../nginx-buoi6-ingress.yaml) · [Hội thoại và minh chứng](https://ampcode.com/threads/T-01a11575-bbd7-76d9-88ff-99613fd36c93)

> **Điểm cốt lõi:** DNS giúp tìm đường vào; LoadBalancer cung cấp endpoint khi có triển khai hỗ trợ; Ingress khai báo rule HTTP theo host/path; controller thực thi rule và chuyển request tới backend của ứng dụng. Cổng browser, cổng Service backend và cổng ứng dụng không bắt buộc giống nhau.

Không cần học thuộc IP, tên Pod hoặc boilerplate YAML. Các địa chỉ trong tài liệu là snapshot của lab, không phải giá trị dùng chung cho mọi cluster.

## 1. Challenge và minh chứng thực hành

Dùng lại Deployment `default/nginx-buoi3` với ba Pod và Service `default/nginx-buoi4`. Context là `orbstack`; không dùng cluster RKE2 khác trên máy.

| Chặng | Minh chứng và kết quả |
|---|---|
| Browser qua ClusterIP | Ngày 2026-10-07, học viên xác nhận mở được `http://192.168.194.166:80` khi Service còn là ClusterIP, port 80. Không có ảnh hoặc raw HTTP output cho bước browser này. |
| LoadBalancer | Học viên chọn `type=LoadBalancer`, `port=8080`, `targetPort=80`. Output Service có EXTERNAL-IP `192.168.139.2`, `8080:32274/TCP`; curl từ Mac tới `http://k8s.orb.local:8080` trả HTTP 200 và trang nginx lúc 16:09:52 ngày 2026-10-07, giờ Việt Nam. |
| Controller | API chỉ đọc ngày 2026-10-08 xác nhận Traefik Ready 1/1, Helm release `deployed`, Service LoadBalancer riêng mở 80/443 và IngressClass `traefik`. Mentor GET cổng 80 trước rule nhận 404; không ghi là học viên tự thực hiện lần GET này. |
| Ingress rule | Học viên chọn backend port 8080. Sau bước giao apply, output describe và API ngày 2026-10-09 xác nhận Ingress `nginx-buoi6` đã tồn tại: host `nginx.k8s.orb.local`, path `/`, class `traefik`, backend `nginx-buoi4:8080`. |
| Host không khớp | Curl học viên tới `http://sai.k8s.orb.local/` trả HTTP 404, body `404 page not found`, lúc 09:30:23 ngày 2026-10-09, giờ Việt Nam. |
| Host đúng | Curl học viên tới `http://nginx.k8s.orb.local/` trả HTTP 200, trang `Welcome to nginx!`, lúc 09:30:27 cùng ngày. |
| Browser qua Ingress | Sau khi được hỏi về đúng URL Ingress, học viên xác nhận “thấy rồi nhé”. Ghi nhận theo xác nhận học viên, không phải ảnh browser hoặc lần kiểm tra browser độc lập của mentor. |
| Review concept | Học viên trả lời đúng tình huống đổi Service port, phân biệt 404 với lỗi DNS và DNS không khắc phục thiếu triển khai LoadBalancer. |

**Giới hạn:** Không thử từ thiết bị LAN/Internet, không kiểm tra HTTPS, không đo phân phối request tới cả ba Pod hoặc tính liên tục khi Pod bị xóa. Browser thành công trên Mac không chứng minh có endpoint public, HA hoặc readiness production. Mentor không cài controller, apply/patch/xóa workload thay học viên; chỉ chuẩn bị manifest, kiểm tra local, inspect và review.

## 2. Các địa chỉ và cổng: xác định vai trò trước

| Khái niệm | Giá trị quan sát trong lab | Ý nghĩa |
|---|---|---|
| Pod IP | `192.168.194.8`, `.9`, `.11` | Địa chỉ các Pod nginx; ứng dụng nghe cổng 80. |
| Service IP / ClusterIP | `192.168.194.166` | Endpoint ảo của Service `nginx-buoi4`, ổn định trong vòng đời Service. |
| Node IP | `192.168.139.2` | INTERNAL-IP của node `orbstack`, nơi các Pod đang chạy. |
| LB IP | `192.168.139.2` | Địa chỉ được công bố trong status LoadBalancer của Service; cùng số với Node IP trong lab, nhưng khác vai trò. Không có quy tắc mọi LB IP phải khác Node IP hoặc LB phải là một máy riêng. |
| Service nginx `port` | `8080` | Cổng Service được client hoặc Ingress backend tham chiếu. |
| Service nginx `targetPort` | `80` | Cổng ứng dụng trên Pod đích. Service không tự làm nginx mở hoặc đổi cổng. |
| Service nginx `nodePort` | `32274` | Đường NodePort qua Node IP, được cấp trong cấu hình LoadBalancer của lab. |
| Service controller `port` | `80` cho HTTP; `443` cho HTTPS | Đường vào Traefik; chỉ HTTP được thực hành trong bài. |

`PORT(S)=8080:32274/TCP` là **Service port : nodePort**, không phải port : targetPort. Xem YAML hoặc `describe` để đọc targetPort.

Các cặp địa chỉ/cổng đã phân biệt:

- `ServiceIP:8080`: gọi endpoint Service nginx. Browser qua ClusterIP đã được xác nhận khi port còn là 80; không ghi đã thử trực tiếp ClusterIP ở port 8080.
- `NodeIP:32274`: đường NodePort. Học viên chọn đúng cặp này trong review, chưa có HTTP test trực tiếp qua nó.
- `LB-IP:8080`: đường vào LoadBalancer của nginx. HTTP đã kiểm chứng qua domain OrbStack `k8s.orb.local:8080`, không phải request trực tiếp tới LB IP.
- `nginx.k8s.orb.local:80`: đường vào controller rồi định tuyến HTTP theo Ingress.

Pod chạy **trên node**; Service/LB không phải nơi chứa Pod. Với Pod mới Ready, khớp selector và backend đã được cập nhật, client không cần sửa URL Service chỉ vì Pod IP thay đổi. Phần thay thế Pod đã thực hành ở [Buổi 05](05-service.md), không lặp lại trong buổi 6.

## 3. DNS, đường vào và HTTP routing là những việc khác nhau

Trong lab, `k8s.orb.local` và `*.k8s.orb.local` thuộc tích hợp local của OrbStack, không do Traefik hoặc resource Ingress tự tạo. Tên `nginx.k8s.orb.local` đã phân giải được trước khi có Ingress rule.

Kiểm tra bộ phân giải hệ điều hành Mac ở chặng trước thấy `k8s.orb.local` trả IPv4 `192.168.138.4`, khác LB IP `192.168.139.2`. Không suy đoán domain phải trỏ trực tiếp tới đúng địa chỉ trong cột EXTERNAL-IP hoặc khẳng định chi tiết proxy nội bộ OrbStack chưa kiểm chứng.

Luồng ở mức trách nhiệm, không mô tả mọi hop networking nội bộ:

```diagram
┌──────────────────────────────┐
│ Browser trên Mac             │
│ http://nginx.k8s.orb.local/  │
└──────────────┬───────────────┘
               │ phân giải tên; HTTP cổng 80
               ▼
┌──────────────────────────────┐
│ Đường vào local của OrbStack │
│ tới Service/controller       │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Traefik thực thi Ingress     │
│ đối chiếu HTTP Host và path  │
└──────────────┬───────────────┘
               │ host/path khớp; chọn backend
               ▼
┌──────────────────────────────┐
│ Một nginx Pod, cổng 80       │
└──────────────────────────────┘
```

Backend được cấu hình bằng **Service `nginx-buoi4`, port 8080**; Service chọn Pod theo `app=nginx-buoi3` và targetPort 80. Sơ đồ không khẳng định traffic từ controller bắt buộc phải đi qua ClusterIP nginx như một hop vật lý.

- **DNS:** tìm địa chỉ cho hostname, không đọc Ingress rule để chọn nginx Pod.
- **LoadBalancer / networking:** cung cấp đường tới controller khi hạ tầng và cấu hình hỗ trợ.
- **Ingress:** khai báo `host`, `path`, `class`, Service backend và port.
- **Traefik:** đọc cấu hình thuộc class phù hợp, nhận HTTP request và thực thi routing.
- **Ứng dụng nginx:** nhận request và tạo response.

`sai.k8s.orb.local` nhận được HTTP 404 nghĩa là đã nhận response HTTP, không phải lỗi “không phân giải được tên”. Trong bài, hostname đó không khớp rule nginx và không có catch-all trong manifest. Không coi mọi 404 trong mọi hệ thống đều là lỗi rule: ứng dụng cũng có thể tự trả 404; cần đối chiếu cấu hình và bằng chứng.

## 4. Controller, IngressClass và manifest cần hiểu

Lab đã có Helm CLI `v4.3.0+gbec5b06`, release `traefik` ở namespace `ingress-system`, chart `41.6.1`, app `v3.7.13`. Helm cài các resource theo chart, không nằm trong luồng HTTP của browser. Controller được cài riêng; OrbStack không cài sẵn controller cho challenge này.

Lệnh cài đã được giao, lưu để tham khảo; **không chạy lại trên lab đã có release**:

```bash
helm install traefik traefik \
  --repo https://traefik.github.io/charts \
  --version 41.6.1 \
  --kube-context orbstack \
  --namespace ingress-system --create-namespace \
  --wait --skip-crds \
  --set providers.kubernetesCRD.enabled=false
```

Bài dùng Ingress chuẩn Kubernetes; không cần IngressRoute, Gateway API hoặc dashboard. Trước bước giao cài, mentor đã render chart/client dry-run và kiểm tra image có Linux ARM64; các kiểm tra chuẩn bị này không thay thế kết quả controller Ready sau cài.

Manifest [nginx-buoi6-ingress.yaml](../nginx-buoi6-ingress.yaml) đã dùng:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-buoi6
  namespace: default
spec:
  ingressClassName: traefik
  rules:
    - host: nginx.k8s.orb.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-buoi4
                port:
                  number: 8080
```

| Field | Điều cần quyết định |
|---|---|
| `metadata.namespace` | Backend Service của Ingress chuẩn này phải ở cùng namespace: `default`. Controller có thể ở namespace khác. |
| `spec.ingressClassName` | Chọn class `traefik`, tương ứng controller đã triển khai. |
| `rules[].host` | Host của request cần khớp; field này không tự bảo đảm DNS được tạo. |
| `path` và `pathType` | `/` với `Prefix` phục vụ các path thuộc prefix root cho host đã khớp. |
| `backend.service.name` | Tham chiếu tên Service, không phải Deployment hoặc Pod. |
| `backend.service.port.number` | Tham chiếu **Service port 8080**, không phải targetPort/Pod port 80 hoặc nodePort 32274. |

Output describe có `nginx-buoi4:8080 (192.168.194.9:80,192.168.194.8:80,192.168.194.11:80)`: phần ngoài ngoặc là Service backend; phần trong ngoặc là các địa chỉ/cổng backend Pod. Không có Events không tự chứng minh HTTP thành công; curl và xác nhận browser cung cấp minh chứng ứng dụng.

Service nginx giữ type LoadBalancer từ chặng trước để không đổi hai hành vi cùng lúc. **Backend của Ingress không bắt buộc là LoadBalancer**; ClusterIP phù hợp nếu chỉ cần truy cập nội bộ từ controller. Chưa thực hành đổi lại type trong buổi này.

## 5. OrbStack làm giúp ↔ cấu hình ngoài lab

Phần này là giải thích/tham khảo, **không phải một hệ thống cloud/on-prem đã được dựng và kiểm thử**.

| Phần | Lab OrbStack | Ngoài OrbStack cần chuẩn bị và kiểm tra |
|---|---|---|
| Truy cập ClusterIP / Service DNS từ host | Mac có hỗ trợ truy cập ClusterIP và tên Service đầy đủ. Tên ngắn `nginx-buoi4` không phân giải trong lần kiểm tra Mac của bài. | Không mặc định máy ngoài cluster có route tới Service CIDR hoặc dùng DNS cluster. App nội bộ dùng service discovery; browser dùng đường expose phù hợp hoặc port-forward để debug. |
| Endpoint LoadBalancer | OrbStack xử lý Service LoadBalancer cho lab local. | `type=LoadBalancer` chỉ khai báo yêu cầu. Cloud cần tích hợp/provider LB và cấu hình internal/public phù hợp. Cluster tự quản lý cần triển khai LB hoặc đường vào thay thế, không chỉ tự điền một IP. Inspect Service/status/events để biết endpoint đã được cấp chưa. |
| Domain browser | `k8s.orb.local` và wildcard có tích hợp local. | Cấu hình bản ghi A/AAAA tới frontend IP, hoặc CNAME tới tên LB phù hợp; cấu hình host trong Ingress tương ứng. Phải quản lý bản ghi tại DNS mà client thực sự dùng. |
| HTTP routing | Traefik được cài riêng, thực thi Ingress host/path/class. | Cần controller đang chạy và nhận traffic; class của rule phải phù hợp. Bản thân Ingress không bảo đảm tự cấp LB/DNS; tự động hóa phụ thuộc controller/tích hợp được cấu hình. |
| Network reachability | Đã truy cập từ chính Mac. | Client phải có route và firewall cho phép frontend port; LB phải đưa traffic tới controller và controller tới backend. IP private không phải public Internet; VPN/gateway có thể cung cấp đường vào phù hợp. |

### Chọn đường vào theo môi trường

- **Cloud có tích hợp LB:** ưu tiên LB được nhà cung cấp hỗ trợ cho controller; cần quyền/tích hợp hoạt động, lựa chọn mạng private/public và quy tắc truy cập. Thuận tiện nhưng phụ thuộc provider và có thể phát sinh chi phí.
- **On-prem/LAN phù hợp:** có thể dùng MetalLB. Trong ví dụ L2 đã giới thiệu, `IPAddressPool.spec.addresses` xác định dải IP được dành riêng, không trùng DHCP/thiết bị; `L2Advertisement.spec.ipAddressPools` chọn pool để công bố trên mạng phù hợp. Có IP trong status chưa đủ nếu client không có route tới mạng đó. Người vận hành phải phối hợp địa chỉ/mạng; không cài MetalLB vào OrbStack chỉ để lặp chức năng sẵn có.
- **NodePort:** dùng Node IP có thể truy cập + nodePort, không cần external LB chỉ để dùng đường này. Đổi lại phải xử lý route/firewall và endpoint của node; có thể đặt LB/proxy bên ngoài phía trước.
- **Port-forward:** phù hợp debug cá nhân, không thay thế endpoint chia sẻ lâu dài. Ví dụ tham khảo chưa thực hành: `kubectl --context=orbstack -n default port-forward service/nginx-buoi4 18080:8080`, rồi gọi `http://localhost:18080` khi lệnh còn chạy. Đường này bỏ qua Ingress và không chứng minh host routing hoạt động.

**Khuyến nghị trong khóa học:** giữ OrbStack cho thực hành nhẹ; hiểu các phần phải cấu hình thêm trước khi đổi môi trường. Không bắt dựng production/cloud để đạt buổi 6.

Theo tài liệu OrbStack, chia sẻ NodePort/LoadBalancer ra LAN cần tùy chọn **Expose services to local network devices**. Chưa kiểm tra hoặc đổi tùy chọn này trong bài. “Cùng LAN” không tự bảo đảm truy cập được IP node ảo; không khẳng định người khác đã truy cập được.

## 6. Lệnh đã dùng và thứ tự điều tra

Các lệnh quan sát, không yêu cầu chạy lại để được tính hoàn thành:

```bash
kubectl --context=orbstack -n default get service nginx-buoi4 -o wide
kubectl --context=orbstack -n default get service nginx-buoi4 -o yaml
kubectl --context=orbstack -n ingress-system get pods
kubectl --context=orbstack -n ingress-system get service traefik -o wide
kubectl --context=orbstack get ingressclass
kubectl --context=orbstack -n default describe ingress nginx-buoi6
kubectl --context=orbstack -n default get endpointslices \
  -l kubernetes.io/service-name=nginx-buoi4 -o yaml
curl -i --max-time 10 http://nginx.k8s.orb.local/
curl -i --max-time 10 http://sai.k8s.orb.local/
```

Manifest đã được kiểm tra client dry-run trước khi học viên áp dụng. Lệnh apply được giao là `kubectl --context=orbstack apply -f nginx-buoi6-ingress.yaml`; mentor không chạy thao tác triển khai này thay học viên.

| Symptom | Bắt đầu điều tra ở đâu? |
|---|---|
| Không phân giải được tên | DNS client/bản ghi; trên Mac có thể inspect bộ phân giải hệ điều hành bằng `dscacheutil -q host -a name nginx.k8s.orb.local`. |
| LoadBalancer pending | Tích hợp/controller LB, cấu hình cấp IP, quyền và events của Service. DNS không tạo endpoint bị thiếu. |
| Đã có frontend nhưng kết nối timeout/refused | Địa chỉ/cổng có đúng không, route/firewall, Service/controller có nhận traffic không. Chưa kết luận là lỗi Ingress host. |
| Đã tới controller, host không khớp | HTTP Host, path, ingressClassName và rule controller đã nhận; 404 của bài thuộc chặng này. |
| Rule đúng nhưng backend lỗi | Service name/namespace/port, selector, EndpointSlice Ready, targetPort và ứng dụng có thực sự nghe cổng đó; đọc status/events/logs theo symptom. |

Để tách DNS khỏi đường vào trong môi trường khác, đã giới thiệu `curl --resolve`. Ví dụ tham khảo, thay `<IP_FRONTEND>` bằng IP frontend thực sự có thể truy cập trước khi chạy:

```bash
curl -i --max-time 10 \
  --resolve 'ui.example.com:80:<IP_FRONTEND>' \
  http://ui.example.com/
```

Lệnh giữ hostname/HTTP Host nhưng chỉ định IP cho kết nối. Nếu thành công trong khi URL bình thường không phân giải được, điều tra DNS; nếu vẫn thất bại thì tiếp tục kiểm tra lớp tương ứng. Chưa chạy bài thử này trên hệ thống ngoài lab, và đây không phải bằng chứng DNS đã được cấu hình đúng.

## 7. Nhầm lẫn đã xử lý và review cuối

- **Tên ngắn Service trên browser:** tên `nginx-buoi4` dùng được từ Pod cùng namespace không có nghĩa browser Mac cũng phân giải được. Học viên dùng ClusterIP/cổng 80 và xác nhận browser hoạt động sau hint chọn địa chỉ trong cột CLUSTER-IP.
- **Service IP, Node IP và LB IP:** được giảng lại theo vai trò từng địa chỉ. Học viên chọn đúng Service endpoint, cặp Node IP/nodePort và vai trò LB IP/Service port. Trong một ví dụ LB giả định, học viên viết sai số IP; mentor đối chiếu lại, không bắt học thuộc địa chỉ.
- **IP private:** EXTERNAL-IP nghĩa là endpoint được công bố cho đường LoadBalancer, không tự đồng nghĩa public Internet. Mac truy cập được chưa chứng minh LAN/Internet truy cập được.
- **Domain OrbStack:** không do nginx, Helm hoặc Ingress tự sinh; phân giải tên khác định tuyến HTTP. Quy tắc đối chiếu ngoài lab đã được lưu vào AGENTS và hướng dẫn mentor theo yêu cầu học viên.
- **Ingress backend port:** học viên chọn đúng 8080 ban đầu nhưng chưa nêu lý do; mentor giải thích Service port khác Pod port. Câu hỏi thay đổi cổng cuối buổi kiểm tra lại hiểu biết này.

| Tình huống review | Câu trả lời học viên và kết quả |
|---|---|
| Service port đổi 8080 → 9000, giữ targetPort 80 | Sửa Ingress backend port number thành 9000; URL browser giữ nguyên. Đúng, vì frontend controller vẫn cổng 80. Không sửa cấu hình thật sang 9000. |
| Host sai trả 404 có phải lỗi DNS? | Không; Traefik dùng host rule để chọn. Đúng ý chính; mentor bổ sung thông tin được lấy từ HTTP Host và còn xét path. |
| Thiếu triển khai LB, chỉ tạo DNS có giải quyết pending? | Không, phải xử lý LoadBalancer trước. Đúng ý chính; mentor chỉnh “DNS không có tác dụng” thành “DNS phân giải tên, không cấp/cấu hình LB”, và bổ sung endpoint phải được cấp/công bố cùng route/firewall phù hợp. |

**Kết quả:** thực hành HTTP đúng/sai host đạt, browser được học viên xác nhận, review concept đạt ngày 2026-10-09. Những cấu hình MetalLB/cloud, DNS ngoài lab, NodePort trực tiếp, port-forward và đổi backend port chỉ là giải thích/scenario; không ghi là đã triển khai.

## 8. Liên hệ Data Engineering và bước tiếp theo

- Spark Worker gọi Master RPC nội bộ và browser mở Spark UI là hai đường networking khác nhau. Service discovery nội bộ không tự tạo đường vào từ Mac.
- Airflow UI, Spark UI, MinIO Console và Trino UI có thể dùng host/path phù hợp qua controller. Backend port phải đối chiếu Service của đúng UI.
- Ingress chuẩn trong bài phục vụ HTTP; không mặc định đưa PostgreSQL hoặc mọi giao thức TCP/RPC qua rule HTTP giống nginx.
- Giữ service-to-service nội bộ khi không cần expose; networking không thay thế storage/persistence của PostgreSQL hoặc MinIO.

**Buổi 06 hoàn thành; tiến độ 6/28.** Chờ bắt đầu [Buổi 07 — Debugging Challenge #1](../roadmap/buoi-hoc/07-debugging-1.md); chưa triển khai challenge buổi 7 hoặc thay đổi workload khi chốt tài liệu.

## Tài liệu tham khảo

- [Kubernetes — Service](https://kubernetes.io/docs/concepts/services-networking/service/): loại Service, port mapping và yêu cầu triển khai LoadBalancer.
- [Kubernetes — Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/): rule host/path, backend và controller.
- [OrbStack — Kubernetes](https://docs.orbstack.dev/kubernetes/): networking từ Mac, domain local và chia sẻ LAN.
- [Traefik — 404 Not Found](https://doc.traefik.io/traefik/getting-started/faq/#404-not-found): response khi không có router phù hợp.
- [Traefik chart 41.6.1](https://github.com/traefik/traefik-helm-chart/blob/v41.6.1/traefik/Chart.yaml): phiên bản chart đã được chọn cho lab.
- [MetalLB — Configuration](https://metallb.io/configuration/): IPAddressPool và công bố L2 trong ví dụ on-prem.
- [Kubernetes — port-forward](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/): đường debug cá nhân khác đường Ingress.
