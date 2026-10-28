# Bài 19 — PVC, StorageClass và provisioning

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](18-vong-doi-du-lieu.md) · [Tiếp](20-storage-multi-node.md)

**Đầu vào:** volume lifecycle và placement. **Đầu ra:** biết yêu cầu storage class nào và tìm dependency thiếu khi claim Pending.

## 1. Khối kiến thức

- PVC là yêu cầu namespaced; PV là object cấp cluster mô tả storage đã cấp; StorageClass chọn provisioner và chính sách. Byte nằm ở backend, không nằm trong metadata PVC/PV.
- Dynamic provisioning cần controller/provisioner hoạt động và backend truy cập được. Static provisioning là phương án khác do người vận hành chuẩn bị PV trước; không bắt DE tự cấp PV trong mọi hệ thống.
- CSI là giao diện tích hợp storage, không phải tên một disk hay bảo đảm HA. K3s local-path là một implementation khác với cloud CSI/distributed storage; cần đọc source/topology PV thực tế.
- `WaitForFirstConsumer` trì hoãn binding/provisioning để xét vị trí workload; claim Pending trước consumer có thể là hành vi đúng. `Immediate` cấp/bind sớm hơn, cần cân nhắc topology.

## 2. Đọc cấu hình

| Field | Ý nghĩa/cạm bẫy |
|---|---|
| PVC `spec.storageClassName` | Chọn class có thật; bỏ field có thể dùng default class, còn chuỗi rỗng là chủ đích không chọn class. |
| PVC `spec.resources.requests.storage`, `accessModes` | Yêu cầu dung lượng/mode, không tự chứng minh backend enforce quota disk. |
| StorageClass `provisioner`, `parameters`, `volumeBindingMode` | Xác định bên thực thi và thời điểm quyết định topology. |
| PV `spec.claimRef`, `storageClassName`, `nodeAffinity` và nguồn volume | Nối claim tới storage cụ thể và giới hạn node. |

## 3. Kiểm tra hiểu trước lab

1. Claim dùng `WaitForFirstConsumer`, chưa có Pod dùng claim và đang Pending. Kết luận? **A.** Chắc chắn lỗi. **B.** Phải xóa PVC. **C.** Có thể đang chờ consumer đúng thiết kế.
2. Thay storageClassName bằng tên mới có tự cài provisioner không? **A.** Có. **B.** Không. **C.** Có nếu tên chứa `csi`.

## 4. Thực hành và bằng chứng

1. Mentor kiểm class/provisioner/version/topology chỉ đọc. Học viên đọc scaffold claim nhỏ, chưa gắn consumer; quan sát theo binding mode thật, không ép mọi cluster cho cùng trạng thái ban đầu.
2. Học viên tạo consumer có placement rõ; kiểm claim Bound, PV/source/node affinity, mount và một marker duy nhất. Không tạo marker tự động mỗi lần startup.
3. Tạo claim test khác với tên class không tồn tại, quan sát Events và nêu dependency thiếu. Khôi phục bằng cấu hình/claim test đúng sau review; không đổi class của PVC chứa dữ liệu thật để chữa thử.

**Đạt khi:** lần được Pod → PVC → PV → backend/node và phân biệt Pending chờ consumer với thiếu class/provisioner. Có readback marker trên volume thực tế.

## 5. Cần DevOps và giới hạn lab

- Cần tên class, loại backend, topology/modes, dung lượng/IOPS, expansion/reclaim và trách nhiệm vận hành. DE mô tả nhu cầu thay vì yêu cầu một tên class đoán trước.
- Với local-path, đọc đường/source và node affinity được provisioner tạo; không suy mọi PVC đều node-local hoặc mọi class đều CSI. `Bound` chưa chứng minh backup hay dung lượng được reserve vật lý.

**Nguồn:** [StorageClasses](https://kubernetes.io/docs/concepts/storage/storage-classes/), [Persistent volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/), [K3s storage](https://docs.k3s.io/storage).
