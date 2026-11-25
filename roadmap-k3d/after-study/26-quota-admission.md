# Tổng kết Bài 26 — Quota, LimitRange và admission

[Bài học gốc](../bai-hoc/26-quota-admission.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Scaffold](../thuc-hanh/26-quota-admission/)

**Hoàn thành đầy đủ ngày 2026-11-24, giờ Việt Nam.** Học viên thực hành quota và phục hồi ngày 22/11; ôn lại từ đầu, kiểm chứng Pod Security Admission (PSA) và đạt review cuối ngày 24/11. Lab dùng context `k3d-de-k3d`, client `v1.33.9`, server `v1.33.6+k3s1`, node Linux ARM64.

## 1. Phân biệt các tầng

| Tầng | Câu hỏi | Dấu hiệu và bước kiểm tra |
| --- | --- | --- |
| RBAC | Danh tính này có quyền gửi request cho resource/verb này không? | Đọc lỗi phân quyền theo subject, verb, resource và namespace; không chỉ nhìn chữ `Forbidden`. |
| Admission | Request có đạt chính sách trước khi lưu object không? | Phân biệt `exceeded quota` và `violates PodSecurity`. Nếu do controller tạo Pod, xem `FailedCreate`/`ReplicaFailure` của controller; có Deployment không có nghĩa có Pod con. |
| Scheduler | Pod đã được lưu có node nào phù hợp không? | Pod tồn tại nhưng `Pending` với `FailedScheduling`, chẳng hạn `Insufficient memory`. Kiểm requests và node khả dụng. |
| Runtime | Container có khởi động và làm đúng việc không? | Kiểm status/Events/logs đúng Pod và lần chạy. Ví dụ `Permission denied` khi ghi checkpoint cần kiểm UID và quyền filesystem, không suy ra PSA đang chặn. |

| Field | Cách đọc trong bài |
| --- | --- |
| ResourceQuota `spec.hard` / `status.used` | `requests.memory: 96Mi` là trần tổng request được tính trong **namespace**, `used` là phần đã tính theo khai báo. Không phải RAM đo được, memory limit hay sức chứa của một node. |
| LimitRange `spec.limits[]`, `type: Container` | Với từng container bỏ cả hai field memory, `defaultRequest: 64Mi` điền request và `default: 128Mi` điền limit trước khi quota tính. Request được khai rõ không bị ghi đè. `min: 32Mi`, `max: 256Mi` là ràng buộc, không tự nâng/hạ giá trị vi phạm. Đọc `spec.containers[].resources` của Pod đã lưu, không chỉ YAML nguồn. |
| Namespace `pod-security.kubernetes.io/enforce`, `enforce-version` | `restricted` chọn bộ quy tắc, `enforce` từ chối Pod vi phạm, `v1.33` ghim phiên bản quy tắc. `warn` cảnh báo, `audit` ghi dấu vào audit log nếu có ghi audit; hai mode đó không tự chặn. |
| Pod `spec.securityContext` | `runAsNonRoot: true` yêu cầu non-root; `runAsUser: 10001` chọn UID cụ thể, không phải giá trị Restricted bắt buộc. `seccompProfile.type: RuntimeDefault` chọn bộ lọc syscall mặc định của runtime. |
| Container `securityContext` | `allowPrivilegeEscalation: false` và `capabilities.drop: ["ALL"]` là hai kiểm tra riêng của Restricted với container Linux. Có dòng thứ hai không bù cho dòng đầu bị thiếu. PSA không tự sửa cấu hình; còn có quy tắc ngoài `securityContext`. |

## 2. Quota và phục hồi — 22/11

File [00](../thuc-hanh/26-quota-admission/00-namespace-va-policy.yaml) tạo `lesson26-test`, `LimitRange/lesson26-container-memory`, `ResourceQuota/lesson26-memory`. [Pod baseline](../thuc-hanh/26-quota-admission/01-pod-baseline.yaml) chỉ khai CPU `25m/100m`, cố ý bỏ memory. [Deployment đối chứng](../thuc-hanh/26-quota-admission/02-deployment-quota.yaml) yêu cầu một Pod mới với cùng kiểu khai báo, nhưng label `app=lesson26-extra` không chọn baseline. BusyBox `1.37.0` pin index `sha256:a7dbc319…` có manifest Linux ARM64 đã đối chiếu; không mount token. `sleep` giữ Pod để quan sát, không tạo tải làm cạn RAM.

| Giờ Việt Nam | Bằng chứng |
| --- | --- |
| **23:28:17 — Baseline** | Học viên thấy `lesson26-baseline` `Running`, request `64Mi`/limit `128Mi`, quota `Used=64Mi`, `Hard=96Mi`. Mentor kiểm độc lập: Pod Ready/restart 0 trên `agent-1`, là Pod duy nhất trong namespace, spec của hai policy khớp file. |
| **23:38:33 — Quota từ chối Pod con** | Học viên tạo được Deployment `lesson26-extra` nhưng `READY=0/1`; selector không có Pod và ReplicaSet `lesson26-extra-b458c7bfb` báo `0 current / 1 desired`. Mentor xác nhận `ReplicaFailure=True`, `FailedCreate`, `exceeded quota: lesson26-memory`, `requested=64Mi`, `used=64Mi`, `limited=96Mi`. Tên xuất hiện trong lỗi là lần thử tạo, không phải Pod từng chạy. |
| **23:43:36 — Phục hồi** | Học viên dùng `set resources` thêm request `memory=32Mi` trong Pod template, giữ CPU `25m` và bỏ limit memory như cũ. Học viên thấy rollout thành công. Mentor xác nhận cùng Deployment UID, generation `1 → 2`; ReplicaSet cũ về 0, ReplicaSet mới `lesson26-extra-7cfdcc5799` có một Pod Ready/restart 0 trên `agent-1`. Pod mới request `32Mi`/limit `128Mi`, baseline giữ UID và request `64Mi`; quota cùng UID và `Used/Hard=96Mi/96Mi`. |

Lệnh thay template đã dùng là `k26 -n lesson26-test set resources deployment/lesson26-extra -c worker --requests='cpu=25m,memory=32Mi'`. **Không chạy lại để review.** File `02` cố ý giữ ca âm không khai memory; live template đã khác sau phục hồi. Không tăng quota, không xóa baseline để nhường chỗ. Con số `32Mi` là ngân sách thử nghiệm vừa bằng `min`, không phải sizing cho ETL thật.

## 3. Đối chứng PSA — 24/11

Học viên tạo [namespace tách biệt](../thuc-hanh/26-quota-admission/03-namespace-psa.yaml) `lesson26-psa` lúc **16:28:37**, có `enforce: restricted` và `enforce-version: v1.33`. Namespace không chứa quota/LimitRange của thí nghiệm trước. [File 04](../thuc-hanh/26-quota-admission/04-pod-psa-thieu-field.yaml) và [file 05](../thuc-hanh/26-quota-admission/05-pod-psa-dat-policy.yaml) cùng tên Pod, namespace, image và mọi cấu hình khác; file `05` chỉ thêm `allowPrivilegeEscalation: false` cho `worker`. Cả sáu scaffold của bài đã qua strict client dry-run; điều đó kiểm đầu vào, không chứng minh qua admission.

```bash
# Từ gốc repo. Hai phép kiểm không lưu Pod; giữ --dry-run=server.
k26() { /usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" --context k3d-de-k3d "$@"; }
b26=roadmap-k3d/thuc-hanh/26-quota-admission
k26 -n lesson26-psa create --dry-run=server -f "$b26/04-pod-psa-thieu-field.yaml"
k26 -n lesson26-psa create --dry-run=server -f "$b26/05-pod-psa-dat-policy.yaml"
k26 -n lesson26-psa get pods
```

Học viên quan sát cả hai kết quả; mentor kiểm độc lập **16:30:23**:

| Lệnh | Phần output cần đọc |
| --- | --- |
| Server dry-run `04` | Exit `1`, `violates PodSecurity "restricted:v1.33": allowPrivilegeEscalation != false`. Lỗi chỉ đúng field của `worker`, không phải quota hay scheduler. |
| Server dry-run `05` | Exit `0`, `pod/lesson26-psa-check created (server dry run)`. Cụm `server dry run` nghĩa là request đã qua admission mà không lưu object. |
| `get pods` | `No resources found in lesson26-psa namespace.` Không Pod nào được lưu; không thử pull image, schedule, quyền ghi hay seccomp thực thi. |

Các dòng `zsh` xen trong transcript của học viên là lỗi shell tách biệt; hai lệnh Kubernetes đầy đủ vẫn cho kết quả trên. Không chạy privileged Pod hoặc nới chính sách.

## 4. Trạng thái khi chốt và cách đọc lại

Kiểm chỉ đọc **16:55:09 ngày 24/11**: cả hai namespace `Active`, giữ UID `12888450-ec25-46eb-85a8-f0f8f9159230` (`lesson26-test`) và `580ebff1-1c8d-4eff-a9fa-d78d683606d4` (`lesson26-psa`). Quota UID `90387d92-e515-401b-b34b-ecf64d756dfb` và LimitRange UID `0feb2e58-efbf-44bc-8fe1-168a30bfabb4` không đổi. Namespace PSA giữ nhãn, không có Pod, ResourceQuota hay LimitRange.

Sau khi học viên mở lại lab ngày 24/11, API truy cập được nhưng hai agent báo `Ready=Unknown` / `NodeStatusUnknown`. **16:31** cùng hai Pod quota đã có `deletionTimestamp` và condition `Ready=False` dù cột container `READY` vẫn `1/1`; Deployment `0/1`. ReplicaSet mới từng báo `FailedCreate` vì request `32Mi` ở mốc quota còn `96Mi/96Mi`; sau đó `Used` đã về `0` khi hai Pod cũ vẫn `Terminating`. Đây là các mốc khác nhau, không suy lỗi cũ còn hiệu lực khi quota đã đổi.

```bash
k26 -n lesson26-test get deployment lesson26-extra
k26 -n lesson26-test get pods -l lesson=26
k26 -n lesson26-test describe resourcequota lesson26-memory
k26 get namespace lesson26-psa --show-labels
k26 -n lesson26-psa get pods
```

Ở snapshot chốt, `get deployment` lại có `READY=1/1`. `get pods` cho thấy `lesson26-extra-7cfdcc5799-qsb8t` (UID `18a26bda-940f-4d27-9238-2690d683dbcc`) `Running`/Ready trên `server-0`, request `32Mi`/limit `128Mi`, vẫn thuộc ReplicaSet `lesson26-extra-7cfdcc5799`. Baseline UID `023c11f1-8353-4b95-bf5f-584cee257acb` và Pod phục hồi ngày 22/11 UID `2c4a6268-2f14-402b-aff0-85a087a6cf13` vẫn `Terminating` trên `agent-1`; đọc `STATUS`, không chỉ cột `READY`. Quota `Used/Hard=32Mi/96Mi`. Hai agent vẫn `Unknown`; không coi có Pod mới là sửa xong node hoặc xác định được nguyên nhân. Không thao tác node/Pod thay học viên hoặc yêu cầu làm lại phục hồi quota vì snapshot sau mở máy.

## 5. Review và hợp đồng platform

- Lượt đầu: quota `1B, 2B, 3B`, LimitRange `1C, 2A`, PSA `B` đúng. Sau khi học viên muốn học lại, ba checkpoint quota/LimitRange/PSA lần lượt `A, B, C` đúng. Đã làm rõ mối nối mà học viên còn vướng: namespace chọn `enforce: restricted`, X trượt vì thiếu field mà luật kiểm, Y có thể qua admission dù chưa kiểm quyền thư mục khi chạy. Không ghi câu đó thành học viên tự chọn đáp án trước khi được giải thích.
- **Review cuối B đúng:** Pod ETL đã chạy và báo `Permission denied` khi ghi `/checkpoint` trên PVC thì kiểm UID thực tế và quyền ghi/mount của thư mục. Đây là tình huống giả định ngoài lab, không phải kết quả test filesystem trong bài.
- K3s cung cấp API server trong lab k3d; LimitRanger, ResourceQuota và PSA là cơ chế Kubernetes, không phải OrbStack cấp quyền filesystem hoặc mặc định các số quota. Ngoài lab, platform xác nhận quota/defaults từng namespace, policy/version và quyền xem Events; với managed cluster xác nhận cấu hình/provider thực tế, với self-managed xác nhận các cơ chế admission đang bật. Đọc lời lỗi để chọn đúng controller/field trước khi đề nghị thay đổi policy.
- DE đề xuất requests/limits và số worker dựa trên tải đo được, kiểm image chạy được dưới UID/GID mong muốn và quyền thư mục/volume. Đạt dry-run chỉ cho phép chuyển sang thử runtime có kiểm soát, không chứng minh ETL, PVC, hay quyền ghi production. Không hạ policy cả namespace để chữa lỗi quyền thư mục.

Giữ sáu scaffold và các tài nguyên của bài đang tồn tại; không có cleanup bắt buộc. Bài 26 đã chốt; chờ [Bài 27 — Helm values và resource được render](../bai-hoc/27-helm.md), chưa giảng hay tạo scaffold bài mới.
