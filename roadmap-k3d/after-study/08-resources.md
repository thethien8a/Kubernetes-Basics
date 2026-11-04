# Tổng kết nội dung học Bài 08 — Requests, limits và sức chứa

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/08-resources.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/09-node-affinity.md)

- **Thông báo:** **Bài 08 đã hoàn thành nội dung học theo xác nhận của học viên.**
- **Ngày xác nhận đã học xong:** 2026-11-03, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`; học viên tự thao tác workload, mentor chỉ kiểm tra chỉ đọc.
- **Kết quả đã nghiệm thu:** các khối lý thuyết đã dạy và lab Pod Pending/FailedScheduling.
- **Phần bỏ qua theo yêu cầu học viên:** kiểm chứng giảm request rồi tạo lại Pod để được gán node/Running/Ready. Đây không còn là việc chờ học viên thực hiện; không giao lại thao tác hoặc quiz đã đạt, không ghi phần này thành runtime thành công.
- **Phân biệt phạm vi:** xác nhận đã học xong là của học viên; không kết luận nghiệm thu recovery đạt hoặc đã đủ toàn bộ bằng chứng runtime. Không mở lại Bài 08 vì phần đã bỏ qua; bài tiếp tục là Bài 09.

## 1. Ba lớp cần phân biệt

| Lớp | Dữ liệu/cấu hình | Cách hiểu |
|---|---|---|
| Scheduling | Container `resources.requests`, Node `status.allocatable` | Scheduler xét requests hiệu lực của Pod cùng các ràng buộc trên từng node; không ghép ngân sách nhiều node cho một Pod. |
| Runtime | Container `resources.limits` | Kubelet/runtime cấu hình giới hạn, kernel Linux thực thi qua cgroups. CPU limit có thể gây throttling; memory limit có thể dẫn tới OOM kill khi không đáp ứng được nhu cầu bộ nhớ trong giới hạn. |
| Quan sát | Metrics API, termination state, Events | Usage không phải request/limit; trạng thái Running không đủ kết luận có hoặc không có throttling. |

- `1000m` CPU bằng 1 CPU; `1Gi = 1024Mi`. `Mi` khác `M`, không dùng `m` để viết MB trong memory Kubernetes.
- Request không phải lượng tài nguyên đang dùng hoặc trần sử dụng. Container có thể dùng hơn request nếu tài nguyên và các ràng buộc cho phép.
- CPU còn nhàn không tự bỏ qua CPU limit. Throttling không trực tiếp kill/restart container chỉ vì chạm quota; vẫn có thể có lỗi gián tiếp như probe thất bại.
- Node còn RAM không tự nới memory limit của container. Nếu container kết thúc do OOM, việc restart còn tùy policy; không đồng nhất mọi restart với OOM hoặc mọi OOM với memory leak.
- Với lần tạo đầu tiên, request lớn hơn limit cùng resource bị API từ chối; khác với Pod đã được nhận nhưng chưa tìm được node.

## 2. Requests của cả Pod

Phạm vi các phép tính đã học là requests theo container, không có Pod-level resources hoặc resize đang diễn ra; cộng overhead nếu nền tảng thực sự khai báo nó.

### Regular init

- Cộng requests của các container trong `containers[]`, kể cả container phụ.
- Regular init chạy tuần tự: lấy request init lớn nhất cho **từng resource**, so với tổng app, lấy mức lớn hơn rồi cộng overhead.
- Init hoàn tất không tự làm request được hạch toán của Pod giảm xuống tổng app.
- `spec.overhead` do admission theo RuntimeClass có cấu hình tương ứng điền vào, không phải field tùy ý để học viên chữa thiếu bộ nhớ.

Ví dụ đã review: app `700m/512Mi`, init A `1000m/128Mi`, init B `300m/768Mi`, overhead `50m/64Mi` → request hiệu lực `1050m/832Mi`. Không chọn nguyên cặp CPU/RAM của một init.

### Native sidecar

Native sidecar có `restartPolicy: Always` ở chính phần tử `initContainers[]`. Khi được coi là started, init tiếp theo có thể chạy trong khi sidecar vẫn hoạt động; sidecar tiếp tục chạy cùng app.

Ví dụ lý thuyết đã đạt checkpoint, không có overhead:

| Giai đoạn | Requests cộng trong giai đoạn |
|---|---|
| Log-agent `100m/128Mi` cùng regular init prepare-data `700m/256Mi` | `800m/384Mi` |
| Log-agent cùng app worker `500m/512Mi` | `600m/640Mi` |

Request hiệu lực là `800m/640Mi`, lấy max riêng CPU và memory. Bỏ `Always` khỏi log-agent chạy liên tục khiến nó thành regular init không hoàn tất, chặn init/app phía sau. Chưa triển khai sidecar hoặc đo peak thực tế.

## 3. Allocatable, heap và metrics

### Ngân sách node

Allocatable là ngân sách node công bố dành cho Pods, không phải RAM đang rảnh và không giảm theo từng Pod. Ngân sách còn theo requests được tính từ allocatable trừ requests hiệu lực đã hạch toán trên node ở mọi namespace.

Nhầm lẫn đã xử lý: allocatable `6Gi`, requests `512Mi + 4Gi = 4,5Gi` → còn `1,5Gi`; thêm Pod request `1Gi` → còn `0,5Gi`, allocatable vẫn `6Gi`. Học viên chọn sai câu đầu rồi chọn đúng câu sửa sai; mentor đưa phép tính, không ghi thành học viên tự viết phép tính.

Snapshot server ngày 2026-11-02: allocatable memory `12304236Ki` (khoảng `11,73Gi`), Allocated resources có CPU requests `200m`, memory requests `140Mi`, memory limits `170Mi`. Các số requests/limits này không phải usage. Capacity và allocatable bằng nhau ở lab không chứng minh OS/Kubernetes không dùng RAM.

Lệnh đọc lại các field Node, không phải ngân sách riêng của namespace:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get node k3d-de-k3d-server-0 \
  -o 'custom-columns=NAME:.metadata.name,CAPACITY_MEMORY:.status.capacity.memory,ALLOCATABLE_MEMORY:.status.allocatable.memory'

/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  describe node k3d-de-k3d-server-0 \
  | sed -n '/^Allocated resources:/,/^Events:/p'
```

Output lịch sử lúc 16:43 ngày 2026-11-02, chỉ trích phần liên quan của từng lệnh:

```text
NAME                  CAPACITY_MEMORY   ALLOCATABLE_MEMORY
k3d-de-k3d-server-0   12304236Ki        12304236Ki
```

```text
Allocated resources:
  Resource           Requests    Limits
  cpu                200m (2%)   0 (0%)
  memory             140Mi (1%)  170Mi (1%)
```

Ở lệnh đầu, đọc hai cột memory của Node; ở lệnh sau, đọc `Requests` và `Limits` đã cộng các Pods trên node. Không đổi nghĩa những cột này thành usage. Giá trị khi chạy lại có thể khác snapshot.

### JVM

- Container limit áp dụng bộ nhớ được hạch toán của container; JVM `-Xmx` chỉ đặt Java heap tối đa.
- Metaspace, thread stacks, direct/native buffers còn cần ngân sách ngoài heap; không nhầm chúng với Pod `spec.overhead`.
- Ví dụ giữ `-Xmx1536m` thì tăng container limit từ `2Gi` lên `3Gi` không tự tăng heap max. Đơn vị `m` của JVM không mang sang memory Kubernetes.
- `java.lang.OutOfMemoryError: Java heap space` khác kernel OOM kill. Heap chưa đầy vẫn có thể OOM kill vì tổng bộ nhớ, và thiếu heap có thể xảy ra trước container limit.

### Metrics

`kubectl top` đọc Metrics API, không hiển thị request/limit: CPU là mức dùng trung bình trong cửa sổ đo, memory là working set ước tính lúc thu thập, không phải heap hoặc peak cả lượt ETL.

Lệnh đọc metrics đã dùng:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  top pod rollout-lab-6bbfc5675d-5b7kr --containers
```

Snapshot 16:09 ngày 2026-11-02:

```text
POD                            NAME   CPU(cores)   MEMORY(bytes)
rollout-lab-6bbfc5675d-5b7kr     web    1m           7Mi
```

Đọc `CPU(cores)` và `MEMORY(bytes)` là usage của mẫu đo, không phải request/limit. Mẫu nhỏ này không đủ sizing production.

Đối chứng 16:11–16:14 ngày 2026-11-02 dùng hai API khác nhau:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  top pod forbid-demo-29893298-kkjvx --containers

/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get pod forbid-demo-29893298-kkjvx \
  -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase'
```

Output lịch sử của lệnh metrics rồi Core API:

```text
Error from server (NotFound): pods "forbid-demo-29893298-kkjvx" not found
```

```text
NAME                          PHASE
forbid-demo-29893298-kkjvx     Succeeded
```

Metrics API không có mẫu nhưng Core API vẫn có Pod `Succeeded`. Không suy Pod bị xóa hoặc usage cả lượt bằng 0 từ lỗi không có metrics; muốn xem peak quá khứ cần hệ thống lưu lịch sử.

## 4. Lab Pending đã kiểm chứng

- [Scaffold](../thuc-hanh/08-resources/01-pending-pod.yaml): Pod đơn `resources-fit-lab`, container `sleeper`, image `busybox:1.37.0`, `sleep 86400`, `restartPolicy: Never`.
- CPU request/limit `25m/100m`; memory request/limit cùng `16Gi`. Request lớn là chủ ý kiểm tra scheduling, không phải chạy chương trình ăn hết RAM.
- Client dùng lúc lab: `/usr/local/bin/kubectl` `v1.33.9`; server đã kiểm ngày 2026-11-02 là `v1.33.6+k3s1`. Không dùng client trên PATH `v1.36.1` cho server này.
- Pod UID `c03eb314-13a4-4586-8ea9-7ed841960c16`, tạo lúc 22:41:24 ngày 2026-11-02 giờ Việt Nam; mentor kiểm tra lúc 22:44–22:47.
- Bằng chứng: phase `Pending`, chưa có `nodeName`, `PodScheduled=False`, reason `Unschedulable`, chưa có containerStatuses.
- Events đúng Pod UID có `FailedScheduling` với thông điệp: `0/3 nodes are available: 1 Insufficient memory, 2 node(s) had untolerated taint {node.kubernetes.io/unreachable: }.` Không suy số lần scheduling từ số Event.
- Ở snapshot đó, server Ready nhưng allocatable nhỏ hơn `16Gi`; hai agent `Ready=Unknown` và có unreachable taints. Đây là lỗi scheduling trước khi container chạy, không phải container OOM.

Lệnh đối chiếu Event với đúng Pod UID:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get events \
  --field-selector='involvedObject.uid=c03eb314-13a4-4586-8ea9-7ed841960c16,reason=FailedScheduling' \
  -o 'custom-columns=REASON:.reason,MESSAGE:.message'
```

Trích phần đầu thông điệp đã quan sát lúc 22:47 ngày 2026-11-02, lược phần preemption và dòng lặp:

```text
REASON             MESSAGE
FailedScheduling   0/3 nodes are available: 1 Insufficient memory, 2 node(s) had untolerated taint {node.kubernetes.io/unreachable: }.
```

Đọc `REASON` cùng `MESSAGE`, không chỉ nhìn phase Pending. Events có retention hữu hạn; chạy lại không thấy Event cũ không phủ định snapshot đã ghi.

### Snapshot mới nhất của Pod

Mentor kiểm tra chỉ đọc lúc **08:39 ngày 2026-11-03**, sau khi xác nhận context và namespace `de-lab` Active. Lệnh tái quan sát:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get pod resources-fit-lab \
  -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase,NODE:.spec.nodeName,MEM_REQUEST:.spec.containers[0].resources.requests.memory,MEM_LIMIT:.spec.containers[0].resources.limits.memory'
```

Output thực tế rút gọn từ các field vừa kiểm tra, không phải kỳ vọng recovery:

```text
NAME                PHASE     NODE     MEM_REQUEST   MEM_LIMIT
resources-fit-lab   Pending   <none>   16Gi          16Gi
```

Nhìn `PHASE`, `NODE`, `MEM_REQUEST` và `MEM_LIMIT`: Pod hiện vẫn chưa được gán node và vẫn giữ cấu hình gây Pending. Lần đọc này còn xác nhận UID cũ, `PodScheduled=False`, chưa có condition Ready; không kiểm lại Nodes, Events, phiên bản, policy, quyền hoặc registry.

Cấu hình recovery `32Mi/64Mi` đã được giải thích cho sleeper; chưa quan sát áp dụng thành công và học viên đã quyết định bỏ qua kiểm chứng. Giữ ghi chú này như giới hạn minh chứng, không phải việc còn phải làm hoặc lý do để mở lại Bài 08. Không ghi Running/Ready hoặc UID mới, không giao lại các thao tác recovery.

## 5. Checkpoint đã đạt

| Khối | Đáp án đã review | Phạm vi |
|---|---|---|
| 1–6 | Tổng 12/12 | Requests/usage, CPU limit, memory limit, tổng Pod requests với regular init, heap và metrics. |
| 7 | Câu đầu về capacity/allocatable đúng; câu ngân sách sai rồi câu sửa sai chọn đúng B | Allocatable không giảm; trừ requests mọi namespace, giữ lịch sử sửa sai. |
| 8 | `1A, 2B` | API từ chối request vượt limit; Pending sau khi đã gán node cần điều tra giai đoạn tiếp theo. |
| 9 | `1B, 2C` | Không mặc định apply thường đổi được resources của Pod hiện hữu; phân biệt UID mới/cũ khi đọc Events. |
| 10 | `1B, 2A` | Requests với native sidecar và hệ quả khi biến sidecar thành regular init không thoát. |

Không hỏi lại chỉ để đủ số câu. Checkpoint không thay bằng chứng runtime hoặc sizing thật. In-place resize có subresource, điều kiện và giới hạn riêng; chưa kiểm chứng trên lab, không khẳng định Kubernetes tuyệt đối không hỗ trợ resize.

## 6. Liên hệ DE–DevOps và giới hạn minh chứng

- **DE tự cấu hình trong phạm vi được cấp:** requests/limits có lý do, JVM/app memory, concurrency; đọc Pod sau admission để tính cả container được inject, defaults và overhead.
- **Cần nền tảng xác nhận:** node pool/sizes/allocatable, reservation, quota/defaults/admission, quyền quan sát và triển khai; image/architecture cùng đường pull thực tế.
- **Quan sát ngoài lab:** Metrics API cần provider, API aggregation, quyền và đường kết nối phù hợp tới kubelet; muốn xem lịch sử/peak cần backend có retention. Metrics Server có sẵn trong K3s lab không phải mặc định của mọi cluster.
- **Lab làm giúp:** k3d/K3s dựng node/runtime và add-ons local; nhiều node-container vẫn dùng chung VM/host. Không cộng allocatable các node thành RAM/CPU vật lý độc lập.
- Metadata registry đã xác nhận `busybox:1.37.0` có ARM64; không chứng minh Pod Pending này đã pull/chạy image. Không tự sửa taint, reservation hoặc node để ép workload vừa.
- Chưa thực nghiệm throttling, OOM, native sidecar, peak ETL, in-place resize hoặc recovery của Pod lab. Không chứng minh HA, khả năng đa node khỏe mạnh hoặc performance production.

## Nguồn theo phiên bản

- [Resource management — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/).
- [Regular init containers — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/init-containers/).
- [Native sidecars — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/).
- [Pod overhead — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/pod-overhead/).
- [Resource metrics pipeline — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/).
- [Node Allocatable — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/).
- [Java 17 launcher](https://docs.oracle.com/en/java/javase/17/docs/specs/man/java.html).
- [In-place resize — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/).
