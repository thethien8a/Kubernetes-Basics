# Tổng kết Bài 04 — Pod, controller và loại workload

[Tiến độ học tập](../tien-do-hoc-tap.md) · [Bài học gốc](../bai-hoc/04-pod-va-controller.md) · [Manifest demo](../manifests/04-demo.yaml)

- **Ngày hoàn thành:** 2026-10-28 (Asia/Saigon)
- **Namespace:** `de-lab`
- **Workload thí nghiệm:** Pod trần `standalone-worker` và Deployment `metadata-api`.
- **Tiêu chí nghiệm thu:** Chứng minh được sự khác biệt cốt tử giữa Naked Pod và Pod do Controller quản lý qua hành vi xóa Pod; xác nhận Pod thay thế có UID, tên và IP mới; Endpoints tự động cập nhật; phân loại đúng 5 loại workload trong Data Engineering.

---

## 1. Kiến thức cốt lõi đã làm chủ

### 1.1 Khác biệt bản chất: Naked Pod vs Controller-managed Pod

| Đặc điểm | Naked Pod (`kind: Pod`) | Pod do Controller quản lý (`Deployment`) |
|---|---|---|
| **Ai quản lý?** | Trực tiếp API Server & Kubelet, **không có Controller** | `kube-controller-manager` (thông qua `ReplicaSetController`) |
| **Khi bị xóa / Node sập?** | **Chết vĩnh viễn**, không có bất kỳ ai tự sinh lại | Controller phát hiện `actual < desired`, **tự động sinh Pod mới bù vào** |
| **Định danh Pod thay thế** | Không có | Pod mới có **UID mới, Tên mới, IP mạng mới** |
| **Khuyến nghị môi trường** | Chỉ dùng để debug tạm thời ngắn hạn | **Bắt buộc dùng Controller** cho mọi workload chính thức |

### 1.2 Bảng phân loại 5 loại Workload chính cho Data Engineering

1. **`Deployment`**: Dành cho dịch vụ không trạng thái (stateless), chạy liên tục (continuous), Pod có thể thay thế nhau (API Metadata, Airflow Webserver).
2. **`StatefulSet`**: Dành cho dịch vụ có trạng thái (stateful), cần định danh mạng cố định theo thứ tự (`-0`, `-1`) và gắn chặt với volume lưu trữ (PostgreSQL, Kafka, ZooKeeper).
3. **`Job`**: Dành cho tác vụ batch chạy một lần tới khi hoàn thành (`exit 0`) rồi dừng (Spark submit, dbt run, DB migration).
4. **`CronJob`**: Lên lịch tự động sinh ra các **Job** định kỳ theo cron expression (chạy ETL 01:00 AM hằng ngày).
5. **`DaemonSet`**: Chạy đúng 1 Pod trên mỗi node để làm nhiệm vụ nền tảng (thu thập log Fluentbit, metrics Node Exporter).

---

## 2. Minh chứng Runtime thực tế

### 2.1 Thí nghiệm xóa Naked Pod
- Khi xóa `pod/standalone-worker`, Pod bị gỡ bỏ hoàn toàn khỏi cluster và không xuất hiện lại.

### 2.2 Thí nghiệm xóa Pod của Deployment
- Xóa Pod cũ: `metadata-api-7cc6644d8d-gpxwj` (IP: `10.42.3.3`).
- Controller lập tức sinh Pod mới: `metadata-api-7cc6644d8d-hgvj9`:
  - **UID mới:** `6869f3bd-0019-465b-99f0-b26b87d5b869` (khác hoàn toàn UID cũ).
  - **IP mới:** `10.42.3.5` (cấp trên node `k3d-de-k3d-agent-0`).
- **Service Endpoints tự động cập nhật:**
  - Lệnh `kubectl get endpoints -n de-lab metadata-api-svc` tự động gỡ IP cũ `10.42.3.3` và bổ sung IP mới `10.42.3.5`.
  - Danh sách endpoints hiện tại: `10.42.1.4:80, 10.42.3.5:80`.
