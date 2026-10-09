# Buổi 20 — Spark ghi dữ liệu vào MinIO

**Tuần 3 — Data Engineering workloads.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Pipeline

```text
CSV
 |
 v
Spark
 |
 v
Parquet
 |
 v
MinIO
```

## Challenge

- Spark đọc input.
- Transform đơn giản.
- Ghi Parquet vào MinIO.

## Học

- endpoint
- credential
- object storage path
- service-to-service communication

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 19](19-hai-tang-resource-management.md) · **Tiếp:** [Buổi 21 — Debugging Challenge #2](21-debugging-2.md).
