# Tổng kết Bài 20 — Access modes và chuyển node

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/20-storage-multi-node.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/21-statefulset.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-18**, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Review cuối:** `1B, 2A`, đúng 2/2. Phân biệt gắn lại volume còn nguyên với khôi phục dữ liệu từ bản sao khi volume mất hoặc hỏng.
- **Kiểm chốt:** **11:10:32 ngày 18/11/2026**, sau review. Pod phục hồi Ready trên `agent-0`, cùng PVC/PV và marker cũ.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`, volume disposable riêng của Bài 20. Học viên tự tạo/thay Pod, ghi một marker giả một lần; mentor chuẩn bị scaffold, dry-run phía client và kiểm tra live chỉ đọc. Không thao tác tài nguyên Bài 19.

## 1. Mental model và cấu hình

| Mode | Điều cần nhớ |
|---|---|
| `ReadWriteOnce` (RWO) | Đọc/ghi từ một **node** tại một thời điểm; nhiều Pod trên cùng node vẫn có thể dùng. Không phải khóa một writer. |
| `ReadWriteOncePod` (RWOP) | Giới hạn chỉ một **Pod** mount volume qua claim tại một thời điểm. Cần volume CSI và driver/thành phần tương thích. |
| `ReadWriteMany` (RWX) | Nhiều node có thể mount đọc/ghi đồng thời nếu backend hỗ trợ; ứng dụng vẫn phải điều phối ghi. |

**Access mode** mô tả kiểu truy cập. **Topology** cho biết volume cụ thể dùng được ở đâu. Một volume RWO có thể gắn lần lượt vào nhiều node nếu backend/driver hỗ trợ, nhưng PV local của lab chỉ dùng được trên node giữ dữ liệu. `Bound` nói PVC đã ghép với PV, không nói Pod đã được xếp node, volume đã mount hoặc dữ liệu chịu được mất node.

| Resource / field | Vai trò |
|---|---|
| PVC `spec.storageClassName`, `spec.accessModes` | Chọn class và yêu cầu kiểu truy cập. Đổi mode trong yêu cầu mới không tạo thêm khả năng cho backend. |
| PV `spec.accessModes`, `spec.local.path` | Mode được khai báo cho PV và nguồn lưu trữ cụ thể trong lab. Đường local của node k3d không mặc nhiên là đường trên Mac hay dữ liệu dùng chung với node khác. |
| Pod `spec.volumes[].persistentVolumeClaim.claimName` | Tham chiếu PVC cùng namespace; đọc tiếp `PVC.spec.volumeName` và `PV.spec.claimRef` để kiểm hai chiều, gồm UID claim. |
| Pod `spec.volumes[].name` ↔ container `volumeMounts[].name`/`mountPath` | Nối volume `data` vào `/data`. File ghi ngoài mount không được bao phủ bởi phép thử này. |
| Pod `spec.nodeSelector` và PV `spec.nodeAffinity` | Scheduler cần node thỏa **cả hai**. Bỏ selector của Pod không gỡ affinity của PV. `Pod.spec.nodeName` cho biết node thực tế được chọn. |
| StorageClass `volumeBindingMode` | `Immediate` xét cấp/bind trước placement của Pod; `WaitForFirstConsumer` xét cấp/bind lần đầu cùng điều kiện scheduling của Pod. Không tự cấp lại hoặc di chuyển PV đã Bound. |
| StorageClass `allowedTopologies` | Với driver hỗ trợ, đây là giới hạn nơi **cấp mới** theo topology mà driver công bố. Không thay thế affinity của PV đã cấp. `<none>` trên class lab không có nghĩa volume dùng được ở mọi node. |

Ví dụ ngoài lab đã đọc (không apply): class AWS EBS CSI chuẩn có `provisioner: ebs.csi.aws.com`, `volumeBindingMode: WaitForFirstConsumer` và `allowedTopologies[].matchLabelExpressions[]` dùng key `topology.ebs.csi.aws.com/zone`, values `[us-east-2c]`. PVC mới dùng class đó và Pod chỉ được đặt ở `us-east-2b` không có vị trí hợp lệ để cấp mới; scheduler không tự nới điều kiện của Pod hoặc class.

## 2. Thiết kế phép thử

Client `/usr/local/bin/kubectl` **v1.33.9**, API server **v1.33.6+k3s1**. Đã kiểm API `v1` cho Pod/PVC và ARM64. Class `local-path` dùng `rancher.io/local-path`, `WaitForFirstConsumer`, reclaim `Delete`, `defaultVolumeType: local`, không khai báo `allowedTopologies`. Preflight thấy provisioner v0.0.32 Ready 1/1 và helper `rancher/mirrored-library-busybox:1.36.1`.

| Scaffold | Vai trò |
|---|---|
| [01-pvc.yaml](../thuc-hanh/20-storage-multi-node/01-pvc.yaml) | `lesson20-data`, class `local-path`, RWO, yêu cầu `128Mi` (không nghiệm thu quota). |
| [02-consumer.yaml](../thuc-hanh/20-storage-multi-node/02-consumer.yaml) | Pod độc lập `lesson20-consumer`, selector hostname `k3d-de-k3d-agent-0`, claim `lesson20-data` mount tại `/data`. Dùng cho baseline, thay Pod cùng node và phục hồi. |
| [03-wrong-node.yaml](../thuc-hanh/20-storage-multi-node/03-wrong-node.yaml) | Chỉ đổi giá trị selector hostname thành `k3d-de-k3d-agent-1`; giữ tên Pod, claim, mount và phần còn lại. |

Ba file qua client dry-run/schema, không tạo workload live khi kiểm. Worker chạy `sleep 86400`, không có lệnh ghi file lúc startup, không mount API token hoặc khai báo env/envFrom. `restartPolicy: Always` có thể chạy lại container, không tạo lại naked Pod đã xóa. Grace period 5 giây; requests `25m/32Mi`, limits `100m/64Mi`. Image `busybox:1.37.0` pin index digest `sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec`, đã kiểm `linux/arm64/v8` qua metadata registry.

**Giữ cố định:** UID PVC, UID PV, liên kết hai chiều, đường mount, nội dung marker đã ghi một lần. Xóa đúng Pod cũ và đợi nó biến mất trước mỗi `create`; không xóa PVC/PV, không sửa affinity, không chạy hai writer. Cùng tên Pod không có nghĩa cùng UID.

## 3. Kết quả thực hành

### 3.1 Storage không đổi qua các lượt

- Namespace `de-lab` Active, UID `6d2e69f9-ada2-4699-af0d-2c98a3974710`.
- PVC `lesson20-data` UID `8533dc57-89cc-45ea-bb82-2292340a93c0`, `Bound`, `Filesystem`. `spec.volumeName=pvc-8533dc57-89cc-45ea-bb82-2292340a93c0`.
- PV UID `db504e82-3192-4fd5-abff-04d37deab093`, `Bound`, claimRef khớp namespace/tên/UID, reclaim `Delete`. `spec.local.path` là `/var/lib/rancher/k3s/storage/pvc-8533dc57-89cc-45ea-bb82-2292340a93c0_de-lab_lesson20-data`.
- `PV.spec.nodeAffinity.required` có một điều kiện `kubernetes.io/hostname In [k3d-de-k3d-agent-0]`. Đây là PV **Bài 20**, không dùng biến `$PV` đã trỏ tới volume Bài 19.

### 3.2 Bốn lượt Pod cùng tên `lesson20-consumer`

| Lượt | UID Pod | Quan sát |
|---|---|---|
| Baseline | `3369becf-fdfc-43f6-9cb2-fb9c1d4395c9` | Ready trên `agent-0`, `/data` là mount point. Mentor thấy marker chưa có; sau khi học viên tự ghi một lần, mentor xác nhận đúng file giả 50 byte, không symlink. |
| Thay Pod cùng node | `9c4d06c6-6ac6-47a8-a6e9-9ff4978544c5` | Metadata tạo 10:44:13 giờ Việt Nam; Ready trên `agent-0`. Hai UID storage giữ nguyên, Pod mới chỉ đọc và thấy đúng marker cũ; mentor đối chiếu độc lập. |
| Đối chứng `agent-1` | `61375672-3022-42a7-b4d8-e2bff5ce42b4` | Tạo 10:56:28; selector `agent-1`, `Pending`, `nodeName` trống, `PodScheduled=False/Unschedulable`, chưa có trạng thái container. PVC/PV vẫn Bound. |
| Phục hồi `agent-0` | `c05749f0-b62e-4450-be2a-e11d74de137a` | Tạo 11:00:37; Ready/Running, restart 0 trên `agent-0`, cùng claim/PV, marker đúng. Mentor kiểm sau phục hồi lúc 11:01:52 và kiểm chốt lúc 11:10:32. |

Marker `/data/lesson20-marker.txt` có nội dung `lesson20-pvc-8533dc57-89cc-45ea-bb82-2292340a93c0` và một newline. Học viên ghi ở baseline với guard UID, kiểm mount và `noclobber`. Các Pod sau không có lệnh startup sinh marker. Bảng kết hợp transcript học viên với các lượt mentor kiểm chỉ đọc; timestamp tạo từ API không phải lịch sử đầy đủ của mọi lệnh.

Event `FailedScheduling` của đúng UID đối chứng được học viên thấy và mentor xác nhận độc lập:

```text
0/3 nodes are available: 1 node(s) didn't match PersistentVolume's node affinity, 2 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.
```

`agent-1` là node khớp selector nhưng bị PV loại; hai node còn lại không khớp selector của Pod. Cả ba node Ready, không cordon/taint/pressure ở lượt kiểm đối chứng. `NODE=<none>` và `PodScheduled=False` cho thấy chưa qua scheduling, không phải lỗi mount sau khi đã đặt Pod. Preemption không đổi selector hoặc nơi dữ liệu nằm.

## 4. Lệnh tái quan sát → output → cách đọc

Các lệnh dưới chỉ đọc. Snapshot cũ không thay cho xác nhận identity nếu tái dùng fixture. Không chạy lại các lệnh ghi marker hoặc guard xóa Pod với UID cũ.

```bash
K=(/usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" --context=k3d-de-k3d -n de-lab)
"${K[@]}" config get-contexts k3d-de-k3d -o name
"${K[@]}" get namespace de-lab -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase'
```

Chỉ tiếp tục khi thấy `k3d-de-k3d` và `de-lab Active`.

```bash
PV20=$("${K[@]}" get pvc lesson20-data -o jsonpath='{.spec.volumeName}')
"${K[@]}" get pod/lesson20-consumer pvc/lesson20-data "pv/$PV20" \
  -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase,NODE:.spec.nodeName,UID:.metadata.uid'
```

Snapshot chốt:

```text
NAME                                       PHASE     NODE                 UID
lesson20-consumer                          Running   k3d-de-k3d-agent-0   c05749f0-b62e-4450-be2a-e11d74de137a
lesson20-data                              Bound     <none>               8533dc57-89cc-45ea-bb82-2292340a93c0
pvc-8533dc57-89cc-45ea-bb82-2292340a93c0   Bound     <none>               db504e82-3192-4fd5-abff-04d37deab093
```

`NODE` chỉ đọc trên dòng Pod; `<none>` trên hai dòng storage không phủ định `PV.spec.nodeAffinity`. Đối chiếu cột `UID` với baseline: chỉ UID Pod đổi.

```bash
"${K[@]}" exec lesson20-consumer -c worker -- cat /data/lesson20-marker.txt
```

Học viên thấy `lesson20-pvc-8533dc57-89cc-45ea-bb82-2292340a93c0`; mentor kiểm mount `/data`, kích thước và checksum khớp 50 byte đã biết. Vì không ghi lại, đây là readback của dữ liệu cũ. Khi kiểm lại nếu marker thiếu, chưa kết luận mất volume chỉ từ một lệnh `cat`: kiểm Node, UID, claim/PV và mount; không tạo marker mới để chữa.

Lệnh học viên dùng để quan sát đối chứng (output **lịch sử**, Pod đó đã được thay):

```bash
"${K[@]}" get pod lesson20-consumer \
  -o 'custom-columns=PHASE:.status.phase,NODE:.spec.nodeName,SCHEDULED:.status.conditions[?(@.type=="PodScheduled")].status,REASON:.status.conditions[?(@.type=="PodScheduled")].reason'
```

```text
PHASE     NODE     SCHEDULED   REASON
Pending   <none>   False       Unschedulable
```

Lệnh đọc Event theo UID của Pod đối chứng:

```bash
BAD20='61375672-3022-42a7-b4d8-e2bff5ce42b4'
"${K[@]}" get events --field-selector "involvedObject.uid=$BAD20,reason=FailedScheduling" \
  -o 'custom-columns=REASON:.reason,MESSAGE:.message'
```

`MESSAGE` ở mục 3.2 là output lịch sử của lệnh này. Sau recovery tên Pod trỏ tới UID khác; Event cũ có thể hết hạn, không tạo lại lỗi chỉ để lấy output.

## 5. Review và yêu cầu DevOps

| Lượt | Kết quả |
|---|---|
| RWO cùng node và RWX cho hai executor | `1B, 2C`, đúng. Nhiều node ghi đồng thời cần backend hỗ trợ RWX cùng cơ chế điều phối ghi của ứng dụng. |
| Giao của selector Pod và PV affinity | `C`, đúng. Pod đòi `agent-1` Pending, claim vẫn Bound; nếu bỏ selector của Pod mới thì PV vẫn giới hạn `agent-0`. |
| Class WFFC và `allowedTopologies` | `B`, đúng. Class và Pod phải có vị trí cấp mới phù hợp; không bên nào tự thắng bên kia. |
| Bằng chứng marker qua Pod replacement | Ban đầu chọn `A`: UID đúng nhưng startup ghi lại làm mất giá trị đối chứng. Sau giải thích chọn `B` đúng ở biến thể “chỉ tạo nếu file thiếu”: vẫn có thể che mất dữ liệu. Lab thực hiện ghi ở Pod đầu, Pod thay thế chỉ đọc. |
| Review cuối: một writer, CSI gắn lại và restore | `1B, 2A`, đúng. Một writer không bắt buộc RWX; kiểm storage tồn tại độc lập với node, topology và khả năng gắn lại an toàn, thử đọc checkpoint và đo thời gian hồi phục. Mất volume cần bản sao phù hợp và thử restore riêng. |

- **Trong lab:** K3s đã có provisioner local-path cấp thư mục trên node được chọn. Trên hệ tự quản lý, DevOps có thể cấp local PV/đường lưu với affinity tương ứng hoặc cung cấp provisioner và backend khác; cùng một path string không phải replication.
- **Ngoài lab:** Nếu workload chỉ có một writer và cần chuyển sang node khác trong topology hỗ trợ, hỏi class/driver CSI, volume có tồn tại khi mất node không, cách dừng writer cũ và detach/attach, timeout phục hồi, và nghiệm thu bằng đọc checkpoint cũ. Nếu nhiều node cần ghi filesystem đồng thời, yêu cầu backend hỗ trợ RWX, không chỉ sửa mode trong YAML. Chốt ứng dụng cần filesystem mount hay API object storage trước khi chọn.
- **Debug đúng tầng:** PVC chưa Bound → kiểm Events, class/provisioner, binding mode và topology cấp mới. PVC đã Bound, Pod chưa có node → so selector/labels với `PV.spec.nodeAffinity`. Pod đã được đặt nhưng không mount → kiểm Events attach/mount và backend; sau đó mới kiểm đường ghi và dữ liệu.
- **Giới hạn:** Không thử mất node/disk/host, attach/detach CSI, mount bằng RWOP/RWX, hai writer, xóa volume, backup/restore hoặc Spark/ETL thật. Node k3d chung host; không kết luận HA, bảo vệ dữ liệu hay tính nhất quán của database từ một marker hoặc từ `Bound`.

## 6. Bàn giao và nguồn

Giữ một Pod phục hồi, một PVC, một PV và ba scaffold. Không có cleanup bắt buộc hoặc câu review còn chờ; không xóa storage hay chạy lại đối chứng để chốt. Snapshot 11:10:32: Pod Ready/restart 0, UID/spec ổn định, marker đúng; ba node Ready/ARM64, không cordon/taint/pressure. Chờ **Bài 21 — StatefulSet**, chưa giảng hoặc chuẩn bị scaffold bài mới.

- [Kubernetes v1.33 — PV access modes và node affinity](https://v1-33.docs.kubernetes.io/docs/concepts/storage/persistent-volumes/).
- [Kubernetes v1.33 — StorageClasses và allowed topologies](https://v1-33.docs.kubernetes.io/docs/concepts/storage/storage-classes/#allowed-topologies).
- [Scheduler v1.33.6 — kiểm PV đã Bound và thông báo xung đột](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/scheduler/framework/plugins/volumebinding/binder.go).
- [local-path-provisioner v0.0.32](https://github.com/rancher/local-path-provisioner/blob/v0.0.32/README.md) · [BusyBox 1.37.0 registry metadata](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0).
- [AWS EBS — giới hạn Availability Zone khi attach](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-attaching-volume.html) (tham khảo, không triển khai).
