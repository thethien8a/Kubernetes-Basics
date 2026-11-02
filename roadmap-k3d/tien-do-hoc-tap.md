# Tiến độ Kubernetes multi-node với k3d

[Mục lục](README.md) · [Cách học](dinh-huong-va-cach-hoc.md) · [Lab và hợp đồng nền tảng](lab-va-hop-dong-nen-tang.md)

## Điểm tiếp tục

- **Ngày lập lộ trình:** 2026-10-28, múi giờ Asia/Saigon.
- **Ngày bắt đầu học:** 2026-10-28 (Asia/Saigon).
- **Bài đang học:** [Bài 08 — Requests, limits và sức chứa](bai-hoc/08-resources.md).
- **Tiến độ:** 7/32 bài hoàn thành.
- **Bài vừa hoàn thành:** Bài 07 đã đạt lý thuyết và ba lab; xem [tổng kết Job/CronJob](after-study/07-job-cronjob.md). Snapshot 12:48 ngày 2026-11-02: CronJob `forbid-demo`, UID `8a10b254-897f-43eb-b2da-78c9b09f94cf`, đang `suspend: true`, không có active refs, ba Job con còn lưu đều `Complete=True`. Giữ các Job/Pod làm evidence, chưa xóa tài nguyên.
- **Khối đang dừng / câu chưa trả lời:** Bài 08 khối 1: CPU request của container, đơn vị millicpu, ngân sách Node allocatable khác usage và request không phải CPU cap. Chờ hai câu tình huống: Pod request 600m khi node chỉ còn 500m theo requests dù CPU usage thấp; container request 250m có thể dùng 600m khi không bị CPU limit/ràng buộc khác và có CPU nhàn rỗi hay không. Chưa đánh dấu khối này đạt; chưa giao lab hoặc tạo scaffold Bài 08. Các số minh họa không phải số đo của lab.
- **Lab:** cluster `de-k3d` (1 server + 2 agents, K3s v1.33.6), context `k3d-de-k3d`, namespace `de-lab` đang `Active`. Kiểm tra chỉ đọc lúc 11:26 ngày 2026-11-02: server `Ready`, không bị đánh dấu unschedulable, ARM64, không có taint, không báo Memory/Disk/PIDPressure; hai agent vẫn `NotReady`. Lần kiểm tra 10:49 ghi nhận condition `Ready=Unknown`, reason `NodeStatusUnknown` trên hai agent. Job nhỏ có thể được scheduler xếp lên server; không coi đây là cluster ba node khỏe mạnh hoặc bằng chứng đa node. Chưa xác định nguyên nhân và không sửa node.
- **Client cho lab tiếp theo:** dùng `/usr/local/bin/kubectl` v1.33.9 có sẵn, tương thích minor với API server v1.33.6. `kubectl` trên PATH hiện là v1.36.1, ngoài phạm vi skew được hỗ trợ cho server này; không đổi PATH, nâng cấp tool hay cluster.
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
| [x] | [07 — Job và CronJob](bai-hoc/07-job-cronjob.md) | Hoàn thành | 2026-11-02: checkpoint Job/CronJob đạt, Job tính tổng/lỗi và CronJob Forbid/suspend đạt runtime; [tổng kết](after-study/07-job-cronjob.md) |
| [ ] | [08 — Resources](bai-hoc/08-resources.md) | Đang học | 2026-11-02: khối 1 CPU requests, allocatable và usage; chờ hai câu checkpoint, chưa giao lab |
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

### 2026-11-01 — Bài 07: đạt checkpoint khối 1–3 và lab Job thành công

- Học viên trả lời `1B, 2C, 3A`, đúng cả ba câu: Job phù hợp tác vụ hữu hạn; với `Never`, Job controller vẫn có thể tạo Pod mới khi còn retry budget; chương trình trả kết quả sai nhưng thoát `0` vẫn có thể dẫn tới Job `Complete`.
- Khối 1 đã giảng mục tiêu của `completions`, `parallelism`, `backoffLimit` và ranh giới của `restartPolicy: Never`. Checkpoint khối 1 không thay cho việc đánh giá `OnFailure`, ba tầng retry, idempotency hoặc CronJob.
- Khối 2: học viên trả lời `1B, 2C, 3B`, đúng cả ba câu: `OnFailure` có thể chạy lại container trong cùng Pod; retry bên trong ứng dụng cần giới hạn riêng, không do `backoffLimit` trực tiếp đếm; ví dụ bảng tổng hợp có thể dùng khóa `UNIQUE(dataset, ngày)` ổn định và UPSERT giá trị tổng đã tính để tránh cộng trùng khi rerun. Đây là review lý thuyết, chưa thực nghiệm ghi DB hoặc chứng minh exactly-once.
- Khối 3: học viên trả lời `1B, 2A, 3B`, đúng cả ba câu: Pod mới không có deadline toàn Job mới; `backoffLimit` không tự giới hạn chương trình treo chưa thoát; TTL dọn Job/Pod phụ thuộc, không thay retention output ở DB. Đã giảng vị trí field, deadline ưu tiên hơn retry budget và thời gian graceful termination.
- Mentor kiểm tra chỉ đọc trước thực hành tại context `k3d-de-k3d`, namespace `de-lab`: lúc đó không thấy Job/CronJob; Deployment `rollout-lab` có 2/2 replica sẵn sàng. Đây là snapshot trước lab, không chứng minh lịch sử thí nghiệm.
- Hai agent có condition `Ready=Unknown`, reason `NodeStatusUnknown`; Docker context `orbstack` cho thấy cả hai container vẫn `Up`. Chưa xác định nguyên nhân mất cập nhật kubelet và không thực hiện thao tác sửa/khởi động lại.
- Kiểm tra lại lúc 22:35 (Asia/Saigon): API và namespace `de-lab` vẫn truy cập được, server `Ready`, hai agent vẫn `NotReady`; chưa kiểm tra lại nguyên nhân.
- Preflight lúc 23:24 (Asia/Saigon): namespace `de-lab` tồn tại; không có Job, CronJob, ResourceQuota, LimitRange hoặc NetworkPolicy trong namespace; identity hiện tại được phép tạo Job. Server ARM64 `Ready` và cho phép scheduling; hai agent vẫn `NotReady` với taint unreachable. Không thêm node selector, đổi taint hoặc chữa node để làm lab Job.
- Đối chiếu [version skew policy](https://kubernetes.io/releases/version-skew-policy/): client trên PATH v1.36.1 lệch ba minor so với API server v1.33.6. Đã chọn client sẵn có `/usr/local/bin/kubectl` v1.33.9 và kiểm tra đọc đúng server `v1.33.6+k3s1`; không nâng cấp hay đổi cấu hình mặc định.
- Đã giải thích và tạo [scaffold Job tính tổng](thuc-hanh/07-job-cronjob/01-sum-job.yaml): Job `sum-1-to-10`, namespace `de-lab`, `completions=1`, `parallelism=1`, `backoffLimit=2`, deadline 120 giây, `Never`, chưa đặt TTL; script shell tính tổng 1–10 và ghi stdout, không kết nối dữ liệu thật. Metadata registry công khai xác nhận `busybox:1.37.0` có manifest `linux/arm64/v8`.
- Ở bước chuẩn bị: client dry-run có validate thành công; script trích từ manifest chạy bằng `/bin/sh` trên Mac trả `sum=55` và exit `0`. Các phép kiểm tra local đó chưa chứng minh runtime Kubernetes; sau bước chuẩn bị lúc đó vẫn chưa có Job/CronJob trong `de-lab`.
- Lab 1, sau khi học viên báo đã làm: mentor kiểm tra chỉ đọc lúc 23:54 (Asia/Saigon). Job `sum-1-to-10`, UID `3c07c6a6-008a-4b78-b5a6-9f99552a8da9`, có `Complete=True`, reason `CompletionsReached`, `succeeded=1`; bắt đầu 23:53:10, hoàn thành 23:53:17 ngày 2026-11-01.
- Pod `sum-1-to-10-dbbkb`, UID `fd26f3f4-e096-446a-a563-0f8038e6bd5c`, có controller owner UID khớp Job trên; chạy ở `k3d-de-k3d-server-0`, phase `Succeeded`, container `sum` exit `0`, restart count `0`. Sau khi kiểm tra script và không có env/envFrom do người dùng khai báo, mentor đọc đúng logs Pod: `sum=55`. Events ghi nhận pull image thành công rồi tạo/chạy container; UID được kiểm tra lại sau khi đọc logs.
- Lab 1 đạt bằng chứng đúng lượt chạy, đúng trạng thái và đúng kết quả. Đây là một lượt thành công trên server, không chứng minh exactly-once, HA, cross-node hoặc hai agent đã phục hồi. Không suy thứ tự lệnh học viên đã chạy từ snapshot.
- Đã giải thích và tạo [scaffold Job lỗi](thuc-hanh/07-job-cronjob/02-failing-job.yaml) riêng tên `retry-demo`, giữ nguyên Job thành công. Script chỉ ghi `simulated failure` vào stderr rồi thoát `42`; `Never`, `backoffLimit=2`, deadline 120 giây, chưa đặt TTL. `42` là mã lỗi chủ động của chương trình trong lab này, không cấu hình `podFailurePolicy` đặc biệt.
- Scaffold lỗi qua client dry-run có validate; script trích từ file chạy local có exit `42`, stdout rỗng và stderr đúng thông báo giả. Chưa tạo Job `retry-demo` trong cluster; kiểm tra live sau dry-run vẫn chỉ thấy Job tính tổng đã `Complete`.
- Tiếp theo: học viên tự chạy Job lỗi, quan sát các Pod attempts, exit code, restart count và reason Job dừng; mentor tự kiểm tra sau đó. CronJob chưa được giảng/thực hành. Bài 07 vẫn `Đang học`, tổng tiến độ giữ nguyên 6/32.

### 2026-11-02 — Job retry đạt runtime, review cách đọc kết quả

- Học viên báo đã chạy xong và hỏi cần quan sát gì/làm gì tiếp. Mentor tự đọc manifest và kiểm tra live chỉ đọc từ 00:14 (Asia/Saigon), context `k3d-de-k3d`, namespace `de-lab`; không tạo, sửa, chạy lại hay xóa resource.
- Job `retry-demo`, UID `62af626f-370f-4fa7-a426-81b41906ecb9`, bắt đầu 00:10:00 và có `Failed=True`, reason `BackoffLimitExceeded` lúc 00:10:33 ngày 2026-11-02. `status.failed=3`, `backoffLimit=2`, deadline 120 giây; lý do kết thúc quan sát được là hết retry budget, không phải `DeadlineExceeded`.
- Ba Pod có UID khác nhau, cùng controller owner UID là Job trên:

| Pod | UID | Thời điểm tạo (Asia/Saigon, 2026-11-02) |
|---|---|---|
| `retry-demo-cmgdx` | `a3e38bd2-fffd-4f88-8afb-38112a1a8ca0` | 00:10:00 |
| `retry-demo-nqdwk` | `97041182-16f4-41a0-a785-720f30190100` | 00:10:10 |
| `retry-demo-9fmz8` | `92f6bde5-be4b-4aa6-9302-e1f04f0b5342` | 00:10:30 |

- Cả ba Pod chạy ở `k3d-de-k3d-server-0`, phase `Failed`, dùng `Never`; container `fail` có exit code `42`, reason `Error`, restart count `0`. Sau khi kiểm tra chương trình không có env/envFrom do người dùng khai báo và chỉ in thông báo giả, mentor đọc logs từng Pod: đều là `simulated failure`. UID và owner UID được kiểm tra lại sau khi đọc logs.
- Events của đúng Job UID có ba `SuccessfulCreate` và một `BackoffLimitExceeded`. Các mốc tạo Pod cách nhau 10 giây rồi 20 giây phù hợp backoff tăng dần; đây là hậu kiểm metadata/Events, không phải bản ghi watch trực tiếp và không suy ra thứ tự lệnh học viên đã chạy.
- Runtime lab retry đạt đúng mục tiêu lỗi có chủ đích: một attempt đầu và hai retry trong lượt quan sát này; `RESTARTS=0` ở từng Pod không có nghĩa Job chưa retry. Không coi số Pod hoặc khoảng chờ này là hợp đồng tuyệt đối trong mọi sự cố hạ tầng.
- Điểm dễ đọc nhầm đã kiểm tra: `kubectl get pods` hiển thị `STATUS=Error` trong case này, còn phase API là `Failed`. `kubectl get job` hiển thị `DURATION` hơn 7 phút dù Job đã `Failed` sau 33 giây. Job này không có `status.completionTime`; đối chiếu hàm `printJob` trong [printer upstream v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/printers/internalversion/printers.go) xác nhận khi thiếu mốc đó, cột duration được tính từ `startTime` tới hiện tại. Dùng condition `Failed=True` và `lastTransitionTime` để xác định đã kết thúc khi nào; không suy Job còn chạy hay deadline bị bỏ qua chỉ từ cột `DURATION`.
- Tiếp theo: giải thích cách đọc `STATUS`, `RESTARTS`, exit code, owner UID và Job condition; chờ hai câu review về retry budget kết thúc trước deadline và trạng thái terminal của Job. Chưa coi học viên đã trả lời các câu mới. Sau review mới sang lý thuyết/cấu hình CronJob; chưa tạo scaffold hay resource CronJob. Bài 07 vẫn `Đang học`, tổng tiến độ 6/32.

### 2026-11-02 — Chốt review Job, bắt đầu CronJob khối 1

- Sau phần giảng lại theo mục 1.6 (lệnh → output → cách đọc), học viên trả lời `1C, 2A`, đúng 2/2 câu: `Failed=True` và `BackoffLimitExceeded` cho biết Job đã dừng vì hết retry budget, không suy còn chạy hoặc deadline bị bỏ qua từ `DURATION`; xóa Pod cũ không reset một Job đã kết thúc. Đây là review concept, không phải minh chứng đã thực nghiệm xóa Pod.
- Bắt đầu khối CronJob 1, đối chiếu [tài liệu Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/): CronJob controller tạo Job theo lịch, Job quản lý Pod attempts; đọc năm vị trí của `schedule`, múi giờ ở `spec.timeZone` và cấu hình Job nằm trong `spec.jobTemplate.spec`. Thay template chỉ ảnh hưởng Job tạo sau thay đổi, không tự sửa Job đã có. Ví dụ cấu hình là trích đoạn minh họa, không phải manifest được triển khai; lịch dự kiến không bảo đảm exactly-once.
- Chờ ba câu tình huống về Job mới ở lượt lịch sau, múi giờ độc lập với Mac/Pod và phạm vi hiệu lực của thay đổi `jobTemplate`. Chưa đánh dấu khối này đạt; `concurrencyPolicy`, `suspend`, xử lý lượt trễ và history CronJob chưa được giảng. Chưa giao lab hay tạo scaffold CronJob; không kiểm tra live hoặc thay đổi cluster trong lượt này. Bài 07 vẫn `Đang học`, tổng tiến độ 6/32.

### 2026-11-02 — CronJob khối 1 đạt, học concurrency và suspend

- Học viên trả lời `1B, 2C, 3A`, đúng 3/3 câu của CronJob khối 1: lượt lịch sau tạo Job mới thay vì reset Job cũ; lịch theo `spec.timeZone`, không theo giờ Mac hay ứng dụng; đổi `jobTemplate` không tự sửa Job đã có. Đây là checkpoint lý thuyết, chưa có minh chứng runtime CronJob.
- Khối 2 giải thích `spec.concurrencyPolicy`: `Allow` cho phép chồng lượt, `Forbid` không tạo lượt mới khi còn Job chưa kết thúc của cùng CronJob, `Replace` thay lượt cũ bằng lượt mới với rủi ro cắt dở tác vụ. Chọn `Forbid` cho lab để quan sát kiểm soát lượt chồng; policy không phải khóa dữ liệu toàn cục và không chặn Job thủ công không thuộc CronJob đó. Lượt bị chặn tại mốc lịch vẫn có thể được tạo trễ sau khi Job cũ kết thúc, tùy điều kiện; không suy ra luôn bỏ vĩnh viễn hoặc xếp hàng chạy đủ mọi lượt.
- Giải thích `spec.suspend`: `true` ngừng tạo lượt mới theo lịch, không dừng/xóa Job đã chạy; khi bật lại `false` có thể tạo lượt trễ ngay. Ví dụ lịch mỗi phút và tác vụ 90 giây là tình huống minh họa, không phải output quan sát live. Cấu hình trích đoạn chưa được triển khai.
- Chờ ba câu tình huống khối 2 về `Forbid` tại mốc lịch khi Job cũ chưa xong, phạm vi policy với writer thủ công và ảnh hưởng của suspend lên Job đang chạy. Chưa đánh dấu khối 2 đạt; chưa đi vào cấu hình `startingDeadlineSeconds` và history limits. Không tạo scaffold CronJob, không kiểm tra live hoặc thay đổi cluster trong lượt này; giữ Bài 07 `Đang học`, tiến độ 6/32.

### 2026-11-02 — CronJob khối 2 đạt, học deadline và history

- Học viên trả lời `1C, 2A, 3B`, đúng 3/3 câu của CronJob khối 2: `Forbid` không tạo lượt mới khi Job cũ của cùng CronJob chưa kết thúc; không khóa writer thủ công không thuộc CronJob đó; suspend không dừng Job đang chạy. Đây là checkpoint lý thuyết, chưa có minh chứng runtime CronJob.
- Khối 3 đối chiếu [tài liệu Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) và [controller v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/controller/cronjob/cronjob_controllerv2.go): `spec.startingDeadlineSeconds` giới hạn độ trễ để tạo Job so với mốc lịch, không phải thời gian chạy hay hạn để Pod bắt đầu; `spec.jobTemplate.spec.activeDeadlineSeconds` là budget thời gian hoạt động của Job con. Ví dụ cửa sổ 30 giây, trễ 20 giây còn đủ điều kiện xét tạo nhưng không bảo đảm tạo, trễ 45 giây bỏ lượt đó; không suy ra mọi lượt lỡ đều được chạy bù.
- Giải thích `spec.successfulJobsHistoryLimit: 3` và `spec.failedJobsHistoryLimit: 2` là giới hạn số Job đã kết thúc theo từng loại của CronJob, không phải số lượt được chạy/retry hoặc thời gian lưu. Chỉ dọn Job cũ vượt giới hạn, không cắt Job active; phân biệt với TTL theo thời gian ở Job và retention dữ liệu/log bên ngoài. Trích đoạn YAML và các mốc giờ là minh họa, chưa triển khai; chưa bật TTL để tránh mất evidence lab.
- Chờ ba câu khối 3 về lượt trễ quá cửa sổ, Job đã tạo đúng cửa sổ nhưng Pod còn Pending và history cleanup không tác động Job active. Chưa đánh dấu khối 3 đạt, chưa tạo scaffold/giao lab CronJob; không kiểm tra live hoặc thay đổi cluster trong lượt này. Bài 07 vẫn `Đang học`, tổng tiến độ 6/32.

### 2026-11-02 — CronJob khối 3 đạt, chuẩn bị lab tạm ngưng

- Học viên trả lời `1B, 2A, 3C`, đúng 3/3 câu: quá cửa sổ tạo trễ thì bỏ lượt đó, không tắt lịch sau; `startingDeadlineSeconds` không hủy Job đã tạo vì Pod còn Pending; history limits dọn Job đã kết thúc theo từng loại, không cắt Job active. CronJob khối 1–3 đạt 9/9 câu lý thuyết, chưa thay thế minh chứng runtime.
- Preflight chỉ đọc tại context `k3d-de-k3d`, namespace `de-lab` đang `Active`: lúc 10:49 server `Ready`, hai agent `NotReady/NodeStatusUnknown`; server ARM64, không có taint và không báo Memory/Disk/PIDPressure trong kiểm tra bổ sung cùng lượt. Hai Job cũ vẫn kết thúc như trước; không thay đổi chúng hay sửa node. Lúc 10:54 chưa có CronJob và Job mang label `app=forbid-demo`.
- Xác nhận `/usr/local/bin/kubectl` v1.33.9, server v1.33.6+k3s1 và API `batch/v1` hỗ trợ `CronJob.spec.timeZone`. Kiểm tra registry chỉ đọc bằng `docker buildx imagetools inspect busybox:1.37.0` thấy platform `linux/arm64/v8`; tiếp tục dùng image version này như hai scaffold Job trước, không import image hay chạy container thay học viên.
- Chuẩn bị [03-forbid-cronjob.yaml](thuc-hanh/07-job-cronjob/03-forbid-cronjob.yaml): lịch mỗi phút, `Asia/Ho_Chi_Minh`, `Forbid`, khởi đầu `suspend: true`; cửa sổ tạo trễ 30 giây, history 3 thành công/2 thất bại; Job con `completions: 1`, `parallelism: 1`, `backoffLimit: 0`, `activeDeadlineSeconds: 180`, Pod `restartPolicy: Never`. Tác vụ chỉ in `task started`, sleep 90 giây rồi in `task completed`, không kết nối dữ liệu thật. Label `app=forbid-demo` có ở CronJob, Job template và Pod template để quan sát riêng thí nghiệm; chưa bật TTL.
- Validation: client-only dry-run với schema validation và kiểm tra cú pháp script bằng `/bin/sh -n` đều đạt; không thực thi script hay tạo object cluster. Chỉ xác nhận cấu hình/cú pháp, chưa xác nhận image pull, scheduling hoặc runtime.
- Giao bước 1: học viên tự apply scaffold vẫn tạm ngưng, xem custom columns `NAME/SUSPEND/POLICY/ACTIVE`, kỳ vọng `forbid-demo/true/Forbid/<none>` và chưa có Job qua selector `app=forbid-demo`. Output giao bài là kỳ vọng, không phải resource đã tồn tại. Chờ học viên thực hiện rồi mentor kiểm tra chỉ đọc; chưa giao bật lịch, chưa quan sát lượt chồng hay suspend sau khi Job đã chạy. Bài 07 vẫn `Đang học`, tổng tiến độ 6/32.

### 2026-11-02 — Nghiệm thu CronJob tạm ngưng, giao quan sát Forbid

- Sau khi học viên báo đã làm, mentor tự kiểm tra chỉ đọc lúc 11:26 tại context `k3d-de-k3d`, namespace `de-lab` đang `Active`. CronJob `forbid-demo`, UID `8a10b254-897f-43eb-b2da-78c9b09f94cf`, được tạo lúc `2026-11-02T04:17:20Z` (11:17:20 Việt Nam), có `suspend: true`, `concurrencyPolicy: Forbid`, không có active refs, `lastScheduleTime` và `lastSuccessfulTime` trống. Job/Pod với label `app=forbid-demo` đều chưa có. Bước 1 tạo tạm ngưng đạt; không suy ra đã thực nghiệm Forbid hoặc chạy thành công tác vụ.
- Live config khớp các field chính của scaffold: lịch mỗi phút, `Asia/Ho_Chi_Minh`, cửa sổ trễ 30 giây, history 3/2, Job backoff 0/deadline 180, Pod `Never`, image `busybox:1.37.0`. File local vẫn `suspend: true`. Node preflight: server `Ready`, ARM64, không có taint hay Memory/Disk/PIDPressure; hai agent vẫn `NotReady`. Không sửa node hoặc workload.
- Theo mục 1.6, mentor trình bày lại lệnh custom columns CronJob cùng output thực tế `forbid-demo/true/Forbid/<none>`, và lệnh lọc Job cùng kết quả không có resource. Đã kiểm tra lệnh đọc Event theo `involvedObject.kind=CronJob,involvedObject.name=forbid-demo`; lúc kiểm tra chưa có Event phù hợp. Đối chiếu [controller Kubernetes v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/controller/cronjob/cronjob_controllerv2.go#L568-L582): Event `JobAlreadyActive` được phát khi controller không tạo lượt vì còn Job active và policy là Forbid; đây chưa phải Event quan sát được trong lab.
- Giao bước 2 bằng hai terminal: A watch Job với custom columns `NAME/ACTIVE/SUCCEEDED/FAILED`; B patch riêng `spec.suspend=false` rồi watch Event của CronJob. Khi thấy `JobAlreadyActive`, học viên Ctrl+C dừng watch ở B và patch `spec.suspend=true` ngay, ưu tiên lúc Job cũ còn active. Ctrl+C không tự tạm ngưng CronJob. Nếu chờ quá 3 phút mà chưa có Event cần thiết, vẫn phải suspend trước khi điều tra; không để lịch chạy vô hạn.
- Lệnh watch dùng `--request-timeout=0` để không bị timeout 10 giây như các phép đọc snapshot. Sau suspend, học viên xác nhận `SUSPEND=true` bằng lệnh kiểm tra đã có, giữ watch Job thêm ít nhất 70 giây để đi qua một mốc lịch tiếp theo và quan sát Job cũ có thể hoàn thành. `ACTIVE` đếm Pod active, không tự chứng minh Pod đã Running; tên Job và các output từ bước bật lịch trở đi chỉ là minh họa/kỳ vọng. Nếu Job đã xong trước khi suspend, chưa đủ minh chứng suspend khi Job đang chạy.
- Các lệnh patch thay đổi object live, không sửa file YAML local; không apply lại scaffold giữa lúc quan sát vì file vẫn `suspend: true`. Mentor không bật/tắt lịch thay học viên. Chờ kết quả runtime để kiểm tra UID/owner, Events, status/timestamps và logs an toàn của tác vụ giả; chưa chốt Bài 07, tiến độ vẫn 6/32.

### 2026-11-02 — Hoàn thành Bài 07, bắt đầu Bài 08

- Khi học viên yêu cầu tiếp tục, mentor kiểm tra chỉ đọc lúc 12:40–12:48 tại context `k3d-de-k3d`, namespace `de-lab`. CronJob vẫn cùng UID `8a10b254-897f-43eb-b2da-78c9b09f94cf`, `suspend: true`, `Forbid`, không có active refs. Ba Job còn lưu `forbid-demo-29893294`, `forbid-demo-29893296`, `forbid-demo-29893298` đều có owner UID khớp CronJob, `succeeded=1`, `Complete=True`; Pod tương ứng exit `0`, restart count `0`, chạy trên server.
- Event đúng CronJob UID có `JobAlreadyActive`, count `2`, first timestamp 12:35:00 và last timestamp 12:37:00 giờ Việt Nam, phù hợp hai mốc còn tác vụ cũ chưa xong. Đây là Event thực tế, không còn chỉ là ví dụ từ source controller; mentor đã đưa lại lệnh và trích output để học viên tự đọc.
- Xác nhận entry managedFields `kubectl-patch` sở hữu `spec.suspend`, thời điểm `2026-11-02T05:38:21Z` (12:38:21), current value `true`; entry `k3s` chỉ cập nhật status. Pod cuối UID `328741be-5ef6-4ff8-afbb-21873aa52858`, Job owner UID `57a73e40-3931-4c8d-af9e-f701302dfc12`, chạy đúng tác vụ giả đã được kiểm tra trước khi đọc log. Log bắt đầu `05:38:00.569200239Z`, hoàn tất `05:39:30.574342534Z`, container exit `0`, Job Complete lúc 12:39:32: tác vụ tiếp tục khoảng 69 giây sau mốc patch. managedFields không phải audit log đầy đủ; kết luận dựa trên kết hợp ownership, snapshot, timestamps và logs.
- Snapshot cuối lúc 12:48: `lastScheduleTime` vẫn 12:38, không có Job mới sau mốc patch trong các resource còn lưu; không suy ra bảo đảm lịch sử/tương lai ngoài khoảng quan sát. Giữ CronJob tạm ngưng và giữ Job/Pod làm evidence, không tự cleanup hay đổi workload. Kiểm tra bổ sung lúc 12:52 ghi bảng mặc định `retry-demo` là `Failed`, `DURATION=12h`, giúp tổng kết có đúng lệnh/output cho nhầm lẫn cũ; không coi duration đó là runtime còn hoạt động.
- Đối chiếu các checkpoint đã đạt: Job khối 1–3, review Job và CronJob khối 1–3 bao phủ ba tầng retry, Complete khác nghiệp vụ đúng, idempotency qua khóa ổn định/UPSERT, lịch/timezone/template, Forbid/suspend và deadline/history. Không hỏi lại để đủ số câu. Tạo [tổng kết Bài 07](after-study/07-job-cronjob.md), đánh dấu `Hoàn thành`, nâng tiến độ lên 7/32; không ghi lý thuyết DB/exactly-once thành thực nghiệm.
- Bắt đầu Bài 08 khối 1 theo [tài liệu Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/): Container `resources.requests.cpu`, `1000m=1 CPU`, phân biệt Node allocatable, tổng requests đã xếp và usage thực đo; scheduler không dùng CPU usage thấp để bỏ qua kiểm tra requests. Request không phải CPU cap; có thể dùng hơn request khi có tài nguyên và không bị limit/ràng buộc khác.
- YAML và số CPU ở khối mới chỉ là minh họa, chưa apply: ví dụ node allocatable 2000m, requests đã xếp 1500m, Pod mới cần 600m; ví dụ container request 250m có nhu cầu 600m. Chờ hai câu checkpoint, chưa đánh dấu khối 1 đạt, chưa giảng chi tiết memory/limits, chưa tạo scaffold hoặc giao lab Bài 08. Nhắc các node-container k3d dùng chung host; ngoài lab cần platform cung cấp allocatable và chính sách tài nguyên, không suy CPU vật lý bằng tổng số CPU quảng bá từ các node local.

## Phần còn vướng

- **Bài 08:** chờ hai câu khối 1 CPU request; chưa có lab hoặc minh chứng runtime về requests/limits. Không lấy việc đã chạy Job/CronJob làm bằng chứng đã hiểu hay thực nghiệm resource scheduling.
- **Giới hạn lab hiện tại:** hai agent `NotReady`; mới xác nhận symptom mất cập nhật kubelet, chưa có nguyên nhân hay biện pháp khắc phục đã kiểm chứng. Lab Job nhỏ có thể thử trên server đang cho phép scheduling, không dùng nó để xác nhận phục hồi hay khả năng đa node. Học viên chưa được giao thao tác sửa node trong bài này.

## Bàn giao cho mentor ở lượt tiếp theo

Đọc hướng dẫn trong [AGENTS.md](AGENTS.md), các tài liệu dùng chung và bài ở mục “Điểm tiếp tục”. Dạy khối kế tiếp trước khi đưa lệnh. Nếu học viên đã làm, tự kiểm tra chỉ đọc ở đúng lab mới; không yêu cầu output có thể tự xem, không sửa workload thay và không lấy runtime đạt làm bằng chứng đã hiểu.
