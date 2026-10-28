# Bài 12 — Bảo trì node, PDB và node failure

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](11-topology-spread.md) · [Tiếp](13-pod-network.md)

**Đầu vào:** probes, replicas và placement. **Đầu ra:** biết DevOps cần điều kiện gì để bảo trì và điều gì không được PDB bảo vệ.

## 1. Khối kiến thức

- Cordon làm node không nhận scheduling thông thường mới; không tự đuổi Pod hiện có. Drain dùng eviction để đưa workload ra khỏi node, có các ngoại lệ/điều kiện cần đọc trước khi thực hiện.
- PDB giới hạn gián đoạn qua Eviction API theo nhóm Pod. Không ngăn máy hỏng, không chặn trực tiếp xóa Pod/Deployment, không điều khiển rollout của Deployment như `maxUnavailable`.
- Node mất liên lạc có giai đoạn phát hiện, cập nhật conditions/taints và tolerations trước khi workload được xử lý. Không hứa Pod chuyển node ngay lập tức hoặc một thời gian cố định cho mọi cluster.
- Pod mới còn cần capacity và placement hợp lệ. PDB không tạo thêm node; stateful workload còn phụ thuộc storage và cơ chế tránh hai writer, học sau.

## 2. Đọc cấu hình

| Field/dữ liệu | Ý nghĩa/cạm bẫy |
|---|---|
| PDB `spec.selector`, `minAvailable` hoặc `maxUnavailable` | Chọn đúng Pod group; chọn một trong hai ngân sách, không đặt cả hai. |
| PDB `status.currentHealthy`, `desiredHealthy`, `disruptionsAllowed` | Quan sát readiness và khả năng eviction ở thời điểm đó. |
| Node `spec.unschedulable`, `status.conditions` | Cordon là chủ đích khác với mất Ready/Unknown. |
| PodSpec `tolerations`, Pod deletion timestamp/owner | Đọc timeline, không chỉ tên Pod cuối cùng. |

## 3. Kiểm tra hiểu trước lab

1. PDB yêu cầu cả hai replicas healthy. Một node hỏng vật lý có bị PDB chặn không? **A.** Có. **B.** Không. **C.** Chỉ nếu là cloud.
2. Drain bị chặn vì PDB, Pod thay thế không đủ chỗ. Bước phù hợp? **A.** Luôn force-delete. **B.** Tắt toàn bộ probes. **C.** Kiểm capacity/placement và thỏa thuận ngân sách gián đoạn.

## 4. Thực hành và bằng chứng

1. Chỉ dùng app stateless giả, hai replicas được quan sát trên hai agents, placement cho phép phục hồi trên agent còn lại. Kiểm node không mang dữ liệu cần giữ; chuẩn bị thao tác khôi phục và timeout quan sát.
2. Học viên đóng vai DevOps thử drain một agent với PDB `minAvailable=2`; ghi eviction bị chặn. Sau review, học viên điều chỉnh ngân sách cho phép một Pod gián đoạn, thực hiện bảo trì và uncordon; không dùng force/bypass PDB làm đáp án.
3. Ở lượt tách biệt, sau khi đã phục hồi baseline, học viên dừng đúng một agent container rồi bật lại. Quan sát timeline node/Pod/PDB; không stop server, không force-delete stateful Pod và không sửa tolerations chỉ để làm test nhanh.

**Đạt khi:** phân biệt bằng evidence trường hợp maintenance bị chặn/được phép với node unavailable; nêu rõ độ trễ và điều kiện phục hồi quan sát được. Không bắt chứng minh zero downtime ở bài này.

## 5. Cần DevOps và giới hạn lab

- DE cung cấp health criteria, disruption budget, thời gian shutdown và đặc tính retry; DevOps cung cấp maintenance policy, capacity dự phòng và hành vi node failure của nền tảng.
- Dừng container node là mô phỏng có giới hạn, không bao phủ network partition/disk loss. Không suy PDB bảo vệ dữ liệu hoặc mọi thao tác xóa.

**Nguồn:** [Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/), [Safe drain](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/).
