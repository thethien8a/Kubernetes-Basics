# Bài 01 — Kiến trúc và ranh giới DE–DevOps

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Tiếp: Bài 02](02-lab-k3d-va-context.md)

**Đầu vào:** đã học khóa cơ bản; chưa cần cluster mới. **Đầu ra:** nói được ai tiếp nhận yêu cầu, ai thực thi và phần nào nền tảng phải cung cấp.

## 1. Khối kiến thức

- **Yêu cầu và thực thi:** API server tiếp nhận resource, lưu trạng thái qua datastore; controller đưa actual state về desired state. Scheduler chọn node cho Pod chưa được gán; kubelet và container runtime trên node thực thi. `kubectl` là client, không giữ workload sống bằng phiên terminal.
- **API không đồng nghĩa năng lực hạ tầng:** PVC là yêu cầu storage; provisioner/backend mới cấp nơi chứa byte. Ingress là rule; controller và đường mạng mới xử lý request. Cài CRD chỉ đăng ký API tùy biến, chưa thay controller thực thi nó.
- **Ba lớp môi trường:** Kubernetes là hệ thống/API; K3s là bản phân phối có cách đóng gói và add-ons riêng; k3d tạo các K3s node trong Docker. OrbStack cung cấp môi trường Docker trên Mac, không phải mọi tính năng của cluster mới.
- **Ranh giới trách nhiệm:** DE mô tả nhu cầu và cấu hình dịch vụ; DevOps/platform cung cấp hoặc xác nhận khả năng nền tảng, quyền và quy trình vận hành. Lab cho phép đóng cả hai vai để hiểu, không suy quyền admin là yêu cầu của ứng dụng.

## 2. Đọc cấu hình

| Resource/field cần nhận diện | Ý nghĩa và điều chưa được bảo đảm |
|---|---|
| Deployment `spec.replicas` | Yêu cầu số Pod; chưa bảo đảm cluster đủ capacity hoặc ứng dụng phục vụ được. |
| PVC `spec.storageClassName` | Chọn class; không cài driver hay tạo storage backend bằng tên class. |
| Ingress `spec.ingressClassName` | Chọn lớp controller; không tự tạo DNS record hoặc public IP. |
| Resource `status.conditions` | Kết quả quan sát được; đọc reason/message để biết bước nào chưa đạt. |

Chỉ đọc các trích đoạn này, chưa cần học hết storage/Ingress. Các bài sau sẽ giải thích cấu hình chi tiết trước khi triển khai.

## 3. Kiểm tra hiểu trước lab

1. API nhận PVC nhưng không có provisioner phù hợp. Kết luận nào đúng? **A.** YAML hợp lệ nên đã có disk. **B.** Cần kiểm class/provisioner/backend. **C.** Restart ứng dụng luôn giải quyết được.
2. Đóng terminal sau khi tạo Deployment có làm controller dừng không? **A.** Có vì kubectl là controller. **B.** Chỉ khi có nhiều node. **C.** Không, controller chạy trong cluster.

## 4. Thực hành và bằng chứng

1. Với ba nhu cầu “chạy API”, “giữ dữ liệu”, “mở UI”, lập chuỗi nhu cầu → resource → thành phần thực thi → bằng chứng mong đợi.
2. Mentor đưa hai trường hợp giả định: resource hợp lệ nhưng thiếu controller; controller có nhưng thiếu backend/capacity. Học viên chỉ ra thông tin cần xin thêm, không tự kết luận nguyên nhân từ một trạng thái Pending.
3. Điền phần đầu [hợp đồng nền tảng](../lab-va-hop-dong-nen-tang.md) cho một dịch vụ DE quen thuộc. Không tạo cluster hoặc cài add-on.

**Đạt khi:** phân loại đúng ba lớp và giải thích được ít nhất một ca “API đã nhận nhưng dịch vụ chưa hoạt động”. Bằng chứng của bài là sơ đồ/phân loại và review concept, không phải runtime.

## 5. Cần DevOps và giới hạn lab

- Yêu cầu đầu tiên: môi trường/namespace được cấp, danh sách khả năng sẵn có, tài liệu truy cập và phạm vi quyền; chưa xin `cluster-admin` để tránh phải tìm hiểu.
- Ngoài lab, hỏi ai quản lý control plane, nodes, network và storage. Managed Kubernetes có thể chuyển một số trách nhiệm cho nhà cung cấp, không xóa các dependency này.

**Nguồn:** [Kubernetes components](https://kubernetes.io/docs/concepts/overview/components/), [k3d](https://k3d.io/stable/).
