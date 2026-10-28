# Lab và hợp đồng nền tảng

[Mục lục](README.md) · [Cách học](dinh-huong-va-cach-hoc.md) · [Tiến độ](tien-do-hoc-tap.md)

## Topology đề xuất, chưa triển khai

Máy theo hồ sơ: Mac mini M4, 24 GB RAM, 10 CPU cores. Dùng Docker engine của OrbStack cho k3d; không sử dụng cluster Kubernetes tích hợp `orbstack` làm cluster khóa mới.

```diagram
┌────────────────────────────────────────────────────────────┐
│ Mac / OrbStack Docker engine — chung tài nguyên vật lý     │
│                                                            │
│ k3d cluster: de-k3d                                        │
│ 1 server (control plane) + 2 agents (workload lab)         │
│ k3d serverlb / port mapping: đường vào local               │
└────────────────────────────────────────────────────────────┘
```

K3s server cũng có thể chạy workload; tên vai trò không tự loại nó khỏi scheduling. Khi cần thí nghiệm đúng hai agent, học viên dùng labels/placement đã giải thích, kiểm Pod thực sự ở đâu. Không đổi scheduling của system Pods chỉ để làm sơ đồ đẹp.

Chọn 1 server + 2 agents vì đủ so sánh placement, cross-node networking và node-local storage mà không học control-plane HA. Không tạo ba control plane hoặc cài distributed storage chỉ để tăng độ “production”. Các node vẫn chia sẻ host/runtime/disk; dừng một node container không tương đương mọi dạng lỗi máy vật lý hay network partition.

## Quyết định cần xác nhận trước Bài 02

| Hạng mục | Cách chốt |
|---|---|
| Runtime/version | Kiểm Docker engine, k3d, kubectl và Helm; chọn K3s image/version hỗ trợ ARM64 và client skew phù hợp. Không tự nâng cấp tool hoặc cluster cũ. |
| Định danh | Dự kiến tên `de-k3d`, context `k3d-de-k3d`, namespace `de-lab`/`de-client`; kiểm không trùng trước khi tạo. Namespace từng bài có thể tách thêm nếu cần. |
| Kubeconfig | Ưu tiên kubeconfig riêng, giữ ngoài Git và tránh tự đổi current context của cluster `orbstack`. Chỉ truyền path/context tường minh sau khi đọc cấu hình. |
| CPU/RAM/disk | Đo mức dùng host/runtime và tài nguyên còn lại, rồi đặt budget cho lab. Không cộng allocatable của ba node container để suy ra host có ba lần CPU/RAM. Requests không phải số đo sử dụng. |
| Ports | API bind loopback; cổng HTTP/HTTPS host được chọn sau khi kiểm xung đột và chỉ mở local theo nhu cầu. Port mapping không tự có DNS hay TLS. |
| Add-ons | Inventory thực tế CoreDNS, networking, NetworkPolicy enforcement, Traefik, ServiceLB, local-path và Metrics API; không suy tất cả chạy đúng chỉ vì K3s thường có sẵn. |
| Phục hồi | Cluster mới là sandbox, dữ liệu giả và resource có nhãn bài. Chốt tài nguyên được dừng/xóa, cách khôi phục và dữ liệu phải giữ trước mỗi thí nghiệm. |

Kiểm tra chỉ đọc ngày 2026-10-28 thấy k3d `v5.8.3`, default K3s do CLI báo `v1.33.6-k3s1`, Docker context `orbstack`; các executable kubectl/Helm có sẵn. Đây không phải pin phiên bản cho khóa, không chứng minh Docker đang chạy hoặc cluster mới đã tồn tại. Không tái sử dụng version chart/image của khóa cũ mà bỏ kiểm tra tương thích.

## Đối chiếu lab với hệ thống được DevOps cung cấp

| Khả năng | Lab dự kiến | Ngoài lab cần cung cấp/xác nhận | Kiểm tra/debug |
|---|---|---|---|
| Cluster/access | k3d tạo K3s nodes, kubeconfig local | Endpoint API, identity, namespace, RBAC và quy trình cấp quyền | Context/server, `auth can-i`, lỗi xác thực/phân quyền; không dump credential. |
| Pod networking | K3s networking trên mạng Docker | CNI/networking, đường giữa nodes, DNS nội bộ | Node/Pod placement → listener → kết nối Pod IP → Service/DNS. |
| NetworkPolicy | K3s có controller policy nếu không bị tắt | Enforcement thực tế, baseline policies, quy trình allow-list | Test kết nối mới từ client hợp lệ và client bị cấm; resource tồn tại chưa đủ. |
| Đường vào | k3d port mapping/serverlb + Traefik/ServiceLB tùy config | Ingress controller/class hoặc Gateway, LB/frontend, firewall/route | Host port → frontend/controller → rule → Service → endpoints → app. |
| DNS/TLS | Tên test và chứng chỉ lab có phạm vi rõ | DNS record, certificate issuer/trust, renewal owner | Resolver phía client, Host/SNI, hostname certificate; không dùng bỏ verify làm nghiệm thu. |
| Storage | local-path cấp storage gắn với node theo cấu hình | StorageClass, provisioner/CSI/backend, topology, modes, expansion và reclaim | PVC/Events → class/PV/source/affinity → Pod mount → dữ liệu. |
| Images | Image import hoặc registry được nối với k3d | Registry/mirror, ARM64/AMD64, pull permissions, trust CA | Reference/digest → node runtime → pull Events → container startup. |
| Quan sát | Status/Events/logs; metrics nếu có | Quyền đọc, metrics/log backend, retention, nơi truy cập logs sau Pod deletion | Đúng UID/lần chạy/thời gian; phân biệt không có dữ liệu quan sát với không có lỗi. |

Cloud managed có thể cung cấp một số controller/CSI/LB; on-prem có thể cần DevOps cài và vận hành. Cả hai vẫn cần biết class, topology, quota, route và quyền thực tế, không chỉ biết tên nhà cung cấp.

## Hợp đồng nền tảng: đầu ra nhỏ sau mỗi bài

“Hợp đồng” ở đây là danh sách yêu cầu có thể kiểm tra, không phải mẫu pháp lý. Mỗi bài chỉ bổ sung phần liên quan; chưa biết thì ghi `Cần xác nhận`, không tự bịa giá trị.

| Mục | Nội dung cần ghi |
|---|---|
| Dịch vụ/phạm vi | Namespace, chủ sở hữu, môi trường và dữ liệu nào được phép dùng. |
| Hành vi cần có | Chạy liên tục hay batch, concurrency, cách truy cập, thời gian gián đoạn chấp nhận được. |
| Tài nguyên | Requests/limits có lý do, quota, placement và image/architecture. |
| Kết nối | Nguồn → đích, protocol/port, DNS, TLS, egress; credential cấp bằng cách nào, không ghi giá trị. |
| Dữ liệu | Dung lượng, access mode, topology, reclaim, backup, RPO/RTO và người chịu trách nhiệm. |
| Quyền/API | ServiceAccount hoặc identity, resource/verb, namespace và chức năng cần quyền đó. |
| Nghiệm thu | Bằng chứng thành công, đối chứng thất bại, cách quan sát và giới hạn chưa kiểm chứng. |
| Ranh giới xử lý | DE có thể tự sửa gì, thay đổi nào phải qua DevOps, thông tin cần gửi khi báo lỗi. |

RPO là lượng dữ liệu có thể mất tính theo thời gian; RTO là thời gian mục tiêu để khôi phục dịch vụ. Thống nhất mục tiêu trước, không suy từ “đã có PVC”.

## Ranh giới an toàn

- Lập kế hoạch không cấp phép triển khai. Trong các buổi học, học viên tự thao tác; mentor không tạo/apply/patch/delete/restart workload thay học viên.
- Kiểm context/namespace/resource trước mọi lệnh. Dùng định danh tường minh; không dùng wildcard xóa Docker volumes, prune toàn hệ thống hoặc xóa namespace của cluster `orbstack`.
- Đổi labels/taints, drain hoặc dừng agent là thao tác giả lập vai trò DevOps trên sandbox mới, không phải quyền DE mặc định. Không dừng server ở bài node failure.
- Lab storage chỉ dùng dữ liệu giả; không xóa PVC để chữa lỗi, không force-delete StatefulSet Pod đang mất liên lạc và không tháo finalizer để vượt cơ chế bảo vệ.
- Không cố làm hết RAM/disk host. Test Pending bằng yêu cầu không phù hợp và lỗi có deadline; không flood workload. Dừng thí nghiệm nếu ảnh hưởng hệ thống ngoài phạm vi.
- Kubeconfig, credentials, private keys và file render chứa Secret không được đưa vào Git, chat hoặc output review. Không yêu cầu học viên gửi output nhạy cảm.
- Không thay trust store macOS hoặc public service ra LAN/Internet chỉ để hoàn thành bài TLS/Ingress.

## Nguồn nền tảng

Đối chiếu ngày 2026-10-28; luôn chọn tài liệu tương ứng phiên bản khi bắt đầu lab:

- [k3d overview](https://k3d.io/stable/) và [config file](https://k3d.io/stable/usage/configfile/).
- [K3s networking services](https://docs.k3s.io/networking/networking-services) và [storage](https://docs.k3s.io/storage).
- [Kubernetes version skew policy](https://kubernetes.io/releases/version-skew-policy/).
