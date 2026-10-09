# Buổi 26 — Trino

**Tuần 4 — Mini Lakehouse Platform.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Architecture

```text
             Nessie
            /      \
           /        \
       Spark        Trino
           \        /
            \      /
             MinIO
               |
            Iceberg
```

## Challenge

Spark tạo Iceberg table.

Trino query chính table đó.

## Goal

```sql
SELECT *
FROM ...
```

thành công.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 25](25-nessie.md) · **Tiếp:** [Buổi 27 — Full Platform Debugging](27-full-platform-debugging.md).
