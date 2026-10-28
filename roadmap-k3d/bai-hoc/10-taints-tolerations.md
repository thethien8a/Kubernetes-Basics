# Bài 10 — Taints và tolerations

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](09-node-affinity.md) · [Tiếp](11-topology-spread.md)

**Đầu vào:** hard/soft placement. **Đầu ra:** phân biệt điều kiện được vào node với điều kiện phải chọn node.

## 1. Khối kiến thức

- Taint nằm trên node, đẩy lùi Pod không tolerate nó. Toleration nằm trên Pod, cho phép vượt rào cản tương ứng nhưng không kéo Pod tới node đó.
- `NoSchedule` ngăn scheduling mới nếu không tolerate, không tự đuổi Pod đang chạy. `PreferNoSchedule` là tránh nếu có thể. `NoExecute` có thể tác động cả Pod đang chạy theo toleration.
- Toleration không bỏ qua thiếu tài nguyên, node affinity hoặc volume topology. Muốn workload vào pool chuyên dụng thường phải hiểu cả taint/toleration lẫn selector/affinity.

## 2. Đọc cấu hình

| Field | Ý nghĩa/lựa chọn |
|---|---|
| Node `spec.taints[]` | Key/value/effect; dùng một taint test trên một agent, không chỉnh taint hệ thống. |
| PodSpec `tolerations[].key`, `operator`, `value`, `effect` | `Equal` match giá trị; `Exists` rộng hơn, không khai toleration toàn bộ chỉ để hết Pending. |
| `tolerations[].tolerationSeconds` | Thời gian tolerate `NoExecute` khi có khai báo; không áp dụng như timer cho mọi effect. |
| PodSpec `nodeSelector` | Kết hợp khi yêu cầu đúng pool, không thay thế toleration. |

## 3. Kiểm tra hiểu trước lab

1. Pod tolerate taint của node GPU nhưng không có yêu cầu placement khác. Nó bắt buộc vào node GPU không? **A.** Có. **B.** Không. **C.** Tự được cấp GPU.
2. Thêm `NoSchedule` lên agent đang có Pod không tolerate có tự xóa Pod đó không? **A.** Có ngay. **B.** Chỉ khi Pod có Service. **C.** Không chỉ vì effect này.

## 4. Thực hành và bằng chứng

1. Học viên lưu taints ban đầu, thêm một taint lab `NoSchedule` trên agent đã chọn; không động server hoặc taints do node conditions tạo.
2. Workload bị buộc chọn agent đó nhưng chưa tolerate sẽ Pending; thu Events. Học viên thêm toleration hẹp, giữ request/selector như cũ rồi xác nhận schedule được.
3. Gỡ đúng taint test và khôi phục cấu hình bài. `NoExecute` chỉ đọc tình huống trong bài này; không cần evict system Pods để chứng minh.

**Đạt khi:** phân biệt hai cơ chế và chỉ ra điều kiện còn thiếu từ Events; không thêm wildcard tolerations làm bản sửa.

## 5. Cần DevOps và giới hạn lab

- Cần hợp đồng pool: labels, taints, allowed tolerations và capacity. DevOps xác nhận workload có được dùng pool đó không.
- Dedicated node pool không chỉ là một taint: còn placement, quyền, quota và cách workload khác được cấu hình. Lab không chứng minh cô lập bảo mật hoặc tài nguyên tuyệt đối.

**Nguồn:** [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/).
