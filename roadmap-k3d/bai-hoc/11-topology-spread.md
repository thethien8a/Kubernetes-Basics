# Bài 11 — Phân bố replicas và miền lỗi

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](10-taints-tolerations.md) · [Tiếp](12-disruptions.md)

**Đầu vào:** requests, affinity, taints. **Đầu ra:** kiểm chứng phân bố replicas thay vì suy từ `replicas: 3`.

## 1. Khối kiến thức

- Replicas tăng số Pod, không tự định nghĩa yêu cầu nằm ở các miền lỗi độc lập. Miền lỗi có thể là node, rack hoặc zone theo labels nền tảng.
- Pod anti-affinity tránh đặt cùng miền với các Pod match selector; topology spread giới hạn/ưu tiên độ lệch số Pod giữa các miền đủ điều kiện.
- `DoNotSchedule` là ràng buộc cứng theo skew; `ScheduleAnyway` ưu tiên phân bố nhưng không bảo đảm độ lệch nhỏ trong mọi điều kiện. Requests/taints/affinity vẫn giới hạn các node có thể chọn.
- Labels zone giả trên hai k3d agents chỉ mô phỏng quyết định scheduler; cả hai vẫn có thể mất cùng một lúc khi host hỏng.

## 2. Đọc cấu hình

| PodSpec field | Ý nghĩa/lựa chọn |
|---|---|
| `topologySpreadConstraints[].topologyKey` | Dùng `kubernetes.io/hostname` để phân biệt nodes thật của lab. |
| `topologySpreadConstraints[].labelSelector` | Nhóm Pod được đếm; selector sai làm phép phân bố không phản ánh nhóm mong muốn. |
| `topologySpreadConstraints[].maxSkew`, `whenUnsatisfiable` | Chọn `1` và `DoNotSchedule` cho ca hai agents đều hợp lệ, đủ chỗ. |
| `affinity.podAntiAffinity` | So sánh required/preferred; required một Pod mỗi node có thể làm replica thứ ba Pending. |

## 3. Kiểm tra hiểu trước lab

1. Có ba replicas Running nhưng đều ở một node. Điều gì đã được chứng minh? **A.** Chịu mất một node. **B.** Chỉ có ba Pod đang chạy, chưa chứng minh phân bố. **C.** Đã có ba vùng độc lập.
2. Chỉ hai agents hợp lệ, hard anti-affinity cho tối đa một Pod của nhóm trên mỗi node, yêu cầu ba replicas. Dự đoán? **A.** Pod thứ ba có thể Pending. **B.** Tự tạo node. **C.** Tự bỏ anti-affinity.

## 4. Thực hành và bằng chứng

1. Học viên giới hạn nhóm test vào hai agents bằng placement đã học; tạo ba replicas nhỏ, kiểm hai agents đều hợp lệ và đủ request budget.
2. Dùng spread `maxSkew=1`, kiểm phân bố 2/1 sau ổn định; không khẳng định agent nào bắt buộc có hai Pod. Ghi node labels, selector, requests và Pod placement.
3. Ở cấu hình riêng, dùng hard anti-affinity theo hostname cho ba replicas trên hai agents; xác nhận ca không đủ miền qua Events rồi khôi phục. Không chạy lẫn hai rule để khó tìm nguyên nhân.

**Đạt khi:** có phân bố 2/1 và đối chứng Pending với hard anti-affinity, giải thích trade-off availability/capacity.

## 5. Cần DevOps và giới hạn lab

- Cần topology labels đáng tin cậy, số miền có capacity, quy tắc pool và giới hạn mở rộng. DE nêu mức gián đoạn chấp nhận được thay vì chỉ đòi “ba replicas”.
- Ngoài lab phải biết các node có chung rack/zone/disk hay không. Không ghi nhận HA vật lý từ một host k3d.

**Nguồn:** [Topology spread](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/), [Pod affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/).
