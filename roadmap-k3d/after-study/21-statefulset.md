# Tổng kết Bài 21 — StatefulSet và danh tính dữ liệu

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/21-statefulset.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/22-backup-va-reclaim.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-18**, giờ Việt Nam (`Asia/Ho_Chi_Minh`). Bốn checkpoint lý thuyết và review cuối đúng **10/10**, trong đó review cuối `1B, 2C`.
- **Kiểm chốt:** **23:33:42–23:33:43 ngày 18/11/2026**, sau review. Hai Pod Ready, đúng PVC/PV và marker; tên riêng trả IP hiện tại, tên nhóm trả hai IP.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab` Active, UID `6d2e69f9-ada2-4699-af0d-2c98a3974710`. Học viên tạo tài nguyên, ghi file giả và xóa đúng một Pod. Mentor chuẩn bị scaffold, dùng client dry-run và chỉ kiểm tra runtime; không thay workload, node hay storage.

## 1. Mental model và các field đã đọc

| Resource / field | Điều cần nhớ |
|---|---|
| StatefulSet `metadata.name`, `spec.replicas` | Với ordinal mặc định từ 0, `marker` có hai thành viên `marker-0` và `marker-1`. Thay Pod vẫn giữ tên thành viên, nhưng `metadata.uid` là UID mới, IP có thể đổi và process memory cũ không được phục hồi. |
| StatefulSet `spec.selector.matchLabels` và `spec.template.metadata.labels` | Selector điều khiển nhóm Pod của StatefulSet; phải khớp nhãn trong Pod template. Trong lab cả hai dùng `app=marker,lesson=21`. |
| StatefulSet `spec.serviceName` ↔ Service `metadata.name` | `marker-peers` là Service do học viên tạo riêng cùng namespace. Controller đặt hostname theo tên Pod và subdomain theo `serviceName`; field này không tự tạo Service và không thay selector của Service. |
| Service `spec.clusterIP: None`, `spec.selector`, `spec.publishNotReadyAddresses: false` | Không có ClusterIP ảo và không chuyển tiếp traffic qua một IP Service. Selector chọn member; EndpointSlice chứa hostname, địa chỉ và readiness. DNS tên nhóm trả IP các endpoint sẵn sàng, tên riêng trả IP của member tương ứng. `publishNotReadyAddresses: true` có thể công bố địa chỉ trước khi Ready, nhưng không sửa lỗi ứng dụng. |
| StatefulSet `spec.volumeClaimTemplates[].metadata.name` và container `volumeMounts[].name` | Mẫu `data` tạo `data-marker-0` và `data-marker-1`. `volumeMounts[].name: data` khớp tên mẫu; đọc `Pod.spec.volumes[].persistentVolumeClaim.claimName` để biết Pod thực tế mount claim nào. Cùng `/data` không nghĩa cùng volume; StatefulSet không sao chép nội dung. |
| StatefulSet `spec.podManagementPolicy`, `spec.updateStrategy.type` | `OrderedReady` tạo 0 rồi chờ Ready trước khi tạo 1; scale-down bỏ ordinal cao trước. `Parallel` nới điều kiện chờ khi scale, không đổi thứ tự `RollingUpdate` mặc định trên v1.33. Đổi template với `RollingUpdate` thay từ ordinal cao xuống thấp; `OnDelete` không tự thay các Pod đang chạy. Các biến thể này chỉ học qua cấu hình và tình huống, không mở một thí nghiệm rollout hay scale-down. |
| StatefulSet `spec.persistentVolumeClaimRetentionPolicy` | `whenScaled: Retain`, `whenDeleted: Retain` giữ claim khi giảm replica/xóa cả set. Giảm `2 → 1` dự đoán bỏ Pod `marker-1` nhưng giữ `data-marker-1`. Xóa riêng một Pod vẫn thuộc số replica mong muốn không phải scale-down. |
| PV `spec.persistentVolumeReclaimPolicy`, `spec.local`, `spec.nodeAffinity` | Hai PV thực tế là local, affinity tới `agent-0`, reclaim `Delete`. Reclaim xử lý storage sau khi claim đã được giải phóng; không kích hoạt chỉ vì một Pod mất hoặc StatefulSet giữ claim khi scale. `Retain` cũng không tạo backup. |

## 2. Thiết kế phép thử

Client `/usr/local/bin/kubectl` **v1.33.9**, API server **v1.33.6+k3s1**. Đã kiểm `apps/v1`, `v1`, `discovery.k8s.io/v1` và API schema của trường retention. Class `local-path` dùng `rancher.io/local-path` v0.0.32, `WaitForFirstConsumer`, reclaim `Delete`, annotation `defaultVolumeType: local`. CoreDNS v1.13.1 và provisioner đều Ready lúc preflight; cluster domain `cluster.local`. Ví dụ chỉ dùng DNS nội bộ, không cài thêm add-on, Traefik hay LoadBalancer.

| Scaffold | Vai trò |
|---|---|
| [01-headless-service.yaml](../thuc-hanh/21-statefulset/01-headless-service.yaml) | `marker-peers` chỉ tra bản ghi địa chỉ, không khai báo cổng vì không kiểm listener hoặc SRV. |
| [02-statefulset.yaml](../thuc-hanh/21-statefulset/02-statefulset.yaml) | Hai Pod trên `k3d-de-k3d-agent-0`, mỗi Pod một PVC `local-path` RWO, yêu cầu `128Mi` và mount `/data`; giữ claim. Cùng node để cô lập việc thay Pod khỏi việc thay topology. |
| [03-dns-client.yaml](../thuc-hanh/21-statefulset/03-dns-client.yaml) | Pod độc lập `marker-dns-client`, tạo sau khi thay `marker-0`, dùng DNS `ClusterFirst`, không PVC và không khớp selector của Service. `restartPolicy: Never`; `sleep` kết thúc thì Pod không tự chạy lại. |

Ba file qua client dry-run/schema; việc đó không phải minh chứng chạy. BusyBox `1.37.0` pin image index `sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec`, đã kiểm metadata `linux/arm64/v8`. Các container chỉ `sleep 86400`, không tự ghi marker, không khai báo env/envFrom và không mount API token. Học viên ghi `/data/lesson21-marker.txt` một lần ở mỗi member, kiểm mount point và không ghi đè file. Mọi lượt sau chỉ đọc để không che mất dữ liệu.

## 3. Runtime và bằng chứng

### 3.1 Thay đúng một Pod, giữ đúng hai volume

- Lượt baseline từ **15:31:44**: hai Pod Ready cùng `agent-0`; `/data` đã mount và chưa có marker. Mentor xác nhận hai file đúng nội dung vào **16:25:41**, trước khi thay Pod.
- Học viên xóa riêng `marker-0` bằng `DeleteOptions.preconditions.uid` trong đúng namespace; không force-delete, không giảm `replicas`, không xóa claim. API ghi event `Killing` cho UID cũ lúc **23:15:22**. Pod mới tạo lúc **23:15:28**, được mentor xác nhận lúc **23:17:21**.
- Lần `exec` đầu học viên thấy `cannot exec into a container in a completed pod; current phase is Failed`. Client từ chối trước khi chạy `cat` vì Pod được đọc đang ở phase cuối. Điều này phù hợp với Pod cũ đang bị xóa, nhưng dòng lỗi không ghi UID để khẳng định. Lượt sau học viên đọc đúng cả hai marker; khi quan sát lại, chờ UID mới và Ready, không xóa lần nữa hay ghi lại file.

| Mốc | Pod | UID | IP | Claim |
|---|---|---|---|---|
| Trước thay | `marker-0` | `010e5b6c-380a-475e-89b3-c54e7b577386` | `10.42.3.98` | `data-marker-0` |
| Sau thay | `marker-0` | `7ab1caa6-2514-4aad-be21-f1074e338f46` | `10.42.3.101` | `data-marker-0` |
| Trước và sau, đối chứng | `marker-1` | `44ec866b-a3d8-4346-b665-f57df43e1966` | `10.42.3.100` | `data-marker-1` |

| PVC Bound | UID PVC | PV Bound | UID PV | Nội dung file (cộng newline) |
|---|---|---|---|---|
| `data-marker-0` | `33fe38b4-249d-4139-bdd5-5717f3ae4871` | `pvc-33fe38b4-249d-4139-bdd5-5717f3ae4871` | `a172b7b2-82ed-4b21-a2ee-d6b4d2a2e15e` | `lesson21-member-0` |
| `data-marker-1` | `9280ea8f-61ef-4db0-9f57-5c9d38510c52` | `pvc-9280ea8f-61ef-4db0-9f57-5c9d38510c52` | `6aa9fcaa-c9cb-4b15-8e34-2b5969935492` | `lesson21-member-1` |

Đối chiếu cả hai chiều `PVC.spec.volumeName` ↔ `PV.spec.claimRef` (namespace, tên, UID). Hai cặp giữ nguyên UID ở các lượt kiểm; hai marker khớp chính xác **18 byte/file**. StatefulSet `marker` giữ UID `12728c75-94a5-4a45-9bb0-00634c73b58e`, generation 1, Ready 2/2. Service `marker-peers` giữ UID `d000a100-b69e-4ff5-8f83-7f792f36a9ca`, `ClusterIP=None`.

### 3.2 DNS sau khi thay Pod

Trước khi thay, mentor tra từ `marker-1` thấy tên của `marker-0` trả `10.42.3.98`. Client mới UID `8322d86c-ad3d-4940-ab51-b900a5630f75` được tạo lúc **23:22:48** trên `k3d-de-k3d-agent-1`, IP `10.42.1.93`; không phải backend. Học viên dùng `nslookup -type=A` và mentor tra độc lập từ đúng client vào **23:25:22** và ở lượt chốt.

| Tên được hỏi trong `de-lab.svc.cluster.local` | `Address` dưới `Name` sau khi thay |
|---|---|
| `marker-0.marker-peers` | `10.42.3.101` |
| `marker-1.marker-peers` | `10.42.3.100` |
| `marker-peers` | `10.42.3.100` và `10.42.3.101`, thứ tự không quan trọng |

EndpointSlice `marker-peers-sphzp` UID `29234231-58db-4f8a-8a9f-05a0282757bf` có đúng hai hostname/IP và `targetRef.uid` tương ứng Pod hiện tại, đều Ready. `Server: 10.43.0.10` trong output của học viên là resolver trả lời, không phải endpoint ứng dụng. Client mới không xóa cache ở CoreDNS; kết quả đúng một lần không đo TTL và không xác nhận một ứng dụng khác đã bỏ IP cũ.

## 4. Lệnh tái quan sát → output → cách đọc

Các lệnh chỉ đọc; không chạy lại lệnh xóa bằng UID cũ hoặc lệnh ghi marker. Dừng nếu không thấy `k3d-de-k3d` và `de-lab Active`.

```bash
K21=(/usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" --context=k3d-de-k3d -n de-lab)
"${K21[@]}" config get-contexts k3d-de-k3d -o name
"${K21[@]}" get namespace de-lab -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase'
```

```bash
"${K21[@]}" get pods -l 'app=marker,lesson=21' \
  -o 'custom-columns=NAME:.metadata.name,UID:.metadata.uid,READY:.status.conditions[?(@.type=="Ready")].status,CLAIM:.spec.volumes[?(@.name=="data")].persistentVolumeClaim.claimName'
```

Snapshot chốt, trình bày theo các cột trên:

```text
NAME       UID                                    READY   CLAIM
marker-0   7ab1caa6-2514-4aad-be21-f1074e338f46   True    data-marker-0
marker-1   44ec866b-a3d8-4346-b665-f57df43e1966   True    data-marker-1
```

`UID` khác nhưng `NAME` và `CLAIM` giống chưa đủ chứng minh dữ liệu còn. Phải đối chiếu UID hai tầng storage ở mục 3.1 và đọc **file cũ**, không tạo lại file nếu thiếu.

```bash
for n in 0 1; do
  "${K21[@]}" exec "marker-$n" -c worker -- cat /data/lesson21-marker.txt || break
done
```

Học viên thấy `lesson21-member-0` rồi `lesson21-member-1`; mentor kiểm độc lập bằng so byte với giá trị kỳ vọng sau khi xác minh mount và identity. Hai dòng khác nhau ở cùng `mountPath` là bằng chứng hai nguồn storage trong fixture này.

```bash
for name in marker-0.marker-peers marker-1.marker-peers marker-peers; do
  "${K21[@]}" exec marker-dns-client -c dns -- \
    nslookup -type=A "${name}.de-lab.svc.cluster.local." || break
done
```

Đọc `Name` và `Address` như bảng mục 3.2; IP và thứ tự có thể thay đổi khi quan sát lại. Nếu DNS còn trả IP cũ, xem UID/IP/Ready của Pod, EndpointSlice rồi kiểm DNS từ phía client và cache; không xóa Pod hay claim để làm mới DNS.

## 5. Review, yêu cầu DevOps và giới hạn

| Lượt | Kết quả |
|---|---|
| Danh tính và claim từng ordinal | `1B, 2C`: cùng tên, UID mới, dùng claim cũ còn tồn tại; hai file không tự đồng bộ. |
| DNS từng member và readiness | `1C, 2A`: dùng FQDN riêng để gọi đích cố định; `Running` chưa Ready thì tên có thể tạm chưa công bố. |
| Scale và đổi template | `1B, 2A`: `OrderedReady` đợi ordinal trước; `Parallel` không làm rolling update mặc định chạy song song. |
| PVC retention và PV reclaim | `1C, 2A`: claim còn thì chưa kích hoạt PV reclaim; `whenScaled: Delete` áp dụng khi giảm replica, không phải thay Pod đang được mong muốn. |
| Review cuối | `1B, 2C`: nếu client riêng tra IP mới nhưng ứng dụng còn gọi IP cũ, kiểm resolver/cách lưu địa chỉ và reconnect của ứng dụng. Với PostgreSQL, endpoint ghi phải theo primary hiện tại, không suy từ ordinal hay việc hai Pod đều Ready. |

- **Lab làm giúp:** K3s cung cấp CoreDNS và provisioner `local-path`; StatefulSet là controller Kubernetes, không phải tính năng riêng k3d. Ngoài lab tự quản lý, DevOps cần cung cấp DNS nội bộ và class/provisioner hoặc PV chuẩn bị sẵn; managed có thể cung cấp sẵn các thành phần nhưng DE vẫn phải hỏi cluster domain, class/driver được phép và topology. Khi PVC đã Bound mà Pod chưa có node, kiểm giao giữa ràng buộc của Pod và `PV.spec.nodeAffinity`; khi Pod đã Ready mà tên thiếu, kiểm `serviceName`, selector, EndpointSlice và resolver/cache theo thứ tự.
- **Data Engineering:** ghi rõ member nào giữ dữ liệu nào, storage có thể gắn lại ở đâu, ai giữ/xóa claim, và endpoint nào chỉ tới writer hợp lệ. Replication, chọn primary/failover, consistency và backup/restore thuộc ứng dụng hoặc hệ thống vận hành riêng; không suy từ `replicas: 2` hay Headless Service.
- **Giới hạn:** đã kiểm thay Pod cùng node, hai marker riêng và DNS nội bộ từ client trên agent khác. Không kiểm TCP/HTTP ứng dụng, DNS bên ngoài, rollout/scale-down thật, xóa PVC/PV, mất node/disk/host, gắn lại bằng CSI, PostgreSQL, database HA hay restore. Các node k3d vẫn dùng chung host.

## 6. Bàn giao

Giữ StatefulSet, Headless Service, EndpointSlice, hai member, hai PVC/PV, một DNS client và ba scaffold. Ở lượt chốt cả ba Pod Running/Ready/restart 0, ba node Ready/ARM64, không cordon/taint/pressure. Không có cleanup bắt buộc, không chạy lại guard/lệnh ghi, chưa mở hay tạo scaffold Bài 22.

- [Kubernetes v1.33 — StatefulSet, identity, rollout và retention](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/controllers/statefulset/) · [DNS cho Service và Pod](https://v1-33.docs.kubernetes.io/docs/concepts/services-networking/dns-pod-service/) · [PV reclaim](https://v1-33.docs.kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming).
- [Vòng đời và phase của Pod v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) · [Kiểm phase trong `kubectl exec` v1.33.9](https://github.com/kubernetes/kubernetes/blob/v1.33.9/staging/src/k8s.io/kubectl/pkg/cmd/exec/exec.go).
- [Local Path Provisioner v0.0.32](https://github.com/rancher/local-path-provisioner/blob/v0.0.32/README.md) · [BusyBox 1.37.0 registry metadata](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0).
