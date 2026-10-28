# Bài 27 — Helm values và resource được render

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](26-quota-admission.md) · [Tiếp](28-debug-va-observability.md)

**Đầu vào:** đọc resource, config refs và yêu cầu nền tảng. **Đầu ra:** đánh giá chart trước khi cài mà không phải tự viết Helm templates.

## 1. Khối kiến thức

- Chart gồm templates/default values và metadata/dependencies; release là một bản cài cụ thể. Values là đầu vào render của chart, không phải Kubernetes manifest để apply trực tiếp.
- Chart version, appVersion và image tag là các thông tin khác nhau. Override image có thể làm entrypoint/config không tương thích; không thay image chỉ vì tên gần giống.
- Một values key chỉ có tác dụng nếu chart/template dùng nó. Sai key có thể bị schema từ chối hoặc bị bỏ qua tùy chart; render mới cho thấy resource thực tế, kể cả dependency/PVC/RBAC bất ngờ.
- Helm hooks, migration và readiness có thứ tự/phụ thuộc. `--wait` không sửa dependency vòng; phải đọc lifecycle đúng chart/Helm version. Rollback release không rollback dữ liệu ứng dụng.

## 2. Đọc cấu hình

| Nguồn cấu hình | Điều cần lần theo |
|---|---|
| Chart metadata `version`, `appVersion`, dependencies | Pin chart và đọc dependency, không coi appVersion luôn là image sẽ chạy. |
| Values về image/resources/service/ingress/persistence | Tên key phải lấy từ chart đang học; lần sang field của Deployment/Service/PVC render. |
| Values về existing Secret/ServiceAccount | Kiểm chart dùng ref hay tự tạo; không đoán tên key giữa các charts. |
| Rendered annotations `helm.sh/hook` và Jobs/init containers | Xác định cài đặt/migration/chờ readiness theo thứ tự nào. |

## 3. Kiểm tra hiểu trước lab

1. Đặt một key values không được template dùng và không bị schema từ chối. Có chắc thay đổi resource không? **A.** Có. **B.** Không. **C.** Chỉ cần upgrade hai lần.
2. Chart rollback thành công sau migration phá dữ liệu có chứng minh dữ liệu đã phục hồi không? **A.** Có. **B.** Có nếu release Ready. **C.** Không, cần kế hoạch dữ liệu riêng.

## 4. Thực hành và bằng chứng

1. Chọn chart demo nhỏ, nguồn và version cố định, không credential thật; mentor giải thích chart/default values trước khi giao thao tác. Học viên lập inventory resources/dependencies dự kiến.
2. Render hai bộ values chỉ khác một cấu hình quan trọng, so field tương ứng và defaults. Nếu chart render Secret, lọc trong bộ nhớ; không dump/lưu raw manifests nhạy cảm hoặc raw live values.
3. Học viên cài một release riêng sau review, kiểm trạng thái và HTTP marker ứng dụng. Đổi một values được chart hỗ trợ rồi kiểm cả render và live result, không chỉ dòng “upgrade succeeded”.

**Đạt khi:** nối được values → template/resource → hành vi, chỉ ra class/Secret/SA/controller phải tồn tại và một mặc định cần đánh giá. Không yêu cầu viết template từ đầu.

## 5. Cần DevOps và giới hạn lab

- Cần chart registry/version được duyệt, quyền release/namespace, class/controller/Secret external, policy upgrades và ownership CRDs nếu chart có. Helm không tự cấp mọi dependency ngoài chart.
- Chart chạy được trên k3d không chứng minh đáp ứng admission/storage/network của cluster công ty. Không uninstall tùy tiện release có dữ liệu; đọc resource retention trước.

**Nguồn:** [Helm values files](https://helm.sh/docs/chart_template_guide/values_files/), [Helm hooks](https://helm.sh/docs/topics/charts_hooks/).
