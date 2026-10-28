# Bài 25 — Image, registry và nhiều node

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](24-serviceaccount-rbac.md) · [Tiếp](26-quota-admission.md)

**Đầu vào:** node placement và container lifecycle. **Đầu ra:** phân biệt build thành công trên Mac với image chạy được ở mọi node cần dùng.

## 1. Khối kiến thức

- Docker engine trên host và container runtime trong K3s nodes có image stores riêng. Image có trên host không tự có trong từng node; k3d image import là bước phân phối cho lab.
- Image reference gồm registry/repository/tag hoặc digest. Tag có thể thay đổi; pin digest làm nội dung xác định hơn, vẫn cần kiểm manifest/architecture phù hợp ARM64.
- `IfNotPresent`, `Always`, `Never` điều khiển cách tìm/pull image; `Always` không đồng nghĩa tải lại mọi byte nếu layer/digest đã cache. ImagePullBackOff là trạng thái backoff, phải đọc Events để tìm nguyên nhân.
- Registry connectivity/auth/trust, image platform và lỗi process là các tầng khác nhau. Đổi tag không sửa được thiếu quyền registry hoặc runtime config sai.

## 2. Đọc cấu hình

| Field/config | Ý nghĩa/lựa chọn |
|---|---|
| Container `image` | Đọc đủ registry/path/tag/digest, tránh nhầm Docker Hub mặc định với registry nội bộ. |
| Container `imagePullPolicy` | `Never` dùng cho thí nghiệm image đã import, không khuyến nghị mặc định cho production. |
| PodSpec `imagePullSecrets[].name` | Ref Secret pull cùng namespace; khác credential ứng dụng gọi S3/DB. |
| K3d `registries` / image import | Nối/phân phối image tới node runtime; không phải field Deployment. |

## 3. Kiểm tra hiểu trước lab

1. Image mới build trên Mac, Pod với `Never` trên agent chưa import image. Điều gì có thể xảy ra? **A.** Tự đọc image host. **B.** Lỗi image chưa có trong node runtime. **C.** Tự đổi thành Always.
2. Image pull thành công nhưng ứng dụng crash vì thiếu config. Nên cấp thêm registry quyền ghi không? **A.** Có. **B.** Chỉ nếu chạy ARM64. **C.** Không, điều tra startup/config đúng tầng.

## 4. Thực hành và bằng chứng

1. Dùng image test có tag riêng và marker đã biết, kiểm ARM64. Học viên build/import theo CLI version đã đối chiếu, ban đầu chưa phân phối đủ hai agent.
2. Với `Never`, chạy Pod vào agent chưa có image và quan sát lỗi; không xóa cache image hệ thống để tạo lỗi. Học viên import tới các nodes cần dùng, chạy lại và kiểm marker/digest/placement.
3. Đọc phương án registry: ít thao tác phân phối thủ công nhưng cần endpoint/CA/auth/network. Không bắt dựng registry production hoặc thử credential sai trên registry thật.

**Đạt khi:** giải thích failure/recovery theo image store từng node và nêu quy trình phân phối ngoài lab. Không coi emulation chạy được là image native đã được kiểm.

## 5. Cần DevOps và giới hạn lab

- Cần registry/mirror, pull identity/Secret mechanism, network/CA, image architecture được hỗ trợ và policy tag/digest/scanning.
- K3d import chỉ là tiện ích local; cluster thực tế thường pull registry. Không dùng hostname `localhost` của Mac làm registry endpoint cho node mà không kiểm đường mạng và cách resolver của node hiểu nó.

**Nguồn:** [Images](https://kubernetes.io/docs/concepts/containers/images/), [k3d image import](https://k3d.io/stable/usage/commands/k3d_image_import/), [k3d registries](https://k3d.io/stable/usage/registries/).
