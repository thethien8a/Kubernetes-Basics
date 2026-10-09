# Buổi 07 — Debugging Challenge #1

**Tuần 1 — Kubernetes từ con số 0.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

LLM tạo một hệ thống có một hoặc nhiều lỗi:

- `ImagePullBackOff`
- `CrashLoopBackOff`
- Pod Pending
- port sai
- selector sai
- Service không route tới Pod

Không nói lỗi là gì.

## Người học phải chủ động dùng

```bash
kubectl get
kubectl describe
kubectl logs
kubectl get events
```

## Tiêu chí hoàn thành tuần 1

Người học có thể:

- tạo workload;
- quan sát trạng thái;
- hiểu Deployment;
- hiểu Service;
- truy cập app từ host;
- debug lỗi Kubernetes cơ bản.

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 06](06-truy-cap-tu-macos.md) · **Tiếp:** [Buổi 08 — ConfigMap](08-configmap.md).
