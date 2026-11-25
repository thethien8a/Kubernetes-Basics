# Tổng kết Bài 25 — Image, registry và nhiều node

[Mục lục](../README.md) · [Bài học gốc](../bai-hoc/25-image-registry.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Bài tiếp theo](../bai-hoc/26-quota-admission.md)

- **Trạng thái:** Hoàn thành đầy đủ ngày **2026-11-22** giờ Việt Nam (`Asia/Saigon`); đủ đối chứng, phục hồi và review.
- **Challenge:** Hai Pod thay cho hai Spark executor sử dụng cùng một image. Chỉ nạp image vào một agent để tách việc **build trên Mac** khỏi việc **node có image để chạy**. Sau đó nạp vào agent còn thiếu và kiểm chính Pod đang chờ có thể khởi động.
- **Phạm vi:** `k3d-de-k3d/de-lab`, hai agent Linux ARM64. Client `/usr/local/bin/kubectl` v1.33.9, server v1.33.6+k3s1, k3d v5.8.3, containerd `2.1.5-k3s1.33`; Docker client/engine 29.8.2 và Buildx v0.37.2. Học viên tự build, import và tạo Pod; mentor chuẩn bị scaffold và kiểm live chỉ đọc.

## 1. Image, node runtime và cấu hình

Scheduler chọn node; kubelet trên node đó yêu cầu runtime chuẩn bị image rồi khởi động container. `kubectl create` không gửi kèm image. Docker trên Mac và containerd trên từng node có kho riêng, dù các node k3d cùng chạy trên một máy vật lý. Marker từ `CMD` cho biết chương trình trong image đã chạy, không chỉ là API đã nhận Pod hay runtime đã lưu image.

| Field / cơ chế | Điều cần nhớ |
|---|---|
| Container `image` | Đọc registry, repository và tag hoặc digest. Tag có thể trỏ tới bản khác; pin digest giúp tái lập bản phát hành. Digest của một index có thể chứa nhiều manifest theo kiến trúc; digest của riêng bản AMD64 không thay cho bản ARM64. |
| Container `imagePullPolicy` | `IfNotPresent` dùng image đã có trên node hoặc pull nếu thiếu; tag mutable có thể làm hai node chạy hai bản khác nhau. `Always` hỏi registry khi khởi động container nhưng có thể dùng lại layer đã cache. `Never` không pull, chỉ dùng image local. |
| Mặc định pull policy | Khi tạo mới và bỏ field: `:latest` hoặc không có tag/digest thường là `Always`, tag khác `latest` hoặc pin digest là `IfNotPresent`. Đổi `image` sau khi policy đã được lưu không tự cập nhật policy. `Always` cũng không đổi container đang chạy. |
| PodSpec `restartPolicy: Never` | Không chạy lại container đã kết thúc. Không cản lần khởi động đầu tiên của Pod đang chờ image. Khác với `imagePullPolicy: Never`. |
| PodSpec `imagePullSecrets[].name` | Ref tới pull Secret cùng namespace với Pod, ví dụ type `kubernetes.io/dockerconfigjson`. Kubelet dùng credential để pull trước lúc app chạy. Không đưa vào env như credential S3/DB, và RoleBinding không cấp quyền đọc repository trên registry. |
| PodSpec `nodeSelector` | Chọn agent theo `kubernetes.io/hostname`. Hai Pod test chỉ khác tên và selector, cùng container và cùng policy; chủ đích để so hai kho node, không phải cấu hình placement đề xuất cho Spark thật. |

Khi debug, nhìn **node đã được gán chưa → trạng thái container → Events → log nếu container đã chạy**. Pod `Pending` có thể đã schedule. `ErrImageNeverPull` trong lab là thiếu image local với policy `Never`. `ImagePullBackOff` là giãn nhịp thử lại sau lỗi pull; đọc thông báo gốc về reference, DNS/kết nối, TLS, quyền hoặc platform. `CrashLoopBackOff` với `Last State: Terminated` hướng tới log `--previous`, exit code và cấu hình khởi động, không phải lý do xin quyền ghi registry.

## 2. Scaffold và cách phân phối trong lab

- [Dockerfile](../thuc-hanh/25-image-registry/Dockerfile) dùng BusyBox `1.37.0` pin index digest `sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec`. Metadata công khai liệt kê `linux/arm64/v8` và `linux/amd64`. Build `--platform linux/arm64 --load` để đưa image test vào Docker trên Mac, không push. `CMD` in `lesson25-image-ok` rồi thoát `0`.
- [01-pods.yaml](../thuc-hanh/25-image-registry/01-pods.yaml) định nghĩa hai Pod `v1` có nhãn `lesson: "25"`, container `worker`, cùng ref `docker.io/library/lesson25-etl-worker:local-v1`. Không ghi đè `command`/`args` hay tự gắn token ServiceAccount. Mỗi Pod requests 25m/32Mi, limits 100m/64Mi. Strict client dry-run đạt; không dùng dry-run thay kết quả chạy.
- Build đầu dừng ở `load metadata` vì Docker client gọi `osxkeychain` nhưng phiên không đọc được keychain. Không có bằng chứng digest BusyBox sai hoặc keychain chắc chắn bị khóa. Mentor kiểm cùng Dockerfile bằng `buildx build --check` với cấu hình client tạm cho Docker Hub ẩn danh và vẫn trỏ cùng socket OrbStack: metadata `DONE`, `Check complete, no warnings found.` Học viên báo build lại được; mentor xác nhận image `linux/arm64` và `CMD` đúng trong Docker. Không cần sửa Dockerfile, đăng xuất hoặc thay cấu hình credential mặc định.
- `k3d image import --cluster` ở v5.8.3 chọn **cluster**, không chọn agent. Cần nạp một agent mỗi lần để giữ đối chứng, nên học viên dùng luồng dưới, trước hết vào `agent-0`, sau khi đã quan sát lỗi mới đổi đích thành `agent-1`. `k8s.io` là namespace nội bộ **containerd**, không phải namespace Kubernetes `de-lab`. Chỉ thao tác trên hai agent của sandbox; không xóa cache hay import image hệ thống.

```bash
# Lệnh tham khảo đã dùng ở bước nạp agent-0; không cần chạy lại để review.
(
  set -o pipefail
  docker --context orbstack image save --platform linux/arm64 \
    docker.io/library/lesson25-etl-worker:local-v1 |
    docker --context orbstack exec -i k3d-de-k3d-agent-0 \
      ctr --namespace k8s.io images import --platform linux/arm64 -
)
```

## 3. Đối chứng và phục hồi đã kiểm chứng

| Mốc ngày 22/11, giờ Việt Nam | Quan sát |
|---|---|
| **16:08:51 — Sau build, trước import** | Docker trên Mac có tag test, `linux/arm64`, `CMD` đúng; hai agent chưa có image theo ref này. Không có Pod test. |
| **16:14:55 — Chỉ nạp agent-0** | Học viên gửi log import có digest `dad896b1…`; mentor kiểm kho `ctr` và CRI: `agent-0` có đúng tag/digest, `agent-1` không có. Cả hai agent Ready. |
| **16:23:23 — Hai Pod, một kho có image** | Hai Pod được tạo lúc 16:22:32. Học viên thấy A trên `agent-0` `Succeeded`/exit `0`; B trên `agent-1` `Pending`/`ErrImageNeverPull`, chưa có exit code. Mentor kiểm độc lập: A in marker; B có `PodScheduled=True`, chưa có image ID; Event theo UID nói `is not present with pull policy of Never`. Archive ARM64 trên Mac vẫn khớp digest của `agent-0`. |
| **16:33:00 — Đã nạp agent-1** | Học viên thấy cả hai `Succeeded`/exit `0`. Mentor xác nhận B giữ UID, node và spec; Events cùng UID có lỗi cũ rồi `Pulled` với thông báo `already present on machine`, `Created` và `Started` lúc 16:31:25. Cùng Pod B chạy lần đầu và kết thúc lúc 16:31:25, restart 0, log đúng marker. Event tên `Pulled` ở đây không phải pull qua mạng. |
| **16:39:03 — Kiểm chốt sau review** | `de-lab` Active, hai agent Ready/ARM64. Hai Pod giữ UID, node, spec và container ID sau phục hồi, không có owner hay deletion timestamp; cả hai `Succeeded`/exit `0`/restart 0 và log `lesson25-image-ok`. Cùng manifest digest ARM64 trên hai agent và cùng runtime `imageID` ở hai Pod. |

| Pod | Node | UID |
|---|---|---|
| `lesson25-worker-a` | `k3d-de-k3d-agent-0` | `86ec79c3-fed0-45a4-81c9-7c001fb54c36` |
| `lesson25-worker-b` | `k3d-de-k3d-agent-1` | `540a25f4-9b13-430c-b593-8c4f6820b78d` |

So đúng loại định danh: manifest ARM64 trong archive và cột `DIGEST` của `ctr` cùng là `sha256:dad896b1abd2b691f82ee13b1a7a3f59f61851d96b6a48a8914ec9a05b90287f`. CRI và `status.containerStatuses[].imageID` cùng là `sha256:1339fea515b42fec045539bd5e9a562a41c5e362a12506c8359e19007017b590`. `docker image inspect` trên Mac báo ID `sha256:a42847c101600fbeecbf312a831cc20fa78cf25d7bf3ceef33de05e7c65318df`; không lấy ID này so trực tiếp với cột digest của manifest nhập vào node.

## 4. Tái quan sát kết quả chốt (chỉ đọc)

Trên Mac của lab, kiểm context `k3d-de-k3d` và namespace `de-lab` Active trước khi đọc Pod. Dùng đúng Docker context `orbstack` khi đọc kho hai agent:

```bash
lab25() {
  /usr/local/bin/kubectl --kubeconfig="$HOME/.kube/config" \
    --context=k3d-de-k3d --namespace=de-lab --request-timeout=5s "$@"
}
lab25 get namespace de-lab -o 'custom-columns=NAME:.metadata.name,PHASE:.status.phase'
lab25 get pod lesson25-worker-a lesson25-worker-b \
  -o 'custom-columns=NAME:.metadata.name,UID:.metadata.uid,NODE:.spec.nodeName,PHASE:.status.phase,EXIT:.status.containerStatuses[0].state.terminated.exitCode'
lab25 logs lesson25-worker-a -c worker
lab25 logs lesson25-worker-b -c worker
for n in 0 1; do
  printf 'agent-%s\n' "$n"
  docker --context orbstack exec "k3d-de-k3d-agent-$n" \
    ctr --namespace k8s.io images list 'name==docker.io/library/lesson25-etl-worker:local-v1'
done
```

Ở snapshot chốt, `de-lab` có `PHASE=Active`; hai dòng Pod có UID ở bảng trên, đúng `NODE`, `PHASE=Succeeded`, `EXIT=0`. Hai log đều chỉ in `lesson25-image-ok`. Cột `REF` của hai kho có đúng tag; nhìn `DIGEST` và `PLATFORMS` để so cùng manifest và `linux/arm64`. Snapshot không phải audit thứ tự mọi lệnh, và Events/log cũ có thể hết hạn. Giữ hai Pod đã kết thúc, image trên Mac và hai agent, cùng hai scaffold; không có cleanup bắt buộc. Không xóa image hoặc tạo lại Pod để tái hiện trạng thái lỗi.

## 5. Review và yêu cầu platform ngoài lab

- **Đạt 7/7 lựa chọn.** Sáu checkpoint trước lab `B, C, B, C, A, B`: kho từng node, index đa kiến trúc, cache với tag mutable, phạm vi pull Secret, log lần chạy trước và hai policy `Never`. Trước khi tạo Pod, đã tạm dừng để làm rõ phép đối chứng: giữ nguyên image và policy, chỉ thay sự hiện diện của image trên node. Review chốt **B**: với `x509: certificate signed by unknown authority` trên node mới, kiểm trust CA ở runtime của node đó; sau khi sửa, thử pull cùng digest và chạy trên node chưa có image. Không dùng executor có cache hoặc import tay để nghiệm thu đường registry.
- **Lab ↔ ngoài lab:** OrbStack chạy Docker trên Mac, k3d tạo node-container, K3s có containerd riêng. Import trực tiếp phân phối image trong sandbox, bỏ qua đường registry. Ngoài lab, CI build cho kiến trúc các node pool và push vào registry; DE cấu hình `image` đúng repo/digest và cơ chế pull của workload. Platform cung cấp endpoint/mirror, DNS, đường mạng/egress, CA mà runtime tin cậy và quyền **pull** đúng repo. `localhost` của node không mặc định là Mac.
- **Triển khai tự quản và managed:** cụm tự quản cần cấu hình trust/mirror trên các node khi dùng registry nội bộ; với managed Kubernetes, nhà cung cấp có thể hỗ trợ registry riêng và cấp quyền qua danh tính node, nhưng phải xác nhận cơ chế và quyền cho node pool thực tế. Nếu dùng `imagePullSecrets`, xác nhận Secret đúng type, đúng namespace và ref, không đọc giá trị. Kiểm reference và placement, đọc Events ở node lỗi, nghiệm thu bằng một lần pull trên node chưa cache rồi bằng kết quả chạy workload.
- **Giới hạn:** đã chạy image ARM64 trên hai agent của cùng Mac. Không chạy biến thể AMD64/emulation, thử private registry, mirror, cấp quyền pull, lỗi CA, autoscaling hay Spark/Airflow thật. Tra metadata BusyBox từ Mac và chạy Pod sau import không chứng minh node có đường pull tới registry. Không lưu credential hay dùng quyền quản trị sandbox làm mẫu quyền DE.

[Kubernetes v1.33 — Images](https://v1-33.docs.kubernetes.io/docs/concepts/containers/images/)
