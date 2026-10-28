# Bài 02 — Lab k3d độc lập và truy cập an toàn

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](01-kien-truc-va-trach-nhiem.md) · [Tiếp](03-doc-manifest.md)

**Đầu vào:** Bài 01 và [quyết định lab](../lab-va-hop-dong-nen-tang.md). **Đầu ra:** tự tạo lab riêng sau khi hiểu config; không nhầm cluster cũ với cluster mới.

## 1. Khối kiến thức

- Một context nối cluster endpoint, user/identity và namespace mặc định. Docker context và kubectl context thuộc hai công cụ khác nhau; tên `orbstack` ở Docker không có nghĩa lệnh kubectl đang nhắm k3d.
- K3d tạo server/agent containers và có thể tạo serverlb. Serverlb là proxy/đường vào của k3d, không phải resource Service `type: LoadBalancer` và không phải Ingress controller.
- Ba node container vẫn dùng chung host. K3s server có thể nhận workload; không giả định “server chỉ chạy control plane”.
- Kubeconfig có thể mang credential có quyền mạnh. Tách file cấu hình truy cập khỏi Git; kiểm endpoint/context mà không in các trường credential.

## 2. Đọc cấu hình

| Cấu hình k3d, không phải Kubernetes manifest | Ý nghĩa/lựa chọn |
|---|---|
| `apiVersion: k3d.io/v1alpha5`, `kind: Simple` | Định dạng config theo CLI hỗ trợ; không `kubectl apply` file này. |
| `metadata.name`, `servers`, `agents` | Dự kiến `de-k3d`, 1, 2; tên được kiểm không trùng trước khi tạo. |
| `image` | Pin K3s image sau kiểm version/ARM64; không sao chép default mà bỏ kiểm tương thích. |
| `kubeAPI.hostIP`, `kubeAPI.hostPort` | Bind API vào loopback và chọn cổng trống; không mở public để tiện lab. |
| `ports[].port`, `ports[].nodeFilters` | Map cổng host vào node/proxy được chọn; chưa tự có HTTP route/DNS. |
| `options.kubeconfig.updateDefaultKubeconfig`, `switchCurrentContext` | Đọc cách tránh ghi/chuyển mặc định; chọn kubeconfig riêng cho lab. |

Mentor xác nhận schema và flags của k3d được cài trước khi đưa config hoàn chỉnh. Labels/placement sẽ học sâu ở Bài 09, không tự thêm nhiều tối ưu ban đầu.

## 3. Kiểm tra hiểu trước lab

1. Docker đang dùng context OrbStack, còn kubectl trỏ cluster cũ. Lệnh tạo Pod đi đâu? **A.** Cluster cũ trong kubectl context. **B.** Tự tìm cluster k3d mới nhất. **C.** Tạo ở cả hai.
2. Ba node cùng báo nhiều CPU có nghĩa Mac được nhân ba CPU không? **A.** Có. **B.** Chỉ với K3s. **C.** Không, còn giới hạn chung của host/runtime.

## 4. Thực hành và bằng chứng

1. Mentor kiểm chỉ đọc tool/runtime, tài nguyên và port; học viên đọc config và chốt tên/version/budget. Nếu thiếu capacity, chọn giảm workload hoặc thống nhất cách giải phóng, không tự dọn khóa cũ.
2. Học viên tự tạo đúng cluster mới, lưu kubeconfig riêng và dùng context tường minh. Quan sát ba nodes và inventory system components; ghi image/version, context và namespace đã chọn.
3. Kiểm cluster mới có ba node Ready, API truy cập được; context mặc định cũ không bị thay ngoài ý muốn. Chưa kết luận DNS/storage/network policy đạt chỉ từ Ready.

**Đạt khi:** học viên chỉ đúng đường kubectl → API mới, phân biệt ba loại “load balancer/controller” và có inventory runtime. Không tạo workload DE ở bài này.

## 5. Cần DevOps và giới hạn lab

- Ngoài lab, cần endpoint API, identity/login, namespace, quyền và đường mạng; thường DE không tự tạo control plane.
- K3d làm thay việc tạo nodes và wiring Docker. Khi lỗi: kiểm runtime → node containers → API endpoint → context/identity; không sửa cluster `orbstack` để chữa cluster k3d.

**Nguồn:** [k3d config](https://k3d.io/stable/usage/configfile/), [kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/).
