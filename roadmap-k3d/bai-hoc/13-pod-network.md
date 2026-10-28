# Bài 13 — Mạng Pod qua nhiều node

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](12-disruptions.md) · [Tiếp](14-service-dns.md)

**Đầu vào:** placement và node/Pod identity. **Đầu ra:** lần theo đường kết nối giữa hai Pod ở hai nodes, trước khi thêm Service/DNS.

## 1. Khối kiến thức

- Containers trong một Pod chia sẻ network namespace nên dùng loopback của Pod. `localhost` trong Pod khác không chỉ tới ứng dụng của Pod trước hoặc Mac.
- Ứng dụng phải listen trên địa chỉ/cổng phù hợp. `0.0.0.0` là wildcard bind IPv4, không phải địa chỉ đích quảng bá cho client; `containerPort` không tự làm process listen.
- Mạng Pod qua nodes do networking plugin và cấu hình node network thực thi. CNI là giao diện tích hợp mạng container, không phải một loại Service.
- Kết nối thành công từ Mac không chứng minh client Pod có cùng DNS/route/policy; debug phải từ đúng phía client. Không cần học iptables/eBPF internals để nhận diện tầng lỗi.

## 2. Đọc cấu hình

| Field/config | Ý nghĩa/cạm bẫy |
|---|---|
| App args/env về bind address/port | Thuộc ứng dụng; cần kiểm listener thực tế, không suy từ YAML mô tả port. |
| Container `ports[].containerPort` | Metadata cổng container, không tự publish host port. |
| Pod `status.podIP`, `status.hostIP`, `spec.nodeName` | Ba danh tính khác nhau; không lấy hostIP làm Pod IP. |
| PodSpec `hostNetwork` | Giữ false/default; không bật để lách lỗi networking của bài. |

## 3. Kiểm tra hiểu trước lab

1. Client Pod ở agent 1 gọi `localhost:8080`, server nằm Pod ở agent 0. Địa chỉ đó trỏ đâu? **A.** Server Pod. **B.** Loopback của client Pod. **C.** Mac host.
2. Đã khai `containerPort: 8080`, process chỉ listen 9090. Cổng nào thực sự có listener? **A.** Cả hai. **B.** 8080. **C.** 9090, trừ khi app có listener khác.

## 4. Thực hành và bằng chứng

1. Đặt HTTP server test và client trên hai agents khác nhau bằng placement đã học; ghi node/IP để chứng minh cross-node.
2. Học viên gọi Pod IP/cổng thật, quan sát HTTP marker đúng. So với cổng sai bằng request có timeout ngắn; không chỉ dùng ping làm bằng chứng HTTP.
3. Đọc ca bind loopback và giải thích tại sao gọi bên trong server Pod khác với gọi từ client Pod. Nếu thử biến thể, dùng workload riêng, không sửa CNI hoặc route hệ thống.

**Đạt khi:** bằng chứng request đi từ client sang Pod khác node và phân biệt sai listener/port với giả thuyết hạ tầng. Không kết luận “CNI hỏng” chỉ từ một timeout.

## 5. Cần DevOps và giới hạn lab

- Cần CNI/networking đã hoạt động, dải Pod/Service không xung đột, đường giữa nodes và quyền dùng công cụ debug phù hợp. Khi báo lỗi, gửi source/destination/port/node và mốc thời gian.
- K3s/k3d làm sẵn wiring; ngoài lab phải có node networking, route/firewall và cấu hình plugin tương ứng. Lab không đo hiệu năng mạng vật lý hoặc mô phỏng mọi đường cloud.

**Nguồn:** [Cluster networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/), [Pods](https://kubernetes.io/docs/concepts/workloads/pods/).
