# Tổng kết buổi 17 — Spark networking và UI

**Ngày học/chốt:** 2026-10-15, giờ Việt Nam. **Trạng thái:** Hoàn thành sau thực hành và review. **Tiến độ:** 17/28.

[Challenge gốc](../roadmap/buoi-hoc/17-spark-networking-va-ui.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Manifest Ingress](../yaml/spark-buoi17-ingress.yaml) · [Manifest Spark](../yaml/spark-buoi16.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a13d72-5993-764d-976a-fd9e459845ef)

> Học viên chọn Ingress thay port-forward, tự triển khai và xác nhận browser mở được UI. Mentor chuẩn bị scaffold, kiểm tra dry-run/schema và đọc cấu hình/trạng thái live; không apply, restart, đổi Master/Workers/Service hoặc submit application thay học viên.

## 1. Challenge và kết quả

Từ browser trên Mac chạy OrbStack, mở `http://spark.k8s.orb.local` và thấy hai Workers registered trên Master UI; phân biệt đường HTTP UI với Spark RPC.

Minh chứng chốt ngày 2026-10-15, context `orbstack`, namespace `default`:

- API có Ingress `spark-master-ui`, UID `d4dc0571-2c74-4533-9106-f4dc5f40f436`; class, host/path và backend khớp manifest.
- Service `spark-master-svc` giữ ClusterIP `192.168.194.202`; EndpointSlice trỏ Master `192.168.194.82`, Ready/serving, có RPC 7077 và UI 8080.
- Kiểm tra HTTP/HTML lúc 16:42 (+07): đúng tiêu đề `Spark Master at spark://192.168.194.82:7077`; cả hai hàng Worker là `ALIVE`, mỗi Worker 1 core/512 MiB. Stylesheet `/static/bootstrap.min.css` cũng tải được qua hostname này.
- `/json/` qua chính Ingress xác nhận Master `ALIVE`, hai Workers `ALIVE` tại `192.168.194.80:7078` và `192.168.194.81:7078`.
- Browser Chrome headless với profile mới, tách khỏi profile người dùng, render đúng UI lúc 16:44 (+07). Ảnh đã được kiểm tra: hai Workers `ALIVE`, bảng/stylesheet hiển thị đúng, không phải trang 404 hay Console khác. Học viên cũng xác nhận bước browser đã xong.
- Trước triển khai, hostname Spark trả 404; sau triển khai trả HTTP 200. Đối chứng sau triển khai: cùng URL/frontend nhưng gửi `Host: unmatched-spark-buoi17.invalid` trả 404.

Đạt challenge buổi 17. UI hiện có một completed application `TestDF`, state `FINISHED`; bản ghi này không tự chứng minh kết quả tính toán, cách submit hoặc vị trí Driver. Chưa dùng nó để đánh dấu buổi 18 hoàn thành.

## 2. Hai đường kết nối độc lập

| Đường | Giao thức/cổng | Mục đích |
|---|---|---|
| Worker → `spark://spark-master-svc:7077` | Spark RPC 7077 | Đăng ký Worker, phối hợp quản lý tài nguyên; không phải HTTP UI. |
| Browser → `http://spark.k8s.orb.local` | HTTP 80 ở frontend | Traefik so khớp Ingress rồi chuyển tới backend UI của Master, cổng 8080. |
| HTTP UI trên Master | HTTP 8080 | Hiển thị registry/trạng thái của Master, không thay Driver hoặc thực thi task. |

Luồng logic của UI:

```text
Mac resolver → frontend local → Traefik
    → rule Host spark.k8s.orb.local, path /
    → backend của Service spark-master-svc:8080
    → Master HTTP listener :8080
```

Đây là luồng logic theo cấu hình backend; không phải packet trace chứng minh controller bắt buộc đi qua ClusterIP thay vì trực tiếp tới endpoint.

Không đổi Worker Master URL sang 8080 khi mở UI. Ingress HTTP thông thường không làm cổng RPC 7077 thành HTTP; trỏ backend UI nhầm sang 7077 có thể làm browser lỗi trong khi Worker RPC vẫn hoạt động.

## 3. Field cấu hình và quan hệ tham chiếu

| Field/khối | Giá trị và lý do |
|---|---|
| `apiVersion`/`kind` | `networking.k8s.io/v1`, `Ingress`: khai báo rule HTTP, không tự cài controller. |
| `metadata.namespace` | `default`, cùng namespace với Service backend. |
| `spec.ingressClassName` | `traefik`, khớp IngressClass được controller hiện có xử lý. |
| `rules[].host` | `spark.k8s.orb.local`: điều kiện so khớp HTTP Host, không tự tạo DNS record. |
| `http.paths[].path`/`pathType` | `/` và `Prefix`: route cả trang chính và đường dẫn static; không cần subpath/rewrite trong bài này. |
| `backend.service.name` | `spark-master-svc`, tên Service thật, không phải tên Deployment hoặc IP Pod. |
| `backend.service.port.number` | `8080`, tham chiếu Service port HTTP UI, không phải frontend port 80 hoặc RPC 7077. |
| Service `targetPort: web-ui` | Tham chiếu container port có tên `web-ui` của Master; listener thực tế chạy ở 8080. |

Không thêm TLS/auth, không expose Worker UI hay Master REST submission trong buổi này. HTTP chỉ dành cho lab local; không lấy cấu hình này làm cấu hình bảo mật production.

## 4. Review và nhầm lẫn đã xử lý

- Ban đầu học viên dùng việc Pod còn tồn tại/chưa chắc đăng ký để giải thích scenario UI sai cổng. Đã tách Pod tồn tại, Pod Ready và Worker ALIVE trong registry Spark: đây là các loại bằng chứng khác nhau.
- Sau giải thích, học viên trả lời đúng không đổi Worker URL sang UI vì kết nối đó là RPC. Không bắt trả lời lại chỉ để lặp thuật ngữ.
- Với scenario `spark.example.com` tới đúng frontend nhưng rule yêu cầu `spark.k8s.orb.local`, học viên trả lời đúng request không khớp Host. DNS tới đúng địa chỉ không tự đổi HTTP Host.
- Theo yêu cầu học viên, bỏ phương án port-forward trước khi thực hành; không khởi chạy tunnel. Chọn rule Ingress độc lập, giữ cấu hình RPC và các workload khác.
- Server dry-run/strict đạt chỉ kiểm tra schema/admission, chưa chứng minh rule đã được lưu hoặc Traefik route được. Sau khi học viên tự apply, mentor mới xác nhận bằng API, HTTP, registry và browser render.

Master UI là công cụ quan sát cluster Spark cho Data Engineer. Hai Workers ALIVE là điều kiện tài nguyên khả dụng ở snapshot này, không phải bằng chứng một DataFrame đã tính đúng, Parquet đã ghi hoặc application có thể chịu lỗi Driver/Master.

## 5. Commands tham khảo và thứ tự debug

Các lệnh triển khai được giao để **học viên tự chạy**, không phải mentor apply thật:

```bash
kubectl --context orbstack -n default apply \
  --dry-run=server --validate=strict -f yaml/spark-buoi17-ingress.yaml
kubectl --context orbstack -n default apply -f yaml/spark-buoi17-ingress.yaml
kubectl --context orbstack -n default get ingress spark-master-ui
```

Kiểm tra chỉ đọc, chạy trên Mac lab có đường tới hostname:

```bash
kubectl --context orbstack -n default get ingress spark-master-ui -o yaml
kubectl --context orbstack -n ingress-system get deployment traefik
kubectl --context orbstack -n default get service spark-master-svc
kubectl --context orbstack -n default get endpointslices \
  -l kubernetes.io/service-name=spark-master-svc
curl --noproxy '*' -I http://spark.k8s.orb.local/
curl --noproxy '*' -I -H 'Host: unmatched-spark-buoi17.invalid' \
  http://spark.k8s.orb.local/
```

Debug theo lớp: resolver của client → frontend/controller và cổng vào → class/Host/path → Service port/selector/EndpointSlice → HTTP listener. Kiểm tra static resources nếu trang có HTML nhưng thiếu giao diện. Đăng ký Worker phải đối chiếu registry/RPC riêng, không chỉ trạng thái Kubernetes hoặc HTTP 200.

## 6. OrbStack làm giúp ↔ hệ thống ngoài lab

**Trong lab:** OrbStack cung cấp wildcard `*.k8s.orb.local` và tích hợp đường mạng/LoadBalancer local cho Mac. Traefik là controller đã được cài trong `ingress-system`, không suy ra OrbStack mặc định cài Ingress controller. Kubernetes Ingress là rule/API; Traefik mới thực thi rule đó.

Mac resolver trong lần kiểm tra trả IPv4 `192.168.138.3`, còn Ingress/LoadBalancer status là `192.168.139.2`. Hai giá trị khác nhau không tự chứng minh cấu hình sai: đường vào thực tế đã được kiểm tra bằng HTTP/browser. Không sửa DNS thành IP Pod Master chỉ để làm các số giống nhau.

**Ngoài OrbStack:**

- Cần controller hoạt động và `ingressClassName` trỏ đúng class. Chỉ tạo Ingress không đủ nếu thiếu thành phần thực thi.
- Cần đường vào controller: cloud có thể dùng Service `LoadBalancer` với tích hợp nhà cung cấp; on-prem có thể dùng LB được cấu hình riêng hoặc NodePort kèm reverse proxy/LB. Chọn theo hạ tầng, không mặc định mọi cluster tự cấp IP public. Bài lab giữ controller/entrypoint sẵn có, không dựng thêm hạ tầng.
- Cần DNS do client sử dụng trỏ hostname tới frontend phù hợp, route/firewall cho phép cổng vào, và mạng/policy cho controller tới backend. `rules.host` phải khớp hostname client gửi, Service port/targetPort phải dẫn tới HTTP listener đúng.
- Với endpoint dùng thật, thêm TLS/chứng chỉ qua `spec.tls` và cơ chế xác thực/kiểm soát truy cập phù hợp. Ingress tồn tại không đồng nghĩa endpoint đã được bảo vệ.
- Kiểm tra theo cùng thứ tự resolver → frontend/controller → class/Host/path → backend/EndpointSlice → listener, thay vì chỉ đổi hostname hoặc restart Worker.

**Giới hạn:** kiểm chứng truy cập local từ Mac chạy OrbStack; chưa chứng minh LAN/Internet/public DNS, TLS/auth, hệ thống multi-node, HA hoặc application execution. Các cấu hình ngoài lab ở trên là đối chiếu lý thuyết, chưa được triển khai/thử nghiệm.

## Bước tiếp theo và tài liệu

[Buổi 18 — Submit Spark application](../roadmap/buoi-hoc/18-submit-spark-application.md): học luồng cấp Executor và luồng Driver gửi task trực tiếp tới Executor trước khi thực hành. Đã thấy `TestDF` trong completed registry, nhưng cần bằng chứng phù hợp để xác định Driver/Executors và kết quả application; mentor không tự chạy thêm job.

- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/).
- [OrbStack Kubernetes: domains, networking và Ingress](https://docs.orbstack.dev/kubernetes/).
- [Spark 4.1.3 Standalone: Master/Worker UI và RPC](https://spark.apache.org/docs/4.1.3/spark-standalone.html).
- [Spark 4.1.3 cluster overview: Driver, cluster manager và Executors](https://spark.apache.org/docs/4.1.3/cluster-overview.html).
