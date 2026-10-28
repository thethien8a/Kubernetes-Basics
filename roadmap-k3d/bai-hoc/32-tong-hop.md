# Bài 32 — Từ yêu cầu dịch vụ tới bàn giao DevOps

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](31-airflow.md)

**Đầu vào:** các bài nền tảng và integration trước đã đạt. **Đầu ra:** tự đọc một bộ cấu hình, phát hiện dependency thiếu và nghiệm thu dịch vụ mà không cần tự viết YAML từ đầu.

## 1. Khối kiến thức

- Đầu ra của DE là yêu cầu có thể thực thi/kiểm tra: loại workload, dữ liệu, kết nối, tài nguyên, identity, observability và recovery. “Cần một cluster để chạy app” chưa đủ cho platform team.
- Phải tách cấu hình ứng dụng với khả năng nền tảng đã có/còn thiếu; không cài một chart rồi suy mọi dependency đã được cung cấp.
- Chấp nhận rủi ro là quyết định có chủ đích: một replica/local-path có thể phù hợp sandbox, không đáp ứng yêu cầu chịu mất node nếu chưa có cơ chế khác. Phải báo chênh lệch thay vì dùng lời hứa HA.

## 2. Đọc cấu hình

Mentor cung cấp manifest/values scaffold cho một pipeline nhỏ: Job đọc fixture giả, ghi kết quả vào PostgreSQL của lab mới. Chỉ cần Job + DB + client kiểm tra; không bắt dựng lại full lakehouse. Trước khi chạy, học viên hoàn thiện bảng:

| Nhóm | Cần chỉ ra từ cấu hình |
|---|---|
| Vòng đời/compute | Vì sao Job/StatefulSet; requests/limits, deadline/retry và rerun safety. |
| Placement/storage | Node requirements, PVC/class/mount, dữ liệu khi Pod hoặc node mất. |
| Network/identity | Source → destination/port, Service/DNS/policy, Secret refs và API permissions thực sự cần. |
| Vận hành | Probes phù hợp, logs/metrics, backup/restore, cleanup và trách nhiệm từng bên. |

## 3. Kiểm tra hiểu trước lab

1. Requirement đòi phục hồi khi mất node, nền tảng chỉ xác nhận local-path một node. Nên làm gì? **A.** Chấp nhận vì PVC Bound. **B.** Nêu gap, yêu cầu backend/recovery phù hợp hoặc thống nhất giảm yêu cầu. **C.** Tăng Job retries để dữ liệu tự sao chép.
2. Job không gọi Kubernetes API, chỉ gọi SQL. Có cần mặc định cấp tạo Pods cho SA của Job không? **A.** Có. **B.** Có nếu chạy nhiều node. **C.** Không, cấp theo chức năng thực sự cần.

## 4. Thực hành và bằng chứng

1. **Phân tích trước triển khai:** chốt fixture, phép tính kỳ vọng độc lập, key chống trùng và cách rerun. Đọc scaffold; mentor đưa hai dependency còn thiếu trên giấy để học viên xác định câu hỏi cần gửi DevOps, không âm thầm phá hạ tầng.
2. **Yêu cầu nền tảng:** hoàn thiện [hợp đồng](../lab-va-hop-dong-nen-tang.md), đánh dấu đã có/cần cấp/chưa kiểm chứng. Mentor đóng vai DevOps trả lời bằng inventory lab thật; không tự cấp quyền hay cài thêm thay học viên.
3. **Thực thi:** học viên triển khai trong namespace/đích dữ liệu mới, kiểm Job outcome và SQL readback đúng dữ liệu. Tự rerun theo thiết kế đã chốt, xác nhận không tạo bản ghi trùng ngoài ý định. Không overwrite dữ liệu khóa cũ.
4. **Sự cố và phục hồi:** học viên chạy một biến thể có lỗi an toàn do mentor chuẩn bị, thuộc tầng đã học; tự điều tra/sửa, mentor kiểm evidence đúng lần. Dùng lại evidence backup/restore Bài 29 nếu phù hợp, không yêu cầu phá dữ liệu thêm.

**Đạt khi:** tất cả tiêu chí dưới đây có bằng chứng hoặc giới hạn được ghi rõ; phần thực hành bắt buộc không được thay bằng “chưa kiểm chứng”.

- Đọc đúng các field/ref và giải thích lựa chọn, không chấm khả năng tự gõ boilerplate.
- Hợp đồng đủ network/storage/resources/images/identity/observability/recovery, phân biệt DE làm với platform cung cấp.
- Có Job outcome, đúng SQL readback và rerun không trùng ngoài ý định; đối chiếu expected độc lập với implementation.
- Có một failure/recovery đúng tầng, gắn UID/thời gian, không credential trong evidence.
- Nêu được giới hạn multi-node chung host, local storage, lab load và phần chưa đáp ứng production.
- Có hướng dẫn bàn giao ngắn: cách kiểm tra, dữ liệu cần giữ, ai xử lý phần nào, cách quay lại checkpoint an toàn.

## 5. Cần DevOps và giới hạn lab

- Đầu ra cuối là bản yêu cầu/bàn giao có thể dùng cho một team platform, không là danh sách công cụ phải cài cho đủ tên. Được phép nói “khả năng nền tảng hiện tại chưa đáp ứng”.
- Không gửi yêu cầu ra hệ thống thật hoặc thay cluster công ty trong khóa. Tốt nghiệp chứng minh hiểu và sử dụng Kubernetes trong phạm vi bài, không chứng nhận vận hành production/HA/bảo mật toàn diện.

**Nguồn:** [Hợp đồng nền tảng của khóa](../lab-va-hop-dong-nen-tang.md), [Kubernetes application debugging](https://kubernetes.io/docs/tasks/debug/debug-application/).
