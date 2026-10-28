# Bài 03 — Đọc manifest và lần theo tham chiếu

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](02-lab-k3d-va-context.md) · [Tiếp](04-pod-va-controller.md)

**Đầu vào:** đúng context lab mới. **Đầu ra:** đọc manifest theo cấu trúc và tham chiếu, không xem YAML như danh sách lệnh chạy từ trên xuống.

## 1. Khối kiến thức

- `apiVersion`/`kind` chọn API và loại object; `metadata` nhận diện; `spec` là mong muốn; `status` do hệ thống phản ánh. Nhiều resource trong một file vẫn có vòng reconcile riêng, không phải transaction đồng bộ.
- Namespace chia phạm vi tên cho resource namespaced; không tự tạo cách ly network hoặc quota. Node/PV/StorageClass là ví dụ resource cấp cluster.
- Label là metadata để chọn nhóm. Selector của controller/Service cần match labels của Pod, không phải chỉ nhãn bên ngoài Deployment.
- UID nhận diện một object cụ thể. Cùng tên sau xóa/tạo không có nghĩa cùng Pod; khi review phải đối chiếu owner và thời gian.

## 2. Đọc cấu hình

| Resource/field | Quan hệ cần lần theo |
|---|---|
| Deployment `metadata.name`, `metadata.namespace` | Tên controller và phạm vi; không tự đặt tên mọi Pod giống controller. |
| Deployment `spec.selector.matchLabels` → `spec.template.metadata.labels` | Chọn Pod thuộc nhóm; selector Deployment không phải field nên đổi tùy tiện sau tạo. |
| Deployment `spec.template.spec.containers[].image` | Image ứng dụng ở Pod template, không phải image của controller. |
| Service `spec.selector` | Chọn Pod cùng namespace; không tham chiếu tên Deployment. |
| Pod `metadata.ownerReferences`, `status.conditions` | Lần lên controller và xem trạng thái thực tế. |

Ví dụ rút gọn để đọc, chưa phải manifest triển khai: `spec.template.metadata.labels: {app: demo}` là nhãn Pod; `metadata.labels: {team: data}` là nhãn Deployment. Hai vị trí không thay thế nhau.

## 3. Kiểm tra hiểu trước lab

1. Đổi label bên ngoài Deployment thành `app=api`, giữ Pod template `app=demo`. Service chọn `app=api` có tự chọn các Pod đó không? **A.** Có. **B.** Không. **C.** Chỉ trên một node.
2. Pod mới cùng tên nhưng UID khác nghĩa là gì? **A.** Object mới. **B.** Chỉ đổi IP. **C.** Chắc chắn container restart trong Pod cũ.

## 4. Thực hành và bằng chứng

1. Đọc scaffold Deployment và Service nhỏ; đánh dấu tên, scope, selector, template và desired state. Chưa cần gọi Service, đường mạng sẽ kiểm ở Bài 14.
2. Học viên tự tạo trong namespace mới sau checkpoint; mentor kiểm API nhận đúng object, labels/ownerReferences và trạng thái Pod.
3. So manifest với live object, giải thích một giá trị mặc định/status được hệ thống bổ sung. Không sao chép toàn bộ live YAML kèm managedFields/status thành cấu hình nguồn.

**Đạt khi:** lần đúng Deployment → ReplicaSet → Pod và Service selector → Pod labels; chỉ được vị trí một field nếu muốn đổi image/replicas. Không đánh giá bằng khả năng gõ YAML từ đầu.

## 5. Cần DevOps và giới hạn lab

- Cần namespace, quy ước labels và quyền tạo/đọc loại resource đã chọn. `Forbidden` khác lỗi schema, khác resource chưa Ready.
- Namespace local chưa chứng minh multi-tenancy; network isolation, quota và RBAC sẽ học riêng. Khi không đủ quyền xem object, gửi tên/scope và lỗi đã lọc thay vì xin mọi quyền.

**Nguồn:** [Objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/), [labels/selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/).
