# Sau buổi 05 — Service, endpoint ổn định và các cổng truy cập

**Ngày học và hoàn thành review:** 2026-10-07, giờ Việt Nam.

[Challenge gốc](../roadmap/buoi-hoc/05-service.md) · [Tiến độ học tập](../roadmap/tien-do-hoc-tap.md) · [Hội thoại và minh chứng](https://ampcode.com/threads/T-01a1149b-42ee-7429-a039-a101af378367)

Tài liệu tổng kết phần đã thực hành và review. Không cần học thuộc tên Pod, địa chỉ IP hoặc boilerplate YAML. Bài dùng lại Service đã sửa ở [Buổi 04](04-labels-va-selectors.md), không tạo Service khác chỉ để lặp lại bài cũ.

> **Điểm cốt lõi:** Client gọi endpoint của Service thay vì lưu IP từng Pod. Khi Pod được thay thế, Kubernetes cập nhật backend; Service giữ endpoint trong vòng đời của nó. `port` là cổng client gọi trên Service, `targetPort` là cổng ứng dụng trên Pod đích, còn `nodePort` là đường vào qua Node IP khi được cấu hình.

## 1. Phạm vi thực hành và mức độ minh chứng

| Phần | Kết quả và nguồn minh chứng |
|---|---|
| Workload | Dùng Deployment `nginx-buoi3`, ba Pod nginx, Service `nginx-buoi4`; context `orbstack`, namespace `default`. |
| Request từ client Pod | Học viên gửi output `HTTP/1.1 200 OK`, trang `Welcome to nginx!`, rồi `pod "curl-buoi5" deleted`. |
| Thay thế một Pod | API chỉ đọc xác nhận Pod cũ biến mất, Pod mới có tên/UID/IP khác, cùng owner ReplicaSet; Deployment trở về `READY=3/3`. |
| Endpoint ổn định | Đối chiếu trước/sau thấy Service giữ nguyên tên, UID, ClusterIP; EndpointSlice bỏ backend cũ và thêm đúng Pod mới Ready. |
| HTTP sau thay thế | Học viên xác nhận kết quả trả về đúng như lần trước, tức HTTP 200 và trang nginx. Không gửi lại raw output; mentor ghi nhận xác nhận này, không yêu cầu chạy lại. |
| `port`, `targetPort`, `nodePort` | Review bằng tình huống giả định có các cổng khác nhau; không thay cấu hình thật sang 8080 hoặc 9000. |
| ClusterIP / NodePort / LoadBalancer | ClusterIP có thực hành; NodePort và LoadBalancer được giải thích/review, chưa triển khai thử. |

**Giới hạn:** Không đo traffic tới từng backend, không kiểm thử liên tục trong lúc xóa Pod, không chứng minh mọi request đều thành công hoặc chia đều giữa ba Pod. Chưa thực hành NodePort, LoadBalancer, Ingress hay browser trên Mac. Mentor chỉ inspect cluster, không xóa Pod hoặc triển khai client thay học viên.

## 2. Client chạy ở đâu và tên Service được dùng thế nào?

Lệnh đã thực hành:

```bash
kubectl --context=orbstack -n default run curl-buoi5 \
  --image=curlimages/curl:latest \
  --restart=Never --rm -i \
  --command -- curl -sS -i --max-time 10 http://nginx-buoi4
```

- `kubectl` được gõ trên Mac, nhưng tiến trình `curl` chạy trong container của Pod `curl-buoi5`.
- `--restart=Never` không tự restart container client sau khi kết thúc.
- `--rm` dọn Pod client sau lần chạy; không xóa các Pod nginx.
- `curl -i` hiện HTTP headers. `--max-time 10` giới hạn thời gian request curl, không phải toàn bộ thời gian tạo Pod hoặc pull image.
- `nginx-buoi4` trong URL là tên Service, không phải tên Deployment hoặc một Pod nginx.

Client và Service cùng namespace `default`, nên client có thể dùng tên ngắn này. Với Service ClusterIP thông thường trong bài, DNS phân giải tên Service thành **ClusterIP**, không thành danh sách ba Pod IP.

```text
DNS trong cluster: nginx-buoi4 → 192.168.194.166
```

Luồng truy cập ở mức mental model:

```diagram
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Client Pod       │────→│ Service          │────→│ 1 nginx Pod      │
│ curl-buoi5       │     │ nginx-buoi4:80   │     │ trong 3 backend  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

**DNS giúp tìm địa chỉ Service; cơ chế networking của Service chuyển kết nối tới backend.** Không coi DNS là bộ chọn Pod cho Service ClusterIP này. Không cần đi sâu CNI hoặc kube-proxy internals trong buổi 5.

Output học viên gửi trước thử nghiệm có:

```text
HTTP/1.1 200 OK
Date: Wed, 07 Oct 2026 04:33:24 GMT
Content-Type: text/html
```

Nội dung có `Welcome to nginx!`; thời gian trong header tương ứng **11:33:24 ngày 2026-10-07, giờ Việt Nam**. Đây là thời gian của response đã gửi, không phải timestamp của request sau thay thế Pod.

## 3. Pod thay thế nhưng endpoint client không đổi

Học viên được giao xóa đúng một Pod nginx, giữ nguyên Service và Deployment. Lệnh lịch sử, không cần chạy lại vì Pod này không còn:

```bash
kubectl --context=orbstack -n default delete pod nginx-buoi3-66546989b4-6gncw
```

### Đối chiếu trước/sau

| Thành phần | Trước thay thế | Sau thay thế |
|---|---|---|
| Pod được chọn để xóa | `nginx-buoi3-66546989b4-6gncw`, IP `192.168.194.7` | Không còn |
| Pod thay thế | Chưa có | `nginx-buoi3-66546989b4-bzts7`, IP `192.168.194.11`, Ready |
| Hai Pod còn lại | `...-mpszf` ở `.8`, `...-dg86c` ở `.9` | Giữ nguyên |
| ReplicaSet owner | `nginx-buoi3-66546989b4` | Pod mới thuộc cùng ReplicaSet |
| Deployment | Desired replicas 3 | `READY=3/3` sau khi ổn định |
| Service | `nginx-buoi4`, IP `192.168.194.166` | Cùng tên, IP và UID |
| Backend trong EndpointSlice | `.7`, `.8`, `.9` | `.8`, `.9`, `.11`, đều Ready |

Kiểm tra API lúc **13:51:34 giờ Việt Nam** đối chiếu UID để phân biệt Pod mới với restart container trong Pod cũ:

- UID Pod cũ: `a7adbab0-35ce-4343-a096-75da2b838bf0`.
- UID Pod mới: `768e25e4-617c-49f6-81ad-3de1057f6b51`.
- Service giữ UID `b7171c2c-b59d-4ca1-818d-9b16fb0fec41`.
- EndpointSlice `nginx-buoi4-p6d8v` có `targetRef` khớp tên/UID Pod mới ở `.11`, `ready=true`, không còn backend `.7`.

Khi chốt buổi lúc **14:57 giờ Việt Nam**, kiểm tra chỉ đọc vẫn thấy ba Pod Ready, Deployment `3/3`, đúng ba backend và Service ClusterIP có `port=80`, `targetPort=80`.

**HTTP sau thay thế:** Học viên xác nhận kết quả giống lần trước. Bản tổng kết ghi nhận HTTP 200/trang nginx theo xác nhận của học viên, không trình bày như một output lần hai đã được lưu hoặc một request do mentor kiểm tra độc lập.

### Ai làm việc gì?

| Thành phần | Trách nhiệm liên quan |
|---|---|
| Deployment | Khai báo desired state của workload, gồm replicas và Pod template; quản lý ReplicaSet. |
| ReplicaSet controller | Tạo Pod bù để đáp ứng số replicas, không phải Service tạo Pod. |
| Service | Giữ endpoint và điều kiện chọn nhóm Pod theo label. |
| EndpointSlice | Ghi địa chỉ/backend và điều kiện liên quan; Kubernetes cập nhật khi nhóm Pod đích thay đổi. |
| DNS | Phân giải tên Service thành ClusterIP trong bài này. |

Service không liệt kê từng Pod IP trong selector. Pod mới có label phù hợp thì backend được cập nhật; client vẫn dùng `http://nginx-buoi4`.

### "Ổn định" không có nghĩa là gì?

- Service IP ổn định trong vòng đời Service, không bảo đảm cùng IP nếu xóa rồi tạo lại Service.
- Pod thay thế không bắt buộc được cấp một IP khác trong mọi môi trường; `.7 → .11` là kết quả quan sát của lần thử này.
- Service vẫn tồn tại không đồng nghĩa luôn có backend Ready. Nếu không có backend phục vụ được, endpoint ổn định không tự tạo ra ứng dụng để trả response.
- Kết quả GET sau thay thế không chứng minh không gián đoạn trong lúc xóa hoặc một kết nối đang mở luôn được giữ nguyên.
- Service cung cấp networking, không lưu dữ liệu ứng dụng hoặc bảo đảm persistence.

## 4. Các field cần hiểu, không cần thuộc boilerplate

| Field | Ý nghĩa |
|---|---|
| `metadata.name` | Tên Service; client trong cluster có thể dùng cho service discovery. |
| `spec.type` | Kiểu đường truy cập: ClusterIP, NodePort hoặc LoadBalancer trong phạm vi buổi học. |
| `spec.clusterIP` | IP endpoint nội bộ của Service; trong lab được cluster cấp. |
| `spec.selector` | Điều kiện đối chiếu label Pod trong cùng namespace, không phải tên Deployment. |
| `spec.ports[].port` | Cổng client gọi trên Service IP. |
| `spec.ports[].targetPort` | Cổng ứng dụng trên Pod đích mà traffic được chuyển tới. |
| `spec.ports[].nodePort` | Cổng trên Node IP khi đường truy cập NodePort được cấu hình. Service ClusterIP hiện tại không có field này. |

Manifest tham khảo phản ánh cấu hình lab, lược các field do API server quản lý; không yêu cầu apply lại:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-buoi4
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: nginx-buoi3
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

## 5. `port` và `targetPort` không bắt buộc giống nhau

Tình huống đã review: nginx vẫn lắng nghe cổng 80, nhưng muốn client gọi `http://nginx-buoi4:8080`.

Cặp field cần có là **`port=8080`, `targetPort=80`**:

```diagram
┌────────┐     ┌───────────────┐     ┌─────────────┐
│ Client │────→│ Service :8080 │────→│ nginx :80   │
└────────┘     └───────────────┘     └─────────────┘
                     port              targetPort
```

Học viên chọn đúng `port=8080` nhưng chưa nêu `targetPort`; mentor bổ sung cổng đích 80. Học viên giải thích đúng ý chính rằng đặt cả hai bằng 8080 sẽ không thành công khi nginx chỉ lắng nghe cổng 80.

**Service không tự làm nginx mở cổng.** Chỉ đổi `targetPort` không đổi cấu hình lắng nghe của ứng dụng. Nếu trỏ tới cổng không có ứng dụng phục vụ, request không đến được nginx như mong muốn; không mặc định đây là một HTTP 404 do nginx trả về.

Đây là tình huống giả định. Cấu hình Service thật khi chốt buổi vẫn là `80 → 80`; chưa thử request qua cổng 8080.

## 6. ClusterIP, NodePort và LoadBalancer

| Loại | Đường truy cập ở mức khái niệm | Khi phù hợp / trade-off |
|---|---|---|
| ClusterIP | Endpoint nội bộ `ServiceIP:port`, hoặc tên Service trong cluster. | Phù hợp app-to-app; không tự tạo entrypoint bên ngoài bằng NodePort hoặc external load balancer. |
| NodePort | Giữ endpoint nội bộ, thêm đường vào `NodeIP:nodePort`. | Không cần một external load balancer để dùng đường vào này, nhưng client phải truy cập được Node IP và cổng đó; vẫn phụ thuộc routing/firewall và cấu hình mạng. |
| LoadBalancer | Endpoint do một triển khai load balancer cung cấp. | Cần môi trường/controller hỗ trợ; địa chỉ có thể private hoặc public, không tự bảo đảm có IP public chỉ từ field `type`. |

### Vì sao chọn ClusterIP cho Spark Worker gọi Master?

Hai component ở trong cluster, cần endpoint ổn định cho giao tiếp nội bộ. ClusterIP đáp ứng mục tiêu mà không thêm đường expose ngoài không cần thiết. Đây là lựa chọn học viên đã trả lời đúng; chưa triển khai Spark trong buổi này.

### Vì sao client ngoài gọi `nodePort`, không gọi `port` trên Node IP?

Ví dụ giả định:

```text
port       = 8080
targetPort = 80
nodePort   = 30080
```

`8080` gắn với Service IP; `30080` là đường truy cập được cấu hình trên Node IP. Hai đường vào cùng nhóm backend:

```diagram
Client ngoài ──→ NodeIP:30080 ──┐
                   nodePort     │   ┌─────────────────┐
                                ├──→│ PodIP:80        │
Client trong ──→ ServiceIP:8080─┘   │ targetPort      │
                     port           └─────────────────┘
```

Sơ đồ là hai lựa chọn đường truy cập, không phải một chuỗi request bắt buộc đi qua đủ ba cổng. Học viên chọn đúng 30080, ban đầu chưa rõ lý do; mentor giải thích bằng sự khác nhau giữa địa chỉ Node IP và Service IP.

### Vì sao LoadBalancer cần hỗ trợ của môi trường?

`type=LoadBalancer` khai báo yêu cầu. Cần một thành phần xử lý yêu cầu đó để cấp/configure load balancer, như tích hợp cloud hoặc triển khai phù hợp cho local/on-premises. Chỉ đổi YAML không tự tạo ra hạ tầng hay một địa chỉ public có thể truy cập được.

Ngay cả khi có triển khai hỗ trợ, endpoint có thể là private. Học viên trả lời đúng "không bảo đảm IP public" nhưng ban đầu chưa rõ lý do; mentor bổ sung sự khác nhau giữa yêu cầu trong API và thành phần thực hiện nó.

**ClusterIP và NodePort vẫn có thể phân phối kết nối tới các backend.** Loại LoadBalancer bổ sung endpoint qua một load balancer bên ngoài, không phải chỉ loại này mới có khả năng đưa traffic tới nhiều Pod.

Mac truy cập được ClusterIP trong phần thực hành trước nhờ hỗ trợ mạng của OrbStack. Không suy ra mọi cluster đều cho host ngoài truy cập trực tiếp ClusterIP, hoặc NodePort luôn dùng được qua `localhost` trên Mac. Phần truy cập browser/host sẽ học ở buổi 6.

## 7. Câu hỏi cuối: ứng dụng đổi cổng nhưng client giữ endpoint

Giả sử vẫn có NodePort với `port=8080`, `nodePort=30080`, nhưng nginx **đã thực sự được cấu hình lắng nghe cổng 9000**.

Muốn client ngoài vẫn gọi `NodeIP:30080`, sửa **`targetPort=9000`**, giữ `port=8080` và `nodePort=30080`.

Học viên trả lời đúng sửa `targetPort` sang 9000. Điều kiện cần nhớ là ứng dụng đã nghe cổng mới; sửa Service không tự làm nginx chuyển sang cổng 9000. Đây chỉ là scenario review, không triển khai NodePort hoặc thay cổng nginx thật.

## 8. Lệnh tham khảo và cách quan sát

Không cần chạy lại lab để được tính hoàn thành. Tên/IP trong tài liệu là snapshot, không phải những giá trị cần học thuộc.

### Inspect — chỉ đọc

```bash
kubectl --context=orbstack -n default get deployment nginx-buoi3
kubectl --context=orbstack -n default get pods -l app=nginx-buoi3 -o wide
kubectl --context=orbstack -n default get service nginx-buoi4 -o wide
kubectl --context=orbstack -n default get endpointslices \
  -l kubernetes.io/service-name=nginx-buoi4 -o wide
kubectl --context=orbstack -n default get endpointslices \
  -l kubernetes.io/service-name=nginx-buoi4 -o yaml
```

- Pod output cho thấy tên, IP, Ready và node.
- Service output cho thấy type, ClusterIP, port và selector.
- EndpointSlice YAML cho phép đối chiếu `addresses`, `conditions.ready`, `targetRef.name` và `targetRef.uid`; không chỉ đếm số slice.
- Readiness/backend đúng hỗ trợ điều tra, nhưng không thay thế kiểm tra HTTP của ứng dụng.

### Tra field qua API schema — chỉ đọc

```bash
kubectl --context=orbstack explain service.spec.ports.port
kubectl --context=orbstack explain service.spec.ports.targetPort
```

Mentor đã dùng hai lệnh explain này để đối chiếu định nghĩa field. Nếu không khai báo `targetPort`, API dùng giá trị `port`; vì vậy với ứng dụng chỉ nghe 80 và Service port 8080 cần khai báo cổng đích phù hợp, không trông chờ Kubernetes đoán cổng ứng dụng.

## 9. Các điểm cần nhớ và liên hệ Data Engineering

- **Endpoint ổn định khác backend ổn định:** client không nên lưu IP từng Pod của một nhóm workload có thể được thay thế.
- **Service khác controller quản lý workload:** Service không tạo Pod bù; ReplicaSet controller làm việc đó trong lab này.
- **Tên/IP phải đi cùng cổng đúng:** `NodeIP:30080` và `ServiceIP:8080` không phải cùng một địa chỉ, dù dẫn tới cùng nhóm backend.
- **Cấu hình API khác hạ tầng được cung cấp:** LoadBalancer cần triển khai hỗ trợ; YAML không tự tạo khả năng truy cập public.
- **Networking khác storage:** endpoint Service không giữ dữ liệu PostgreSQL hoặc MinIO sau thay thế Pod; persistence thuộc các buổi storage sau.
- Với data platform, Spark Worker gọi Master hoặc client nội bộ gọi MinIO nên dùng service discovery phù hợp. Browser trên Mac truy cập UI là bài toán đường vào khác, không mặc định dùng y nguyên tên DNS nội bộ.

Nên ôn lại lý do NodePort dùng Node IP/cổng riêng và vì sao LoadBalancer phụ thuộc triển khai hỗ trợ. Đây là phần ban đầu học viên chọn đúng đáp án nhưng chưa rõ lý do, đã được giải thích trong review.

**Kết quả: Buổi 05 đạt sau thực hành và review.** HTTP ban đầu có output trực tiếp; HTTP sau thay thế được ghi nhận theo xác nhận học viên. Không bổ sung thực hành giả định vào kết quả.

**Tiếp theo:** [Buổi 06 — Truy cập từ macOS](../roadmap/buoi-hoc/06-truy-cap-tu-macos.md), chưa bắt đầu. Sẽ học browser trên Mac → Service / Ingress → nginx Pod.

## Tài liệu tham khảo

- [Kubernetes — Service](https://kubernetes.io/docs/concepts/services-networking/service/): port mapping và các loại Service.
- [Kubernetes — DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/): tên Service, namespace và ClusterIP.
- [Kubernetes — EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/): backend và điều kiện endpoint.
- [Kubernetes — ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/): duy trì số replicas và tạo Pod bù.
- [OrbStack — Kubernetes](https://docs.orbstack.dev/kubernetes/): đặc điểm môi trường local.
- [Hội thoại Buổi 05](https://ampcode.com/threads/T-01a1149b-42ee-7429-a039-a101af378367): output, snapshot API, xác nhận học viên và câu hỏi review.
