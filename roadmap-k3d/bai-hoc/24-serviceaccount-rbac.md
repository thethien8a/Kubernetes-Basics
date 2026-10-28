# Bài 24 — ServiceAccount và RBAC

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](23-config-secret.md) · [Tiếp](25-image-registry.md)

**Đầu vào:** namespaces, API/resource và Secret safety. **Đầu ra:** yêu cầu quyền theo chức năng, không xin cluster-admin để ứng dụng chạy được.

## 1. Khối kiến thức

- Identity của người dùng kubectl khác ServiceAccount của Pod. Xác thực trả lời “ai”, authorization trả lời “được làm gì”; ServiceAccount không tự có quyền chỉ vì đã tồn tại.
- Role định nghĩa resource/verb trong namespace; RoleBinding gắn role với subject. ClusterRole có thể được tham chiếu bằng RoleBinding để cấp quyền namespaced trong phạm vi binding, không tự biến thành quyền toàn cluster.
- Kubernetes API permission khác quyền PostgreSQL/S3 và khác NetworkPolicy. Có TCP connectivity không nghĩa API cho phép tạo Pod; đọc được Pod không nghĩa được đọc logs nếu thiếu subresource tương ứng.
- Quyền tạo workload có thể cho phép sử dụng Secret/ServiceAccount trong namespace theo admission policy. Chỉ cấm API `get secrets` không đủ để suy người tạo Pod không tiếp cận được dữ liệu nhạy cảm.

## 2. Đọc cấu hình

| Field | Ý nghĩa/cạm bẫy |
|---|---|
| PodSpec `serviceAccountName`, `automountServiceAccountToken` | Chọn runtime identity và nhu cầu API token, không dùng token nếu app không cần. |
| Role `rules[].apiGroups`, `resources`, `verbs` | Core API group dùng chuỗi rỗng; `get`, `list`, `watch`, `create` khác nhau. |
| RoleBinding `subjects[]`, `roleRef` | Đúng kind/name/namespace của subject; tên giống nhau ở namespace khác không cùng identity. |
| RBAC resource `pods/log` | Subresource riêng, không suy `get pods` luôn kèm đọc logs/exec. |

## 3. Kiểm tra hiểu trước lab

1. Pod có ServiceAccount mới nhưng chưa có role binding phù hợp. Có tự tạo Executor Pods được không? **A.** Không thể suy là được. **B.** Luôn được. **C.** Được vì chạy trong cluster.
2. RoleBinding trong namespace A tham chiếu ClusterRole cho quyền đọc Pods. Nó tự cấp đọc Pods namespace B không? **A.** Có. **B.** Không chỉ nhờ binding đó. **C.** Chỉ khi tên Pod giống nhau.

## 4. Thực hành và bằng chứng

1. Học viên tạo ServiceAccount và Role/RoleBinding hẹp cho đọc một ConfigMap test hoặc danh sách ConfigMaps trong namespace lab; giải thích khác biệt phạm vi hai lựa chọn trước khi chọn.
2. Kiểm allow đúng resource/namespace và deny với create/delete hoặc namespace khác. Dùng identity thật của Pod hoặc impersonation chỉ trong sandbox bằng identity có quyền impersonate; không thử bằng admin rồi suy app có quyền.
3. Thu HTTP status/`auth can-i` và kết quả không nhạy cảm; token chỉ được client nạp nội bộ, không echo/ghi file review. Khôi phục/xóa đúng role test khi học viên kết thúc.

**Đạt khi:** ma trận identity × action × namespace có cả allow và deny; viết được yêu cầu quyền tối thiểu cùng lý do nghiệp vụ.

## 5. Cần DevOps và giới hạn lab

- Cần identity, namespace, quy tắc RBAC/admission và quy trình xin quyền; không yêu cầu quyền sửa Role/ClusterRole cho chính ứng dụng chỉ để nó tự cấp quyền.
- Admin kubeconfig do k3d cấp là tiện ích lab. Ma trận RBAC nhỏ không là audit bảo mật toàn cluster, và không kiểm quyền ứng dụng ở S3/SQL.

**Nguồn:** [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/), [ServiceAccounts](https://kubernetes.io/docs/concepts/security/service-accounts/).
