# Sau buổi 11 - Ephemeral filesystem và Volume

**Ngày học và hoàn thành:** 2026-10-11, giờ Việt Nam. **Tiến độ sau review:** 11/28.

[Challenge gốc](../roadmap/buoi-hoc/11-ephemeral-filesystem-va-volume.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Pod demo](../app-buoi11.yaml)

> Vòng đời Pod không phải vòng đời dữ liệu cần giữ. Image/YAML không lưu những thay đổi app đã ghi lúc chạy; có volume cũng chưa đủ để kết luận dữ liệu tồn tại qua việc thay Pod.

## 1. Challenge và phạm vi

Học viên tự triển khai Pod BusyBox, ghi file, xóa Pod rồi tạo lại từ cùng manifest và quan sát dữ liệu:

- Context `orbstack`, namespace `default`, Pod đơn lẻ `app-buoi11`, container `app`.
- Image `busybox:1.36`; script chỉ `while true; do sleep 3600; done`, không tự tạo lại file khi khởi động.
- CPU request/limit 10m/100m, RAM 16Mi/32Mi; chỉ dùng một Pod nhỏ.
- Không có volume ứng dụng bao phủ `/tmp/orders.txt`. Pod live có projected service-account volume mặc định ở đường dẫn khác; không ghi rằng Pod hoàn toàn không có volume.
- Dữ liệu giả `order_id=101` được học viên ghi vào `/tmp/orders.txt` bằng exec, không đưa vào image hoặc manifest.

Mentor chỉ đọc manifest/API và kiểm tra file, lưu baseline trước khi học viên tự xóa/tạo lại Pod. Không viết/xóa file, apply/delete/restart workload thay học viên hoặc đọc token service-account. Không triển khai PostgreSQL, PVC/PV hoặc storage provisioner cho Buổi 11.

## 2. Minh chứng trước và sau

| Phần đối chiếu | Trước khi xóa/tạo lại | Sau khi tạo lại |
|---|---|---|
| Giờ mentor kiểm tra | 14:58:13 | 15:06:35 |
| Tên Pod | app-buoi11 | app-buoi11 |
| UID | `06007aea-2977-4daf-9124-7881d1eef4d1` | `d1e6a793-95c2-459a-ad2e-043d79c378a8` |
| Pod được tạo | 13:23:28 | 15:04:42 |
| Container bắt đầu | 13:23:29 | 15:04:43 |
| Node / Pod IP | orbstack / 192.168.194.29 | orbstack / 192.168.194.30 |
| Runtime | Running/Ready 1/1, RESTARTS=0 | Running/Ready 1/1, RESTARTS=0 |
| File `/tmp/orders.txt` | Chính xác `order_id=101` kèm newline | Không tồn tại; phép kiểm tra chỉ đọc trả `orders.txt absent` |
| Image/script/resources | BusyBox, vòng sleep, cấu hình nhỏ | Giữ nguyên như baseline |

Hai Pod dùng cùng image digest `sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662`. API trước/sau mỗi phép đọc giữ cùng UID/containerID tại mốc đó, tránh lấy trạng thái một Pod rồi đọc file của Pod khác. UID và containerID giữa hai mốc đã đổi; tên giống nhau không làm chúng thành cùng object.

Snapshot trước không còn Events theo tên Pod; snapshot sau có Killing và Scheduled/Pulled/Created/Started. Không suy ra lịch sử Events chỉ từ một snapshot rỗng hoặc suy ra trình tự mọi lệnh của học viên. Các timestamp trong bảng là giờ Việt Nam ngày 2026-10-11.

Kiểm tra bổ sung lúc 15:21:56 xác nhận Pod mới vẫn cùng UID, Running/Ready và RESTARTS=0; không có thí nghiệm storage mới trong phép kiểm tra này.

## 3. Image và writable layer

```diagram
Trước: Pod UID A ──→ lớp ghi A ──→ orders.txt
Sau:   Pod UID B ──→ lớp ghi B ──→ không có orders.txt
```

- **Image** cung cấp chương trình và nội dung ban đầu. Container mới dùng lại cùng image có lại các file đóng sẵn đó, với giả định đường dẫn không bị volume mount che và app không tự sửa/xóa chúng.
- **Writable layer** là lớp ghi của container. File tạo hoặc thay đổi lúc chạy ở lớp này không được ghi ngược vào image hoặc YAML.
- Tạo lại container từ image không phải khôi phục dữ liệu runtime. Trong thực hành, file được ghi sau startup, image/script giữ nguyên và container mới không có file đó.
- Manifest mô tả desired state/cách chạy, không phải backup của filesystem đang chạy. Giữ tên Pod, image và YAML không bảo đảm dữ liệu runtime được giữ.

**Chuẩn hóa từ ngữ:** trong bài ta xóa và tạo Pod mới, UID đổi. Restart container trong cùng Pod là việc khác: UID Pod có thể giữ nguyên trong khi containerID/restart count đổi. Khi nói “restart Pod”, cần làm rõ đang chỉ restart container hay thay Pod; không dùng cách nói đó để quyết định vòng đời dữ liệu.

Buổi này kiểm chứng trực tiếp việc thay Pod, không chủ động làm container crash/restart để kiểm chứng riêng writable layer.

## 4. Volume không đồng nghĩa persistent storage

Volume đưa một nguồn dữ liệu vào filesystem container tại một đường dẫn mount. Nguồn đó và vòng đời của nó quyết định dữ liệu có tồn tại sau các thay đổi runtime hay không.

| Loại nguồn | Khi restart container trong cùng Pod | Khi xóa/thay Pod | Phạm vi Buổi 11 |
|---|---|---|---|
| Writable filesystem container | Container được tạo lại có trạng thái sạch, không giữ các thay đổi runtime cũ. | Không giữ các thay đổi runtime của container cũ. | Thay Pod đã kiểm chứng; container restart riêng chỉ giải thích. |
| `emptyDir` | Giữ dữ liệu trong cùng Pod. | Dữ liệu bị xóa cùng Pod; Pod mới có emptyDir mới. | Chỉ giải thích/review, chưa mount hoặc thực hành. |
| Persistent storage qua PV/PVC | Có thể giữ dữ liệu độc lập với container/Pod khi dùng lại đúng nguồn còn tồn tại. | Vòng đời storage không phụ thuộc riêng Pod; còn phụ thuộc nguồn lưu trữ và chính sách quản lý. | Dẫn nhập cho Buổi 12, chưa cấp/mount/kiểm chứng persistence. |

Các field tham khảo, không yêu cầu học thuộc syntax:

- `spec.volumes`: khai báo nguồn volume cho Pod.
- `spec.containers[].volumeMounts[].name`: khớp tên volume cần dùng.
- `volumeMounts[].mountPath`: đường dẫn container nhìn thấy nguồn đó; app phải thực sự ghi vào đường dẫn đã mount.
- `emptyDir`: nguồn tạm gắn vòng đời Pod, không phải cách lưu dữ liệu database qua việc thay Pod.

ConfigMap volume đã học ở Buổi 08 cấp dữ liệu cấu hình từ API, không phải nguồn để app ghi dữ liệu PostgreSQL. Không coi “có mount” hoặc “ghi trên disk” riêng lẻ là bằng chứng persistence, HA hoặc backup.

## 5. Review và bổ sung của mentor

| Câu review | Câu trả lời / đánh giá |
|---|---|
| File sau tạo lại Pod và hậu quả với PostgreSQL? | Học viên quan sát file không còn và nhận định PostgreSQL lưu theo cách này sẽ mất dữ liệu khi có Pod mới. Đúng trong giả định thư mục data nằm ở writable filesystem container; đây là liên hệ, chưa chạy PostgreSQL thật. |
| File đóng sẵn trong image so với file tạo bằng exec? | Học viên trả lời không cùng số phận: file image có lại, file tạo bằng exec mất khi tạo lại Pod nếu không mount. Đạt ý chính phân biệt nguồn; mentor bổ sung tạo file runtime không lưu ngược vào image và việc mount chỉ hữu ích khi nguồn có vòng đời phù hợp. |
| Pod mới cùng tên, gắn emptyDir mới, dữ liệu cũ còn không? | Học viên trả lời không, dữ liệu vẫn mất. Đạt cho tình huống thay Pod; học viên dùng từ “restart Pod”, mentor chuẩn hóa xóa/tạo Pod mới và nhắc emptyDir vẫn giữ dữ liệu qua restart container trong cùng Pod. Không ghi rằng học viên đã tự kiểm chứng hoặc tự giải thích trường hợp restart container. |

**Kết quả:** thực hành filesystem và concept chính đã đạt, Buổi 11 Hoàn thành ngày 2026-10-11. Không hỏi lại chỉ để sửa thuật ngữ; lưu rõ phần mentor bổ sung và giới hạn thực hành. PV/PVC/StorageClass vẫn là buổi kế tiếp, chưa được tính là đã học.

## 6. Commands để ôn

Các lệnh này tái hiện bài khi học viên chủ động thực hành lại. `delete` làm mất file demo trong Pod; không dùng cho workload/dữ liệu thật chưa có kế hoạch bảo vệ. Mentor không chạy các lệnh thay đổi này thay học viên.

```bash
kubectl --context=orbstack -n default apply -f app-buoi11.yaml
kubectl --context=orbstack -n default wait \
  --for=condition=Ready pod/app-buoi11 --timeout=120s
kubectl --context=orbstack -n default exec app-buoi11 -- sh -c \
  'printf "order_id=101\n" > /tmp/orders.txt && cat /tmp/orders.txt'
kubectl --context=orbstack -n default get pod app-buoi11 \
  -o custom-columns='NAME:.metadata.name,UID:.metadata.uid'

kubectl --context=orbstack -n default delete pod app-buoi11 \
  --wait=true --timeout=120s
kubectl --context=orbstack -n default apply -f app-buoi11.yaml
kubectl --context=orbstack -n default wait \
  --for=condition=Ready pod/app-buoi11 --timeout=120s
kubectl --context=orbstack -n default exec app-buoi11 -- cat /tmp/orders.txt
```

Không chạy lại lệnh ghi sau tạo Pod mới: file tự tạo lại không chứng minh dữ liệu cũ được giữ. Đối chiếu UID, cấu hình nguồn/mount, trạng thái container và file; chỉ thấy Pod Ready chưa đủ kiểm tra dữ liệu.

## 7. OrbStack và ngoài lab

- Thí nghiệm writable filesystem là cơ chế Kubernetes/container runtime, không dùng wildcard DNS, LoadBalancer hoặc local-path provisioner của OrbStack. OrbStack chuẩn bị node Linux/runtime cho lab.
- Ngoài lab, người vận hành chuẩn bị node/runtime và khả năng cung cấp/pull image phù hợp kiến trúc CPU; app vẫn phải chọn đúng nguồn lưu dữ liệu và mountPath. File runtime không được tự lưu vào image chỉ vì đổi môi trường.
- Với emptyDir, kubelet tạo/quản lý vùng tạm của Pod trên node. Mặc định dùng backing storage của node, không cần PV/PVC/StorageClass hoặc CSI; `medium: Memory` là lựa chọn khác, dùng RAM và liên quan memory accounting. Bài không cấu hình medium hoặc đo storage/RAM của emptyDir.
- Persistence thực tế cần nguồn lưu trữ được quản lý ngoài vòng đời Pod, cấu hình cấp/mount phù hợp và kiểm tra dữ liệu sau thay Pod; thành phần/backend cụ thể thuộc Buổi 12. Chưa kiểm chứng node hỏng, di chuyển sang node khác, HA hoặc backup/restore.

**Giới hạn minh chứng:** chỉ trực tiếp thực hành filesystem không gắn volume ứng dụng trên OrbStack. emptyDir/persistent storage là theory/review, chưa mount/chạy thử; chưa cấu hình cluster ngoài lab hoặc PostgreSQL thật.

## 8. Liên hệ Data Engineering và bước tiếp theo

- PostgreSQL/metadata database cần giữ dữ liệu qua việc thay Pod; không đặt toàn bộ state cần giữ vào writable layer.
- Scratch/cache có thể chấp nhận mất và tạo lại, nên volume tạm như emptyDir có mục đích riêng; không dùng nó thay storage cần bền vững.
- Kubernetes tái tạo workload không đồng nghĩa khôi phục dữ liệu. Muốn đánh giá đúng phải hỏi app ghi ở đâu, nguồn dữ liệu nào và nguồn đó sống bao lâu.

**Buổi 11 hoàn thành, tổng 11/28.** Tiếp theo là [Buổi 12 - PV, PVC và StorageClass](../roadmap/buoi-hoc/12-pv-pvc-storageclass.md). Pod demo vẫn được giữ; chốt tài liệu không tự xóa workload hoặc cấp storage.

## Tài liệu tham khảo

- [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/).
- [emptyDir](https://kubernetes.io/docs/concepts/storage/volumes/#emptydir).
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/).
