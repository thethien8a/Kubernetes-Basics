# Buổi 13 — PostgreSQL trên Kubernetes

**Tuần 2 — Configuration, resources và storage.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Architecture

```text
PostgreSQL Pod
   |
   +--> Secret
   |
   +--> Service
   |
   +--> PVC
```

## Challenge

Triển khai PostgreSQL sao cho:

1. Có user/password.
2. App khác trong cluster connect được.
3. Data persist.
4. Xóa Pod.
5. Pod được tạo lại.
6. Data vẫn còn.

## Có thể dùng Deployment trước để quan sát hạn chế.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 12](12-pv-pvc-storageclass.md) · **Tiếp:** [Buổi 14 — StatefulSet](14-statefulset.md).
