# Tổng kết Bài 09 — Node labels, selector và affinity

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/09-node-affinity.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/10-taints-tolerations.md)

- **Ngày hoàn thành:** 2026-11-03, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phạm vi:** cluster `de-k3d`, context `k3d-de-k3d`, namespace `de-lab`; chỉ labels test trên hai agent và bốn Pod độc lập, không dữ liệu thật.
- **Phiên bản đã dùng:** API server `v1.33.6+k3s1`, client `/usr/local/bin/kubectl` `v1.33.9`, image `busybox:1.37.0` hỗ trợ Linux ARM64. Client trên PATH v1.36.1 không được dùng vì ngoài phạm vi skew của server này.
- **Nghiệm thu:** học viên tự thay đổi cluster/workload; mentor đọc manifest và kiểm tra live chỉ đọc, gắn UID/status/Events với từng đối chứng. Snapshot không phải audit đầy đủ mọi lệnh học viên chạy.
- **Kết quả:** đạt checkpoint, placement bằng selector, Pending do selector, recovery bằng Pod mới, đối chứng required/preferred và cleanup về baseline. Bốn Pod đã được xóa; giữ scaffold và bằng chứng lịch sử trong tài liệu, không apply lại chỉ để ôn.

## 1. Mental model

```text
Node labels mô tả thuộc tính theo hợp đồng nền tảng
                     |
PodSpec: selector + required affinity + requests + các điều kiện cứng khác
                     |
            Tập node hợp lệ để xét đặt Pod
                     |
       Preferred affinity và các tiêu chí tính điểm khác
                     |
            Scheduler chọn node → spec.nodeName
                     |
           Kubelet/runtime chuẩn bị và chạy container
```

- Label trên **Pod** phục vụ việc nhận diện/lọc Pod, không thay cho label trên **Node** khi xét nodeSelector.
- `lab-pool=batch` hay `lab-tier=memory` không tự tạo node pool, lắp RAM hoặc xác nhận hardware thật.
- CPU usage thấp hoặc nhiều RAM ở node khác không cho phép bỏ qua selector. Một node cụ thể phải thỏa toàn bộ điều kiện cứng và đủ ngân sách requests.
- Có `spec.nodeName` mới chỉ chứng minh Pod đã được gán node; còn phải kiểm tra phase, conditions và runtime. Ready của container `sleep` không phải nghiệm thu một tác vụ ETL.

## 2. Field và lựa chọn cấu hình

Các đường dẫn PodSpec dưới đây ở `Pod.spec`; với Deployment thường ở `spec.template.spec`.

| Resource/field | Ý nghĩa và lựa chọn đã học |
|---|---|
| Node `metadata.labels` | Thuộc tính scheduler đối chiếu. Node cluster-scoped; `-n de-lab` không giới hạn tác động của lệnh sửa Node. |
| Pod `metadata.labels` | Lab dùng `lesson="09"`, `app=placement-lab`, `team=data`, `environment=lab` để nhận diện resource. |
| PodSpec `nodeSelector` | Điều kiện cứng, nhiều cặp key/value là AND. Hợp với phép so khớp bằng đơn giản. |
| `affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution` | Ràng buộc cứng, diễn đạt được tập giá trị và nhiều nhóm điều kiện nhưng dài hơn selector. |
| `requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms[]` | Các term là OR; node phải thỏa trọn ít nhất một term. Thứ tự term không tạo ưu tiên. |
| `nodeSelectorTerms[].matchExpressions[]` | Các expression trong cùng term là AND. `operator: In`, `values: [batch, etl]` cho phép một trong hai giá trị. |
| `affinity.nodeAffinity.preferredDuringSchedulingIgnoredDuringExecution[]` | Chỉ ưu tiên trong tập node hợp lệ, không vượt selector/required/requests hoặc các điều kiện cứng khác. |
| Preferred `weight`, `preference.matchExpressions` | Lab dùng weight `80`; là trọng số của rule khi tính điểm affinity, không phải xác suất 80%, số Pod hoặc bảo đảm chọn node đó. |
| `IgnoredDuringExecution` | Thay Node label sau scheduling không tự evict/migrate Pod theo rule affinity này; Pod mới phải được xét lại. Không miễn các cơ chế gián đoạn khác. |
| Pod `spec.nodeName` | Đọc để biết vị trí thực tế; không khai báo nó như cách né scheduler để chữa Pending. |

Nếu cùng khai báo nodeSelector và required affinity, chúng phải cùng đúng trên **một node**, không ghi đè nhau.

Ví dụ AND/OR đã review bằng lý thuyết:

```text
(pool=batch AND tier=memory) OR (pool=etl AND tier=standard)
```

Tách hai expressions của một term thành hai term riêng có thể đổi AND thành OR, mở rộng tập node được phép. Không ghép các mảnh điều kiện đúng rải rác giữa các term.

**Trade-off:** dùng selector khi chỉ cần các phép bằng; dùng required khi vị trí là bắt buộc và cần biểu thức linh hoạt hơn; dùng preferred khi chạy trên nhóm thay thế vẫn hợp lệ. Preferred không có timer chờ rồi mới fallback, nhưng điều đó không bảo đảm Pod Running tức thì.

## 3. Scaffold và cấu hình đã thực hành

| File còn lưu | Pod | Cấu hình lúc thực hành |
|---|---|---|
| [01-selector-batch.yaml](../thuc-hanh/09-node-affinity/01-selector-batch.yaml) | `placement-batch` | Selector `batch AND memory`, baseline thành công. |
| [02-selector-missing.yaml](../thuc-hanh/09-node-affinity/02-selector-missing.yaml) | `placement-missing` | Ban đầu `missing AND memory`; sau recovery file hiện là `batch AND memory`, vẫn giữ tên Pod/file. |
| [03-required-memory.yaml](../thuc-hanh/09-node-affinity/03-required-memory.yaml) | `placement-required` | Selector `lab-pool=etl` và required `lab-tier In [memory]`. |
| [04-preferred-memory.yaml](../thuc-hanh/09-node-affinity/04-preferred-memory.yaml) | `placement-preferred` | Selector `lab-pool=etl`, chỉ preferred `lab-tier In [memory]`, weight 80. |

Cả bốn cùng một container `worker`, `busybox:1.37.0`, `IfNotPresent`, `command: ["sleep", "3600"]`, `restartPolicy: Always`; requests `25m/32Mi`, limits `100m/64Mi`. Không controller owner, declared env/envFrom hoặc volume dữ liệu PVC/hostPath/emptyDir. Đây là naked Pods để cô lập quan sát scheduling, không phải mẫu triển khai dịch vụ production.

Phần cứng/môi trường giữ nguyên, chỉ đổi điều kiện trong Pod để so required/preferred; không cordon, taint hoặc dừng node cho đối chứng này.

## 4. Bằng chứng runtime trước cleanup

Tất cả mốc giờ trong phần này là ngày 2026-11-03, giờ Việt Nam.

### 4.1 Labels làm đầu vào

Trước đổi, 14:42–14:44: cả ba node thiếu `lab-pool` và `lab-tier`. Sau học viên gán nhãn, mentor kiểm 14:50–14:56; labels được giữ đến hết đối chứng affinity.

Lệnh chỉ đọc đã dùng, với helper khóa đúng client/context/namespace:

```bash
klab() {
  /usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
    --context=k3d-de-k3d -n de-lab --request-timeout=10s "$@"
}

klab get nodes \
  -o 'custom-columns=NAME:.metadata.name,POOL:.metadata.labels.lab-pool,TIER:.metadata.labels.lab-tier'
```

Snapshot trước cleanup, kiểm lại 22:01–22:03; **không phải labels hiện tại**:

```text
NAME                  POOL     TIER
k3d-de-k3d-agent-0     batch    memory
k3d-de-k3d-agent-1     etl      standard
k3d-de-k3d-server-0    <none>   <none>
```

Nhìn đồng thời POOL và TIER: không node nào có `etl AND memory`; agent-0 có memory nhưng sai pool, server thiếu pool, agent-1 đúng pool nhưng tier standard.

### 4.2 Selector, Pending và recovery

| Đối chứng | UID | Bằng chứng mentor đã kiểm |
|---|---|---|
| Baseline `placement-batch` | `0b61fe48-009b-4aa7-94c9-7059014c3191` | Tạo 15:05:23, kiểm 15:07–15:14: Running, Scheduled/Ready=True trên agent-0; selector batch/memory, Events đúng UID có Scheduled/Pulling/Pulled/Created/Started. |
| `placement-missing` trước sửa | `02539279-ba11-446f-90bb-120a66337e38` | Tạo 15:24:06, kiểm từ 15:35: Pending, nodeName trống, PodScheduled=False/Unschedulable, chưa containerStatuses; selector missing/memory, FailedScheduling đúng UID do selector mismatch. |
| `placement-missing` sau recovery | `bd638f5c-f8be-4c5c-8e15-c237423f3365` | Tạo 16:48:27, kiểm 16:48–16:56: selector batch/memory, Running/Ready trên agent-0, restart 0, container chạy từ 16:48:28; Events đúng UID có Scheduled/Pulled/Created/Started. |

Sửa duy nhất `lab-pool: missing` về `batch`, giữ tier/image/command/resources và baseline. NodeSelector của Pod thông thường trong case này không sửa tại chỗ bằng update Pod thông thường, kể cả khi Pending; học viên tạo lại đúng Pod thử nghiệm. Cùng tên nhưng UID khác chứng minh đó là **Pod mới**.

Với Deployment, cách quản lý thường là sửa Pod template và để controller rollout Pod mới; không cần chuyển lab này thành Deployment để nghiệm thu.

[recover-selector.py](../thuc-hanh/09-node-affinity/recover-selector.py) là helper học viên đã khởi chạy, khóa UID Pending cũ và hash fixture để giảm thao tác chép lệnh. Mentor không chạy helper thay học viên. Helper có guard kiểm trước lệnh, không phải transaction atomic; **không chạy lại sau bài**, không gỡ guard hoặc coi nó là công cụ recovery dùng chung. File 02 hiện đã ở trạng thái sau sửa và Pod target cũ không còn.

### 4.3 Required khác preferred ở đâu?

Lệnh quan sát đã dùng:

```bash
klab get pods placement-required placement-preferred \
  -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase,NODE:.spec.nodeName,SCHEDULED:.status.conditions[?(@.type=="PodScheduled")].status,READY:.status.conditions[?(@.type=="Ready")].status'
```

Snapshot thực tế 22:01–22:03, **chỉ còn trong lịch sử vì Pod đã cleanup**:

```text
NAME                  PHASE     NODE                 SCHEDULED   READY
placement-required    Pending   <none>               False       <none>
placement-preferred   Running   k3d-de-k3d-agent-1   True        True
```

- Required UID `16a8ed6a-3899-40d8-a738-0c62115ecf05`, tạo 17:23:12; PodScheduled=False/Unschedulable, chưa có node/containerStatuses.
- Preferred UID `46042208-a82e-42b5-b4be-ef5a49ca8180`, cũng tạo 17:23:12; Running/PodScheduled=True/Ready=True trên agent-1 etl/standard, dù tier không match ưu tiên memory.
- Hai Pod có hard selector etl, live affinity và image/resources đúng file 03/04. Chỉ agent-1 qua selector; required loại nó vì tier standard, preferred vẫn cho phép nó.
- Baseline/recovery Pod UID và cả ba Node UID/labels không đổi qua đối chứng. Ba node Ready, không taint/cordon trong lượt đọc.

Lệnh xem Event của **đúng UID**, không chỉ tên có thể được dùng lại:

```bash
klab get events \
  --field-selector=involvedObject.uid=16a8ed6a-3899-40d8-a738-0c62115ecf05,reason=FailedScheduling \
  -o 'custom-columns=REASON:.reason,MESSAGE:.message'
```

Đoạn message thực tế đã kiểm và học viên đã quan sát từ truy vấn theo tên:

```text
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.
```

`nodeName` trống + PodScheduled=False + message selector/affinity đặt lỗi ở tầng scheduling, chưa phải app/probe/image startup. Đuổi Pod ưu tiên thấp không làm đổi Node labels nên không chữa mismatch này; message không chứng minh Pod nào đã bị evict. Không tăng CPU/RAM hoặc thêm imagePullSecret để chữa lỗi label trong bằng chứng này.

Preferred có runtime imageID `docker.io/library/busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec`; metadata registry đã đối chiếu linux/arm64/v8. Snapshot 22:03 còn Events Created/Started/Pulled, không còn Scheduled/Pulling ban đầu; không dựng lại cold-pull hoặc thời điểm scheduling từ dữ liệu đã hết retention. Version tag trong scaffold không phải digest pin bất biến.

## 5. Cleanup đã được kiểm chứng

Học viên xóa đúng bốn Pod rồi bỏ đúng `lab-pool`/`lab-tier` trên hai agent; không xóa namespace, Node, file scaffold hoặc tài nguyên bài khác. Vì baseline thiếu key, hoàn tác đúng là bỏ key; nếu baseline từng có giá trị khác thì phải trả lại giá trị đó.

Mentor kiểm tra chỉ đọc 22:33–22:34, xác minh cuối lúc **22:34:57**:

```bash
klab get pods placement-batch placement-missing placement-required placement-preferred \
  --ignore-not-found -o name

klab get pods -l lesson=09 -o name
```

Cả hai lệnh đều không có dòng output, không phải lỗi truy cập bị bỏ qua. Đây là bằng chứng hiện tại bốn tên Pod không còn và selector lesson=09 rỗng; Event còn retention không có nghĩa Pod vẫn tồn tại.

```bash
klab get nodes \
  -o 'custom-columns=NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,POOL:.metadata.labels.lab-pool,TIER:.metadata.labels.lab-tier'
```

Snapshot sau cleanup, rút gọn từ các field mentor đã kiểm:

```text
NAME                  READY   POOL     TIER
k3d-de-k3d-agent-0     True    <none>   <none>
k3d-de-k3d-agent-1     True    <none>   <none>
k3d-de-k3d-server-0    True    <none>   <none>
```

Mentor đối chiếu thêm JSON để xác nhận hai key **không tồn tại**, không chỉ có giá trị rỗng. Cả ba node không taint/cordon, UID giữ nguyên:

| Node | UID |
|---|---|
| agent-0 | `4ea95101-66d2-4a51-bf3e-c3d47602425d` |
| agent-1 | `09b5909c-9cf8-4432-95c6-bda7167922f3` |
| server-0 | `15152848-8931-45f4-a706-a61e4f1e87db` |

Không chạy lại mutation để quan sát. Kiểm tra này xác nhận trạng thái cuối trong phạm vi trên, không audit tuyệt đối mọi thay đổi hoặc mọi tài nguyên cluster.

## 6. Review concept và nhầm lẫn đã sửa

| Checkpoint | Kết quả đã ghi nhận |
|---|---|
| Khối 1: Node labels, selector AND, fit cùng một node | `1C, 2A, 3B`, 3/3; câu 2 học viên gõ `Á`, hiểu là A. |
| Khối 2: required, In nhiều values, IgnoredDuringExecution | `1B, 2C, 3A`, 3/3. |
| Khối 3: preferred và weight | Lượt đầu `1C, 2C, 3A`, đúng 2/3; câu 1 sai về timeout fallback. Câu chốt riêng chọn A đúng: node khác hợp lệ vẫn được xét mà không chờ timeout của preferred. Chốt sau sửa sai, không đổi lịch sử thành đạt ngay lần đầu. |
| Khối 4: AND/OR và thứ tự terms | `1B, 2A, 3B`, 3/3. |
| Khối 5: Node cluster-scoped và hoàn tác đúng baseline | `1B, 2C`, 2/2. |
| Review tầng lỗi và update Pod selector | `1C, 2A`, 2/2: lỗi trước startup thuộc scheduler; Pending không miễn quy tắc update. |

Không quiz lại các checkpoint đã đạt để đủ số câu. Nhiều terms/expressions, thay label khi Pod đang chạy và Deployment rollout được review bằng lý thuyết, **không ghi thành các thí nghiệm runtime riêng đã thực hiện**.

Các điểm quan sát cần giữ:

- Restart container khác tạo lại Pod. Snapshot 22:03 baseline/recovery/preferred lần lượt restart 6/5/4, lastState Completed/exit 0 với sleep 3600/Always; UID vẫn giữ nguyên. Không suy agent hỏng từ restart count này.
- Preflight từng bị kẹt vì hai agent mất K3s/heartbeat sau lỗi Node IP/interface của network policy controller. Học viên restart agents, mentor đã kiểm process/Lease/Node/system Pods phục hồi trước lab. Chưa chứng minh nguyên nhân timing/IP tận gốc hoặc bảo đảm không tái phát; chi tiết giữ trong nhật ký tiến độ. Không dùng việc khôi phục agents làm bằng chứng recovery Bài 08 đã bỏ qua.

## 7. Liên hệ Data Engineering và hợp đồng với DevOps

| DE cần quyết định/cấu hình | Platform cần cung cấp/xác nhận |
|---|---|
| ETL có bắt buộc pool/tier hay chỉ mong muốn? Chọn required hoặc preferred đúng yêu cầu. | Key/value labels ổn định, ý nghĩa thực và pool nào được phép chạy thay thế. |
| Đọc selector/affinity cùng requests; trong Helm phải xem resource render đúng chart/version, không đoán tên values. | Capacity/allocatable, policy placement và quyền đọc cấu hình/Events. Chưa thực hành Helm trong bài này. |
| Gửi context/namespace, tên và UID Pod, selector/affinity, Node labels và message FailedScheduling đã lọc. | Nếu không có node etl/memory, xác nhận/cấp pool phù hợp hoặc cùng điều chỉnh yêu cầu; không dán nhãn memory lên máy không đúng khả năng chỉ để hết Pending. |
| Dùng labels đã thỏa thuận, không tự sửa Node chung để sửa workload. | Người được ủy quyền quản lý Node labels và quy trình thay đổi. Quyền admin sandbox không phải quyền DE mặc định. |

**Lab làm giúp ↔ ngoài lab:** k3d/K3s đã tạo các Node/API/scheduler/runtime để quan sát. Selector và affinity là cơ chế Kubernetes, không phải tiện ích placement riêng của k3d. On-prem cần platform quản lý inventory và labels thật; managed cloud có thể cấp labels theo node pool nhưng vẫn phải xác nhận key/value, capacity và chính sách thực tế.

Image phải có trong cache/runtime của chính node hoặc kéo được từ registry đúng kiến trúc, mạng, quyền và trust. Image trên Mac không tự có trên mọi node; bài không dùng image import để che đường phân phối image. Khi Pod đã có node mà chưa Ready, kiểm runtime/pull Events rồi startup, không tiếp tục chữa affinity theo quán tính.

## 8. Giới hạn minh chứng và nguồn

- Node labels giả không chứng minh RAM, GPU, storage/network locality hoặc bảo mật/cách ly tài nguyên.
- Ba node-container vẫn chung host/runtime/disk; không cộng allocatable thành RAM vật lý độc lập hoặc coi là ba miền lỗi thật.
- Preferred chạy trên agent-1 chứng minh node không match ưu tiên vẫn được phép; không chứng minh weight là xác suất, luôn thắng khi có nhiều ứng viên hoặc thời gian scheduling được bảo đảm.
- Snapshot/Events không là lịch sử bền vững; không suy chính xác thứ tự lệnh, timer fallback hoặc mọi lần scheduler thử. Không có bằng chứng hiệu năng ETL, HA, backup hoặc exactly-once.
- Cleanup đã đạt trong phạm vi Bài 09; Bài 08 vẫn đóng theo xác nhận học viên, không tạo việc recovery phải làm lại.

Nguồn đã đối chiếu theo Kubernetes v1.33 và metadata image:

- [Assigning Pods to Nodes: selector, affinity, AND/OR, weight](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/).
- [Pod update and replacement](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/#pod-update-and-replacement).
- [Pod priority and preemption](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/).
- [Images](https://v1-33.docs.kubernetes.io/docs/concepts/containers/images/) và [BusyBox tag metadata](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0).
- [Version skew policy](https://kubernetes.io/releases/version-skew-policy/).
