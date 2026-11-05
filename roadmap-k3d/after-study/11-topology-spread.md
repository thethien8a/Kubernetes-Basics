# Tổng kết Bài 11 — Phân bố replicas và miền lỗi

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/11-topology-spread.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/12-disruptions.md)

- **Ngày hoàn thành:** 2026-11-05, giờ Việt Nam (`Asia/Ho_Chi_Minh`); cleanup được mentor kiểm chứng lúc **16:26:44**.
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`; hai Deployment riêng `spread-lab` và `anti-affinity-lab`, chỉ dùng hai agent cho workload test.
- **Phiên bản:** client `/usr/local/bin/kubectl` `v1.33.9`, API server `v1.33.6+k3s1`, nodes ARM64. Không tự đổi tool hoặc nâng cấp cluster.
- **Kết quả:** spread đạt ba Pod Ready phân bố 1/2; hard anti-affinity có đúng một Pending do không đủ node hợp lệ; recovery về 2/2 giữ hard rules; cleanup Deployment/ReplicaSet/Pod đạt.
- **Ranh giới:** học viên tự apply, sửa replicas và cleanup; mentor chỉ chuẩn bị scaffold, kiểm tra chỉ đọc và lưu tài liệu. Snapshot không phải audit toàn bộ thứ tự lệnh.

## 1. Bài này giải quyết việc gì?

**Replicas trả lời “có bao nhiêu bản sao”; placement trả lời “chúng nằm ở đâu”.** Ba Pod cùng Running không tự chứng minh chúng nằm trên những miền lỗi độc lập.

Ví dụ đã dùng khi giảng lại mục đích: một API stateless cho phép ba bản sao. Nếu cả ba cùng node, mất node đó có thể làm mất cả ba. Trải 2/1 giữa hai node giúp không dồn tất cả vào một node, nhưng chưa chứng minh HA toàn hệ thống. API này là ví dụ lý thuyết; container lab thực tế chỉ chạy `sleep`.

| Yêu cầu | Cơ chế và giới hạn |
|---|---|
| Muốn ba bản sao | Deployment `spec.replicas: 3`; controller duy trì desired count, không tự diễn đạt yêu cầu miền lỗi. |
| Chỉ cho workload dùng một nhóm node | Node selector/required node affinity; không phải luật cấm Pod chung node. |
| Chia tương đối đều, chấp nhận hai Pod chung node | Topology spread; trong ca lab ba Pod/hai miền đủ chỗ, hard `maxSkew: 1` cho phân bố 2/1 hoặc 1/2. |
| Không cho hai Pod cùng nhóm chung node | Required Pod anti-affinity theo hostname; ba Pod cần ít nhất ba node hợp lệ và đủ capacity. |
| Chỉ ưu tiên tránh chung node | Preferred Pod anti-affinity; không bảo đảm tách node và không bỏ qua điều kiện cứng. |

Miền lỗi có thể là node, rack, zone hoặc host chung. **Đổi label không tạo ra hạ tầng độc lập.** Hai agent k3d vẫn chung Mac/runtime/disk; không coi phân bố giữa chúng là chịu mất host.

## 2. Đọc cấu hình theo mục đích

Với Deployment, **PodSpec** nằm ở `spec.template.spec`; labels của Pod ở `spec.template.metadata.labels`, khác labels chỉ đặt trên Deployment.

| Field | Cách đọc trong bài |
|---|---|
| `affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms[].matchExpressions[]` | Chọn Node có label `kubernetes.io/hostname` thuộc một trong hai giá trị agent-0/agent-1. Server Ready vẫn bị loại nếu không match. |
| `topologySpreadConstraints[].topologyKey` | Key của **Node label** dùng chia miền; các Node cùng giá trị thuộc cùng miền. Lab dùng `kubernetes.io/hostname`. |
| `topologySpreadConstraints[].labelSelector` | Chọn **nhóm Pod được đếm** trong cùng namespace; lab khớp `app` AND `lesson`. Không dùng selector này để chọn Node. |
| `topologySpreadConstraints[].maxSkew` | Giới hạn độ lệch khi xét đặt Pod mới với hard rule; `1` không có nghĩa một Pod/node. |
| `topologySpreadConstraints[].whenUnsatisfiable` | `DoNotSchedule`: không chọn nơi vi phạm rule; `ScheduleAnyway`: ưu tiên giảm lệch, không cam kết giới hạn cứng. |
| `affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[]` | Danh sách các term bắt buộc; mỗi term chứa `labelSelector` của Pod cần tránh và `topologyKey` chia miền. |
| `affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution[]` | Mỗi entry có `weight` và `podAffinityTerm`; chỉ là ưu tiên khi chấm điểm node hợp lệ. |

**Các điều kiện phải cùng thỏa:** node hợp lệ theo placement, đủ request budget, không bị taint chưa tolerate, thỏa các hard constraints liên quan. Một node qua spread nhưng thiếu memory request budget vẫn không dùng được.

Tình huống lý thuyết đã học: đang 2/1, cả hai miền vẫn được tính; node ít Pod không đủ budget, node nhiều Pod còn chỗ. Hard spread có thể chặn việc thành 3/1, nên Pod mới vẫn Pending. Đó không phải số đo usage hoặc một thí nghiệm đã chạy.

Scheduler xét placement cho Pod mới; các rule này không tự di chuyển mọi Pod đang chạy để luôn cân bằng lại. `IgnoredDuringExecution` không phải cơ chế tự đuổi Pod khi điều kiện đã dùng lúc scheduling thay đổi.

## 3. Hai scaffold và cấu hình tham khảo

| File được giữ lại | Cấu hình và trạng thái sau bài |
|---|---|
| [01-spread.yaml](../thuc-hanh/11-topology-spread/01-spread.yaml) | `spread-lab`, replicas=3, required node affinity hai agent, hard spread theo hostname; giữ nguyên file. |
| [02-hard-anti-affinity.yaml](../thuc-hanh/11-topology-spread/02-hard-anti-affinity.yaml) | `anti-affinity-lab`, đối chứng ban đầu replicas=3; học viên đã sửa thành **2** để recovery. Giữ trạng thái này, không đổi lại 3. Required node affinity và required Pod anti-affinity vẫn nguyên. |

Hai nhóm có `app` riêng và `lesson: "11"`. Deployment selector, Pod template labels và selector của rule phải khớp đúng nhóm. `spread-lab` không bị đếm thành Pod đối chứng chỉ vì cùng lesson. Không đặt cả explicit spread và hard anti-affinity lên cùng nhóm trong thí nghiệm này.

Khối spread dưới `spec.template.spec` của file 01:

```yaml
topologySpreadConstraints:
  - topologyKey: kubernetes.io/hostname
    labelSelector:
      matchLabels:
        app: spread-lab
        lesson: "11"
    maxSkew: 1
    whenUnsatisfiable: DoNotSchedule
```

Khối hard anti-affinity dưới `spec.template.spec.affinity` của file 02:

```yaml
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: anti-affinity-lab
          lesson: "11"
      topologyKey: kubernetes.io/hostname
```

Cả hai dùng container `worker`, command `["sleep", "3600"]`, `restartPolicy: Always`, `imagePullPolicy: IfNotPresent`, requests `25m/32Mi`, limits `100m/64Mi` mỗi Pod. Image đã pin và kiểm hỗ trợ `linux/arm64/v8` trước lab:

```text
busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

Đây không phải API thật, sizing ETL hoặc hợp đồng restart=0 lâu dài. `sleep` kết thúc sau một giờ thì `Always` có thể restart container. `IfNotPresent` có thể dùng cache; container chạy đúng image không chứng minh vừa pull mới từ registry.

### Preferred chỉ được học qua ví dụ, không triển khai

Đoạn sau nằm dưới `spec.template.spec.affinity`, **chỉ tham khảo cho một nhóm mới** có Pod labels `app=soft-anti-demo`, `lesson="11"`; không phải manifest hoàn chỉnh để apply:

```yaml
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: soft-anti-demo
            lesson: "11"
        topologyKey: kubernetes.io/hostname
```

- `weight` từ 1–100 là trọng số ưu tiên, không phải xác suất hoặc bảo đảm 100%.
- **Required lọc node; preferred chấm điểm các node đã hợp lệ.** Thêm preferred không nới required. Hai agent đã có một Pod mỗi node thì hard anti-affinity vẫn chặn Pod thứ ba.
- `ScheduleAnyway` là giá trị của topology spread, không phải field của Pod anti-affinity.
- Không có Deployment mềm hoặc thí nghiệm migration từ required sang preferred; không coi đổi một đoạn YAML là đã di chuyển các Pod đang chạy.

## 4. Bằng chứng thực hành

Các mốc dưới đây là ngày 2026-11-05, giờ Việt Nam. Trạng thái trước cleanup là **snapshot lịch sử**, không phải resource hiện còn tồn tại.

Helper cho các lệnh quan sát, khóa đúng binary/kubeconfig/context/namespace; không in credential:

```bash
k11() {
  /usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" \
    --context k3d-de-k3d --namespace de-lab \
    --request-timeout=10s "$@"
}
```

Trước kiểm tra live, xác nhận context `k3d-de-k3d` và namespace `de-lab` Active. Tên/AGE/UID có thể khác nếu một lab mới được chủ động tạo; không apply lại chỉ để tái hiện snapshot.

### 4.1 Spread đạt 1/2

Lệnh đã dùng:

```bash
k11 get pods -l app=spread-lab,lesson=11 -o wide
```

Snapshot mentor kiểm lúc **13:45**, rút gọn cột:

```text
NAME                           READY   STATUS    NODE
spread-lab-77fb49f49c-jkqzj     1/1     Running   k3d-de-k3d-agent-1
spread-lab-77fb49f49c-nh4vv     1/1     Running   k3d-de-k3d-agent-0
spread-lab-77fb49f49c-shggj     1/1     Running   k3d-de-k3d-agent-1
```

Đọc `READY`, `STATUS`, rồi **đếm theo `NODE`**: agent-0 một, agent-1 hai, không Pod ở server. Deployment desired/updated/ready/available=3, file/live khớp; owner chain Deployment → ReplicaSet → Pod được đối chiếu bằng UID.

### 4.2 Pending đúng nguyên nhân hard anti-affinity

Lệnh đã dùng:

```bash
k11 get deployment anti-affinity-lab
k11 get pods -l app=anti-affinity-lab,lesson=11 -o wide
```

Học viên đã thấy `READY 2/3`, `UP-TO-DATE 3`, `AVAILABLE 2`; hai Pod Running trên hai agent, một Pod Pending/chưa node. Mentor xác minh lúc **15:19**: Pending Pod `anti-affinity-lab-5cfc6cc85c-lhrvs`, UID `f186e668-2008-4e9f-b3d1-ca71cced3f3a`, `PodScheduled=False/Unschedulable`, chưa containerStatuses.

Lệnh đọc Events của **đúng Pod UID**, chỉ còn trả dữ liệu khi Event còn retention:

```bash
k11 get events \
  --field-selector 'involvedObject.uid=f186e668-2008-4e9f-b3d1-ca71cced3f3a,reason=FailedScheduling' \
  -o custom-columns='REASON:.reason,MESSAGE:.message'
```

Hai đoạn MESSAGE mentor đã kiểm tra, trích nguyên văn phần liên quan:

```text
2 node(s) didn't match pod anti-affinity rules
1 node(s) didn't match Pod's node affinity/selector
```

`FailedScheduling` và đoạn **anti-affinity** xác nhận nguyên nhân: hai agent đã có Pod cùng nhóm nên bị hard rule chặn; server ngoài danh sách required node affinity. Không kết luận từ riêng chữ Pending, không chữa bằng imagePullSecret hoặc app logs.

Deployment có `ProgressDeadlineExceeded` ở snapshot muộn vì chưa đạt desired đầy đủ; điều này không thay Event root cause và không tự rollback hoặc giải quyết thiếu miền. Baseline spread vẫn 3/3.

### 4.3 Recovery giữ luật cứng, giảm desired

Học viên tự sửa **duy nhất `spec.replicas` của file 02 từ 3 thành 2** rồi apply. Mentor xác minh lúc **15:40**:

```bash
k11 get deployment spread-lab anti-affinity-lab
```

Output rút gọn cột, cũng được kiểm lại trước cleanup lúc 16:03:

```text
NAME                READY
spread-lab          3/3
anti-affinity-lab   2/2
```

Đọc `2/2` là **desired đã về hai và cả hai Ready**, không phải ba bản sao chạy được hoặc required trở thành mềm. Deployment generation=observedGeneration=2; cùng ReplicaSet, hai Pod Running cũ giữ UID và mỗi agent một Pod; Pending `lhrvs` không còn. Selector, required node/Pod affinity, image và resources giữ nguyên.

Hai Pod đối chứng được giữ qua recovery:

| Pod suffix | UID | Node |
|---|---|---|
| `7g48m` | `06b29c39-f5e7-42aa-b4b8-0aefc91d9a17` | agent-0 |
| `mfx9s` | `c4a1ecc7-a2e9-4207-81d5-85f113fe4a4a` | agent-1 |

Đây là kết quả đã quan sát, không phải bảo đảm mọi lần scale down đều chọn đúng Pod Pending để xóa. Xóa riêng một Pod khi desired vẫn là ba cũng không xóa yêu cầu ba Pod của controller.

### Identity của hai nhóm trước cleanup

| Resource | UID |
|---|---|
| Deployment `spread-lab` | `d097c8b0-a6b3-4fa3-ad19-8f01a1dd5052` |
| ReplicaSet `spread-lab-77fb49f49c` | `eed6ab7e-0d0b-48ae-ab66-19a63bfdfc47` |
| Deployment `anti-affinity-lab` | `d385e082-0cbf-4155-ac38-7fd3dfd4e7e2` |
| ReplicaSet `anti-affinity-lab-5cfc6cc85c` | `e94643b0-5eab-479e-a92e-a3e89ce2ed43` |

## 5. Cleanup đã kiểm chứng

Sau khi học viên báo “xong”, mentor kiểm tra chỉ đọc lúc **16:26:44**: context đúng, `de-lab` Active, API trả kết quả thành công. Các lệnh sau **không có dòng stdout**:

```bash
k11 get deployment spread-lab anti-affinity-lab --ignore-not-found -o name
k11 get deployments,replicasets,pods \
  -l 'lesson=11,app in (spread-lab,anti-affinity-lab)' -o name
```

Mentor kiểm thêm toàn bộ Deployment/ReplicaSet/Pod trong namespace qua metadata: không còn tên/tiền tố của hai nhóm, label `lesson=11` hoặc `app` tương ứng, UID cũ hoặc dependent tham chiếu owner UID cũ. Selector `lesson=11` được đọc lại cuối lượt cũng có **0 resource**; không chỉ dựa vào selector hẹp hoặc bỏ qua lỗi API.

Lệnh quan sát Node:

```bash
k11 get nodes \
  -o custom-columns='NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status'
```

Output mentor sau cleanup:

```text
NAME                  READY
k3d-de-k3d-agent-0    True
k3d-de-k3d-agent-1    True
k3d-de-k3d-server-0   True
```

Nhìn `READY=True` ở cả ba node. JSON xác nhận thêm: ba UID và hostname labels giữ nguyên, ARM64, taints rỗng, `unschedulable=False`, Memory/Disk/PIDPressure=False. Node là cluster-scoped; `-n de-lab` không làm phép đọc Node chỉ có phạm vi namespace.

Giữ hai file scaffold với replicas **3/2**; không tạo lại workload, sửa Node hoặc xóa namespace để kiểm chứng cleanup. Mentor không thực hiện mutation; snapshot sau dọn không chứng minh chính xác mọi flag hoặc thứ tự lệnh học viên đã chạy.

## 6. Review và nhầm lẫn đã làm rõ

| Nội dung kiểm tra | Kết quả thực tế |
|---|---|
| Replicas không tự chứng minh phân bố/HA; hai agent chung host | Khối 1 `1B, 2A`, đúng 2/2. |
| Topology key đọc Node labels; selector chọn nhóm Pod | Khối 2 `1B, 2C`, đúng 2/2. |
| Chọn chia đều khi cần ba Pod trên hai node | Chọn A đúng sau khi giảng lại mục đích. |
| Đang 2/1, thêm Pod thứ tư khi cả hai node đủ chỗ | Chọn B đúng: thành 2/2 với hard maxSkew=1. |
| Chấp nhận lệch, chỉ ưu tiên phân bố | Chọn A đúng: `ScheduleAnyway`. |
| Server Ready nhưng ngoài hai hostname được phép | Chọn B đúng: required node affinity vẫn loại server. |
| Hard anti-affinity, ba replicas/hai node | Chọn A đúng: hai Running, một Pending; sau đó được kiểm chứng bằng runtime/Events. |
| Giữ required rồi thêm preferred=100 | Chọn B đúng nhưng học viên nói chưa chắc; mentor đã giải thích hai tầng lọc node → chấm điểm, không coi trọng số là quyền phá hard rule. |

Học viên từng thấy giải thích quá nặng field/công thức và chưa rõ mục đích. Mentor đã quay lại bài toán “bao nhiêu bản sao, nằm ở đâu”, tách “chia đều” khỏi “cấm chung node”, rồi nối từng field vào ví dụ. Bộ ba câu khối 3 cũ đã tạm dừng, không ghi thành đã trả lời hoặc hỏi lại để đủ số.

Điểm cần nhớ khi ôn: `maxSkew=1` không phải một Pod/node; preferred không nới required; recovery về hai replicas không đáp ứng SLA ba replicas tách node. Runtime không thay kiểm tra hiểu và đáp án quiz không thay bằng chứng runtime.

## 7. Liên hệ DE, DevOps và giới hạn

| Lựa chọn | Trade-off và khuyến nghị |
|---|---|
| Spread cứng | Giữ yêu cầu độ lệch, có thể thiếu replicas nếu capacity không nằm ở miền cần dùng; phù hợp ca lab chia đều để thấy rõ rule. |
| Spread/anti-affinity mềm | Linh hoạt chạy đủ bản sao khi các điều kiện cứng cho phép, nhưng chấp nhận dồn miền; chọn khi yêu cầu ứng dụng cho phép. |
| Required anti-affinity | Giữ yêu cầu không chung miền, cần đủ miền/capacity hoặc chấp nhận Pending; không mặc định dùng cho mọi workload. |

Nếu production thật sự yêu cầu ba bản sao tách node, DE cần nêu rõ yêu cầu đó với platform và xác nhận ít nhất ba node hợp lệ, đủ capacity. Giảm replicas xuống hai chỉ là recovery sandbox đã thỏa thuận, không phải đạt yêu cầu ba bản sao.

**Lab làm giúp ↔ ngoài lab:** k3d/K3s cung cấp Node/API/scheduler/runtime để quan sát; topology spread và Pod anti-affinity là cơ chế scheduling của Kubernetes, không cần add-on placement riêng của k3d. On-prem cần platform xác nhận ánh xạ máy/rack/zone, nhãn nhất quán, pool và capacity. Managed cloud có thể cung cấp node groups/zone labels, nhưng vẫn phải xác nhận node có ở những miền thật khác nhau và workload được phép dùng chúng. Quyền admin của sandbox không phải quyền DE mặc định.

Khi debug, đi theo thứ tự: đúng context/namespace/Pod UID → PodScheduled/Events → Node labels và required placement → Pod template labels/selector/phạm vi namespace → số miền/capacity/taints và hard constraints khác. Nếu cần sửa Helm values, phải đối chiếu chart/version và resource render; bài này chưa thực hành Helm.

Chưa kiểm chứng: mất Node/host, API thật, HA vật lý, replication/backup dữ liệu, benchmark hoặc tự cân lại khi topology thay đổi. Preferred, zone/rack và tình huống thiếu capacity chỉ được học qua ví dụ; không ghi thành các lab bổ sung đã chạy. Không đọc/in Secret, token hoặc kubeconfig credential.

**Bước tiếp theo:** Bài 12 — Bảo trì node, PDB và node failure; chưa bắt đầu hoặc tạo scaffold bài mới. Theo quy tắc từ 2026-11-05, chỉ cập nhật gộp tài liệu khi chốt trọn bài, không ghi tiến độ sau từng lượt học.

## Nguồn

- [Pod Topology Spread Constraints — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/).
- [Assigning Pods to Nodes — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/).
- [BusyBox 1.37.0 registry metadata](https://hub.docker.com/v2/repositories/library/busybox/tags/1.37.0), đã đối chiếu digest/ARM64 trước lab; không phải bằng chứng fresh pull từ node.
