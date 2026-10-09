# Kiến trúc đích, resource budget và mental model

[Mục lục lộ trình](kubernetes_data_engineer_training_roadmap.md) · [Tiến độ học tập](tien-do-hoc-tap.md)

Dùng để đối chiếu trong quá trình học và khi làm Final Challenge, không cần triển khai toàn bộ ngay từ đầu.

## 1. Final architecture target

Một kiến trúc tham khảo:

```text
                         macOS
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
     Airflow UI                         Spark UI
          |                                 |
          +---------------+-----------------+
                          |
                          v
                 Kubernetes Services
                          |
          +---------------+----------------+
          |                                |
          v                                v
       Airflow                      Spark Standalone
                                        |
                                +-------+-------+
                                |               |
                                v               v
                            Worker 1         Worker 2
                                |
                                v
                             Spark Job
                                |
                                v
                             Iceberg
                            /       \
                           /         \
                       Nessie       MinIO
                           \         /
                            \       /
                              Trino

                         PostgreSQL
```

Đây là target học tập, không phải kiến trúc production bắt buộc.

---

## 2. Resource budget cho máy local

Máy có:

```text
24 GB RAM
10 CPU cores
```

Không nên để mọi workload dùng unrestricted resources.

Một allocation ban đầu có thể theo tư duy:

```text
Kubernetes + system overhead
~2–4 GB

Spark Master
nhỏ

Spark Workers
phần lớn RAM/CPU khi chạy job

PostgreSQL
nhỏ tới trung bình

MinIO
nhỏ tới trung bình

Airflow
nhỏ

Nessie
nhỏ

Trino
trung bình
```

Không cần chạy workload nặng.

Mục tiêu là học orchestration và integration.

Khi full stack thiếu RAM:

- giảm Spark Worker replicas;
- giảm executor memory;
- scale component xuống khi không dùng;
- không chạy job lớn;
- chỉ bật component cần thiết cho challenge.

LLM phải tránh đưa cấu hình resource quá lớn so với máy.

---

## 3. Các mental model bắt buộc phải hình thành

### Kubernetes

```text
YAML
 |
 v
Desired State
 |
 v
Kubernetes Controllers
 |
 v
Actual State
 |
 +---- reconcile ----+
```

---

### Deployment

```text
Deployment
   |
   v
ReplicaSet
   |
   v
Pods
```

---

### Service

```text
Stable Service Endpoint
        |
        v
  label selector
        |
        v
      Pods
```

---

### Persistent storage

```text
Pod lifecycle
!=
data lifecycle
```

---

### Spark Standalone

```text
Spark Master
= resource coordination for Spark cluster

Spark Worker
= offers CPU/RAM to Spark

Driver
= controls one Spark application

Executor
= executes application tasks
```

---

### Data platform

```text
Airflow
= orchestration

Spark
= compute

Iceberg
= table format

MinIO
= object storage

Nessie
= catalog/versioned metadata service

Trino
= SQL query engine

PostgreSQL
= relational database / metadata backend where needed
```
