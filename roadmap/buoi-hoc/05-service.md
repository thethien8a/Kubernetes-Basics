# Buổi 05 — Service

**Tuần 1 — Kubernetes từ con số 0.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Challenge

Có ba nginx Pod.

Tạo Service phía trước chúng.

```text
Client
   |
   v
Service
   |
   +--> Pod
   +--> Pod
   +--> Pod
```

## Học

- ClusterIP
- NodePort
- LoadBalancer

## Không cần đi sâu implementation internals.

## Cần hiểu

> Service cung cấp endpoint ổn định phía trước các Pod có IP động.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 04](04-labels-va-selectors.md) · **Tiếp:** [Buổi 06 — Truy cập từ macOS](06-truy-cap-tu-macos.md).
