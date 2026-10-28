# Kubernetes multi-node với k3d dành cho Data Engineer

**Mục tiêu:** hiểu khái niệm, đọc cấu hình và biết cần DevOps cung cấp gì để một dịch vụ hoạt động trên Kubernetes.

**Nhịp học:** không deadline; 32 bài là 32 đơn vị năng lực, không phải 32 ngày hay 32 lần gặp. Một bài có thể chia thành nhiều lượt. Không yêu cầu tự viết YAML từ trí nhớ.

Khóa này là lộ trình duy nhất trong repo. Lộ trình OrbStack cũ đã học xong và được xoá ngày 2026-10-28 theo yêu cầu của học viên; tiến độ mới bắt đầu từ 0/32.

## Đọc trước khi học

1. [Định hướng và cách học](dinh-huong-va-cach-hoc.md): đầu ra, cách chia khối, checkpoint và tiêu chí đạt.
2. [Lab và hợp đồng nền tảng](lab-va-hop-dong-nen-tang.md): topology, ranh giới lab, an toàn và mẫu yêu cầu DevOps.
3. [Tiến độ riêng](tien-do-hoc-tap.md): điểm tiếp tục, minh chứng và phần chưa chắc.
4. [Quy tắc học và mentor](huong-dan-hoc-va-mentor.md) và [hướng dẫn cho mentor khóa này](AGENTS.md).

Mỗi bài đã có lý thuyết trọng tâm, bảng field cần đọc, checkpoint, kế hoạch lab, tiêu chí đạt và yêu cầu DevOps. Đây là thiết kế bài học, chưa phải các bản cài đã kiểm chứng. Scaffold/lệnh theo phiên bản thực tế sẽ được chuẩn bị khi đến bài, sau phần giải thích. Không chạy tất cả bài hoặc toàn bộ data platform cùng lúc.

## Chặng 1 — Biết mình đang dùng nền tảng nào

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 01 | [Kiến trúc và ranh giới DE–DevOps](bai-hoc/01-kien-truc-va-trach-nhiem.md) | Tách API/resource, controller/add-on và hạ tầng thực thi. |
| 02 | [Lab k3d độc lập và truy cập an toàn](bai-hoc/02-lab-k3d-va-context.md) | Đọc cấu hình cluster, nhận diện đúng context và giới hạn multi-node local. |
| 03 | [Đọc manifest và lần theo tham chiếu](bai-hoc/03-doc-manifest.md) | Phân biệt desired state/status, namespace, label và tham chiếu resource. |

## Chặng 2 — Hiểu vòng đời dịch vụ và tác vụ

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 04 | [Pod, controller và loại workload](bai-hoc/04-pod-va-controller.md) | Chọn workload theo vòng đời, không theo độ quen của YAML. |
| 05 | [Startup, readiness và liveness](bai-hoc/05-probes.md) | Phân biệt đang chạy, sẵn sàng phục vụ và cần restart. |
| 06 | [Rollout và dừng ứng dụng](bai-hoc/06-rollout-va-shutdown.md) | Hiểu ngân sách rollout và trách nhiệm xử lý SIGTERM của ứng dụng. |
| 07 | [Job, CronJob và retry](bai-hoc/07-job-cronjob.md) | Phân biệt lịch chạy, lần chạy, retry và tính an toàn khi chạy lại. |

## Chặng 3 — Hiểu việc đặt workload trên nhiều node

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 08 | [Requests, limits và sức chứa](bai-hoc/08-resources.md) | Phân biệt yêu cầu scheduling, giới hạn runtime và số đo sử dụng. |
| 09 | [Node labels, selector và affinity](bai-hoc/09-node-affinity.md) | Đọc điều kiện bắt buộc/ưu tiên và giải thích Pending. |
| 10 | [Taints và tolerations](bai-hoc/10-taints-tolerations.md) | Hiểu được phép vào node không đồng nghĩa bắt buộc vào node. |
| 11 | [Phân bố replicas và miền lỗi](bai-hoc/11-topology-spread.md) | Kiểm chứng replicas thực sự nằm trên các node khác nhau. |
| 12 | [Bảo trì node, PDB và node failure](bai-hoc/12-disruptions.md) | Phân biệt eviction có chủ đích với sự cố, hiểu giới hạn phục hồi. |

## Chặng 4 — Biết kết nối cần những thành phần nào

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 13 | [Mạng Pod qua nhiều node](bai-hoc/13-pod-network.md) | Phân biệt listener, Pod IP, Node IP và vai trò networking plugin. |
| 14 | [Service, EndpointSlice và DNS](bai-hoc/14-service-dns.md) | Lần theo tên → Service → backend; phân biệt DNS lỗi với backend lỗi. |
| 15 | [Đường vào cluster và Ingress](bai-hoc/15-ingress-va-loadbalancer.md) | Phân biệt port mapping, LoadBalancer, controller và rule. |
| 16 | [DNS bên ngoài và TLS](bai-hoc/16-dns-tls.md) | Biết cần hostname, endpoint, certificate và cơ chế gia hạn nào. |
| 17 | [NetworkPolicy và egress](bai-hoc/17-networkpolicy.md) | Viết yêu cầu kết nối và kiểm chứng cả chiều cho phép/lẫn bị chặn. |

## Chặng 5 — Hiểu dữ liệu khi Pod và node thay đổi

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 18 | [Các vòng đời của dữ liệu](bai-hoc/18-vong-doi-du-lieu.md) | Phân biệt writable layer, emptyDir và persistent volume. |
| 19 | [PVC, StorageClass và provisioning](bai-hoc/19-storageclass.md) | Nhận diện bên cấp storage, topology và lý do claim Pending. |
| 20 | [Access modes và chuyển node](bai-hoc/20-storage-multi-node.md) | Không đồng nhất RWO với một Pod hoặc PVC với khả năng chịu mất node. |
| 21 | [StatefulSet và danh tính dữ liệu](bai-hoc/21-statefulset.md) | Hiểu identity/storage association không tự tạo replication. |
| 22 | [Reclaim, mở rộng và backup/restore](bai-hoc/22-backup-va-reclaim.md) | Phân biệt giữ volume, giữ bản sao dữ liệu và phục hồi đã kiểm chứng. |

## Chặng 6 — Hiểu cấu hình và quyền nền tảng cấp cho ứng dụng

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 23 | [ConfigMap, Secret và thay đổi cấu hình](bai-hoc/23-config-secret.md) | Lần theo nguồn config, cách đưa vào ứng dụng và hành vi cập nhật. |
| 24 | [ServiceAccount và RBAC](bai-hoc/24-serviceaccount-rbac.md) | Yêu cầu đúng danh tính, resource, verb và phạm vi namespace. |
| 25 | [Image, registry và nhiều node](bai-hoc/25-image-registry.md) | Hiểu image local không tự có trên mọi node; phân biệt lỗi pull/run. |
| 26 | [Quota, LimitRange và admission](bai-hoc/26-quota-admission.md) | Phân biệt bị từ chối trước khi tạo Pod với Pending sau khi được nhận. |

## Chặng 7 — Đọc bản triển khai và đưa bằng chứng đúng tầng

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 27 | [Helm values và resource được render](bai-hoc/27-helm.md) | Phát hiện dependency, mặc định và rủi ro trước khi cài chart. |
| 28 | [Quan sát và trao đổi sự cố](bai-hoc/28-debug-va-observability.md) | Thu bằng chứng an toàn, khoanh vùng lỗi và gửi yêu cầu có thể xử lý. |

## Chặng 8 — Chuyển nhu cầu DE thành yêu cầu nền tảng

| Bài | Nội dung | Năng lực đầu ra |
|---|---|---|
| 29 | [PostgreSQL và hợp đồng lưu trữ](bai-hoc/29-postgresql.md) | Nêu rõ persistence, truy cập, backup và giới hạn availability. |
| 30 | [Spark Native Kubernetes](bai-hoc/30-spark-native.md) | Hiểu Driver/Executor Pods, API permissions và tài nguyên ứng dụng. |
| 31 | [Airflow và nơi thực thi task](bai-hoc/31-airflow.md) | Phân biệt chạy Airflow trên Kubernetes với executor tạo Pod task. |
| 32 | [Bài tổng hợp và bàn giao DevOps](bai-hoc/32-tong-hop.md) | Đọc cấu hình, phát hiện phụ thuộc thiếu và nghiệm thu một dịch vụ nhỏ. |

## Không bắt buộc trong khóa

Quản trị etcd, dựng cluster bằng kubeadm, multi-control-plane HA, tự viết Operator, CNI/eBPF internals, service mesh và vận hành distributed storage không phải điều kiện tốt nghiệp. HPA/node autoscaling, Gateway API, GitOps và secret manager là hướng mở rộng sau khóa nếu cần; không ngầm yêu cầu cài thêm trong các bài cơ bản.

**Bắt đầu:** đọc [Bài 01](bai-hoc/01-kien-truc-va-trach-nhiem.md). Chưa tạo cluster cho tới khi hoàn thành phần chuẩn bị của Bài 02.
