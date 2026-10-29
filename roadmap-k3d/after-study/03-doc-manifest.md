# Tổng kết Bài 03 — Đọc manifest và lần theo tham chiếu

[Tiến độ học tập](../tien-do-hoc-tap.md) · [Bài học gốc](../bai-hoc/03-doc-manifest.md) · [Manifest demo](../manifests/03-demo.yaml)

- **Ngày hoàn thành:** 2026-10-28 (Asia/Saigon)
- **Namespace:** `de-lab`
- **Tài nguyên triển khai:** Deployment `metadata-api` (2 replicas), Service `metadata-api-svc` (ClusterIP).
- **Tiêu chí nghiệm thu:** Đọc đúng cấu trúc 4 tầng manifest; lần đúng chuỗi sở hữu `Deployment ──▶ ReplicaSet ──▶ Pod` qua `ownerReferences`; giải thích đúng liên kết nhãn `Service.spec.selector ──▶ Pod.metadata.labels` và chỉ ra các giá trị mặc định được K8s tự động bổ sung.

---

## 1. Kiến thức cốt lõi đã làm chủ

### 1.1 Cấu trúc 4 tầng của một Object Kubernetes

Mọi manifest chuẩn đều gồm:
1. `apiVersion` & `kind`: Xác định schema và loại đối tượng (ví dụ `apps/v1` + `Deployment`, `v1` + `Service`).
2. `metadata`: Thông tin nhận diện (`name`, `namespace`, `labels`, `annotations`, `uid`).
3. `spec`: **Desired State** do người dùng mô tả.
4. `status`: **Actual State** do Controller quan sát và cập nhật thực tế.

### 1.2 Ba vị trí đặt Label trong Deployment & Sợi dây liên kết tới Service

```diagram
┌────────────────────────────────────────────────────────┐
│ Deployment: metadata-api                               │
│   metadata.labels: { team: data }                      │ ── (1) Nhãn quản lý Deployment (chỉ để phân loại)
│   spec.selector.matchLabels:                           │
│     app: metadata-api                                  │ ── (2) Bộ lọc chọn Pod để quản lý
│   spec.template:                                       │
│     metadata.labels:                                   │
│       app: metadata-api                                │ ── (3) Nhãn in lên từng Pod khi sinh ra
│       tier: backend                                    │
└────────────────────────────────────────────────────────┘
                           ▲
                           │ (Khớp nhãn trực tiếp)
┌──────────────────────────┴─────────────────────────────┐
│ Service: metadata-api-svc                              │
│   spec.selector:                                       │
│     app: metadata-api                                  │ ── (4) Service chỉ tìm Pod có nhãn này để gom IP
└────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> - `Deployment.spec.selector.matchLabels` **bắt buộc phải khớp** với `Deployment.spec.template.metadata.labels`.
> - `Service.spec.selector` **kết nối trực tiếp tới Pod labels**, không liên quan tới nhãn ngoài của Deployment.

### 1.3 Chuỗi sở hữu (OwnerReferences Chain)

Khi apply một Deployment, hệ thống không tạo Pod trực tiếp mà thông qua tầng trung gian:
$$\text{Deployment} \xrightarrow{\text{sở hữu}} \text{ReplicaSet} \xrightarrow{\text{sở hữu}} \text{Pods}$$

Minh chứng thực tế quan sát qua trường `metadata.ownerReferences`:
- Pod `metadata-api-7cc6644d8d-gpxwj` có owner là: `ReplicaSet/metadata-api-7cc6644d8d`
- ReplicaSet `metadata-api-7cc6644d8d` có owner là: `Deployment/metadata-api`

---

## 2. Giá trị mặc định được K8s tự động bổ sung (Live vs Declared)

Khi so sánh file YAML khai báo với đối tượng live trong cluster (`kubectl get ... -o yaml`), Kubernetes đã tự động inject các trường mặc định quan trọng:
1. **Deployment strategy:**
   ```yaml
   strategy:
     type: RollingUpdate
     rollingUpdate:
       maxSurge: 25%
       maxUnavailable: 25%
   ```
2. **Pod runtime defaults:**
   - `restartPolicy: Always`: Tự động khởi động lại container nếu tiến trình thoát.
   - `dnsPolicy: ClusterFirst`: Ưu tiên phân giải tên miền qua CoreDNS nội bộ của cluster.
   - `terminationGracePeriodSeconds: 30`: Chờ 30 giây cho container dọn dẹp trước khi gửi tín hiệu `SIGKILL`.

---

## 3. Minh chứng Runtime

- **Namespace `de-lab`:** Hoạt động bình thường.
- **Pods:**
  - `metadata-api-7cc6644d8d-gpxwj` (Node: `k3d-de-k3d-agent-0`, IP: `10.42.3.3`, Status: `Running 1/1`)
  - `metadata-api-7cc6644d8d-r8j9p` (Node: `k3d-de-k3d-agent-1`, IP: `10.42.1.4`, Status: `Running 1/1`)
- **Service & Endpoints:**
  - Service `metadata-api-svc` (ClusterIP: `10.43.133.161:80/TCP`)
  - Endpoints gom chính xác 2 Pod IP: `10.42.1.4:80,10.42.3.3:80`
