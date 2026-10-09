# Buổi 27 — Full Platform Debugging

**Tuần 4 — Mini Lakehouse Platform.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

Platform:

```text
                         +-------------+
                         |   Airflow   |
                         +------+------+
                                |
                                v
                    +--------------------+
                    | Spark Standalone   |
                    |                    |
                    | Master             |
                    | Worker 1           |
                    | Worker 2           |
                    +---------+----------+
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
                     phục vụ các workload
                     cần metadata/database
```

LLM cố tình tạo từ 3 tới 5 lỗi.

Ví dụ:

- Service selector sai
- PVC không mount
- credential sai
- DNS name sai
- Spark worker thiếu resource
- Trino catalog config sai
- Nessie endpoint sai
- Airflow không trigger được Spark

Người học phải debug từ symptom.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 26](26-trino.md) · **Tiếp:** [Buổi 28 — Final Challenge](28-final-challenge.md).
