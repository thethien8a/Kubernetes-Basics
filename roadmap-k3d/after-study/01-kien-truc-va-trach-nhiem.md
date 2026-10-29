# Tổng kết Bài 01 — Kiến trúc và ranh giới DE–DevOps

[Tiến độ học tập](../tien-do-hoc-tap.md) · [Bài học gốc](../bai-hoc/01-kien-truc-va-trach-nhiem.md) · [Hợp đồng nền tảng](../lab-va-hop-dong-nen-tang.md)

- **Ngày hoàn thành:** 2026-10-28 (Asia/Saigon)
- **Môi trường:** Bài lý thuyết kiến trúc & ranh giới trách nhiệm, chưa tạo cluster.
- **Tiêu chí nghiệm thu:** Đã hoàn thành 5 câu trắc nghiệm tình huống, phân tích đúng 3 lớp môi trường, giải thích cơ chế desired state, xử lý 2 ca giả định điều tra lỗi và điền phần đầu hợp đồng nền tảng cho dịch vụ Data.

---

## 1. Kiến thức cốt lõi đã làm chủ

### 1.1 Luồng Desired State ──▶ Actual State

Kubernetes vận hành dựa trên cơ chế khai báo (declarative) và vòng lặp điều hòa (reconciliation loop):
1. **`kubectl`**: Là HTTP CLI client. Gửi manifest khai báo desired state tới `kube-apiserver` qua REST API rồi ngắt kết nối. Đóng terminal hoặc tắt máy không ảnh hưởng tới workload.
2. **`kube-apiserver`**: Cổng giao tiếp trung tâm duy nhất. Mọi thành phần đều giao tiếp qua API Server, không bao giờ truy cập trực tiếp datastore hay giao tiếp ngang hàng.
3. **Datastore (`etcd` / SQLite qua kine)**: Nơi lưu trữ trạng thái bền vững của toàn bộ cluster (Single Source of Truth).
4. **`kube-controller-manager`**: Chứa các controller chạy vòng lặp liên tục để so sánh actual state với desired state. Khi thiếu Pod (ví dụ Pod chết), controller tạo bản ghi Pod mới.
5. **`kube-scheduler`**: Lắng nghe các Pod có `spec.nodeName` rỗng, tính toán tài nguyên (requests vs node capacity) và gán Pod vào node tối ưu nhất bằng cách ghi `nodeName`. Scheduler không chạy container.
6. **`kubelet`**: Agent trên từng worker node, đọc Pod được gán vào node mình, ra lệnh cho Container Runtime khởi chạy container, kiểm tra probes và liên tục cập nhật `status.conditions` ngược về API Server.
7. **Container Runtime (`containerd`, `CRI-O`)**: Tầng cấp thấp trực tiếp kéo image và tương tác với kernel (cgroups, namespaces) để chạy container.

### 1.2 API không đồng nghĩa năng lực hạ tầng

Lệnh `kubectl apply` thành công chỉ chứng minh cú pháp và schema hợp lệ. Việc thực thi cần controller và hạ tầng phía sau:
- **PVC (PersistentVolumeClaim)**: Chỉ là lá đơn xin ổ đĩa. Phải có **CSI Driver / Storage Provisioner** và **Storage Backend** vật lý (EBS, Ceph, local disk) cấp byte thật thì PVC mới chuyển sang trạng thái `Bound`.
- **Ingress**: Chỉ là tập luật routing HTTP. Phải có **Ingress Controller** (như Traefik, NGINX) và **Load Balancer / DNS** định tuyến thì traffic ngoài mới vào được.
- **CRD (Custom Resource Definition)**: Chỉ là đăng ký từ vựng mới vào API Server. Phải có **Operator / Custom Controller** chạy để thực thi logic của resource đó.

### 1.3 Ba lớp môi trường & Đối chiếu mục 1.4

| Tầng | Trong Lab | Ngoài Production |
|---|---|---|
| **API & Core** | Kubernetes API tiêu chuẩn | Kubernetes API tiêu chuẩn |
| **Bản phân phối** | **K3s**: Gộp control plane vào một process `k3s server`, dùng SQLite (qua kine), tích hợp sẵn Flannel, Traefik, local-path provisioner | Kubernetes chuẩn tách rời từng component; dùng cụm **`etcd` phân tán (3–5 nodes)** để đảm bảo đồng thuận Raft |
| **Hạ tầng node** | **k3d trên OrbStack (Docker)**: Giả lập multi-node bằng container trên 1 máy Mac mini (24 GB RAM) | Cụm máy chủ vật lý on-prem hoặc Managed Cloud (AWS EKS, GCP GKE) tách biệt hoàn toàn về phần cứng và mạng |

*Giới hạn minh chứng:* Việc chạy nhiều node container trên Mac dùng chung CPU, RAM và Linux kernel. Dừng một node k3d không mô phỏng đầy đủ mất kết nối mạng diện rộng (network partition) hay sự cố đứt cáp nguồn vật lý.

---

## 2. Bảng cấu hình trọng yếu cần đọc

| Resource / Field | Ý nghĩa khai báo | Điều chưa được bảo đảm |
|---|---|---|
| Deployment: `spec.replicas` | Số lượng Pod mong muốn | Chưa bảo đảm cluster có đủ CPU/RAM để chạy hết các bản sao. |
| PVC: `spec.storageClassName` | Chỉ định StorageClass muốn xin | Chưa bảo đảm có provisioner tương ứng hoặc hạ tầng còn dung lượng disk. |
| Ingress: `spec.ingressClassName` | Chỉ định Ingress Controller xử lý | Chưa bảo đảm có Ingress Controller đang chạy hay đã có DNS trỏ về IP cluster. |
| Mọi resource: `status.conditions` | Trạng thái thực tế do hệ thống cập nhật | Cần đọc `reason` và `message` để biết chính xác điểm nghẽn. |

---

## 3. Thực hành & Minh chứng phân tích

### 3.1 Chuỗi Nhu cầu ──▶ Resource ──▶ Thực thi ──▶ Bằng chứng

| Nhu cầu ứng dụng | Resource K8s | Thành phần thực thi | Bằng chứng mong đợi |
|---|---|---|---|
| **1. API Data Catalog (Stateless)** | `Deployment` | `DeploymentController` + `ReplicaSetController` duy trì bản sao; `kubelet` + `containerd` chạy container | `kubectl get deployment` báo `AVAILABLE 1/1`; Pod có status `Running`, ready `1/1` |
| **2. PostgreSQL Metadata (Stateful)** | `PersistentVolumeClaim` (kèm `StatefulSet`) | `CSI Driver` / `local-path-provisioner` cấp ổ đĩa thật | PVC có status **`Bound`**; Pod mount volume thành công và ở trạng thái `Running` |
| **3. Mở UI Airflow ra Web** | `Service` + `Ingress` | `Ingress Controller` (Traefik) định tuyến + `kube-proxy` chuyển traffic tới endpoints | `kubectl get ingress` hiển thị address; truy cập trình duyệt trả về mã HTTP 200/302 |

### 3.2 Xử lý hai ca giả định điều tra lỗi

1. **Ca A (Áp dụng CRD nhưng không sinh Pod)**:
   - *Cách kiểm tra:* Kiểm tra xem Pod controller của Operator (ví dụ Spark Operator) có đang chạy không (`kubectl get pods -A -l app.kubernetes.io/name=spark-operator`).
   - *Nguyên nhân:* CRD mới chỉ đăng ký API schema. Nếu controller bị crash hoặc chưa deploy, không ai xử lý CRD để sinh ra Pod.
2. **Ca B (Pod Pending do RAM hay do Storage)**:
   - *Cách kiểm tra:* Chạy `kubectl describe pod <pod-name>` và đọc mục **Events**.
   - *Phân biệt:* Nếu do RAM, `kube-scheduler` sẽ báo `0/3 nodes available: 3 Insufficient memory`. Nếu do Storage, Kubelet / Controller sẽ báo `FailedMount` hoặc `persistentvolumeclaim ... not found / not bound`.

### 3.3 Hợp đồng nền tảng ban đầu (PostgreSQL Metadata cho Data Platform)

```yaml
1. Dịch vụ / Phạm vi:
   - Tên: postgres-metadata
   - Namespace: de-lab
   - Trách nhiệm: Data Engineer quản lý schema/data; DevOps quản lý hạ tầng cluster & backup volume.
2. Hành vi cần có:
   - Chạy liên tục (Continuous Service).
   - Chấp nhận gián đoạn ngắn (RTO ~ 5-10 phút) khi rolling update hoặc node bảo trì.
3. Tài nguyên ước lượng:
   - Requests: 500m CPU, 512Mi RAM (mức tối thiểu cho môi trường lab/dev).
   - Limits: 1000m CPU, 1Gi RAM (ngăn rò rỉ RAM làm ảnh hưởng các Pod khác trên node).
4. Dữ liệu:
   - Cần lưu trữ bền vững (Persistent Volume) qua PVC.
   - Dung lượng lab: 1Gi (StorageClass: local-path). Ngoài prod: 50Gi (StorageClass: SSD cloud có snapshot định kỳ).
   - Pod restart hoặc dời sang node khác, dữ liệu bảng không bị mất.
```

---

## 4. Những điểm nhầm lẫn đã được xử lý

1. **`kubectl apply` báo `created` không đồng nghĩa ứng dụng đã chạy:** Cần phân biệt rõ giữa việc API Server chấp nhận bản khai báo và việc Controller/Kubelet thực thi thành công.
2. **Trạng thái của PVC là `Bound`, không phải `Running`:** `Running` là trạng thái của Pod/Container; PVC khi được cấp ổ đĩa thành công sẽ có trạng thái `Bound`.
3. **Vai trò Scheduler vs Kubelet:** Scheduler chỉ chấm điểm và ghi tên node (`nodeName`) vào Pod Spec. Kubelet trên chính node đó mới là bên đọc Pod Spec và điều khiển Container Runtime khởi chạy container.
