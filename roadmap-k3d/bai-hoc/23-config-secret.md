# Bài 23 — ConfigMap, Secret và thay đổi cấu hình

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](22-backup-va-reclaim.md) · [Tiếp](24-serviceaccount-rbac.md)

**Đầu vào:** mounts và Pod lifecycle. **Đầu ra:** lần theo nguồn config/credential mà không làm lộ chúng hoặc nhầm cập nhật Secret với rotation hệ thống đích.

## 1. Khối kiến thức

- ConfigMap chứa cấu hình không nhạy cảm, Secret dành cho dữ liệu nhạy cảm; base64 không phải mã hóa bảo mật. Cần quyền truy cập, chính sách lưu trữ và kiểm soát cách ứng dụng/log sử dụng dữ liệu.
- Env được đưa vào lúc container khởi động; thay resource không tự đổi env trong process đang chạy. Volume projection có thể cập nhật sau độ trễ, nhưng ứng dụng phải đọc lại; mount `subPath` không nhận cập nhật tự động như mount thông thường.
- Secret key là tên trong hợp đồng cấu hình, không nhất thiết là tên env hoặc tài khoản. `secretKeyRef` nối key tới env; URI connection có thể chứa credential dù tên biến không có chữ password.
- Đổi Secret không tự đổi mật khẩu đã lưu ở database/dịch vụ ngoài. Rotation cần phối hợp phía cấp credential, client reload/restart và thời gian chồng lấn phù hợp.

## 2. Đọc cấu hình

| Field | Quan hệ cần kiểm |
|---|---|
| Container `env[].valueFrom.configMapKeyRef` / `secretKeyRef` | Tên resource/key cùng namespace, env name có thể khác key. |
| Container `envFrom` | Đưa nhiều key vào env; cân nhắc chỉ cấp key cần thiết. |
| PodSpec `volumes[].configMap` / `secret`, Container `volumeMounts` | Tên/key/path/permissions và app đọc đường nào. |
| Container `volumeMounts[].subPath` | Mount một phần; hiểu giới hạn cập nhật trước khi chọn. |

## 3. Kiểm tra hiểu trước lab

1. ConfigMap đổi nhưng env của process cũ giữ nguyên có nhất thiết lỗi Kubernetes không? **A.** Có. **B.** Không, env không tự refresh. **C.** Chỉ đúng với Secret.
2. Secret chứa mật khẩu DB mới, DB đã khởi tạo từ trước. Restart client có tự đổi password trên DB không? **A.** Có. **B.** Chỉ khi dùng StatefulSet. **C.** Không, phải phối hợp cập nhật phía DB.

## 4. Thực hành và bằng chứng

1. Dùng ConfigMap không nhạy cảm với marker phiên bản; app test nhận cả env và mounted file, có cơ chế đọc lại đã giải thích.
2. Học viên đổi marker, quan sát file cập nhật/env cũ, sau đó thay Pod và kiểm env mới. Phân biệt config đã thay với app thật sự dùng config mới.
3. Với Secret test do học viên chuẩn bị an toàn, mentor chỉ kiểm type/key names/refs và app báo boolean “đã nạp”, không in giá trị, hash credential hoặc dump env. Không rotate credential khóa cũ.

**Đạt khi:** có evidence hai cách cập nhật khác nhau và biết truy vết ref/key mà không lộ dữ liệu; nêu kế hoạch rotation gồm cả service đích.

## 5. Cần DevOps và giới hạn lab

- Cần quy trình cấp/rotate credential, tên Secret/key, ownership, RBAC, encryption-at-rest và secret manager nếu tổ chức dùng. External Secrets/CSI secret integration cần controller/provider riêng, không tự có.
- Mounted Secret thành công chưa chứng minh IAM/SQL login đúng hoặc môi trường đã được audit bảo mật. Không lưu file chứa credential vào thư mục scaffold được Git theo dõi.

**Nguồn:** [ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/), [Secret](https://kubernetes.io/docs/concepts/configuration/secret/).
