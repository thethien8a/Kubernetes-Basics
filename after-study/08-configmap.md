# Sau buổi 08 - ConfigMap

**Ngày học và hoàn thành:** 2026-10-09, giờ Việt Nam. **Tiến độ sau review:** 8/28.

[Challenge gốc](../roadmap/buoi-hoc/08-configmap.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Deployment](../app-buoi8.yaml) · [ConfigMap](../configmap-buoi8.yaml)

> Tách config khỏi image không đồng nghĩa ứng dụng tự cập nhật config khi đang chạy. Phải phân biệt dữ liệu trên API, cách cấp dữ liệu vào container và cách chương trình đọc dữ liệu đó.

## 1. Challenge và phạm vi

App demo cần DB_HOST, DB_PORT và LOG_LEVEL, không đóng các giá trị vào image. Học viên tự tạo ConfigMap, nối env, rollout và bổ sung mounted file; mentor chỉ inspect và lưu tài liệu, không sửa hoặc triển khai workload thay học viên.

- Context `orbstack`, namespace `default`.
- Deployment `app-buoi8`, một replica, image `busybox:1.36`.
- ConfigMap `app-config-buoi8`, các giá trị DB_HOST/DB_PORT giữ `postgresql`/`5432`; LOG_LEVEL lần lượt INFO, DEBUG và WARN.
- Script chỉ in cấu hình, không kết nối PostgreSQL hoặc điều khiển verbosity của một ứng dụng thật.
- Không tạo DB, Service, Ingress, PVC hoặc cấp credential thật cho bài.

Lúc đầu mentor giao challenge trước khi giải thích đủ nền. Học viên yêu cầu được hướng dẫn; mentor bổ sung vai trò resource, các field tham chiếu và ví dụ, không yêu cầu học thuộc YAML.

## 2. ConfigMap và runtime config

ConfigMap là API object giữ dữ liệu không nhạy cảm dạng key/value. `metadata.name` định danh bộ cấu hình; `data` chứa các key và giá trị string. DB_HOST/DB_PORT/LOG_LEVEL là key do ứng dụng sử dụng, không phải từ khóa đặc biệt của Kubernetes.

ConfigMap không phải Pod, không chạy chương trình, không dựng database và không tự đưa env vào mọi container. Pod phải tham chiếu nguồn config; chương trình phải đọc env hoặc file để dùng giá trị.

Image giữ code/công cụ ứng dụng. ConfigMap giữ cấu hình cho môi trường chạy; đổi config không cần rebuild image. Trong lab, các Pod qua ba giai đoạn giữ cùng tag và image digest.

**Không dùng ConfigMap cho password hoặc token.** ConfigMap không cung cấp tính bí mật/mã hóa. Secret là abstraction dành cho dữ liệu nhạy cảm nhưng cũng không có nghĩa ai cũng bị cấm đọc hoặc dữ liệu mặc nhiên được bảo vệ tuyệt đối; quyền truy cập và cấu hình bảo mật cluster vẫn quan trọng. Chi tiết Secret thuộc Buổi 09.

## 3. Hai cách nhận cấu hình

| Cách | Hành vi | Điều ứng dụng phải làm |
|---|---|---|
| Env qua configMapKeyRef | Giá trị được cấp khi container khởi tạo; process đang chạy không tự nhận giá trị mới chỉ vì ConfigMap đổi. | Đọc env; tạo Pod mới là cách đã thực hành để nhận config mới. |
| File qua ConfigMap volume | Kubelet cập nhật projected file sau khi nguồn đổi, có độ trễ đồng bộ/cache. | Đọc lại, poll hoặc reload file. Chỉ đọc lúc startup thì file đổi chưa làm cấu hình trong app đổi. |

Env phù hợp key/value đơn giản; file phù hợp ứng dụng đọc file config hoặc nội dung nhiều dòng. Trong bài giữ cả hai cách để so sánh, không chọn một cách rồi coi cách kia không cần học.

Khác biệt quan trọng: thêm mount/script vào Pod template tạo rollout mới; sau khi mount đã hoạt động, chỉ đổi dữ liệu ConfigMap có thể cập nhật file trong container đang chạy mà không thay Pod.

## 4. Field đã dùng

| Field | Vai trò |
|---|---|
| ConfigMap `metadata.name` | `app-config-buoi8`, tên resource làm nguồn. |
| ConfigMap `data` | Ba key/value; DB_PORT được viết `"5432"` để là string. |
| Container `env[].name` | Tên biến môi trường mà chương trình đọc. |
| `valueFrom.configMapKeyRef.name` | Tên ConfigMap trong namespace của Pod. |
| `valueFrom.configMapKeyRef.key` | Key lấy từ data; không phải tên resource. |
| Pod template `volumes[].name` | `app-config`, tên nội bộ của volume trong Pod. |
| `volumes[].configMap.name` | Tham chiếu resource `app-config-buoi8`. |
| Container `volumeMounts[].name` | Khớp với volumes.name, không phải trực tiếp tên ConfigMap. |
| `volumeMounts[].mountPath` | Thư mục `/etc/app-config` trong container, không phải thư mục trên Mac. |
| `volumeMounts[].readOnly` | Container chỉ đọc config; không ngăn kubelet cập nhật projected data từ nguồn. |

Không dùng `items`, nên mỗi key thành một file cùng tên: DB_HOST, DB_PORT và LOG_LEVEL. Không dùng `subPath`; mount kiểu subPath không nhận cập nhật ConfigMap như thí nghiệm này.

Ví dụ tham chiếu một key qua env:

```yaml
env:
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: app-config-buoi8
        key: LOG_LEVEL
```

Nguồn volume ở `spec.template.spec`, cùng cấp với containers:

```yaml
volumes:
  - name: app-config
    configMap:
      name: app-config-buoi8
```

Mount ở bên trong container app, cùng cấp với image/env/command:

```yaml
volumeMounts:
  - name: app-config
    mountPath: /etc/app-config
    readOnly: true
```

## 5. Minh chứng thực hành

Các địa chỉ, tên và UID dưới đây là snapshot của lab, không phải giá trị dùng chung. Deployment giữ cùng UID `a7d1668b-c62c-4137-b2e5-0500c51fd843` qua các giai đoạn; ConfigMap giữ UID `fc43130b-77f5-47a0-b227-430737cee462` khi data đổi.

| Giai đoạn | Minh chứng |
|---|---|
| Env ban đầu | Revision 1, Deployment 1/1, Pod `app-buoi8-64d5f97bb9-4t8lj`, UID `2fddce27-77b3-4325-8509-fdf7e4886faa`, IP `192.168.194.20`; logs và printenv xác nhận INFO. |
| Sau đổi ConfigMap và rollout | Revision 2, restartedAt `2026-10-09T15:35:21+07:00`, Pod `app-buoi8-746f67974c-949c6`, UID `ecb51442-ed48-4167-a1e6-28c8a4925a17`, IP `192.168.194.21`; printenv/logs DEBUG. |
| Sau thêm mount/script | Revision 3, Pod `app-buoi8-d9bcdb575-xvzsz`, UID `7a51c060-36b8-4f07-9986-a765df4d0033`, IP `192.168.194.22`, Running/Ready, RESTARTS=0; cùng container in ENV DEBUG và FILE DEBUG khi khởi động. |
| Sau chỉ đổi ConfigMap sang WARN | ConfigMap live WARN; current printenv vẫn DEBUG, cat file trả WARN. Lịch sử logs của cùng container chuyển FILE DEBUG sang WARN, ENV giữ DEBUG, không restart. |

Logs quan trọng, thời gian theo giờ Việt Nam:

- 16:31:25: container bắt đầu in ENV LOG_LEVEL DEBUG và FILE DEBUG.
- 16:44:55: dòng file cuối trong lịch sử còn DEBUG.
- 16:45:25: dòng file đầu tiên có WARN, env vẫn DEBUG.
- 16:52:55: tiếp tục ENV DEBUG/FILE WARN; Pod hiện tại RESTARTS=0.

Timestamps gốc là UTC: 09:31:25Z, 09:44:55Z, 09:45:25Z và 09:52:55Z. Không đo được độ trễ chính xác từ lúc apply ConfigMap vì không có timestamp apply.

Tất cả giai đoạn dùng `busybox:1.36`, cùng digest `sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662`. Snapshot chứng minh image dùng trong container giữ nguyên, không chứng minh tag này bất biến mãi mãi.

Không có raw output riêng ở thời điểm ConfigMap đã DEBUG nhưng Pod env cũ còn INFO. Không ghi mốc trung gian đó là đã quan sát; thí nghiệm file sau đó có chứng cứ trực tiếp nguồn/file WARN trong khi env của container giữ DEBUG.

## 6. App đọc lại file

Script thực tế trong Deployment:

```sh
while true; do
  printf 'ENV: DB_HOST=%s DB_PORT=%s LOG_LEVEL=%s\n' \
    "$DB_HOST" "$DB_PORT" "$LOG_LEVEL"
  printf 'FILE: LOG_LEVEL=%s\n' "$(cat /etc/app-config/LOG_LEVEL)"
  sleep 30
done
```

Mỗi vòng mở và đọc lại file theo path. Nhờ vậy sau khi kubelet cập nhật file, app demo in giá trị mới. Chu kỳ 30 giây là chu kỳ đọc của app, không phải cam kết mọi cập nhật ConfigMap xuất hiện sau đúng 30 giây.

Nếu thay Pod ở trạng thái hiện tại, env của container mới sẽ lấy WARN từ ConfigMap hiện tại. DEBUG/WARN là trạng thái của container đã khởi tạo trước khi nguồn đổi, không phải giá trị cố định trong manifest.

## 7. Review và phần cần bổ sung

| Câu review | Câu trả lời / đánh giá |
|---|---|
| Vì sao env DEBUG nhưng file WARN trên cùng Pod? | Học viên phân biệt giá trị env được cấp khi khởi tạo/restart với file theo cập nhật ConfigMap. Đạt ý chính. Trong lab đã kiểm chứng thay Pod qua rollout, không thử riêng container crash/restart trong cùng UID Pod. |
| App chỉ đọc file lúc startup có dùng config mới không? | Học viên nêu cần cơ chế đọc lại file. Đạt; mentor bổ sung reload hoặc thay Pod là lựa chọn khi app không đọc lại được, không mặc định file đổi là app đã đổi. |
| Hai tên volume/reference khớp thế nào, ngoài OrbStack có cần PVC không? | Học viên trả lời đúng volumeMounts.name khớp volumes.name và configMap.name trỏ resource. Chưa biết PVC; đây là nội dung Buổi 12, không dùng kiến thức chưa học để đánh trượt. Mentor bổ sung ConfigMap volume do kubelet cung cấp, không dùng provisioner/PVC; không ghi học viên tự nêu đầy đủ phần này hoặc đã học PVC. |
| Password/token có nên ở ConfigMap không? | Học viên chọn không, nêu có thể xem value. Phân loại đúng nhưng lý do cần bổ sung: Secret cũng có thể được đọc khi có quyền; ConfigMap dành dữ liệu không nhạy cảm, không có tính bí mật/mã hóa. Bảo mật Secret phụ thuộc access control và cấu hình cluster, sẽ học ở Buổi 09. |

**Kết quả:** thực hành và concept chính ConfigMap đạt. Các phần mentor bổ sung được ghi rõ, không biến thành bằng chứng học viên đã triển khai ngoài lab, đã học PVC hoặc đã hiểu toàn bộ bảo mật Secret.

## 8. OrbStack và ngoài lab

ConfigMap env/volume là cơ chế Kubernetes chuẩn. Bài không dựa vào DNS local, khả năng Mac gọi ClusterIP, LoadBalancer hoặc StorageClass/provisioner của OrbStack.

- Resource ConfigMap tồn tại trên API, trong namespace mà Pod tham chiếu.
- Kubelet trên node cấp env lúc khởi tạo container và cập nhật ConfigMap projected file theo cơ chế đồng bộ/cache.
- App chịu trách nhiệm đọc config và reload/poll khi cần.
- Trên cluster self-managed hoặc managed, cùng field name/key/volume/mount vẫn cần đúng; không cần thêm hệ thống cấp đĩa cho riêng ConfigMap volume.

Debug theo lớp: kiểm tra data/tên/namespace ConfigMap, Pod spec và Events, đường dẫn/file bên trong container, rồi cách app đọc config và logs. Đừng sửa StorageClass khi lỗi thực tế là tham chiếu ConfigMap hoặc mountPath.

**Giới hạn:** chỉ kiểm chứng trên OrbStack. Không kiểm tra kubelet cache strategy, encryption at rest hoặc RBAC riêng cho config, không thực hành subPath, app production reload, PV/PVC hoặc cluster ngoài lab.

## 9. Command để ôn

Các command đọc dưới đây chỉ dành cho config không nhạy cảm của bài; không áp dụng thói quen xuất toàn bộ YAML/env cho Secret:

```bash
kubectl --context=orbstack -n default get configmap app-config-buoi8 -o yaml
kubectl --context=orbstack -n default get deployment,pod -l app=app-buoi8 -o wide
kubectl --context=orbstack -n default get pod -l app=app-buoi8 \
  -o custom-columns=NAME:.metadata.name,UID:.metadata.uid
kubectl --context=orbstack -n default logs deployment/app-buoi8 --tail=8 --timestamps=true
kubectl --context=orbstack -n default exec deployment/app-buoi8 -- printenv LOG_LEVEL
kubectl --context=orbstack -n default exec deployment/app-buoi8 -- cat /etc/app-config/LOG_LEVEL
```

Các thao tác đã do học viên thực hiện khi cần: apply ConfigMap, apply Deployment sau chỉnh template, `rollout restart deployment/app-buoi8`, `rollout status deployment/app-buoi8 --timeout=120s`. Không cần chạy lại để được tính hoàn thành.

## 10. Liên hệ Data Engineering

- App ingestion có thể giữ image và đổi địa chỉ DB/endpoint hoặc log-level config theo môi trường.
- File config phù hợp chương trình đọc file cấu hình, nhưng phải xác định đọc lúc startup hay hỗ trợ reload.
- Khi có nhiều replica, cần kiểm tra instance nào đã nhận config mới; không suy ra tất cả app đã cập nhật chỉ từ một ConfigMap trên API.
- Credential không trộn vào bộ config không nhạy cảm hoặc ghi ra logs để chứng minh app nhận dữ liệu.

**Buổi 08 hoàn thành, tiến độ 8/28.** Buổi tiếp theo là [Buổi 09 - Secret](../roadmap/buoi-hoc/09-secret.md).

## Tài liệu tham khảo

- [Kubernetes ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/).
- [Configure a Pod to Use a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/).
- [Updating Configuration via a ConfigMap](https://kubernetes.io/docs/tutorials/configuration/updating-configuration-via-a-configmap/).
- [ConfigMap Volume](https://kubernetes.io/docs/concepts/storage/volumes/#configmap).
- [Object Names and IDs](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/).
- [Secrets Good Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/).
