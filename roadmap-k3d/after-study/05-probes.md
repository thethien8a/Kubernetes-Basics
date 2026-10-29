# Tổng kết Bài 05 — Startup, readiness và liveness probes

[Tiến độ học tập](../tien-do-hoc-tap.md) · [Bài học gốc](../bai-hoc/05-probes.md) · [Manifest demo](../manifests/05-demo.yaml)

- **Ngày hoàn thành:** 2026-10-28 (Asia/Saigon)
- **Namespace:** `de-lab`
- **Workload:** Deployment `probe-lab` (Nginx container có đủ Startup, Readiness, Liveness).
- **Tiêu chí nghiệm thu:** Thực nghiệm và đối chiếu thành công hai trạng thái lỗi; chứng minh Readiness fail không làm restart container (`RESTARTS: 0`) và giữ an toàn cho Rolling Update; chứng minh Liveness fail khiến Kubelet kill container liên tục dẫn tới `CrashLoopBackOff`; hiểu rõ hiểm họa Restart Storm trong Data Platform.

---

## 1. So sánh cốt lõi: Readiness Probe vs Liveness Probe

| Tiêu chí | Readiness Probe | Liveness Probe |
|---|---|---|
| **Câu hỏi then chốt** | *"Ứng dụng có sẵn sàng nhận traffic lúc này không?"* | *"Ứng dụng còn sống bình thường hay bị deadlock/treo?"* |
| **Hành vi khi FAIL** | **KHÔNG restart container**; Pod chuyển `READY: False`; rút IP khỏi Service Endpoints | **Kubelet KILL container ngay lập tức**; tăng `RESTARTS`; vào `CrashLoopBackOff` |
| **Mục đích sử dụng** | **Gating Traffic**: Chờ nạp dữ liệu/cache, bảo vệ người dùng không nhận lỗi kết nối | **Phục hồi tiến trình**: Khắc phục các lỗi deadlock nội tại mà việc restart có thể sửa được |
| **Cảnh báo Data Platform** | Cho phép kiểm tra trạng thái dependency nếu app không thể phục vụ | **TUYỆT ĐỐI KHÔNG** trỏ vào database bên ngoài (tránh bão restart storm) |

---

## 2. Minh chứng Runtime thực tế

Mentor đã kiểm tra trực tiếp các Pod trong namespace `de-lab`:

### 2.1 Minh chứng 1 — Readiness Fail (`path: /not-found`)
- Pod `probe-lab-5ddff599c9-vshfp`:
  - `STATUS: Running`
  - `READY: 0/1 (Ready: False)`
  - **`RESTARTS: 0`**
  - **Sự kiện Kubelet:**
    `Warning Unhealthy: Readiness probe failed: HTTP probe failed with statuscode: 404`
  - **Phát hiện Rolling Update:** Deployment tự động bảo vệ hệ thống: vì Pod mới không Ready, K8s tạm dừng rollout và **giữ nguyên Pod cũ** (`probe-lab-7d9cb8b7f5-rk924`), không làm gián đoạn dịch vụ.

### 2.2 Minh chứng 2 — Liveness Fail (`path: /deadlock`)
- Pod `probe-lab-d7584f4b-d2lws`:
  - **`RESTARTS: 5`**
  - `STATUS: CrashLoopBackOff`
  - **Sự kiện Kubelet:**
    ```text
    Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 404
    Normal   Killing    Container web failed liveness probe, will be restarted
    Warning  BackOff    Back-off restarting failed container web in pod probe-lab-...
    ```

---

## 3. Bài học thiết kế cho Data Engineer

1. **Ứng dụng nạp dữ liệu nặng (Spark, Airflow, JVM):** Luôn dùng `startupProbe` với `failureThreshold` và `periodSeconds` đủ lớn để ứng dụng có 1–2 phút khởi động mà không bị Liveness probe kill nhầm.
2. **Khác biệt giữa Running và Ready:** Một Pod ở trạng thái `Running` chỉ có nghĩa là tiến trình Linux đã bật. Chỉ khi `Ready: 1/1` thì ứng dụng mới thực sự sẵn sàng xử lý dữ liệu và nhận traffic từ Service.
