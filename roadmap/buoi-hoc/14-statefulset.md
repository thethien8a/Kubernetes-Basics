# Buổi 14 — StatefulSet

**Tuần 2 — Configuration, resources và storage.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

**Trạng thái:** Hoàn thành theo yêu cầu học viên ngày 2026-10-13. [Tổng kết và minh chứng](../../after-study/14-statefulset.md).

Học viên yêu cầu chốt buổi và không quay lại phần còn lại. PostgreSQL giữ identity/dữ liệu qua thay Pod đã kiểm chứng; lab template hai member đã có claim/PV Bound và nguồn mount riêng. Thí nghiệm marker/thay Pod trong lab template và hai câu review cuối chưa được kiểm chứng/trả lời, không ghi thành đã đạt hoặc giao lại. Điểm học tiếp là [Buổi 15 — MinIO](15-minio.md), hiện Chưa học.

## Học

- Stable Pod identity
- Stable storage association
- Ordered lifecycle ở mức khái niệm

## Trước thực hành — Ôn lý thuyết và đọc cấu hình

Các khối dưới đây lưu lý thuyết và cấu hình của buổi, gắn với [manifest PostgreSQL](../../postgres-buoi14.yaml) và [manifest storage riêng](../../storage-buoi14.yaml). Cách học đã đổi sang lý thuyết/cấu hình trước thực hành, chia khối nhỏ và kiểm tra hiểu. Buổi 14 đã chốt theo yêu cầu học viên; nội dung được giữ để tham khảo, không phải yêu cầu tiếp tục lab, dừng/xóa workload hoặc làm bù phần chưa kiểm chứng.

### 1. Ôn Pod, PVC, PV và StorageClass

- **Pod:** đơn vị chạy container; Pod thay thế là object mới, UID mới. Đường dẫn `/data` là nơi container nhìn thấy volume, không tự nói volume đó đến từ đâu hoặc có persistent hay không.
- **PVC:** yêu cầu storage trong namespace; Pod tham chiếu PVC để chọn nguồn volume. Hai container cùng nhìn thấy đường dẫn `/data` không có nghĩa cùng nguồn storage.
- **PV:** object mô tả nguồn storage và binding tới PVC; các byte nằm ở backend, không nằm trong object PVC/PV.
- **StorageClass:** mô tả cách cấp storage. Trong lab, `local-path` dùng provisioner `rancher.io/local-path` để cấp nguồn local/PV; StatefulSet controller tạo PVC, không tự tạo disk hoặc copy database.
- **Mount:** kubelet/runtime gắn nguồn volume vào container; ứng dụng phải ghi bên trong `mountPath` để file được volume đó bảo vệ.

Đường tham chiếu cần đọc: Pod → claimName → PVC → PV → nguồn storage; container `volumeMounts` đưa nguồn đó vào đường dẫn mà ứng dụng dùng. Phân biệt quan hệ API này với nơi byte thực sự được ghi.

### 2. StatefulSet giữ identity gì?

StatefulSet quản lý các member có ordinal (số thứ tự). Với `storage-buoi14` và `replicas: 2`, ordinal mặc định là 0/1, tạo tên `storage-buoi14-0` và `storage-buoi14-1`. Pod 0 bị thay thì controller tạo lại member 0 cùng tên; không giữ UID/IP/container filesystem cũ. Identity giúp ghép Pod thay thế với đúng claim của member, nhưng không thay cơ chế persistence của backend.

Deployment phù hợp khi các replica có thể thay thế cho nhau và không cần identity theo member. StatefulSet phù hợp khi cần identity/storage association hoặc lifecycle có thứ tự. Không phải cứ chạy database là bắt buộc StatefulSet; tăng replicas không tự cấu hình replication/HA.

### 3. Claim cố định và volumeClaimTemplates khác nhau

- **PostgreSQL hiện có:** Pod tham chiếu `claimName: data-postgres-buoi13`. Giữ claim cũ để giữ database; nếu tăng replicas trong cấu hình này, các member vẫn tham chiếu cùng claim, không tự có PVC riêng.
- **Lab storage mới:** `spec.volumeClaimTemplates` là mẫu yêu cầu, không phải một PVC dùng chung. Mỗi template tạo một PVC cho mỗi ordinal; template tên `data` sinh `data-storage-buoi14-0` và `data-storage-buoi14-1`. Container `volumeMounts.name: data` khớp tên template. Controller đưa claimName tương ứng vào từng Pod được tạo.

| Member dự kiến | PVC dự kiến | Đường dẫn bên trong container |
|---|---|---|
| `storage-buoi14-0` | `data-storage-buoi14-0` | `/data` |
| `storage-buoi14-1` | `data-storage-buoi14-1` | `/data` |

Cùng mountPath nhưng khác nguồn. Ghi `/data/member.txt` ở member 0 không tự ghi sang member 1. Pod 0 thay thế dùng lại claim 0 còn được giữ; dữ liệu còn phụ thuộc backend còn tồn tại và ứng dụng đã ghi đúng mount, không chỉ tên claim ổn định.

### 4. Đọc field quan trọng trong lab storage

| Resource/field | Giá trị trong manifest | Ý nghĩa, quan hệ và điều cần chú ý |
|---|---|---|
| StatefulSet `metadata.name` | `storage-buoi14` | Là phần tên dùng để tạo Pod/PVC theo ordinal; tách khỏi PostgreSQL. |
| StatefulSet `spec.replicas` | `2` | Mong muốn hai member; không đồng nghĩa có database replication. |
| StatefulSet `spec.selector.matchLabels` và `spec.template.metadata.labels` | `app: storage-buoi14` | Selector phải khớp label Pod template để controller nhận diện member. |
| Service `spec.selector` | `app: storage-buoi14` | Chọn cùng các Pod; nếu khác label thì discovery/backend của Service không đúng. |
| StatefulSet `spec.serviceName` | `storage-buoi14-headless` | Trỏ governing headless Service đã khai báo riêng; không tự tạo Service đó. |
| Service `spec.clusterIP` | `None` | Headless, không có ClusterIP chuyển traffic như Service thường. Bài chỉ sleep, không có server ứng dụng/cổng cần expose. |
| StatefulSet `spec.podManagementPolicy` | `OrderedReady` | Tạo/scale up theo ordinal, đợi predecessor Running và Ready. Không phải đồng bộ dữ liệu ứng dụng. |
| `spec.volumeClaimTemplates[].metadata.name` | `data` | Tên mẫu claim; phải khớp `volumeMounts[].name`, không điền tên PVC PostgreSQL. |
| Template `spec.storageClassName` | `local-path` | Chọn cách cấp storage; class/backend/provisioner phải tồn tại và phù hợp. |
| Template `spec.accessModes` | `ReadWriteOnce` | RWO theo một node, không khóa theo một Pod. Nguồn riêng là do claim/PV riêng, không phải RWO tự chia dữ liệu. |
| Template `spec.resources.requests.storage` | `1Gi` | Yêu cầu dung lượng cho mỗi claim; local-path không chứng minh reserve/quota chỉ nhờ field này. |
| Container `volumeMounts` | `name: data`, `mountPath: /data` | Gắn nguồn claim tương ứng vào `/data`; file ngoài mount không được claim này bảo vệ. |
| Container `image`, `command`, `args` | `busybox:1.36`, shell chỉ sleep | Workload nhẹ để quan sát storage; startup không tự tạo lại marker, tránh kết quả persistence giả. |
| Container `resources` | CPU request/limit 10m/100m; RAM 16Mi/32Mi | Request phục vụ scheduling, limit giới hạn tài nguyên mỗi container; không liên quan dung lượng claim. |

### 5. DNS, readiness và lifecycle phải tách khỏi dữ liệu

Headless Service/EndpointSlice và hostname/subdomain cung cấp thông tin discovery; CoreDNS trả lời DNS, kubelet cấu hình resolver Pod. `serviceName` không biến StatefulSet thành DNS server. Tên member dự kiến có dạng `storage-buoi14-0.storage-buoi14-headless.default.svc.cluster.local`; lab đã có CoreDNS/cluster domain này. DNS member thường được publish khi Ready. BusyBox bài này không có readiness probe ứng dụng: Ready không chứng minh marker hoặc dữ liệu đúng.

Khi chỉ thay Pod 0 và giữ PVC/PV, cần quan sát tên Pod giữ nguyên, UID mới, dùng đúng claim/PV cũ và đọc đúng marker member 0; member 1 vẫn có marker riêng. Hai claim riêng không copy/sync dữ liệu sang nhau. OrderedReady chỉ bảo đảm lifecycle workload trong phạm vi policy, không bảo đảm replication hoặc thứ tự giao dịch database.

Manifest không đặt `persistentVolumeClaimRetentionPolicy`, nên mặc định giữ PVC template khi scale down/xóa StatefulSet (`Retain`). Đây là policy giữ PVC, khác với **PV reclaim policy** xử lý nguồn volume khi PVC bị xóa; class local-path của lab dùng reclaim Delete. Không tự thử xóa PVC/data hoặc coi default giữ claim là backup/HA. Phần này được đối chiếu [StatefulSet v1.35](https://v1-35.docs.kubernetes.io/docs/concepts/workloads/controllers/statefulset/).

### 6. Cấp storage và thứ tự kiểm tra trong/ngoài lab

Lab dùng local-path với `WaitForFirstConsumer`: PVC có thể chờ consumer/scheduling trước provisioning/binding; Pending ở pha này chưa tự là lỗi. Khi có workload cần claim và các điều kiện phù hợp, provisioner cấp nguồn/PV, PVC bind, kubelet mount. Ngoài OrbStack cần backend và provisioner/CSI hoặc PV cấp sẵn phù hợp, cấu hình class.provisioner/binding/reclaim/topology/quyền và mapping claim/mountPath. Managed Kubernetes có thể chuẩn bị driver/class/DNS nhưng phải kiểm tra thực tế; không copy tên class/IP DNS lab rồi mặc định dùng được.

Kiểm tra từ Pod/Events và claimName → PVC phase/Events → StorageClass/provisioner → PV claimRef/source/node affinity → mount bên trong container → file thực tế. Với DNS, kiểm tra resolver Pod → kube-dns/EndpointSlice → CoreDNS → wiring headless/member. Chỉ thử thay Pod trên node local không chứng minh chịu mất node/disk, replica, quota hoặc backup.

**Điểm cần phân biệt:** cùng mountPath khác với cùng PVC; StatefulSet controller tạo claim còn provisioner cấp nguồn storage/PV; Pod thay thế dùng claim được giữ của đúng ordinal. Không bắt nhớ syntax hoặc tính đọc/giảng lý thuyết là minh chứng triển khai. Phần này là nội dung tham khảo của buổi đã chốt, không phải câu hỏi cần làm bù trước Buổi 15.

## Challenge

Refactor PostgreSQL sang StatefulSet nếu phù hợp.

### Thực hành bổ sung — Mỗi member có PVC riêng

Dùng [lab storage riêng](../../storage-buoi14.yaml), không scale PostgreSQL đang tham chiếu một claim cố định hoặc chuyển dữ liệu database sang claim mới.

1. Triển khai StatefulSet `storage-buoi14` hai member, dùng `volumeClaimTemplates` tên `data`; cả hai mount `/data` trong container nhưng dùng hai PVC riêng.
2. Tự kiểm tra Pod → claimName → PVC/PV và nguồn mount của từng member.
3. Ghi hai nội dung khác nhau vào cùng tên file `/data/member.txt`, mỗi member một nội dung; startup không được tự tạo lại dấu test.
4. Sau khi mentor lưu baseline, thay chỉ Pod `storage-buoi14-0`. Pod mới phải cùng tên/UID mới, dùng lại đúng PVC/PV/dữ liệu member 0; member 1 giữ dữ liệu riêng.

**Acceptance:** hai PVC Bound và hai nguồn storage riêng; dữ liệu không trộn giữa member; association/dữ liệu giữ qua Pod thay thế. Giữ PostgreSQL/Secret/Service/PVC/PV cũ nguyên trạng. Không coi mô hình này là PostgreSQL replication, HA hoặc minh chứng chịu mất node.

OrbStack đã chuẩn bị class/controller `local-path`; ngoài lab cần backend/provisioner/CSI hoặc PV cấp sẵn phù hợp. Kiểm tra từ PVC Events → StorageClass/binding/provisioner → PV source/topology → Pod mount và file. Nếu class/controller thiếu, khai báo template không tự cấp storage. Không cần dựng production để học association theo ordinal.

Phần triển khai hai member/claim/PV và nguồn mount đã được mentor kiểm tra live; các bước marker và thay Pod trong lab này chưa có minh chứng. Học viên quyết định chốt Buổi 14 và không quay lại: không giao lại bước 3–4 hoặc hai câu review cuối, không dùng trạng thái chốt để ghi các phép thử chưa kiểm chứng là đã đạt. Giữ workload/dữ liệu nguyên trạng.

## Câu hỏi

> StatefulSet giải quyết vấn đề gì mà Deployment không giải quyết tốt?

## Tiêu chí hoàn thành tuần 2

Người học có thể:

- tách config khỏi image;
- quản lý Secret;
- cấu hình CPU/RAM;
- hiểu PVC/PV/StorageClass;
- triển khai PostgreSQL có persistent data.

---

Trạng thái chốt và phạm vi minh chứng được lưu trong [tiến độ](../tien-do-hoc-tap.md) và [tổng kết](../../after-study/14-statefulset.md). Khi học viên muốn tiếp tục, mở Buổi 15 theo cách học mới; không tự mở lại Buổi 14 hoặc bắt đầu workload mới.

**Trước:** [Buổi 13](13-postgresql.md) · **Tiếp:** [Buổi 15 — MinIO](15-minio.md).
