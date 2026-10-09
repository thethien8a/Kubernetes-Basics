# Buổi 10 — CPU và Memory

**Tuần 2 — Configuration, resources và storage.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Học

```text
requests
limits
```

## Challenge

Thử các case:

```text
request RAM quá cao
CPU limit thấp
memory limit thấp
```

Quan sát:

- Pending
- OOMKilled
- CPU throttling ở mức khái niệm

## Người học cần phân biệt

```text
request
=> scheduler dùng để quyết định placement

limit
=> giới hạn runtime container
```

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 09](09-secret.md) · **Tiếp:** [Buổi 11 — Ephemeral filesystem và Volume](11-ephemeral-filesystem-va-volume.md).
