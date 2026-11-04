# Tổng kết Bài 10 — Taints và tolerations

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/10-taints-tolerations.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/11-topology-spread.md)

- **Ngày hoàn thành:** 2026-11-04, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`; một Pod trần `taint-gate-lab` và một taint test trên `k3d-de-k3d-agent-0`. Không dữ liệu ứng dụng thật.
- **Phiên bản:** API server `v1.33.6+k3s1`, client `/usr/local/bin/kubectl` `v1.33.9`, image `busybox:1.37.0` đã đối chiếu hỗ trợ `linux/arm64/v8`.
- **Kết quả:** đạt lý thuyết/checkpoint, đối chứng Pending, recovery cùng Pod UID bằng toleration hẹp và cleanup về baseline lúc **10:10:07**.
- **Ranh giới thực thi:** học viên tự thêm/gỡ taint, tạo/patch/xóa Pod; mentor chỉ đọc file/live, kiểm fixture local và lưu tài liệu. Snapshot không phải audit đầy đủ mọi lệnh.

## 1. Mental model

```text
Selector/required affinity + requests + các điều kiện cứng khác
                              |
                Node nào có thể là ứng viên?
                              |
             Node taints ↔ Pod tolerations
                              |
         Còn taint NoSchedule/NoExecute chưa match?
                 có → node bị loại
                              |
            Scheduler chọn node và gán Pod
                              |
          Kubelet/runtime chuẩn bị, chạy container
```

- **Taint nằm trên Node**, đặt rào cản đối với Pod không tolerate nó.
- **Toleration nằm trên Pod**, cho phép vượt rào cản tương ứng, không kéo hoặc buộc Pod tới node đó.
- Muốn chạy trong pool cụ thể thường phải kết hợp placement và toleration theo hợp đồng nền tảng. Toleration không bỏ qua thiếu tài nguyên, affinity hoặc volume topology.
- Node label và taint là hai cấu hình khác nhau. Cùng chữ `etl` không làm chúng tự tạo hoặc thay thế nhau.

## 2. Field, effect và matching

Với Pod trần, PodSpec ở `Pod.spec`; với Deployment thường ở `spec.template.spec`.

| Resource/field | Ý nghĩa và lựa chọn đã học |
|---|---|
| Node `spec.taints[]` | Mỗi entry có key/value/effect. Lab chỉ sửa taint test trên một agent, không sửa system keys. Node là cluster-scoped; `-n de-lab` không giới hạn tác động của taint. |
| PodSpec `nodeSelector` | Điều kiện chọn node qua labels; trong lab dùng nhãn hostname đã kiểm tra, vẫn để scheduler xét taint và các điều kiện khác. |
| PodSpec `tolerations[].key` | Key của taint được chấp nhận, không phải yêu cầu Node phải có label cùng tên. |
| `operator: Equal`, `value` | Match đúng key/value/effect; chọn cho rule lab vì biết chính xác taint cần tolerate. |
| `operator: Exists` | Bỏ ràng buộc bằng value, không khai value; vẫn phải match key/effect khi chúng được chỉ định. Không mặc định tốt hơn Equal. |
| `effect` | Toleration `NoSchedule` không tự match `NoExecute` cùng key/value. Bỏ effect mở phạm vi sang các effect của key đang xét. |
| `tolerationSeconds` | Cửa sổ tolerate `NoExecute`, không phải deadline ETL hoặc thời gian chờ scheduling. Không dùng làm timer cho `NoSchedule`. |
| PodSpec `nodeName` | Đọc để biết vị trí thực tế; không khai trực tiếp để chữa Pending vì có thể bỏ qua scheduler và rào cản `NoSchedule`. |

### Ba effect khi Pod chưa tolerate taint tương ứng

| Effect | Pod mới | Pod đã chạy trên node |
|---|---|---|
| `NoSchedule` | Scheduler không đặt lên node đó. | Không tự evict chỉ vì thêm taint này. |
| `PreferNoSchedule` | Tránh nếu có thể, không cấm cứng. | Không tự evict chỉ vì effect này. |
| `NoExecute` | Không được schedule khi chưa tolerate. | Có cơ chế eviction theo matching và cửa sổ tolerate. |

**Giới hạn thực hành:** lab chỉ thêm một taint `NoSchedule`. `PreferNoSchedule`, `NoExecute`, wildcard và nhiều taints được học bằng tình huống, không thực nghiệm eviction hoặc thay taints hệ thống.

### Matching rộng và nhiều taints

- Giữ key/effect với `Exists`: chấp nhận mọi value của đúng key/effect đó.
- Bỏ key nhưng giữ `Exists` và `NoSchedule`: match mọi key/value của `NoSchedule`, không tự gồm `NoExecute`.
- Bỏ cả key/effect với `Exists`: rất rộng, có thể tolerate cả `NoExecute`; không dùng để chữa Pending theo quán tính.
- Xét từng taint riêng. Match một taint không miễn những taint khác còn chặn Pod.

Ví dụ lý thuyết: Node có `lab-dedicated=etl:NoSchedule` và `lab-storage=fast:NoSchedule`; Pod chỉ tolerate key đầu vẫn bị key sau chặn. Hai taints này không được triển khai cùng nhau trong lab.

### Cửa sổ NoExecute đã review bằng lý thuyết

- Không có toleration khớp: không có cửa sổ tolerate để trì hoãn eviction vì taint đó.
- Match mà không đặt `tolerationSeconds`: không giới hạn thời gian tolerate riêng taint đó.
- Trong ví dụ match với `tolerationSeconds: 120`, cửa sổ hết khi taint vẫn còn sẽ dẫn tới eviction; không phải giới hạn runtime của task.
- Gỡ taint ở giây 60 trước khi hết cửa sổ: không còn eviction vì riêng taint đã gỡ tại giây 120.
- Xử lý eviction bất đồng bộ; không bảo đảm process dừng chính xác ở giây 120, đặc biệt khi node mất liên lạc. Không thay retry/idempotency của ETL.

## 3. Scaffold và thiết kế đối chứng

File được giữ lại: [01-no-toleration.yaml](../thuc-hanh/10-taints-tolerations/01-no-toleration.yaml).

| Thành phần | Cấu hình thực hành |
|---|---|
| Node test | Chỉ `k3d-de-k3d-agent-0`; taint `lab-dedicated=etl:NoSchedule`. |
| Pod | `taint-gate-lab` trong `de-lab`; labels `lesson="10"`, `app=taint-gate-lab`, `team=data`, `environment=lab`. |
| Placement | `nodeSelector: kubernetes.io/hostname=k3d-de-k3d-agent-0`; đã kiểm giá trị label và tính riêng biệt trên các node. |
| Container | `worker`, `busybox:1.37.0`, `IfNotPresent`, `sleep 3600`, `restartPolicy: Always`. |
| Resources | Requests `25m/32Mi`, limits `100m/64Mi`; giữ nguyên qua Pending và recovery. |
| Cấu hình ban đầu | Không khai toleration cho taint test, không nodeName hoặc controller owner. |
| Dữ liệu | Không khai env/envFrom hoặc volume dữ liệu ứng dụng; live có projected service-account volume mặc định, không đọc nội dung credential. |

Nếu bỏ selector, Pod có thể chọn node khác và Running mà chưa hề vượt rào cản của agent-0. Nếu đặt nodeName trực tiếp, đối chứng mất ý nghĩa kiểm tra scheduler. Vì vậy giữ selector và chỉ thêm toleration cần thiết.

Khối cấu hình tương đương với entry đã thêm vào live Pod, **không phải nội dung mới của file baseline**:

```yaml
tolerations:
  - key: lab-dedicated
    operator: Equal
    value: etl
    effect: NoSchedule
```

File `01-no-toleration.yaml` chủ ý giữ trạng thái trước recovery. Patch live không sửa file, không phải đã cập nhật template của controller. Không apply lại fixture hoặc chạy lại patch UID cũ chỉ để ôn bài.

## 4. Bằng chứng runtime trước cleanup

Các mốc dưới đây là ngày 2026-11-04, giờ Việt Nam.

### 4.1 Baseline và identity

- Preflight 09:01–09:03: `de-lab` Active, ba node Ready, không taint/cordon/pressure; agent-0 có đúng hostname label.
- Mentor đã ghi baseline taints trước khi học viên thêm taint. Lần đọc 09:33 không thấy `baseline-agent-0.txt` ở đường dẫn được giao; không suy học viên chưa từng lưu ở nơi khác, không tạo file sau taint rồi gọi là baseline trước taint.
- Pod test tạo lúc **09:30:58**, UID **`b98dea5b-1894-4673-9f17-bde609769738`**; UID này giữ nguyên qua Pending và recovery.

### 4.2 Pending đúng nguyên nhân

Helper khóa binary/kubeconfig/context/namespace; các lệnh tái quan sát dưới đây chỉ đọc, không in kubeconfig credential:

```bash
klab() {
  /usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
    --context=k3d-de-k3d --namespace=de-lab \
    --request-timeout=10s "$@"
}

klab get pod taint-gate-lab \
  -o custom-columns='NAME:.metadata.name,PHASE:.status.phase,NODE:.spec.nodeName,SCHEDULED:.status.conditions[?(@.type=="PodScheduled")].status,READY:.status.conditions[?(@.type=="Ready")].status'
```

Snapshot trước recovery, mentor kiểm 09:33 và lại 09:50; **Pod đã cleanup, không phải trạng thái hiện tại**:

```text
NAME             PHASE     NODE     SCHEDULED   READY
taint-gate-lab   Pending   <none>   False       <none>
```

`nodeName` trống, `PodScheduled=False/Unschedulable`, chưa containerStatuses, không owner/deletion/gates: lỗi ở tầng scheduling, chưa phải lỗi ứng dụng đã chạy.

Lệnh đọc Event đúng UID; chỉ còn trả kết quả khi Event vẫn được lưu:

```bash
klab get events \
  --field-selector=involvedObject.uid=b98dea5b-1894-4673-9f17-bde609769738,reason=FailedScheduling \
  -o custom-columns='REASON:.reason,MESSAGE:.message'
```

Message thực tế học viên đã quan sát và mentor đã kiểm, ngắt dòng để đọc:

```text
0/3 nodes are available:
1 node(s) had untolerated taint {lab-dedicated: etl},
2 node(s) didn't match Pod's node affinity/selector.
preemption: 0/3 nodes are available:
3 Preemption is not helpful for scheduling.
```

- Một node bị chặn taint là agent-0 theo inventory; hai node khác bị selector loại đúng thiết kế.
- Preemption cân nhắc loại Pod ưu tiên thấp hơn để tạo node phù hợp, nhưng không thay taint/labels/selector. Đừng xóa workload khác hoặc tăng priority để chữa mismatch này.
- Số 3 ở đoạn preemption đếm node, không nói đã evict ba Pod hoặc restart ba node.
- Event UID `f7a24763-c825-4432-8a5f-39a2cdf6ed44` có mốc 09:30:58; Event `4813999b-7e9c-42db-89f3-71268bf3ea94` có mốc 09:36:25. Không suy lịch sử retries đầy đủ từ số Event còn lưu.

### 4.3 Recovery cùng Pod, taint vẫn còn

Học viên tự dùng JSON Patch: kiểm `/metadata/uid`, rồi append `/spec/tolerations/-` entry hẹp. Cách này giữ hai tolerations hệ thống `not-ready`/`unreachable` dạng `Exists/NoExecute/300` giây. `spec.tolerations` cho phép thêm entry vào Pod có sẵn; không suy mọi field Pod đều mutable. Xóa/tạo lại cũng là lựa chọn nhưng đổi UID, không cần cho đối chứng này.

Mentor chỉ kiểm cú pháp/logic trên fixture giả với `--local=true`, không patch live. Patch thật do học viên chạy, sau đó tự quan sát `patched`, `condition met` và bảng trạng thái.

Kết quả mentor xác minh 09:58:55–09:58:56, từ cùng lệnh custom columns ở trên:

```text
NAME             PHASE     NODE                 SCHEDULED   READY
taint-gate-lab   Running   k3d-de-k3d-agent-0   True        True
```

- Cùng UID và creationTimestamp cũ, selector/image/command/resources không đổi, thêm đúng một toleration `lab-dedicated/Equal/etl/NoSchedule`; không wildcard hoặc nodeName khai báo để né scheduler.
- PodScheduled=True lúc **09:56:34**, container chạy lúc **09:56:35**, Ready=True lúc **09:56:36**, restart count **0**.
- Event Scheduled UID `c0d8a205-9e53-44e6-8cf1-31520a0130ae` tham chiếu đúng Pod UID, xác nhận assigned agent-0; có Pulled/Created/Started.
- Pulled ghi `Container image "busybox:1.37.0" already present on machine`: dùng cache của node, không chứng minh một pull mới từ registry trong lượt này.
- Runtime imageID: `docker.io/library/busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec`. Không đồng nhất imageID này với digest manifest ARM64 của registry hoặc coi tag version là digest pin bất biến.

Lệnh kiểm taint đã dùng:

```bash
klab get node k3d-de-k3d-agent-0 \
  -o jsonpath='{range .spec.taints[*]}{.key}{"="}{.value}{":"}{.effect}{"\n"}{end}'
```

Output **trước cleanup**, trong khi Pod đã Running:

```text
lab-dedicated=etl:NoSchedule
```

Đó là đối chứng chính: không cần bỏ rào cản Node; chỉ thêm toleration đúng cho Pod. Ready của container `sleep` chỉ chứng minh container sẵn sàng trong lab, không nghiệm thu ETL thật.

Hai Event FailedScheduling cũ vẫn còn lúc review recovery; Event lịch sử không có nghĩa Pod vẫn đang Pending. Pod ServiceLB trên agent-0 vẫn cùng UID/Running/Ready ở snapshot, không chứng minh mọi namespace hoàn toàn không bị ảnh hưởng bởi taint.

## 5. Cleanup đã kiểm chứng

Học viên báo cleanup xong. Mentor kiểm tra chỉ đọc **10:10:06–10:10:07**, xác nhận context và `de-lab` Active trước khi đọc:

```bash
klab get pod taint-gate-lab --ignore-not-found -o name
klab get pods -l lesson=10 -o name
```

Cả hai lệnh không có dòng output; API truy cập thành công, không phải lỗi bị bỏ qua. Pod theo tên và nhóm `lesson=10` không còn.

```bash
klab get nodes \
  -o custom-columns='NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,TAINTS:.spec.taints'
```

Output sau cleanup:

```text
NAME                  READY   TAINTS
k3d-de-k3d-agent-0    True    <none>
k3d-de-k3d-agent-1    True    <none>
k3d-de-k3d-server-0   True    <none>
```

Mentor đối chiếu thêm JSON: taints rỗng, không unschedulable, Memory/Disk/PIDPressure=False; ba Node UID giữ nguyên:

| Node | UID |
|---|---|
| agent-0 | `4ea95101-66d2-4a51-bf3e-c3d47602425d` |
| agent-1 | `09b5909c-9cf8-4432-95c6-bda7167922f3` |
| server-0 | `15152848-8931-45f4-a706-a61e4f1e87db` |

Đã trở về baseline taints của mentor trước lab. Cách gỡ được giảng là `lab-dedicated:NoSchedule-` trên đúng agent-0: dấu `-` cuối gỡ theo key/effect; không dùng dạng bỏ effect để gỡ mọi taint cùng key. Chỉ xóa Pod test, không force/xóa namespace/đụng taints hệ thống hoặc server. Snapshot cuối không là audit thứ tự mọi thao tác.

Giữ scaffold; không apply lại hoặc chạy patch dùng UID cũ sau cleanup. Mentor không chạy mutation thay học viên.

## 6. Review và lỗi đã xử lý

| Checkpoint | Kết quả |
|---|---|
| Khối 1: thiếu toleration dù selector đúng, toleration không hút Pod, NoSchedule không tự đuổi Pod cũ | `1B, 2C, 3A`, 3/3. |
| Khối 2: PreferNoSchedule, cửa sổ NoExecute, gỡ taint trước hạn | `1C, 2A, 3B`, 3/3. |
| Khối 3: Exists, nhiều taints, bỏ key nhưng giữ effect | `1B, 2C, 3A`, 3/3. |
| Thiết kế đối chứng: selector hostname thay nodeName hoặc chọn node bất kỳ | Chọn B đúng, 1/1. |
| Đọc Event preemption: ba node không trở nên hợp lệ chỉ nhờ loại Pod ưu tiên thấp hơn | Chọn B đúng, 1/1. |

Không hỏi lại để đủ số câu. `NoExecute`, nhiều taints và wildcard chỉ đạt bằng lý thuyết/checkpoint, không ghi thành đã thực nghiệm.

Học viên từng gõ thêm backslash trước `[[`, làm Bash tìm command tên `[[` và báo `command not found`. Với `&&`, nhánh patch chưa chạy ở lượt shell lỗi; học viên bỏ dấu thừa rồi thực hiện thành công. Đây là lỗi shell, không phải Kubernetes. Không cần chạy lại patch đã thành công.

## 7. Liên hệ DE và hợp đồng nền tảng

| DE cần cấu hình/đưa bằng chứng | Platform/DevOps cần cung cấp hoặc xác nhận |
|---|---|
| Selector/affinity, toleration hẹp và requests theo nhu cầu ETL. | Labels/taints thật của pool, ý nghĩa và capacity; workload có được dùng pool đó không. |
| Gửi context/namespace, Pod UID, thời gian, selector/tolerations và FailedScheduling đã lọc. | Quyền đọc/patch phù hợp, taints hệ thống và quy trình thay đổi Node. |
| Giữ rào cản Node chung, chỉ dùng toleration được phép; không coi wildcard là bản sửa mặc định. | Chính sách allowed tolerations/admission/quota và chủ sở hữu pool. Taint không tự là cơ chế phân quyền/cách ly bảo mật. |
| Khi triển khai bền, cập nhật manifest/template/Helm values nguồn theo đúng chart/version và quy trình. | Cách release và kiểm resource render; chưa thực hành Helm trong bài này. Patch một Pod không tự cập nhật controller/template. |

**Lab làm giúp ↔ ngoài lab:** k3d/K3s cung cấp Node/API/scheduler/runtime để quan sát; taints/tolerations là cơ chế Kubernetes, không cần add-on placement riêng của k3d. On-prem cần platform quản lý inventory/labels/taints và quy trình đổi pool. Managed cloud có thể hỗ trợ node groups với cấu hình đó, nhưng vẫn phải xác nhận key/value, quyền và capacity thực tế.

Quyền admin của lab không là quyền DE mặc định. Taint Node ảnh hưởng scheduling mới ở mọi namespace nếu Pod không tolerate; không suy `-n de-lab` làm thao tác Node chỉ tác động namespace lab.

## 8. Giới hạn và nguồn

- Chỉ kiểm chứng một Pod `sleep` trên một agent, không phải ETL đúng, benchmark, HA hoặc dedicated pool/cách ly tuyệt đối.
- Ba node-container vẫn chung host/runtime/disk; không coi là ba máy/vùng lỗi độc lập.
- NoSchedule không tự evict Pod cũ nhưng vẫn có thể chặn Pod mới ở namespace khác. Snapshot ServiceLB còn Ready không chứng minh không có ảnh hưởng ngoài phạm vi quan sát.
- Lượt recovery dùng image cache trên agent-0; không chứng minh registry luôn truy cập được hoặc image có sẵn ở mọi node. Image trên Mac không tự xuất hiện trong runtime của node.
- Không thực nghiệm NoExecute/eviction hoặc tạo PriorityClass, không gỡ taints hệ thống. Không đọc/in token, Secret hoặc credential trong projected volume/kubeconfig.
- Runtime đạt không thay checkpoint hiểu; ngược lại, quiz đạt không thay runtime. Bài 08 vẫn đóng theo xác nhận, không tạo việc recovery phải làm lại.

Nguồn đã đối chiếu:

- [Taints and Tolerations — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/).
- [Assigning Pods to Nodes](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/).
- [Pod update and replacement](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/#pod-update-and-replacement).
- [Priority and preemption](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/).
- [BusyBox tag metadata](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0) và [version skew policy](https://kubernetes.io/releases/version-skew-policy/).
