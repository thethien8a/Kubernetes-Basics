# Tổng kết Bài 30 — Spark Native Kubernetes

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/30-spark-native.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Tiếp](../bai-hoc/31-airflow.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-27** (`Asia/Ho_Chi_Minh`). Review cuối chọn **B** đúng. Snapshot chốt chỉ đọc lúc **23:48:55**.
- **Phạm vi:** `k3d-de-k3d/lesson30-spark`, namespace `Active`, UID `9bcedd0c-beb7-4d62-8375-351aa853dbbd`. Lượt `demo-01`, app ID `spark-6d483ab48a6c49dcaf5383a35157e74c`.
- **Kết quả:** Driver và hai Executor `Succeeded`, exit `0`, restart `0`. Hai task trả `16` từ `agent-1` và `40` từ `agent-0`; Driver in `56`. Mỗi dòng task khớp Pod UID, node và Driver owner của lượt chạy.
- **Phiên bản:** `/usr/local/bin/kubectl` v1.33.9, API v1.33.6+k3s1, ba node ARM64. `spark-submit --version` báo Spark 4.0.2, Java 17.0.21.1 từ bộ runtime đặt riêng ngoài Git tại `~/.local/share/k8s-practice/lesson30/spark-4.0.2-java17`.

## 1. Từ submit đến task

Trong cluster mode, `spark-submit` dùng kubeconfig để tạo Driver Pod và resource của lần submit. Driver dùng **ServiceAccount của Pod** để gọi API và quản lý Executor Pods. Kubernetes scheduler chọn node cho các Pod; Spark Driver chia việc và giao task cho Executor. Native mode sử dụng Kubernetes API; Standalone Master/Worker và Spark Operator là những cách triển khai khác.

`--master k8s://https://127.0.0.1:6445` chọn API endpoint từ Mac qua cổng k3d. `--deploy-mode cluster` đặt Driver trong Pod; client mode đặt Driver ở nơi gọi `spark-submit`. Driver gọi API nội bộ qua `https://kubernetes.default.svc`. Executor đăng ký với Spark Driver qua DNS của headless Service; cổng mặc định của Spark Native 4.0.2 là `7078` cho Driver RPC và `7079` cho Driver block manager.

| Cấu hình | Quyết định và cách đọc |
|---|---|
| `spark.kubernetes.context`, `spark.kubernetes.namespace` | Context `k3d-de-k3d` cho kết nối ban đầu; namespace `lesson30-spark` cho Driver, Executor và RBAC của lần chạy. |
| `spark.kubernetes.authenticate.{driver,executor}.serviceAccountName` | Điền `spec.serviceAccountName` thành `spark-driver` và `spark-executor`. Nếu đã khai SA cho Driver, bỏ SA của Executor khi không có template đặt SA thì Spark dùng SA Driver cho Executor. Kubernetes mới dùng `default` khi Pod gửi đến API để trống field. |
| `Role.rules`, `RoleBinding.subjects`, `roleRef` | Role namespaced cấp quyền đọc/tạo/theo dõi/dọn Pod, tạo ConfigMap cho Executor và dọn resource theo tập. `deletecollection` cấp theo resource và namespace, không giới hạn theo label mà Spark dùng khi gửi request. Executor không nhận Role Driver và tắt tự gắn token. |
| `spark.{driver,executor}.memory=512m`, `memoryOverhead=384m` | Heap JVM `512 MiB`; thêm ngân sách cho native, Python và phần ngoài heap. Với cấu hình này, Spark ghi tổng `896Mi` vào request và limit. Spark off-heap hay cấu hình memory riêng của PySpark có thể thêm vào tổng. |
| `executor.instances=2`, `dynamicAllocation.enabled=false`, `executor.cores=1`, `task.cpus=1` | Hai Executor mục tiêu, mỗi Executor có một chỗ chạy task. Hai partition trong barrier stage cần hai chỗ đồng thời; thiếu chỗ không tự chuyển thành thực thi tuần tự. |
| `spark.kubernetes.{driver,executor}.{request,limit}.cores` | Container request `250m` để scheduler xét đặt Pod, limit `1` CPU áp dụng khi chạy. Hai field này khác số chỗ chạy task của Spark. |
| Executor `spec.affinity` và `lesson30-run` | Required node affinity chỉ nhận hostname của hai agent. Required Pod anti-affinity theo hostname tránh Executor có cả `spark-role=executor` và `lesson30-run=demo-01`. Selector chỉ chọn Pod có nhãn; giá trị trong template phải khớp nhãn do Spark gắn. |
| `spark.kubernetes.container.image` và `local:///` | Image chung Spark 4.0.2 Python, pin digest của index. URI `local:///opt/lesson30/lesson30.py` đọc file trong Driver filesystem; file xuất hiện qua ConfigMap `lesson30-app`, key `lesson30.py`, volume `app-code` mount chỉ đọc. |
| `spark.kubernetes.driver.ownPersistentVolumeClaim=false` và `emptyDir` | Dùng scratch riêng từng Pod trên đĩa node, phù hợp với Role không cấp quyền PVC. Bật `spark.kubernetes.local.dirs.tmpfs` sẽ làm scratch dùng RAM và được tính vào memory container. |
| `submission.waitAppCompletion`, `executor.deleteOnTermination` | Cùng đặt `false` cho lab: CLI trả về sau submit; giữ Executor Pods để đọc spec và đối chiếu bằng chứng sau khi app xong. Driver `activeDeadlineSeconds: 480`; barrier kiểm chỗ chạy mỗi `5s` với tối đa `48` lần thất bại. |

## 2. Lab và bằng chứng

1. **Namespace và RBAC:** học viên tạo namespace cùng hai ServiceAccount, Role và RoleBinding. Kiểm đúng `--as` trong `lesson30-spark`: `create pods` của Driver là `yes`, của Executor là `no`; thêm phép kiểm cho Driver `deletecollection services` trả `yes`. Đây là kiểm quyền, chưa tạo Spark Pod.
2. **App và Pod templates:** ConfigMap live có đúng key `lesson30.py` và nội dung khớp scaffold. Kiểm cục bộ bằng context task giả cho `16` và `40`; kiểm client với hai Pod template xác nhận cấu hình hợp lệ ở phạm vi client. Runtime thật được kiểm ở bước sau.
3. **Submit:** học viên báo `done`. Mentor kiểm read-only từ Kubernetes và log đã lọc. App dùng `[3, 8, 11, 20]`, chia hai partition, lọc chẵn và nhân hai. Task trả `partitionId` cùng tên, UID, node của Executor qua `env[].valueFrom.fieldRef` (`metadata.name`, `metadata.uid`, `spec.nodeName`). Driver nhận các kết quả rồi cộng và in `56`.

| Pod | UID | Node | Bắt đầu / kết thúc container (giờ Việt Nam) | Kết quả task |
|---|---|---|---|---|
| `lesson30-demo-01-driver` | `11c42aa2-ddf7-462f-bb01-eeb8147be897` | `k3d-de-k3d-server-0` | `23:33:01` / `23:33:51` | `total=56` |
| `lesson30-demo-01-17dac1a21dda6b2e-exec-1` | `3a0ec458-2832-42d5-8788-0fd335982fbd` | `k3d-de-k3d-agent-1` | `23:33:45` / `23:33:50` | `partition=0 subtotal=16` |
| `lesson30-demo-01-17dac1a21dda6b2e-exec-2` | `b6bf47b7-19b8-4afe-90f3-79a0ac243dc3` | `k3d-de-k3d-agent-0` | `23:33:41` / `23:33:50` | `partition=1 subtotal=40` |

Hai Executor giữ block affinity và Downward API như scaffold. Cả hai `ownerReferences` trỏ đúng UID của Driver. Cả ba Pod có cùng app selector, `restartPolicy: Never`, cấu hình request/limit đúng, `emptyDir` mặc định và image spec pin `docker.io/library/spark:4.0.2-python3@sha256:cf4427b1cb3f562774aadfc99d1379ec0bd8fed97130ff4d33207ea8830d4ec7`. `imageID` báo cùng digest; Events đúng UID ghi nhận `Scheduled`, `Pulling`, `Pulled`, `Created`, `Started`. Driver có projected API token volume, hai Executor không có; chỉ kiểm sự hiện diện. Snapshot cuối xác nhận cùng ba UID, kết quả task còn khớp và không có Service, PVC hoặc ResourceQuota trong namespace. Snapshot sau khi app kết thúc không tái hiện trạng thái Service trong lúc chạy.

### Lệnh tái quan sát

```bash
kspark() {
  /usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" \
    --context=k3d-de-k3d --namespace=lesson30-spark --request-timeout=10s "$@"
}

kspark get pods -l lesson30-run=demo-01 \
  -o 'custom-columns=NAME:.metadata.name,ROLE:.metadata.labels.spark-role,PHASE:.status.phase,EXIT:.status.containerStatuses[0].state.terminated.exitCode,NODE:.spec.nodeName,SA:.spec.serviceAccountName'

kspark logs pod/lesson30-demo-01-driver -c spark-kubernetes-driver |
  grep -E '^LESSON30_(PARTITION|RESULT) '
```

Ở lệnh đầu, `PHASE=Succeeded` và `EXIT=0` trên cả ba dòng chứng minh kết thúc thành công; `NODE` và `SA` cho biết placement và danh tính. Ở lệnh thứ hai, output mentor đã kiểm (rút gọn UID để đọc nhanh):

```text
LESSON30_PARTITION partition=0 pod=lesson30-demo-01-17dac1a21dda6b2e-exec-1 uid=3a0ec458… node=k3d-de-k3d-agent-1 subtotal=16
LESSON30_PARTITION partition=1 pod=lesson30-demo-01-17dac1a21dda6b2e-exec-2 uid=b6bf47b7… node=k3d-de-k3d-agent-0 subtotal=40
LESSON30_RESULT total=56
```

UID đầy đủ ở bảng trên. Đọc từng `partition`, `uid`, `node` và `subtotal` để nối công việc đã chạy với Pod thực tế. Hai Pod ở hai node là bằng chứng placement; các bản ghi task khớp UID mới xác nhận cả hai xử lý dữ liệu.

## 3. Review và hợp đồng nền tảng

- **Checkpoint:** đạt cả tám khối sau một lần sửa nhầm về ServiceAccount Executor. Ở câu gốc chọn `B?` (`default`); câu chốt chọn `C` đúng: Pod trực tiếp để trống dùng `default`, còn Executor để trống cấu hình riêng được Spark điền `spark-driver` trước khi gửi tới API.
- **Review cuối `B`:** ResourceQuota `requests.memory: 2Gi` kiểm tổng request khi nhận object. Driver và một Executor cần `1792Mi`, còn ba Pod cần `2688Mi`, vượt `2048Mi`. Dù hai node đủ chỗ, yêu cầu tạo Executor thứ hai vẫn bị quota từ chối và barrier stage thiếu một chỗ. Đây là tình huống giả định; không triển khai ResourceQuota trong lượt lab.

| Yêu cầu cho đội nền tảng | Cấu hình và cách kiểm |
|---|---|
| Endpoint, xác thực, RBAC | Từ runner kiểm đúng API endpoint, route và TLS. Cấp quyền nộp Driver Pod và apply Service/ConfigMap trong namespace; cấp riêng RoleBinding cho Driver, kiểm `auth can-i` bằng đúng danh tính. Với managed cluster, cơ chế danh tính của cloud vẫn cần quyền Kubernetes tương ứng. |
| Budgets và placement | Tổng lab `750m` CPU và `2688Mi` RAM theo requests; xem quota và `resources` sau admission. Chọn node pool bằng label được quản lý, mỗi Executor cần một node hợp lệ. Kiểm quota trước khi quy lỗi cho scheduler, rồi đọc `spec.nodeName` hoặc `FailedScheduling`. |
| Images và code | Registry/mirror phục vụ digest và kiến trúc phù hợp, quyền pull qua node identity hoặc `imagePullSecrets` phù hợp. Khi lỗi pull, đọc Events của Pod. Với code đóng gói hoặc mount, kiểm đúng file trong Driver và cách phân phối dependencies tới Executor. |
| Mạng và quan sát | CNI và DNS phục vụ mạng Pod. Nếu namespace có policy chặn mặc định, cho phép DNS, Driver tới API và kết nối RPC/block Spark theo cổng thực tế; job shuffle còn cần các Executor trao đổi block. Khi không đăng ký được Executor, lần theo Service DNS → EndpointSlice → listener/cổng. |
| Scratch, dữ liệu và log | Chốt ngân sách ephemeral storage hoặc memory khi dùng tmpfs, nơi giữ dữ liệu đầu vào/kết quả và cơ chế lưu log sau khi Pod bị dọn. Bài lab chỉ dùng dữ liệu giả; object storage, connector, IAM và lưu log lâu dài cần hợp đồng riêng. |

k3d làm sẵn đường API local qua `serverlb`; ngoài lab dùng endpoint điều khiển mà runner thực sự truy cập được. Hai node container trên một Mac đủ kiểm native scheduling và task execution; chưa chứng minh hiệu năng hai máy độc lập, HA, quyền CI thực tế hoặc kết nối storage ngoài cluster.

**Tài nguyên giữ lại:** namespace, hai ServiceAccount, Role/Binding, `lesson30-app`, các ConfigMap Spark còn lưu, Driver và hai Executor đã kết thúc, cùng bảy [scaffold](../thuc-hanh/30-spark-native/) và bộ Java/Spark riêng ngoài Git. Bài không có bước recovery hay cleanup bắt buộc.

[Spark 4.0.2 trên Kubernetes](https://spark.apache.org/docs/4.0.2/running-on-kubernetes.html) · [Cấu hình Spark 4.0.2](https://spark.apache.org/docs/4.0.2/configuration.html) · [Downward API Kubernetes v1.33](https://v1-33.docs.kubernetes.io/docs/concepts/workloads/pods/downward-api/)
