# Buổi 21 — Debugging Challenge #2

**Tuần 3 — Data Engineering workloads.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

LLM cố tình phá một số điểm:

- Worker không register Master
- Sai Spark Master URL
- Service DNS sai
- Spark UI không truy cập được
- MinIO credential sai
- Spark job không ghi được object
- Executor hoặc Worker OOM

Người học phải điều tra.

## Tiêu chí hoàn thành tuần 3

Người học có thể:

- dựng Spark Standalone;
- hiểu Master/Worker/Driver/Executor;
- expose UI;
- cấu hình resource;
- chạy Spark job;
- ghi dữ liệu vào MinIO;
- debug Spark/Kubernetes networking cơ bản.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 20](20-spark-ghi-du-lieu-vao-minio.md) · **Tiếp:** [Buổi 22 — Airflow](22-airflow.md).
