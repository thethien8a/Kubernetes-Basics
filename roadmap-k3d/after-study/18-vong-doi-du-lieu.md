# Tổng kết Bài 18 — Các vòng đời của dữ liệu

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/18-vong-doi-du-lieu.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/19-storageclass.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-17**, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Review:** tám lựa chọn trắc nghiệm đúng; review cuối `1C, 2A` đạt 2/2.
- **Thực hành:** đối chứng container restart trong cùng Pod và Pod replacement, mỗi thí nghiệm có baseline marker riêng.
- **Kiểm chốt độc lập:** **16:16:25 ngày 17/11/2026**; Pod mới Running/Ready, restart 0, bốn marker của hai thí nghiệm đều không còn.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`, một naked Pod `data-lifecycle-lab`; chỉ dùng dữ liệu giả.
- **Ranh giới:** học viên tự apply, ghi marker, dừng đúng container rồi xóa/tạo lại Pod. Mentor chuẩn bị scaffold, kiểm schema và kiểm tra chỉ đọc; không thay workload/node hoặc đọc credential.
- **Khi đóng bài:** giữ Pod mới và [scaffold](../thuc-hanh/18-vong-doi-du-lieu/01-pod.yaml), không ghi thành đã cleanup. Bài gốc không yêu cầu xóa fixture cuối bài. Chưa mở Bài 19.

## 1. Challenge và tiêu chí đã đạt

1. Phân biệt nội dung có sẵn trong image với file ứng dụng ghi vào writable layer.
2. Tạo hai marker khác nhau tại đường không mount volume và đường mount `emptyDir`; không đóng gói marker vào image hoặc để startup script tạo lại.
3. Tạo lại container có kiểm soát, đối chiếu Pod UID, container ID, restart count và marker.
4. Chuẩn bị hai marker mới cho thí nghiệm thứ hai rồi thay Pod; đối chiếu identity và dữ liệu trước/sau.
5. Lập bảng vòng đời writable layer/emptyDir/PVC, tách thực hành đã kiểm chứng khỏi dự đoán.
6. Đọc đường ghi thực tế, volume source, mount và budget scratch; nêu yêu cầu storage cần trao đổi với DevOps.

Hai đối chứng runtime đều đạt. PVC, node/disk loss, `medium: Memory` và xử lý vượt storage limit chỉ học qua lý thuyết/cấu hình/tình huống, không ghi thành đã thực nghiệm.

## 2. Mental model đã học

### 2.1 Image, writable layer và volume là các nguồn dữ liệu khác nhau

- File như `/app/transform.py` được đóng gói trong image là nội dung ban đầu để tạo container.
- Ghi file vào writable layer khi chạy không làm thay đổi image. Khi Kubernetes tạo lại container, writable layer mới không phải bản phục hồi phần ghi của container cũ.
- File từ image lại xuất hiện vì dùng image để tạo container, không phải bằng chứng persistence của dữ liệu ứng dụng.
- Volume được mount vào một đường dẫn của container. Loại nguồn volume quyết định vòng đời, không phải việc đường dẫn có tên `/data`, `/scratch` hay `/tmp`.
- Ứng dụng phải thật sự ghi vào đường đã mount. Có PVC ở `/data` không bảo vệ file ứng dụng vẫn ghi vào `/tmp` không mount volume.

Trong bài, “container restart” là Kubernetes tạo lại container, không phải chỉ chạy lại một tiến trình bên trong container vẫn tồn tại.

### 2.2 `emptyDir` thuộc về Pod

```text
Pod UID A
├── Container và writable layer riêng
└── emptyDir được mount tại /scratch
```

- Container được tạo lại trong cùng Pod: UID A giữ nguyên, container ID đổi; `emptyDir` vẫn thuộc Pod A.
- Xóa Pod A rồi tạo Pod B: Pod B có UID khác và `emptyDir` mới, kể cả cùng tên và cùng node.
- Pod name hoặc node name không thay thế Pod UID khi phân biệt hai thí nghiệm.
- `restartPolicy: Always` cho kubelet tạo lại container trong Pod còn tồn tại; nó không tự tạo lại một naked Pod đã bị xóa.
- Marker có cùng nội dung sau restart/replacement chưa đủ chứng minh persistence nếu image hoặc startup script có thể tái tạo nó.

### 2.3 PVC không phải chính ổ đĩa — phần lý thuyết

```text
Ứng dụng ghi /data/result.csv
  → volume mount /data
  → PVC
  → PV
  → storage backend thực sự giữ byte
```

PVC là yêu cầu sử dụng storage; PV biểu diễn storage được cấp, có vòng đời độc lập với riêng một Pod. Backend mới là nơi dữ liệu nằm.

Pod mới có thể dùng lại dữ liệu nếu PVC/PV được giữ, backend còn dữ liệu và placement/mount phù hợp. Điều này không tự bảo đảm:

- chịu mất node hoặc disk;
- truy cập được từ mọi node;
- có replication, backup hoặc restore đã kiểm chứng;
- giữ dữ liệu sau mọi thao tác xóa PVC/PV.

Trích đoạn đã giảng, **chưa triển khai PVC `etl-output`**:

```yaml
spec:
  containers:
    - name: worker
      volumeMounts:
        - name: output
          mountPath: /data
  volumes:
    - name: output
      persistentVolumeClaim:
        claimName: etl-output
```

`output` là tên volume nội bộ trong Pod; `etl-output` là tên PVC cùng namespace. Chúng không cần giống nhau. Khai báo `claimName` trong Pod không tự tạo PVC. Provisioning sẽ học ở Bài 19.

### 2.4 Scratch không miễn phí — phần cấu hình và dự đoán

| Lựa chọn | Nguồn tài nguyên | Trade-off |
|---|---|---|
| `emptyDir` medium mặc định | Storage backing của node, thường là disk/SSD | Cạnh tranh dung lượng/I/O với các nguồn sử dụng node storage khác. |
| `emptyDir.medium: Memory` | tmpfs, dùng RAM | Có thể nhanh, nhưng file tính vào memory usage của container ghi chúng; không thay vòng đời Pod. |

- `resources.requests.ephemeral-storage`: nhu cầu để scheduler xét placement, không phải số đo usage hoặc một partition cấp riêng.
- `resources.limits.ephemeral-storage`: kubelet theo dõi để xử lý/evict khi vượt, với điều kiện filesystem/layout hỗ trợ việc đo.
- Với Pod một container dùng emptyDir mặc định: ngân sách tổng xét writable layer, container logs và emptyDir. EmptyDir chưa tới `sizeLimit` không chứng minh tổng usage còn trong limit.
- `emptyDir.sizeLimit` giới hạn riêng volume, không cấp sẵn disk và không bảo đảm node không hết chỗ vì nguồn khác.
- Không coi ephemeral-storage limit là cơ chế chặn ghi tức thì ở đúng byte giới hạn.
- Memory-backed emptyDir tính vào memory usage, không phải local ephemeral-storage usage; phải tính chung RAM ứng dụng và file tmpfs.

Ví dụ trắc nghiệm dùng limit 128Mi, writable layer/logs 100Mi và emptyDir 40Mi: tổng 140Mi có thể dẫn tới eviction nếu kubelet đo/enforce được. Đây là phép dự đoán, không phải số đo hoặc cấu hình runtime của Pod lab.

## 3. Scaffold, phiên bản và field quan trọng

Chỉ tạo [01-pod.yaml](../thuc-hanh/18-vong-doi-du-lieu/01-pod.yaml) đúng lúc sau lý thuyết/checkpoint và preflight. Client dry-run/schema thành công; Pod chưa tồn tại sau dry-run. Kiểm cú pháp shell không thực thi script ghi marker trên Mac.

- API Pod: `v1`; `/usr/local/bin/kubectl` **v1.33.9**, API server **v1.33.6+k3s1**.
- Ba node ARM64. Registry manifest được đọc trước lab, xác nhận `linux/arm64/v8` và index digest cho image pin:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

- Manifest ARM64 được registry trả về: `sha256:d82c2ab94640ded77cf76514ce6a84870761105058a4a9e51b05a8a79be97a6c`.
- Preflight namespace `de-lab` Active; không có LimitRange, ResourceQuota hoặc NetworkPolicy trong lượt kiểm. Chưa có Pod cùng tên hoặc `lesson=18`.
- Runtime node: containerd `2.1.5-k3s1.33`. Executable `/bin/crictl` đã được kiểm version/help và lọc metadata để xác nhận đúng Pod/container trước khi giao thao tác; dùng trực tiếp `crictl`, không suy cú pháp từ bản tài liệu khác.

| Field | Giá trị / quan hệ đã đọc |
|---|---|
| Pod `metadata.name`, `namespace`, labels | `data-lifecycle-lab`, `de-lab`, `lesson: "18"`; không dùng selector rộng để xóa. |
| `spec.restartPolicy` | `Always`; áp dụng cho container trong Pod, không thay thế controller tạo Pod. |
| Container `command` | `["sleep", "86400"]`; không viết marker lúc khởi động. Sau 24 giờ sleep có thể kết thúc và container được chạy lại trong cùng Pod. |
| Container `image`, `imagePullPolicy` | Pin version/digest, `IfNotPresent`; không dùng image import từ Mac. |
| `spec.volumes[].name`, `emptyDir` | `scratch`, medium mặc định, `sizeLimit: 16Mi`; không có PVC/hostPath. |
| Container `volumeMounts[].name`, `mountPath` | `scratch` nối tới volume trên và mount `/scratch`; `/tmp` không mount volume. |
| Container requests | CPU `25m`, memory `32Mi`, ephemeral-storage `32Mi`; budget lab, không phải benchmark ETL. |
| Container limits | CPU `100m`, memory `64Mi`, ephemeral-storage `64Mi`. |
| `spec.automountServiceAccountToken` | `false`; chương trình không cần gọi API, không đọc token để review. |
| `spec.terminationGracePeriodSeconds` | `5`; phạm vi Pod test với dữ liệu giả, không coi là cấu hình shutdown chung cho database. |
| Placement / owner | Không thêm node selector; cả hai lượt Pod thực tế ở agent-1. Không controller owner, không thay scheduling của node. |

## 4. Bằng chứng thực hành

Tất cả giờ dưới là **17/11/2026, giờ Việt Nam**. Học viên gửi transcript thao tác/quan sát; mentor còn kiểm tra chỉ đọc ở từng baseline và sau thay đổi. Không dùng snapshot cuối để dựng lại lịch sử đã không quan sát.

### 4.1 Identity

| Pha | Pod UID | Container ID (không gồm prefix `containerd://`) | Restart |
|---|---|---|---|
| Baseline đầu | `daf9abdb-83c6-46e6-a72c-cfa8a692a806` | `4f83c0658078905cb8b8549ecc663380cb198143c89c78a7a387fa5e35ac0670` | 0 |
| Sau container restart | Giữ UID `daf9abdb-83c6-46e6-a72c-cfa8a692a806` | `1d75e94d3ea67170b2490dd09cb87ce3b6bd8ed53ea5534570f9a1fb6fba6672` | 1 |
| Sau Pod replacement / khi đóng bài | `a70d309f-8fda-4e74-8e7f-b6b360573623` | `64a15ccc4170ea3f84f4b0213b58d6aaac41e7217f410bd672bb3244f4b7d060` | 0 |

Cả ba pha đều ở `k3d-de-k3d-agent-1`. Vì vậy thí nghiệm replacement chứng minh emptyDir mới không kế thừa marker ngay cả khi không đổi node.

### 4.2 Thí nghiệm container restart

- Pod đầu tạo **15:30:57**, container chạy từ **15:30:58**.
- Mentor kiểm baseline lúc **15:32:50**: Running/Ready, restart 0, cấu hình khớp scaffold, hai marker đúng:
  - `/tmp/lesson18-layer.txt` = `lesson18-layer-before-restart`.
  - `/scratch/lesson18-volume.txt` = `lesson18-emptydir-before-restart`.
- Trước khi giao dừng container, mentor đối chiếu runtime labels: đúng namespace, Pod name/UID và container `worker`; chỉ đọc metadata đã lọc, không in raw inspect.
- Học viên chạy một lần `crictl stop --timeout 2` với đúng full container ID đầu, qua Docker context `orbstack` vào agent-1. Không dừng node, Pod sandbox hoặc container khác.
- Lần chạy cũ kết thúc **15:41:17**, exit `137`, reason `Error`; container mới chạy từ **15:41:17**. Đây là lượt dừng có chủ đích, không suy OOM chỉ từ exit 137.
- Mentor kiểm sau lúc **15:43:10**: cùng Pod UID, container ID mới, restart 1/Ready; marker writable layer mất, marker emptyDir còn nguyên. Identity ổn định trong phép đọc.

### 4.3 Thí nghiệm Pod replacement

Không lấy marker writable layer đã mất ở thí nghiệm trước làm baseline thứ hai. Học viên tạo hai marker mới với tên riêng, giữ marker cũ:

- `/tmp/lesson18-layer-replace.txt` = `lesson18-layer-before-replace`.
- `/scratch/lesson18-volume-replace.txt` = `lesson18-emptydir-before-replace`.

Mentor kiểm **15:49:31**: cả hai marker mới đúng, vẫn Pod UID đầu/container ID thứ hai/restart 1/Ready, không owner hoặc deletionTimestamp.

Học viên dùng guard context/namespace/UID/container ID, tự xóa đúng Pod rồi `create` lại từ cùng scaffold; chờ Ready. Không ghi lại marker sau khi tạo Pod mới.

- Pod mới tạo **16:05:09**, container chạy từ **16:05:10**.
- Mentor kiểm **16:06:50**: UID mới, Running/Ready, restart 0, cùng agent-1; hai marker replacement đều mất. Hai marker của thí nghiệm đầu cũng mất.
- Events của đúng UID mới có `Scheduled`, `Pulled`, `Created`, `Started`. `Pulled` không tự chứng minh đã tải image mới từ registry thay vì dùng cache.
- Kiểm chốt **16:16:25** sau review: cùng UID/container ID mới, restart 0/Ready, cả bốn marker vẫn không còn; cấu hình không đổi.

Việc tạo lại Pod khỏe sau xóa đã đạt. Đây là thao tác thủ công trong thí nghiệm, không phải controller tự recovery hoặc bằng chứng HA.

## 5. Lệnh tái quan sát → snapshot → cách đọc

Các lệnh dưới là **chỉ đọc**, không yêu cầu chạy lại stop/delete/create hoặc ghi marker. Dùng cùng terminal hỗ trợ shell array:

```bash
K=(/usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" --context k3d-de-k3d -n de-lab)

"${K[@]}" config get-contexts k3d-de-k3d -o name
"${K[@]}" get namespace de-lab -o custom-columns='NAME:.metadata.name,PHASE:.status.phase'

"${K[@]}" get pod data-lifecycle-lab -o custom-columns='UID:.metadata.uid,RESTARTS:.status.containerStatuses[0].restartCount,READY:.status.containerStatuses[0].ready,NODE:.spec.nodeName'
```

Snapshot khi đóng bài:

```text
k3d-de-k3d
NAME     PHASE
de-lab   Active

UID                                    RESTARTS   READY   NODE
a70d309f-8fda-4e74-8e7f-b6b360573623   0          true    k3d-de-k3d-agent-1
```

Context được chỉ định tường minh, không đổi current context. Nhìn `UID`, không chỉ tên Pod; `RESTARTS=0` là trạng thái của container trong Pod mới, không xóa lịch sử thí nghiệm của Pod cũ. Đây là custom columns, không phải bộ cột mặc định.

```bash
"${K[@]}" exec data-lifecycle-lab -c worker -- sh -ec '
for p in /tmp/lesson18-layer.txt /scratch/lesson18-volume.txt /tmp/lesson18-layer-replace.txt /scratch/lesson18-volume-replace.txt; do
  if [ -e "$p" ] || [ -L "$p" ]; then
    printf "%s=PRESENT\n" "$p"
  else
    printf "%s=MISSING\n" "$p"
  fi
done
'
```

Kết quả mentor kiểm ở snapshot chốt:

```text
/tmp/lesson18-layer.txt=MISSING
/scratch/lesson18-volume.txt=MISSING
/tmp/lesson18-layer-replace.txt=MISSING
/scratch/lesson18-volume-replace.txt=MISSING
```

Kết luận trước/sau dựa trên các baseline đã kiểm trong mục 4, không chỉ từ bốn dòng `MISSING` hiện tại. Khi tái quan sát về sau, xác nhận lại identity/trạng thái; không yêu cầu Pod UID hoặc restart count khớp mãi.

Lệnh lịch sử dừng container, **không chạy lại với ID cũ**:

```text
docker --context orbstack exec k3d-de-k3d-agent-1 crictl stop --timeout 2 4f83c0658078905cb8b8549ecc663380cb198143c89c78a7a387fa5e35ac0670
```

Trong bài, thao tác này chỉ được giao sau kiểm baseline và có guard UID/container ID/namespace. `--timeout 2` cho runtime chờ sau yêu cầu dừng nhẹ trước khi buộc dừng. Chờ restart count tăng lên 1 trước khi chờ Ready để tránh đọc trúng Ready cũ.

## 6. Bảng vòng đời và giới hạn minh chứng

| Sự kiện | File mới ghi vào writable layer | `emptyDir` | Persistent volume qua PVC |
|---|---|---|---|
| Tạo lại container trong cùng Pod, backend còn hoạt động | Mất — đã kiểm chứng | Giữ — đã kiểm chứng | Dự đoán giữ dữ liệu; chưa thử trong bài này. |
| Pod replacement | Mất — đã kiểm chứng | Mất — đã kiểm chứng, cùng node | Có thể dùng lại nếu giữ PVC/PV, backend còn dữ liệu và mount/placement hợp lệ; chưa thử. |
| Mất node/disk vĩnh viễn | Không bảo đảm giữ được; lý thuyết | Không bảo đảm giữ được; lý thuyết | Phụ thuộc backend/topology/cơ chế bảo vệ; chưa thử. |

Không thực nghiệm PVC/provisioning, di chuyển volume giữa node, mất node/disk/host, memory-backed emptyDir, vượt limit/eviction, backup/restore, Spark hoặc ETL thực tế. Không tạo thêm các thí nghiệm này thành việc phải làm bù để chốt Bài 18.

## 7. Lab làm giúp ↔ ngoài lab và hợp đồng với DevOps

- **Volume:** emptyDir là cơ chế Kubernetes chuẩn, không phải tiện ích `local-path` hoặc PVC do K3s cấp. Kubelet quản lý volume gắn với Pod và backing storage của node; bài này không dùng provisioner.
- **Hạ tầng lab:** k3d nodes là container trên Docker engine của OrbStack, cùng host/VM/disk/RAM. Ba node Ready không tạo ra ba failure domain độc lập hoặc ba lần dung lượng vật lý.
- **Dừng container:** Docker chỉ là đường vào node container của lab; `crictl` nói chuyện với runtime qua CRI. Ngoài lab, node/runtime access phải được platform cho phép, thường là trách nhiệm DevOps; không mặc định có Docker hoặc quyền admin cho DE. Cần đúng runtime endpoint và đối chiếu namespace/Pod UID/container ID trước thao tác.
- **Persistent storage ngoài lab:** on-prem có thể cần PV cấp sẵn hoặc provisioner/CSI/backend được cài và cấu hình; cloud managed có thể chuẩn bị một phần. Vẫn phải xác nhận class, topology, dung lượng, quyền mount, reclaim và bảo vệ dữ liệu; không coi mọi PVC là remote/replicated storage.
- **Thứ tự kiểm tra:** đường ứng dụng thật sự ghi → mountPath/volume name/source → Pod UID/container ID/sự kiện vừa xảy ra → nếu dùng PVC thì claim/PV/backend/topology → chính sách retention/backup và bằng chứng restore.

| Nhu cầu DE | Cấu hình / thông tin phải làm rõ |
|---|---|
| Scratch có thể tính lại | Có thể dùng emptyDir; ước lượng peak, chọn medium và requests/limits phù hợp; không biến bài test marker thành capacity benchmark. |
| Output cần sống qua Pod replacement | Nếu lưu filesystem, ghi đúng đường persistent volume; xác nhận PVC/PV/backend được giữ và truy cập được. |
| Checkpoint/log cần lưu lâu | Chọn nơi lưu và retention theo yêu cầu phục hồi; không mặc định mọi checkpoint/log đều phù hợp emptyDir. |
| Dữ liệu không thể mất | Thống nhất backup/restore, RPO/RTO và owner; persistence qua Pod replacement không thay thế các cam kết đó. |
| Báo sự cố | Gửi context/namespace/Pod UID, đường ghi, volume source, sự kiện trước/sau và bằng chứng đã lọc; không gửi token/Secret/raw env. |

Các cấu hình ngoài lab là tham khảo đã giải thích, không phải nền tảng production đã triển khai trong bài.

## 8. Review, điểm đã làm rõ và bàn giao

| Lượt | Câu trả lời | Kết quả / nội dung |
|---|---|---|
| Writable layer / emptyDir | `1B, 2C` | Đúng 2/2: container restart giữ emptyDir của Pod; Pod UID mới có emptyDir mới, dù cùng tên/node. |
| PVC / đường ghi / giới hạn | `1A, 2B` | Đúng 2/2: app phải ghi vào mount; persistence qua một lần thay Pod không chứng minh backup/HA. |
| Scratch budget | `1C, 2A` | Đúng 2/2: tmpfs dùng memory; tổng writable/logs/emptyDir có thể vượt ephemeral-storage limit. |
| Review cuối | `1C, 2A` | Đúng 2/2: startup có thể tái tạo file; tách scratch/output, ghi đúng mount và xác nhận backend/retention/backup với DevOps. |

Không ghi nhận câu trả lời sai. Các điểm đã chủ động làm rõ, không gán thành lỗi học viên:

- Tên Pod giống nhau không chứng minh cùng object; dùng UID.
- File tồn tại hoặc cùng nội dung có thể do image/startup tái tạo, không đủ chứng minh byte cũ được giữ.
- Cần marker baseline mới cho thí nghiệm replacement vì marker writable layer của thí nghiệm restart đã mất.
- Dữ liệu mất khi thay Pod trên cùng node không chứng minh node hỏng; đó là vòng đời của nguồn storage đang chọn.
- “Pod có PVC”, “emptyDir chưa đầy” và “exit 137” đều không đủ để suy lần lượt rằng app đã ghi persistent, tổng storage chưa vượt limit hoặc đã OOM.

Khi đóng bài, namespace `de-lab` UID `6d2e69f9-ada2-4699-af0d-2c98a3974710` Active; Pod mới giữ UID/container ID ở mục 4, không owner/deletionTimestamp, Running/Ready/restart 0. Cả ba node Ready/ARM64, không cordon/taint, Memory/Disk/PIDPressure False ở lượt kiểm chốt.

Không có recovery/cleanup bắt buộc hoặc câu review đang chờ. Không chạy lại lệnh stop với container ID cũ hoặc delete bằng guard UID Pod cũ để tái hiện; giữ nguyên Pod mới. Khi học viên muốn tiếp tục, bắt đầu lý thuyết/cấu hình **Bài 19 — StorageClass**, chưa tạo PVC hoặc scaffold bài mới.

## 9. Nguồn đã đối chiếu

- [Kubernetes v1.33 — Volumes / emptyDir](https://v1-33.docs.kubernetes.io/docs/concepts/storage/volumes/#emptydir).
- [Kubernetes v1.33 — Pod lifecycle](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/).
- [Kubernetes v1.33 — Persistent Volumes](https://v1-33.docs.kubernetes.io/docs/concepts/storage/persistent-volumes/).
- [Kubernetes v1.33 — Local ephemeral storage](https://v1-33.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/#local-ephemeral-storage).
- [Kubernetes v1.33 — crictl](https://v1-33.docs.kubernetes.io/docs/tasks/debug/debug-cluster/crictl/).
- [K3s CLI tools](https://docs.k3s.io/cli), đối chiếu thêm executable/help thực tế trong image lab, không lấy tài liệu hiện hành làm bằng chứng mọi subcommand có sẵn.
