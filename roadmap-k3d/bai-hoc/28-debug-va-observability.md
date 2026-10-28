# Bài 28 — Quan sát và trao đổi sự cố

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](27-helm.md) · [Tiếp](29-postgresql.md)

**Đầu vào:** các tầng lifecycle, scheduling, network, storage và access. **Đầu ra:** báo lỗi bằng evidence đúng phạm vi, không đổ mặc định cho Kubernetes hoặc xin quyền quá rộng.

## 1. Khối kiến thức

- Phân loại theo bước: API chưa nhận → controller chưa tạo Pod → chưa schedule → chưa pull/mount/start → không Ready → network/app/data lỗi. Một symptom có nhiều nguyên nhân; dùng quan sát để loại giả thuyết.
- Status/Events/logs/metrics trả lời các câu khác nhau. Events có retention giới hạn; `logs --previous` thường chỉ giúp container instance trước trong Pod còn được truy cập, không là kho log lâu dài cho mọi Pod đã xóa.
- Metrics API thường phục vụ số đo tài nguyên ngắn hạn; lịch sử, truy vấn, alert và lưu logs cần backend/agent riêng. Không cài cả Prometheus/Loki stack chỉ để học cách yêu cầu khả năng quan sát.
- Bằng chứng phải gắn context/namespace/UID/container/thời gian/lần chạy. Log “SUCCESS” của lần cũ không chứng minh lần mới đạt; trước đọc logs phải xét khả năng lộ credential/dữ liệu.

## 2. Đọc cấu hình

| Dữ liệu/field | Câu hỏi trả lời |
|---|---|
| Workload/Pod `status.conditions`, Events reason/message | Bước nào chưa đạt và component nào báo? |
| Pod `metadata.ownerReferences`, `containerStatuses` | Đúng controller/attempt/container chưa; Waiting hay Terminated, restart count thế nào? |
| Container resources/probes, Service endpoints, PVC conditions | Có bằng chứng cấu hình và runtime cùng chỉ tới một tầng không? |
| Logging/metrics destination và retention | Sau khi Pod mất còn truy vết ở đâu; ai được phép xem? |

## 3. Kiểm tra hiểu trước lab

1. Pod hiện tại lỗi nhưng log lần chạy hôm qua có SUCCESS. Có thể chốt đã phục hồi không? **A.** Không. **B.** Có nếu cùng app name. **C.** Có nếu cùng namespace.
2. Không có Metrics API có nghĩa ứng dụng không dùng CPU/RAM không? **A.** Có. **B.** Không, đang thiếu đường quan sát đó. **C.** Chỉ cần đổi namespace.

## 4. Thực hành và bằng chứng

1. Mentor chuẩn bị scaffold challenge với ba lỗi an toàn đã thuộc phần học: selector sai, request không schedule được, ref config thiếu. Học viên tạo từng ca riêng; không chèn lỗi vào workload đang dùng hoặc dữ liệu thật.
2. Học viên khoanh tầng và sửa tối thiểu, lưu symptom → giả thuyết → bằng chứng → thay đổi → kiểm lại. Mentor dùng Hint Ladder và tự kiểm chỉ đọc, không sửa hộ.
3. Viết một yêu cầu hỗ trợ DevOps theo mẫu dưới; không gửi ra ngoài thật. Chỉ đề nghị kiểm tra/phân quyền cần thiết, tách quan sát khỏi suy luận.

**Mẫu báo lỗi:** môi trường/namespace + thời gian/UID → expected/actual → source/destination hoặc resource liên quan → bằng chứng đã lọc → giả thuyết đã loại → phần cần DevOps xác nhận → mức ảnh hưởng. Không đính raw kubeconfig/Secret/env.

**Đạt khi:** ba ca có nguyên nhân/recovery đúng, ít nhất một yêu cầu hỗ trợ đủ để người khác điều tra mà không cần đoán lại bối cảnh. Không đòi nhớ cú pháp debug.

## 5. Cần DevOps và giới hạn lab

- Cần quyền đọc workload/Events/logs, metrics/dashboard, log retention sau Pod deletion và quy trình escalation. `exec`/debug containers là quyền riêng có rủi ro, không mặc định cấp để xem mọi Secret.
- Snapshot local không chứng minh toàn bộ lịch sử lỗi. Không có bằng chứng thì ghi thiếu, không bịa thứ tự thao tác hoặc nguyên nhân duy nhất.

**Nguồn:** [Debug applications](https://kubernetes.io/docs/tasks/debug/debug-application/), [Logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/).
