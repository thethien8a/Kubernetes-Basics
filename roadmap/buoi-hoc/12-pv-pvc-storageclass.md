# Buổi 12 — PV, PVC và StorageClass

**Tuần 2 — Configuration, resources và storage.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Mental model

```text
Pod
 |
 | asks for storage
 v
PVC
 |
 v
PV
 |
 v
Physical / local storage
```

Dynamic provisioning:

```text
PVC
 |
 v
StorageClass
 |
 v
provision PV
```

## Học kỹ

- PV
- PVC
- StorageClass
- Access modes
- Dynamic provisioning
- Reclaim behavior

## Không yêu cầu nhớ syntax.

Người học phải trả lời được:

> Nếu application cần 10 GiB persistent storage thì Kubernetes abstractions nào tham gia?

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 11](11-ephemeral-filesystem-va-volume.md) · **Tiếp:** [Buổi 13 — PostgreSQL](13-postgresql.md).
