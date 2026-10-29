# Tổng kết Bài 06 — Rollout và dừng ứng dụng (Graceful Shutdown)

[Tiến độ học tập](../tien-do-hoc-tap.md) · [Bài học gốc](../bai-hoc/06-rollout-va-shutdown.md) · [Manifest demo](../manifests/06-demo.yaml)

- **Ngày hoàn thành:** 2026-10-28 (Asia/Saigon)
- **Namespace:** `de-lab`
- **Workload:** Deployment `rollout-lab` (`RollingUpdate: maxSurge=1, maxUnavailable=0`).
- **Tiêu chí nghiệm thu:** Nắm vững cơ chế RollingUpdate; thực nghiệm thành công hiện tượng stuck rollout khi bản mới lỗi readiness; giải thích đúng ngân sách tài nguyên surge ($2 + 1 = 3$ Pods); thực hiện cứu hộ rollback thành công bằng `kubectl rollout undo`; hiểu sâu vòng đời Graceful Shutdown (`preStop`, `SIGTERM`, `SIGKILL`) và rủi ro đối với dữ liệu Data Platform.

---

## 1. Cơ chế RollingUpdate và Hai "Van Điều Tiết"

Khi cập nhật Pod template của Deployment:
- **`maxSurge` (Vượt mức cho phép):** Số Pod tối đa được tạo thêm vượt ngưỡng `spec.replicas` trong lúc rollout. Đòi hỏi cluster phải có sẵn capacity/headroom cho Pod dôi dư.
- **`maxUnavailable` (Thiếu hụt cho phép):** Số Pod cũ tối đa được phép tắt đi khi Pod mới chưa Ready.
  - Khi cấu hình **`maxUnavailable: 0`**, Kubernetes đặt an toàn dịch vụ lên hàng đầu: bắt buộc duy trì đủ 100% số Pod cũ cho tới khi Pod mới hoàn toàn `Ready: 1/1`.

```diagram
[Deployment v1 (2 Pods Ready)]
       │
       ▼ (Apply v2 với maxSurge: 1, maxUnavailable: 0)
[Sinh ReplicaSet v2 (1 Pod mới do maxSurge=1)]
       │
       ├─► Pod v2 bị lỗi Readiness (404) ──▶ Không bao giờ Ready!
       │
       ▼ (K8s ĐÓNG BĂNG ROLLOUT - STUCK)
ReplicaSet v1 (vẫn giữ 2 Pods cũ chạy bình thường)  <-- Dịch vụ KHÔNG bị gián đoạn!
ReplicaSet v2 (giữ 1 Pod lỗi Ready: 0/1)
Tổng số Pods trong cụm: 2 + 1 = 3 Pods
```

---

## 2. Vòng đời Graceful Shutdown & Cạm bẫy Data Engineer

### 2.1 Quy trình dừng Pod an toàn
1. Service lập tức **gỡ IP của Pod khỏi Endpoints** (để ngừng nhận request mới).
2. Kubelet kích hoạt hook **`lifecycle.preStop`** (nếu có cấu hình).
3. Kubelet gửi tín hiệu **`SIGTERM`** tới tiến trình chính trong container:
   - Ứng dụng có thời gian hoàn tất các request đang dang dở, commit Kafka offset, đóng transaction DB hoặc flush memory buffer xuống disk.
4. Hết hạn **`terminationGracePeriodSeconds`** (mặc định 30s): Nếu tiến trình chưa thoát, Kubelet buộc phải gửi **`SIGKILL`** ép dừng container ngay lập tức.

### 2.2 Cạm bẫy Rollback trong Data Platform
- Lệnh `kubectl rollout undo` chỉ đưa cấu hình Pod template (code/image) về bản trước đó.
- **Rollback K8s KHÔNG THỂ đảo ngược database migration hay dữ liệu đã bị ghi hỏng.** Nếu phiên bản v2 đã lỡ chạy migration làm biến đổi schema DB, việc rollback container sẽ khiến code v1 bị crash nếu không có tính tương thích ngược (backward compatibility).

---

## 3. Minh chứng Runtime thực tế

Mentor đã kiểm tra trực tiếp trạng thái live sau thí nghiệm:

### 3.1 Giai đoạn Stuck Rollout
- Lệnh theo dõi bị kẹt:
  `Waiting for deployment "rollout-lab" rollout to finish: 1 out of 2 new replicas have been updated.`
- Kiểm tra ReplicaSet:
  - `rollout-lab-6bbfc5675d` (v1 cũ): Giữ nguyên `DESIRED: 2, CURRENT: 2, READY: 2`.
  - `rollout-lab-75557d8ff5` (v2 mới): Giữ `DESIRED: 1, CURRENT: 1, READY: 0`.
  - Hai Pod cũ có tuổi đời liên tục (Age 10m) không hề bị khởi động lại hay xóa nhầm!

### 3.2 Giai đoạn Rollback Cứu hộ (`kubectl rollout undo`)
- ReplicaSet lỗi v2 (`75557d8ff5`) được hạ về `DESIRED: 0, CURRENT: 0, READY: 0`.
- ReplicaSet cũ v1 (`6bbfc5675d`) được khôi phục thành active: `DESIRED: 2, CURRENT: 2, READY: 2`.
- Rollout status báo thành công ngay lập tức: `deployment "rollout-lab" successfully rolled out`.
