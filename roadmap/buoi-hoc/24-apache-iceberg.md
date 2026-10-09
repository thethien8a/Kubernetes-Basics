# Buổi 24 — Apache Iceberg

**Tuần 4 — Mini Lakehouse Platform.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Chuyển từ

```text
Spark
 |
 v
Parquet files
```

sang:

```text
Spark
 |
 v
Iceberg Table
 |
 v
Object Storage
```

## Học

Phân biệt:

```text
Compute Engine
Table Format
Object Storage
Catalog
```

## Người học phải trả lời được

- Iceberg có lưu data không?
- MinIO có biết schema table không?
- Spark đóng vai trò gì?
- Metadata Iceberg phục vụ việc gì?

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 23](23-airflow-trigger-spark.md) · **Tiếp:** [Buổi 25 — Nessie](25-nessie.md).
