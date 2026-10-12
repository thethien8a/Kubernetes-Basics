# Sau buổi 12 - PV, PVC và StorageClass

**Bắt đầu:** 2026-10-11. **Hoàn thành sau review:** 2026-10-12, giờ Việt Nam. **Tiến độ sau buổi:** 12/28.

[Challenge gốc](../roadmap/buoi-hoc/12-pv-pvc-storageclass.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [PVC](../storage-buoi12.yaml) · [Pod consumer](../app-buoi12.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a12943-80ca-717b-9eb3-6ead54ef0d19)

> Pod mới dùng lại cùng PVC/PV và nguồn storage có thể đọc dữ liệu cũ. Các byte nằm trên backend lưu trữ, không nằm trong image, YAML hoặc object PVC/PV; persistence qua thay Pod không đồng nghĩa HA hay backup.

## 1. Challenge và phạm vi

Nối từ Buổi 11: file runtime trong filesystem container mất khi thay Pod. Buổi 12 yêu cầu một app xin 10Gi storage, mount nguồn đó rồi kiểm tra dữ liệu qua việc thay Pod.

- Context `orbstack`, namespace `default`, một node `orbstack`.
- Học viên tự tạo PVC `data-buoi12`, chỉ định StorageClass `local-path`, request storage `10Gi`, access mode `ReadWriteOnce`, volume mode `Filesystem`.
- Sau baseline PVC Pending, học viên tự triển khai Pod đơn lẻ `app-buoi12`, container `app`, image `busybox:1.36`.
- Pod mount PVC tại `/data`. Script chỉ `while true; do sleep 3600; done`, không tự tạo file khi khởi động.
- CPU request/limit 10m/100m, RAM 16Mi/32Mi; không Service, Ingress, database hoặc Secret/env ứng dụng.
- Học viên ghi chuỗi giả `order_id=202` kèm newline vào `/data/orders.txt`, rồi xóa/tạo lại chỉ Pod từ cùng manifest và chỉ đọc lại file.
- Giữ PVC/PV, claimName, mountPath, image/script và resources; không ghi lại file sau thay Pod hoặc ghi đầy 10Gi.

Mentor cung cấp scaffold/commands, tự đọc manifest/API/Events và file/mount bằng công cụ chỉ đọc, lưu baseline trước khi học viên thay Pod. Không apply/delete/restart workload, ghi/xóa dữ liệu, đổi StorageClass hoặc chạy script setup/teardown thay học viên. Không đọc token service-account.

## 2. Các thành phần và trách nhiệm

| Thành phần | Vai trò | Trong bài |
|---|---|---|
| PVC - PersistentVolumeClaim | Yêu cầu xin cấp/sử dụng storage: dung lượng, access mode, class. Không phải template tạo disk hoặc nơi lưu byte file. | `default/data-buoi12`, 10Gi/RWO/local-path. |
| StorageClass | Mô tả loại/quy tắc cấp storage, tên provisioner, parameters và chính sách binding/reclaim. Không phải controller đang chạy. | `local-path`, provisioner `rancher.io/local-path`, WaitForFirstConsumer, Delete. |
| Provisioner | Controller thực hiện cấp động: đọc PVC/class, chuẩn bị storage backing và tạo PV. Không tạo PVC thay cho app. | Deployment `kube-system/local-path-provisioner`, image `rancher/local-path-provisioner:v0.0.36`. |
| PV - PersistentVolume | Object đại diện nguồn storage đã được cấp, mô tả nguồn, dung lượng, access mode, binding và ràng buộc node/topology nếu có. | PV local trỏ tới thư mục trên node, bind đúng PVC. |
| Backend storage | Nơi thực sự lưu các byte của file. | Filesystem/thư mục trên node Linux `orbstack`. |

```diagram
PVC: yêu cầu ──┐
               ├──→ provisioner ──→ chuẩn bị storage + tạo PV
SC: quy tắc ──┘

Pod mount /data ──→ PVC data-buoi12 ↔ PV ──→ storage trên node
```

Sơ đồ mô tả quan hệ cấp/sử dụng storage, không có nghĩa dữ liệu file được lưu hoặc truyền qua các object API. Provisioner không nằm trên đường đọc/ghi từng byte của app.

**Bind khác mount:** PVC bind với PV; container mount volume tại `mountPath`. App ghi vào `/data` thì ghi vào nguồn đã mount. `/tmp` không tự mang tính persistent hay ephemeral: nguồn bao phủ đường dẫn đó mới quyết định vòng đời. Trong Pod bài này, `/tmp` không có mount riêng và nằm trong filesystem container, còn `/data` dùng PVC.

PVC/PV binding là quan hệ một-một; không đồng nghĩa volume chỉ có một Pod dùng. Cấp thủ công PV hợp lệ cũng có thể đáp ứng PVC mà không cần dynamic provisioner tạo PV mới; bài chọn cấp động vì lab đã có controller/class sẵn.

## 3. Field và cấu hình cần nhận ra

Không yêu cầu nhớ toàn bộ YAML; hai manifest liên kết ở đầu tài liệu là cấu hình thực hành.

| Chủ sở hữu | Field | Ý nghĩa |
|---|---|---|
| PVC | `spec.storageClassName: local-path` | Chọn class rõ ràng, không phụ thuộc default class ẩn. |
| PVC | `spec.resources.requests.storage: 10Gi` | Dung lượng storage yêu cầu, không phải RAM. |
| PVC | `spec.accessModes: [ReadWriteOnce]` | Xin mount đọc/ghi từ một node; không phải khóa theo một Pod. |
| Pod | `spec.volumes[].persistentVolumeClaim.claimName: data-buoi12` | Chọn PVC trong cùng namespace của Pod. |
| Container | `volumeMounts[].name` | Khớp tên volume `data` trong Pod. |
| Container | `volumeMounts[].mountPath: /data` | Đường dẫn container thấy nguồn dữ liệu; app phải ghi vào đây. |
| StorageClass | `provisioner`, `volumeBindingMode`, `reclaimPolicy` | Ai cấp, thời điểm cấp/bind và policy được dùng cho PV cấp động mới. |
| PV | `spec.local.path`, `spec.nodeAffinity`, `spec.claimRef` | Nguồn node-local và binding tới đúng tên/namespace/UID PVC. |
| PV | `spec.persistentVolumeReclaimPolicy` | Policy của PV hiện có khi storage được trả lại sau khi bỏ PVC. |

StorageClass hiện dùng `WaitForFirstConsumer`: provisioning/binding chờ consumer Pod để phối hợp placement và storage phù hợp node/topology. Không ép `nodeName`, đổi binding mode hoặc tạo PV thủ công để bỏ qua trạng thái chờ trong thí nghiệm.

## 4. Minh chứng cấp động và persistence

### PVC trước consumer

Ngày 2026-10-11, mentor kiểm tra lúc 16:33:10 và đối chiếu lại 16:37:28:

- PVC tồn tại đúng spec, UID `f9758cbb-12ce-4ea5-8a67-59daad34231f`, tạo lúc 16:23:51.
- Phase Pending, chưa có `spec.volumeName` hoặc selected-node; Used By none, chưa Pod nào dùng claim và inventory PV rỗng.
- Event Normal `WaitForFirstConsumer`: `waiting for first consumer to be created before binding`.
- Provisioner Running/Ready, RESTARTS=0 ở baseline; class giữ WaitForFirstConsumer/Delete.

**Nhận định:** đây là trạng thái chờ theo policy, không phải bằng chứng thiếu RAM/disk hoặc provisioner hỏng. Các cột Capacity/Access Modes chưa có trong status không phủ nhận request/accessModes đã khai báo trong spec.

### Sau khi có consumer

PVC giữ UID, chuyển Bound, selected-node `orbstack`; PV được tạo lúc 17:04:16. Events của PVC có ExternalProvisioning/Provisioning rồi `ProvisioningSucceeded` do `rancher.io/local-path`, thông báo cấp đúng PV. Pod có Scheduled/Pulled/Created/Started.

- PV: `pvc-f9758cbb-12ce-4ea5-8a67-59daad34231f`.
- PV UID: `6ae35b86-6cf9-4154-9a0f-5fabc07a2ca1`.
- ClaimRef khớp `default/data-buoi12` và UID PVC; cả PVC/PV Bound.
- Source `local.path`: `/var/lib/rancher/k3s/storage/pvc-f9758cbb-12ce-4ea5-8a67-59daad34231f_default_data-buoi12`.
- Node affinity yêu cầu `kubernetes.io/hostname In [orbstack]`.
- Metadata capacity 10Gi, RWO, class local-path, reclaim Delete.

### Trước và sau thay chỉ Pod

Các mốc trong bảng là giờ Việt Nam ngày 2026-10-11.

| Đối chiếu | Trước khi thay Pod | Sau khi tạo Pod mới |
|---|---|---|
| Mốc đọc API / file | 17:17:16 / 17:18:03 | 22:05:04 / 22:07:38 |
| Pod name | app-buoi12 | app-buoi12 |
| Pod UID | `f419498e-2343-49b8-aaf6-9919dd3847e8` | `5a5faa3b-c165-48c5-a916-1b089a52dd63` |
| Pod được tạo | 17:04:08 | 22:03:44 |
| Node / Pod IP | orbstack / 192.168.194.32 | orbstack / 192.168.194.33 |
| Trạng thái | Running/Ready 1/1, RESTARTS=0 | Running/Ready 1/1, RESTARTS=0 |
| PVC/PV | Hai UID và binding đã lưu ở trên | Giữ nguyên hai UID, binding, nguồn và Bound |
| File `/data/orders.txt` | `order_id=202` kèm newline | Chính xác cùng chuỗi byte, đối chiếu với baseline |
| Image/script/mount/resources | BusyBox, sleep, PVC tại /data | Giữ nguyên; không tự sinh file |

Cùng image digest `sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662`. ContainerID đổi cùng Pod; tên giống nhau không có nghĩa cùng object. ResourceVersion PVC/PV giữ 133387/133385 qua mốc thay Pod, không có minh chứng cấp PV mới trong phép thử này.

```diagram
Trước: Pod UID A ──→ PVC data-buoi12 ↔ cùng PV ──→ storage cũ
Sau:   Pod UID B ━━▶ PVC data-buoi12 ↔ cùng PV ──→ storage cũ
```

Mountinfo trước/sau có `/data` type btrfs, source `/dev/vdb1`, filesystem root `/k8s/default/k3s/storage/pvc-f9758cbb-12ce-4ea5-8a67-59daad34231f_default_data-buoi12`; root container là overlay. `PV.local.path` là đường dẫn trên node, filesystem root trong mountinfo không phải đường dẫn trực tiếp trên Mac; không kiểm tra trực tiếp node để suy ra toàn bộ mapping OrbStack.

**Mốc chốt ngày 2026-10-12:** metadata lúc 12:45:33 và đọc file/mount lúc 12:46:56 vẫn cùng Pod mới/PVC/PV, Ready, RESTARTS=0, Bound, nguồn mount và chính xác `order_id=202` kèm newline. API sau các phép đọc giữ cùng UID/containerID/binding. Provisioner Ready 1, class vẫn WaitForFirstConsumer/Delete.

**Kết luận đã kiểm chứng:** dữ liệu tồn tại qua thay Pod khi app mới dùng lại đúng PVC/PV và backing storage còn tồn tại, trên cùng node local. Không coi Ready riêng lẻ, apply thành công hoặc giữ tên Pod là bằng chứng persistence; snapshot không audit mọi command hay thay đổi file từ bên ngoài.

## 5. RWO, dung lượng và reclaim

### ReadWriteOnce

RWO cho mount đọc/ghi từ một node; nhiều Pod trên cùng node vẫn có thể dùng volume. Nó không phải khóa ghi theo Pod hoặc bảo đảm các ứng dụng ghi chung data an toàn. Buổi này chỉ thực hành một Pod consumer mỗi thời điểm; không chạy hai Pod cùng volume hoặc nhiều node.

### Request 10Gi trong local-path lab

Source provisioner v0.0.36 và cấu hình setup đã đọc chỉ chuẩn bị directory, không preallocate 10Gi hoặc đặt filesystem quota cho volume trong lab này. Con số 10Gi trong PVC/PV metadata không chứng minh đã reserve đủ dung lượng hoặc chặn ghi vượt 10Gi; không suy ra mọi backend/driver đều có hành vi này. Chỉ ghi file vài byte, không thử quota hoặc lấp đầy disk.

### Reclaim policy

Claim trong bài là PVC `data-buoi12`. Reclaim policy là quy tắc xử lý PV/storage khi PVC đã bỏ sử dụng, được xóa và volume được trả lại.

| Policy | Hành vi được giải thích, chưa thực hành |
|---|---|
| Delete | Với driver hỗ trợ, controller dọn PV và storage backing; teardown local-path lab có thể xóa thư mục/data. Thuận tiện dọn tài nguyên nhưng không được mặc định kỳ vọng giữ dữ liệu sau bỏ PVC. |
| Retain | Giữ storage/data và PV ở trạng thái cần quản lý lại thủ công; không tự làm backup hoặc tự cấp dữ liệu cũ cho mọi PVC mới. Người vận hành chịu trách nhiệm tái sử dụng/dọn. |

- Xóa chỉ Pod và giữ PVC/PV khác với xóa PVC sau khi không còn Pod sử dụng. Trường hợp đầu đã thử; trường hợp thứ hai chỉ review giả định.
- Policy Delete không áp dụng mỗi lần container restart hoặc Pod được thay, không hứa cleanup tức thì/thành công vô điều kiện và không chứng minh secure erase.
- StorageClass cung cấp reclaim policy cho PV cấp động mới. Không mặc định đổi StorageClass là đã đổi policy của PV hiện có; xem `PV.spec.persistentVolumeReclaimPolicy` của đúng volume.
- Giữ dữ liệu qua xóa Pod chỉ đúng với nguồn có vòng đời phù hợp. `emptyDir` cũng là volume mount nhưng mất dữ liệu khi xóa Pod; không khái quát mọi mount đều persistent.

**An toàn:** không xóa PVC/PV, đổi policy hoặc chạy teardown trong Buổi 12. Không dùng thao tác xóa dữ liệu để kiểm tra câu hỏi lý thuyết.

## 6. Review, nhầm lẫn và phần mentor bổ sung

| Chủ đề | Câu trả lời và kết quả |
|---|---|
| File ngoài mount PVC | Học viên nêu PVC không bảo vệ file /tmp của cấu hình hiện tại. Đạt ý chính; mentor chuẩn hóa PVC bind PV, còn thư mục được mount, nguồn quyết định vòng đời chứ không phải tên đường dẫn. |
| Vai trò PVC/PV | Lần đầu gọi PVC là template, PV là storage thực tế và provisioner triển khai PVC. Sau giải thích, học viên trả lời PVC là yêu cầu tài nguyên, PV là object đại diện vùng storage đã cấp/mô tả nguồn và node, byte lưu trong thư mục trên node. Review đạt cho PV local của lab; mô tả node/topology phụ thuộc loại PV, không phải mọi PV đều gắn một node. |
| RWO với hai Pod cùng node | Học viên trả lời không cấm, hướng tới giới hạn theo node. Đạt ý chính; mentor bổ sung định nghĩa mount đọc/ghi từ một node và cảnh báo đồng thời ghi là trách nhiệm ứng dụng. Chưa thực hành nhiều Pod. |
| Thiếu provisioner ngoài lab | Ban đầu chưa biết. Sau giải thích, học viên trả lời “Không vì provisioner phụ trách việc tạo PV”. Đạt cho câu chỉ có StorageClass/PVC nhưng chưa cài/chạy provisioner thì không tự cấp storage/PV mới. Chuẩn bị backend, cấu hình driver/quyền/topology và debug chi tiết là phần mentor bổ sung, chưa triển khai ngoài lab. |
| Xóa PVC với Delete so với xóa Pod | Ban đầu chưa hiểu claim/policy. Sau giải thích, học viên trả lời không kỳ vọng giữ dữ liệu nếu xóa PVC; xóa Pod không ảnh hưởng dữ liệu đã mount trong tình huống này. Đạt với PVC/PV/backing storage còn; mentor giới hạn phát biểu cho nguồn persistent, không mọi volume. Không thực hành reclaim hoặc thử xóa dữ liệu. |

Đã cung cấp scaffold/commands và giải thích các trạng thái sau quan sát; khi learner chưa hiểu thuật ngữ, dùng tên resource thật và giảm xuống từng tình huống review, không sửa workload hay triển khai thêm để giảng. Runtime đạt không được dùng thay câu trả lời concept; chốt sau hai câu PVC/PV và reclaim đạt ngày 2026-10-12.

## 7. Commands để ôn

Các lệnh đầu là trình tự tạo baseline học viên đã dùng; không phải lệnh reset dữ liệu. PVC hiện Bound nên apply lại PVC không tái hiện Pending ban đầu. Không xóa claim đang giữ dữ liệu chỉ để xem lại WaitForFirstConsumer.

```bash
kubectl --context=orbstack -n default apply -f storage-buoi12.yaml
kubectl --context=orbstack -n default get pvc data-buoi12
kubectl --context=orbstack -n default describe pvc data-buoi12

kubectl --context=orbstack -n default apply -f app-buoi12.yaml
kubectl --context=orbstack -n default wait \
  --for=condition=Ready pod/app-buoi12 --timeout=120s
kubectl --context=orbstack -n default exec app-buoi12 -- sh -c \
  "printf 'order_id=202\n' > /data/orders.txt && cat /data/orders.txt"
```

Sau khi lưu baseline, phép thử đã dùng chỉ thay Pod và đọc, không chạy lại lệnh ghi:

```bash
kubectl --context=orbstack -n default delete pod app-buoi12 --wait=true &&
kubectl --context=orbstack -n default apply -f app-buoi12.yaml &&
kubectl --context=orbstack -n default wait \
  --for=condition=Ready pod/app-buoi12 --timeout=120s &&
kubectl --context=orbstack -n default exec app-buoi12 -- cat /data/orders.txt
```

Commands chỉ đọc để xem cấu hình/identity:

```bash
kubectl --context=orbstack get storageclass local-path -o yaml
kubectl --context=orbstack -n default get pod app-buoi12 \
  -o custom-columns='NAME:.metadata.name,UID:.metadata.uid,NODE:.spec.nodeName'
kubectl --context=orbstack -n default get pvc data-buoi12 -o yaml
kubectl --context=orbstack get pv pvc-f9758cbb-12ce-4ea5-8a67-59daad34231f -o yaml
kubectl --context=orbstack -n kube-system get deployment local-path-provisioner
```

Chỉ dùng đúng resource demo và dữ liệu giả. Với app thật cần kiểm tra nội dung trước khi đọc logs/exec, không dump env, token hoặc Secret. Mentor không thực hiện các lệnh write/apply/delete ở phần ôn thay học viên.

## 8. OrbStack làm giúp và cấu hình ngoài lab

- **Trong lab:** đã có filesystem node, StorageClass local-path và controller rancher. ConfigMap local-path-config chọn path mặc định `/var/lib/rancher/k3s/storage`, không có sharedFileSystemPath; helper của provisioner chuẩn bị directory rồi PV mô tả nguồn local. API StorageClass hoặc local volume tự nó không tạo directory/disk hay replication.
- **Cấp động ngoài lab:** cần backend lưu dữ liệu và controller/driver phù hợp, cấu hình StorageClass.provisioner/parameters/binding/reclaim, quyền truy cập backend và topology. App chọn class qua PVC rồi mount đúng đường dẫn. CSI là giao diện/driver kết nối Kubernetes với hệ storage phù hợp; lab này dùng local-path, không chứng minh đã cài/thử CSI.
- **Cấp tĩnh:** người quản trị chuẩn bị storage thật trước rồi tạo PV mô tả nguồn, capacity/access modes/class và node affinity nếu là local. Không có nghĩa apply một PV YAML sẽ tự tạo disk/directory. Đổi lại người vận hành quản lý từng volume thủ công; bài dùng cấp động để tận dụng controller sẵn và thấy rõ luồng request → cấp PV.
- **On-prem/tự quản lý:** có thể chuẩn bị local filesystem hoặc backend dùng chung cùng driver/controller tương ứng. Local đơn giản nhưng gắn node và không tự chịu lỗi node; backend dùng chung/replicated cần hạ tầng, cấu hình và quy trình vận hành riêng. Không triển khai thêm storage system chỉ để giải thích trong tháng đầu.
- **Cloud/managed Kubernetes:** nhà cung cấp có thể chuẩn bị CSI/default class/backend tích hợp, nhưng phải kiểm tra driver đang chạy, class/parameters, quyền tài khoản và topology thực tế; không chỉ copy tên `local-path` rồi kỳ vọng cloud disk được cấp.
- **Node khác/node hỏng:** PV local hiện có affinity orbstack; không giả định Pod có thể chuyển sang bất kỳ node nào và tự đem directory đi theo. Backend replicated/remote, khả năng attach/mount, backup/restore và app/database HA là các vấn đề khác, chưa kiểm thử ở đây.
- **Debug:** PVC status/describe/Events → StorageClass/name/provisioner/binding → controller status/logs → PV binding/source/node affinity → Pod Events/mount/path ghi và backend/quyền/dung lượng. WaitForFirstConsumer chưa có consumer là chờ đúng policy, không tự suy ra thiếu controller từ mọi Pending. Không xuất credential khi kiểm tra backend/logs.

## 9. Liên hệ Data Engineering và giới hạn

- PostgreSQL/metadata database cần thư mục data nằm trên đúng nguồn persistent; manifest/image hay chỉ giữ tên Pod không bảo vệ dữ liệu runtime. Đây là liên hệ, chưa chạy PostgreSQL trong Buổi 12.
- Provisioner cấp storage, kubelet/runtime thực hiện mount, app phải ghi đúng đường dẫn; Kubernetes không tự chuyển mọi file của ứng dụng vào PVC.
- Giữ PVC/PV không thay thế backup; Delete thuận tiện dọn lab nhưng có thể làm mất data khi bỏ claim. RWO không bảo đảm hai database instances cùng ghi một directory sẽ an toàn.

**Đã thực hành:** PVC Pending theo WaitForFirstConsumer, cấp động/Bound, mount/file và persistence qua thay Pod cùng node. **Chỉ giải thích/review:** RWO nhiều Pod/node, Delete/Retain/reclaim, filesystem quota/10Gi và cấu hình ngoài lab. **Chưa làm:** xóa PVC/PV/data, thử node hỏng/migration, mount emptyDir, backup/restore, HA, PostgreSQL hoặc triển khai CSI/backend khác.

**Buổi 12 Hoàn thành, tổng 12/28.** Tiếp theo là [Buổi 13 - PostgreSQL](../roadmap/buoi-hoc/13-postgresql.md), chưa bắt đầu trong lượt chốt này. Pod/PVC/PV demo vẫn được giữ; tổng kết không phải thao tác dọn tài nguyên.

## Tài liệu tham khảo

- [Persistent Volumes v1.35](https://v1-35.docs.kubernetes.io/docs/concepts/storage/persistent-volumes/).
- [Storage Classes v1.35](https://v1-35.docs.kubernetes.io/docs/concepts/storage/storage-classes/).
- [local-path-provisioner v0.0.36](https://github.com/rancher/local-path-provisioner/blob/v0.0.36/README.md).
