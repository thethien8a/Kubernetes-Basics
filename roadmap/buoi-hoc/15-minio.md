# Buổi 15 — MinIO

**Tuần 3 — Data Engineering workloads.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Architecture

```text
MinIO
 |
 +--> Service
 |
 +--> Persistent Storage
```

## Challenge

Triển khai MinIO.

Phải truy cập được:

```text
MinIO API
MinIO Console
```

từ Mac khi phù hợp.

## Cần hiểu

- Object storage khác filesystem thế nào ở mức DE.
- MinIO data phải persist.
- Service nội bộ và endpoint bên ngoài khác nhau thế nào.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 14](14-statefulset.md) · **Tiếp:** [Buổi 16 — Spark Standalone](16-spark-standalone.md).
