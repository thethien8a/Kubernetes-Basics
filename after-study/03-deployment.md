# Sau buổi 03 — Deployment, ReplicaSet và desired state

**Bắt đầu:** 2026-10-06 · **Hoàn thành review:** 2026-10-07, giờ Việt Nam.

[Challenge gốc](../roadmap/buoi-hoc/03-deployment.md) · [Tiến độ học tập](../roadmap/tien-do-hoc-tap.md) · [Hội thoại và minh chứng](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f)

Tài liệu này tổng kết kiến thức sau khi thực hành, không yêu cầu học thuộc tên Pod, command hoặc boilerplate YAML.

> **Điểm cốt lõi:** Đặt trạng thái mong muốn ở Deployment. Deployment controller quản lý ReplicaSet; ReplicaSet controller duy trì số lượng Pod. Restart container và tạo Pod thay thế là hai việc khác nhau.

## 1. Đã thực hành và kiểm tra những gì?

- Tạo Deployment `nginx-buoi3` dùng image `nginx`, với `replicas=3`.
- Quan sát Deployment, ReplicaSet và ba Pod trong namespace `default`, context `orbstack`.
- Xóa đúng một Pod, không xóa Deployment hoặc ReplicaSet.
- Quan sát một Pod mới xuất hiện; khi ổn định, Deployment trở lại `READY=3/3`.
- Đối chiếu tên, tuổi, IP và UID để xác nhận đó là Pod mới, không phải container của Pod cũ được restart.
- Kiểm tra quan hệ sở hữu qua `metadata.ownerReferences` và Event tạo Pod của ReplicaSet.
- Review tình huống giảm số Pod, làm rõ phải chỉnh `.spec.replicas` của Deployment đang quản lý workload.

**Giới hạn minh chứng:** Đã kiểm tra thao tác xóa và tạo Pod bù. Các tình huống scale xuống một/hai Pod được kiểm tra bằng câu hỏi lý thuyết, chưa có minh chứng thực hành scale trong hội thoại. Chưa kiểm tra HTTP, đổi image/rollout, mất node hoặc persistence.

## 2. Các đối tượng và thành phần có trách nhiệm gì?

Deployment, ReplicaSet và Pod là các **resource** được lưu và quản lý qua Kubernetes API. **Controller** là logic điều khiển quan sát resource và điều chỉnh trạng thái thực tế; bản thân resource không phải một tiến trình chạy ứng dụng.

| Đối tượng / thành phần | Trách nhiệm trong bài này |
|---|---|
| Deployment | Khai báo cấu hình ứng dụng: số replicas, Pod template và selector. Là cấp quản lý mà người dùng thao tác với workload này. |
| Deployment controller | Tạo/quản lý ReplicaSet theo cấu hình Deployment; cũng điều phối cập nhật khi Pod template thay đổi. Bài này chưa thực hành cập nhật template. |
| ReplicaSet | Giữ yêu cầu về số lượng Pod, selector và template dùng để tạo Pod. ReplicaSet trong bài thuộc Deployment. |
| ReplicaSet controller | Trực tiếp tạo hoặc xóa Pod để điều chỉnh số lượng theo yêu cầu của ReplicaSet. |
| Pod | Một instance của workload. Trong lab, mỗi Pod chứa một container nginx. |
| Scheduler | Chọn node phù hợp cho Pod mới chưa được gán node. Không phải thành phần giữ đủ số replicas. |
| Kubelet và container runtime | Chạy container trên node, xử lý restart container theo policy và báo trạng thái. Không thay ReplicaSet controller tạo Pod bù sau khi Pod bị xóa. |
| kubectl | Client gửi yêu cầu và đọc thông tin từ API server. Không cần giữ Terminal mở để Deployment tiếp tục được quản lý. |

Quan hệ quản lý đã được xác nhận trên cluster:

```diagram
┌────────────────────────┐
│ Deployment nginx-buoi3 │
│ spec.replicas = 3      │
└───────────┬────────────┘
            │ quản lý
            ▼
┌────────────────────────────────┐
│ ReplicaSet                     │
│ nginx-buoi3-66546989b4         │
└───────────┬────────────────────┘
            │ quản lý
            ▼
┌────────────────────────┐
│ Ba Pod nginx           │
│ Mỗi Pod: một container │
└────────────────────────┘
```

**Ba replicas là ba Pod**, không phải ba container trong một Pod hoặc ba Kubernetes node. Cả ba Pod của lab cùng nằm trên node `orbstack`.

## 3. Desired state, actual state và reconciliation

### Desired state — trạng thái mong muốn

Trong bài này, người dùng đặt yêu cầu ở:

```text
Deployment nginx-buoi3
spec.replicas = 3
```

Nghĩa là workload cần được duy trì với ba Pod. Đây là **cấu hình yêu cầu**, không phải số Pod đang có tại mọi thời điểm.

### Actual state — trạng thái thực tế

Đây là những gì đang tồn tại và được quan sát: có bao nhiêu Pod, Pod đã Ready chưa, được đặt ở node nào, có đang khởi động hoặc kết thúc không.

Khi xóa một Pod, cấu hình `replicas=3` không thay đổi. Số Pod đang được duy trì có thể tạm thiếu so với yêu cầu.

### Reconciliation — liên tục điều chỉnh chênh lệch

```diagram
┌────────────────────┐     ┌─────────────────────────┐
│ Mong muốn: 3 Pod   │────▶│ So sánh với thực tế     │
└────────────────────┘     └────────────┬────────────┘
                                        │ thiếu một Pod
                                        ▼
                           ┌─────────────────────────┐
                           │ ReplicaSet controller   │
                           │ tạo Pod mới từ template │
                           └────────────┬────────────┘
                                        ▼
                           ┌─────────────────────────┐
                           │ Scheduler chọn node     │
                           │ Kubelet/runtime chạy    │
                           └────────────┬────────────┘
                                        ▼
                           ┌─────────────────────────┐
                           │ Trở về đủ số lượng Pod  │
                           └─────────────────────────┘
```

Đây không phải cơ chế `kubectl` tự chạy lại câu lệnh tạo Pod. Các controller tiếp tục điều khiển hệ thống sau khi client đã kết thúc.

**Reconcile không phải bảo đảm tức thì:** Trong lúc thay thế có thể thấy Pod `Terminating`, `Pending` hoặc `ContainerCreating`. Danh sách có thể tạm chứa cả Pod đang kết thúc và Pod mới. Nếu thiếu tài nguyên hoặc image gặp lỗi, việc có đủ Pod Ready có thể bị chậm hoặc không đạt; controller không tự sửa được mọi vấn đề của ứng dụng.

## 4. Field cấu hình cần hiểu

| Field của Deployment | Ý nghĩa |
|---|---|
| `.metadata.name` | Tên resource Deployment để thao tác hoặc kiểm tra. Trong lab là `nginx-buoi3`. |
| `.spec.replicas` | Số Pod mong muốn. Đây là field cần đổi khi muốn tăng/giảm số bản sao trong bài này. |
| `.spec.template` | Mẫu Pod: image, container và các cấu hình Pod mà ReplicaSet dùng để tạo instance. |
| `.spec.selector` | Selector xác định tập Pod phù hợp; phải khớp label của Pod template. Labels/selectors sẽ được học kỹ ở buổi 4. |

ReplicaSet cũng có `.spec.replicas`, nhưng **ReplicaSet này do Deployment quản lý**. Với workload đã tạo bằng Deployment, thay đổi yêu cầu ở Deployment, không chỉnh trực tiếp ReplicaSet con.

Phân biệt cách gọi:

- **Resource:** Deployment `nginx-buoi3`.
- **Field:** `.spec.replicas`.
- **Giá trị:** `3`, `2` hoặc `1` tùy số bản sao mong muốn.

Nếu muốn giảm từ ba Pod xuống một Pod, không chỉ xóa thủ công hai Pod. Nếu Deployment vẫn yêu cầu ba, ReplicaSet controller sẽ tạo Pod bù. Cách đúng là đổi `.spec.replicas` của Deployment thành `1`; để giữ hai Pod thì đặt thành `2`.

## 5. Cách đọc output đã dùng

### Deployment

Snapshot trước và sau khi hệ thống ổn định đều có:

```text
NAME          READY   UP-TO-DATE   AVAILABLE
nginx-buoi3   3/3     3            3
```

| Cột | Cách đọc |
|---|---|
| `READY` | Số Pod Ready / số replicas mong muốn. `3/3` là ba Pod Ready trên yêu cầu ba. |
| `UP-TO-DATE` | Số Pod dùng Pod template hiện tại của Deployment. |
| `AVAILABLE` | Số Pod được Deployment tính là khả dụng; Pod phải Ready và đáp ứng thời gian sẵn sàng tối thiểu nếu có cấu hình. Mặc định thời gian này bằng 0. |
| `AGE` | Tuổi của resource Deployment, không phải tuổi của tất cả Pod bên dưới. |

### ReplicaSet

```text
NAME                     DESIRED   CURRENT   READY
nginx-buoi3-66546989b4     3         3         3
```

| Cột | Cách đọc |
|---|---|
| `DESIRED` | Số Pod yêu cầu ở ReplicaSet; trong bài được Deployment điều phối về ba. |
| `CURRENT` | Số Pod controller đang ghi nhận. Không có nghĩa mọi Pod đã Ready. |
| `READY` | Số Pod đã được báo Ready. |

Ngay bảng này đã đủ để kiểm tra câu hỏi: **Sau khi xóa Pod, desired state có đổi không?** Trước và sau đều `DESIRED=3`; xóa một Pod không sửa cấu hình mong muốn.

Thông tin `.status` là kết quả quan sát và có thể cần thời gian cập nhật. Không hiểu một snapshot là trạng thái vĩnh viễn hoặc mọi thay đổi đều xuất hiện đồng thời.

### Pod

- `NAME`: định danh để đối chiếu và thao tác đúng đối tượng, không cần học thuộc.
- `AGE`: giúp nhận ra Pod mới tạo so với các Pod đã tồn tại lâu.
- `IP`: địa chỉ Pod, khác địa chỉ node và không phải định danh bền vững của workload.
- `NODE`: node nơi Pod được gán.
- `RESTARTS`: số lần restart container được báo cho Pod đó, không phải số lần Deployment từng tạo Pod thay thế.
- `READY`: số container Ready / tổng số container được hiển thị cho Pod. Trong lab là `1/1`.

**Tên khác chứng minh đó là đối tượng Pod khác; UID giúp xác định danh tính cả khi một tên được dùng lại.** Pod mới không bắt buộc có IP khác trong mọi tình huống, nên không dùng IP làm bằng chứng duy nhất.

## 6. Minh chứng trước và sau khi xóa Pod

Các giá trị dưới đây là snapshot đã ghi nhận trong buổi học, không phải địa chỉ cần học thuộc hoặc được bảo đảm giữ nguyên ở lần thực hành sau.

| Trước khi xóa | Pod IP | Kết quả sau khi ổn định |
|---|---|---|
| `nginx-buoi3-66546989b4-4b9gl` | `192.168.194.6` | Đã bị xóa, không còn trong danh sách. |
| `nginx-buoi3-66546989b4-6gncw` | `192.168.194.7` | Vẫn tồn tại. |
| `nginx-buoi3-66546989b4-mpszf` | `192.168.194.8` | Vẫn tồn tại. |

Pod thay thế:

| Field | Giá trị ghi nhận |
|---|---|
| Tên | `nginx-buoi3-66546989b4-dg86c` |
| Pod IP | `192.168.194.9` |
| Node | `orbstack` |
| Trạng thái trong output học viên gửi | `Running`, `READY=1/1`, `RESTARTS=0` |
| Tuổi trong snapshot sau khi xóa | `78s`, trong khi hai Pod cũ có tuổi `8h` |
| Owner | ReplicaSet `nginx-buoi3-66546989b4` |

Đối chiếu API xác nhận UID của Pod bị xóa và Pod thay thế khác nhau. Hai Pod còn lại giữ nguyên UID. ReplicaSet vẫn thuộc Deployment `nginx-buoi3`; đây là **tạo Pod mới trong ReplicaSet hiện có**, không phải tạo ReplicaSet mới cho mỗi lần xóa Pod.

Trong lần kiểm tra ngay sau thí nghiệm, đã đọc được Event của ReplicaSet:

```text
Reason:  SuccessfulCreate
Object:  replicaset/nginx-buoi3-66546989b4
Message: Created pod: nginx-buoi3-66546989b4-dg86c
```

Event này là minh chứng đã được ghi nhận trong hội thoại. Đến lần kiểm tra khi viết tổng kết, truy vấn Events không còn trả về Event đó; quan hệ owner và ba Pod vẫn kiểm tra được. Không dùng Events như nhật ký lưu trữ lâu dài hoặc suy ra rằng một hành động chưa từng xảy ra chỉ vì Event không còn trong kết quả hiện tại.

## 7. Restart container khác tạo Pod thay thế

| Tình huống | Thành phần xử lý chính | Điều xảy ra |
|---|---|---|
| Container nginx kết thúc, Pod vẫn được node quản lý | Kubelet phối hợp container runtime, theo `restartPolicy` | Restart container bên trong Pod hiện có; không biến nó thành một Pod mới. |
| Pod thuộc ReplicaSet bị xóa, yêu cầu số lượng không đổi | ReplicaSet controller | Tạo Pod mới để bù số lượng; scheduler và kubelet tiếp tục xử lý Pod mới. |
| Pod đơn lẻ ở buổi 2 bị xóa, không có controller quản lý | Không có controller yêu cầu tạo Pod bù | Pod không tự xuất hiện lại. |

`restartPolicy: Always` không có nghĩa là phục hồi đối tượng Pod đã bị xóa. Trong các Pod của Deployment ở bài này, policy đã kiểm tra là `Always`.

Đây là lý do dùng Deployment cho workload cần chạy liên tục thường phù hợp hơn tạo Pod trực tiếp: không phải tự tạo lại từng Pod khi nó bị xóa, có cấp cấu hình chung và cơ chế quản lý cập nhật. Không vì vậy mà mọi workload đều phải dùng Deployment; workload chạy một lần hoặc cần identity/storage ổn định sẽ học các resource phù hợp ở các buổi sau.

## 8. Lệnh tham khảo

Các lệnh dưới đây dùng context `orbstack`, namespace `default`. Phân biệt rõ lệnh **chỉ đọc** với lệnh **thay đổi cluster**; không cần chạy lại để được tính hoàn thành buổi này.

### Lệnh chỉ đọc

```bash
kubectl --context=orbstack -n default get deployment nginx-buoi3
kubectl --context=orbstack -n default get rs -l app=nginx-buoi3
kubectl --context=orbstack -n default get pods -l app=nginx-buoi3 -o wide
kubectl --context=orbstack -n default get deploy,rs,pods -l app=nginx-buoi3 -o wide
```

- `rs` là viết tắt của ReplicaSet.
- `-l app=nginx-buoi3` lọc resource mang label đó; không tự tạo hoặc thay đổi resource.
- `-o wide` bổ sung thông tin như IP và node cho Pod.

Theo dõi thay đổi; Ctrl+C chỉ dừng client theo dõi:

```bash
kubectl --context=orbstack -n default get pods -l app=nginx-buoi3 -o wide -w
```

Kiểm tra cấu hình mong muốn và trạng thái chi tiết:

```bash
kubectl --context=orbstack -n default get deployment nginx-buoi3 -o jsonpath='{.spec.replicas}{"\n"}'
kubectl --context=orbstack -n default describe deployment nginx-buoi3
kubectl --context=orbstack -n default describe rs nginx-buoi3-66546989b4
```

Với một Pod đang tồn tại, thay `POD_NAME` bằng tên lấy từ output; không chạy nguyên placeholder:

```bash
kubectl --context=orbstack -n default describe pod POD_NAME
```

Tìm `Controlled By` để xem owner. `metadata.ownerReferences` trong output JSON/YAML cung cấp thông tin sở hữu; không chỉ dựa vào việc tên có chung tiền tố.

### Lệnh thay đổi cluster — chỉ là tài liệu tham khảo

Lệnh tạo đã dùng trong lab; không chạy lại nếu Deployment cùng tên đang tồn tại:

```bash
kubectl --context=orbstack -n default create deployment nginx-buoi3 --image=nginx --replicas=3
```

Lệnh xóa chỉ một Pod để thử khả năng tạo bù, không xóa Deployment hoặc ReplicaSet:

```bash
kubectl --context=orbstack -n default delete pod POD_NAME
```

Lệnh scale tương ứng với tình huống giữ hai Pod đã review về lý thuyết:

```bash
kubectl --context=orbstack -n default scale deployment nginx-buoi3 --replicas=2
```

Lệnh này sửa yêu cầu ở Deployment; **không phải thao tác đã được chạy để viết tổng kết**. Trạng thái kiểm tra khi viết tài liệu vẫn là Deployment yêu cầu ba replicas và có ba Pod Ready.

## 9. Các nhầm lẫn đã được sửa

| Nhầm lẫn | Cách hiểu đúng |
|---|---|
| Phải nhớ tên Pod để hiểu bài. | Không cần nhớ tên; chỉ cần đọc/đối chiếu tên hoặc UID khi cần thao tác hay chứng minh Pod mới. |
| Không biết kiểm tra desired state ở đâu. | Cột `DESIRED` của ReplicaSet đã có trong output; cấu hình cấp người dùng của bài này là Deployment `.spec.replicas`. |
| Muốn từ ba Pod xuống một thì xóa hai Pod. | Nếu yêu cầu vẫn là ba, controller tạo bù. Phải đổi yêu cầu mong muốn. |
| ReplicaSet trực tiếp tạo Pod, vậy cứ sửa ReplicaSet. | Với ReplicaSet do Deployment sở hữu, đặt cấu hình ở Deployment, không quản lý trực tiếp resource con. |
| Pod xuất hiện lại nghĩa là Pod cũ được restart. | Pod đã bị xóa không sống lại; một Pod mới được tạo để thay thế. |
| Deployment hoặc scheduler restart nginx trong Pod. | Kubelet/runtime xử lý container; ReplicaSet controller xử lý số lượng Pod; scheduler chọn node. |
| Ba replicas nghĩa là ba node hoặc luôn có ba Pod Ready tức thì. | Trong lab, ba Pod cùng một node. Tạo bù cần thời gian và phụ thuộc điều kiện chạy workload. |

## 10. Liên hệ Data Engineering và giới hạn của lab

Khi sau này quản lý component chạy liên tục của data platform, ví dụ một nhóm Spark Worker Pod, cần phân biệt **số Pod mong muốn** với việc ứng dụng bên trong đã đăng ký hoặc xử lý dữ liệu thành công chưa.

- Quản lý vòng đời Pod không thay thế kiểm tra hành vi của Spark hoặc ứng dụng.
- Controller tạo Pod bù không đồng nghĩa dữ liệu của ứng dụng được giữ lại; persistence sẽ được học riêng.
- Ba Pod cùng node `orbstack` không tạo ra khả năng chịu mất node. Bài này kiểm tra việc xóa một Pod, không phải high availability của toàn platform.

Không triển khai thêm component DE hoặc cấu hình production để minh họa những điểm này trong buổi 3.

## 11. Câu hỏi đã review và kết luận

1. **Sau khi xóa một Pod, `DESIRED` có đổi không?** Không; vẫn là ba vì chưa sửa yêu cầu.
2. **Ai trực tiếp tạo Pod bù?** ReplicaSet controller, không phải kubelet hoặc scheduler.
3. **Muốn còn một hoặc hai Pod, chỉnh ở đâu?** Deployment tương ứng, field `.spec.replicas`, giá trị `1` hoặc `2`.
4. **Container kết thúc nhưng Pod còn tồn tại, ai xử lý restart?** Kubelet phối hợp runtime theo policy.
5. **Vì sao khác Pod đơn lẻ ở buổi 2?** Pod đơn lẻ trong bài đó không có controller yêu cầu duy trì số lượng; Pod của buổi 3 có ReplicaSet quản lý.

**Kết quả: Buổi 03 đạt sau thực hành và review.** Ghi nhớ chuỗi trách nhiệm và field cấu hình, không học thuộc các tên sinh tự động.

**Tiếp theo:** [Buổi 04 — Labels và Selectors](../roadmap/buoi-hoc/04-labels-va-selectors.md), chưa bắt đầu trong lần cập nhật này.

## Tài liệu tham khảo

- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/): desired state, `.spec.replicas`, scaling và khuyến nghị không quản lý trực tiếp ReplicaSet do Deployment sở hữu.
- [Kubernetes — ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/): tạo/xóa Pod theo số lượng yêu cầu, Pod template, ownerReferences và sự khác nhau giữa quản lý Pod với restart container.
- [Hội thoại thực hành và review](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f): nguồn của tên, IP, UID đã đối chiếu, output và Event được ghi nhận trong bài.
