# Bài 14 — Service, EndpointSlice và DNS

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](13-pod-network.md) · [Tiếp](15-ingress-va-loadbalancer.md)

**Đầu vào:** Pod connectivity và readiness. **Đầu ra:** debug riêng tên, Service ports và backend, không đổi mọi tầng cùng lúc.

## 1. Khối kiến thức

- Service kiểu ClusterIP cung cấp endpoint ổn định trong vòng đời Service; backend Pod có thể thay đổi. Service selector và EndpointSlices mô tả nhóm đích; Service không phải container proxy do bạn phải viết.
- `port` là cổng Service, `targetPort` là cổng backend; named targetPort được resolve từ tên port của Pod. Các số có thể khác nhau.
- DNS Service thông thường phân giải tới ClusterIP; headless Service khác, sẽ dùng ở StatefulSet. Tên ngắn phụ thuộc namespace/search domains; đọc cluster domain thực tế, không hard-code host DNS của OrbStack.
- DNS trả lời được chưa chứng minh Service có backend Ready. Readiness thất bại thường làm backend không được dùng cho kết nối mới; không tự xóa Service hoặc bảo đảm mọi kết nối cũ bị ngắt.

## 2. Đọc cấu hình

| Field | Quan hệ cần kiểm |
|---|---|
| Service `metadata.namespace`, `spec.selector` | Match Pod labels cùng namespace. |
| Service `spec.ports[].port`, `targetPort`, `protocol` | Cổng client gọi khác cổng app listen; protocol phải đúng. |
| EndpointSlice `endpoints[].addresses`, `conditions.ready`, `ports` | Đối chiếu backend thực tế, không chỉ nhìn Service tồn tại. |
| PodSpec `dnsPolicy` và DNS config runtime | Cluster DNS/search path; không sửa CoreDNS để chữa typo tên Service. |

## 3. Kiểm tra hiểu trước lab

1. DNS resolve Service thành công nhưng EndpointSlice không có backend phù hợp. DNS đã chứng minh ứng dụng hoạt động chưa? **A.** Chưa. **B.** Rồi. **C.** Chỉ khi từ Mac.
2. Client ở namespace khác dùng tên ngắn của Service và bị lỗi. Nên kiểm gì trước? **A.** Tăng RAM. **B.** Xóa Service. **C.** Tên/namespace/search domain và tên có qualification phù hợp.

## 4. Thực hành và bằng chứng

1. Chạy Service với client cùng namespace và client namespace khác; kiểm DNS trả lời và HTTP marker. Dùng tên đã qualify theo namespace ở ca khác namespace.
2. Học viên làm sai selector trong bản test rồi khôi phục; chứng minh DNS vẫn có thể trả lời trong khi backend không còn đúng. Ca targetPort sai làm ở lượt riêng nếu cần.
3. Học viên thay một backend Pod, giữ Service; ghi Service UID/IP, backend UID/IP và gọi lại từ client. Tái dùng readiness scenario để quan sát EndpointSlice thay đổi.

**Đạt khi:** nối được DNS → Service → EndpointSlice → listener và có một ca lỗi/recovery đúng tầng. Không dùng Pod IP cũ làm cấu hình client lâu dài.

## 5. Cần DevOps và giới hạn lab

- Cần DNS cluster, Service dataplane, cluster domain và network policy cho luồng cần gọi. DE cung cấp namespace/name/protocol/port, không chỉ nói “mở network”.
- Tên Service trong Pod không mặc định resolve được trên Mac/LAN. Host DNS tiện dụng của OrbStack không thuộc hợp đồng Kubernetes chuẩn.

**Nguồn:** [Service](https://kubernetes.io/docs/concepts/services-networking/service/), [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/).
