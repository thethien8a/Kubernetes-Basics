# Bài 15 — Đường vào cluster và Ingress

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](14-service-dns.md) · [Tiếp](16-dns-tls.md)

**Đầu vào:** Service/backend hoạt động nội bộ. **Đầu ra:** yêu cầu đúng đường vào thay vì chỉ thêm `type: LoadBalancer`.

## 1. Khối kiến thức

- NodePort mở cổng Service trên địa chỉ node theo implementation/config; LoadBalancer yêu cầu hạ tầng/controller cung cấp frontend. Không loại nào tự bảo đảm có public IP hoặc firewall cho phép.
- Ingress là rule HTTP(S), controller đọc rule để chuyển traffic; không mặc định phù hợp giao thức Spark RPC/PostgreSQL. Dịch vụ nội bộ không cần public UI để client Pod gọi được.
- K3d serverlb/port mapping, K3s ServiceLB và Traefik Ingress controller là ba vai trò khác nhau. ServiceLB thường dùng host ports trên nodes; địa chỉ node container không mặc định được Mac/LAN route tới.
- So hai lựa chọn: NodePort đơn giản để thấy mapping nhưng phải quản lý cổng; Ingress phù hợp nhiều HTTP UI dùng hostname/path nhưng cần controller và frontend. Chọn Ingress cho HTTP demo, không cài thêm MetalLB chỉ để làm bài.

## 2. Đọc cấu hình

| Field/config | Ý nghĩa/cạm bẫy |
|---|---|
| Service `spec.type`, `ports[].nodePort` | Chọn kiểu expose; NodePort không tự map cổng Docker ra Mac. |
| K3d `ports[].port`, `nodeFilters` | Đường host → proxy/node; phải đối chiếu bản config đã tạo ở Bài 02. |
| Ingress `spec.ingressClassName` | Chọn controller/class tồn tại, không chỉ tên đặt tùy ý. |
| `spec.rules[].host`, `http.paths[].path`, `pathType` | Điều kiện route; Host/path không match có thể trả default response. |
| Backend `service.name`, `service.port` trong path | Tham chiếu Service port cùng namespace, không trực tiếp container port. |

## 3. Kiểm tra hiểu trước lab

1. Tạo Ingress rule nhưng không có controller xử lý class. Điều gì còn thiếu? **A.** Chỉ đổi Pod name. **B.** Controller/đường vào phù hợp. **C.** Thêm replicas tự sửa được.
2. Backend Service port 8080 chuyển tới app 9090. Ingress tham chiếu cổng nào? **A.** 9090 luôn luôn. **B.** Host port trên Mac. **C.** Service port 8080 hoặc tên port tương ứng.

## 4. Thực hành và bằng chứng

1. Vẽ đường Mac → cổng mapped → frontend/controller → Service → Pod dựa trên inventory thật. Kiểm cổng đã map; nếu thiếu, dừng để học viên xem xét thay đổi lab, không tự xóa/tạo cluster mất dữ liệu.
2. Học viên tạo Ingress HTTP cho app test, gọi với Host đúng qua endpoint local; so với Host không match và với Service nội bộ.
3. Mentor kiểm route/class/backend và response marker, không chỉ HTTP 200 của trang mặc định controller. Chưa cần DNS OS hay TLS; dùng cách chỉ định Host/resolve tường minh và ghi giới hạn.

**Đạt khi:** giải thích đủ từng chặng và có đúng response ứng dụng với rule match, đối chứng không match. Không ghi “public/LAN truy cập được” nếu chỉ thử trên Mac.

## 5. Cần DevOps và giới hạn lab

- Cần controller/class, frontend/LB, host/ports được phép, route/firewall; yêu cầu riêng DNS/TLS ở bài sau. Cloud LB controller hoặc on-prem LB là implementation cần xác nhận, không tên resource tự thực thi.
- Debug từ client: kết nối frontend → controller/rule → Service/endpoints → app; không sửa app port khi lỗi thực ra host port chưa được publish.

**Nguồn:** [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/), [K3s networking services](https://docs.k3s.io/networking/networking-services), [k3d exposing services](https://k3d.io/stable/usage/exposing_services/).
