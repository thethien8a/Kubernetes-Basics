# Tổng kết buổi 14 - StatefulSet

**Ngày học và chốt:** 2026-10-13, giờ Việt Nam. **Trạng thái:** Hoàn thành theo yêu cầu học viên. **Tiến độ:** 14/28.

[Challenge gốc](../roadmap/buoi-hoc/14-statefulset.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [StatefulSet/headless Service PostgreSQL](../postgres-buoi14.yaml) · [Lab PVC riêng](../storage-buoi14.yaml) · [Client](../postgres-client-buoi13.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a1336b-b82a-721c-9a67-b58634e290f7)

> StatefulSet giữ identity của member, không giữ nguyên object Pod, UID hoặc Pod IP. Dữ liệu còn vì Pod mới dùng lại nguồn persistent còn tồn tại; StatefulSet không tự copy dữ liệu, cấu hình database replication hoặc cung cấp DNS server.

> Học viên yêu cầu chốt: “kết thúc buổi 14 đi, coi như ta xong buổi 14 rồi ko quay lại nữa”. Buổi 14 được đóng trong lộ trình theo quyết định này; không giao lại phần lab hoặc câu hỏi còn lại. Lần học tiếp theo bắt đầu Buổi 15, không tự mở lại Buổi 14.

> Phần PostgreSQL giữ dữ liệu qua thay Pod đã kiểm chứng. Lab PVC riêng đã có hai member Ready, hai claim/PV Bound và hai nguồn mount riêng; chưa kiểm chứng hai marker khác nhau và dữ liệu qua thay Pod trong lab này. Hai câu review cuối về Ready/retention chưa được trả lời. Chốt lộ trình không phải xác nhận toàn bộ acceptance bổ sung đã đạt.

> Cách học từ 2026-10-13 là lý thuyết/cấu hình trước, thực hành sau, chia khối nhỏ. Các mục bên dưới lưu kiến thức và bằng chứng đã có, không phải yêu cầu tiếp tục lab hoặc dọn workload/dữ liệu.

## 1. Challenge, lựa chọn và phạm vi

Buổi 13 đã chứng minh PostgreSQL một instance có persistence bằng Deployment + PVC. Buổi 14 bổ sung yêu cầu tên và DNS của từng member ổn định qua thay Pod:

1. Chuyển PostgreSQL từ Deployment sang StatefulSet, giữ dữ liệu và endpoint client cũ.
2. Không tạo lại bảng, INSERT lại dữ liệu hoặc thêm startup script tái tạo orders.
3. Thay chỉ Pod StatefulSet; đối chiếu cùng tên nhưng UID mới, DNS và dữ liệu đúng.
4. Review storage association theo member, OrderedReady và trách nhiệm DNS ngoài lab.
5. Bổ sung lab BusyBox hai member dùng `volumeClaimTemplates`; phần cấp claim/PV và mount đã được mentor kiểm tra, còn thí nghiệm marker/thay Pod không tiếp tục theo yêu cầu chốt buổi.

Học viên chọn giữ PVC/PV và Service ClusterIP, thay Deployment bằng StatefulSet. Mentor bổ sung headless Service/serviceName, scaffold và commands; học viên tự triển khai, đưa Deployment cũ về 0 và tự thay Pod. Mentor chỉ đọc manifest/API, mount, DNS và SQL READ ONLY để kiểm tra, không apply/scale/delete/restart workload hoặc ghi dữ liệu thay học viên.

Context `orbstack`, namespace `default`, một node `orbstack`. Chỉ chạy một PostgreSQL instance, không replication/HA. Deployment vẫn là lựa chọn hợp lệ cho database đơn giản khi không cần identity theo member; StatefulSet được chọn vì yêu cầu mới, không chỉ vì ứng dụng là database.

## 2. Cấu hình đã dùng và trách nhiệm

| Thành phần/field | Cấu hình và ý nghĩa |
|---|---|
| StatefulSet | `postgres-buoi14`, `replicas: 1`; trực tiếp quản lý Pod, không qua ReplicaSet như Deployment. |
| `serviceName` | `postgres-buoi14-headless`; liên kết network identity với governing headless Service. |
| Headless Service | `postgres-buoi14-headless`, `clusterIP: None`, selector `app: postgres-buoi13`, port 5432 → named port `postgres`. Không có ClusterIP để làm endpoint chuyển traffic như Service thường. |
| Client Service | Giữ `postgres-buoi13`, ClusterIP `192.168.194.177:5432`; client giữ `PGHOST=postgres-buoi13`. |
| Labels/selector | Pod giữ `app: postgres-buoi13` để cả hai Service chọn đúng backend. |
| Storage | Tham chiếu PVC cũ `data-postgres-buoi13`, mount `/var/lib/postgresql/data`; `PGDATA=/var/lib/postgresql/data/pgdata` nằm bên trong mount. |
| `volumeClaimTemplates` | Không dùng trong manifest PostgreSQL để giữ database cũ. Lab `storage-buoi14` dùng template `data`, đã có hai claim/PV và nguồn mount riêng như mục 4. |
| `podManagementPolicy` | `OrderedReady`; điều khiển thứ tự tạo/scale Pod, không cấu hình replication. |
| Update strategy | Mặc định StatefulSet là `RollingUpdate`, không sao chép strategy `Recreate` của Deployment. |
| Image/resources | Giữ `postgres:16-alpine`, CPU request/limit 100m/500m, RAM 256Mi/512Mi. |
| Secret/client | Giữ Secret mount file và contract `_FILE` phía server, pgpass phía client như [Buổi 13](13-postgresql-tren-kubernetes.md); không lưu credential vào tài liệu. |
| Readiness | TCP 5432 chỉ kiểm tra cổng, không thay cho login/SELECT và kiểm tra đúng dữ liệu. |

Hai Service có vai trò khác nhau: Service ClusterIP cũ là endpoint client ổn định; headless Service hỗ trợ discovery/địa chỉ từng member. Không bắt client cũ chuyển sang dùng Pod IP hoặc tên member để bài chạy.

```diagram
┌─────────────┐     ┌──────────────────────┐     ┌───────────────────┐
│ Client Pod  │────▶│ Service postgres-13  │────▶│ PostgreSQL Pod    │
└─────────────┘     │ ClusterIP:5432       │     │ postgres-buoi14-0 │
                    └──────────────────────┘     └─────────┬─────────┘
                                                          │ mount
                                                    ┌─────▼─────┐
                                                    │ PVC ↔ PV  │
                                                    └─────┬─────┘
                                                          ▼
                                                 storage trên node
```

Nhãn `postgres-13` trong sơ đồ viết gọn Service `postgres-buoi13`. PVC/PV là object yêu cầu/binding/mô tả nguồn; byte database nằm trên backend, không nằm trong API object.

**Trade-off của bài:** một claim cố định giữ database hiện có nhưng không tạo storage riêng cho nhiều member. Không scale manifest này lên hai: RWO giới hạn theo node, không khóa theo Pod hoặc làm hai PostgreSQL cùng ghi một directory an toàn. Chuyển controller có downtime; không đo thời gian gián đoạn hoặc chứng minh chuyển đổi không chồng instance trong mọi thời điểm chỉ từ snapshot.

## 3. Identity và minh chứng trước/sau

StatefulSet dùng ordinal để phân biệt member; trong bài, member 0 có tên `postgres-buoi14-0`. Khi thay Pod, controller khôi phục member có cùng tên/hostname/subdomain, nhưng tạo object Pod mới. DNS member giữ tên, địa chỉ có thể cập nhật theo Pod IP mới.

Các mốc là ngày 2026-10-13, giờ Việt Nam:

| Đối chiếu | Baseline StatefulSet 14:36:41 | Sau thay Pod, kiểm tra 15:01:58–15:09:11 |
|---|---|---|
| Pod name/hostname | `postgres-buoi14-0` | Giữ nguyên |
| Pod UID | `6d58c9bb-e869-46de-9208-d0be735724de` | `6513b27a-6bce-41ca-a302-ac83c0245259` |
| Pod IP | `192.168.194.39` | `192.168.194.41` |
| Direct owner | StatefulSet `postgres-buoi14` | Giữ cùng StatefulSet UID/generation/revision |
| Runtime | Running/Ready, RESTARTS=0 | Pod mới tạo 14:58:31, Running/Ready, RESTARTS=0 |
| PVC/PV | PVC `data-postgres-buoi13`, PV `pvc-52bbd1e9-90c9-4bc7-874d-04375ff258c1`, Bound | Giữ UID/binding và nguồn mount |
| Client Service | ClusterIP `192.168.194.177` | Giữ nguyên; backend đổi `.39` → `.41` |
| DNS member | Tên member trả `.39` | Cùng tên trả `.41`; getent và nslookup đều được kiểm tra |
| SQL qua client Service | Hai dòng orders cũ | Vẫn đúng hai dòng, không CREATE/INSERT lại |

Identity giữ nguyên qua hai mốc:

- StatefulSet UID `166e577b-b842-4649-8ed2-141d4d8b98e8`, generation 1, revision `postgres-buoi14-76bf784c7`.
- PVC UID `52bbd1e9-90c9-4bc7-874d-04375ff258c1`; PV UID `a0575825-f2fe-4bfd-9133-491008dc2686`.
- Client Service UID `5295b58a-ff6e-4e0a-bb72-e4ab79410ba7`; headless Service UID `626a5725-38d7-40d6-a7db-fab8cb5cc850`.
- Client UID `dc34ede1-50c5-4251-aff9-bc234d7ad12a`, IP `192.168.194.40`, Ready/RESTARTS=0.

PV dùng `local.path` trên node orbstack, node affinity cùng node, reclaim Delete. Mountinfo trước/sau xác nhận `/var/lib/postgresql/data` là mount btrfs/source `/dev/vdb1`, filesystem root:

```text
/k8s/default/k3s/storage/pvc-52bbd1e9-90c9-4bc7-874d-04375ff258c1_default_data-postgres-buoi13
```

**Kiểm tra phần PostgreSQL:** metadata từ 16:46:24; mount, DNS và session SQL mới lúc 16:51:12. Deployment cũ vẫn replicas 0, StatefulSet replicas/Ready 1; server/client/PVC/PV/Services giữ identity sau thay Pod. Server/client image, command/args/env và nguồn-mount ứng dụng được đối chiếu manifest trước exec, không initContainer tái tạo orders. SQL từ client qua PGHOST cũ, transaction READ ONLY kết thúc ROLLBACK:

```text
database: labdb
server_address: 192.168.194.41
client_address: 192.168.194.40
data_directory: /var/lib/postgresql/data/pgdata
count: 2
101 | An   | 120000
205 | Binh | 85000
```

nslookup trực tiếp tới DNS `192.168.194.138` trả Service FQDN → `.177`, member FQDN → `.41`. Mountinfo vẫn đúng nguồn cũ; metadata sau đọc giữ Pod/client UID, Ready/RESTARTS=0. Không đọc/xuất Secret, pgpass hoặc credential. Snapshot không audit mọi command/thay đổi từ bên ngoài; đây là persistence qua thay Pod trên cùng node, không phải chứng minh HA/backup.

## 4. Storage association, lab PVC riêng và lifecycle

Với StatefulSet giả định `db` và template claim `data`, `volumeClaimTemplates` tạo claim riêng theo ordinal:

```diagram
┌──────────┐     ┌───────────┐
│ Pod db-0 │────▶│ data-db-0 │
└──────────┘     └───────────┘
┌──────────┐     ┌───────────┐
│ Pod db-1 │────▶│ data-db-1 │
└──────────┘     └───────────┘
```

Pod db-0 thay thế dùng lại claim của member 0 còn được giữ; không lấy claim của member 1. Claim mới không tự có byte từ claim cũ. StatefulSet không thiết lập PostgreSQL primary/replica, copy database, đồng bộ log hoặc failover. Việc đó thuộc ứng dụng/cơ chế replication riêng. Không dùng minh chứng PostgreSQL một claim cố định để khẳng định đã thử persistence với template nhiều claim.

### Lab hai member: phần đã kiểm chứng

Mentor đã đọc manifest/API và mountinfo trong lượt ôn lý thuyết ngày 2026-10-13, context `orbstack`, namespace `default`. StatefulSet `storage-buoi14` có replicas/Ready 2/2, template `data`, headless Service theo `serviceName`, OrderedReady và RollingUpdate. Không suy ra toàn bộ lịch sử lệnh hoặc thời điểm Ready từ snapshot.

| Member | PVC Bound | PV Bound |
|---|---|---|
| `storage-buoi14-0` | `data-storage-buoi14-0` | `pvc-39727993-d18c-4b89-9887-aa6422121e56` |
| `storage-buoi14-1` | `data-storage-buoi14-1` | `pvc-21874060-09e2-4c5b-b5b8-9340b3a2fece` |

- Pod 0 UID `f94cc127-da15-4383-a0f8-87a62c14a09a`, IP `192.168.194.43`; Pod 1 UID `c6aeba86-7e46-4e3b-816e-ff69b05a16b6`, IP `192.168.194.45`. Cả hai trên node `orbstack`, Ready và tham chiếu đúng claim của ordinal.
- PVC UID lần lượt `39727993-d18c-4b89-9887-aa6422121e56` và `21874060-09e2-4c5b-b5b8-9340b3a2fece`; PV UID tương ứng `fee27317-a922-41f3-814c-3d75d944372f` và `25ae05ea-b26d-421e-9f77-0c29b2936b20`, claimRef đúng UID. Hai claim dùng `local-path`, RWO, request 1Gi mỗi claim; hai PV reclaim Delete, nguồn local và node affinity `orbstack`.
- Image `busybox:1.36`, command/args/resources và mount data được đối chiếu scaffold trước exec; chỉ có container `app` chạy sleep, không initContainer hoặc startup logic tự tạo marker, không env/envFrom chứa credential.

Mountinfo xác nhận `/data` trong mỗi Pod dùng một filesystem root riêng:

```text
/k8s/default/k3s/storage/pvc-39727993-d18c-4b89-9887-aa6422121e56_default_data-storage-buoi14-0
/k8s/default/k3s/storage/pvc-21874060-09e2-4c5b-b5b8-9340b3a2fece_default_data-storage-buoi14-1
```

Cả hai là btrfs/source `/dev/vdb1`: hai thư mục riêng trên cùng filesystem/disk của node, không phải hai disk vật lý hoặc hai failure domain độc lập. Chưa đọc/ghi marker, lưu baseline nội dung hoặc đối chiếu Pod mới trong lab này; hai PVC Bound và hai Pod Ready không thay minh chứng đó.

### Ai tạo claim, ai cấp storage?

StatefulSet controller tạo PVC từ `spec.volumeClaimTemplates` qua API. PVC `storageClassName: local-path` chọn StorageClass có provisioner `rancher.io/local-path`; local-path-provisioner cấp nguồn storage/PV cho yêu cầu, không tạo các claim theo ordinal. Kubelet/runtime thực hiện mount. Khi chưa có PV phù hợp và provisioner ngừng, PVC vẫn có thể được tạo nhưng chờ provisioning/binding, Pod cần volume chưa chạy được; không nhất thiết thiếu disk vật lý hoặc tự chuyển sang `/data` ephemeral.

### Ready, ordering và giữ PVC

Với tạo ban đầu/scale up theo `OrderedReady`, member được tạo theo ordinal 0 → 1 → 2; đợi predecessor **Running và Ready**, không chỉ có object Pod hoặc đã Running. Scale down theo thứ tự ordinal cao xuống thấp, chờ kết thúc. Đây là lifecycle workload, không bảo đảm application-level replication hoặc thứ tự giao dịch dữ liệu. Một replica trong bài không đủ quan sát ordering; các tình huống này chỉ là theory/scenario, không scale PostgreSQL để thử.

Running là pha vòng đời, Ready là điều kiện sẵn sàng; readiness probe thất bại không tự restart container. BusyBox không khai báo probe ứng dụng nên Ready không chứng minh file hoặc persistence. Member 1 đã chạy không tự bị xóa chỉ vì member 0 về sau mất Ready. Xóa cả StatefulSet không có bảo đảm shutdown theo thứ tự như scale down; `spec.updateStrategy` là policy khác với `podManagementPolicy`.

Manifest storage không khai báo `spec.persistentVolumeClaimRetentionPolicy`; API đã mặc định `whenScaled: Retain`, `whenDeleted: Retain`. Policy này giữ PVC từ template khi giảm replicas hoặc xóa StatefulSet, không quản lý claim PostgreSQL cố định. `whenDeleted` không có nghĩa xóa từng Pod. PV reclaim policy Delete xử lý PV/backend khi PVC bị xóa, không kích hoạt chỉ vì Pod bị thay hoặc giảm replicas mà claim vẫn còn. Scale down/up dùng lại claim được giữ khi backend còn tồn tại là lý thuyết đã giảng, chưa chạy thí nghiệm retention/reclaim.

## 5. DNS: identity metadata không thay DNS server

Tên member trong lab:

```text
postgres-buoi14-0.postgres-buoi14-headless.default.svc.cluster.local
```

- StatefulSet/serviceName và Pod hostname/subdomain xác định network identity; headless Service/selector/EndpointSlice cung cấp thông tin backend để DNS publish record.
- CoreDNS là phần mềm trả lời DNS. `kube-dns` là Service dẫn truy vấn tới các CoreDNS Pod, không phải Service PostgreSQL hoặc một loại controller StatefulSet.
- Kubelet cấu hình resolver Pod theo cấu hình cluster và dnsPolicy. Client dùng ClusterFirst; `/etc/resolv.conf` trỏ `192.168.194.138`, search `default.svc.cluster.local svc.cluster.local cluster.local`.

```diagram
┌────────────┐  DNS :53  ┌─────────────────┐     ┌─────────────┐
│ Client Pod │─────────▶│ Service kube-dns│────▶│ CoreDNS Pod │
└────────────┘          │ 192.168.194.138 │     │ Trả lời DNS │
                        └─────────────────┘     └─────────────┘
```

CoreDNS trong snapshot 15:53:48 và lần kiểm tra DNS ở phần ôn lý thuyết Ready/available 1/1, kube-dns có backend Ready `192.168.194.2`. Service có cổng DNS UDP/TCP 53, selector `k8s-app=kube-dns`; Corefile có zone `kubernetes cluster.local`. Truy vấn nslookup mới từ client tới resolver `.138` tiếp tục trả Service PostgreSQL → `.177`, member 0 → `.41`; không truy vấn lại SQL trong lượt ôn này. DNS member thường cần Pod Ready, trừ cấu hình publishNotReadyAddresses; cache có thể làm thay đổi record chưa được quan sát ngay.

Headless vẫn có `type: ClusterIP` nhưng `clusterIP: None`, không có VIP và không được platform load-balance/proxy traffic như Service thường. DNS tên chung có thể trả nhiều Pod IP; client/thư viện mạng chọn địa chỉ và kết nối trực tiếp. DNS đầy đủ của member chọn đúng địa chỉ member. `serviceName` không tự tạo Service hoặc backend, selector phải khớp label; DNS chỉ tìm địa chỉ, không chuyển tiếp kết nối PostgreSQL.

**Scenario review, không phải lỗi thật:** database Ready và headless/EndpointSlice đúng, nhưng query DNS timeout và kube-dns không có backend Ready. Học viên chọn kiểm tra CoreDNS. Đạt nhận diện subsystem cần debug; mentor bổ sung kiểm tra Deployment/Pod CoreDNS, Ready/Events/logs và selector/EndpointSlice của kube-dns. Endpoint trống chưa đủ kết luận server crash: cũng cần loại trừ Service selector sai. Sửa StatefulSet không thay việc có DNS server phục vụ. Không phá DNS hoặc thực hành xử lý sự cố này trong lab.

## 6. Commands chỉ đọc để ôn/debug

Không apply lại `postgres-buoi13.yaml`: file cũ có replicas 1 và có thể khởi động thêm database trên cùng PVC. Giữ Deployment cũ ở 0 và không tăng StatefulSet trong mẫu claim cố định.

```bash
kubectl --context=orbstack -n default get statefulset postgres-buoi14
kubectl --context=orbstack -n default get pod postgres-buoi14-0 \
  -o custom-columns='NAME:.metadata.name,UID:.metadata.uid,IP:.status.podIP'
kubectl --context=orbstack -n default get pvc data-postgres-buoi13
kubectl --context=orbstack get pv pvc-52bbd1e9-90c9-4bc7-874d-04375ff258c1
kubectl --context=orbstack -n default get svc postgres-buoi13 postgres-buoi14-headless
kubectl --context=orbstack -n default get endpointslice \
  -l kubernetes.io/service-name=postgres-buoi14-headless
kubectl --context=orbstack -n default exec postgres-client-buoi13 -c client -- \
  nslookup postgres-buoi14-0.postgres-buoi14-headless.default.svc.cluster.local

kubectl --context=orbstack -n kube-system get deployment coredns
kubectl --context=orbstack -n kube-system get pods -l k8s-app=kube-dns
kubectl --context=orbstack -n kube-system get svc kube-dns
kubectl --context=orbstack -n kube-system get endpointslice \
  -l kubernetes.io/service-name=kube-dns
kubectl --context=orbstack -n default exec postgres-client-buoi13 -c client -- \
  cat /etc/resolv.conf

kubectl --context=orbstack -n default get statefulset storage-buoi14
kubectl --context=orbstack -n default get pod storage-buoi14-0 storage-buoi14-1
kubectl --context=orbstack -n default get pvc data-storage-buoi14-0 data-storage-buoi14-1
kubectl --context=orbstack get pv \
  pvc-39727993-d18c-4b89-9887-aa6422121e56 \
  pvc-21874060-09e2-4c5b-b5b8-9340b3a2fece
```

Trong thí nghiệm học viên đã dùng chuỗi scale Deployment về 0 → chờ Pod cũ được xóa → apply manifest StatefulSet mới → đợi rollout → tạo client còn thiếu. Sau baseline, học viên delete đúng Pod postgres-buoi14-0 với wait, không force; chờ object mới tồn tại và Ready. Không xóa StatefulSet/Services/Secret/PVC/PV hoặc chạy SQL ghi. Không lặp lại thao tác phá/thay Pod chỉ để ôn tài liệu.

## 7. Review phần đã học và giới hạn

| Chủ đề | Học viên trả lời và phần mentor bổ sung |
|---|---|
| Stable identity | Giữ tên Pod, không giữ object cũ vì UID thay đổi. Đạt. Tên DNS/hostname ổn định và IP mới đã có minh chứng live. |
| Storage theo ordinal | Pod db-0 dùng data-db-0; db-1 không tự nhận dữ liệu db-0. Sau ôn tiếp, trả lời ghi cùng pathname không tự xuất hiện ở Pod khác vì claim/PV riêng. Đạt trong scenario; association và mount hai member đã kiểm tra, file isolation chưa thử. |
| OrderedReady | Không tạo ngay member 1/2 khi member 0 chưa Ready; nêu thứ tự 0 → 1 → 2. Đúng kết luận/thứ tự; điều kiện đợi Running và Ready là mentor làm rõ, không ghi học viên tự nêu đủ điều kiện. |
| DNS ngoài lab | Ban đầu chưa trả lời được; sau giải thích, chọn kiểm tra CoreDNS khi đường DNS thiếu backend Ready. Đạt nhận diện dependency/hướng debug. Chi tiết kubelet, Corefile, selector và diagnostic commands là mentor bổ sung, không phải đã tự cấu hình cluster ngoài lab. |
| PVC/provisioner | Ban đầu nghĩ local-path-provisioner cũng tạo PVC từ template. Mentor tách StatefulSet controller tạo claim và provisioner cấp storage/PV. Học viên sau đó trả lời PVC vẫn được tạo khi provisioner ngừng; mentor chuẩn hóa “không có phần cứng” thành chưa provisioning/binding, không nhất thiết thiếu disk. |
| DNS từng member | Chọn đúng DNS đầy đủ của member 1 và trả lời selector không khớp thì serviceName đúng chưa đủ. Lý do “headless route traffic” được mentor sửa thành client chọn IP từ DNS; chưa có câu trả lời kiểm tra lại riêng sau phần sửa này. |
| Ready/retention | Đã giảng Running khác Ready, readiness không tự restart, OrderedReady và default PVC Retain khác PV reclaim Delete. Hai câu cuối về Ready có chứng minh file/persistence không và scale 2 → 1 → 2 dùng claim nào chưa được học viên trả lời khi yêu cầu chốt buổi. |

**Đã kiểm chứng thực hành:** chuyển controller PostgreSQL một instance giữ data/endpoint, thay chỉ Pod StatefulSet, cùng tên/UID mới, giữ PVC/PV/mount, DNS đổi địa chỉ và client đọc dữ liệu cũ; lab BusyBox hai member dùng template có hai claim/PV Bound và hai nguồn mount đúng/riêng.

**Chỉ giải thích/review:** dùng lại claim theo ordinal sau thay Pod với template riêng, file không tự đồng bộ, lifecycle nhiều ordinal, thiếu DNS server, lỗi kube-dns/CoreDNS, trade-off cố định claim và database replication. Ready/retention đã giảng nhưng chưa review cuối.

**Chưa kiểm chứng và không giao tiếp trong buổi này:** hai marker riêng và persistence qua thay Pod trong lab template, scale/retention/reclaim, nhiều database members, HA/replication/failover, mất node/disk, backup/restore, triển khai/khắc phục DNS hay storage ngoài lab. Không ghi các mục này là đã đạt; tổng kết không cho phép dọn dữ liệu hoặc tự thay workload.

## 8. OrbStack làm giúp ↔ cấu hình ngoài lab và liên hệ DE

**Trong lab:** OrbStack/môi trường cluster đã chuẩn bị node/runtime, CoreDNS/resolver và local-path provisioner/backend filesystem. Identity StatefulSet và headless Service là cơ chế Kubernetes, không phải tên miền Mac `orb.local`. Dữ liệu giữ ở nguồn local trên node, không phải StatefulSet copy dữ liệu từ Pod cũ.

**DNS tự quản lý/on-prem:** triển khai hoặc xác nhận DNS cluster như CoreDNS, Service/backend và đường UDP/TCP 53 hoạt động; zone trong Corefile khớp clusterDomain, kubelet clusterDNS trỏ resolver thích hợp, dnsPolicy Pod phù hợp. Quan hệ serviceName → headless Service → selector/EndpointSlice → hostname/subdomain cần đúng. CoreDNS phù hợp để dùng cùng mental model như lab; managed cloud có thể quản lý DNS add-on sẵn, giảm phần vận hành nhưng vẫn cần kiểm tra cấu hình/health thực tế. Không copy IP DNS lab sang cluster khác.

**Debug DNS:** từ resolver Pod/dnsPolicy và truy vấn nslookup → Service kube-dns/EndpointSlice/selector → CoreDNS Pod Ready/Events/logs/Corefile → wiring record member. Nếu query trả tên không tồn tại khác với timeout, cần điều tra record/readiness/cache thay vì mặc định server chết. Chỉ đọc logs đã kiểm tra an toàn; không dump env/Secret/credential.

**Storage tự quản lý/on-prem:** cần nguồn storage và PV cấp sẵn hoặc backend + controller/provisioner/CSI thích hợp; cấu hình StorageClass.provisioner/parameters/binding/reclaim/topology/quyền và claim/mountPath/đường ghi của app. Local đơn giản cho lab nhưng gắn node; remote/replicated backend có chi phí hạ tầng/vận hành riêng, không tự thay database replication/backup. Managed cloud có thể chuẩn bị driver/class, vẫn phải kiểm tra topology/attach và quyền thực tế.

**Debug storage:** PVC Bound/Events → class/provisioner/controller → PV source/claimRef/node affinity → Pod Events/mount → đường ghi PGDATA/backend. Giữ tên member/PVC không tự làm volume local khả dụng trên node khác; nếu byte mất thì API object không tái dựng được database. Thử thành công cùng node không chứng minh quota, node-failure recovery, HA hoặc backup.

**Data Engineering:** endpoint client ổn định, identity member, storage bền vững, replication và discovery là các trách nhiệm riêng. Phân biệt chúng trước khi dựng MinIO/object storage hoặc các hệ thống dữ liệu nhiều member; tăng replicas Kubernetes không đồng nghĩa đã có một data cluster đúng.

**Buổi 14 đã chốt theo yêu cầu học viên, tiến độ 14/28.** Không giao lại marker/thay Pod hoặc hai câu review còn lại. Điểm tiếp tục là [Buổi 15 - MinIO](../roadmap/buoi-hoc/15-minio.md), hiện Chưa học; chưa tự bắt đầu buổi mới. Giữ nguyên workload/dữ liệu, không chuyển PostgreSQL sang template hoặc scale database. Tài liệu/scaffold là thay đổi local chưa commit/push.

## Tài liệu tham khảo

- [StatefulSet Kubernetes v1.35](https://v1-35.docs.kubernetes.io/docs/concepts/workloads/controllers/statefulset/).
- [Service và headless Service v1.35](https://v1-35.docs.kubernetes.io/docs/concepts/services-networking/service/).
- [DNS cho Services và Pods v1.35](https://v1-35.docs.kubernetes.io/docs/concepts/services-networking/dns-pod-service/).
- [PV/PVC và StorageClass đã học](12-pv-pvc-storageclass.md).
- [PostgreSQL/client/credential đã học](13-postgresql-tren-kubernetes.md).
