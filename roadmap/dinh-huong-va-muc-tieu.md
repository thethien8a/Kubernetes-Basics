# Định hướng và mục tiêu học Kubernetes cho Data Engineer

[Mục lục lộ trình](kubernetes_data_engineer_training_roadmap.md) · [Tiến độ học tập](tien-do-hoc-tap.md)

Đọc một lần trước Buổi 1. Tài liệu này giữ bối cảnh, phạm vi và tiêu chuẩn đầu ra của lộ trình.

## 1. Bối cảnh người học

Người học:

- Là Data Engineer.
- Đã hiểu Docker khá ổn.
- Linux/CLI ở mức đủ dùng.
- Linux networking còn ít kinh nghiệm hơn các phần khác.
- Chưa từng tự tạo một Kubernetes cluster từ đầu.
- Không muốn học Kubernetes theo kiểu thuộc syntax YAML.
- Không cần nhớ chính xác boilerplate manifest.
- Muốn hiểu:
  - cần resource nào;
  - field/config nào quan trọng;
  - sửa field đó thì hành vi hệ thống thay đổi ra sao;
  - debug như thế nào khi workload không hoạt động.
- Muốn học bằng cách:
  - được giao challenge;
  - tự tìm cách làm;
  - gửi kết quả cho LLM review;
  - tự debug trước;
  - chỉ nhận hint khi thực sự bí.

Người học có thể yêu cầu LLM sinh skeleton YAML hoặc command khi cần.

Điều cần đánh giá là **khả năng hiểu kiến trúc và cấu hình**, không phải khả năng nhớ cú pháp YAML.

---

## 2. Mục tiêu đào tạo

Sau lộ trình này, người học cần đạt được các năng lực sau.

### 2.1 Kubernetes fundamentals

Hiểu được các khái niệm:

- Cluster
- Control Plane
- Node
- Pod
- Container
- Deployment
- ReplicaSet
- Service
- Namespace
- Label
- Selector
- ConfigMap
- Secret
- Resource request
- Resource limit
- Job
- CronJob
- Volume
- PersistentVolume
- PersistentVolumeClaim
- StorageClass
- StatefulSet
- Ingress

Không yêu cầu thuộc cú pháp đầy đủ của manifest.

---

### 2.2 Networking

Chỉ cần đi sâu tới mức đủ để data platform hoạt động tốt.

Cần hiểu:

- Pod IP
- Service discovery
- Kubernetes DNS
- ClusterIP
- NodePort
- LoadBalancer
- Ingress
- `port`
- `targetPort`
- Traffic từ máy host vào service
- Traffic service-to-service bên trong cluster

Không cần đi sâu trong tháng đầu vào:

- CNI internals
- kube-proxy internals
- eBPF internals
- routing table chuyên sâu
- service mesh
- advanced NetworkPolicy

Mục tiêu thực tế:

> Có thể truy cập Spark UI, Airflow UI, MinIO Console, Trino UI và các UI cần thiết từ macOS.

---

### 2.3 Storage

Storage là phần cần học tương đối kỹ vì liên quan trực tiếp tới Data Engineering.

Cần hiểu:

- Container ephemeral filesystem
- Volume
- PersistentVolume
- PersistentVolumeClaim
- StorageClass
- Dynamic provisioning
- Access modes
- Reclaim behavior
- StatefulSet và persistent storage
- Tại sao database/object storage cần persistence

---

### 2.4 Data Engineering workloads

Ưu tiên:

1. Apache Spark
2. Apache Airflow
3. MinIO
4. PostgreSQL
5. Apache Iceberg
6. Trino
7. Project Nessie

---

## 3. Kiến trúc Spark mong muốn

Giai đoạn đầu sử dụng **Spark Standalone chạy bên trong Kubernetes**.

Kiến trúc mong muốn:

```text
Kubernetes Cluster
│
├── Spark Master Pod
│
├── Spark Worker Pod 1
│
├── Spark Worker Pod 2
│
└── các workload khác
```

Trong mô hình này:

- Kubernetes quản lý Pod/container.
- Spark Master vẫn là cluster manager của Spark Standalone.
- Spark Worker đăng ký với Spark Master.
- Spark application có Driver.
- Driver xin tài nguyên từ Spark Master.
- Executors chạy trên Spark Workers.

Người học phải phân biệt rõ:

```text
Kubernetes Node
!=
Spark Worker
!=
Spark Executor
!=
Spark Driver
```

Sau khi hiểu Spark Standalone on Kubernetes, có thể dành một buổi so sánh với:

```text
Spark Native Kubernetes
```

Trong Spark Native Kubernetes:

```text
spark-submit
    |
    v
Kubernetes API
    |
    +--> Driver Pod
    |
    +--> Executor Pod
    +--> Executor Pod
```

Kubernetes lúc này đóng vai trò cluster manager trực tiếp cho Spark application.

---

## 4. Môi trường local

Máy:

```text
Mac mini
Apple M4
24 GB RAM
10 CPU cores
```

Đã cài:

```text
OrbStack
```

### 4.1 Giai đoạn đầu

Ưu tiên sử dụng Kubernetes tích hợp trong OrbStack.

Lý do:

- setup nhanh;
- phù hợp với beginner;
- networking thuận tiện trên macOS;
- dễ expose các UI;
- không cần xử lý multi-node ngay lập tức.

Ban đầu chỉ cần một local Kubernetes cluster đơn giản.

Không dựng multi-node ngay.

---

### 4.2 Giai đoạn sau

Khi cần học các chủ đề:

- node scheduling;
- worker node;
- node failure;
- nodeSelector;
- affinity;
- taints/tolerations;

có thể dựng thêm một cluster bằng `kind`:

```text
1 control-plane
2 workers
```

Không cần chuyển sang kind trước khi những khái niệm trên thực sự cần thiết.

---

## 5. Các chủ đề KHÔNG ưu tiên trong tháng đầu

Không cần đi sâu:

- etcd administration
- multi-control-plane HA
- certificate rotation
- Kubernetes source code
- custom scheduler
- admission controller nâng cao
- CRD development
- Operator development
- service mesh
- advanced CNI
- advanced NetworkPolicy
- production-grade Kafka cluster
- production-grade PostgreSQL HA
- full observability stack
- CKA-style cluster administration

Có thể học sau khi hoàn thành roadmap.

---

## 6. Definition of Done

Khóa học hoàn thành khi người học có thể được giao yêu cầu:

> Dựng một data platform local trên Kubernetes.

và tự đưa ra được những quyết định như:

```text
Workload này cần Deployment hay StatefulSet?

Có cần persistent storage không?

PVC phải mount vào đâu?

Service loại nào?

Service nào chỉ cần internal?

UI nào cần expose?

Config nào dùng ConfigMap?

Credential nào dùng Secret?

Resource request/limit nên đặt khoảng nào?

Spark Master tìm Workers hay Workers tìm Master bằng endpoint nào?

Spark job truy cập MinIO endpoint nào?

Iceberg metadata/catalog đặt ở đâu?

Trino tìm Iceberg table bằng cách nào?
```

Người học **không bắt buộc** tự viết mọi YAML từ đầu mà không tra cứu.
