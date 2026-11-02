# Tổng kết Bài 07 — Job, CronJob và retry

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/07-job-cronjob.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/08-resources.md)

- **Ngày hoàn thành:** 2026-11-02, giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phạm vi:** context `k3d-de-k3d`, namespace `de-lab`, dữ liệu giả.
- **Phiên bản đã dùng:** server `v1.33.6+k3s1`, client `/usr/local/bin/kubectl` `v1.33.9`, image `busybox:1.37.0` có manifest ARM64.
- **Cách nghiệm thu:** học viên tự thao tác workload; mentor kiểm tra chỉ đọc manifest, UID/owner, status, Events, exit code và logs đã kiểm tra an toàn. Các snapshot không phải bản ghi đầy đủ mọi lệnh học viên đã gõ.
- **Kết quả:** đạt lý thuyết, Job thành công, Job lỗi/retry, CronJob Forbid và suspend khi tác vụ cũ chưa kết thúc. CronJob được giữ ở trạng thái tạm ngưng; chưa xóa evidence.

## 1. Mental model và ba tầng retry

| Thành phần | Trách nhiệm |
|---|---|
| CronJob controller | Tạo các Job mới theo lịch và policy; không reset một Job cũ cho lượt kế tiếp. |
| Job controller | Quản lý Pod attempts để đạt yêu cầu hoàn thành, trong retry/deadline budget. |
| Pod/container | Chạy chương trình; exit code và kết quả nghiệp vụ là hai điều cần kiểm tra riêng. |

Ba tầng retry cần tách biệt:

1. **Ứng dụng:** thư viện/code tự thử lại thao tác, cần budget và tính an toàn riêng. `backoffLimit` không trực tiếp đếm từng lần retry bên trong code.
2. **Container:** `OnFailure` có thể khởi động lại container trong cùng Pod; `Never` không thực hiện kiểu restart đó.
3. **Job:** với `Never`, một Pod thất bại vẫn có thể được thay bằng Pod attempt mới nếu Job còn retry budget. Không suy Job chưa retry từ `RESTARTS=0` của mỗi Pod.

`Complete=True` không chứng minh kết quả nghiệp vụ đúng. Chương trình tính sai nhưng thoát `0` vẫn có thể khiến Kubernetes đánh dấu Job hoàn thành. Lab tính tổng phải kiểm riêng kết quả độc lập: tổng 1–10 là 55.

### Chạy lại không được cộng trùng dữ liệu

Ví dụ đã review ở checkpoint lý thuyết: bảng tổng hợp dùng khóa ổn định `UNIQUE(dataset, ngày)` và UPSERT **giá trị tổng đã tính**, thay vì mỗi lần rerun lại cộng thêm cùng lượng dữ liệu. Khóa ngẫu nhiên theo từng attempt không tự chống trùng cho cùng một đơn vị công việc.

Đây là tình huống thiết kế, không phải lab ghi database. Job retry và CronJob scheduling không cung cấp bảo đảm exactly-once cho side effect của ứng dụng.

## 2. Cấu hình đã đọc hiểu

### Job

| Field | Ý nghĩa và lựa chọn trong bài |
|---|---|
| `spec.completions` | Mục tiêu số lần hoàn thành; Job tính tổng và Job template CronJob khai báo `1`. Job lỗi không ghi field này và dùng mặc định `1`. |
| `spec.parallelism` | Mức song song mong muốn của Job; Job tính tổng và Job template CronJob khai báo `1`, Job lỗi dùng mặc định `1`. |
| `spec.backoffLimit` | Retry budget của Job; hai Job đầu chọn `2`, Job con của CronJob chọn `0` để tập trung vào lịch. Không thay budget retry bên trong ứng dụng. |
| `spec.activeDeadlineSeconds` | Budget thời gian hoạt động của toàn Job trong cấu hình đang học, không cấp một budget mới cho mỗi Pod attempt; có thể kết thúc Job trước khi dùng hết retry budget. |
| `spec.template.spec.restartPolicy` | Chọn `Never` để tách rõ container restart với Pod attempt mới. |
| `spec.ttlSecondsAfterFinished` | Dọn theo thời gian sau khi Job kết thúc. Chưa khai báo trong lab để giữ evidence; không quản lý retention output ở DB. |

Xóa Pod cũ không reset trạng thái terminal của một Job đã `Failed`. Muốn thử một lượt mới phải chủ động quản lý resource/lượt chạy mới, không suy Job cũ tự sống lại.

### CronJob

| Field | Ý nghĩa và lựa chọn trong bài |
|---|---|
| `spec.schedule` | Năm vị trí cron; lab dùng `* * * * *`, mỗi phút. Không phải bảo đảm mỗi lượt luôn được tạo hoặc chạy đúng giây. |
| `spec.timeZone` | Lab dùng `Asia/Ho_Chi_Minh`; không lấy múi giờ Mac hoặc timezone bên trong container làm nguồn quyết định lịch. |
| `spec.jobTemplate.spec` | Cấu hình Job con. Đổi template chỉ ảnh hưởng Job tạo sau, không tự sửa Job đã có. |
| `spec.concurrencyPolicy` | `Allow` cho phép lượt chồng; `Forbid` không tạo lượt mới khi còn Job chưa kết thúc của cùng CronJob; `Replace` có rủi ro cắt dở tác vụ cũ. Lab chọn `Forbid`. |
| `spec.suspend` | `true` ngừng tạo Job theo lịch, không dừng Job đã có. Bật lại có thể tạo một lượt trễ còn đủ điều kiện. |
| `spec.startingDeadlineSeconds` | Lab chọn `30`: giới hạn độ trễ xét tạo Job so với mốc lịch, không phải runtime limit hay hạn để container bắt đầu Running. |
| `spec.jobTemplate.spec.activeDeadlineSeconds` | Lab chọn `180`: budget hoạt động của Job con. Pod Pending không tự làm ngừng budget này. |
| `spec.successfulJobsHistoryLimit` | Lab chọn `3`: tối đa ba Job đã thành công còn được giữ theo cơ chế history của CronJob. |
| `spec.failedJobsHistoryLimit` | Lab chọn `2`: tối đa hai Job đã thất bại còn được giữ; không phải hai retry. |

`Forbid` không phải khóa dữ liệu toàn cục: nó không chặn writer/Job thủ công không thuộc CronJob này. Lượt bị chặn có thể còn được xét tạo trễ tùy thời điểm và cấu hình; không coi đó là một hàng đợi bảo đảm chạy bù đủ mọi lượt.

History limits dọn theo **số lượng Job đã kết thúc**, TTL dọn theo **thời gian**, còn retention dữ liệu/log bên ngoài là một chính sách khác. Không cắt Job active để đáp ứng history limit. Việc có ba Job thành công được giữ trong snapshot chưa phải một thí nghiệm riêng về cleanup khi vượt giới hạn.

## 3. Scaffold và bằng chứng của hai lab Job

| Scaffold | Mục tiêu |
|---|---|
| [01-sum-job.yaml](../thuc-hanh/07-job-cronjob/01-sum-job.yaml) | Tính tổng 1–10, kiểm cả trạng thái và output. |
| [02-failing-job.yaml](../thuc-hanh/07-job-cronjob/02-failing-job.yaml) | Thoát lỗi có chủ đích, quan sát Pod attempts và retry budget. |
| [03-forbid-cronjob.yaml](../thuc-hanh/07-job-cronjob/03-forbid-cronjob.yaml) | Tác vụ 90 giây với lịch mỗi phút, ban đầu suspend, quan sát Forbid rồi suspend lại. |

### Job tính tổng — snapshot ngày 2026-11-01

- Job `sum-1-to-10`, UID `3c07c6a6-008a-4b78-b5a6-9f99552a8da9`: `Complete=True`, `succeeded=1`, reason `CompletionsReached`.
- Bắt đầu 23:53:10, hoàn thành 23:53:17 giờ Việt Nam; mentor kiểm tra lúc 23:54.
- Pod `sum-1-to-10-dbbkb`, UID `fd26f3f4-e096-446a-a563-0f8038e6bd5c`, controller owner UID khớp Job; container exit `0`, restart count `0`, log `sum=55`.

### Job lỗi — snapshot ngày 2026-11-02

- Job `retry-demo`, UID `62af626f-370f-4fa7-a426-81b41906ecb9`: bắt đầu 00:10:00, có `Failed=True` lúc 00:10:33, reason `BackoffLimitExceeded`.
- Ba Pod có UID khác nhau, cùng Job owner: `retry-demo-cmgdx`, `retry-demo-nqdwk`, `retry-demo-9fmz8`.
- Mỗi container exit `42`, restart count `0`, log `simulated failure`. Trong lượt này có attempt đầu và hai retry; không coi số Pod/khoảng backoff là hợp đồng tuyệt đối trong mọi sự cố.
- Deadline 120 giây chưa phải lý do kết thúc: retry budget đã cạn trước.

### Nhầm lẫn về cột DURATION đã xử lý

Lệnh xem bảng mặc định:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get job retry-demo
```

Snapshot kiểm tra bổ sung lúc 12:52 ngày 2026-11-02; giá trị thời gian có thể đổi khi chạy lại:

```text
NAME         STATUS   COMPLETIONS   DURATION   AGE
retry-demo   Failed   0/1           12h        12h
```

Nhìn cột `STATUS=Failed` cùng `DURATION=12h`: không thể suy từ duration rằng Job vẫn chạy 12 giờ. Job này không có `status.completionTime`; printer Kubernetes v1.33.6 dùng thời gian từ `startTime` tới hiện tại khi thiếu mốc đó. Đọc condition, reason và timestamp tương ứng để xác định đã kết thúc vì sao và lúc nào.

Quy tắc giảng được cập nhật trong bài: mentor tự đọc CLI không có nghĩa học viên đã thấy output. Khi review phải đưa lệnh tái quan sát, output liên quan, tên cột/field, cách đọc và kết luận; phân biệt snapshot với ví dụ/kỳ vọng.

## 4. CronJob: UID, các lượt chạy và kết quả

Mentor kiểm tra chỉ đọc từ 12:40 đến 12:48 ngày 2026-11-02, giờ Việt Nam.

- CronJob `forbid-demo`, UID `8a10b254-897f-43eb-b2da-78c9b09f94cf`, được học viên tạo lúc 11:17:20 ở trạng thái tạm ngưng.
- Bước tạm ngưng ban đầu được kiểm tra lúc 11:26: chưa có Job/Pod khớp `app=forbid-demo`.
- Sau thực hành, ba Job còn lưu đều có controller owner UID khớp CronJob trên, `succeeded=1`, `Complete=True`.

| Job | UID | Tạo lúc (giờ Việt Nam) | Job Complete lúc |
|---|---|---|---|
| `forbid-demo-29893294` | `d8400963-a75c-4a54-9e69-4f54961301e4` | 12:34:16 | 12:35:49 |
| `forbid-demo-29893296` | `d1a138a2-b400-4b7b-b606-852c2f5552b6` | 12:36:00 | 12:37:33 |
| `forbid-demo-29893298` | `57a73e40-3931-4c8d-af9e-f701302dfc12` | 12:38:00 | 12:39:32 |

Các Pod tương ứng là `forbid-demo-29893294-rnsf4`, `forbid-demo-29893296-hx4f6`, `forbid-demo-29893298-kkjvx`; đều ở `k3d-de-k3d-server-0`, phase `Succeeded`, exit `0`, restart count `0`. Khoảng chạy container ghi nhận lần lượt là 12:34:17–12:35:47, 12:36:00–12:37:30 và 12:38:00–12:39:30.

### 4.1 Bằng chứng Forbid, không chỉ đếm số Job

Lệnh tái quan sát, cột tự chọn:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get events \
  --field-selector='involvedObject.kind=CronJob,involvedObject.name=forbid-demo' \
  -o custom-columns='REASON:.reason,COUNT:.count,MESSAGE:.message'
```

Trích dòng thực tế lúc kiểm tra, đã lược các Event khác:

```text
REASON             COUNT   MESSAGE
JobAlreadyActive   2       Not starting job because prior execution is running and concurrency policy is Forbid
```

Event có involvedObject UID khớp CronJob; `firstTimestamp=2026-11-02T05:35:00Z`, `lastTimestamp=2026-11-02T05:37:00Z`. Hai mốc này nằm trong các khoảng tác vụ cũ chưa xong. `COUNT` là bộ đếm của bản ghi Event được tổng hợp, không phải số Pod lỗi hay một bộ đếm bền vững của mọi lượt bị lỡ.

### 4.2 Suspend không cắt tác vụ cũ

Lệnh đọc trạng thái hiện tại và mốc managedFields:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get cronjob forbid-demo --show-managed-fields=true \
  -o jsonpath='suspend={.spec.suspend}{"\n"}{range .metadata.managedFields[?(@.manager=="kubectl-patch")]}patchTime={.time}{"\n"}{end}'
```

Output thực tế:

```text
suspend=true
patchTime=2026-11-02T05:38:21Z
```

Mentor đã kiểm thêm: entry `kubectl-patch` quản lý field `spec.suspend`; entry `k3s` cập nhật status, không sở hữu field này. managedFields là dấu vết quản lý field ở snapshot, không phải audit log đầy đủ mọi thao tác; cần đọc cùng trạng thái, owner và mốc thực thi.

Pod cuối có UID `328741be-5ef6-4ff8-afbb-21873aa52858`, owner là Job UID `57a73e40-3931-4c8d-af9e-f701302dfc12`. Sau khi xác nhận đúng chương trình chỉ in hai thông báo và sleep, đọc log:

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  logs forbid-demo-29893298-kkjvx -c slow-task --timestamps=true --tail=10
```

```text
2026-11-02T05:38:00.569200239Z task started
2026-11-02T05:39:30.574342534Z task completed
```

`Z` là UTC; cộng 7 giờ để đọc các mốc này theo giờ Việt Nam:

| Mốc | Giờ Việt Nam |
|---|---|
| Container bắt đầu | 12:38:00 |
| Mốc patch của manager sở hữu `suspend` | 12:38:21 |
| Container hoàn tất | 12:39:30 |
| Job được ghi nhận Complete | 12:39:32 |

Tác vụ tiếp tục khoảng 69 giây sau mốc patch, rồi exit `0`. Mốc container thoát và mốc controller ghi nhận Job Complete không phải cùng một field.

### 4.3 Trạng thái cuối, giữ evidence

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get jobs -l app=forbid-demo \
  -o custom-columns='NAME:.metadata.name,SUCCEEDED:.status.succeeded,COMPLETE:.status.conditions[?(@.type=="Complete")].status'
```

Snapshot thực tế lúc 12:48:

```text
NAME                   SUCCEEDED   COMPLETE
forbid-demo-29893294    1           True
forbid-demo-29893296    1           True
forbid-demo-29893298    1           True
```

```bash
/usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
  --context=k3d-de-k3d -n de-lab --request-timeout=10s \
  get cronjob forbid-demo \
  -o custom-columns='NAME:.metadata.name,SUSPEND:.spec.suspend,ACTIVE:.status.active[*].name,LAST_SCHEDULE:.status.lastScheduleTime'
```

```text
NAME          SUSPEND   ACTIVE   LAST_SCHEDULE
forbid-demo   true      <none>   2026-11-02T05:38:00Z
```

Không ghi nhận Job mới sau mốc patch trong các resource còn lưu; `lastScheduleTime` vẫn là 12:38 dù đã đi qua nhiều mốc lịch tiếp theo. Không coi snapshot này là bảo đảm về mọi lịch sử hoặc hành vi tương lai.

File scaffold vẫn `suspend: true`; patch live không sửa file. `Ctrl+C` chỉ thoát watch, không dừng CronJob. Khi thực hành đã dùng `--request-timeout=0` cho watch; các lệnh snapshot dùng timeout 10 giây. Không apply lại scaffold giữa lúc đang quan sát lịch vì nó sẽ đưa live config về tạm ngưng.

## 5. Checkpoint đã đạt

| Phần | Đáp án đã review | Nội dung |
|---|---|---|
| Job khối 1 | `1B, 2C, 3A` | Workload hữu hạn, Never vẫn có Job retry, Complete khác nghiệp vụ đúng. |
| Job khối 2 | `1B, 2C, 3B` | OnFailure, retry ứng dụng, khóa ổn định và UPSERT chống cộng trùng. |
| Job khối 3 | `1B, 2A, 3B` | Deadline toàn Job, chương trình treo, TTL khác retention dữ liệu. |
| Review Job | `1C, 2A` | Condition/reason thay DURATION, xóa Pod không reset Job Failed. |
| CronJob khối 1 | `1B, 2C, 3A` | Lượt mới, timezone, thay đổi template. |
| CronJob khối 2 | `1C, 2A, 3B` | Forbid, phạm vi writer, suspend không dừng Job cũ. |
| CronJob khối 3 | `1B, 2A, 3C` | Tạo trễ khác runtime, Pod Pending, history không cắt Job active. |

Không hỏi lại các concept này chỉ để đủ số câu sau lab. Runtime và checkpoint lý thuyết được đối chiếu riêng trước khi chốt bài.

## 6. Hợp đồng DE–DevOps và giới hạn lab

- **DE chịu trách nhiệm:** xác định đơn vị công việc/ngày dữ liệu, tính an toàn khi rerun, output/checkpoint/commit và budget retry của code; kiểm cả trạng thái Kubernetes lẫn kết quả nghiệp vụ.
- **Cần nền tảng cung cấp/xác nhận:** namespace/quota, image registry và kiến trúc node, quyền tạo/sửa CronJob hoặc quy trình triển khai thay thế, quyền đọc Job/Pod/Events/logs, lịch/timezone, xử lý missed schedules, deadline và retention phù hợp. Không lấy quyền admin lab làm quyền DE mặc định ngoài thực tế.
- **Thành phần thực thi:** K3s cung cấp controller Job/CronJob chuẩn Kubernetes. Mac chạy kubectl để gửi yêu cầu API, không phải nơi cron tự thực thi chương trình. Image phải có trong runtime của node hoặc node phải pull được từ registry; image trên Mac không tự có trên mọi node.
- **Log và dữ liệu:** muốn đọc logs sau khi Job/Pod đã bị dọn cần log backend/retention do nền tảng cung cấp. Dọn object Kubernetes không tự xóa output đã ghi ở database/object storage.
- **Giới hạn đã biết:** các Pod của bài chạy trên server; hai agent ở snapshot 11:26 ngày 2026-11-02 vẫn NotReady, chưa xác định hoặc sửa nguyên nhân. Không chứng minh cluster ba node khỏe, cross-node, HA, SLA, hiệu năng production hoặc exactly-once.
- **Chưa thực nghiệm:** ghi database/dedup thật, lỗi controller/missed schedule có chủ đích, cleanup history vượt ngưỡng, TTL cleanup và Replace. Các phần đó đã phân biệt là lý thuyết/tham khảo, không ghi thành runtime đạt.
- **Trạng thái bàn giao:** `forbid-demo` đang tạm ngưng, không có Job active tại snapshot cuối; giữ các Job/Pod làm evidence. Mentor không xóa hoặc thay đổi workload khi chốt bài.

## Nguồn theo phiên bản

- [Job — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/controllers/job/).
- [CronJob — Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/).
- [Event Forbid trong controller v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/controller/cronjob/cronjob_controllerv2.go#L568-L582).
- [Printer Kubernetes v1.33.6](https://github.com/kubernetes/kubernetes/blob/v1.33.6/pkg/printers/internalversion/printers.go).
- [Version skew policy](https://kubernetes.io/releases/version-skew-policy/): đã dùng client cùng minor với server, không dùng client v1.36.1 trên PATH cho lab này.
