# Sau buổi 04 — Labels, Selectors và cách Service chọn Pod

**Ngày học và hoàn thành review:** 2026-10-07, giờ Việt Nam.

[Challenge gốc](../roadmap/buoi-hoc/04-labels-va-selectors.md) · [Tiến độ học tập](../roadmap/tien-do-hoc-tap.md) · [Hội thoại và minh chứng](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f)

Tài liệu tổng kết những gì đã thực hành và review, không yêu cầu học thuộc tên Pod, IP hoặc boilerplate YAML.

> **Điểm cốt lõi:** Service đối chiếu `.spec.selector` với `.metadata.labels` của Pod trong cùng namespace. Nhãn của chính Service hay Deployment không thay thế nhãn của Pod. Pod mới lấy nhãn từ Pod template, không tự kế thừa `Deployment.metadata.labels`.

## 1. Đã thực hành và kiểm tra những gì?

- Dùng lại Deployment `nginx-buoi3` và ba Pod nginx từ buổi 3, trong context `orbstack`, namespace `default`.
- Tạo Service `nginx-buoi4` bằng CLI, với selector cố tình không khớp các Pod hiện có.
- Quan sát nhãn Pod, `describe service` và EndpointSlice để tìm nguyên nhân Service không có Pod đích.
- Học viên xác định Service đang tìm `app=nginx-buoi4`, trong khi Pod có `app=nginx-buoi3`; đề xuất đổi selector của Service sang `app=nginx-buoi3`.
- Sau hướng dẫn sửa, kiểm tra chỉ đọc xác nhận selector thực tế đã đổi, EndpointSlice chứa đúng ba Pod đích và tất cả đều Ready.
- Gửi request từ Mac qua Service IP; nhận HTTP 200 và trang nginx.
- Review sự khác nhau giữa tên resource, nhãn của resource, selector và nhãn trong Pod template.
- Đọc template của Deployment và ReplicaSet để giải đáp tình huống Pod được tạo lại sau khi chỉ đổi nhãn của chính Deployment.

**Giới hạn minh chứng:** Trong buổi 4 không thực hiện đổi `Deployment.metadata.labels` hoặc xóa lại Pod. Các tình huống Pod thay thế, IP mới và xóa cả ba Pod chỉ được giải thích về lý thuyết. Chưa chạy client Pod để kiểm tra DNS nội bộ, chưa thử NodePort, LoadBalancer hoặc Ingress.

## 2. Label và selector là gì?

### Label — nhãn gắn trên resource

Label là một cặp `key=value` dùng để mô tả, phân nhóm hoặc chọn resource.

Trong lab, các Pod có:

```text
app=nginx-buoi3
pod-template-hash=66546989b4
```

- `app` là key; `nginx-buoi3` là value.
- Nhiều Pod có thể mang cùng một label; label không phải tên hay định danh duy nhất của Pod.
- `pod-template-hash` là nhãn đã quan sát trên Pod và template của ReplicaSet; không cần ghi nhớ giá trị sinh tự động này.

### Selector — điều kiện lựa chọn theo label

Selector của Service trong bài là điều kiện cần khớp trên Pod:

```yaml
spec:
  selector:
    app: nginx-buoi3
```

Service chọn các Pod có `app=nginx-buoi3` trong namespace của nó. Pod vẫn có thể mang thêm nhãn khác, như `pod-template-hash`; không cần liệt kê nhãn đó trong selector này.

**Service không chọn Pod theo việc tên Pod hoặc tên Deployment giống tên Service.** Tên `nginx-buoi4` và `nginx-buoi3` khác nhau không cản trở việc chọn đúng Pod.

## 3. Phân biệt các field dễ nhầm

| Field | Vai trò trong bài |
|---|---|
| `Service.metadata.name` | Tên Service, ở đây là `nginx-buoi4`. Không phải điều kiện tìm Pod. |
| `Service.metadata.labels` | Nhãn của chính resource Service; sau sửa vẫn là `app=nginx-buoi4`. |
| `Service.spec.selector` | Điều kiện Service dùng để chọn Pod; sau sửa là `app=nginx-buoi3`. |
| `Deployment.metadata.labels` | Nhãn gắn trên chính Deployment, không phải nhãn Service trực tiếp đối chiếu. |
| `Deployment.spec.template.metadata.labels` | Nhãn trong mẫu Pod mà Deployment cung cấp cho ReplicaSet tương ứng. |
| `ReplicaSet.spec.template.metadata.labels` | Nhãn trong mẫu ReplicaSet dùng khi tạo Pod. |
| `Pod.metadata.labels` | Nhãn thực tế của Pod mà selector Service cần khớp. |

Quan hệ cần nhớ sau khi sửa:

```diagram
┌────────────────────────────────┐
│ Service nginx-buoi4            │
│ spec.selector                  │
│ app=nginx-buoi3                │
└───────────────┬────────────────┘
                │ so khớp trong namespace default
                ▼
┌────────────────────────────────┐
│ Pod.metadata.labels            │
│ app=nginx-buoi3                │
│ pod-template-hash=66546989b4   │
└────────────────────────────────┘
```

**Service chọn nhóm Pod; ReplicaSet controller duy trì số lượng Pod.** Sửa selector không tạo thêm Pod, không sửa yêu cầu replicas và không restart container nginx.

## 4. Minh chứng trước khi sửa

Lệnh tạo Service học viên đã chạy:

```bash
kubectl --context=orbstack -n default create service clusterip nginx-buoi4 --tcp=80:80
```

Lệnh `kubectl create service clusterip` này sinh nhãn Service và selector `app=nginx-buoi4`, theo tên đã truyền cho CLI. Đã kiểm tra bằng client dry-run. Đây là cách lệnh sinh cấu hình, **không phải quy tắc Kubernetes yêu cầu tên Service phải giống tên Deployment**.

Snapshot từ output học viên gửi:

| Phần quan sát | Giá trị trước khi sửa |
|---|---|
| Ba Pod nginx | `Running`, `READY=1/1`, `RESTARTS=0` |
| Label trên mỗi Pod | `app=nginx-buoi3,pod-template-hash=66546989b4` |
| Tên Service | `nginx-buoi4` |
| Nhãn của Service | `app=nginx-buoi4` |
| Selector của Service | `app=nginx-buoi4` |
| Service IP | `192.168.194.166` |
| Type, Port và TargetPort | `ClusterIP`, `80/TCP`, `80/TCP` |
| Dòng `Endpoints` trong describe | Trống |

EndpointSlice đã tồn tại nhưng chưa có địa chỉ đích:

```text
NAME                ADDRESSTYPE   PORTS     ENDPOINTS
nginx-buoi4-p6d8v    IPv4          <unset>   <unset>
```

### Đọc bằng chứng như thế nào?

- Pod đang chạy không có nghĩa Service chắc chắn chọn được Pod đó.
- `Running` và `READY` là các thông tin khác nhau; trong lab cả ba Pod có container Ready và được kiểm tra trạng thái backend sau sửa.
- Dòng `Endpoints` trống và cột `ENDPOINTS=<unset>` cho thấy Service chưa có địa chỉ Pod đích được ghi nhận.
- Một resource EndpointSlice không tương đương một Pod đích; phải xem các endpoint bên trong.
- `PORTS=<unset>` trong slice rỗng không có nghĩa Service chưa cấu hình port: `describe service` vẫn thể hiện Port và TargetPort đều là 80.
- Trong trường hợp này, điều kiện `app=nginx-buoi4` không khớp nhãn `app=nginx-buoi3` của các Pod cần chọn. Không cần sửa image hoặc restart nginx để giải quyết sự không khớp đó.

## 5. Cách sửa và kết quả đã kiểm chứng

Giữ nguyên Deployment, các Pod và tên Service; chỉ đổi điều kiện chọn Pod:

```diff
 spec:
   selector:
-    app: nginx-buoi4
+    app: nginx-buoi3
```

Lệnh sửa đã được hướng dẫn:

```bash
kubectl --context=orbstack -n default patch service nginx-buoi4 \
  --type=merge \
  -p '{"spec":{"selector":{"app":"nginx-buoi3"}}}'
```

Mentor kiểm tra lệnh bằng `--dry-run=client -o yaml`, không áp dụng patch lên cluster thay học viên. Kiểm tra selector thực tế ngay sau dry-run vẫn là `app=nginx-buoi4`; ở lần review sau, API ghi nhận Service đã được sửa thành `app=nginx-buoi3`.

### Backend sau khi sửa

Kiểm tra API chỉ đọc đối chiếu địa chỉ và `targetRef` trong EndpointSlice với ba Pod:

| Pod | Pod IP | Node | Điều kiện endpoint |
|---|---|---|---|
| `nginx-buoi3-66546989b4-6gncw` | `192.168.194.7` | `orbstack` | `ready=true`, `serving=true`, `terminating=false` |
| `nginx-buoi3-66546989b4-mpszf` | `192.168.194.8` | `orbstack` | `ready=true`, `serving=true`, `terminating=false` |
| `nginx-buoi3-66546989b4-dg86c` | `192.168.194.9` | `orbstack` | `ready=true`, `serving=true`, `terminating=false` |

EndpointSlice `nginx-buoi4-p6d8v` đã có port 80 và ba endpoint trên. Service vẫn giữ tên `nginx-buoi4`, nhãn riêng `app=nginx-buoi4` và IP `192.168.194.166`.

### HTTP qua Service

Request kiểm tra từ Mac qua Service IP trả:

```text
HTTP/1.1 200 OK
Content-Type: text/html
```

Nội dung trang có `Welcome to nginx!`. Response được ghi nhận lúc **2026-10-07 10:40:59, giờ Việt Nam**.

**Kết luận đã kiểm chứng:** Service có đúng ba backend Ready và một request qua Service thành công. Không suy ra rằng đã đo phân phối request tới từng Pod hoặc kiểm thử không gián đoạn khi Pod bị xóa.

Truy cập trực tiếp Pod/Service IP từ Mac trong bài dùng hỗ trợ networking của OrbStack. Không mặc định rằng mọi cluster Kubernetes đều cho phép host bên ngoài truy cập ClusterIP trực tiếp. Chi tiết các loại Service và truy cập từ Mac thuộc buổi 5–6.

## 6. Pod IP đổi thì vì sao không phải sửa Service?

Cấu hình Service trong bài không liệt kê từng Pod IP; nó khai báo điều kiện label cần khớp.

Nếu một Pod thay thế có IP mới nhưng vẫn mang label phù hợp, Kubernetes cập nhật danh sách địa chỉ đích trong EndpointSlice. Với cấu hình lab này, Pod đủ điều kiện nhận traffic khi Ready. Client không phải sửa cấu hình Service theo IP mới của từng Pod.

Điều kiện quan trọng là **Pod mới còn khớp selector**, không phải nó có cùng tên hoặc IP với Pod bị xóa.

Đây là câu hỏi đã review về lý thuyết. Trong buổi 4 chưa xóa Pod để kiểm thử lại luồng HTTP sau thay thế.

## 7. Đổi nhãn Deployment rồi tạo lại Pod thì sao?

Tình huống đã hỏi và giải thích:

> Chỉ đổi `Deployment.metadata.labels` thành `app=khac`, không đổi template hoặc nhãn Pod. Sau đó giả sử xóa cả ba Pod để ReplicaSet tạo lại: Pod mới có thành `app=khac` không?

**Không.** ReplicaSet tạo Pod từ `.spec.template` của nó, không lấy nhãn từ `Deployment.metadata.labels`.

Các field minh họa trong tình huống giả định, không phải manifest để apply:

```yaml
metadata:
  labels:
    app: khac
spec:
  template:
    metadata:
      labels:
        app: nginx-buoi3
```

Chỉ nhãn của chính Deployment đổi. Mẫu Pod của Deployment và ReplicaSet tương ứng vẫn giữ `app=nginx-buoi3`.

Đã đọc template thực tế của ReplicaSet `nginx-buoi3-66546989b4`:

```yaml
spec:
  template:
    metadata:
      labels:
        app: nginx-buoi3
        pod-template-hash: "66546989b4"
```

Nếu thiếu replicas, ReplicaSet controller tạo Pod từ mẫu này. Do đó Pod mới vẫn có `app=nginx-buoi3` và Service vẫn khớp khi các Pod sẵn sàng.

**Cách nhớ:** `Deployment.metadata.labels` là “nhãn của resource Deployment”; `Deployment.spec.template.metadata.labels` là “nhãn trong công thức tạo Pod”. Hai field có thể cùng giá trị trong lab nhưng không phải một field và không tự đồng bộ khi chỉ sửa nhãn ngoài cùng.

Không thực hiện thay đổi hoặc xóa hàng loạt để chứng minh tình huống trên. Nếu xóa cả ba Pod, có thể có khoảng thời gian không có backend Ready; selector giữ nguyên không bảo đảm ứng dụng luôn phục vụ được trong thời gian tạo lại.

## 8. Lệnh tham khảo sau buổi học

Tên và địa chỉ trong tài liệu là snapshot đã ghi nhận, không cần học thuộc. Các lệnh có context `orbstack`, namespace `default`; lệnh create/patch ở trên thay đổi cluster và không cần chạy lại để được tính hoàn thành.

### Xem Pod, nhãn, Service và backend — chỉ đọc

```bash
kubectl --context=orbstack -n default get pods -l app=nginx-buoi3 -o wide --show-labels
kubectl --context=orbstack -n default describe service nginx-buoi4
kubectl --context=orbstack -n default get endpointslices -l kubernetes.io/service-name=nginx-buoi4
kubectl --context=orbstack -n default get endpointslices -l kubernetes.io/service-name=nginx-buoi4 -o yaml
```

- `--show-labels` hiện nhãn trên resource.
- `-l` lọc theo label; ở lệnh EndpointSlice, nhãn `kubernetes.io/service-name` xác định các slice của Service cần xem.
- `-o wide` bổ sung IP và node cho bảng Pod.
- YAML của EndpointSlice cho phép xem `addresses`, `conditions.ready` và `targetRef` để đối chiếu Pod đích, không chỉ đếm số slice.

### Đối chiếu nhãn Deployment và Pod template — chỉ đọc

```bash
kubectl --context=orbstack -n default get deployment nginx-buoi3 -o yaml
kubectl --context=orbstack -n default get rs -l app=nginx-buoi3 -o yaml
```

Đọc riêng `.metadata.labels` và `.spec.template.metadata.labels`; không coi hai nhóm nhãn là một chỉ vì cùng có key `app` và cùng value trong snapshot.

### Kiểm tra HTTP qua Service từ Mac trên OrbStack

```bash
SERVICE_IP=$(kubectl --context=orbstack -n default get service nginx-buoi4 -o jsonpath='{.spec.clusterIP}')
curl --max-time 5 -i "http://${SERVICE_IP}/"
```

Đây là GET kiểm tra ứng dụng, không phải thao tác sửa cấu hình Kubernetes. Lệnh lấy IP từ Service đang tồn tại thay vì yêu cầu nhớ địa chỉ đã ghi trong snapshot.

## 9. Các nhầm lẫn đã được sửa

| Nhầm lẫn / điểm chưa rõ | Cách hiểu đúng |
|---|---|
| Pod Running thì Service phải có backend. | Pod vẫn có thể không khớp selector. Phải đọc label, selector và endpoint. |
| Có một EndpointSlice nghĩa là có một Pod đích. | Slice có thể rỗng; phải xem địa chỉ endpoint và điều kiện Ready. |
| `Labels` và `Selector` trong describe Service là cùng vai trò. | `Labels` gắn trên chính Service; `Selector` là điều kiện chọn Pod. |
| Service và Deployment phải cùng tên. | Service chọn theo nhãn Pod trong cùng namespace, không theo tên Deployment. |
| Service chọn Pod dựa vào nhãn của Deployment. | Field được đối chiếu trực tiếp là `Pod.metadata.labels`. |
| Pod IP đổi thì phải khai báo lại IP trong Service. | Kubernetes cập nhật backend; cấu hình selector không cần liệt kê IP từng Pod. |
| Đổi `Deployment.metadata.labels` thì Pod tạo lại sẽ lấy nhãn đó. | Pod được tạo từ template của ReplicaSet; nhãn ngoài cùng của Deployment không tự thay đổi Pod template. |

## 10. Câu hỏi đã review và liên hệ Data Engineering

1. **Service ban đầu tìm nhãn nào, các Pod có đáp ứng không?** Tìm `app=nginx-buoi4`; các Pod mang `app=nginx-buoi3`, nên không khớp.
2. **Giữ nguyên Pod, nên sửa gì?** Đổi selector của Service thành `app=nginx-buoi3`, không đổi tên hoặc tạo lại workload.
3. **Service và Deployment khác tên có cản trở chọn Pod không?** Không; cần selector khớp label của Pod trong cùng namespace.
4. **Pod mới có IP khác nhưng label phù hợp thì phải sửa Service không?** Không phải sửa IP trong cấu hình Service; Kubernetes cập nhật EndpointSlice.
5. **Chỉ đổi nhãn ngoài cùng của Deployment, Pod hiện có còn được chọn không?** Có, nếu label của Pod và selector Service giữ nguyên.
6. **Trong tình huống đó, Pod tạo lại có mang `app=khac` không?** Không; template ReplicaSet vẫn mang `app=nginx-buoi3`. Đây là phần thắc mắc đã được giải đáp bằng đọc template và giải thích, không phải thí nghiệm xóa ba Pod.

Sau này, khi Spark Worker không kết nối được Spark Master dù Pod Master Running, hoặc một client không gọi được component của data platform, cần tách **ứng dụng chạy** khỏi **Service chọn đúng backend**. Các bước đọc label, selector và EndpointSlice giúp điều tra lớp lựa chọn này trước khi kết luận ứng dụng bị lỗi.

Không triển khai thêm Spark, storage hoặc component data platform trong buổi 4.

**Kết quả: Buổi 04 đạt sau thực hành và review.** Ghi nhớ nguồn nhãn và điều kiện lựa chọn, không học thuộc tên sinh tự động hoặc IP.

**Tiếp theo:** [Buổi 05 — Service](../roadmap/buoi-hoc/05-service.md), đang bắt đầu; dùng lại Service đã sửa để học endpoint ổn định và các loại Service. Chưa có minh chứng thực hành client Pod nội bộ hoặc review đủ buổi 5.

## Tài liệu tham khảo

- [Kubernetes — Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/): nhãn và lựa chọn resource.
- [Kubernetes — Service](https://kubernetes.io/docs/concepts/services-networking/service/): selector, Pod đích và endpoint của Service.
- [Kubernetes — ReplicaSet: Pod template](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/#pod-template): mẫu dùng khi tạo Pod mới.
- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/): Deployment và Pod template.
- [OrbStack — Kubernetes](https://docs.orbstack.dev/kubernetes/): hỗ trợ truy cập mạng cluster từ Mac.
- [Hội thoại thực hành và review](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f): nguồn output học viên, kiểm tra API/HTTP và các câu hỏi đã giải đáp.
