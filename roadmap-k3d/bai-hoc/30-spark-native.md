# Bài 30 — Spark Native Kubernetes

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](29-postgresql.md) · [Tiếp](31-airflow.md)

**Đầu vào:** Job/process, RBAC, image distribution, resources và networking. **Đầu ra:** biết Spark cần quyền/năng lực nào từ cluster và đọc được cấu hình tạo Driver/Executor Pods.

## 1. Khối kiến thức

- Spark Standalone trong khóa cũ dùng Master/Worker daemons. Spark Native Kubernetes dùng Kubernetes làm cluster manager; chọn cluster deploy mode để Driver nằm trong Pod và tạo Executor Pods qua API. Không cần dựng Standalone Master/Workers cho mode này.
- Identity submit ứng dụng và ServiceAccount của Driver là hai danh tính ở hai giai đoạn; executor identity cũng phải đọc theo cấu hình/version. Driver cần permissions đúng resource/verb/namespace, không cần cluster-admin mặc định.
- Spark heap/cores/concurrency khác Pod requests/limits. Memory overhead, Python/off-heap và scratch phải được tính; đặt `executor.memory` không có nghĩa toàn bộ container chỉ dùng đúng bằng heap đó.
- Executor Pod tồn tại chưa chứng minh task chạy ở đó. Driver/Executors cần network với nhau, image/code/dependencies và dữ liệu input/output phù hợp. Spark Operator là lựa chọn bổ sung có CRD/controller, không điều kiện của native `spark-submit`.

## 2. Đọc cấu hình

| Cấu hình Spark, không phải field Kubernetes | Đối chiếu resource/runtime |
|---|---|
| `--master` đích Kubernetes API, `--deploy-mode cluster` | Chọn cluster manager và vị trí Driver, không trỏ Spark RPC 7077 của Standalone. |
| `spark.kubernetes.context`, `spark.kubernetes.namespace` | Tránh submit vào context/namespace cũ. |
| `spark.kubernetes.container.image` | Driver/Executors có image tương thích, script/dependencies cần được phân phối. |
| `spark.kubernetes.authenticate.driver.serviceAccountName` | Runtime identity của Driver trong cluster mode; kiểm Role/Binding tương ứng. |
| `spark.executor.instances`, `spark.executor.memory`, `spark.executor.memoryOverhead` | Đọc Pod resources render/live, không lấy số Spark cores làm bằng chứng CPU vật lý đã cấp. |

## 3. Kiểm tra hiểu trước lab

1. Driver có thể gọi API nhưng bị Forbidden khi tạo Executor Pods. Điều cần kiểm? **A.** Runtime identity/RBAC và namespace. **B.** Mật khẩu PostgreSQL. **C.** Cổng Spark Master 7077.
2. Hai Executor Pods Ready có chứng minh cả hai đã xử lý task không? **A.** Có. **B.** Không, cần evidence task execution. **C.** Có nếu khác node.

## 4. Thực hành và bằng chứng

1. Chọn/pin Spark image/version, kiểm ARM64 và API dependencies. Chuẩn bị app nhỏ, kỳ vọng tính độc lập: các giá trị `[3, 8, 11, 20]`, lọc số chẵn rồi nhân 2, tổng 56. Chưa dùng S3/JAR connector để tránh trộn lỗi.
2. Học viên chuẩn bị quyền namespace hẹp và submit cluster mode vào lab mới, yêu cầu hai Executors với placement đã giải thích theo Spark version. Đọc Driver/Executor Pod specs, image và node thực tế.
3. Kiểm đúng app/Driver UID, completion/exit, kết quả 56 và task evidence trên Executor. Để xác nhận multi-node execution, bố trí đủ partitions/công việc nhỏ có giới hạn và kiểm tasks trên cả hai agents; nếu chưa thấy thì chỉ ghi allocation, không tự nhận đã phân tán.

**Đạt khi:** ứng dụng cho kết quả đúng, có execution evidence phù hợp mục tiêu multi-node và bản yêu cầu RBAC/resources/images/network đầy đủ. Không dùng một Job Complete bên ngoài làm bằng chứng thay Driver/application outcome.

## 5. Cần DevOps và giới hạn lab

- Cần namespace/quota, Driver SA/Role, registry/image platform, network Driver–Executor/API, scratch và log retention. Nếu dùng object storage sau này, cần endpoint/TLS/credential/IAM và connector đúng version riêng.
- Spark chạy trên hai node containers không benchmark distributed compute thật. Không cài Operator hay mở public Driver UI/RPC chỉ để submit thành công.

**Nguồn:** [Spark on Kubernetes](https://spark.apache.org/docs/latest/running-on-kubernetes.html). Đổi sang docs đúng Spark version khi chuẩn bị lab; không dùng `latest` làm image pin.
