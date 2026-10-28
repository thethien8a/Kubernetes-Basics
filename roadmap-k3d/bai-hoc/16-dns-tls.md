# Bài 16 — DNS bên ngoài và TLS

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](15-ingress-va-loadbalancer.md) · [Tiếp](17-networkpolicy.md)

**Đầu vào:** route HTTP đã kiểm chứng. **Đầu ra:** tách đúng DNS, routing, certificate và application authentication.

## 1. Khối kiến thức

- DNS client ngoài cluster phải phân giải hostname tới frontend reachable từ client đó. Ingress `host` là điều kiện route, không tự tạo DNS record.
- TLS xác thực tên server bằng certificate/trust chain và bảo vệ kết nối; không thay việc đăng nhập/phân quyền ứng dụng. SNI trong TLS và Host HTTP liên quan hostname nhưng ở các bước khác nhau.
- Certificate cần đúng hostname, còn hạn và có CA được client tin. Cấp/gia hạn thủ công ít thành phần nhưng có trách nhiệm vận hành; cert-manager tự động hóa theo issuer nếu nền tảng đã cung cấp, không tự có vì khai Ingress TLS.
- Chọn certificate test cho bài; client dùng CA file riêng theo request. Không cài CA lab vào trust store toàn máy hoặc dùng `-k` làm bằng chứng cấu hình đúng.

## 2. Đọc cấu hình

| Field/config | Quan hệ cần kiểm |
|---|---|
| Ingress `spec.rules[].host`, `spec.tls[].hosts` | Cần khớp hostname định dùng và certificate. |
| Ingress `spec.tls[].secretName` | Ref TLS Secret cùng namespace; không tự sinh certificate. |
| Secret type `kubernetes.io/tls`, key names `tls.crt`, `tls.key` | Hợp đồng dữ liệu TLS; private key phải giữ kín, mentor không dump Secret. |
| DNS record/đích frontend, CA trust của client | Thuộc hạ tầng/client, không là field PodSpec. |

## 3. Kiểm tra hiểu trước lab

1. HTTPS chỉ chạy khi bỏ xác minh certificate. Có thể nghiệm thu TLS đúng chưa? **A.** Chưa. **B.** Rồi vì đã mã hóa. **C.** Chỉ cần thêm replicas.
2. Ingress host đã khai nhưng máy client không resolve được. Khối nào cần kiểm? **A.** Readiness trước tiên. **B.** DNS phía client/record và endpoint. **C.** Job retry count.

## 4. Thực hành và bằng chứng

1. Chọn hostname `.test` cho lab, frontend local và HTTPS mapping đã kiểm. Giải thích cách resolve override trong client test khác với cấu hình DNS thật; không đụng DNS toàn máy khi chưa cần.
2. Học viên chuẩn bị certificate/key lab ngoài Git bằng quy trình đã giải thích, tạo TLS Secret và route. Mentor chỉ xem refs/key names, certificate public metadata khi cần; không xem private key.
3. Gọi đúng hostname với CA tin cậy tường minh, kiểm response app; đối chứng sai hostname hoặc CA không tin cậy phải thất bại xác minh. Không ghi đã kiểm DNS OS nếu dùng resolve override.

**Đạt khi:** route HTTPS được xác minh danh tính và phân biệt bằng chứng DNS với TLS. Ghi ngày hết hạn và ai chịu trách nhiệm renewal, không tự triển khai cert-manager.

## 5. Cần DevOps và giới hạn lab

- Cần hostname/record, frontend, certificate issuer/Secret mechanism, trust chain, renewal owner và auth/access policy cho UI.
- HTTPS local với CA test không chứng minh public trust, LAN reachability hay SSO. Trong cloud/on-prem, kiểm từng lớp thay vì giả định DNS tự cấp LB hoặc cert tự được gia hạn.

**Nguồn:** [Ingress TLS](https://kubernetes.io/docs/concepts/services-networking/ingress/), [TLS Secrets](https://kubernetes.io/docs/concepts/configuration/secret/).
