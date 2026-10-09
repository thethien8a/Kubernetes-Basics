# Buổi 16 — Spark Standalone on Kubernetes

**Tuần 3 — Data Engineering workloads.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Architecture

```text
               Kubernetes

          +----------------+
          | Spark Master   |
          +-------+--------+
                  |
          spark://master
                  |
        +---------+---------+
        |                   |
        v                   v
+---------------+   +---------------+
| Spark Worker  |   | Spark Worker  |
+---------------+   +---------------+
```

## Challenge

Dựng:

```text
1 Spark Master
2 Spark Workers
```

## Cần hiểu

- Spark Master là gì?
- Spark Worker là gì?
- Kubernetes Node khác Spark Worker như thế nào?
- Worker tìm Master qua Service như thế nào?

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 15](15-minio.md) · **Tiếp:** [Buổi 17 — Spark networking và UI](17-spark-networking-va-ui.md).
