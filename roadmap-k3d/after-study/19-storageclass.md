# Tổng kết Bài 19 — PVC, StorageClass và provisioning

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/19-storageclass.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/20-storage-multi-node.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-17**, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Review:** 12/12 lựa chọn trắc nghiệm đúng; câu review cuối về class/backend ngoài lab trả lời **C**, đạt.
- **Kiểm chốt:** **22:24:09 ngày 17/11/2026**, sau review cuối; manifest và runtime khớp, marker đọc lại đúng.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`, ba PVC, một naked Pod consumer và một PV được provisioner cấp; chỉ dùng dữ liệu giả.
- **Ranh giới:** học viên tự tạo resource và ghi marker; mentor chuẩn bị scaffold, kiểm schema và kiểm tra chỉ đọc. Không sửa/xóa workload, đổi node, cài driver hoặc đọc credential thay học viên.
- **Khi đóng bài:** giữ bốn scaffold và toàn bộ resource để đối chiếu. Hai PVC test vẫn `Pending` có chủ đích; không ghi thành đã cleanup hoặc đã sửa claim lỗi tại chỗ. Bài gốc không yêu cầu xóa fixture; chưa mở Bài 20.

## 1. Mục tiêu và tiêu chí đã đạt

1. Phân biệt PVC, PV, StorageClass, provisioner và backend; byte nằm ở backend, không nằm trong metadata resource.
2. Quan sát PVC dùng `WaitForFirstConsumer` khi chưa có Pod, rồi tạo consumer có placement rõ trên agent-0.
3. Lần theo Pod → PVC → PV → source và node affinity thực tế; kiểm mount `/data`.
4. Học viên ghi một marker duy nhất sau khi Pod chạy, không đặt lệnh tạo marker trong startup; mentor đọc lại từ volume.
5. Tạo claim test với tên class không tồn tại, kiểm Events theo đúng PVC UID và xác định dependency thiếu.
6. Recovery bằng PVC test mới chọn class đúng; phân biệt `Pending` do lỗi với `Pending` chờ consumer.
7. Review yêu cầu DevOps theo implementation/backend và đặc tính storage, không chỉ theo tên class hoặc chữ `Bound`.

Runtime, đối chứng lỗi, recovery và review đều đạt. Không dùng quiz hoặc client dry-run thay bằng chứng thực hành.

## 2. Mental model và cấu hình đã học

### 2.1 Resource khai báo khác thành phần thực thi

| Thành phần | Vai trò / phạm vi |
|---|---|
| PVC | Yêu cầu storage trong một namespace; Pod tham chiếu PVC cùng namespace. |
| PV | Resource toàn cluster biểu diễn volume cụ thể; có vòng đời độc lập với riêng một Pod. |
| StorageClass | Resource toàn cluster mô tả loại storage được cung cấp, provisioner và chính sách/tham số. |
| Provisioner | Thành phần xử lý yêu cầu cấp volume; tên trong StorageClass không tự cài chương trình này. |
| Backend | Nơi thực sự giữ byte; đặc tính truy cập, topology, quota và bảo vệ dữ liệu phụ thuộc implementation. |

**Luồng cấp phát động:** PVC chọn class → provisioner/backend xử lý → tạo PV → PVC/PV được bind. Đây không phải đường truyền nội dung file qua API.

**Đường sử dụng:** ứng dụng ghi vào filesystem đã mount tại `/data`; cấu hình volume nối mount đó tới PVC/PV và backend.

- **Static provisioning:** người vận hành chuẩn bị storage/PV trước; kiểm soát rõ tài nguyên nhưng phải quản lý việc cấp phát.
- **Dynamic provisioning:** cấp theo PVC/class, giảm thao tác thủ công nhưng cần provisioner/backend hoạt động và quyền/cấu hình phù hợp.
- **CSI:** giao diện chuẩn tích hợp storage, không phải một disk hoặc bảo đảm HA. PV trong lab này dùng source `local`, không phải CSI; không suy mọi PV phải có `spec.csi`.

### 2.2 Field cần đọc

| Resource / field | Ý nghĩa và cạm bẫy |
|---|---|
| PVC `metadata.name`, `metadata.namespace` | Tên claim và phạm vi; class/PV toàn cluster không làm PVC dùng xuyên namespace. |
| PVC `spec.storageClassName` | Tên class cụ thể; đổi chuỗi không tạo class, driver hoặc backend. |
| PVC `spec.resources.requests.storage` | Yêu cầu dung lượng để cấp/chọn volume phù hợp, không tự chứng minh disk được reserve hay enforce quota. |
| PVC `spec.accessModes` | Yêu cầu kiểu truy cập; `ReadWriteOnce` là đọc/ghi từ một node, không đồng nghĩa chỉ một Pod. Đào sâu ở Bài 20. |
| StorageClass `provisioner` | Implementation chịu trách nhiệm provisioning. |
| StorageClass `parameters` | Cấu hình riêng của provisioner; không có bộ key chung cho mọi provider. Class lab không khai báo parameters. |
| StorageClass `volumeBindingMode` | Thời điểm xét bind/provisioning và quan hệ với placement của Pod. |
| StorageClass `reclaimPolicy` | Chính sách thu hồi được PV cấp động kế thừa; `Delete` không phải bảo đảm giữ dữ liệu khi xóa claim. Chưa thử xóa PVC/PV trong bài này. |
| Pod `spec.volumes[].persistentVolumeClaim.claimName` | Tham chiếu tên PVC, không phải tên PV/class hoặc label. |
| Pod `spec.volumes[].name` ↔ container `volumeMounts[].name` | Tên volume nội bộ phải khớp; không cần giống tên PVC. Không khớp là cấu hình Pod không hợp lệ. |
| Container `volumeMounts[].mountPath` | Đường ứng dụng dùng; có PVC không bảo vệ file ghi ngoài mount. |
| Pod `spec.nodeSelector` | Điều kiện scheduling; giữ scheduler tham gia khi dùng delayed binding, không gán `nodeName` để bỏ qua scheduler. |
| PVC `spec.volumeName` ↔ PV `spec.claimRef` | Hai chiều liên kết; kiểm namespace/name và PVC UID, không chỉ tên. |
| PV `spec.local.path`, `spec.nodeAffinity` | Nguồn storage cụ thể và giới hạn node thực tế của volume này. Không chỉ nhìn `spec.hostPath` hoặc `spec.csi`. |

### 2.3 Ba cách chọn class không tương đương

| Khai báo trong PVC | Hành vi |
|---|---|
| `storageClassName: local-path` | Chọn chính xác class này; tên chỉ có ý nghĩa trong hợp đồng của cluster đang dùng. |
| Bỏ field | Cho phép dùng default class nếu được cung cấp; không đồng nghĩa chủ đích không có class. |
| `storageClassName: ""` | Chủ đích không dùng class/default và không yêu cầu dynamic provisioning qua class; vẫn có thể bind PV không có class nếu phù hợp. |

Chọn rõ một tên class không tồn tại **không tự fallback sang default**. Các biến thể bỏ field/chuỗi rỗng được học qua cấu hình và trắc nghiệm, chưa triển khai trong lab.

### 2.4 Binding mode và Pending

- **Immediate:** xét bind/provisioning khi có PVC, trước khi biết điều kiện đặt Pod; với storage giới hạn theo topology có thể tạo xung đột với placement.
- **WaitForFirstConsumer:** chờ Pod dùng claim để xét storage cùng điều kiện scheduling; chưa có consumer thì `Pending` có thể đúng thiết kế.
- Scheduler tham gia quyết định vị trí; provisioner thực hiện cấp storage. Binding mode không tự tạo khả năng backend chưa có.
- Không dùng `Pod.spec.nodeName` với thí nghiệm delayed binding; dùng selector/affinity đã hiểu và kiểm kết quả thực tế.

Tình huống Immediate xung đột zone và bypass scheduler chỉ học lý thuyết/trắc nghiệm, chưa tạo thí nghiệm mới.

### 2.5 Recovery đúng phạm vi

PVC `storageclass-missing` đã có tên class tường minh. `Pending` không làm `storageClassName` thành field được sửa tùy ý; không đổi tên class rồi apply để xem như đã chuyển backend.

Trong lab, tạo PVC **mới** `storageclass-recovered` chọn `local-path`, giữ claim lỗi làm đối chứng. Đây là recovery dependency, **không sửa claim cũ, không migration/copy dữ liệu và không xóa PVC để chữa lỗi**.

Ngoài lab, nếu yêu cầu class là đúng nhưng platform chưa cung cấp thì cần class/provisioner/backend phù hợp; không chọn đại default chỉ để được `Bound`.

## 3. Inventory, version và scaffold

- Client: `/usr/local/bin/kubectl` **v1.33.9**; API server **v1.33.6+k3s1**. Dùng kubeconfig `~/.kube/config`, context/namespace tường minh; không dump credential hoặc đổi current context.
- API Pod/PVC `v1` đã kiểm hỗ trợ. Ba node ARM64; snapshot chốt đều Ready, không cordon/taint, Memory/Disk/PIDPressure False.
- StorageClass `local-path`, UID `f7dd82a9-be6e-4f15-80f6-fa7cefd53458`: default `true`, provisioner `rancher.io/local-path`, `WaitForFirstConsumer`, reclaim `Delete`, annotation `defaultVolumeType: local`.
- Deployment `kube-system/local-path-provisioner` Ready 1/1, image `rancher/local-path-provisioner:v0.0.32`.
- ConfigMap `local-path-config`: default node path `/var/lib/rancher/k3s/storage`; helper image `rancher/mirrored-library-busybox:1.36.1`. Chỉ đọc cấu hình cần thiết, không cài/sửa add-on.
- Metadata registry trước consumer xác nhận `linux/arm64/v8` cho cả image Pod và helper hiện có. Image Pod pin:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

Manifest ARM64 BusyBox được registry trả về: `sha256:d82c2ab94640ded77cf76514ce6a84870761105058a4a9e51b05a8a79be97a6c`. Metadata registry không tự chứng minh node đã pull mới; Event của consumer ghi image **already present on machine**.

| Scaffold | Cấu hình / mục đích |
|---|---|
| [01-pvc.yaml](../thuc-hanh/19-storageclass/01-pvc.yaml) | `storageclass-data`, class `local-path`, RWO/128Mi; tạo trước consumer. |
| [02-consumer.yaml](../thuc-hanh/19-storageclass/02-consumer.yaml) | Naked Pod `storageclass-consumer`, worker mount volume `output` tại `/data`, claimName `storageclass-data`, selector hostname agent-0. |
| [03-missing-class-pvc.yaml](../thuc-hanh/19-storageclass/03-missing-class-pvc.yaml) | Claim riêng `storageclass-missing`, class cố ý không tồn tại `lesson19-no-such-class`, RWO/128Mi. |
| [04-recovered-pvc.yaml](../thuc-hanh/19-storageclass/04-recovered-pvc.yaml) | Claim mới `storageclass-recovered`, class `local-path`, RWO/128Mi; không có consumer. |

Consumer chỉ `sleep 86400`, `Always`, grace period 5 giây, không mount API token/declared env/envFrom. Requests CPU/RAM `25m/32Mi`, limits `100m/64Mi`; không phải quota của PVC. Lệnh startup không tạo marker.

Bốn file được chuẩn bị đúng lúc, qua client dry-run/schema; sau từng dry-run, target mới vẫn chưa tồn tại live. Học viên tự chạy lệnh create, mentor không triển khai thay.

Theo README đúng version, local-path-provisioner v0.0.32 chưa hỗ trợ volume capacity limit. `128Mi` không chứng minh chặn ghi tại 128Mi; không thực nghiệm ghi đầy disk.

## 4. Bằng chứng thực hành

Mọi giờ dưới đây là **17/11/2026, Asia/Ho_Chi_Minh**. Phân biệt timestamp tạo resource từ API, snapshot mentor kiểm tra và output học viên đã quan sát; không dựng lại thứ tự mọi lệnh từ snapshot cuối.

### 4.1 Identity khi chốt

| Resource | UID | Trạng thái / quan hệ |
|---|---|---|
| Namespace `de-lab` | `6d2e69f9-ada2-4699-af0d-2c98a3974710` | Active. |
| PVC `storageclass-data` | `d74edbd0-2b91-40c5-8335-426125358ff1` | Bound, class local-path, 128Mi/RWO, Filesystem. |
| PV `pvc-d74edbd0-2b91-40c5-8335-426125358ff1` | `bc12547c-8267-4e53-ac93-72f790f49fad` | Bound, claimRef đúng namespace/name/UID của claim chính, reclaim Delete. |
| Pod `storageclass-consumer` | `5b3d5afb-d56f-4081-bd49-d959fa27d5e3` | Running/Ready, agent-0, restart 0, không controller owner/deletionTimestamp. |
| PVC `storageclass-missing` | `a263395c-16e2-4be8-bd61-45f3b15b3044` | Pending, class không tồn tại, không volumeName/PV/consumer. |
| PVC `storageclass-recovered` | `2f8240e3-96d7-4135-9905-d9ea8970aacf` | Pending, class local-path, chờ consumer; không volumeName/PV/consumer. |

Container ID worker: `fb5d0fc21b1e9f714c8885aed358ebb0f8cb72098d0d60377839ef97d24c9f54` (prefix runtime `containerd://`). Runtime imageID khớp index digest BusyBox đã pin.

### 4.2 Từ claim chưa có consumer tới PV thực tế

- **17:07:19:** preflight chưa có PVC trong de-lab hoặc PV trong lượt kiểm toàn cluster.
- PVC chính tạo **17:18:46**. Snapshot **17:20:28**: Pending, volumeName trống, không consumer/PV; Event `Normal / WaitForFirstConsumer / waiting for first consumer to be created before binding`.
- Pod tạo **20:58:04**, PV tạo **20:58:16**, container chạy từ **20:58:18**, theo metadata API.
- Mentor kiểm **21:01:40**: cùng PVC UID đã Bound, Pod Ready trên agent-0/restart 0. Events của claim có Provisioning/ProvisioningSucceeded; Pod có Scheduled/Pulled/Created/Started.
- Source thực tế là **`spec.local.path`**, không phải `hostPath` hoặc `csi`. Annotation class `defaultVolumeType: local` phù hợp với source quan sát được.

Trích spec PV đã kiểm:

```yaml
spec:
  local:
    path: /var/lib/rancher/k3s/storage/pvc-d74edbd0-2b91-40c5-8335-426125358ff1_de-lab_storageclass-data
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - k3d-de-k3d-agent-0
```

Đây là đường filesystem trên node k3d agent-0, không mặc nhiên là thư mục cùng tên trên Mac. Vị trí Pod của provisioner không quyết định vị trí byte; phải đọc source/affinity của PV.

### 4.3 Marker và readback

- **21:23:03:** mentor kiểm chỉ đọc `/proc/self/mountinfo`, có `MOUNTPOINT=/data`; file `/data/lesson19-marker.txt` chưa tồn tại, identity ổn định.
- Lệnh giao cho học viên ghi một lần có guard namespace/UID, từ chối file/link đã tồn tại và dùng noclobber, kèm lệnh đọc riêng. Học viên báo đã làm; mentor không ghi marker và không suy toàn bộ flags/thứ tự lệnh thực chạy chỉ từ snapshot.
- **21:47:42:** mentor đọc đúng marker, cùng Pod/PVC/PV UID; tiếp tục kiểm khớp ở các lượt đối chứng/recovery và snapshot chốt.
- Marker là regular file, không symlink, **50 byte** gồm newline:

```text
lesson19-pvc-d74edbd0-2b91-40c5-8335-426125358ff1
```

Readback chứng minh một lần ghi/đọc từ volume đang mount. Chưa thử persistence qua Pod replacement, đổi node, node/disk loss hoặc backup/restore trong Bài 19.

### 4.4 Đối chứng thiếu class và recovery

- Claim lỗi tạo **21:57:01**. Học viên quan sát Pending và message class not found; mentor kiểm **21:59:11**, đúng UID và không có PV/consumer.
- Event thực tế: `Warning / ProvisioningFailed / storageclass.storage.k8s.io "lesson19-no-such-class" not found`. Class không tồn tại, không có PV cấp sẵn mang class này; đây là case dynamic provisioning thiếu dependency.
- Claim recovery **mới** tạo **22:08:11**. Mentor kiểm **22:09:49**: class local-path, Pending, Event `Normal / WaitForFirstConsumer / waiting for first consumer to be created before binding`, chưa có consumer/PV.
- Claim lỗi không bị đổi class hoặc xóa để chữa lỗi; claim chính và marker không bị thay thế. Recovery đạt vì chọn đúng dependency và trạng thái chờ đúng, không phải vì mọi PVC đã Bound.
- **22:24:09:** kiểm chốt sau review cuối: ba claim giữ UID/trạng thái trên, toàn cluster có một PV; Pod chính Ready/restart 0, marker đúng, ba node Ready/ARM64, không cordon/taint/pressure. Giữ fixture, không cleanup.

## 5. Lệnh tái quan sát → snapshot → cách đọc

Các lệnh dưới **chỉ đọc**, không yêu cầu chạy lại create/ghi marker. Tên/UID và trạng thái có thể đổi về sau; xác nhận lại trước khi tái dùng resource, không buộc snapshot khớp mãi.

```bash
K=(/usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" --context k3d-de-k3d -n de-lab)

"${K[@]}" config get-contexts k3d-de-k3d -o name
"${K[@]}" get namespace de-lab -o custom-columns='NAME:.metadata.name,PHASE:.status.phase'

"${K[@]}" get pvc storageclass-data storageclass-missing storageclass-recovered \
  -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,CLASS:.spec.storageClassName'
```

Snapshot chốt:

```text
k3d-de-k3d
NAME     PHASE
de-lab   Active

NAME                     STATUS    CLASS
storageclass-data        Bound     local-path
storageclass-missing     Pending   lesson19-no-such-class
storageclass-recovered   Pending   local-path
```

Nhìn STATUS cùng CLASS, rồi xem Events; không kết luận lỗi chỉ từ Pending. Các bảng trên dùng **custom columns**.

```bash
"${K[@]}" describe pvc storageclass-missing
"${K[@]}" describe pvc storageclass-recovered
```

Trong bảng Events của từng claim, snapshot có các hàng dưới — đã lược Age/From:

```text
Type      Reason                 Message
Warning   ProvisioningFailed     storageclass.storage.k8s.io "lesson19-no-such-class" not found
Normal    WaitForFirstConsumer   waiting for first consumer to be created before binding
```

Hàng Warning thuộc claim missing, hàng Normal thuộc claim recovered. Mentor còn lọc Events bằng `involvedObject.uid` của từng PVC để tránh nhầm lượt resource.

```bash
PV=$("${K[@]}" get pvc storageclass-data -o jsonpath='{.spec.volumeName}')
"${K[@]}" get pv "$PV" -o yaml

"${K[@]}" get pod storageclass-consumer \
  -o custom-columns='NAME:.metadata.name,PHASE:.status.phase,READY:.status.containerStatuses[0].ready,NODE:.spec.nodeName'
```

Với PV, đọc claimRef namespace/name/UID, storageClassName, **local.path** và nodeAffinity.required; PV là resource toàn cluster dù K có `-n de-lab`. Snapshot Pod:

```text
NAME                    PHASE     READY   NODE
storageclass-consumer   Running   true    k3d-de-k3d-agent-0
```

Kiểm mount và marker của fixture đã xác minh, không đọc file/env/credential khác:

```bash
"${K[@]}" exec storageclass-consumer -c worker -- \
  awk '$5 == "/data" {print "MOUNTPOINT=" $5}' /proc/self/mountinfo

"${K[@]}" exec storageclass-consumer -c worker -- \
  cat /data/lesson19-marker.txt
```

Snapshot:

```text
MOUNTPOINT=/data
lesson19-pvc-d74edbd0-2b91-40c5-8335-426125358ff1
```

Mentor kiểm trước khi đọc: đúng Pod/container/config, claim/PV UID, marker là regular file không symlink, đúng độ dài và nội dung dữ liệu giả. Không dump logs, env, Secret hoặc kubeconfig.

## 6. Review và lỗi đã xử lý

| Lượt | Câu trả lời | Kết quả |
|---|---|---|
| Vai trò provisioner / namespace PVC | `1B, 2C` | Đúng 2/2. |
| WFFC chờ consumer / Immediate xung đột topology | `1B, 2A` | Đúng 2/2. |
| Class rỗng / capacity limit local-path | `1C, 2B` | Đúng 2/2. |
| Tên volume/mount / vị trí provisioner khác nơi giữ byte | `1B, 2C` | Đúng 2/2. |
| Local PV không bắt buộc có CSI | `B` | Đúng. |
| Class tường minh không tồn tại không fallback default | `C` | Đúng. |
| PVC Pending không sửa class tùy ý; recovery bằng claim mới | `B` | Đúng. |
| Review cuối: tên class không thay việc xác nhận implementation/backend ngoài lab | `C` | Đúng. |

Tổng **12/12**, không ghi nhận câu trả lời concept sai. Không coi các nhầm lẫn được mentor chủ động cảnh báo là lỗi học viên.

Một lỗi thực hành đã được học viên tự sửa: đang ở thư mục `19-storageclass/` nhưng dùng `-f thuc-hanh/19-storageclass/03-missing-class-pvc.yaml` nên client không tìm thấy file. Chuyển sang `-f 03-missing-class-pvc.yaml` tạo được PVC. Đây là lỗi relative path theo cwd, không phải lỗi storage; lần đầu chưa tạo resource. Lệnh tạo recovery dùng đường dẫn tuyệt đối dưới `$HOME/Downloads/k8s-practice/roadmap-k3d/`.

Class không tồn tại là lỗi **cố ý của thí nghiệm**, không phải YAML sai cấu trúc. Không sửa class của claim chính hoặc xóa PVC để vượt lỗi.

## 7. Lab làm giúp ↔ ngoài lab, liên hệ DE và giới hạn

- **Lab:** K3s đã có local-path provisioner/helper và cấu hình đường node. PVC/StorageClass là API; add-on mới thực hiện chuẩn bị volume. PV thực tế trong bài dùng local path với node affinity agent-0.
- **Ngoài lab:** on-prem cần backend/provisioner hoặc PV cấp sẵn; cloud managed có thể làm sẵn một phần CSI/controller/backend. Vẫn phải xác nhận tên class, provisioner/parameters, topology, modes, capacity/quota, reclaim/expansion và quyền thực tế.
- **Trade-off:** static giúp kiểm soát storage cấp sẵn nhưng tăng quản lý thủ công; dynamic giảm thao tác từng volume nhưng phụ thuộc controller/backend. Khi storage giới hạn topology, ưu tiên WFFC nếu implementation hỗ trợ; Immediate vẫn có trường hợp phù hợp.
- **Tên class không phải SLA:** class cùng tên trên hai cluster không bảo đảm cùng backend/đặc tính. CSI không tự tạo HA; Bound không chứng minh backup, quota vật lý hoặc truy cập từ mọi node.
- **Debug đúng tầng:** đường ứng dụng ghi → volumeMount/volume/claimName → namespace/PVC status và Events → class/provisioner/binding mode → PV source/affinity và placement → backend/mount/readback. Thiếu class khác với class tồn tại nhưng provisioner/backend chưa đáp ứng.
- **Giới hạn local:** node k3d là container chung host/runtime/disk của môi trường local. Đường node không mặc nhiên là đường Mac, và ba node Ready không tạo ba failure domain vật lý độc lập.

| Nhu cầu DE | Điều cần xác nhận với platform |
|---|---|
| Output/checkpoint cần tồn tại độc lập với Pod | Đường ghi thực tế nằm trong persistent mount; PVC/PV/backend và quyền truy cập phù hợp. |
| Dung lượng và hiệu năng | Capacity được enforce/reserve thế nào, IOPS/throughput và quota; không coi marker nhỏ là benchmark hoặc 128Mi của local-path là hard limit. |
| Placement và khả năng phục hồi | Topology/node/zone, modes, dữ liệu khi mất node, reclaim và quy trình vận hành. |
| Dữ liệu quan trọng | Backup/restore, owner, mục tiêu phục hồi; không suy từ chữ Bound. |
| Báo lỗi Pending | Context/namespace/PVC UID, tên class, consumer/placement và Events đã lọc; không gửi credential. |

Các cấu hình ngoài lab chỉ được giải thích/review, không triển khai production. Chưa thực nghiệm static PV, backend/CSI khác, class nil/chuỗi rỗng, Immediate, đổi node/Pod replacement với PVC, mất node/disk/host, enforce quota, expansion, reclaim deletion, backup/restore hoặc ETL thật.

## 8. Bàn giao

Giữ ba PVC, một PV, một Pod và bốn scaffold như bảng identity. Không có cleanup bắt buộc hoặc câu review đang chờ của Bài 19. Claim missing còn Pending do lỗi cố ý, claim recovered còn Pending do chờ consumer; không mở lại bài chỉ để ép cả hai Bound hoặc tự xóa chúng.

Chờ **Bài 20 — Access modes và chuyển node**, chưa giảng hoặc tạo scaffold bài mới. Không chạy lại lệnh ghi marker hoặc create chỉ để xem output; khi tái dùng tài nguyên phải kiểm identity/status live.

## 9. Nguồn đã đối chiếu

- [Kubernetes v1.33 — Persistent Volumes](https://v1-33.docs.kubernetes.io/docs/concepts/storage/persistent-volumes/).
- [Kubernetes v1.33 — StorageClasses](https://v1-33.docs.kubernetes.io/docs/concepts/storage/storage-classes/), gồm default class, binding mode và parameters.
- [Kubernetes v1.33 — CSI volumes](https://v1-33.docs.kubernetes.io/docs/concepts/storage/volumes/#csi).
- [local-path-provisioner v0.0.32 — README](https://github.com/rancher/local-path-provisioner/blob/v0.0.32/README.md): node paths, volume types, helper và giới hạn capacity.
- [Controller v1.33.6 — chờ consumer và provisioning](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/controller/volume/persistentvolume/pv_controller.go), [delay binding helper](https://github.com/kubernetes/kubernetes/blob/v1.33.6/staging/src/k8s.io/component-helpers/storage/volume/pv_helpers.go).
- [Default class admission v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/plugin/pkg/admission/storage/storageclass/setdefault/admission.go).
- [PVC update validation v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/apis/core/validation/validation.go#L2395-L2441): case class đã khai báo tường minh; không dùng ngoại lệ gán class từ nil để suy ra đổi tên class tùy ý.
- Metadata registry đã đọc trước lab: [BusyBox 1.37.0](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0), [helper BusyBox 1.36.1](https://hub.docker.com/v2/repositories/rancher/mirrored-library-busybox/tags/1.36.1).
