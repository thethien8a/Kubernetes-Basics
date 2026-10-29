# Tiến độ Kubernetes multi-node với k3d

[Mục lục](README.md) · [Cách học](dinh-huong-va-cach-hoc.md) · [Lab và hợp đồng nền tảng](lab-va-hop-dong-nen-tang.md)

## Điểm tiếp tục

- **Ngày lập lộ trình:** 2026-10-28, múi giờ Asia/Saigon.
- **Ngày bắt đầu học:** 2026-10-28 (Asia/Saigon).
- **Bài đang học:** [Bài 07 — Job và CronJob](bai-hoc/07-job-cronjob.md).
- **Tiến độ:** 6/32 bài hoàn thành.
- **Khối đang dừng / câu chưa trả lời:** đã hoàn thành Bài 06. Bắt đầu Bài 07: Job và CronJob (Cơ chế xử lý batch processing tới hoàn thành, restartPolicy: Never/OnFailure, backoffLimit, concurrencyPolicy, xử lý idempotency và duplicate execution).
- **Lab:** cluster `de-k3d` (1 server + 2 agents, K3s v1.33.6) đang hoạt động bình thường, context `k3d-de-k3d`.
- **Khóa cũ:** học viên xác nhận đã học xong ngày 2026-10-28; lộ trình cũ đã được xoá khỏi repo, không dùng số liệu cũ để ghi thành tích khóa mới.

## Quy tắc ghi tiến độ

Trạng thái: `Chưa học`, `Đang học`, `Bị kẹt`, `Cần ôn`, `Hoàn thành`. Chỉ đánh dấu hoàn thành khi đạt tiêu chí trong bài và [cách học](dinh-huong-va-cach-hoc.md). Một bài có nhiều lượt thì ghi checkpoint để không hỏi lại phần đã hiểu.

Mentor ghi ngày giờ Việt Nam, context/namespace, manifest/scaffold, resource identity và bằng chứng đã lọc; phân biệt quan sát trực tiếp, học viên báo và lý thuyết chưa thử. Khi chốt bài, tạo tổng kết riêng trong `after-study/` của khóa này rồi cập nhật link dưới đây.

## Checklist

| Đạt | Bài | Trạng thái | Ngày học / minh chứng |
|---|---|---|---|
| [x] | [01 — Kiến trúc và trách nhiệm](bai-hoc/01-kien-truc-va-trach-nhiem.md) | Hoàn thành | 2026-10-28: nghiệm thu lý thuyết, trắc nghiệm tình huống, chuỗi thực thi & hợp đồng nền tảng; [tổng kết](after-study/01-kien-truc-va-trach-nhiem.md) |
| [x] | [02 — Lab k3d và context](bai-hoc/02-lab-k3d-va-context.md) | Hoàn thành | 2026-10-28: cluster de-k3d 3 node Ready, context k3d-de-k3d, nghiệm thu inventory & 3 loại LB; [tổng kết](after-study/02-lab-k3d-va-context.md) |
| [x] | [03 — Đọc manifest](bai-hoc/03-doc-manifest.md) | Hoàn thành | 2026-10-28: nghiệm thu giải phẫu manifest, ownerReferences & quan hệ nhãn Service/Pod; [tổng kết](after-study/03-doc-manifest.md) |
| [x] | [04 — Pod và controller](bai-hoc/04-pod-va-controller.md) | Hoàn thành | 2026-10-28: nghiệm thu thí nghiệm Naked Pod vs Controller, self-healing & endpoints update; [tổng kết](after-study/04-pod-va-controller.md) |
| [x] | [05 — Probes](bai-hoc/05-probes.md) | Hoàn thành | 2026-10-28: nghiệm thu phân biệt Readiness (gating, 0 restarts) vs Liveness (CrashLoopBackOff, restarts 5); [tổng kết](after-study/05-probes.md) |
| [x] | [06 — Rollout và shutdown](bai-hoc/06-rollout-va-shutdown.md) | Hoàn thành | 2026-10-28: nghiệm thu stuck rollout (maxSurge=1, maxUnavailable=0), cứu hộ rollback & graceful shutdown; [tổng kết](after-study/06-rollout-va-shutdown.md) |
| [ ] | [07 — Job và CronJob](bai-hoc/07-job-cronjob.md) | Đang học | 2026-10-28: bắt đầu học các cơ chế batch processing chuyên sâu cho DE |
| [ ] | [08 — Resources](bai-hoc/08-resources.md) | Chưa học | — |
| [ ] | [09 — Node affinity](bai-hoc/09-node-affinity.md) | Chưa học | — |
| [ ] | [10 — Taints/tolerations](bai-hoc/10-taints-tolerations.md) | Chưa học | — |
| [ ] | [11 — Topology spread](bai-hoc/11-topology-spread.md) | Chưa học | — |
| [ ] | [12 — Disruptions](bai-hoc/12-disruptions.md) | Chưa học | — |
| [ ] | [13 — Mạng Pod](bai-hoc/13-pod-network.md) | Chưa học | — |
| [ ] | [14 — Service và DNS](bai-hoc/14-service-dns.md) | Chưa học | — |
| [ ] | [15 — Ingress và LoadBalancer](bai-hoc/15-ingress-va-loadbalancer.md) | Chưa học | — |
| [ ] | [16 — DNS và TLS](bai-hoc/16-dns-tls.md) | Chưa học | — |
| [ ] | [17 — NetworkPolicy](bai-hoc/17-networkpolicy.md) | Chưa học | — |
| [ ] | [18 — Vòng đời dữ liệu](bai-hoc/18-vong-doi-du-lieu.md) | Chưa học | — |
| [ ] | [19 — StorageClass](bai-hoc/19-storageclass.md) | Chưa học | — |
| [ ] | [20 — Storage multi-node](bai-hoc/20-storage-multi-node.md) | Chưa học | — |
| [ ] | [21 — StatefulSet](bai-hoc/21-statefulset.md) | Chưa học | — |
| [ ] | [22 — Backup và reclaim](bai-hoc/22-backup-va-reclaim.md) | Chưa học | — |
| [ ] | [23 — ConfigMap và Secret](bai-hoc/23-config-secret.md) | Chưa học | — |
| [ ] | [24 — ServiceAccount/RBAC](bai-hoc/24-serviceaccount-rbac.md) | Chưa học | — |
| [ ] | [25 — Image và registry](bai-hoc/25-image-registry.md) | Chưa học | — |
| [ ] | [26 — Quota và admission](bai-hoc/26-quota-admission.md) | Chưa học | — |
| [ ] | [27 — Helm](bai-hoc/27-helm.md) | Chưa học | — |
| [ ] | [28 — Debug và observability](bai-hoc/28-debug-va-observability.md) | Chưa học | — |
| [ ] | [29 — PostgreSQL](bai-hoc/29-postgresql.md) | Chưa học | — |
| [ ] | [30 — Spark Native](bai-hoc/30-spark-native.md) | Chưa học | — |
| [ ] | [31 — Airflow](bai-hoc/31-airflow.md) | Chưa học | — |
| [ ] | [32 — Tổng hợp](bai-hoc/32-tong-hop.md) | Chưa học | — |

## Nhật ký

### 2026-10-28 — Thiết kế khóa mới

Đã chốt mục tiêu đọc hiểu Kubernetes/YAML và nhận diện dependency để trao đổi với DevOps; không deadline, không học thuộc YAML. Tài liệu được chia thành 32 bài, có scope, checkpoint, lab dự kiến và acceptance criteria. Chưa có bài học, resource hay workload nào được thực thi/nghiệm thu trong khóa mới. Chưa ghi chứng cứ runtime hoặc câu trả lời checkpoint.

### 2026-10-28 — Hoàn thành Bài 06, chuyển sang Bài 07

Học viên đã hoàn thành Bài 06:
- Trả lời đúng các câu hỏi tình huống về cơ chế `maxUnavailable: 0` và rủi ro mất mát dữ liệu do `SIGKILL` thiếu graceful shutdown.
- Thực nghiệm trên Deployment `rollout-lab`:
  + Quan sát hiện tượng stuck rollout khi bản mới lỗi readiness: `rollout status` bị treo ở `1 out of 2 new replicas have been updated`.
  + Phân tích đúng ngân sách surge: ReplicaSet cũ giữ 2 Pods, ReplicaSet mới giữ 1 Pod lỗi ($2 + 1 = 3$ Pods). Dịch vụ không hề bị gián đoạn vì Pod cũ vẫn sống.
  + Thực hiện thao tác cứu hộ khẩn cấp bằng `kubectl rollout undo`, đưa hệ thống về trạng thái `successfully rolled out`.
- Đã nghiệm thu Bài 06, tạo bản tổng kết tại [after-study/06-rollout-va-shutdown.md](after-study/06-rollout-va-shutdown.md). Chuyển Bài 07 sang trạng thái `Đang học`.

## Phần còn vướng

Chưa có. Khi học, ghi: bài/khối → điều chưa chắc hoặc symptom → bằng chứng đã có → giả thuyết còn mở → mức hint → kết quả. Không lưu raw credential/logs.

## Bàn giao cho mentor ở lượt tiếp theo

Đọc hướng dẫn trong [AGENTS.md](AGENTS.md), các tài liệu dùng chung và bài ở mục “Điểm tiếp tục”. Dạy khối kế tiếp trước khi đưa lệnh. Nếu học viên đã làm, tự kiểm tra chỉ đọc ở đúng lab mới; không yêu cầu output có thể tự xem, không sửa workload thay và không lấy runtime đạt làm bằng chứng đã hiểu.
