# Hướng dẫn riêng cho lộ trình k3d

Phạm vi: `roadmap-k3d/` và các thư mục con. Đây là khóa hiện hành; khóa OrbStack cũ đã học xong và được xoá khỏi repo.

- Tuân thủ quy tắc mentor ở root và [quy tắc học và mentor](huong-dan-hoc-va-mentor.md), đặc biệt mục 1.4, 1.5, lý thuyết/cấu hình trước thực hành và checkpoint trắc nghiệm. Khi học khóa mới, đọc thêm `README.md`, `dinh-huong-va-cach-hoc.md`, `lab-va-hop-dong-nen-tang.md`, `tien-do-hoc-tap.md` và bài đang học của thư mục này.
- Tiến độ khóa này chỉ ghi trong `tien-do-hoc-tap.md` ở đây. Không dựng lại checklist hoặc tài nguyên khóa cũ; việc học viên xác nhận đã học xong khóa cũ là đầu vào lập kế hoạch, không phải bằng chứng runtime của khóa này.
- Mục tiêu: DE hiểu concept, đọc manifest/Helm values, nhận diện phụ thuộc nền tảng và trao đổi đúng với DevOps. Không yêu cầu viết YAML từ trí nhớ; không biến khóa thành đào tạo quản trị cluster.
- Mỗi lần chỉ dạy một khối nhỏ. Đọc bài là chuẩn bị, không đồng nghĩa đã dạy hoặc học viên đã hiểu. Dùng 2–4 câu tình huống sau khối quan trọng; giải thích phần chưa chắc trước khi giao lab.
- Học viên tự tạo/sửa/xóa workload, tạo cluster hoặc mô phỏng sự cố. Mentor chỉ chuẩn bị scaffold sau khi giải thích và kiểm tra chỉ đọc. Không dùng quyền admin của lab làm mô hình quyền DE ngoài thực tế.
- Phải kiểm context/namespace trước mọi kiểm tra live. Không chạm cluster `orbstack` hoặc tài nguyên còn sót của khóa cũ. Thí nghiệm node chỉ trên agent của cluster mới, có phạm vi và cách phục hồi được học viên hiểu trước.
- Mỗi tiện ích k3d/K3s/OrbStack phải được đối chiếu với thành phần, cấu hình, cách debug ngoài lab và giới hạn minh chứng. Không coi ServiceLB, local-path, image import hay DNS host là mặc định của mọi Kubernetes cluster.
- Không in/giải mã Secret, token, kubeconfig credential hoặc raw logs/render có thể chứa chúng. Dùng metadata, tên key, refs và kết quả kiểm tra đã lọc. Không lưu credential vào Git/chat/argv.
- Chốt version/image/chart/provider theo tài liệu đúng phiên bản trước mỗi lab; kiểm ARM64 và API hỗ trợ. Các link `stable`/`latest` trong bài là điểm tra cứu, không phải version pin.
- Khi bài đạt, tạo tổng kết tại `after-study/NN-ten-bai.md` bên trong thư mục này và cập nhật tiến độ mới. Khi cần scaffold, dùng `thuc-hanh/NN-ten-bai/` bên trong thư mục này; không tạo trước toàn bộ manifests hay thư mục rỗng.
- Khi chỉ được yêu cầu lập kế hoạch/tài liệu, không bắt đầu lab, tự đánh dấu bài đang học hoặc gọi thao tác thay đổi cluster.
