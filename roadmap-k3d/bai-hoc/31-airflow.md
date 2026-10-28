# Bài 31 — Airflow và nơi thực thi task

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](30-spark-native.md) · [Tiếp](32-tong-hop.md)

**Đầu vào:** Helm, DB, RBAC, config/Secret, networking. **Đầu ra:** đọc được dependency của Airflow và phân biệt Pod chạy Airflow với Pod chạy task.

## 1. Khối kiến thức

- Airflow điều phối DAG/task state; metadata DB giữ trạng thái điều phối, không thay nơi lưu dataset. Với bản Airflow được chọn, đọc đúng vai trò Scheduler, DAG Processor, API/UI và migration trước khi cài.
- LocalExecutor chạy task bằng processes cùng môi trường Scheduler; ít thành phần nhưng chia sẻ resources. KubernetesExecutor tạo Pod cho task, cần provider/config/API permissions và có startup overhead. Executor logic không phải một daemon độc lập bắt buộc phải cài riêng.
- Chạy Airflow trong Kubernetes không tự chọn KubernetesExecutor. KubernetesPodOperator là operator để một task tạo/chạy Pod, khác cơ chế executor toàn hệ thống; chưa cần triển khai cả hai cách trong cùng bài.
- DAG distribution, task image, logs sau khi task Pod mất, credential và database persistence là các dependency riêng. UI mở được không chứng minh task đã chạy hoặc logs được giữ lâu dài.

## 2. Đọc cấu hình

| Khối cấu hình | Điều cần lần theo |
|---|---|
| Airflow `[core] executor` và chart values tương ứng | Xác định nơi task chạy; đọc render/config theo đúng chart/app version. |
| KubernetesExecutor provider config và Pod template | Namespace, image, SA, resources, volumes/refs; không chép template của version khác mà bỏ schema check. |
| Metadata database connection / Secret reference | Database user khác UI user và Kubernetes identity; không dump URI có password. |
| DAG/log distribution và persistence | Code có ở Pod thực thi không; logs xem bằng đường nào và còn sau Pod deletion không? |
| Migration Jobs/init waits và UI Service/Ingress | Đọc install lifecycle, health và đường truy cập; không áp `--wait` máy móc. |

## 3. Kiểm tra hiểu trước lab

1. Airflow Scheduler chạy trong Pod, dùng LocalExecutor. Mỗi task có tự được một Pod riêng không? **A.** Có. **B.** Không. **C.** Chỉ khi DAG có hai tasks.
2. Chọn KubernetesExecutor nhưng task image không có DAG/dependencies đúng. Chỉ cấp thêm cluster-admin có giải quyết đúng vấn đề không? **A.** Có. **B.** Tăng replicas là đủ. **C.** Không, cần sửa phân phối code/image/config tương ứng.

## 4. Thực hành và bằng chứng

1. Chia bài thành ba lượt: đọc kiến trúc/dependencies → đọc/render chart và executor → chạy task/kiểm evidence. Pin app/chart/provider tương thích ARM64; chọn budget bằng số đo, không chạy đồng thời các workload nặng trước đó.
2. Dùng một release Airflow mới với KubernetesExecutor để kiểm mối liên hệ API/Pod; LocalExecutor là phương án so sánh lý thuyết/kinh nghiệm cũ, không bắt dựng hai platform. Học viên tự chuẩn bị DB/credentials/DAG distribution đã giải thích và triển khai.
3. Chạy DAG hai task nhỏ, có marker riêng theo run; kiểm task instances, task Pod UID/node/image/SA, kết quả mong đợi và đường xem logs. Giữ evidence trước cleanup, không trigger Spark hoặc cài cả lakehouse trong bài này.

**Đạt khi:** chứng minh task chạy ở đâu, phân biệt trạng thái DAG với Pod và lập hợp đồng DB/RBAC/images/DAGs/logs/network. Phần retention chưa thử sau Pod deletion phải ghi chưa kiểm chứng.

## 5. Cần DevOps và giới hạn lab

- Cần chart/provider được hỗ trợ, task SA/namespace/quota, task image registry, metadata DB, DAG distribution, log backend, UI DNS/TLS/auth và secret mechanism. Không yêu cầu RWX chỉ vì một chart ví dụ dùng chung filesystem.
- Local-path và một DB instance không chứng minh scheduler/task/log HA. Tăng parallelism không cấp thêm tài nguyên và không tự scale nodes.

**Nguồn:** [Airflow executors](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html), [KubernetesExecutor](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/kubernetes_executor.html), [Airflow Helm chart](https://airflow.apache.org/docs/helm-chart/stable/index.html).
