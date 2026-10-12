# Sau buổi 10 - CPU và Memory

**Ngày học và review đạt:** 2026-10-10, giờ Việt Nam. **Ngày lưu tổng kết:** 2026-10-11. **Tiến độ sau review:** 10/28.

[Challenge gốc](../roadmap/buoi-hoc/10-cpu-va-memory.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Manifest cuối bài](../app-buoi10.yaml) · [Hội thoại thực hành và review](https://ampcode.com/threads/T-01a124e8-0c58-74cc-9f3b-573959d0a36a)

> Requests là nhu cầu khai báo dùng để tính ngân sách scheduling; limits được thực thi khi container chạy. Không đồng nhất requests, limits và mức sử dụng thực tế.

## 1. Challenge và phạm vi

Học viên tự triển khai ba thí nghiệm trên Deployment `default/app-buoi10`, một replica trong context `orbstack`:

1. Request RAM vượt ngân sách node, rồi giảm request để Pod được schedule.
2. Chạy cùng vòng tính hữu hạn với CPU limit 100m và 500m, giữ CPU request 100m.
3. Chương trình Python cấp buffer 128Mi với memory limit 64Mi, rồi tăng chỉ limit để khắc phục.

Mentor tự đọc manifest/API, Events, logs và cgroup bằng thao tác chỉ đọc; không chạy tải hoặc sửa/apply workload thay học viên trong các thí nghiệm. Dọn demo ngày 2026-10-11 là yêu cầu riêng của học viên, được ghi ở mục 9.

Không triển khai Spark, PostgreSQL, Metrics Server, PVC hoặc toàn bộ data platform cho bài này. Manifest hiện có là bản Python sau khắc phục, không phải ba phiên bản thí nghiệm cùng lúc.

## 2. Mental model và field quan trọng

```diagram
Pod template: resources
     │
     ├── requests ──→ Scheduler ──→ Chọn node theo ngân sách
     │
     └── limits ────→ Kubelet/runtime ──→ Linux cgroup/kernel
                                              │
                                              ├── CPU: throttling
                                              └── Memory: có thể OOM-kill
```

| Field / khái niệm | Ý nghĩa cần nhớ |
|---|---|
| `spec.template.spec.containers[].resources.requests` | Nhu cầu khai báo của container trong Deployment; scheduler dùng để xét placement. Không phải trần sử dụng hoặc RAM được cấp phát sẵn. |
| `resources.limits.cpu` | Trần thời gian CPU được runtime/kernel thực thi. Dùng hết quota có thể bị throttling, không bị kill chỉ vì dùng hết quota CPU. |
| `resources.limits.memory` | Giới hạn memory của cgroup. Khi cấp phát vượt khả năng trong giới hạn, kernel có thể OOM-kill; không phải lượng RAM được cấp sẵn hoặc bảo đảm node luôn có đủ RAM thực. |
| `Node.status.allocatable` | Ngân sách node dành cho Pod, cần đối chiếu tổng requests đã được schedule trên chính node đó. |
| `100m`, `500m` CPU | 0,1 và 0,5 CPU; không phải 10% và 50% toàn node 10 CPU. |
| `Mi`, `Gi` | Đơn vị nhị phân: 1Gi = 1024Mi. Không bỏ đơn vị khi đọc request/limit RAM. |
| `State`, `Last State`, `Restart Count` | Trạng thái hiện tại, lần kết thúc gần nhất và số lần restart container trong Pod. |

Với tình huống đơn giản của bài, ngân sách scheduling RAM còn lại là Allocatable trừ tổng requests của các Pod hiện có trên node. RAM thực đang dùng thấp không thay thế phép tính này. Đây không phải quy tắc bỏ qua taints, affinity hoặc các điều kiện scheduling khác.

## 3. Request RAM cao: Pending trước khi container chạy

| Mốc kiểm chứng ngày 2026-10-10 | Cấu hình và kết quả |
|---|---|
| 16:38 giờ Việt Nam | Request RAM 16Gi, limit 16Gi; node Allocatable `12304840Ki`, khoảng 11,73GiB. Pod Pending, chưa có node/IP, `PodScheduled=False`, reason Unschedulable, chưa có containerStatuses. Events có FailedScheduling/Insufficient memory. |
| 17:00 giờ Việt Nam | Học viên giảm chỉ request RAM xuống 1Gi, giữ limit 16Gi và app chỉ sleep. Pod mới Running/Ready 1/1, RESTARTS=0; logs có `app-buoi10 started`. |

Pod Pending: `app-buoi10-598cf6746b-pqjfc`, UID `145b4e4f-5d4f-4141-8821-ab780e05f4fb`. Pod sau khắc phục: `app-buoi10-6d96844df7-lsdwz`, UID `ef9db177-98cb-419a-9d47-2d375aeb01c4`.

Request 16Gi vượt cả Allocatable của node, nên giải phóng Pod khác cũng không làm node này chứa được request đó. App chỉ sleep không khiến scheduler bỏ qua requests. Giữ limit 16Gi không chặn placement sau khi request vừa ngân sách, nhưng cũng không bảo đảm app sẽ dùng được 16Gi RAM thực.

**Phân biệt:** READY 0/1 riêng lẻ không chứng minh container chưa chạy; trong case này cần node trống, PodScheduled=False và chưa có containerStatuses. Pending do placement không phải OOMKilled.

## 4. CPU limit: thời gian trôi qua và throttling

Hai lượt dùng `busybox:1.36`, cùng vòng tính một triệu lần tăng biến, CPU request 100m và RAM request/limit 1Gi/16Gi. Script chạy phép tính hữu hạn bằng `busybox time -p`, sau đó giữ container sống bằng sleep.

| Minh chứng | Limit 100m | Limit 500m |
|---|---|---|
| Pod | `app-buoi10-68cb8c55cc-h8rmq` | `app-buoi10-5968c68757-bjbz5` |
| Giờ logs, ngày 2026-10-10 | 17:25:14 | 21:56:13 |
| `real`, giây | 30,57 | 1,58 |
| `user`, giây | 3,04 | 0,80 |
| `sys`, giây | 0,00 | 0,00 |
| `cpu.max` | `10000 100000` | `50000 100000` |
| `nr_throttled` tại snapshot | 306 | 16 |
| `throttled_usec` tại snapshot | 27510828 | 572366 |
| Trạng thái | Running/Ready, RESTARTS=0 | Running/Ready, RESTARTS=0 |

- `real` là thời gian trôi qua; `user`/`sys` là thời gian CPU của lệnh đo, có làm tròn.
- `cpu.max` ở lượt 100m cho quota 10ms CPU mỗi chu kỳ 100ms; lượt 500m cho 50ms mỗi chu kỳ 100ms.
- `cpu.stat` là bộ đếm tích lũy của container tại lúc đọc, không phải phép đo tách riêng vòng tính. Bộ đếm throttling dương xác nhận cơ chế kernel, thay vì chỉ đoán từ việc app chậm.
- 500m vẫn có throttling khi phép tính muốn chạy liên tục; tăng limit không có nghĩa bộ đếm phải về 0.

**Giới hạn so sánh:** real giảm khoảng 19,35 lần nhưng quota chỉ tăng 5 lần; user cũng giảm 3,8 lần. Hai lượt cách nhau khoảng 4,5 giờ, điều kiện CPU host/node chưa được kiểm soát. Không quy toàn bộ tăng tốc cho CPU limit hoặc gọi đây là benchmark chuẩn. Tỷ lệ user/real khoảng 9,9% và 50,6% phù hợp quota ở hai lượt, nhưng bằng chứng trực tiếp vẫn là cpu.max/cpu.stat.

## 5. Memory limit: OOMKilled và khắc phục

Học viên dùng `python:3.12-alpine`, chạy Python trực tiếp làm tiến trình chính. Script tạo bytearray 128Mi, ghi một byte mỗi bước 4096 byte, in `Allocated 128 MiB` rồi sleep 3600 giây. CPU request/limit giữ 100m/500m.

| Mốc kiểm chứng ngày 2026-10-10 | Kết quả |
|---|---|
| Request/limit RAM 32Mi/64Mi, 22:14–22:20 | Pod đã schedule, nhưng container Waiting/CrashLoopBackOff. Last State Terminated/OOMKilled, exit 137; Restart Count tăng 5 → 6 trong cùng UID Pod. |
| Tăng chỉ limit lên 1Gi, 22:33 | Pod Python mới Running/Ready 1/1, RESTARTS=0; logs có `Allocated 128 MiB`. Deployment updated/ready/available đều 1, không còn lấy Pod CPU cũ làm minh chứng. |
| Đọc cgroup sau khắc phục | `memory.max=1073741824` bytes, `memory.current=140906496` bytes, khoảng 134,4Mi; các bộ đếm OOM tại snapshot bằng 0. |
| Monitor 22:35:12–22:36:12 | Cùng UID và container startedAt, Running/Ready, RESTARTS=0 trong 60 giây quan sát. |

Pod lỗi: `app-buoi10-b774ff8c6-wr294`, UID `f8ac92b0-4394-4e1b-b0a4-addff48f1575`. Pod sau khắc phục: `app-buoi10-5d4f9d6ff8-5vcjr`, UID `b52ec227-f7d7-4f02-b27d-e7366dff61ef`.

Các field trong manifest cuối bài:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "32Mi"
  limits:
    cpu: "500m"
    memory: "1Gi"
```

**Trade-off:** 1Gi đủ cho thí nghiệm nhưng chưa chứng minh tối ưu. Request 32Mi thấp hơn RAM quan sát; giữ nguyên để cô lập biến, không coi là sizing phù hợp cho app thật. Buffer không phải toàn bộ RAM Python sử dụng; phải tính cả interpreter và các thành phần còn lại.

**Cách đọc lỗi:** CrashLoopBackOff là chờ sau thất bại lặp, không phải nguyên nhân gốc. Exit 137 riêng lẻ không đủ khẳng định OOM; trong bài có Last State.reason=OOMKilled. Khi rollout lỗi, Deployment còn giữ Pod CPU cũ Ready nên READY 1/1 của Deployment không chứng minh bản Python đã chạy ổn.

## 6. Review đã đạt và phần mentor bổ sung

| Câu review | Câu trả lời / đánh giá |
|---|---|
| Request RAM quá cao gây vấn đề ở đâu? | Học viên nhận định request vượt tài nguyên node nên chưa được gán node/chạy container. Mentor chuẩn hóa units và Allocatable/tổng requests. |
| CPU limit 100m làm Pending, restart hay chậm hơn? | Học viên dự đoán phép tính chậm hơn, không Pending/restart trong case này; sau đó dự đoán tăng limit làm real giảm. Runtime và cgroup phù hợp. |
| App cố dùng 128Mi với request 32Mi, limit 64Mi: sửa field nào? | Học viên chọn limits.memory vì placement đã đạt nhưng limit không đủ. Mentor bổ sung giới hạn runtime không phải RAM cấp sẵn, và overhead của Python. |
| Request 32Mi nhưng app dùng khoảng 134Mi: request có phải trần không? | Học viên trả lời request không phải trần. Mentor nối với minh chứng mức dùng còn dưới limit 1Gi. |
| Node 2Gi, requests hiện có 1,5Gi, RAM thực dùng 400Mi: Pod mới request 768Mi có vừa không? | Học viên tự tính 2Gi − 1,5Gi = 512Mi < 768Mi nên không schedule trong giả định chỉ xét RAM và giữ nguyên Pod hiện có. Đây là tình huống review, không phải số liệu node live. |
| Tên/UID Pod giữ nguyên, Restart Count tăng 5 → 6? | Học viên trả lời nguyên văn “container restart” lúc 22:54:15 ngày 2026-10-10. Mentor xác nhận đúng và bổ sung lý do: restart trong cùng Pod giữ UID; Pod mới có UID khác. Không ghi lý do này là học viên đã tự nêu. |

Mentor đã xác nhận review Buổi 10 đạt trong hội thoại trước. Lượt lưu tài liệu sau đó bị dở; ngày 2026-10-11 đối chiếu lại hội thoại và hoàn tất tổng kết/tiến độ, không bắt học viên trả lời lại.

## 7. Command quan sát để ôn

Workload demo đã được dọn. Các lệnh dưới đây chỉ dùng khi học viên tự triển khai lại app phù hợp; không còn logs/cgroup live của các Pod cũ để đọc lại. Nhật ký tiến độ lưu các snapshot trước/sau.

```bash
kubectl --context=orbstack -n default get pods -l app=app-buoi10 -o wide
kubectl --context=orbstack -n default describe pod -l app=app-buoi10
kubectl --context=orbstack describe node orbstack
kubectl --context=orbstack -n default logs deployment/app-buoi10 -c app \
  --tail=10 --timestamps=true
kubectl --context=orbstack -n default exec deployment/app-buoi10 -c app -- \
  cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/cpu.stat
kubectl --context=orbstack -n default exec deployment/app-buoi10 -c app -- \
  cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current \
      /sys/fs/cgroup/memory.events
```

Đường dẫn cgroup trên đã đọc được trong lab Linux/cgroup v2; không giả định mọi node/container runtime có cùng layout. Trước khi đọc logs cần xác nhận app không in dữ liệu nhạy cảm. Không cài Metrics Server chỉ để hoàn thành bài: lab chưa có Metrics API, status/Events/logs và cgroup đã đủ cho các phép quan sát này.

## 8. OrbStack, ngoài lab và liên hệ Data Engineering

- OrbStack chuẩn bị node Linux cho lab; RAM Mac 24GB không đồng nghĩa Allocatable của node. Bài quan sát Allocatable khoảng 11,73GiB.
- Requests/limits, scheduling và Linux cgroup là cơ chế Kubernetes/runtime/kernel, không cần wildcard DNS, LoadBalancer hoặc local-path provisioner của OrbStack.
- Trên cluster tự quản lý, người vận hành chuẩn bị node/runtime và cấu hình reservation; trên managed Kubernetes, provider quản lý một phần hạ tầng nhưng vẫn phải kiểm tra Allocatable và ngân sách từng node thực tế. App khai báo requests/limits trong Pod template.
- Khi Pending, kiểm tra scheduling conditions/Events và ngân sách node trước. Khi container dừng, đọc State/Last State/reason/exit code; khi CPU chậm, cần đối chiếu quota và throttling, không chỉ dựa vào elapsed time.
- Với Spark/data workload, RAM interpreter, buffer, heap/off-heap và tải thay đổi cần được đo để sizing; Pod limit không đồng nhất tài nguyên Spark Worker quảng bá. Đây là liên hệ cho các buổi sau, chưa triển khai Spark hoặc đo sizing production.

**Giới hạn:** thực hành trên OrbStack, chưa kiểm chứng cluster ngoài lab; CPU không phải benchmark kiểm soát, RAM là snapshot và monitor hữu hạn, không có tải DE thật. Chưa học Volume/PV/PVC/StorageClass trong Buổi 10.

## 9. Dọn demo ngày 2026-10-11 theo yêu cầu học viên

Trước khi dọn lúc 11:43 giờ Việt Nam, Pod Python giữ cùng UID, Ready với Restart Count 13. **Lần kết thúc gần nhất** là Completed/exit 0, từ 10:32:47 đến 11:32:48 giờ Việt Nam, phù hợp script sleep 3600 rồi kết thúc và restartPolicy Always. Snapshot này không chứng minh nguyên nhân mọi lần restart trước đó. memory.current khoảng 134,1Mi; memory.events của container hiện tại không có OOM, không dùng bộ đếm này để suy ra lịch sử mọi container cũ.

Đối chiếu bài sau không yêu cầu giữ các app demo 08–10; live chỉ có tham chiếu ConfigMap/Secret từ chính nhóm demo và không có PV/PVC hoặc app mount dữ liệu bền vững. Đã xóa chính xác:

- Deployment `app-buoi8`, `app-buoi9`, `app-buoi10`, cùng ReplicaSet/Pod do chúng quản lý bằng foreground cascading deletion.
- ConfigMap `app-config-buoi8` và Secret lab `app-secret-buoi9`; không xuất/giải mã nội dung Secret.

Kiểm tra sau dọn lúc 11:44:28: namespace default không còn workload/ReplicaSet/Pod; cả hai config resource không còn. Tổng Pod giảm 7 → 4. Node Ready; CoreDNS, local-path provisioner, Traefik và Pod ServiceLB của Traefik giữ cùng UID, Ready và restart count như trước. Giữ Service hệ thống, StorageClass, namespace, manifest và minh chứng học tập. Không thao tác context minikube/k3d-demo, xóa image cache hoặc tắt cluster.

Chưa đo lượng RAM macOS giảm; limit 1Gi không phải lượng RAM thực tế được giải phóng. Dọn workload không đồng nghĩa trả ngay mọi bộ nhớ/cache của VM về host.

**Buổi 10 hoàn thành, tổng 10/28.** Tiếp tục [Buổi 11 - Ephemeral filesystem và Volume](../roadmap/buoi-hoc/11-ephemeral-filesystem-va-volume.md).

## Tài liệu tham khảo

- [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/).
- [Reserve Compute Resources for System Daemons](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/).
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/).
