# Bài 09 — Node labels, selector và affinity

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](08-resources.md) · [Tiếp](10-taints-tolerations.md)

**Đầu vào:** requests và labels. **Đầu ra:** biết yêu cầu node pool thế nào và vì sao có CPU rảnh mà Pod vẫn Pending.

## 1. Khối kiến thức

- Node labels mô tả thuộc tính/nhóm theo quy ước nền tảng. Label `pool=batch` không tự lắp thêm RAM, GPU hoặc đảm bảo máy thuộc loại nào.
- `nodeSelector` và required node affinity là ràng buộc cứng; preferred node affinity là ưu tiên trong các node hợp lệ, không là bảo đảm vị trí.
- `IgnoredDuringExecution` nghĩa thay label không tự di chuyển Pod đang chạy. Placement được đánh giá khi scheduling, khác với cơ chế eviction.
- Khi có nhiều điều kiện, phải đọc quan hệ AND/OR: các biểu thức trong cùng term là AND, các `nodeSelectorTerms` là OR; `nodeSelector` và node affinity cùng khai báo thì đều phải đáp ứng.

## 2. Đọc cấu hình

| Field | Ý nghĩa/lựa chọn |
|---|---|
| Node `metadata.labels` | Học viên đóng vai DevOps gán nhãn test chỉ lên agent lab, ghi lại để hoàn tác. |
| PodSpec `nodeSelector` | Ví dụ `lab-pool: batch`; nếu không node nào match thì chưa schedule được. |
| `affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms` | Điều kiện cứng với `matchExpressions` và operator/values. |
| `affinity.nodeAffinity.preferredDuringSchedulingIgnoredDuringExecution` | Điểm ưu tiên/weight, vẫn chịu requests, taints và mọi ràng buộc cứng. |

## 3. Kiểm tra hiểu trước lab

1. Preferred affinity thích agent 0, agent 0 hết chỗ nhưng agent 1 hợp lệ. Pod có thể chạy agent 1 không? **A.** Có. **B.** Không bao giờ. **C.** Chỉ sau khi xóa affinity.
2. Required affinity match lúc Pod được đặt; sau đó node mất label, dùng `IgnoredDuringExecution`. Điều gì được bảo đảm? **A.** Pod tự migrate. **B.** Node bị xóa. **C.** Thay label không tự evict Pod theo rule này.

## 4. Thực hành và bằng chứng

1. Học viên ghi baseline labels, gán nhãn hai agent và đặt workload vào agent phù hợp bằng selector; kiểm `spec.nodeName` thực tế.
2. Tạo biến thể selector không có node match; đọc Events rồi sửa tối thiểu để phục hồi. Không tăng CPU/RAM để chữa lỗi label.
3. So required/preferred bằng cấu hình và một tình huống node ưu tiên không hợp lệ; chỉ kết luận điều kiện đã quan sát, không hứa scheduler luôn chọn một node cụ thể khi có nhiều lựa chọn.

**Đạt khi:** giải thích được ca Pending và chỉ ra bộ labels cần thỏa thuận với DevOps. Không dùng `nodeName` để bỏ qua scheduler như lời giải mặc định.

## 5. Cần DevOps và giới hạn lab

- Cần tên/ý nghĩa labels ổn định, node pool phù hợp workload và quy trình thay đổi; DE không nên tự đổi labels node chung.
- Label giả trong lab giúp học scheduling, không chứng minh hardware/storage/network thật. Quyền sửa node labels có ý nghĩa bảo mật, không tự cấp cho application ServiceAccount.

**Nguồn:** [Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/).
