# Buổi 19 — Hai tầng resource management

**Tuần 3 — Data Engineering workloads.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

Đây là buổi quan trọng.

## Kubernetes layer

```text
Spark Worker Pod
requests / limits
```

## Spark layer

```text
worker cores
worker memory
executor cores
executor memory
```

## Challenge

Phân tích các case:

```text
Kubernetes limit = 4 CPU
Spark Worker advertises = 8 cores
```

và:

```text
Kubernetes memory limit = 4 GiB
Spark Worker advertises = 8 GiB
```

## Mục tiêu

Hiểu việc khai báo resource ở Spark không thể vượt qua physical/runtime constraints của Pod.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 18](18-submit-spark-application.md) · **Tiếp:** [Buổi 20 — Spark ghi dữ liệu vào MinIO](20-spark-ghi-du-lieu-vao-minio.md).
