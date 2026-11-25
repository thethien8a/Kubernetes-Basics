# Tổng kết Bài 24 — ServiceAccount và RBAC

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/24-serviceaccount-rbac.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/25-image-registry.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-20** giờ Việt Nam (`Asia/Ho_Chi_Minh`); đạt review và thu hồi quyền test.
- **Challenge:** Một ETL cần tự gọi Kubernetes API để đọc đúng một ConfigMap đã biết tên. Cấp `get` hẹp, kiểm cả allow/deny bằng cùng ServiceAccount, rồi thu hồi mà không xóa cấu hình.
- **Phạm vi:** context `k3d-de-k3d`, đích chính `de-lab`, đối chứng `de-client`; client `/usr/local/bin/kubectl` v1.33.9, server v1.33.6+k3s1 ở preflight. Chỉ dùng API `v1` và `rbac.authorization.k8s.io/v1`, không dùng image hay chart. Mentor chuẩn bị manifest và kiểm live chỉ đọc; các thao tác tạo/xóa là phần của học viên.

## 1. Danh tính, quyền và cấu hình

| Field / cơ chế | Điều cần nhớ |
|---|---|
| PodSpec `serviceAccountName` | Danh tính được chọn từ ServiceAccount cùng namespace. Bỏ field thì dùng `default` của namespace, không thừa hưởng quyền kubeconfig của người tạo Pod. |
| PodSpec `automountServiceAccountToken` | `false` tắt tự gắn token, không bỏ ServiceAccount hay thu hồi quyền RBAC. Kubelet vẫn có thể nạp env/file theo ConfigMap/Secret refs; đó không phải app tự gọi Kubernetes API. |
| Role `rules[].apiGroups`, `resources`, `resourceNames`, `verbs` | `apiGroups: [""]` là group lõi, `configmaps` là tên resource API. `get` đúng một tên đủ cho yêu cầu này. Bỏ `resourceNames` mở `get` cho mọi tên trong namespace, không cho `list` hay `watch`. `list` thông thường có thể trả cả nội dung object, không chỉ tên. |
| RoleBinding `subjects`, `roleRef`, `metadata.namespace` | Subject `de-lab/lesson24-reader` nhận quyền trong Role `lesson24-read-settings`. Namespace của subject xác định **ai**, namespace của binding xác định **ở đâu**; hai namespace có thể khác. Role không tự cấp quyền; RBAC cộng các grant, binding hẹp không phủ định grant rộng ở chỗ khác. |
| ClusterRole và scope | Có thể tái sử dụng một ClusterRole bằng RoleBinding ở từng namespace cần dùng. Tham chiếu ClusterRole không tự cấp quyền toàn cluster. Với rule cho resource namespaced, ClusterRoleBinding cấp quyền tương ứng trên mọi namespace. |
| Subresource | `get pods` (đọc object/trạng thái theo tên) khác `get pods/log`. Mở rộng namespace cho `pods` không thêm quyền vào `pods/log`. |

Xác thực trả lời **ai**; authorization xét **danh tính, verb, resource và đích**. Pod spec còn phải qua admission. Kết nối mạng thành công không cấp quyền API hay IAM/SQL. Không suy người tạo được Pod không thể tiếp cận Secret chỉ vì `get secrets` trực tiếp bị từ chối: platform còn phải kiểm quyền dùng Secret và ServiceAccount của Pod bằng chính sách phù hợp.

## 2. Scaffold và bằng chứng

- [01-baseline.yaml](../thuc-hanh/24-serviceaccount-rbac/01-baseline.yaml): tạo ServiceAccount `lesson24-reader`, ConfigMap `lesson24-etl-settings` với giá trị giả `batch-size: "240"` và Role `lesson24-read-settings`; **không** bind.
- [02-rolebinding.yaml](../thuc-hanh/24-serviceaccount-rbac/02-rolebinding.yaml): chỉ thêm `lesson24-bind-reader` trong `de-lab` để cấp rule `get` trên ConfigMap đã nêu. Hai file có nhãn `lesson: "24"`, đạt strict client dry-run; đó không phải bằng chứng đã tạo live.
- `auth can-i` chỉ hỏi quyết định quyền, không thực hiện verb đang hỏi. Kubeconfig admin của lab được phép dùng `--as=system:serviceaccount:de-lab:lesson24-reader`; quyết định kiểm cho ServiceAccount, không suy từ quyền admin. Phép precheck trước khi tạo resource trả `no` cho tên dự kiến, không dùng nó làm bằng chứng resource tồn tại. Baseline chính được đọc lại sau khi ba resource live đã tồn tại.

| Mốc mentor tự kiểm ngày 20/11 | Quan sát và kết luận |
|---|---|
| **23:23:32 — Role đã có, chưa bind** | ServiceAccount, ConfigMap và Role có metadata tạo 23:22:21 và khớp scaffold; ConfigMap `240`. Không thấy binding test; `can-i get` đúng tên trả `no`/exit 1. |
| **23:28:12 — Đã bind** | Ba resource cũ giữ UID. Binding có metadata tạo 23:27:01, đúng `roleRef`/`subjects`. Cùng câu hỏi trả `yes`/exit 0; `get` thật bằng cùng danh tính trả `240`/exit 0. Ma trận bên dưới kiểm cả yêu cầu ngoài phạm vi. |
| **23:39:20 — Trước thu hồi** | Role/RoleBinding giữ UID; trong `de-lab` chỉ binding test trỏ tới Role test; câu hỏi đúng tên vẫn `yes`. Giao xóa đúng hai tên, đối chiếu UID trước, không xóa ServiceAccount hoặc ConfigMap. |
| **23:44:57 — Chốt sau thu hồi** | Role và RoleBinding test không còn. ServiceAccount và ConfigMap cùng UID, ConfigMap admin vẫn đọc ra `240`; `can-i` của ServiceAccount trả `no`/exit 1, yêu cầu `get` thật cùng danh tính trả `Forbidden`/exit 1, không có giá trị. |

Ma trận `auth can-i` lúc đã bind, cùng danh tính `system:serviceaccount:de-lab:lesson24-reader`:

| Namespace đích | Verb và resource | Quan sát |
|---|---|---|
| `de-lab` | `get configmaps/lesson24-etl-settings` | `yes` |
| `de-lab` | `get configmaps/lesson24-other-settings` | `no` |
| `de-lab` | `list configmaps` | `no` |
| `de-lab` | `create configmaps` | `no` |
| `de-lab` | `delete configmaps/lesson24-etl-settings` | `no` |
| `de-client` | `get configmaps/lesson24-etl-settings` | `no` |

Chỉ thay tên ở hàng 2 và namespace đích ở hàng cuối để đối chiếu với hàng 1. Phép hỏi không cần object đối chứng tồn tại và không tạo/xóa ConfigMap thật. Học viên báo xong bước baseline và yêu cầu tiếp tục ở các bước sau; các snapshot là kết quả mentor tự kiểm, không chứng minh thứ tự từng lệnh hay học viên đã nhìn mọi output.

## 3. Tái quan sát trạng thái đã chốt (chỉ đọc)

Trên Mac chạy lab, xác nhận context `k3d-de-k3d` trỏ API `https://127.0.0.1:6445` và `de-lab` Active. Không tạo lại Role/RoleBinding chỉ để tái hiện mốc `yes`.

```bash
lab24() {
  /usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
    --context=k3d-de-k3d --namespace=de-lab --request-timeout=5s "$@"
}
reader=system:serviceaccount:de-lab:lesson24-reader
lab24 get rolebinding/lesson24-bind-reader role/lesson24-read-settings --ignore-not-found -o name
lab24 get configmap/lesson24-etl-settings -o 'jsonpath={.data.batch-size}{"\n"}'
lab24 --as="$reader" auth can-i get configmaps/lesson24-etl-settings
lab24 --as="$reader" get configmap/lesson24-etl-settings -o 'jsonpath={.data.batch-size}{"\n"}'
```

Ở snapshot chốt: lệnh đầu không in tên nào, lệnh đọc bằng admin in `240`; hai lệnh bằng ServiceAccount lần lượt in `no` và báo `Forbidden`. `Forbidden` nêu đúng user, verb `get`, resource `configmaps` và namespace `de-lab`: quyền mất đi nhưng dữ liệu vẫn còn.

- **Giữ:** ServiceAccount UID `91f0308a-5a08-4564-b839-475447669c65`, ConfigMap UID `311cb03c-324d-47a0-b0cc-fed2b66976b2` với `batch-size: "240"`, hai scaffold.
- **Đã thu hồi:** không còn Role UID `b4472f55-fa07-474d-8610-738f28bb3767` và RoleBinding UID `018dd3c5-f495-4ffd-b8f7-ae90e83dea6d`. Không chạy lại lệnh xóa với UID cũ.

## 4. Review và yêu cầu DevOps

- **Đạt 10/10 lựa chọn:** danh tính/token `1B, 2C`; Role/RoleBinding `1B, 2A`; ClusterRole/subresource `1C, 2B`; API/admission/quyền dữ liệu `1B, 2C`; `can-i` chọn `A`; review cuối chọn `B`. Không có câu sai hoặc còn chờ.
- **Yêu cầu quyền tối thiểu từ tình huống review:** “Cho ServiceAccount `jobs/schema-checker` quyền `get` đúng ConfigMap `schema-contract` trong `data-config` để job xác minh schema đầu vào. Bind ở `data-config`; không cấp `list` hay quyền ghi chỉ để đọc theo tên. Nghiệm thu bằng danh tính của job, không dùng kết quả của admin thay thế.” Nếu workload chỉ cần giá trị được kubelet đưa vào env/file, trước hết xem có cần quyền API trực tiếp không.
- **Lab ↔ ngoài lab:** k3d tạo kubeconfig có quyền quản trị trong sandbox. Với cụm tự quản, platform cung cấp endpoint/trust, xác thực người dùng qua cơ chế đã chọn, namespaces và RBAC/admission. Với managed Kubernetes, đăng nhập hoặc liên kết IAM có thể do nhà cung cấp hỗ trợ, nhưng không tự thay thế RBAC cho workload. Khi debug, xác định danh tính phục vụ request và kiểm đúng verb/resource/name/namespace; chỉ impersonate khi được cấp quyền phù hợp, nếu không kiểm bằng danh tính thật. Lỗi từ chối impersonation không phải kết quả kiểm quyền của ServiceAccount.
- **Giới hạn:** Lab chứng minh authorization và một yêu cầu đọc API thật qua impersonation, không thử app nạp token, tạo Pod, cấp quyền cluster-wide, đọc log, admission runtime, NetworkPolicy, S3/SQL hay Spark/Airflow thật. Không tạo/đọc token hoặc Secret, không dùng kubeconfig admin của lab làm mô hình quyền DE ngoài lab.

[Kubernetes v1.33 — RBAC](https://v1-33.docs.kubernetes.io/docs/reference/access-authn-authz/rbac/)
