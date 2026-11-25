# Tổng kết Bài 22 — Reclaim, mở rộng và backup/restore

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/22-backup-va-reclaim.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/23-config-secret.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-19**, giờ Việt Nam (`Asia/Ho_Chi_Minh`). Review cuối `1B, 2C`, đúng 2/2.
- **Challenge:** Ghi bộ file giả một lần, tạo archive ngoài volume nguồn, rồi khôi phục chỉ từ archive vào PVC mới. Nghiệm thu đúng tên file, byte, SHA-256 và nội dung; nguồn giữ nguyên.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab` Active, UID `6d2e69f9-ada2-4699-af0d-2c98a3974710`. Học viên tự tạo tài nguyên, backup và restore. Mentor chuẩn bị scaffold, kiểm client dry-run và kiểm tra live chỉ đọc. Không dùng volume các bài trước làm nguồn.

## 1. Mental model và cấu hình

| Resource / cấu hình | Điều cần nhớ |
|---|---|
| `StorageClass.reclaimPolicy` → `PV.spec.persistentVolumeReclaimPolicy` | Class đặt policy ban đầu cho PV được cấp động. Với PV đã cấp, đọc policy ở chính PV; tạo class khác với `Retain` không đổi PV cũ. `Delete` yêu cầu dọn đối tượng PV và storage phía sau khi PVC bị xóa và PV được giải phóng, nếu loại volume và driver hỗ trợ. `Retain` giữ volume gốc để xử lý thủ công; PV `Released` không tự sẵn sàng cho claim mới. Không policy nào tự tạo backup. |
| `StorageClass.allowVolumeExpansion`, `PVC.spec.resources.requests.storage`, `PVC.status.capacity.storage` và `status.conditions[]` | Class cho phép chưa đủ: driver/backend cũng phải hỗ trợ. Request là dung lượng mong muốn. `FileSystemResizePending=True` nghĩa là resize phía controller xong nhưng filesystem trên node còn chờ; kiểm dung lượng thực tế tại mount. Không sửa trực tiếp `PV.spec.capacity` để ép resize, không dùng expansion để thu nhỏ. Lab chỉ đọc `ALLOWVOLUMEEXPANSION=false`. |
| `PVC.spec.storageClassName`, `accessModes`, `volumeMode` và `volumeName` | Hai claim chọn `local-path`, `ReadWriteOnce`, `Filesystem`, yêu cầu `64Mi` mỗi claim. `ReadWriteOnce` giới hạn mount đọc-ghi theo node, không khóa theo Pod. `64Mi` không phải quota cứng cho thư mục local-path. `volumeName` trỏ tới PV thực tế; kiểm ngược `PV.spec.claimRef` theo namespace, tên và UID. |
| `Pod.spec.volumes[].persistentVolumeClaim.claimName` và `volumeMounts[]` | `claimName` chọn PVC; `name` nối mount với volume trong Pod; `mountPath` chỉ là đường dẫn trong container. `readOnly: true` bảo vệ mount của reader, không ngăn writer khác. Đích chỉ mount PVC mới với quyền ghi, không mount nguồn. |
| Quiesce, archive và checksum | Job hữu hạn kết thúc ghi trước lúc backup. Nếu writer còn cập nhật, CSV và manifest có thể là hai phiên bản khác nhau dù đóng gói thành công. Checksum toàn archive kiểm artifact được truyền/lưu; checksum từng file và đối chiếu nội dung mới kiểm bộ file khôi phục. Snapshot ở tầng storage không mặc định nhất quán theo ứng dụng hay nằm ngoài miền lỗi. |
| Lịch, nơi lưu, retention, quyền, RPO/RTO | Đây là cấu hình của quy trình backup, không phải field PVC. RPO là cửa sổ dữ liệu có thể mất: từ mốc dữ liệu mới nhất phục hồi được đến sự cố. RTO là thời gian từ gián đoạn đến khi hệ thống dùng lại được. Giám sát tuổi của bản dùng được, không chỉ lịch chạy; giữ đủ phiên bản để xử lý lỗi phát hiện muộn. |

Dự đoán đã review, **không xóa hoặc gây sự cố để kiểm**:

| Tình huống | Dự đoán |
|---|---|
| Chỉ xóa Pod, giữ PVC | Không kích hoạt reclaim. Có thể mount lại PV nếu node và dữ liệu còn truy cập được. |
| Xóa PVC của PV có `Delete` | Provisioner có thể dọn storage gốc khi volume được giải phóng. `Retain` giữ nguồn gốc, không tạo bản sao độc lập. |
| Xóa container của node giữ local PV | Liên kết PVC–PV có thể vẫn `Bound`; dữ liệu còn hay mất phụ thuộc đường dẫn lưu bên dưới container. PV không tự chuyển sang agent khác. |
| Hỏng ổ chứa cả volume và archive | Có thể mất cả nguồn, đích và bản sao. Tách PVC hay tách thư mục trên một Mac không đồng nghĩa tách miền lỗi. |

## 2. Thiết kế lab và scaffold

```text
Job writer → PVC lesson22-source → reader /source (ro)
    → tar stdout qua kubectl exec → archive trên Mac
    → stdin qua kubectl exec -i → Pod restore /restore (rw) → PVC lesson22-restored
```

Client `/usr/local/bin/kubectl` **v1.33.9**, server **v1.33.6+k3s1**, nodes ARM64. Class `local-path` dùng `rancher.io/local-path` v0.0.32, `WaitForFirstConsumer`, `Delete`, không bật expansion. Hai PV có `spec.local` và affinity tới `k3d-de-k3d-agent-1`. Image BusyBox `1.37.0` ghim index `sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec`; registry có `linux/arm64/v8`.

| Scaffold | Vai trò |
|---|---|
| [01-source-pvc.yaml](../thuc-hanh/22-backup-va-reclaim/01-source-pvc.yaml) | `lesson22-source`, claim sạch cho dữ liệu giả. |
| [02-writer-job.yaml](../thuc-hanh/22-backup-va-reclaim/02-writer-job.yaml) | `lesson22-writer`: `completions: 1`, `parallelism: 1`, `backoffLimit: 0`, deadline 120 giây và `restartPolicy: Never`. Ghi hai file tại `/source/dataset`; `mkdir` không `-p` và `sh -e` chặn ghi đè nếu thư mục đã tồn tại, kể cả thư mục dở từ lượt lỗi. Không coi Job là bảo đảm exactly-once. |
| [03-source-reader.yaml](../thuc-hanh/22-backup-va-reclaim/03-source-reader.yaml) | `lesson22-reader` chỉ sleep, mount `lesson22-source` tại `/source` read-only; lấy baseline và đọc dữ liệu để tạo archive. |
| [04-restore-pvc.yaml](../thuc-hanh/22-backup-va-reclaim/04-restore-pvc.yaml) | `lesson22-restored`, claim riêng, không trỏ tới PV nguồn. |
| [05-restore-pod.yaml](../thuc-hanh/22-backup-va-reclaim/05-restore-pod.yaml) | `lesson22-restore` chỉ sleep, mount đúng claim đích tại `/restore` read-write. Không tự giải nén khi khởi động và không mount PVC nguồn. |

Năm file qua client dry-run/schema; script writer được thử trong thư mục tạm cho đúng hai file và từ chối ghi đè cả thư mục đầy đủ lẫn thư mục dở. Các kiểm cục bộ này không phải kết quả runtime. Containers không cần gọi API nên tắt tự mount ServiceAccount token.

## 3. Runtime và bằng chứng

| Mốc ngày 19/11, giờ Việt Nam | Bằng chứng |
|---|---|
| **14:58:03** — Job hoàn tất | Lượt kiểm lúc **15:02** thấy Job `Complete=True`, `succeeded=1`; Pod đúng owner UID, `Succeeded`, writer exit `0`. PVC nguồn `Bound`. Events của đúng PVC UID có `WaitForFirstConsumer`, `Provisioning` và `ProvisioningSucceeded`. Không suy học viên đã nhìn thấy trạng thái `Pending` chỉ từ Events. |
| **15:40:14** — baseline nguồn | Reader Ready trên `agent-1`, `/source` là `ro` trong `/proc/mounts`, dùng đúng PVC/PV; Pod writer đã kết thúc. Mentor đọc độc lập và so từng byte với dữ liệu giả. |
| **16:23:17** — backup bắt đầu và kiểm xong | Học viên tạo `dataset.tar` trên Mac, lưu checksum và thời điểm. Archive **3072 byte** tại `~/.local/share/k8s-practice/lesson22/backup/`, ngoài volume nguồn và Git; không còn `.part`. Mentor kiểm hai entry là file thường, đúng tên/byte/nội dung và SHA-256 toàn archive `9acd786cb239c32ea515926bf8bff586fafd230156eda8167939834273f041cc`. Đọc lại hai file nguồn, hash không đổi. |
| **16:49:15** — đích còn trống | Hai PVC/PV `Bound`, UID PV và đường dẫn local khác nhau; `/restore` là `rw`. `ls -1A /restore` exit `0`, stdout trống. Pod restore chỉ mount PVC đích. |
| **16:55:38** — bắt đầu restore và kiểm xong | Học viên truyền đúng archive từ Mac vào Pod restore; tạo mới `/restore/dataset`. Hai entry/byte/hash và nội dung khớp ở đích. Backup và restore mỗi lượt có hai mốc rơi vào cùng một giây ở độ phân giải ghi log; mốc restore bắt đầu sau khi đích đã sẵn sàng, không đo downtime dịch vụ. |
| **17:14:52** — kiểm chốt sau review | Nguồn và đích còn đúng PVC/PV và Pod UID, mỗi mount còn đọc đúng hai file. Reader và restore Ready/restart 0, writer vẫn `Complete=True`/exit `0`. Archive và hai file ghi giờ không đổi. Ba node Ready/ARM64, không cordon/taint/pressure; provisioner Ready 1/1. |

| Tài nguyên | UID / liên kết |
|---|---|
| PVC `lesson22-source` → PV `pvc-de71db47-2f48-4c74-ba6c-5358c9ea99cc` | PVC UID `de71db47-2f48-4c74-ba6c-5358c9ea99cc`; PV UID `923a4ac9-4fab-4056-ae54-de6f882e795a` |
| PVC `lesson22-restored` → PV `pvc-82cdf80c-cbad-4cc5-a75a-c71b7d3d424d` | PVC UID `82cdf80c-cbad-4cc5-a75a-c71b7d3d424d`; PV UID `1242853f-05f8-4edf-99c7-45ddeeb87045` |
| Job `lesson22-writer` / Pod `lesson22-writer-rb8cn` | Job UID `0ad5fac8-883d-4554-9abd-b27ca80d1f64`; Pod UID `1741b558-f5b8-421d-af7a-90d8ed105771` |
| Pod `lesson22-reader` / Pod `lesson22-restore` | Reader UID `cf493c99-4fee-4832-911c-def66a0f28d9`; restore UID `a4e9e729-b6bc-4775-8cf3-e0dcb46a5497` từ lúc volume trống qua restore đến khi chốt |

| File | Byte | SHA-256 tại nguồn, archive và đích |
|---|---:|---|
| `rows.csv` | 20 | `8776e8485cb6f1fd3c4e9d6698a6de3054a4a7322b0655cfd4491ec36396a1cd` |
| `manifest.json` | 11 | `245aaaf492d2b51f479776969a7a901463d43f6bdb79c70e74fc46e099e2f55b` |

CSV là `id,status` rồi `1,ok` và `2,ok`; manifest là `{"rows":2}`. Hai dòng dữ liệu không tính header. `Complete=True`, `Bound`, `Ready` hoặc `dataset.tar: OK` riêng lẻ đều không chứng minh bộ file trên đích.

## 4. Tái quan sát chỉ đọc

Dùng context/namespace tường minh. Nếu xem lại sau đó, đối chiếu UID và trạng thái Ready trước khi exec vào fixture. Không chạy lại writer, lệnh tạo `.part` hay lệnh extract để review.

```bash
K22=(/usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" --context=k3d-de-k3d -n de-lab)
"${K22[@]}" get pvc lesson22-source lesson22-restored \
  -o 'custom-columns=NAME:.metadata.name,STATUS:.status.phase,VOLUME:.spec.volumeName'
```

Snapshot chốt, rút gọn tên PV:

```text
NAME                STATUS   VOLUME
lesson22-source     Bound    pvc-de71db47…
lesson22-restored   Bound    pvc-82cdf80c…
```

Nhìn `VOLUME` để đối chiếu hai binding khác nhau. Hai lệnh sau kiểm nội dung ở đúng hai mount:

```bash
"${K22[@]}" exec lesson22-reader -c reader -- \
  sh -ec 'cd /source/dataset; sha256sum rows.csv manifest.json'
"${K22[@]}" exec lesson22-restore -c restore -- \
  sh -ec 'cd /restore/dataset; sha256sum rows.csv manifest.json'
```

Hai lệnh cho cùng hai dòng SHA-256 như bảng ở mục 3, khớp baseline trước backup. Trên Mac, đọc bản sao và các mốc đã lưu:

```bash
(
  cd "$HOME/.local/share/k8s-practice/lesson22/backup" || exit 1
  tar -tf dataset.tar
  shasum -a 256 -c dataset.tar.sha256
  cat backup-times.txt restore-times.txt
)
```

`tar -tf` in `rows.csv`, `manifest.json`; `shasum` in `dataset.tar: OK`. Hai file cuối ghi `backup_started`/`backup_verified` tại `2026-11-19T16:23:17+0700` và `restore_started`/`restore_verified` tại `2026-11-19T16:55:38+0700`. Tên entry khác với chứng minh nội dung; so thêm hash từng entry và hash ở mount đích.

**Luồng đã thực hành:** `tar -cf - -C /source/dataset rows.csv manifest.json` chạy trong reader; `>` ở shell Mac ghi vào `.part`. Sau khi lệnh thành công, đúng danh sách và hash từng entry, mới đổi tên và lưu checksum archive. Khi restore, `< dataset.tar` mở file trên Mac, `kubectl exec -i` nối stdin vào container, rồi `tar -xf - -C /restore/dataset` ghi trong thư mục mới. Không dùng TTY cho archive nhị phân. Hai lượt có chốt chống ghi đè và không chạy lại trên đích đã có dữ liệu.

## 5. Review, yêu cầu DevOps và giới hạn

- **Review đã đạt:** phân biệt reclaim với backup, class cho phép expansion với driver thực thi, quiesce với mount read-only, retention với tần suất, mount path với `claimName`, và redirect trên Mac với stdin/stdout trong Pod. Review cuối `1B, 2C`: đích lệch hash thì không nghiệm thu dù archive và kích thước khớp; muốn chứng minh phục hồi khi mất vùng chính phải có bản sao còn truy cập được ở đích phục hồi, quyền và storage phù hợp, rồi diễn tập đến lúc pipeline dùng lại được.
- **Điểm đã làm rõ:** ban đầu chưa biết tính RPO/RTO. Lấy lúc gián đoạn làm mốc, nhìn lùi về thời điểm dữ liệu trong bản dùng được và nhìn tới lúc dịch vụ dùng lại được. Câu củng cố: bản có dữ liệu đến 13:45, gián đoạn 14:00, dùng lại 14:18 → cửa sổ mất dữ liệu 15 phút, gián đoạn 18 phút. Với RPO 10/RTO 20 phút, học viên chọn đúng **chỉ đạt RTO**. Upload xong không làm dữ liệu mới hơn; giải nén xong chưa chắc app dùng được.
- **Lab làm giúp:** K3s cung cấp local-path provisioner để tạo thư mục trên node; k3d đặt các node trên cùng Mac. Ngoài lab tự quản lý, chuẩn bị local PV sạch với đường dẫn và `nodeAffinity` hoặc cài CSI tương thích backend. Managed có thể cung cấp CSI, nhưng vẫn phải xác nhận class, topology, dung lượng và quyền ở nơi restore. Nếu PVC/Pod không sẵn sàng, đọc binding, Events của PVC/Pod, rồi kiểm scheduler, provisioner/CSI, backend và mount trước khi giải nén.
- **Hợp đồng với DevOps:** định nghĩa sự cố và tiêu chí app dùng lại được; chốt RPO/RTO, cơ chế quiesce hoặc backup theo ứng dụng, vị trí bản sao tách miền lỗi cần chịu, thời lượng retention, quyền ghi/restore và mã hóa phù hợp, người kiểm restore và cách đo từ lúc gián đoạn. Với CSI snapshot, xác nhận nơi dữ liệu snapshot thực sự nằm và có truy cập được khi sự cố hay không.
- **Giới hạn:** đã restore file tĩnh vào PV riêng, nhưng hai PV đều trên node container `agent-1` và archive vẫn trên cùng Mac. Chưa thử reclaim thực tế, xóa claim/node, expansion, mất disk/Mac, restore xuyên vùng, backup database thật, HA hay RPO/RTO production. Phần backup PostgreSQL thật thuộc Bài 29.

## 6. Bàn giao

Giữ năm scaffold, Job và Pod writer đã hoàn tất, reader, restore Pod, hai PVC/PV, archive và các file kiểm tra ngoài Git. Không có cleanup hoặc review còn chờ. Bài 23 chưa mở.

- [Kubernetes v1.33 — PersistentVolume reclaim và expansion](https://v1-33.docs.kubernetes.io/docs/concepts/storage/persistent-volumes/) · [StorageClass](https://v1-33.docs.kubernetes.io/docs/concepts/storage/storage-classes/) · [Volume snapshots](https://v1-33.docs.kubernetes.io/docs/concepts/storage/volume-snapshots/)
- [Local Path Provisioner v0.0.32](https://github.com/rancher/local-path-provisioner/tree/v0.0.32) · [BusyBox 1.37.0 registry metadata](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0)
- [RPO/RTO](https://cloud.google.com/architecture/dr-scenarios-planning-guide) · [Giới hạn copy file của PostgreSQL](https://www.postgresql.org/docs/current/backup-file.html)
