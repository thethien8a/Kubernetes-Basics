# Bài 26 — Quota, LimitRange và admission

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](25-image-registry.md) · [Tiếp](27-helm.md)

**Đầu vào:** resources, RBAC, namespace. **Đầu ra:** phân biệt chưa được phép tạo workload với đã được nhận nhưng chưa schedule/chạy được.

## 1. Khối kiến thức

- ResourceQuota giới hạn tổng tài nguyên/số object trong namespace. LimitRange đặt defaults và giới hạn cho từng object/container theo cấu hình; không đồng nghĩa node có capacity đó.
- API request có thể bị từ chối bởi authorization hoặc admission. Deployment đã tồn tại nhưng controller không tạo được Pod vì quota: cần xem Events/conditions của controller, không tìm logs Pod chưa tồn tại.
- Pod Security Admission có các mode enforce/warn/audit và policy level; warn không chặn như enforce. Policy version phải phù hợp cluster, không áp namespace labels toàn hệ thống để làm bài.
- SecurityContext mô tả cách process chạy, ví dụ non-root/capabilities/seccomp. Được admission nhận chưa chứng minh image tương thích UID/filesystem hoặc ứng dụng thực thi thành công.

## 2. Đọc cấu hình

| Field | Ý nghĩa/cạm bẫy |
|---|---|
| ResourceQuota `spec.hard`, `status.used` | Tổng quota theo keys như requests.cpu/memory hoặc pods; không đọc thành RAM đang sử dụng. |
| LimitRange `spec.limits[].default`, `defaultRequest`, `min`, `max` | Defaults cho Pod mới và giới hạn; kiểm live spec sau admission. |
| Namespace labels `pod-security.kubernetes.io/enforce`, `enforce-version` | Áp policy cho namespace test; pin minor phù hợp, không sửa namespace khác. |
| Container `securityContext.runAsNonRoot`, `allowPrivilegeEscalation`, `capabilities` | Một phần cấu hình bảo mật; Restricted còn yêu cầu khác như seccomp theo version. |

## 3. Kiểm tra hiểu trước lab

1. Deployment tồn tại, ReplicaSet báo quota exceeded, chưa có Pod mới. Tầng cần điều tra? **A.** App logs của Pod mới. **B.** Admission/quota và controller Events. **C.** PVC luôn luôn.
2. Namespace chỉ đặt Pod Security mode warn. Warning có đồng nghĩa request bị chặn không? **A.** Có. **B.** Chỉ khi image lớn. **C.** Không chỉ vì warn.

## 4. Thực hành và bằng chứng

1. Học viên tạo namespace test riêng, quota và LimitRange nhỏ đã giải thích; tạo workload hợp lệ, kiểm default resources được thêm và quota used.
2. Tạo trường hợp vượt quota bằng số lượng/request khai báo, không tải làm cạn host. Thu rejection/Events, điều chỉnh yêu cầu hoặc giảm workload test rồi xác nhận tạo được Pod.
3. Ở lượt tách biệt, đọc chuẩn security rồi áp policy cho namespace disposable; dùng server dry-run với Pod vi phạm đã biết và bản sửa đúng toàn bộ policy. Không cần chạy privileged Pod hoặc xin miễn trừ toàn namespace để đạt.

**Đạt khi:** phân biệt quota rejection, security rejection và scheduling Pending, có một ca quota recovery và đối chứng admission. Ghi rõ dry-run chưa chứng minh runtime của securityContext.

## 5. Cần DevOps và giới hạn lab

- Cần quota/defaults, security policy/version, image UID/filesystem requirements và quy trình xin ngoại lệ có phạm vi. DE cung cấp request/limit/concurrency có căn cứ.
- Tạo policy trong lab là vai platform giả lập. Không tắt webhook/admission/PSA của cluster dùng chung khi ứng dụng bị từ chối; trước hết đọc lỗi và sửa đúng hợp đồng.

**Nguồn:** [ResourceQuota](https://kubernetes.io/docs/concepts/policy/resource-quotas/), [LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/), [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/).
