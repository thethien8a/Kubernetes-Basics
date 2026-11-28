# Tổng kết Bài 28 — Quan sát và trao đổi sự cố

[Bài học gốc](../bai-hoc/28-debug-va-observability.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Scaffold](../thuc-hanh/28-debug-va-observability/) · [Bài tiếp theo](../bai-hoc/29-postgresql.md)

**Đã học xong theo xác nhận của học viên ngày 2026-11-25, giờ Việt Nam.** Học viên chọn chốt sớm vì đã xử lý các chủ đề liên quan ở những bài trước. Sáu checkpoint và ca Service selector lỗi/phục hồi đã đạt. Không tính Bài 28 là nghiệm thu đầy đủ đề gốc và không giao phần đã bỏ qua thành việc phải làm bù.

## 1. Khoanh tầng trước khi tìm nguyên nhân

| Dấu hiệu | Đọc gì và kết luận tới đâu |
|---|---|
| Deployment chưa Ready, không có Pod con | Kiểm desired replicas và ReplicaSet. `FailedCreate` cùng message `exceeded quota` là lỗi admission của yêu cầu tạo Pod, không phải node đang dùng hết RAM. Deployment được lưu không chứng minh Pod đã được lưu. |
| Pod `Pending`, chưa có `spec.nodeName`, `PodScheduled=False` | Đọc Event `FailedScheduling` của đúng Pod. Với `Insufficient memory`, đối chiếu Pod `spec.containers[].resources.requests.memory` với ngân sách theo requests trên từng node. Field tương ứng ở Deployment nằm dưới `spec.template.spec`. Không cộng allocatable nhiều node hoặc dùng mức dùng RAM hiện tại thay requests. |
| Pod đã có node, container chưa start | Đọc `status.containerStatuses[].state.waiting.reason` và Event của kubelet. Với `CreateContainerConfigError`, message mới chỉ đúng lỗi cụ thể. `env[].valueFrom.configMapKeyRef.name/key` trỏ tên/key trong namespace của Pod. `optional: true` không cấp giá trị mặc định. |
| Container đã kết thúc hoặc restart | `lastState.terminated.exitCode` và `restartCount` chỉ ra lần kết thúc/restart, không tự cho nguyên nhân. `logs -c <container> --previous` chỉ lấy log instance trước của container trong cùng Pod nếu còn; Pod cùng tên nhưng UID khác không phải cùng Pod. Ghép timestamp, UID, container và run ID trước khi dùng log làm bằng chứng. |
| Pod Ready mà Service không có backend | Đối chiếu toàn bộ `Service.spec.selector` với Pod `metadata.labels` trong cùng namespace rồi đọc EndpointSlice. Slice rỗng chưa đủ để kết luận selector sai nếu chưa có bằng chứng về các Pod. Nếu đã có địa chỉ nhưng `ready=false`, kiểm readiness trước khi sửa selector. |

**Checkpoint đã đạt:** `C, B, A, C, B, B` lần lượt cho tầng kubelet sau scheduling, ref ConfigMap cùng namespace, log theo UID cũ, thiếu dữ liệu lịch sử, báo slice rỗng đúng phạm vi và yêu cầu node pool đủ sức chứa trên một node.

## 2. Lab 1 — Lỗi Service selector và phục hồi

Context `k3d-de-k3d`, namespace `lesson28-debug`, client `/usr/local/bin/kubectl` `v1.33.9`, server `v1.33.6+k3s1`. BusyBox `1.37.0` ghim index digest và đã kiểm manifest `linux/arm64/v8`. Pod HTTP trả marker giả tại cổng `8080`; readiness probe gọi trực tiếp Pod, không qua Service. Service `ClusterIP:80` chuyển tới cổng `8080` của backend.

- **Ca lỗi:** Pod Ready, label `role=backend`; file `02` và Service live chọn `role=worker`. EndpointSlice tồn tại nhưng `ADDRESS=<none>` và `READY=<none>`. Lượt kiểm HTTP trước phục hồi trả `ServiceUnavailable: no endpoints available for service "lesson28-route"`.
- **Chọn cách sửa:** Học viên xác định đúng chỗ cần xem là `spec.selector.role` và đề xuất bỏ key. Bỏ key có thể chạy với fixture hiện tại nhưng mở rộng phạm vi chọn; đổi `worker` thành `backend` giữ chủ ý chỉ chọn backend. Sau khi đối chiếu file với live, học viên tự sửa đúng file, thấy `service/lesson28-route configured` và xác nhận live trả `backend`. Không đổi Pod labels hoặc restart Pod.
- **Phục hồi, 23:31:44 ngày 25/11:** mentor kiểm độc lập `10.42.0.120:8080`, endpoint `ready=true`, đúng UID Pod trước sửa; HTTP qua API proxy trả `lesson28-route-ok`. **Snapshot chốt 23:48:39:** giữ namespace Active, Pod Ready/restart `0`, Service selector `backend`, EndpointSlice Ready cùng đích; tại mốc này chỉ kiểm metadata/status, không gọi lại HTTP.

| Object giữ lại | UID và địa chỉ đã đối chiếu |
|---|---|
| Pod `lesson28-route-backend` | `5bbd6762-0754-47df-96b7-814dcad109ec` / `10.42.0.120` |
| Service `lesson28-route` | `6066c5d8-aa99-4222-95eb-a3fd92868c8c` / ClusterIP `10.43.45.68` |
| EndpointSlice `lesson28-route-drq4x` | `b1f5564a-9ec6-4a7f-b2b4-f845f8d584a7` / trỏ đúng UID Pod |

Lệnh tái quan sát chỉ đọc, không apply lại ca lỗi:

```bash
k28() {
  /usr/local/bin/kubectl --kubeconfig "$HOME/.kube/config" \
    --context k3d-de-k3d --request-timeout=8s "$@"
}
k28 -n lesson28-debug get endpointslices \
  -l kubernetes.io/service-name=lesson28-route \
  -o 'custom-columns=NAME:.metadata.name,ADDRESS:.endpoints[*].addresses[*],READY:.endpoints[*].conditions.ready'
k28 get --raw '/api/v1/namespaces/lesson28-debug/services/lesson28-route:http/proxy/'
```

Nhìn địa chỉ backend và `READY=true` trong lệnh đầu, marker `lesson28-route-ok` trong lệnh sau. API proxy cần quyền `get` trên `services/proxy`; phép thử không kiểm DNS, dataplane của ClusterIP hay NetworkPolicy từ client Pod. Ngoài lab, kiểm thêm từ nguồn được phép qua đường truy cập thực của ứng dụng.

## 3. Quan sát ngoài lab và giới hạn đã chốt

- `kubectl top` ở lượt giảng đọc được Pod của **Bài 27** dùng `2m` CPU và `17Mi` working set tại mẫu gần nhất. APIService `v1beta1.metrics.k8s.io` báo `Available=True`, trỏ `kube-system/metrics-server`. K3s đóng gói Metrics Server trong lab; cluster tự quản lý phải cung cấp add-on tương thích, APIService và đường thu từ kubelet, còn managed Kubernetes cần xác nhận nhà cung cấp đã bật gì và quyền xem. Không có mẫu không có nghĩa usage bằng 0; số đo hiện tại không thay lịch sử. Muốn điều tra sau khi Pod mất hoặc tìm đỉnh tại giờ sự cố, cần hệ thống đã thu và còn lưu log/metrics.
- Báo DevOps theo `context/namespace + resource/UID + thời điểm → expected/actual → bằng chứng đã lọc → điều chưa biết → yêu cầu kiểm tra cụ thể`. Yêu cầu quyền đọc đúng resource/phạm vi khi cần, không xin `cluster-admin` hoặc đính raw log, Secret, env hay kubeconfig. Đã kiểm bằng tình huống slice rỗng, không ghi rằng học viên đã viết/gửi một bản báo lỗi hoàn chỉnh.
- **Lab 2**: file `03-memory-worker.yaml` qua strict client dry-run, request `16Gi` vượt `12304236Ki` allocatable trên từng node tại preflight. Đây là dự đoán scheduling, không phải Event đã quan sát của Lab 2. Lượt chốt không thấy Deployment `lesson28-memory` hoặc ReplicaSet/Pod mang labels của nó. **Lab 3**: chỉ học lý thuyết ConfigMap bắt buộc bị thiếu; không có scaffold hay runtime của ca này trong Bài 28. Kinh nghiệm từ Bài 08, 14, 23 và 26 là kiến thức nền, không thay bằng chứng riêng của bài.
- Giữ bốn scaffold và fixture Lab 1, không cleanup hoặc đổi workload khi chốt. Bài 29 chưa bắt đầu.

Nguồn: [Debug applications](https://kubernetes.io/docs/tasks/debug/debug-application/) · [Kubernetes v1.33 — Logging architecture](https://v1-33.docs.kubernetes.io/docs/concepts/cluster-administration/logging/) · [Resource metrics pipeline](https://v1-33.docs.kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/) · [K3s packaged components](https://docs.k3s.io/installation/packaged-components).
