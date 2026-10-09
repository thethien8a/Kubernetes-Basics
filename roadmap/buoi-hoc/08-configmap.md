# Buổi 08 — ConfigMap

**Tuần 2 — Configuration, resources và storage.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Challenge

Một application cần:

```text
DB_HOST
DB_PORT
LOG_LEVEL
```

Không hard-code vào image.

## Học

```text
ConfigMap
    |
    +--> environment variable
    |
    +--> mounted file
```

## Cần hiểu

- ConfigMap dùng cho configuration không nhạy cảm.
- Application image và runtime config nên được tách biệt.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 07](07-debugging-1.md) · **Tiếp:** [Buổi 09 — Secret](09-secret.md).
