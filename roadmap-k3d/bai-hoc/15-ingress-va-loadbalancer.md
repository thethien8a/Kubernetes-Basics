# Bài 15 — Đường vào cluster: Ingress và Gateway API

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](14-service-dns.md) · [Tiếp](16-dns-tls.md)

**Đầu vào:** Service/backend hoạt động nội bộ. **Đầu ra:** yêu cầu đúng đường vào (Ingress hoặc Gateway API) thay vì chỉ thêm `type: LoadBalancer`.

## 1. Khối kiến thức

- **NodePort vs LoadBalancer:** NodePort mở cổng Service trên địa chỉ node theo implementation/config; LoadBalancer yêu cầu hạ tầng/controller (như Cloud LB, MetalLB, K3s ServiceLB) cung cấp IP/frontend. Không loại nào tự bảo đảm có public IP hoặc firewall cho phép.
- **Ingress truyền thống:** Là một resource gom chung cấu hình HTTP(S) routing, Host/path matching và TLS. Controller (như NGINX Ingress, Traefik) đọc rule để cấu hình reverse proxy; phụ thuộc nặng vào annotation riêng của từng vendor và khó phân chia quyền giữa DevOps và Dev/DE.
- **Kubernetes Gateway API (Chuẩn thế hệ mới):** Thay thế Ingress bằng mô hình hướng vai trò (Role-oriented) chia tách trách nhiệm rõ ràng:
  - `GatewayClass`: Do DevOps/Hạ tầng định nghĩa bộ điều khiển (Istio, Envoy Gateway, Cilium,...).
  - `Gateway`: Do Cluster Admin/DevOps quản lý điểm lắng nghe cổng (port 80/443), địa chỉ IP LoadBalancer và chứng chỉ TLS.
  - `HTTPRoute` / `GRPCRoute` / `TCPRoute`: Do Application Developer / Data Engineer viết để định tuyến traffic từ Gateway vào Service backend cụ thể (hỗ trợ cross-namespace, URL rewrite, request header modifier).
- **Phương pháp lần vết mạng ngược (Network Reverse Tracing):** Khi một URL/domain truy cập được từ trình duyệt mà `kubectl get ingress -A` không thấy rule:
  1. *Lấy IP đích:* Dùng `nslookup <domain>` hoặc `dig` để tìm IP máy chủ tiếp nhận traffic.
  2. *Tìm Service tiếp nhận:* Dùng `kubectl get svc -A -o wide | grep <IP>` để tìm Service (thường là type `LoadBalancer`) đang giữ IP này.
  3. *Nhận diện Controller qua Selector/Tên:* Nếu thấy nhãn `gateway.networking.k8s.io/...`, cụm đang dùng Gateway API; nếu thấy `ingress-nginx`, cụm dùng Ingress thông thường.
  4. *Truy vấn tài nguyên định tuyến tương ứng:* Gọi `kubectl get gateway,httproute -A` thay vì chỉ tìm `Ingress`.
- **K3d serverlb vs ServiceLB vs Ingress Controller:** K3d serverlb là proxy container bên ngoài k3d mapping port host vào node; ServiceLB quản lý cổng trên node; Ingress/Gateway Controller định tuyến ở tầng ứng dụng (L7).

## 2. Đọc cấu hình

| Field/config | Ý nghĩa/cạm bẫy |
|---|---|
| Service `spec.type`, `ports[].nodePort` | Chọn kiểu expose; NodePort không tự map cổng Docker ra Mac. |
| Ingress `spec.ingressClassName`, `spec.rules[].host` | Chọn controller và điều kiện route L7; Host không match có thể trả default 404. |
| Gateway `spec.gatewayClassName` | Chọn bộ điều khiển Gateway API (ví dụ `istio`, `envoy`). |
| Gateway `spec.listeners[].allowedRoutes` | Khai báo route từ namespace nào được phép gắn vào Gateway (`from: All` hoặc `Same`). |
| HTTPRoute `spec.parentRefs` | Chỉ định Gateway cụ thể mà route này đăng ký nhận traffic. |
| HTTPRoute `spec.hostnames` | Tên miền định tuyến (ví dụ `ddlh-sep.amigo.lab`). |
| HTTPRoute `spec.rules[].matches` | Điều kiện match theo path (`PathPrefix`, `Exact`), method (`GET`, `POST`), headers. |
| HTTPRoute `spec.rules[].backendRefs` | Service đích nhận traffic (port và weight). |
| HTTPRoute `spec.rules[].filters` | Các bộ lọc chuyển đổi như `URLRewrite` hoặc `RequestHeaderModifier`. |

## 3. Kiểm tra hiểu trước lab

1. Tạo Ingress rule nhưng không có controller xử lý class. Điều gì còn thiếu? **A.** Chỉ đổi Pod name. **B.** Controller/đường vào phù hợp. **C.** Thêm replicas tự sửa được.
2. Backend Service port 8080 chuyển tới app 9090. Ingress/HTTPRoute tham chiếu cổng nào? **A.** 9090 luôn luôn. **B.** Host port trên Mac. **C.** Service port 8080 hoặc tên port tương ứng.
3. Khi truy cập được domain `https://app.example.com` nhưng `kubectl get ingress -A` không thấy rule, bước đầu tiên nên làm gì? **A.** Xóa cluster làm lại. **B.** Tra DNS lấy IP đích và tìm Service LoadBalancer tương ứng. **C.** Khẳng định DNS bị lỗi.
4. Trong kiến trúc Gateway API, Data Engineer muốn deploy dịch vụ của mình và định tuyến domain vào cần tạo resource nào? **A.** `GatewayClass`. **B.** `Gateway`. **C.** `HTTPRoute` trỏ vào `Gateway` có sẵn của hạ tầng.

## 4. Thực hành và bằng chứng

1. **Phân tích mô hình đường vào:** Vẽ đường traffic từ Client → External IP/LB → Controller (Ingress hoặc Gateway) → Route rule → Service → Pod.
2. **Thực hành Ingress cục bộ (k3d):** Tạo Ingress HTTP cho app test, gọi với Host đúng qua endpoint local; so với Host không match và với Service nội bộ.
3. **Thực hành truy vết thực tế (Case study cụm dùng Gateway API):**
   - Dùng lệnh `kubectl get gateway,httproute -A` để phát hiện các route đang hoạt động trong cluster.
   - Kiểm tra một HTTPRoute cụ thể (như `dv-sep-nginx-service-http`), đối chiếu `parentRefs` (Gateway) và `backendRefs` (Service backend).
   - Kiểm chứng tính năng filter nếu có (như `URLRewrite` hoặc `RequestHeaderModifier`).

**Đạt khi:** Giải thích đủ từng chặng vào của traffic; phân biệt được Ingress và Gateway API; biết cách dùng phương pháp Reverse Tracing để tìm ra rule định tuyến khi Ingress bị ẩn hoặc thay thế bằng Gateway API.

## 5. Cần DevOps và giới hạn lab

- **Phân công trách nhiệm:** Với Ingress, DE thường phải tự viết toàn bộ hoặc xin DevOps gắn annotation phức tạp. Với Gateway API, DevOps cung cấp `Gateway` chung (đã cấu hình sẵn TLS, LB IP, WAF); DE chỉ cần viết và apply `HTTPRoute` trong namespace của mình.
- **Giới hạn lab:** Local k3d mặc định cài sẵn Traefik Ingress Controller; Gateway API yêu cầu cài thêm CRDs (`gateway.networking.k8s.io`) và controller hỗ trợ (như Istio/Envoy) nếu muốn thực hành tạo mới từ đầu.

**Nguồn:** [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/), [Kubernetes Gateway API](https://gateway-api.sigs.k8s.io/), [K3s networking services](https://docs.k3s.io/networking/networking-services).
