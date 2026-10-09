# Buổi 28 — Final Challenge

**Tuần 4 — Mini Lakehouse Platform.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

LLM chỉ đưa requirement.

Không đưa sẵn full YAML.

## Requirement

Dựng local data platform trên Kubernetes gồm:

```text
PostgreSQL
Airflow
Spark Standalone
  - 1 Master
  - 2 Workers
MinIO
Apache Iceberg
Nessie
Trino
```

## Yêu cầu kỹ thuật

### Storage

Các workload cần persistence phải có persistent storage phù hợp.

### Networking

Các service nội bộ phải giao tiếp bằng Kubernetes service discovery.

Các UI quan trọng phải truy cập được từ Mac:

- Spark UI
- Airflow UI
- MinIO Console
- Trino UI nếu dùng

### Configuration

Không hard-code credential trong container image.

Sử dụng:

```text
ConfigMap
Secret
```

khi phù hợp.

### Resource management

Các workload phải có:

```text
requests
limits
```

hợp lý với máy 24 GB RAM / 10 cores.

Không được phân bổ resource một cách phi thực tế.

### Data pipeline

Ít nhất một flow:

```text
Airflow
   |
   v
Spark
   |
   v
Iceberg Table
   |
   +--> MinIO
   |
   +--> Nessie
   |
   v
Trino query
```

---

Đối chiếu [kiến trúc và resource budget](../kien-truc-va-mental-model.md), sau đó review theo [Definition of Done](../dinh-huong-va-muc-tieu.md).

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) và checklist nghiệm thu cuối khóa.

**Trước:** [Buổi 27](27-full-platform-debugging.md).
