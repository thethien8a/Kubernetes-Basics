# Tổng kết Bài 12 — Bảo trì node, PDB và node failure

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/12-disruptions.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/13-pod-network.md)

- **Kết luận:** Bài 12 đã học xong và được chốt theo phạm vi học viên yêu cầu ngày **2026-11-08**, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phần thực hành đã đạt:** hai đối chứng Eviction API; drain bị PDB chặn/được phép; cordon–uncordon; khôi phục hai Pod về hai agent.
- **Phần node failure:** chỉ học lý thuyết theo lựa chọn của học viên, không nghiệm thu mô phỏng dừng/bật agent, node unavailable hoặc thời gian failover như đã thực hành. Không giao lại phần này hoặc yêu cầu làm bù để chuyển bài.
- **Phân biệt bằng chứng:** đã đóng nội dung học không đồng nghĩa có đủ toàn bộ thực hành của đề gốc. Tiến độ học là 12/32; tổng nghiệm thu đầy đủ theo yêu cầu gốc vẫn 10/32, giống cách tách xác nhận và bằng chứng ở Bài 08.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`; Docker context `orbstack` chỉ là engine chạy k3d, không phải cluster Kubernetes `orbstack`.
- **Phiên bản đã kiểm:** `/usr/local/bin/kubectl` v1.33.9, API server v1.33.6+k3s1, nodes ARM64; container node dùng `rancher/k3s:v1.33.6-k3s1`.
- **Kiểm tra đóng bài:** chỉ đọc lúc **13:12:57 ngày 2026-11-08**. Giữ workload và manifest; không thực hiện hoặc ghi nhận cleanup, không tự xóa tài nguyên thay học viên.

## 1. Bài toán cần hiểu

Bảo trì có kế hoạch và node ngừng hoạt động là hai tình huống khác nhau:

```text
Bảo trì qua drain:
  Cordon node → yêu cầu eviction → PDB xét ngân sách → cho phép/từ chối

Node ngừng hoạt động:
  Workload mất khả năng phục vụ → control plane phát hiện và xử lý
  → controller có thể tạo Pod thay thế trên node hợp lệ khác
```

PDB giới hạn gián đoạn qua Eviction API, không giữ máy hoạt động, tự cấp thêm capacity, bảo vệ dữ liệu hoặc bảo đảm thời gian phục hồi. Replicas mô tả desired state; có Pod mới không đồng nghĩa tác vụ ETL dở dang hoặc dữ liệu đã được phục hồi đúng.

## 2. Concept và field quan trọng

| Resource/field | Ý nghĩa và giới hạn đã học |
|---|---|
| Node `spec.unschedulable` | Cordon đặt cờ chặn scheduling thông thường mới, không tự đuổi Pod hiện có. |
| Node `status.conditions[type=Ready]` | Sức khỏe node độc lập với cờ cordon. `Ready,SchedulingDisabled` có nghĩa node còn khỏe nhưng đang khóa scheduling; SchedulingDisabled không phải condition API riêng. |
| `kubectl drain` | Cordon trước, kiểm tra Pod rồi mới xử lý eviction. Không phải giao dịch tự rollback: lỗi, timeout hoặc Ctrl+C không tự uncordon. |
| `--ignore-daemonsets` | Bỏ qua Pod do DaemonSet quản lý, không xóa chúng và không bỏ qua PDB. |
| `--timeout` của drain | Giới hạn thời gian chờ thao tác drain, không phải deadline phục hồi node hoặc ứng dụng. |
| `--force` | Cho phép xử lý Pod không controller; không phải cách chữa PDB và có thể làm mất Pod bài khác không được controller tạo lại. Không dùng trong lab này. |
| `--disable-eviction` | Chuyển sang delete, bỏ qua kiểm tra PDB; không dùng để hoàn thành đối chứng. |
| PDB `spec.selector.matchLabels` | Chọn nhóm Pod trong cùng namespace, không chọn Node hoặc dựa vào tên Deployment. Lab khớp `app=disruption-lab` AND `lesson="12"`. |
| PDB `spec.minAvailable` | Số healthy tối thiểu cần giữ khi xét eviction. Mức sàn cố định có ý nghĩa khác với giới hạn số unavailable khi scale thay đổi. |
| PDB `spec.maxUnavailable` | Giới hạn số replica unavailable theo nhóm. Chỉ chọn một trong minAvailable/maxUnavailable. Không phải quota cho mỗi node hoặc tổng số lần được evict. |
| PDB `status.currentHealthy` | Số Pod healthy hiện được controller tính; Running chưa đủ, health của PDB dựa trên condition Ready. |
| PDB `status.desiredHealthy` | Số healthy cần giữ theo ngân sách. |
| PDB `status.disruptionsAllowed` | Ngân sách eviction tại thời điểm quan sát, không bảo đảm capacity hoặc readiness của Pod thay thế. Status cập nhật bất đồng bộ. |
| Deployment `spec.strategy.rollingUpdate.maxUnavailable` | Điều khiển rollout, khác resource/phạm vi với PDB maxUnavailable. PDB không điều khiển rollout hay chặn xóa trực tiếp Pod/Deployment. |
| Pod `metadata.uid`, `ownerReferences`, `deletionTimestamp` | Nhận diện đúng object/lần chạy, controller chịu trách nhiệm và quá trình kết thúc; Pod thay thế là UID mới, không phải Pod cũ được chuyển nguyên trạng. |
| Eviction `deleteOptions.preconditions.uid` | Chỉ cho phép xóa đúng object mang UID đã kiểm tra; không dùng lại UID của Pod đã bị thay thế. |
| Pod `spec.tolerations[]` | Live Pod có NoExecute tolerations cho not-ready/unreachable, mỗi loại 300 giây; scaffold không khai báo rõ phần này. Đây là cấu hình quan sát được, không phải RTO 300 giây từ lúc máy hỏng. |

PDB không chặn mọi nguồn unavailable. Pod mất readiness hoặc node failure vẫn có thể làm healthy giảm; các unavailable này ảnh hưởng ngân sách tiếp theo.

## 3. Scaffold và lựa chọn cấu hình

- [01-disruption-lab.yaml](../thuc-hanh/12-disruptions/01-disruption-lab.yaml): Deployment `disruption-lab`, namespace `de-lab`, replicas=2.
- [02-pdb.yaml](../thuc-hanh/12-disruptions/02-pdb.yaml): PDB `disruption-budget`, cùng selector Pod; **giá trị cuối là minAvailable=2**.

| Lựa chọn | Lý do và giới hạn |
|---|---|
| Required node affinity theo hostname hai agent | Giữ workload thí nghiệm khỏi server, không đổi labels/taints của Node. Hostname đã đối chiếu live, không mặc định tên node luôn bằng label ở mọi hệ thống. |
| Preferred Pod anti-affinity theo hostname, weight=100 | Ưu tiên tách worker nhưng cho phép chạy chung agent còn lại khi drain. Không bảo đảm 1/1 hoặc xác suất 100%; baseline phải được quan sát. |
| Requests 25m/32Mi, limits 100m/64Mi mỗi worker | Ngân sách nhỏ cho ứng dụng giả; requests không phải usage, không cộng allocatable các node k3d để suy tài nguyên vật lý. |
| BusyBox pin digest, IfNotPresent | Metadata registry đã xác nhận ARM64; có thể dùng cache, không coi runtime thành công là vừa pull mới. |
| Shell chờ, trap TERM/INT; grace period 10 giây | Không xử lý dữ liệu thật; có đường thoát khi shutdown, không suy đo mọi container cũ đã exit graceful từ snapshot sau xóa. |
| Không volume, không mount token ServiceAccount | Worker không cần dữ liệu bền vững hoặc gọi API. Không thực hành storage/fencing. |
| Không readiness probe | Ready của worker giả không chứng minh một API, ETL hoặc pipeline thật xử lý nghiệp vụ đúng. |

Image reference của scaffold:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

## 4. Bằng chứng thực hành

Các mốc dưới đây theo giờ Việt Nam. Dòng phản hồi CLI là output học viên đã cung cấp; đối chiếu resource/UID/status là mentor tự kiểm tra chỉ đọc. Snapshot không phải audit đầy đủ mọi lệnh hoặc toàn bộ lịch sử.

### 4.1 Eviction API bị chặn và được phép

| Đối chứng | Quan sát đã kiểm chứng |
|---|---|
| Hai healthy, minAvailable=2 | Học viên nhận `TooManyRequests: Cannot evict pod as it would violate the pod's disruption budget.` Pod ngwml UID a61b423d-0500-4868-a900-f7d2507064cc và buddy sds8g giữ UID, Ready; PDB healthy/required/allowed=2/2/0. Mentor kiểm lại ngày 06/11. |
| Đổi minAvailable=1 | PDB hội tụ healthy/required/allowed=2/1/1, chưa có Pod nào tự bị evict chỉ vì đổi PDB. |
| Gửi Eviction cho ngwml, kèm UID precondition | Học viên quan sát response `status=Success`, `code=201`. Ngwml không còn; 5f79z UID 1c620a36-c005-4e2d-860c-b9d99452b093 Ready trên agent-0; sds8g giữ UID trên agent-1. Cùng ReplicaSet, không phải chuyển nguyên Pod cũ. Mentor đối chiếu lúc 23:57 ngày 06/11. |

Request Eviction được gửi tới subresource `/api/v1/namespaces/de-lab/pods/<pod-name>/eviction`, dùng body `policy/v1`, không apply như Deployment. Success chỉ xác nhận yêu cầu được chấp nhận; cần kiểm tra riêng Pod thay thế Ready và PDB hồi phục. Snapshot cuối không chứng minh học viên đã bắt gặp khoảng disruptionsAllowed=0 trong chuyển tiếp.

### 4.2 Pod ngoài bài chặn drain trước bước PDB

Ngày 07/11, preflight 13:39 chỉ thấy worker Bài 12 và ServiceLB trên agent. Các bare Pods `nfk-17a/be-1`, `be-2`, `client` được tạo lúc 13:44, trước lượt drain của học viên.

Học viên quan sát:

```text
node/k3d-de-k3d-agent-0 cordoned
cannot delete Pods that declare no controller (use --force to override): nfk-17a/be-1
```

Lượt này dừng ở bước kiểm tra Pod, **không tính là PDB đã chặn eviction**. Học viên uncordon, không dùng --force và không xóa tài nguyên bài kia. Mentor kiểm lúc 13:54 xác nhận Node phục hồi và worker giữ UID. Đây là bài học về inventory có thể thay đổi giữa preflight và thao tác; cần cửa sổ bảo trì có phối hợp, không chỉ một snapshot sạch.

### 4.3 Drain thực sự bị PDB chặn

Sau khi bài kia hoàn tất, mentor kiểm lại phạm vi lúc 17:14 ngày 07/11: agent chỉ có worker Bài 12 và ServiceLB. PDB minAvailable=2, healthy/required/allowed=2/2/0.

Học viên chạy drain với `--ignore-daemonsets --timeout=60s`, quan sát cordon thành công và các lần retry có thông báo:

```text
Cannot evict pod as it would violate the pod's disruption budget.
```

Học viên **Ctrl+C**, nhìn thấy `Ready,SchedulingDisabled`, sau đó tự uncordon về Ready. Đối chứng PDB chặn đạt; **không ghi đã quan sát timeout 60 giây** và không bắt chạy lại chỉ để chờ timeout. Mentor kiểm lúc 17:22: hai worker giữ UID, Ready/restart=0, Node không cordon, PDB 2/2/0.

### 4.4 Drain được phép và khôi phục phân bố

Với minAvailable=1, học viên chạy drain Agent 0 với timeout 90 giây và cung cấp:

```text
pod/disruption-lab-794fbd4f97-5f79z evicted
node/k3d-de-k3d-agent-0 drained
```

Trong lúc Agent 0 còn `Ready,SchedulingDisabled`, học viên quan sát:

- Pod thay thế `8blzf`, UID e6fd4194-e40d-4733-b6e1-a6ebe8548180, Ready trên agent-1.
- Buddy `sds8g` vẫn UID 811967b6-f733-4f32-a2eb-7580c5dafafc trên agent-1.
- PDB trở lại healthy/required/allowed=2/1/1.

Học viên uncordon. Mentor kiểm lại lúc **20:53 ngày 07/11**: 5f79z không còn, cả hai worker Ready trên agent-1, cùng ReplicaSet, ba Node Ready/không cordon. Drain thành công và workload phục hồi đã được đối chiếu riêng.

Uncordon không tự rebalance. Một eviction có UID precondition cho 8blzf sau đó tạo Pod `vr87m`, UID a68c6d69-0112-44a8-bd7a-3ed838d83b0c, trên agent-0. Mentor kiểm lúc **21:11 ngày 07/11** xác nhận baseline 1/1, buddy sds8g giữ UID. Đây là một lần scheduler thực sự chọn agent-0, không phải bảo đảm của preferred trong mọi tình huống.

## 5. Lý thuyết node failure và giới hạn nghiệm thu

Đã giảng và kiểm tra các điểm:

- Kubelet gửi heartbeat qua Node status và Lease; `Ready=Unknown` nói control plane không xác nhận được sức khỏe node, không chứng minh tiến trình ứng dụng đã chết.
- Pod còn hiển thị Running có thể là trạng thái API cũ, không phải phép kiểm tra trực tiếp container trên node mất liên lạc.
- Node conditions liên quan taints not-ready/unreachable; Pod có NoExecute tolerations 300 giây. Khoảng này gắn với taint tương ứng, không phải thời gian phục hồi đầu-cuối tính từ lúc node hỏng.
- Sau phát hiện/chịu taint vẫn còn xử lý deletion, controller tạo Pod, scheduling, image startup và readiness; Pod cũ có thể còn Terminating. Không force-delete stateful Pod chỉ vì node mất liên lạc.
- PDB không ngăn sự cố hạ tầng; replicas/PDB không thay retry, checkpoint, backup hoặc bảo đảm pipeline không gián đoạn.
- Kế hoạch 8 phút từng được đưa ra chỉ là giới hạn an toàn của thí nghiệm dự kiến, không phải SLA/RTO của Kubernetes.

Học viên phản hồi chưa hiểu mục đích thí nghiệm; mentor đã quay lại bài toán bảo trì có kế hoạch so với mất node, giải thích mục tiêu phục hồi workload thay vì học Docker stop. Ngày 08/11, học viên quyết định **phần này chỉ cần lý thuyết và yêu cầu chốt bài ngay**.

Vì vậy, không ghi thành đã quan sát: stop/start agent, node unavailable, thời điểm NoExecute eviction, healthy giảm dưới minAvailable hoặc thời gian failover/recovery. Không dùng lý thuyết hoặc quiz để thay bằng chứng runtime đó, nhưng cũng không giữ chúng thành bài tập bù hay điều kiện chặn Bài 13.

## 6. Review và nhầm lẫn đã xử lý

| Tình huống trắc nghiệm đã trả lời | Kết quả |
|---|---|
| PDB minAvailable=2 với hai healthy; node hỏng không bị PDB ngăn | 1B, 2A — đúng. |
| Cordon không đuổi Pod; uncordon không tự phân bố lại | 1B, 2C — đúng. |
| Drain xong nhưng Pod thay thế có thể Pending | C — đúng. |
| Running nhưng chưa Ready chưa bổ sung healthy cho PDB | A — đúng. |
| Giữ tối đa một unavailable khi scale thay đổi | B, chọn maxUnavailable=1 — đúng. |
| Drain timeout không tự rollback cordon | B — đúng. |
| Eviction riêng một Pod không tự cordon Node | B — đúng. |
| Node Unknown và Pod Running chưa đủ kết luận runtime thực | C — đúng. |
| Toleration 300 giây không cam kết Pod mới Ready sau đúng 300 giây | B — đúng. |

Các đáp án trên là lựa chọn trắc nghiệm, không ghi thành học viên đã tự trình bày mọi lời giải. Khi học viên hỏi vì sao drain lỗi mà Node vẫn SchedulingDisabled, mentor đã giải thích lại tính nhiều bước/không tự rollback và phân biệt Node Ready với cờ unschedulable.

Các lỗi nhập shell `heredoc>` hoặc dấu `\` cuối dòng được phân biệt với lỗi Kubernetes; chỉ dùng response hoàn chỉnh và kiểm tra resource làm minh chứng, không suy số request từ đoạn nhập dở.

## 7. Lệnh tái quan sát và trạng thái khi đóng bài

Helper dùng đúng binary/kubeconfig/context; không in credential:

```bash
k12() {
  /usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" \
    --context k3d-de-k3d --namespace de-lab \
    --request-timeout=10s "$@"
}

k12 get pods -l app=disruption-lab,lesson=12 \
  -o custom-columns='NAME:.metadata.name,UID:.metadata.uid,READY:.status.conditions[?(@.type=="Ready")].status,NODE:.spec.nodeName'

k12 get pdb disruption-budget \
  -o custom-columns='NAME:.metadata.name,MIN:.spec.minAvailable,HEALTHY:.status.currentHealthy,REQUIRED:.status.desiredHealthy,ALLOWED:.status.disruptionsAllowed'
```

Snapshot mentor kiểm lúc **13:12:57 ngày 08/11**, không phải output tương lai:

```text
NAME                              UID                                    READY   NODE
disruption-lab-794fbd4f97-sds8g     811967b6-f733-4f32-a2eb-7580c5dafafc   True    k3d-de-k3d-agent-1
disruption-lab-794fbd4f97-vr87m     a68c6d69-0112-44a8-bd7a-3ed838d83b0c   True    k3d-de-k3d-agent-0

NAME                MIN   HEALTHY   REQUIRED   ALLOWED
disruption-budget   2     2         2          0
```

Đọc UID để nhận diện đúng Pod, READY/NODE để thấy baseline 1/1; ALLOWED=0 phù hợp với giữ hai healthy khi chỉ có hai replicas. Namespace không giới hạn tác động của thao tác lên Node vì Node là cluster-scoped.

| Resource còn giữ | UID |
|---|---|
| Deployment disruption-lab | 6e946b97-e3da-4440-8f6d-b550e8ac5fd7 |
| ReplicaSet disruption-lab-794fbd4f97 | 0deeee0d-dfd6-414b-bb76-3fd3d2783aa2 |
| PDB disruption-budget | bf560dcd-db13-4b3c-9a65-84460dddb0fb |

Ba Node Ready=True, không taint/cordon; UID agent-0/agent-1/server-0 lần lượt là 4ea95101-66d2-4a51-bf3e-c3d47602425d, 09b5909c-9cf8-4432-95c6-bda7167922f3, 15152848-8931-45f4-a706-a61e4f1e87db. Docker metadata cho thấy cả ba node container running; StartedAt agent-0 vẫn 2026-11-06T02:19:35.117686105Z. Đây là trạng thái cuối, không phải bằng chứng đã chạy node failure.

Không thực hiện hoặc ghi nhận cleanup. Mentor không stop/start/restart container, sửa/apply/delete workload hoặc ghi credential. Các Pod ngwml, 5f79z và 8blzf đã bị thay thế: không chạy lại request eviction theo tên/UID cũ để tái hiện lịch sử.

## 8. Lab làm giúp, ngoài lab cần gì?

- Cordon, PDB, Eviction API, ReplicaSet và scheduler là cơ chế Kubernetes; k3d/K3s cung cấp môi trường node-container thuận tiện để quan sát, không tạo ra HA vật lý. Các node chung Mac/runtime/disk.
- ServiceLB svclb-traefik là add-on K3s trong lab, không phải mặc định của mọi Kubernetes. Khi drain, phải inventory mọi namespace và nhận diện DaemonSet/networking/storage thay vì mặc định được phép xóa mọi Pod hệ thống.
- On-prem cần platform cung cấp node pool/labels/capacity dự phòng, quyền và quy trình bảo trì/phục hồi máy. Managed cloud có thể tự động hóa một phần, nhưng vẫn phải xác nhận công cụ tôn trọng PDB, node/failure policy, quota và placement thực tế.
- Debug theo thứ tự: đúng context/namespace/UID → inventory node ở mọi namespace → controller owner, volume/data cần giữ → PDB selector/readiness/status → capacity/placement/taints → Events của replacement. Khi node mất liên lạc, thêm Node conditions/Lease và tolerations; không bỏ qua hàng rào bảo vệ để làm test nhanh.
- DE cung cấp tiêu chí health, mức gián đoạn chấp nhận được, shutdown/retry/checkpoint; platform xác nhận maintenance window, capacity và quyền Node. Quyền admin lab không phải quyền DE mặc định.
- Chưa kiểm chứng zero downtime, ETL đúng, dữ liệu/backup/replication, HA khi mất host, network partition hoặc thời gian phục hồi production.

**Điểm tiếp tục:** chờ Bài 13 theo nhịp học viên. Không mở lại Bài 12, không giao phần node failure thành bài tập bù, không tự cleanup các workload đang giữ.

## Nguồn

- [Disruptions — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/disruptions/).
- [Cấu hình PDB](https://v1-33.docs.kubernetes.io/docs/tasks/run-application/configure-pdb/).
- [Safe drain](https://v1-33.docs.kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/).
- [API-initiated Eviction](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/api-eviction/).
- [Taints and tolerations](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/).
- [Node Status](https://v1-33.docs.kubernetes.io/docs/reference/node/node-status/).
- [Luồng drain trong kubectl v1.33.9](https://github.com/kubernetes/kubernetes/blob/v1.33.9/staging/src/k8s.io/kubectl/pkg/cmd/drain/drain.go).
- [Metadata BusyBox 1.37.0](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0).
