# Theo dõi tiến độ học Kubernetes cho Data Engineer

[Mục lục lộ trình](kubernetes_data_engineer_training_roadmap.md) · [Quy tắc học và mentor](huong-dan-hoc-va-mentor.md)

## Tổng quan

- **Ngày bắt đầu:** 2026-10-06
- **Buổi đang học:** Chờ bắt đầu Buổi 07 — Debugging Challenge #1. Buổi 06 hoàn thành thực hành và review ngày 2026-10-09: HTTP qua Ingress đúng/sai host đạt, học viên xác nhận browser thấy trang nginx; đã lưu [tổng kết](../after-study/06-truy-cap-tu-macos.md). Chưa bắt đầu challenge Buổi 07.
- **Tiến độ:** 6/28 buổi hoàn thành — cập nhật sau review theo checklist bên dưới.
- **Ngày hoàn thành khóa:** —

## Cách cập nhật

1. Trước khi học, điền **Buổi đang học**, đổi trạng thái buổi đó thành `Đang học` và ghi ngày học dạng `YYYY-MM-DD`.
2. Nếu chưa giải quyết được lỗi, dùng `Bị kẹt`, ghi symptom và những gì đã thử vào phần lỗi còn vướng.
3. Chỉ đổi `- [ ]` thành `- [x]` và đặt `Hoàn thành` khi đã làm được challenge, giải thích được concept/câu hỏi trọng tâm và có kết quả review.
4. Ghi minh chứng: đường dẫn manifest/script, output đã lược bỏ dữ liệu nhạy cảm, ảnh hoặc ghi chú kết quả kiểm tra. Không lưu password, token hay nội dung Secret vào file này.
5. Sau mỗi buổi review đạt, mentor tự cập nhật tổng số buổi hoàn thành, **Buổi đang học**, nhật ký và tạo/cập nhật bản tổng kết trong `after-study/`, không đợi học viên nhắc. Thêm link tổng kết vào minh chứng. Không tính checklist nghiệm thu cuối khóa vào tổng 28 buổi.

Trạng thái dùng thống nhất: `Chưa học` · `Đang học` · `Bị kẹt` · `Cần ôn` · `Hoàn thành`.

Nếu cần học lại, bỏ dấu `[x]`, đặt `Cần ôn` và cập nhật tổng tiến độ. Nếu một buổi kéo dài nhiều ngày, ghi các lần học trong nhật ký; không cần ép hoàn thành trong một ngày.

## Tuần 1 — Kubernetes từ con số 0

**Mốc cần đạt:** Deploy, expose và debug được workload cơ bản.

- [x] **[Buổi 01 — Kubernetes cluster đầu tiên](buoi-hoc/01-cluster-dau-tien.md)** — Cluster hoạt động; quan sát được context, node, namespace và Pod hệ thống; giải thích được vai trò Control Plane và kubectl.
  - **Trạng thái:** Hoàn thành · **Ngày học:** 2026-10-06 · **Minh chứng/ghi chú:** Context `orbstack`; một node `Ready`; CoreDNS và Local Path Provisioner đều `Running`, `READY=1/1`, `RESTARTS=0`. Đã review namespace và tình huống Pod chạy trên `node-b`, không phụ thuộc phiên Terminal. Chi tiết trong nhật ký và [hội thoại review](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f).
- [x] **[Buổi 02 — Pod đầu tiên](buoi-hoc/02-pod-dau-tien.md)** — Tạo, inspect và xóa nginx Pod; giải thích vì sao Pod đơn lẻ không tự được tạo lại.
  - **Trạng thái:** Hoàn thành · **Ngày học:** 2026-10-06 · **Minh chứng/ghi chú:** `nginx-buoi2` trong `default` đạt `Running`, `READY=1/1`, `RESTARTS=0`; Pod IP `192.168.194.5`, node `orbstack`. Đã xem logs và Events khởi động; sau khi xóa, kiểm tra chỉ đọc xác nhận Pod không còn. Đã review khác biệt restart container và tạo lại Pod. Chi tiết trong nhật ký và [hội thoại review](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f).
- [x] **[Buổi 03 — Deployment](buoi-hoc/03-deployment.md)** — Có 3 replicas; xóa một Pod và quan sát Pod thay thế; giải thích Deployment, ReplicaSet và desired state.
  - **Trạng thái:** Hoàn thành · **Ngày học:** 2026-10-07 · **Minh chứng/ghi chú:** Bắt đầu challenge ngày 2026-10-06, hoàn thành thực hành/review ngày 2026-10-07. Deployment `nginx-buoi3` đạt `READY=3/3`; xóa một Pod, ReplicaSet tạo Pod mới và trở về `DESIRED=CURRENT=READY=3`. Đã review đúng cấp cấu hình Deployment `.spec.replicas` và phân biệt restart container với tạo Pod bù. Xem [tổng kết sau buổi học](../after-study/03-deployment.md) và nhật ký bên dưới.
- [x] **[Buổi 04 — Labels và Selectors](buoi-hoc/04-labels-va-selectors.md)** — Tìm và sửa selector sai dựa trên label; giải thích cách Service chọn Pod.
  - **Trạng thái:** Hoàn thành · **Ngày học:** 2026-10-07 · **Minh chứng/ghi chú:** Service `nginx-buoi4` ban đầu chọn `app=nginx-buoi4`, không khớp các Pod `app=nginx-buoi3`; EndpointSlice rỗng. Sau sửa selector, API ghi nhận đúng ba backend Ready và HTTP qua Service IP `192.168.194.166` trả 200. Đã review tên resource, nhãn Pod, selector và nhãn trong Pod template; đổi nhãn ngoài cùng Deployment không tự đổi nhãn Pod tạo lại. Xem [tổng kết sau buổi học](../after-study/04-labels-va-selectors.md) và nhật ký bên dưới.
- [x] **[Buổi 05 — Service](buoi-hoc/05-service.md)** — Gọi nginx qua Service thay vì Pod IP; phân biệt ClusterIP, NodePort và LoadBalancer.
  - **Trạng thái:** Hoàn thành · **Ngày học:** 2026-10-07 · **Minh chứng/ghi chú:** Client Pod gọi tên Service nhận HTTP 200; API xác nhận Pod thay thế, backend đã cập nhật, Service giữ nguyên UID/IP. Học viên xác nhận HTTP sau thay thế giống lần trước, không gửi lại raw output. Đã review endpoint ổn định, vai trò ReplicaSet, các cổng và ba loại Service; trả lời đúng sửa targetPort khi ứng dụng đổi cổng. NodePort/LoadBalancer và cổng 8080/9000 chỉ là tình huống review, chưa triển khai. Xem [tổng kết sau buổi học](../after-study/05-service.md) và [hội thoại Buổi 05](https://ampcode.com/threads/T-01a1149b-42ee-7429-a039-a101af378367).
- [x] **[Buổi 06 — Truy cập từ macOS](buoi-hoc/06-truy-cap-tu-macos.md)** — Browser trên Mac truy cập được nginx; giải thích luồng traffic từ host tới Pod.
  - **Trạng thái:** Hoàn thành · **Ngày học:** 2026-10-09 · **Minh chứng/ghi chú:** Bắt đầu ngày 2026-10-07, chốt ngày 2026-10-09. Browser qua ClusterIP và hostname Ingress theo xác nhận học viên. Curl `http://k8s.orb.local:8080` trả 200; Ingress `nginx-buoi6` theo [manifest](../nginx-buoi6-ingress.yaml) dùng class `traefik`, backend `nginx-buoi4:8080`, Pod cổng 80. Output curl host đúng trả 200/trang nginx, host sai trả 404; API chỉ đọc xác nhận cấu hình. Review đổi backend port/URL frontend, DNS/HTTP Host và LB pending đạt ý chính; mentor bổ sung cấu hình ngoài lab. Cloud/MetalLB, DNS ngoài lab và truy cập LAN/Internet chưa thực hành. Xem [tổng kết sau buổi học](../after-study/06-truy-cap-tu-macos.md) và [hội thoại Buổi 06](https://ampcode.com/threads/T-01a11575-bbd7-76d9-88ff-99613fd36c93).
- [ ] **[Buổi 07 — Debugging Challenge #1](buoi-hoc/07-debugging-1.md)** — Tự điều tra và sửa lỗi được giao bằng status, describe, logs và events; đạt tiêu chí cuối tuần 1.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —

## Tuần 2 — Configuration, resources và storage

**Mốc cần đạt:** PostgreSQL chạy được và dữ liệu còn sau khi Pod bị tạo lại.

- [ ] **[Buổi 08 — ConfigMap](buoi-hoc/08-configmap.md)** — App nhận runtime config từ ConfigMap, không hard-code vào image; hiểu cách inject bằng env và mounted file.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 09 — Secret](buoi-hoc/09-secret.md)** — Inject credential bằng Secret; phân biệt với ConfigMap và giải thích giới hạn bảo mật của Secret.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 10 — CPU và Memory](buoi-hoc/10-cpu-va-memory.md)** — Thử request RAM cao, CPU limit thấp, memory limit thấp; giải thích Pending, OOMKilled, throttling và request vs limit.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 11 — Ephemeral filesystem và Volume](buoi-hoc/11-ephemeral-filesystem-va-volume.md)** — Ghi file rồi tạo lại Pod; quan sát dữ liệu mất và giải thích vì sao database cần persistence.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 12 — PV, PVC và StorageClass](buoi-hoc/12-pv-pvc-storageclass.md)** — Giải thích được luồng cấp storage 10 GiB, access modes, dynamic provisioning và reclaim behavior.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 13 — PostgreSQL](buoi-hoc/13-postgresql.md)** — Kết nối DB từ trong cluster; ghi dữ liệu, xóa Pod và kiểm tra dữ liệu vẫn còn sau khi Pod được tạo lại.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 14 — StatefulSet](buoi-hoc/14-statefulset.md)** — Đánh giá/chuyển PostgreSQL sang StatefulSet khi phù hợp; giải thích stable identity, storage association và lifecycle; đạt tiêu chí cuối tuần 2.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —

## Tuần 3 — Data Engineering workloads

**Mốc cần đạt:** Spark Standalone chạy job và ghi Parquet vào MinIO.

- [ ] **[Buổi 15 — MinIO](buoi-hoc/15-minio.md)** — MinIO có persistent storage, API và Console truy cập được; phân biệt endpoint nội bộ và endpoint từ Mac.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 16 — Spark Standalone](buoi-hoc/16-spark-standalone.md)** — Dựng 1 Master và 2 Workers; giải thích Worker tìm Master qua Service và khác Kubernetes Node thế nào.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 17 — Spark networking và UI](buoi-hoc/17-spark-networking-va-ui.md)** — Master UI từ Mac hiển thị 2 workers registered; phân biệt UI traffic và Master RPC.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 18 — Submit Spark application](buoi-hoc/18-submit-spark-application.md)** — PySpark application chạy được; xác định vị trí Driver và Executors, vai trò Master và Worker.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 19 — Hai tầng resource management](buoi-hoc/19-hai-tang-resource-management.md)** — Phân tích được case Pod limit 4 CPU/4 GiB nhưng Worker quảng bá 8 cores/8 GiB; phân biệt Kubernetes và Spark resource config.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 20 — Spark ghi dữ liệu vào MinIO](buoi-hoc/20-spark-ghi-du-lieu-vao-minio.md)** — Spark đọc input, transform và ghi Parquet thành công vào MinIO; giải thích endpoint, credential và object path.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 21 — Debugging Challenge #2](buoi-hoc/21-debugging-2.md)** — Điều tra và sửa lỗi Spark/MinIO/networking/resource được giao; đạt tiêu chí cuối tuần 3.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —

## Tuần 4 — Mini Lakehouse Platform

**Mốc cần đạt:** Airflow → Spark → Iceberg trên MinIO/Nessie → Trino query.

- [ ] **[Buổi 22 — Airflow](buoi-hoc/22-airflow.md)** — Deploy Airflow, truy cập UI từ Mac; giải thích Scheduler, Metadata Database và DAG.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 23 — Airflow trigger Spark](buoi-hoc/23-airflow-trigger-spark.md)** — DAG trigger Spark job chạy được; phân biệt orchestration với compute.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 24 — Apache Iceberg](buoi-hoc/24-apache-iceberg.md)** — Phân biệt compute engine, table format, object storage và catalog; giải thích vai trò data/metadata Iceberg.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 25 — Nessie](buoi-hoc/25-nessie.md)** — Giải thích vai trò catalog/versioning, namespace/table discovery và vị trí data, table metadata, catalog.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 26 — Trino](buoi-hoc/26-trino.md)** — Trino query thành công chính Iceberg table Spark đã tạo; kết quả khớp dữ liệu đã ghi.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 27 — Full Platform Debugging](buoi-hoc/27-full-platform-debugging.md)** — Debug từ symptom và sửa 3–5 lỗi do mentor tạo; ghi lại bằng chứng, nguyên nhân và cách kiểm tra sau sửa.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —
- [ ] **[Buổi 28 — Final Challenge](buoi-hoc/28-final-challenge.md)** — Tự dựng full platform từ requirement và chạy được flow end-to-end; đạt toàn bộ checklist nghiệm thu dưới đây.
  - **Trạng thái:** Chưa học · **Ngày học:** — · **Minh chứng/ghi chú:** —

## Nghiệm thu cuối khóa

Đối chiếu [Final Challenge](buoi-hoc/28-final-challenge.md), [Definition of Done](dinh-huong-va-muc-tieu.md) và [resource budget](kien-truc-va-mental-model.md).

- [ ] Đủ PostgreSQL, Airflow, Spark Standalone (1 Master + 2 Workers), MinIO, Iceberg, Nessie và Trino.
- [ ] Workload cần persistence có storage phù hợp; kiểm tra dữ liệu sau khi tạo lại Pod.
- [ ] Các service nội bộ dùng Kubernetes service discovery; các UI cần thiết truy cập được từ Mac.
- [ ] Tách runtime config/credential bằng ConfigMap/Secret khi phù hợp, không hard-code credential trong image.
- [ ] Requests/limits và Spark resource config hợp lý với máy 24 GB RAM / 10 cores.
- [ ] Airflow trigger Spark ghi Iceberg table trên MinIO với Nessie catalog; Trino query đúng dữ liệu đó.
- [ ] Giải thích được các quyết định Deployment/StatefulSet, storage, networking, config, resource và cách debug từ symptom.

## Lỗi còn vướng / nội dung cần ôn

Thêm một dòng khi bị kẹt hoặc cần ôn. Giữ lại dòng đã giải quyết để có lịch sử điều tra.

| Buổi | Symptom / câu hỏi | Đã thử và bằng chứng | Hướng điều tra tiếp / mức hint | Kết quả / ngày xử lý |
|---|---|---|---|---|
| 01 | Ban đầu chưa rõ vai trò hai Pod hệ thống và trách nhiệm khi tạo Pod. | Quan sát CoreDNS và Local Path Provisioner; sau giải thích đã trả lời đúng tình huống `node-b` và đóng Terminal. | Đã giải thích sau review; nên ôn chuỗi kubectl → API server → scheduler → kubelet/container runtime. | Đã xử lý qua review; Buổi 01 đạt ngày 2026-10-06. |
| 02 | Chưa rõ vì sao Pod bị xóa không xuất hiện lại và `restartPolicy: Always` đến từ đâu; mất output lần đầu. | Tạo lại Pod, gửi output get/logs/describe; kiểm tra client dry-run và help xác nhận mặc định của kubectl run; sau lần xóa cuối Pod không còn. | Hint 1: phân biệt restart container trong Pod còn tồn tại với tạo Pod mới; giải thích mặc định `--restart=Always` và vai trò controller. | Đã hiểu ý chính, đủ minh chứng và review đạt ngày 2026-10-06. |
| 03 | Chưa biết kiểm tra `DESIRED` ở đâu; ban đầu chọn chỉnh ReplicaSet để đổi số Pod của Deployment. | Đối chiếu output trước/sau khi xóa, cột `DESIRED=3`, ownerReferences và Event `SuccessfulCreate`; sau giải thích trả lời đúng chỉnh Deployment, field replicas thành 2. | Review quan hệ Deployment → ReplicaSet → Pod và phân biệt field với resource; không yêu cầu học thuộc tên Pod. | Đã xử lý và review đạt ngày 2026-10-07; chi tiết trong bản tổng kết. |
| 04 | Chưa biết đọc backend rỗng; nhầm nhãn của Deployment với nhãn Service đối chiếu; hỏi nhãn Pod tạo lại sau khi đổi nhãn ngoài cùng Deployment. | Output labels/describe/EndpointSlice cho thấy selector không khớp; học viên xác định cách sửa. API sau sửa có ba endpoint Ready, HTTP 200. Đọc template Deployment/ReplicaSet để giải đáp nguồn nhãn Pod mới. | Hint 4: đặt selector Service cạnh nhãn Pod; sau học viên đề xuất đúng mới cung cấp cú pháp patch. Giải thích phân biệt metadata.labels và spec.template.metadata.labels. | Đã xử lý và review đạt ngày 2026-10-07; đổi nhãn Deployment/xóa ba Pod chỉ là tình huống giả định, không thực hiện. |
| 05 | Ban đầu nêu port nhưng thiếu targetPort; chọn đúng NodePort 30080 và LoadBalancer không bảo đảm IP public nhưng chưa rõ lý do. | Mentor giải thích cổng gắn với Node IP / Service IP / Pod IP và triển khai hỗ trợ LoadBalancer. Học viên trả lời đúng targetPort=9000 khi nginx đã nghe 9000, giữ endpoint client. | Không có lỗi runtime được báo; có giải thích sau review. Nên ôn đường vào qua từng địa chỉ và phân biệt yêu cầu API với hạ tầng được cấp. | Review đạt ngày 2026-10-07; HTTP sau thay thế theo xác nhận học viên, không yêu cầu gửi lại output. |
| 06 | Ban đầu đề xuất `http://nginx-buoi4:80` cho browser trên Mac. | Kiểm tra DNS trên Mac lab không phân giải tên ngắn; tên đầy đủ `nginx-buoi4.default.svc.cluster.local` phân giải tới Service. Sau hint, học viên chọn ClusterIP/cổng 80 từ output và xác nhận browser truy cập được. | Phân biệt DNS trong Pod cùng namespace với DNS trên Mac; hint dùng địa chỉ ở cột CLUSTER-IP. Chưa có lỗi browser do học viên gửi cho URL tên ngắn. | Bước truy cập ClusterIP đạt ngày 2026-10-07; browser qua Ingress được học viên xác nhận và toàn Buổi 06 đạt ngày 2026-10-09. |
| 06 | Học viên chưa hiểu các ký hiệu ServiceIP, NodeIP, LB-IP sau phần so sánh Service types. | Học viên nhận diện đúng URL Service, endpoint ổn định và cặp Node IP/NodePort `192.168.139.2:32274`. Trong ví dụ LB có IP khác node, chọn đúng vai trò LB IP + Service.port=8080 nhưng viết `192.51.100.2` thay vì `198.51.100.20`. Đây là review lý thuyết, không có thao tác thay thế Pod mới hoặc HTTP qua NodePort/URL giả định. | Mentor đối chiếu URL ví dụ thành `http://198.51.100.20:8080`, nhắc Pod chạy trên node, không nằm trong Service/LB. Không yêu cầu học thuộc số IP hoặc lặp lại review chỉ để chép số; tại lần ôn này chưa triển khai Ingress. | Ngày 2026-10-08 review vai trò địa chỉ/cổng đạt; cần chú ý đọc đúng giá trị IP. Sau đó thực hành/review Ingress đạt, toàn buổi chốt ngày 2026-10-09. |
| 06 | Chưa rõ nguồn domain OrbStack, DNS có giải quyết LB pending không và cổng backend Ingress. | DNS local đã phân giải trước khi có rule; describe có Service:8080 và Pod:80; curl host đúng 200, host sai 404. Review cuối chọn đúng backend port mới, URL frontend giữ nguyên, 404 không phải lỗi DNS và cần xử lý LB trước. | Mentor tách DNS, triển khai LB, HTTP Host/path, class/controller và backend; bổ sung rule đối chiếu ngoài lab theo yêu cầu học viên. Không cấu hình cloud/MetalLB/DNS bên ngoài hoặc thử LAN/Internet. | Đã xử lý qua thực hành và review ngày 2026-10-09; chi tiết, cấu hình tham khảo và giới hạn minh chứng trong [tổng kết](../after-study/06-truy-cap-tu-macos.md). |

## Nhật ký học tập

Copy mẫu này cho mỗi lần học, kể cả khi buổi chưa hoàn thành. Ghi ngày theo giờ Việt Nam (Asia/Saigon).

```markdown
### YYYY-MM-DD — Buổi NN
- Thời gian học:
- Challenge / phần đã làm:
- Minh chứng (manifest, script, output đã lược dữ liệu nhạy cảm):
- Concept đã hiểu / câu hỏi đã trả lời:
- Symptom → bằng chứng → nguyên nhân → cách sửa → kiểm tra lại:
- Hint đã dùng (không / 1 / 2 / 3 / 4 / solution):
- Kết quả review / nội dung cần ôn:
- Tổng kết kiến thức (link after-study khi buổi review đạt):
- Việc tiếp theo:
```

### 2026-10-06 — Buổi 01
- Thời gian học: Không ghi nhận thời lượng; ngày theo giờ Việt Nam.
- Challenge / phần đã làm: Bật Kubernetes trên OrbStack; quan sát context, node, namespace và Pod hệ thống.
- Minh chứng: Các lệnh chỉ đọc `kubectl config get-contexts`, `kubectl config current-context`, `kubectl cluster-info`, `kubectl get nodes -o wide`, `kubectl get namespaces`, `kubectl get pods -A -o wide` xác nhận context `orbstack`, một node `Ready` có role `control-plane`, các namespace hệ thống và hai Pod trong `kube-system` đều `Running`, `READY=1/1`, `RESTARTS=0`. Xem [hội thoại và output review](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f).
- Concept đã hiểu / câu hỏi đã trả lời: Phân biệt các cluster qua cấu hình context trên máy; `get pods` dùng namespace mặc định của context, `-A` xem mọi namespace trong cluster; DNS lỗi có thể ảnh hưởng việc tìm Service bằng tên; container chạy trên node được scheduler chọn, không phụ thuộc vòng đời Terminal.
- Symptom → bằng chứng → nguyên nhân → cách sửa → kiểm tra lại: Không có lỗi runtime được báo. Vướng kiến thức về Pod hệ thống và luồng tạo Pod; mentor giải thích vai trò CoreDNS, Local Path Provisioner, kubectl, API server, scheduler và kubelet/runtime; học viên trả lời đúng tình huống kiểm tra tiếp theo.
- Hint đã dùng: Không dùng hint debug; có giải thích lý thuyết sau review.
- Kết quả review / nội dung cần ôn: Buổi 01 đạt. Ôn tên và trách nhiệm các thành phần trong luồng tạo Pod; workload local vẫn phụ thuộc cluster/node và máy Mac.
- Việc tiếp theo: Buổi 02 — tự tạo, inspect và xóa nginx Pod, quan sát hành vi sau khi xóa.

### 2026-10-06 — Buổi 02
- Thời gian học: Không ghi nhận thời lượng; ngày theo giờ Việt Nam.
- Challenge / phần đã làm: Tạo nginx Pod bằng `kubectl run`; xem trạng thái, IP, logs và describe; xóa Pod, quan sát không có Pod thay thế. Sau khi mất output lần đầu, tạo lại Pod để lấy minh chứng rồi xóa Pod đó.
- Minh chứng: Học viên gửi output `kubectl get pod nginx-buoi2 -o wide`, `kubectl logs nginx-buoi2 --tail=20`, `kubectl describe pod nginx-buoi2`. Pod trong namespace `default` đạt `Running`, `READY=1/1`, `RESTARTS=0`, IP `192.168.194.5`; chạy trên node `orbstack` có IP `192.168.139.2`. Logs cho thấy nginx hoàn tất cấu hình và khởi động worker processes. Events gồm `Scheduled`, `Pulling`, `Pulled`, `Created`, `Started`. Sau lần xóa cuối, lệnh chỉ đọc lọc đúng tên Pod trả về `No resources found in default namespace`; Events còn `Killing — Stopping container nginx-buoi2`. Xem [hội thoại và output review](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f).
- Concept đã hiểu / câu hỏi đã trả lời:
  - Trong lab, một Pod chứa một container nginx; nginx worker processes là tiến trình trong container, không phải Pod hoặc Kubernetes node khác.
  - `get` xem trạng thái và vị trí/IP; `logs` xem stdout/stderr của container; `describe` xem trạng thái chi tiết và Events Kubernetes.
  - Scheduler gán Pod vào node; kubelet phối hợp container runtime tải image, tạo và chạy container. Phân biệt Pod IP với Node IP.
  - `kubectl run` mặc định dùng `--restart=Always`, sinh `spec.restartPolicy: Always`; có thể xem cấu hình bằng `--dry-run=client -o yaml` mà không tạo Pod.
  - `restartPolicy` thuộc cấu hình Pod nhưng điều khiển việc restart container trong Pod còn tồn tại; không tạo Pod mới sau khi Pod bị xóa. Pod tạo trực tiếp trong lab không có controller yêu cầu duy trì số lượng Pod.
- Symptom → bằng chứng → nguyên nhân → cách sửa → kiểm tra lại: Pod không xuất hiện lại sau delete là hành vi của Pod đơn lẻ, không phải lỗi cluster. Mất output được xử lý bằng cách chạy lại phần quan sát và gửi minh chứng trước khi xóa. Không có lỗi runtime được báo.
- Hint đã dùng: 1 — tách vòng đời container và Pod; sau đó giải thích lý thuyết và chỉ ra mặc định trong help/client dry-run.
- Kết quả review / nội dung cần ôn: Buổi 02 đạt. Ôn restart container khác tạo Pod thay thế; các kiểm tra đã làm chưa kiểm tra HTTP, không bổ sung kiểm tra truy cập ngoài phạm vi buổi này.
- Việc tiếp theo: Buổi 03 — Deployment nginx với 3 replicas; so sánh hành vi sau khi xóa một Pod.

### 2026-10-06 — Buổi 03 (bắt đầu)
- Challenge / phần đang học: Tạo Deployment nginx với 3 replicas; quan sát Deployment, ReplicaSet và Pod; xóa một Pod để kiểm chứng hành vi quản lý số lượng Pod.
- Minh chứng tại thời điểm bắt đầu: Chưa có output triển khai trong hội thoại; command tạo Deployment mới chỉ được kiểm tra bằng client dry-run, không tạo workload thay học viên.
- Kết quả tại thời điểm bắt đầu: Chưa review; trạng thái `Đang học`, chưa tính vào tổng số buổi hoàn thành.
- Việc tiếp theo: Học viên tạo và inspect trước, gửi output để giữ minh chứng rồi thực hiện thử xóa một Pod.

### 2026-10-07 — Buổi 03 (hoàn thành)
- Thời gian học: Không ghi nhận thời lượng; ngày theo giờ Việt Nam.
- Challenge / phần đã làm: Tạo Deployment `nginx-buoi3` với 3 replicas, inspect Deployment/ReplicaSet/Pod, xóa một Pod và quan sát Pod thay thế. Mentor chỉ đọc cluster để kiểm tra, không thực hiện thao tác xóa hoặc scale thay học viên.
- Minh chứng: Trước và sau khi hệ thống ổn định, Deployment đạt `READY=3/3`, `UP-TO-DATE=3`, `AVAILABLE=3`; ReplicaSet `nginx-buoi3-66546989b4` có `DESIRED=3`, `CURRENT=3`, `READY=3`. Pod `nginx-buoi3-66546989b4-4b9gl` bị xóa; Pod mới `nginx-buoi3-66546989b4-dg86c` xuất hiện, IP `192.168.194.9`, `AGE=78s` trong snapshot học viên gửi, `READY=1/1`, `RESTARTS=0`. Hai Pod còn lại giữ nguyên; cả ba cùng node `orbstack`. Đối chiếu UID và ownerReferences xác nhận Pod mới thuộc ReplicaSet, ReplicaSet thuộc Deployment. Event `SuccessfulCreate — Created pod: nginx-buoi3-66546989b4-dg86c` đã được đọc trong review và lưu trong tổng kết; ở lần kiểm tra khi viết tài liệu Event không còn trả về.
- Concept đã hiểu / câu hỏi đã trả lời: Desired state khác actual state; xóa Pod không thay đổi yêu cầu 3 replicas. ReplicaSet controller tạo Pod bù; scheduler chọn node; kubelet/runtime chạy và restart container. Muốn giữ 2 Pod thì sửa `.spec.replicas=2` của Deployment tương ứng, không chỉnh trực tiếp ReplicaSet do Deployment quản lý. Không cần học thuộc tên Pod, nhưng cần đối chiếu định danh khi debug.
- Symptom → bằng chứng → nguyên nhân → cách sửa → kiểm tra lại: Không có lỗi runtime được báo. Nhầm cấp cấu hình ReplicaSet/Deployment được sửa bằng giải thích quan hệ sở hữu và đối chiếu tài liệu; học viên trả lời đúng tình huống giữ hai Pod. Các tình huống scale xuống một/hai Pod mới được review về lý thuyết, chưa có minh chứng thực hành scale trong hội thoại.
- Hint đã dùng: Không dùng hint debug; có giải thích sau quan sát và chỉnh lại mental model trong review.
- Kết quả review / nội dung cần ôn: Buổi 03 đạt. Ôn cấp đặt cấu hình mong muốn, vai trò từng controller và việc reconcile không bảo đảm mọi thời điểm đều đủ Pod Ready.
- Tổng kết kiến thức đầy đủ: [after-study/03-deployment.md](../after-study/03-deployment.md).
- Việc tiếp theo: Chờ bắt đầu Buổi 04 — Labels và Selectors; buổi 4 vẫn `Chưa học`, chưa triển khai challenge mới.

### 2026-10-07 — Buổi 04 (hoàn thành)
- Thời gian học: Không ghi nhận thời lượng; ngày theo giờ Việt Nam.
- Challenge / phần đã làm: Dùng lại Deployment `nginx-buoi3` với ba Pod; học viên tạo Service `nginx-buoi4` có selector sai, inspect label/selector/backend và xác định cần đổi selector sang `app=nginx-buoi3`. Mentor kiểm tra cú pháp bằng client dry-run, không áp dụng patch hoặc xóa Pod thay học viên.
- Minh chứng: Output học viên cho thấy ba Pod `Running`, `READY=1/1`, nhãn `app=nginx-buoi3,pod-template-hash=66546989b4`; Service chọn `app=nginx-buoi4`, dòng Endpoints trống, EndpointSlice `nginx-buoi4-p6d8v` có `ENDPOINTS=<unset>`. Sau sửa, kiểm tra API chỉ đọc xác nhận selector `app=nginx-buoi3`; các địa chỉ `192.168.194.7`, `.8`, `.9` trỏ đúng ba Pod, đều `ready=true`, `serving=true`, `terminating=false`. Service giữ tên/nhãn riêng và IP `192.168.194.166`; GET qua Service từ Mac trả HTTP 200 và trang nginx lúc 10:40:59, giờ Việt Nam. Xem [hội thoại và minh chứng](https://ampcode.com/threads/T-01a1107e-4443-77bd-935a-75507972607f).
- Concept đã hiểu / câu hỏi đã trả lời: Service so selector với nhãn Pod trong cùng namespace, không dựa vào tên Deployment hoặc nhãn của chính Service. Pod IP mới không cần khai báo thủ công trong Service. Chỉ đổi Deployment.metadata.labels không đổi nhãn Pod hiện có; Pod tạo lại lấy nhãn từ template ReplicaSet, không kế thừa nhãn ngoài cùng Deployment. Học viên trả lời đúng tình huống chọn Pod và đã được giải đáp phần tạo lại Pod.
- Symptom → bằng chứng → nguyên nhân → cách sửa → kiểm tra lại: Service không có địa chỉ đích dù Pod đang Ready → label Pod khác selector Service → đổi điều kiện chọn, giữ nguyên workload → API có đúng ba backend Ready và HTTP qua Service thành công.
- Hint đã dùng: 4 — so sánh trực tiếp selector và label; sau khi học viên tự đề xuất giá trị đúng, cung cấp command patch. Có giải thích nguồn nhãn từ Pod template sau review.
- Kết quả review / nội dung cần ôn: Buổi 04 đạt. Ôn phân biệt metadata.labels, spec.selector và spec.template.metadata.labels. Không thực hiện đổi nhãn Deployment hoặc xóa lại Pod trong buổi 4; chưa kiểm thử HTTP sau thay thế, DNS nội bộ hoặc các loại Service khác.
- Tổng kết kiến thức đầy đủ: [after-study/04-labels-va-selectors.md](../after-study/04-labels-va-selectors.md).
- Việc tiếp theo: Buổi 05 — Service; tái sử dụng Service đã sửa để gọi nginx từ client trong cluster và học endpoint ổn định.

### 2026-10-07 — Buổi 05 (bắt đầu)
- Challenge / phần đang học: Gọi nginx qua Service, không gọi trực tiếp từng Pod IP; sau đó kiểm tra endpoint ổn định và phân biệt ClusterIP, NodePort, LoadBalancer.
- Minh chứng tại thời điểm bắt đầu: Service `nginx-buoi4` là ClusterIP, IP `192.168.194.166`, port 80; ba Pod nginx vẫn `Running`, `READY=1/1`. Mẫu client `curl-buoi5` được kiểm tra bằng client dry-run không attach; image `curlimages/curl:latest` có manifest Linux ARM64. Mentor chưa tạo client Pod thay học viên; chưa có output request từ client Pod trong hội thoại.
- Kết quả tại thời điểm bắt đầu: Chưa review buổi 5; trạng thái `Đang học`, không tính vào tổng bốn buổi hoàn thành.
- Việc tiếp theo: Học viên chạy client Pod tạm gọi `http://nginx-buoi4`, gửi output để kiểm chứng luồng client trong cluster → Service → nginx Pod.

### 2026-10-07 — Buổi 05 (bước 1 đạt, đang học)
- Challenge / phần đã làm: Học viên chạy client Pod tạm bằng image `curlimages/curl:latest`, gọi `http://nginx-buoi4` trong namespace `default`, không dùng IP từng Pod nginx.
- Minh chứng: Output học viên gửi có `HTTP/1.1 200 OK`, nội dung `Welcome to nginx!` và `pod "curl-buoi5" deleted`. Header Date của response là `2026-10-07 04:33:24 GMT`, tương ứng 11:33:24 giờ Việt Nam. Kiểm tra API chỉ đọc khi review xác nhận client không còn; ba Pod nginx vẫn Ready, Service vẫn là ClusterIP `192.168.194.166`. Xem [hội thoại thực hành Buổi 05](https://ampcode.com/threads/T-01a1149b-42ee-7429-a039-a101af378367).
- Concept đã trả lời: Tiến trình curl chạy bên trong Pod, dù lệnh kubectl được gõ trên Mac; `nginx-buoi4` là tên Service, client không cần biết IP của ba Pod nginx. Phần giải thích DNS cần phân biệt tên Service → ClusterIP với cơ chế chuyển traffic tới backend, không coi DNS là bộ chọn Pod cho Service ClusterIP này.
- Symptom / hint: Không có lỗi runtime được báo; không dùng hint debug.
- Kết quả review: Bước gọi Service từ client nội bộ đạt. Một HTTP 200 không chứng minh traffic đã tới cả ba backend hoặc không gián đoạn khi Pod bị xóa. Buổi 05 vẫn `Đang học`, tổng tiến độ 4/28; chưa xuất bản tổng kết hoàn thành.
- Việc tiếp theo: Học viên tự xóa đúng một Pod nginx, quan sát Pod thay thế và EndpointSlice, gọi lại cùng URL để kiểm chứng Service sau thay thế; sau đó review `port`/`targetPort` và ClusterIP, NodePort, LoadBalancer. Chưa thực hiện thao tác xóa trong bước 1; mentor không thay đổi workload.

### 2026-10-07 — Buổi 05 (bước 2: backend đã cập nhật, chờ HTTP)
- Minh chứng API: Kiểm tra chỉ đọc lúc 13:51:34 giờ Việt Nam xác nhận Pod cũ `nginx-buoi3-66546989b4-6gncw` (IP `192.168.194.7`, UID `a7adbab0-35ce-4343-a096-75da2b838bf0`) không còn. Pod mới `nginx-buoi3-66546989b4-bzts7` có UID `768e25e4-617c-49f6-81ad-3de1057f6b51`, IP `192.168.194.11`, Ready và cùng owner ReplicaSet `nginx-buoi3-66546989b4`. Hai Pod còn lại giữ nguyên; Deployment trở về `READY=3/3`.
- Service và backend: Service `nginx-buoi4` giữ nguyên UID `b7171c2c-b59d-4ca1-818d-9b16fb0fec41`, ClusterIP `192.168.194.166`, selector `app=nginx-buoi3`, port/targetPort đều 80. EndpointSlice `nginx-buoi4-p6d8v` có địa chỉ `.8`, `.9`, `.11`, tất cả `ready=true`; targetRef của `.11` khớp đúng tên và UID Pod mới, không còn backend `.7`.
- Concept đã trả lời: Học viên trả lời đúng tên/IP Service không đổi, client không cần sửa URL và ReplicaSet controller tạo Pod bù, không phải Service.
- Giới hạn minh chứng: Chưa nhận output request qua tên Service sau thay thế; Ready và EndpointSlice đúng chưa đủ để chốt HTTP thành công hay không gián đoạn trong lúc xóa Pod. Mentor không xóa Pod hoặc triển khai client thay học viên.
- Kết quả / việc tiếp theo: Review hai câu trả lời đạt; phần thay thế Pod và cập nhật backend đã được kiểm chứng. Cần bổ sung HTTP status sau thay thế, review port/targetPort bằng tình huống hai port khác nhau, rồi phân biệt ClusterIP, NodePort, LoadBalancer. Buổi 05 vẫn `Đang học`, tổng 4/28.

### 2026-10-07 — Buổi 05 (review port/targetPort, tiếp tục các loại Service)
- Câu trả lời học viên: Với client gọi cổng 8080 và nginx lắng nghe cổng 80, chọn `port=8080` đúng nhưng chưa nêu giá trị `targetPort`. Giải thích đúng ý chính: nếu đặt cả hai bằng 8080 thì request không thành công vì nginx không lắng nghe cổng đích đó.
- Bổ sung trong review: Cấu hình cần là `port=8080`, `targetPort=80`; Service chuyển traffic tới cổng của ứng dụng, không tự làm nginx mở cổng hoặc đổi cấu hình lắng nghe. Đây là tình huống giả định, chưa patch Service hoặc thử HTTP qua cổng 8080.
- Phần tiếp theo: Giới thiệu ClusterIP cho endpoint nội bộ, NodePort thêm đường truy cập qua Node IP và nodePort, LoadBalancer yêu cầu một triển khai load balancer phù hợp. Tham chiếu [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/#service-type); chưa có câu trả lời review các loại Service hoặc thực hành NodePort/LoadBalancer.
- Việc còn thiếu: Output HTTP qua tên Service sau thay thế Pod; review lựa chọn loại Service và các cổng truy cập. Buổi 05 vẫn `Đang học`, tổng 4/28; chưa tạo tổng kết hoàn thành.

### 2026-10-07 — Buổi 05 (hoàn thành)
- Thời gian học: Không ghi nhận thời lượng; ngày chốt theo giờ Việt Nam.
- Challenge / phần đã làm: Dùng lại ba Pod nginx và Service đã sửa ở buổi 4; học viên chạy client Pod gọi tên Service, thay thế đúng một Pod nginx và kiểm tra lại cùng endpoint. Mentor chỉ inspect cluster, không triển khai hoặc xóa workload thay học viên.
- Minh chứng: HTTP ban đầu có output `200 OK`, trang nginx và thông báo client Pod được dọn. API đối chiếu trước/sau xác nhận Pod `.7` đã được thay bằng Pod mới `.11`, ba backend Ready, Deployment `3/3`, Service giữ tên/UID/ClusterIP `192.168.194.166`. Học viên xác nhận HTTP sau thay thế trả về giống lần trước và không cần gửi lại output; kết quả này ghi nhận theo xác nhận, không phải raw output lần hai hoặc HTTP do mentor kiểm tra độc lập. Snapshot chỉ đọc khi chốt lúc 14:57 giờ Việt Nam vẫn có ba Pod Ready và Service ClusterIP `port=80`, `targetPort=80`.
- Concept / review: Học viên trả lời đúng curl chạy trong Pod, tên URL là Service, không cần biết IP từng Pod, client không đổi URL khi Pod thay thế và ReplicaSet controller tạo Pod bù. Chọn đúng ClusterIP cho Spark Worker gọi Master nội bộ, cổng 30080 khi dùng Node IP, và LoadBalancer không bảo đảm IP public. Phần lý do NodePort/LoadBalancer ban đầu chưa rõ đã được mentor giải thích; không ghi là học viên tự giải thích ngay từ đầu. Tình huống cuối chọn đúng `targetPort=9000` khi nginx đã nghe 9000, giữ cổng client.
- Symptom / hint: Không có lỗi runtime được báo; không dùng hint debug. Bổ sung targetPort còn thiếu và giải thích endpoint/cổng cùng yêu cầu triển khai LoadBalancer sau review. NodePort, LoadBalancer, port 8080 và nginx nghe 9000 chỉ là tình huống giả định, không thay cấu hình thật.
- Kết quả / nội dung nên ôn: Buổi 05 đạt, tiến độ 5/28. Ôn vì sao nodePort gắn với Node IP còn port gắn với Service IP, và vì sao LoadBalancer cần thành phần thực hiện yêu cầu. Không suy ra đã đo chia đều request hoặc không gián đoạn lúc xóa Pod.
- Tổng kết kiến thức đầy đủ: [after-study/05-service.md](../after-study/05-service.md).
- Việc tiếp theo: Chờ bắt đầu Buổi 06 — Truy cập từ macOS; buổi 6 vẫn `Chưa học`, chưa triển khai challenge browser / Ingress.

### 2026-10-07 — Buổi 06 (bắt đầu)
- Challenge / phần đang học: Truy cập nginx từ browser trên Mac qua Service, không dùng IP từng Pod. Bắt đầu bằng Service hiện có để quan sát hỗ trợ networking của OrbStack; sau đó học LoadBalancer, Ingress và domain local theo kết quả thực hành.
- Minh chứng tại thời điểm bắt đầu: Kiểm tra API chỉ đọc lúc 15:26 giờ Việt Nam xác nhận context `orbstack`, Deployment `nginx-buoi3` 3/3; các Pod ở `.8`, `.9`, `.11` đều Ready. Service `nginx-buoi4` giữ ClusterIP `192.168.194.166`, selector `app=nginx-buoi3`, port/targetPort đều 80, chưa có nodePort. Không có IngressClass; danh sách Pod toàn cluster chỉ gồm nginx, CoreDNS và Local Path Provisioner.
- Tài liệu đối chiếu: [OrbStack Kubernetes](https://docs.orbstack.dev/kubernetes/) xác nhận hỗ trợ truy cập ClusterIP và tên đầy đủ `service.namespace.svc.cluster.local` từ Mac, LoadBalancer và domain `*.k8s.orb.local`; không cài Ingress controller mặc định. Đây là thông tin tài liệu, chưa phải kết quả browser của học viên.
- Kết quả tại thời điểm bắt đầu: Chưa có output truy cập từ Mac hoặc review concept; Buổi 06 `Đang học`, tổng tiến độ vẫn 5/28, chưa tạo tổng kết hoàn thành. Mentor không thay đổi workload.
- Việc tiếp theo: Học viên tự chọn URL dựa trên địa chỉ/cổng Service, mở browser trên Mac và gửi URL cùng kết quả; nếu lỗi, quan sát symptom và tự điều tra trước khi nhận hint. LoadBalancer, Ingress và domain local chưa thực hành.

### 2026-10-07 — Buổi 06 (bước 1 đạt, tiếp tục LoadBalancer)
- Minh chứng học viên: Xác nhận truy cập được `http://192.168.194.166:80`; gửi output `kubectl get services` có `nginx-buoi4`, `TYPE=ClusterIP`, `CLUSTER-IP=192.168.194.166`, `EXTERNAL-IP=<none>`, `PORT(S)=80/TCP`. Kết quả browser theo xác nhận, không có ảnh hoặc HTTP status để kết luận thêm.
- Đối chiếu và review: API chỉ đọc lúc 15:52 giờ Việt Nam vẫn có Service ClusterIP, selector `app=nginx-buoi3`, port/targetPort 80; Deployment 3/3. URL chọn địa chỉ/cổng Service, không dùng Pod IP. Mentor giải thích Mac truy cập được nhờ networking OrbStack, không phải Service đã có IP public; cổng client là Service.port, traffic ứng dụng không đi qua kubectl.
- DNS / hint: Ban đầu học viên hỏi tên ngắn `nginx-buoi4`; kiểm tra bằng bộ phân giải DNS hệ điều hành Mac không tìm thấy tên ngắn nhưng phân giải được tên đầy đủ của Service. Mentor gợi ý dùng cột CLUSTER-IP; học viên chọn URL đúng. Chưa thực hành browser với tên đầy đủ.
- Kết quả: Bước browser qua ClusterIP đạt; toàn Buổi 06 vẫn `Đang học`, tổng 5/28, chưa tạo tổng kết hoàn thành. Mentor không thay đổi workload hoặc gửi request HTTP thay học viên.
- Việc tiếp theo: Challenge tái sử dụng Service `nginx-buoi4` với LoadBalancer để mở `http://k8s.orb.local:8080`, giữ nginx nghe cổng 80 và giữ selector. Học viên đề xuất các field type/port/targetPort trước khi triển khai; đổi cổng Service sẽ thay cổng URL ClusterIP cũ. Đây mới là requirement, chưa có thay đổi cấu hình hoặc kết quả LoadBalancer/Ingress.

### 2026-10-07 — Buổi 06 (review cấu hình LoadBalancer, chờ triển khai)
- Câu trả lời học viên: Chọn đúng `spec.type=LoadBalancer`, `spec.ports[0].port=8080`, `spec.ports[0].targetPort=80` cho browser gọi cổng 8080 trong khi nginx vẫn nghe cổng 80.
- Kiểm tra của mentor: Đọc Service hiện tại vẫn thấy ClusterIP, port/targetPort 80 và selector `app=nginx-buoi3`. Kiểm tra JSON Patch bằng `kubectl patch --local` trên JSON đọc từ API cho kết quả đúng ba field, giữ selector và ClusterIP; không áp dụng patch lên cluster. Kiểm tra local không chứng minh đã được cấp endpoint LoadBalancer hoặc HTTP thành công.
- Việc tiếp theo: Học viên tự chạy patch, inspect Service và mở `http://k8s.orb.local:8080` trên Mac. URL ClusterIP sau đổi cổng là `http://192.168.194.166:8080`; chưa có minh chứng triển khai hoặc truy cập các URL mới. Buổi 06 vẫn `Đang học`, tổng 5/28; Ingress còn chờ.

### 2026-10-07 — Buổi 06 (HTTP qua LoadBalancer đạt, hỏi về môi trường thông thường)
- Minh chứng học viên: Gửi `get service` có `TYPE=LoadBalancer`, ClusterIP `192.168.194.166`, EXTERNAL-IP `192.168.139.2`, `PORT(S)=8080:32274/TCP`, selector `app=nginx-buoi3`. Curl chạy từ Terminal Mac tới `http://k8s.orb.local:8080` trả `HTTP/1.1 200 OK` và nội dung `Welcome to nginx!`; header Date `09:09:52 GMT` tương ứng 16:09:52 giờ Việt Nam. Có raw output curl, chưa có xác nhận browser cho URL LoadBalancer.
- Đối chiếu API chỉ đọc lúc 16:11 giờ Việt Nam: Service giữ UID/ClusterIP/selector; type LoadBalancer, port 8080, targetPort 80, nodePort 32274, `allocateLoadBalancerNodePorts=true`; status có IP `192.168.139.2`, `ipMode=VIP`. Node `orbstack` có INTERNAL-IP cùng địa chỉ này; đây là địa chỉ private, không phải IP public Internet. Kiểm tra DNS hệ điều hành Mac phân giải `k8s.orb.local` thành `192.168.138.4`, không trùng EXTERNAL-IP; domain thuộc tích hợp local của OrbStack, không suy ra cơ chế DNS mặc định của Kubernetes.
- Câu hỏi đang học: Ngoài OrbStack thì truy cập LoadBalancer thế nào? Cần phân biệt triển khai LB/network reachability với tên DNS; môi trường cloud có tích hợp hỗ trợ, self-managed có thể dùng MetalLB hoặc NodePort, debug cá nhân có thể dùng port-forward. Các lựa chọn này mới là lý thuyết, chưa cài MetalLB, tạo DNS bên ngoài hoặc chạy port-forward. Tham chiếu [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer), [MetalLB](https://metallb.io/) và [port-forward](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/).
- Kết quả / việc tiếp theo: Cấu hình và HTTP qua LoadBalancer đạt; tiếp tục giải thích và review DNS/LB trước chặng Ingress. Buổi 06 vẫn `Đang học`, tổng 5/28, chưa tạo tổng kết hoàn thành. Mentor không sửa workload hoặc gửi HTTP thay học viên.

### 2026-10-07 — Buổi 06 (review private IP và DNS)
- Câu trả lời học viên: Đúng ý chính rằng DNS không giải quyết được LoadBalancer pending khi chưa có triển khai hỗ trợ; cần chỉnh cách nói "DNS không giúp lấy ra IP External" thành "DNS có thể trả địa chỉ đã có trong bản ghi, nhưng không cấp IP hoặc tạo/cấu hình LoadBalancer".
- Nội dung cần phân biệt: IP private không truy cập trực tiếp qua Internet công cộng; máy khác vẫn có thể truy cập nếu có đường mạng phù hợp như VPN hoặc một gateway/proxy được cấu hình. Cùng LAN không tự bảo đảm truy cập Node IP ảo của OrbStack, còn phụ thuộc routing, cổng và chính sách exposure/firewall.
- Tài liệu đối chiếu: [OrbStack — Exposing ports to LAN](https://docs.orbstack.dev/kubernetes/#exposing-ports-to-lan) ghi NodePort/LoadBalancer mặc định chỉ cho truy cập từ máy local; chia sẻ LAN cần tùy chọn "Expose services to local network devices". Chưa kiểm tra trạng thái tùy chọn trên máy học viên, chưa thử từ máy LAN/Internet và không thay đổi cấu hình chia sẻ.
- Kết quả / việc tiếp theo: Câu hỏi DNS/LB pending đạt ý chính, mentor bổ sung phân biệt DNS với cấp endpoint và reachability. Tiếp theo là chặng Ingress để định tuyến HTTP theo host/path; chưa thực hành hoặc review Ingress, Buổi 06 vẫn `Đang học`, tổng 5/28.

### 2026-10-08 — Buổi 06 (ôn địa chỉ theo vai trò, tạm dừng Ingress)
- Symptom / nhu cầu học: Sau khi hỏi sự khác nhau giữa Service types, học viên nói chưa hiểu ServiceIP, NodeIP và LB-IP. Các minh chứng truy cập thành công trước đó không chứng minh học viên đã hiểu đủ các vai trò địa chỉ.
- Minh chứng chỉ đọc: Node `orbstack` có INTERNAL-IP `192.168.139.2`; Service `nginx-buoi4` có ClusterIP `192.168.194.166` và địa chỉ trong status LoadBalancer `192.168.139.2`. Service vẫn type LoadBalancer, port 8080, targetPort 80, nodePort 32274. Ba Pod nginx ở `.8`, `.9`, `.11` vẫn Ready; dùng Pod `.11` làm ví dụ, không suy ra request trước đã tới đúng Pod này.
- Điều chỉnh cách giảng: Bắt đầu từ Pod chạy nginx và node chứa Pod, rồi giải thích Service IP là endpoint ảo để gọi nhóm Pod, LB IP là địa chỉ đầu vào được triển khai LB công bố cho Service. Node IP và LB IP trùng số trong lab nhưng khác vai trò; không khẳng định chúng luôn khác nhau hoặc LB phải là một máy riêng. Chỉ minh họa lại URL Service đã dùng, chưa thêm resource/cổng hoặc triển khai Ingress.
- Review đầu tiên: Học viên trả lời đúng "gọi địa chỉ service" cho URL `http://192.168.194.166:8080`; đạt phần nhận diện Service IP thay vì Pod IP. Câu trả lời này chưa chứng minh đã phân biệt đầy đủ Node IP/LB IP.
- Review endpoint ổn định: Với tình huống Pod mới có IP khác, đã Ready/match label/backend cập nhật, Service giữ nguyên, học viên trả lời đúng không cần sửa URL vì Service chuyển request tới backend mới. Đây là câu trả lời lý thuyết, không phải một lần thực hành thay thế Pod mới hoặc kiểm thử không gián đoạn.
- Review Node IP/NodePort: Học viên chọn đúng cặp A `192.168.139.2:32274`, giải thích IP thuộc node `orbstack`, không chọn Service IP ghép với nodePort. Đạt phần nhận diện địa chỉ node và đường NodePort; không phải minh chứng đã thử HTTP qua NodePort.
- Kết quả / việc tiếp theo: Phần Service IP/endpoint ổn định và Node IP/NodePort đạt. Review LB IP bằng tình huống giả định node có INTERNAL-IP `10.0.0.10`, Service có EXTERNAL-IP `198.51.100.20`, port 8080; các địa chỉ chỉ là dữ liệu bài tập, không phải lab mới hoặc URL cần truy cập thật. Vai trò LB IP và Ingress vẫn cần review; không yêu cầu xóa Pod hoặc chạy lại lab. Buổi 06 vẫn `Đang học`, tổng 5/28; mentor không thay đổi workload hoặc cấu hình mạng.

### 2026-10-08 — Buổi 06 (review LB IP, chuẩn bị Ingress)
- Câu trả lời học viên: Viết `http://192.51.100.2:8080` và giải thích chọn địa chỉ/cổng của Service LoadBalancer để truy cập nhóm Pod. Chọn đúng vai trò LB IP + Service.port, không chọn Node IP/NodePort, nhưng giá trị IP chưa khớp `198.51.100.20` trong đề.
- Review: Đạt ý chính về đường vào qua LB; mentor đối chiếu URL đúng của ví dụ là `http://198.51.100.20:8080` và chỉnh cách nói Pod nằm trong Service/LB thành Pod chạy trên node, Service chọn nhóm Pod làm backend. Các địa chỉ là dữ liệu giả định, không gửi request HTTP tới chúng; không suy ra đã kiểm thử đường NodePort hoặc IP LoadBalancer trực tiếp.
- Minh chứng chỉ đọc ngày 2026-10-08: Deployment `nginx-buoi3` 3/3, Service `nginx-buoi4` vẫn LoadBalancer với port 8080 và nodePort 32274. Không có IngressClass hoặc Ingress; danh sách Pod không có Ingress controller. Terminal kiểm tra chưa tìm thấy `helm` trong PATH, Homebrew có sẵn tại `/opt/homebrew/bin/brew`. Mentor không cài công cụ hoặc triển khai controller thay học viên.
- Challenge tiếp theo: Truy cập nginx qua host-based Ingress tại `http://nginx.k8s.orb.local/`, cổng HTTP 80; hostname không khớp không được phục vụ trang nginx. Giữ Deployment và Service hiện có. Thành công qua URL LoadBalancer cũ `:8080` không chứng minh Ingress đã hoạt động.
- Bước chuẩn bị được giao: Học viên tự cài Helm qua Homebrew và gửi `helm version --short`; sau đó dùng một controller Traefik và Ingress chuẩn Kubernetes, chưa cần dashboard, Gateway API hoặc platform đầy đủ. Đây mới là bước giao, chưa có minh chứng cài Helm/controller hoặc thực hành Ingress.
- Tài liệu đối chiếu: [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/#prerequisites) yêu cầu controller để thực thi rule; [Traefik Kubernetes quickstart](https://doc.traefik.io/traefik/getting-started/quick-start-with-kubernetes/) nêu hỗ trợ Ingress và cài qua Helm; [Helm trên macOS](https://helm.sh/docs/intro/install/#from-homebrew-macos) ghi lệnh `brew install helm`. Không sao chép phần IngressRoute/Gateway API/dashboard của quickstart vào lab này.
- Kết quả / việc tiếp theo: Phần phân biệt Service IP, Node IP và LB IP đạt ý chính; chuẩn bị chặng Ingress. Buổi 06 vẫn `Đang học`, tổng 5/28, chưa tạo tổng kết hoàn thành; chờ minh chứng học viên thực hiện bước chuẩn bị.

### 2026-10-08 — Buổi 06 (Helm sẵn sàng, giao cài Ingress controller)
- Minh chứng học viên: Gửi output `helm version --short` là `v4.3.0+gbec5b06`; mentor đối chiếu CLI cũng trả cùng phiên bản. Bước chuẩn bị Helm đạt, không đồng nghĩa đã cài controller.
- Kiểm tra chỉ đọc: Context `orbstack` chưa có IngressClass hoặc Helm release. Node vẫn Kubernetes `v1.35.6+orb1`, kiến trúc ARM64. Service `default/nginx-buoi4` vẫn LoadBalancer, port 8080, targetPort 80 theo cấu hình đã kiểm chứng; không có thao tác sửa nginx trong bước này.
- Gói được chọn: [Traefik chart 41.6.1](https://github.com/traefik/traefik-helm-chart/blob/v41.6.1/traefik/Chart.yaml), app `v3.7.13`, yêu cầu Kubernetes >=1.25.0-0. Metadata [Docker Hub của tag v3.7.13](https://hub.docker.com/v2/repositories/library/traefik/tags/v3.7.13/) có image Linux ARM64/v8; không pull hoặc chạy container để kiểm tra.
- Validation chuẩn bị: Helm 4.3.0 render chart với namespace `ingress-system`, `providers.kubernetesCRD.enabled=false`, không cài CRD; `kubectl create --dry-run=client --validate=strict` nhận manifest hợp lệ. Đã kiểm tra đủ sáu resource chuẩn: ServiceAccount, ClusterRole, ClusterRoleBinding, Service, Deployment, IngressClass. Một replica Traefik, Service LoadBalancer HTTP 80 → container web 8000, class `traefik`, provider Ingress bật; không sinh CRD, IngressRoute, Gateway hoặc Ingress rule, không đụng resource nginx. Đây là render/client validation, chưa chứng minh controller chạy hoặc HTTP thành công.
- Bước được giao: Học viên tự chạy `helm install` release `traefik`, chart `traefik` từ `https://traefik.github.io/charts`, version 41.6.1, context `orbstack`, namespace `ingress-system` với `--create-namespace --wait --skip-crds --set providers.kubernetesCRD.enabled=false`. Giữ Deployment/Service nginx; controller có Service riêng trên cổng 80 và HTTPS 443 mặc định, chưa dùng HTTPS trong challenge.
- Minh chứng cần nhận: Pod controller Ready, Service LoadBalancer có HTTP port 80, IngressClass `traefik`, curl từ Mac tới `http://k8s.orb.local:80/`. Khi request tới Traefik nhưng chưa có rule khớp thì [404 là hành vi được tài liệu mô tả](https://doc.traefik.io/traefik/getting-started/faq/#404-not-found), không phải kết quả truy cập nginx thành công. Chưa có output các kiểm tra runtime này.
- Kết quả / việc tiếp theo: Helm đã sẵn sàng; chờ học viên cài và quan sát controller, sau đó mới tạo rule host-based cho nginx. Mentor không cài controller hoặc thay đổi workload. Buổi 06 vẫn `Đang học`, tổng 5/28, chưa tạo tổng kết hoàn thành.

### 2026-10-08 — Buổi 06 (controller đã sẵn sàng, tiếp tục rule Ingress)
- Minh chứng chỉ đọc: Lần kiểm tra lúc 21:19 xác nhận Helm release `traefik` ở `ingress-system` có status `deployed`, chart 41.6.1, app v3.7.13, thời điểm cập nhật 13:27 giờ Việt Nam. Lần kiểm tra lúc 21:39 vẫn thấy Deployment/Pod Traefik Ready 1/1, class `traefik`, Service LoadBalancer cổng 80/443. Không cần cài lại controller; mentor không thực hiện thao tác cài.
- Backend giữ nguyên: Deployment `nginx-buoi3` 3/3; Service `default/nginx-buoi4` vẫn port 8080, targetPort 80, selector `app=nginx-buoi3`. Chưa có Ingress trong cluster. GET chỉ đọc của mentor tới `http://k8s.orb.local:80/` lúc 21:46 trả HTTP 404, body `404 page not found`; không ghi là học viên đã tự chạy kiểm tra này hoặc đã truy cập nginx qua Ingress.
- Nội dung đã giải thích: `k8s.orb.local` và wildcard là tiện ích OrbStack, không do Service hoặc Ingress tự tạo. DNS trên Mac đã phân giải được cả tên gốc và `nginx.k8s.orb.local` khi chưa có rule. Theo yêu cầu học viên, đã thêm mục 1.4 trong quy tắc mentor, rule tiếp quản/prompt bàn giao và `AGENTS.md` để bắt buộc đối chiếu cấu hình ngoài OrbStack; không coi việc mentor giải thích là học viên đã review đạt nội dung này.
- Challenge đang giao: Ingress chuẩn Kubernetes ở `default`, class `traefik`, host `nginx.k8s.orb.local`, path `/` Prefix, tham chiếu Service `nginx-buoi4`. URL HTTP cổng 80 phải trả 200 và trang nginx; hostname `sai.k8s.orb.local` cùng cổng phải trả 404. Giữ nguyên Deployment/Service; URL LoadBalancer cũ cổng 8080 không phải minh chứng cho Ingress.
- Quyết định chờ học viên: Backend port của rule chọn 80 hay 8080, giải thích dựa trên ba cổng browser/controller, Service nginx và ứng dụng nginx. Chưa có câu trả lời hoặc thao tác tạo rule; mentor đã kiểm tra cú pháp CLI bằng client dry-run, không tạo Ingress thay học viên. API `kubectl explain` xác nhận backend tham chiếu Service cùng namespace và port của Service.
- Đối chiếu ngoài lab đang giới thiệu: DNS A/AAAA hoặc CNAME trỏ đường vào có thể truy cập; mạng/firewall cho phép TCP 80; triển khai LB phụ thuộc môi trường cloud hoặc cluster tự quản lý. Ví dụ một LAN phù hợp có thể dùng [MetalLB với IPAddressPool và L2Advertisement](https://metallb.io/configuration/) để cấp/công bố IP; đây là tham khảo, không cài vào OrbStack. Bản thân Ingress rule không bảo đảm cấp DNS/LB; việc tự động cấp cần controller/tích hợp phù hợp môi trường. Kiểm tra tách lớp bằng phân giải DNS và `curl --resolve` giữ hostname nhưng chỉ định IP; nếu đã tới controller mà không khớp rule thì kiểm tra host/path/class, sau đó Service/EndpointSlice và Pod khi có lỗi backend.
- Kết quả / việc tiếp theo: Chặng controller đã sẵn sàng theo API/HTTP chỉ đọc; đang chọn cấu hình rule và học đối chiếu ngoài lab. Buổi 06 vẫn `Đang học`, tổng 5/28; chưa tạo tổng kết hoàn thành, chưa bắt đầu Buổi 07.

### 2026-10-08 — Buổi 06 (backend port đúng, manifest chờ áp dụng)
- Câu trả lời học viên: Chọn `8080` cho backend port của rule. Giá trị đúng; chưa tự nêu lý do. Mentor bổ sung rằng Ingress tham chiếu port của Service; targetPort=80 trỏ tới cổng 80 nginx đã lắng nghe, không làm ứng dụng đổi cổng.
- Chuẩn bị: Đã tạo [nginx-buoi6-ingress.yaml](../nginx-buoi6-ingress.yaml) ở thư mục gốc: Ingress `nginx-buoi6`, namespace `default`, class `traefik`, host `nginx.k8s.orb.local`, path `/` Prefix, Service backend `nginx-buoi4`, port 8080; không có default backend/catch-all. Đây là mẫu được cung cấp sau khi học viên chọn cấu hình, không phải thao tác triển khai thay học viên.
- Validation: Đã đọc lại manifest; `kubectl create --dry-run=client --validate=strict -f nginx-buoi6-ingress.yaml` thành công. Kiểm tra JSON độc lập xác nhận namespace, class, host cụ thể, Prefix root và backend port 8080, không phải cổng Pod 80. API sau kiểm tra vẫn không có Ingress; dry-run không chứng minh HTTP routing đã hoạt động.
- Bước được giao: Học viên tự apply manifest bằng context `orbstack`, inspect Ingress trong `default`, mở `http://nginx.k8s.orb.local/` trên browser và gửi curl cho hostname đúng/sai cùng cổng 80. Cần HTTP 200 với trang nginx cho host đúng, HTTP 404 cho `sai.k8s.orb.local`; chưa nhận kết quả apply/browser/curl.
- Đối chiếu ngoài lab: Cấu trúc Ingress này dùng API Kubernetes chuẩn; host thực tế cần DNS trỏ tới đường vào controller đã được cấp và có network/firewall phù hợp như phần đối chiếu trước. Service backend có thể dùng ClusterIP; lab giữ LoadBalancer 8080 từ chặng trước để không thay hai hành vi cùng lúc. Không sửa Service hoặc DNS/hạ tầng bên ngoài trong bước này.
- Kết quả / việc tiếp theo: Backend port chọn đúng, manifest local đã được kiểm tra và chờ học viên áp dụng. Buổi 06 vẫn `Đang học`, tổng 5/28; chờ minh chứng routing và review concept/đối chiếu ngoài lab trước khi tạo tổng kết hoàn thành.

### 2026-10-09 — Buổi 06 (HTTP qua Ingress đạt, chờ review cuối)
- Minh chứng học viên: Output `describe ingress nginx-buoi6` có namespace `default`, Address `192.168.139.2`, class `traefik`, host `nginx.k8s.orb.local`, path `/`, backend `nginx-buoi4:8080` và ba địa chỉ `192.168.194.9:80`, `.8:80`, `.11:80`; không có Events. Curl từ Mac tới `http://sai.k8s.orb.local/` trả HTTP 404/body `404 page not found` lúc 09:30:23 giờ Việt Nam; `http://nginx.k8s.orb.local/` trả HTTP 200/trang `Welcome to nginx!` lúc 09:30:27. Chưa có xác nhận browser cho hostname Ingress.
- Đối chiếu chỉ đọc của mentor: Ingress đã tồn tại, cấu hình khớp manifest: class `traefik`, host cụ thể, path `/` Prefix, backend Service port 8080, không khai báo defaultBackend. Service `nginx-buoi4` giữ selector `app=nginx-buoi3`, port 8080, targetPort 80; Service controller `traefik` mở cổng 80/443. Mentor không apply, patch hoặc gửi lại HTTP thay học viên trong lần review này.
- Kết quả thực hành: Hai request đúng/sai host đạt acceptance criteria HTTP cho Ingress. Có ba backend trong describe không chứng minh đã gửi request tới cả ba Pod; HTTP thành công từ Mac không chứng minh truy cập LAN/Internet hoặc readiness production.
- Review còn chờ: Học viên tự giải thích cổng frontend, Service backend và ứng dụng; phân biệt DNS với host routing qua tình huống 404; xác định đường vào controller, DNS và routing/firewall cần chuẩn bị ngoài OrbStack. Chưa ghi là học viên đã hiểu chỉ dựa trên output thành công.
- Kết quả / việc tiếp theo: Buổi 06 vẫn `Đang học`, tổng 5/28, chưa tạo tổng kết hoàn thành hoặc bắt đầu Buổi 07. Xác nhận browser qua hostname Ingress và review concept trước khi chốt buổi.

### 2026-10-09 — Buổi 06 (review concept đạt, chờ xác nhận browser)
- Câu trả lời học viên: (1) Đổi backend `service.port.number` của Ingress từ 8080 sang 9000 khi Service port đổi, URL browser giữ nguyên. (2) HTTP 404 của host sai không phải lỗi phân giải DNS; Traefik chọn theo host rule. (3) DNS không giải quyết được LB pending trong tình huống thiếu triển khai LB, cần xử lý đường vào LoadBalancer trước.
- Review: Cả ba câu đạt ý chính. Mentor bổ sung Traefik đối chiếu HTTP `Host` và path của request với rule; DNS không chọn backend HTTP. Chỉnh cách nói "DNS không có tác dụng" thành "DNS vẫn phân giải tên nhưng không cấp địa chỉ, tạo hoặc cấu hình LB"; cần triển khai/tích hợp LB phù hợp, công bố endpoint có thể truy cập, rồi cấu hình DNS và routing/firewall. Không coi học viên đã tự nêu đầy đủ mọi field hạ tầng ngoài lab.
- Giới hạn thực hành: Đổi port sang 9000 và tình huống LB pending chỉ là câu hỏi lý thuyết; không sửa Service/Ingress thật hoặc tạo DNS. Không yêu cầu chạy lại curl đã đạt.
- Kết quả / việc tiếp theo: Review concept đạt; còn thiếu xác nhận browser tại `http://nginx.k8s.orb.local/`. Buổi 06 vẫn `Đang học`, tổng 5/28, Buổi 07 chưa bắt đầu. Chốt và tự lưu tổng kết sau xác nhận này; không đánh dấu browser thành công dựa trên output curl.

### 2026-10-09 — Buổi 06 (hoàn thành)
- Thời gian học: Không ghi nhận thời lượng; buổi bắt đầu ngày 2026-10-07, tiếp tục ngày 2026-10-08 và chốt ngày 2026-10-09, giờ Việt Nam.
- Challenge / phần đã làm: Browser trên Mac truy cập nginx qua ClusterIP; đổi Service sang LoadBalancer 8080 → 80; dùng Traefik và Ingress host-based qua HTTP 80, kiểm tra cả host khớp/không khớp. Giữ Deployment nginx và Service backend từ các buổi trước; mentor không triển khai, sửa hoặc xóa workload thay học viên.
- Minh chứng: Browser qua ClusterIP theo xác nhận học viên; output curl LoadBalancer có 200/trang nginx. API/describe xác nhận controller, class và rule `nginx-buoi6` trỏ Service `nginx-buoi4:8080` tới ba backend Pod cổng 80. Ngày 2026-10-09 output curl `nginx.k8s.orb.local` trả 200, `sai.k8s.orb.local` trả 404; sau câu hỏi về URL Ingress, học viên xác nhận “thấy rồi nhé”. Browser qua Ingress được ghi nhận theo xác nhận này, không phải ảnh hoặc lần browser test độc lập của mentor.
- Concept / review: Phân biệt Service IP, Node IP, LB IP và cổng tương ứng; Ingress backend tham chiếu Service port, frontend controller giữ cổng riêng. Học viên trả lời đúng đổi backend port 8080 → 9000 mà URL browser giữ nguyên, 404 không phải lỗi DNS và DNS không giải quyết thiếu triển khai LoadBalancer. Mentor bổ sung HTTP Host/path và endpoint phải được cấp/công bố cùng đường mạng phù hợp; không ghi là học viên tự nêu đầy đủ field hạ tầng.
- Symptom / hint: Ban đầu vướng tên ngắn Service trên Mac và vai trò địa chỉ; hint dùng ClusterIP từ output rồi giảng lại theo từng vai trò. Không có lỗi runtime chưa xử lý; host sai 404 là kết quả mong đợi của challenge. Quy tắc mentor/AGENTS đã được bổ sung để bắt buộc đối chiếu tiện ích OrbStack với cấu hình ngoài lab.
- Giới hạn: Cloud/MetalLB, DNS ngoài lab, port-forward và đổi port sang 9000 chỉ được giải thích/tham khảo; chưa thử HTTP trực tiếp qua NodePort/LB IP, chưa kiểm thử LAN/Internet, TLS, phân phối tới mọi Pod hoặc không gián đoạn.
- Kết quả / nội dung cần ôn: Buổi 06 đạt, tổng tiến độ 6/28. Ôn sự độc lập giữa DNS, endpoint LoadBalancer, HTTP routing và cổng Service/Pod; Mac truy cập thành công không đồng nghĩa endpoint public hay production-ready.
- Tổng kết kiến thức đầy đủ: [after-study/06-truy-cap-tu-macos.md](../after-study/06-truy-cap-tu-macos.md).
- Việc tiếp theo: Chờ bắt đầu Buổi 07 — Debugging Challenge #1; vẫn `Chưa học`, chưa tạo lỗi hoặc triển khai challenge mới khi chốt buổi 6.

## Tiếp tục học với LLM

Gửi file tiến độ này, [quy tắc mentor](huong-dan-hoc-va-mentor.md), các tài liệu dùng chung và file buổi đang học theo hướng dẫn trong prompt bàn giao. Yêu cầu LLM tiếp tục từ kết quả/lỗi đang ghi ở đây, không tự giả định bạn đã hoàn thành các buổi trước.
