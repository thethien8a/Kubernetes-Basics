# Tổng kết Bài 02 — Lab k3d độc lập và truy cập an toàn

[Tiến độ học tập](../tien-do-hoc-tap.md) · [Bài học gốc](../bai-hoc/02-lab-k3d-va-context.md) · [Cấu hình k3d](../k3d-config.yaml)

- **Ngày hoàn thành:** 2026-10-28 (Asia/Saigon)
- **Cluster runtime:** `de-k3d` (Context: `k3d-de-k3d`)
- **Topology:** 1 server (control-plane) + 2 agents (workers) trên K3s `v1.33.6+k3s1` (ARM64).
- **Tiêu chí nghiệm thu:** Cluster khởi tạo thành công bằng file config declarative; 3 nodes Ready; context độc lập không ghi đè cấu hình cũ; phân biệt rõ luồng kubectl API và 3 loại loadbalancer/proxy; hoàn thành inventory các Pod hệ thống trong `kube-system`.

---

## 1. Kiến thức cốt lõi đã làm chủ

### 1.1 Khái niệm Context & Kubeconfig

$$\text{Context} = \text{Cluster (Endpoint API)} + \text{User (Auth token)} + \text{Namespace mặc định}$$

- **Tách biệt Docker Context vs Kubectl Context:**
  - Docker context (`orbstack`): Chỉ định daemon Docker socket trên macOS.
  - Kubectl context (`k3d-de-k3d`): Chỉ định Kubernetes API Server mà `kubectl` sẽ gửi HTTP request tới. Lệnh `kubectl` độc lập hoàn toàn với Docker context.
- **File kubeconfig:** Lưu tại `~/.kube/config`, chứa endpoint `https://127.0.0.1:6445` và client certificates của cluster `de-k3d`.

### 1.2 Đường đi của request `kubectl` từ máy Mac vào Cluster

```diagram
[Client: kubectl trên macOS]
       │  (1) Gửi HTTPS request tới 127.0.0.1:6445
       ▼
[Container: k3d-de-k3d-serverlb]  (Nginx proxy cấp Docker hạ tầng)
       │  (2) Chuyển tiếp tới port 6443 nội bộ
       ▼
[Container: k3d-de-k3d-server-0]
       │  (3) Tiếp nhận bởi process k3s server
       ▼
[kube-apiserver]  (Xử lý authentication, authorization & trả dữ liệu)
```

### 1.3 Phân biệt 3 loại "Load Balancer / Proxy" trong kiến trúc K8s & Lab

Đây là điểm then chốt tránh nhầm lẫn giữa tầng hạ tầng local, tầng mạng Layer 4 và tầng routing Layer 7:

| Thành phần | Vị trí | Tầng mạng & Trách nhiệm | Tương đương ngoài Production |
|---|---|---|---|
| **`k3d-de-k3d-serverlb`** | Ngoài cluster (1 Docker container riêng của k3d) | Proxy Nginx hạ tầng: Forward port từ macOS (`6445`, `8085`) vào container nodes | Không tồn tại ngoài đời (Production dùng mạng LAN vật lý hoặc Cloud VPC). |
| **`svclb-*` (ServiceLB / Klipper LB)** | Trong cluster (`kube-system`), chạy DaemonSet | **Layer 4 (TCP/UDP)**: Xử lý K8s **`Service type: LoadBalancer`** (ví dụ mở port 5432 cho PostgreSQL) | Cloud Controller Manager gọi API tạo **AWS Network Load Balancer (NLB)** hoặc GCP LB. |
| **`traefik` (Ingress Controller)** | Trong cluster (`kube-system`), chạy Deployment | **Layer 7 (HTTP/HTTPS)**: Đọc resource **`Ingress`** (Host, Path) để định tuyến URL vào Service/Pod (như Airflow UI, Spark UI) | **NGINX Ingress Controller**, Traefik, AWS ALB Controller. |

### 1.4 Bản chất tài nguyên Multi-node trên Host cá nhân

- 3 node container của k3d (`server-0`, `agent-0`, `agent-1`) đều chạy trên cùng một Linux VM của OrbStack và chia sẻ chung **24 GB RAM vật lý** của máy Mac mini M4.
- Con số allocatable 24 GB trên mỗi node **không được cộng dồn** thành 72 GB. Cần đặt budget an toàn cho các workload data để tránh gây tràn RAM host.

---

## 2. Inventory Runtime của Cluster `de-k3d`

Mentor đã kiểm tra trực tiếp trạng thái runtime thực tế:

### 2.1 Nodes
- `k3d-de-k3d-server-0`: Control-plane, K3s `v1.33.6+k3s1`, Container Runtime `containerd://2.1.5-k3s1.33`, Status `Ready`.
- `k3d-de-k3d-agent-0`: Worker node, Status `Ready`.
- `k3d-de-k3d-agent-1`: Worker node, Status `Ready`.

### 2.2 System Pods (`kube-system`)
- `coredns-*`: Dịch vụ DNS phân giải tên nội bộ cho cluster.
- `local-path-provisioner-*`: CSI Driver tự động cấp Storage PVC dạng host-path trên node.
- `metrics-server-*`: Cung cấp API đo lường tài nguyên CPU/RAM cho `kubectl top`.
- `traefik-*`: Ingress Controller tiếp nhận traffic HTTP ngoài vào.
- `svclb-traefik-*`: DaemonSet mở port cho Service Traefik trên từng node.

---

## 3. Nhầm lẫn đã được xử lý trong bài

- **Nhầm giữa Ingress Controller (Traefik) và ServiceLB (`svclb-*`):**
  - *Nhầm lẫn:* Nghĩ rằng Traefik sẽ cấp port/IP cho Service `type: LoadBalancer` của PostgreSQL.
  - *Bản chất:* Traefik là Ingress Controller hoạt động ở **Layer 7 (HTTP/HTTPS)** cho web traffic. Còn Service `type: LoadBalancer` là đối tượng **Layer 4 (TCP/UDP)** do **ServiceLB (`svclb-*`)** (hoặc AWS NLB ngoài cloud) đảm nhiệm.
