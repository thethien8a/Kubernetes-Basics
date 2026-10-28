# Bài 17 — NetworkPolicy và egress

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](16-dns-tls.md) · [Tiếp](18-vong-doi-du-lieu.md)

**Đầu vào:** DNS và kết nối Pod/Service. **Đầu ra:** yêu cầu luồng mạng cụ thể và chứng minh policy được thực thi.

## 1. Khối kiến thức

- NetworkPolicy cần networking solution/controller có enforcement. API nhận policy không chứng minh traffic bị lọc; K3s có controller tích hợp nhưng vẫn phải kiểm trạng thái và hành vi thực tế.
- Ingress/egress isolation được áp dụng theo Pod selector và từng chiều. Các allow rules cộng hợp; không phải rule cuối thắng. Một kết nối cần được cả egress phía nguồn và ingress phía đích cho phép khi hai phía bị isolate.
- Cùng một peer entry có namespaceSelector và podSelector là AND; hai entries riêng là OR. Đây là khác biệt YAML có thể mở rộng quyền ngoài ý định.
- Default-deny egress có thể chặn DNS. Chuẩn NetworkPolicy kiểm L3/L4, không thay TLS, HTTP authorization hoặc allow-list tên miền tùy ý; việc hỗ trợ FQDN thuộc giải pháp khác cần hỏi nền tảng.

## 2. Đọc cấu hình

| NetworkPolicy field | Ý nghĩa/cạm bẫy |
|---|---|
| `metadata.namespace`, `spec.podSelector` | Nhóm Pod bị áp policy; `{}` chọn mọi Pod trong namespace đó. |
| `spec.policyTypes` | Nêu rõ Ingress/Egress, không để nhầm chiều cần kiểm. |
| `spec.ingress[].from[]`, `spec.egress[].to[]` | Đọc phạm vi podSelector/namespaceSelector/ipBlock và AND/OR. |
| Rule `ports[].port`, `protocol` | Cho đúng giao thức/cổng ứng dụng; DNS thường cần xem cả UDP/TCP theo cấu hình thực tế. |

## 3. Kiểm tra hiểu trước lab

1. Có policy trong API nhưng networking không enforce. Đã có cách ly chưa? **A.** Có vì object tồn tại. **B.** Chưa. **C.** Có nếu namespace khác nhau.
2. Một peer chứa cả namespaceSelector và podSelector khác hai peer entries riêng thế nào? **A.** AND so với OR. **B.** Không khác. **C.** Chỉ thay thứ tự thực thi.

## 4. Thực hành và bằng chứng

1. Tạo namespace test riêng, server và hai client có nhãn khác nhau; kiểm baseline kết nối mới đều thành công. Inventory các policy áp vào nhóm để tránh allow-all khác làm sai thí nghiệm.
2. Học viên đặt deny ingress rồi allow chỉ client hợp lệ; kiểm client A được phép và B bị chặn, luôn dùng kết nối mới có timeout. Không dùng phiên TCP mở trước khi đổi policy để kết luận.
3. Ở khối egress riêng, thử deny và mở DNS/đích cần thiết; quan sát resolve và HTTP riêng biệt. Không áp deny lên `kube-system` hoặc namespace đang chứa workload khóa khác.

**Đạt khi:** ma trận source → destination/port có kết quả allow/deny đúng, gồm đối chứng. Nếu không thấy enforcement thì giữ bài chưa đạt, điều tra nền tảng thay vì giả ghi đã bảo mật.

## 5. Cần DevOps và giới hạn lab

- Cần implementation hỗ trợ, baseline policies, DNS path, egress/proxy/NAT nếu dùng external API và quy trình mở luồng. Đưa rõ nguồn/đích/port/protocol/mục đích, không yêu cầu “allow all”.
- Chính sách L3/L4 trong lab không chứng minh IAM S3, quyền SQL hoặc xác thực API. Hành vi NAT/hostNetwork có thể khác implementation; bài chỉ dùng Pod network thông thường.

**Nguồn:** [Network policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/), [K3s network policy controller](https://docs.k3s.io/networking/networking-services).
