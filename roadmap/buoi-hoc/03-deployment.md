# Buổi 03 — Deployment

**Tuần 1 — Kubernetes từ con số 0.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Challenge

Deploy nginx với:

```text
replicas = 3
```

Sau đó:

```text
delete 1 Pod
```

Quan sát Kubernetes tạo Pod thay thế.

## Mental model

```text
Desired State
replicas = 3
      |
      v
Deployment Controller
      |
      v
Actual State luôn được reconcile về 3 Pod
```

## Người học cần hiểu

- Deployment làm gì?
- ReplicaSet làm gì?
- Vì sao không nên tạo Pod trực tiếp cho workload thông thường?
- Desired state là gì?
- Reconciliation loop là gì ở mức khái niệm?

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 02](02-pod-dau-tien.md) · **Tiếp:** [Buổi 04 — Labels và Selectors](04-labels-va-selectors.md).
