# Bài 20 — Access modes và chuyển node

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](19-storageclass.md) · [Tiếp](21-statefulset.md)

**Đầu vào:** claim Bound và đọc được PV topology. **Đầu ra:** giải thích vì sao Pod có thể tạo lại nhưng dữ liệu không tự đi theo sang node khác.

## 1. Khối kiến thức

- RWO cho phép read-write từ một node; vẫn có thể nhiều Pod trên node đó. RWOP là ràng buộc một Pod, cần CSI/phiên bản hỗ trợ. RWX cho phép nhiều node mount read-write nếu backend hỗ trợ, không tự làm ứng dụng an toàn khi nhiều writer.
- Access mode không thay topology. Volume node-local gắn dữ liệu với node; network/block storage có khả năng gắn lại tùy driver, zone và quy trình detach/attach, không mặc định “mount ở đâu cũng được”.
- Cùng một host path string trên hai node containers có thể là hai nguồn dữ liệu khác nhau. Bind cùng thư mục Mac vào mọi node có thể tạo chia sẻ nhân tạo, không phải minh chứng storage replication.
- Pod mất node và Pod đổi UID trên cùng node là hai thử nghiệm khác nhau. Không bỏ node affinity của PV để ép workload đọc nhầm dữ liệu hoặc mount sai nguồn.

## 2. Đọc cấu hình

| Field | Điều cần liên hệ |
|---|---|
| PVC/PV `spec.accessModes` | Yêu cầu mode và khả năng backend; không chỉ đổi chữ RWO→RWX. |
| PV `spec.nodeAffinity` | Giới hạn nơi consumer có thể chạy, khác node affinity của app. |
| PodSpec `nodeSelector` và volume `claimName` | Giao của điều kiện workload với topology volume phải có node hợp lệ. |
| StorageClass `allowedTopologies`, `volumeBindingMode` | Cách nền tảng hạn chế/căn chỉnh nơi cấp storage, tùy provisioner. |

## 3. Kiểm tra hiểu trước lab

1. RWO có nhất thiết giới hạn đúng một Pod không? **A.** Không, nhiều Pod trên cùng node vẫn có thể dùng. **B.** Có. **C.** Nó nghĩa là chỉ đọc.
2. Local PV gắn agent 0; Pod mới bắt buộc agent 1. Biện pháp nào đúng để điều tra? **A.** Xóa node affinity PV ngay. **B.** Đọc xung đột placement/topology và yêu cầu storage phù hợp. **C.** Tăng replicas sẽ copy dữ liệu.

## 4. Thực hành và bằng chứng

1. Dùng volume disposable ở agent 0, ghi marker một lần, giữ claim/PV. Học viên thay consumer trên cùng node rồi đọc lại; ghi cả UID Pod và UID claim/PV.
2. Dừng consumer cũ an toàn, tạo consumer mới dùng cùng claim nhưng yêu cầu agent 1; với PV node-local đã xác nhận, quan sát Pending/volume node affinity conflict. Không chạy hai writer hoặc sửa PV affinity.
3. Học viên khôi phục placement tương thích và đọc marker cũ. So với tình huống CSI gắn lại/RWX bằng tài liệu; chưa cài distributed storage hoặc claim RWOP trên driver không hỗ trợ.

**Đạt khi:** có cả persistence qua Pod replacement và đối chứng không thể chuyển tùy ý sang node khác. Nêu backend nào còn phải yêu cầu nếu cần chịu mất node.

## 5. Cần DevOps và giới hạn lab

- Hỏi mode thật được hỗ trợ, topology/zone, detach/attach, timeout recovery, dữ liệu khi node mất và cách restore. Nêu rõ một writer hay nhiều writer, filesystem hay object storage.
- Lab local-path chỉ chứng minh giới hạn của backend đã chọn. Không đồng nhất network storage với backup/HA; block disk gắn lại cũng không tự bảo đảm database consistency.

**Nguồn:** [Access modes và PV topology](https://kubernetes.io/docs/concepts/storage/persistent-volumes/), [Local volumes](https://kubernetes.io/docs/concepts/storage/volumes/).
