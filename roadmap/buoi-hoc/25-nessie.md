# Buổi 25 — Nessie

**Tuần 4 — Mini Lakehouse Platform.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Architecture

```text
          Nessie
            ^
            |
      catalog / metadata
            |
          Spark
            |
            v
          MinIO
```

## Học

- Catalog
- Table metadata
- Namespace/table discovery
- Versioned catalog ở mức khái niệm

## Câu hỏi quan trọng

> Data nằm ở đâu?

> Table metadata nằm ở đâu?

> Catalog có vai trò gì?

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 24](24-apache-iceberg.md) · **Tiếp:** [Buổi 26 — Trino](26-trino.md).
