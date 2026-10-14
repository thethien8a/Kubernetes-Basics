# Lộ trình đào tạo Kubernetes cho Data Engineer — 1 tháng

**Đối tượng:** Data Engineer muốn học Kubernetes theo hướng thực hành  
**Thời lượng:** 1 tháng, khoảng 7 buổi/tuần, tổng cộng ~28 buổi  
**Phương pháp:** Ôn kỹ lý thuyết và cấu hình → kiểm tra hiểu → tự thực hành từng bước → debug/review, LLM đóng vai trò mentor/reviewer\
**Môi trường chính:** macOS trên Mac mini Apple M4, 24 GB RAM, 10 CPU cores  
**Container runtime / local platform:** OrbStack  
**Mục tiêu cuối:** Tự dựng và vận hành được một mini data platform trên Kubernetes

Lộ trình đã được tách thành **28 file buổi học**, mỗi file là một phần nhỏ có thể mở riêng. File này là mục lục; nội dung challenge, câu hỏi và tiêu chí cuối tuần nằm trong các file tương ứng, không bị rút bỏ.

**Theo dõi việc học tại [tien-do-hoc-tap.md](tien-do-hoc-tap.md).**

## Cách dùng

1. Đọc [định hướng và mục tiêu](dinh-huong-va-muc-tieu.md) cùng [hướng dẫn học và mentor](huong-dan-hoc-va-mentor.md) trước Buổi 1.
2. Học tuần tự từ Buổi 01 đến Buổi 28. Trước mỗi phần thực hành, ôn kỹ lý thuyết/kiến thức nền liên quan, đọc và giải thích cấu hình tương ứng, dự đoán hành vi và kiểm tra hiểu; sau đó mới giao challenge → tự triển khai từng bước → quan sát/debug → review/tổng kết. Chia phần dài thành khối nhỏ, không chỉ giao YAML/lệnh rồi mới giảng ở review.
3. Sau review, cập nhật checklist, ngày học, minh chứng và lỗi còn vướng trong [file tiến độ](tien-do-hoc-tap.md).
4. Tra [kiến trúc, resource budget và mental model](kien-truc-va-mental-model.md) khi cần đối chiếu; không cần dựng full stack từ đầu.
5. Khi chuyển sang LLM khác, dùng prompt bàn giao trong [hướng dẫn mentor](huong-dan-hoc-va-mentor.md). LLM có quyền truy cập tự đọc file tiến độ/buổi đang học và kiểm tra kết quả bằng công cụ chỉ đọc; chỉ yêu cầu học viên cung cấp tài liệu/output tối thiểu đã loại dữ liệu nhạy cảm khi không thể tự truy cập.

Mốc 4 tuần là lịch tham khảo. Một buổi có thể chia thành nhiều lần học; chỉ chuyển tiếp khi đã hoàn thành challenge và hiểu được phần trọng tâm, không chạy theo số ngày.

## Tài liệu dùng chung

| Tài liệu | Nội dung | Khi nào dùng |
|---|---|---|
| [Định hướng và mục tiêu](dinh-huong-va-muc-tieu.md) | Bối cảnh người học, năng lực cần đạt, Spark Standalone vs Native Kubernetes, môi trường local, phạm vi và Definition of Done | Trước Buổi 1 và lúc nghiệm thu |
| [Hướng dẫn học và mentor](huong-dan-hoc-va-mentor.md) | Lý thuyết/cấu hình trước thực hành, không học thuộc YAML/kubectl, hint ladder cho debug, format review, quy tắc LLM và prompt tiếp tục | Trước khi học và khi mở hội thoại mới |
| [Kiến trúc và mental model](kien-truc-va-mental-model.md) | Kiến trúc cuối khóa, budget máy 24 GB RAM / 10 cores và các mô hình tư duy cần hình thành | Tra cứu trong khóa, đặc biệt Tuần 3–4 |
| [Tiến độ học tập](tien-do-hoc-tap.md) | Checklist 28 buổi, trạng thái/ngày học/minh chứng, lỗi còn vướng, nhật ký và nghiệm thu | Cập nhật sau mỗi lần học |

## Tuần 1 — Kubernetes từ con số 0

Mục tiêu:

> Có thể đọc trạng thái cluster, deploy workload cơ bản, expose service và debug lỗi đơn giản.

| Buổi | Phần học |
|---|---|
| 01 | [Kubernetes cluster đầu tiên](buoi-hoc/01-cluster-dau-tien.md) |
| 02 | [Pod đầu tiên](buoi-hoc/02-pod-dau-tien.md) |
| 03 | [Deployment](buoi-hoc/03-deployment.md) |
| 04 | [Labels và Selectors](buoi-hoc/04-labels-va-selectors.md) |
| 05 | [Service](buoi-hoc/05-service.md) |
| 06 | [Truy cập từ macOS vào Kubernetes](buoi-hoc/06-truy-cap-tu-macos.md) |
| 07 | [Debugging Challenge #1 và kiểm tra cuối tuần](buoi-hoc/07-debugging-1.md) |

## Tuần 2 — Configuration, resources và storage

Mục tiêu:

> Chạy được stateful workload có persistent data.

| Buổi | Phần học |
|---|---|
| 08 | [ConfigMap](buoi-hoc/08-configmap.md) |
| 09 | [Secret](buoi-hoc/09-secret.md) |
| 10 | [CPU và Memory](buoi-hoc/10-cpu-va-memory.md) |
| 11 | [Ephemeral filesystem và Volume](buoi-hoc/11-ephemeral-filesystem-va-volume.md) |
| 12 | [PV, PVC và StorageClass](buoi-hoc/12-pv-pvc-storageclass.md) |
| 13 | [PostgreSQL trên Kubernetes](buoi-hoc/13-postgresql.md) |
| 14 | [StatefulSet và kiểm tra cuối tuần](buoi-hoc/14-statefulset.md) |

## Tuần 3 — Data Engineering workloads

Mục tiêu:

> Dựng được các thành phần compute và storage cơ bản của một data platform.

| Buổi | Phần học |
|---|---|
| 15 | [MinIO](buoi-hoc/15-minio.md) |
| 16 | [Spark Standalone on Kubernetes](buoi-hoc/16-spark-standalone.md) |
| 17 | [Spark networking và UI](buoi-hoc/17-spark-networking-va-ui.md) |
| 18 | [Submit Spark application](buoi-hoc/18-submit-spark-application.md) |
| 19 | [Hai tầng resource management](buoi-hoc/19-hai-tang-resource-management.md) |
| 20 | [Spark ghi dữ liệu vào MinIO](buoi-hoc/20-spark-ghi-du-lieu-vao-minio.md) |
| 21 | [Debugging Challenge #2 và kiểm tra cuối tuần](buoi-hoc/21-debugging-2.md) |

## Tuần 4 — Mini Lakehouse Platform

Mục tiêu:

> Kết nối các thành phần thành một data platform hoàn chỉnh.

| Buổi | Phần học |
|---|---|
| 22 | [Airflow](buoi-hoc/22-airflow.md) |
| 23 | [Airflow trigger Spark](buoi-hoc/23-airflow-trigger-spark.md) |
| 24 | [Apache Iceberg](buoi-hoc/24-apache-iceberg.md) |
| 25 | [Nessie](buoi-hoc/25-nessie.md) |
| 26 | [Trino](buoi-hoc/26-trino.md) |
| 27 | [Full Platform Debugging](buoi-hoc/27-full-platform-debugging.md) |
| 28 | [Final Challenge](buoi-hoc/28-final-challenge.md) |

## Bắt đầu

Mở [Buổi 01 — Kubernetes cluster đầu tiên](buoi-hoc/01-cluster-dau-tien.md). Trước thực hành, học khái niệm/thành phần cluster và cấu hình truy cập/context; sau đó enable Kubernetes trên OrbStack, quan sát cluster và đối chiếu với phần đã học. Buổi đầu không viết YAML.

Khi hoàn thành, ghi kết quả vào [tiến độ học tập](tien-do-hoc-tap.md), rồi chuyển sang Buổi 02.
