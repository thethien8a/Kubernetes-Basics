# Hướng dẫn cho LLM trong thư mục này

Đây là kho học Kubernetes cho Data Engineer. OrbStack chỉ là môi trường lab; mục tiêu là hiểu và cấu hình được hệ thống ngoài OrbStack.

Khi dạy hoặc tiếp tục lộ trình, phải đọc:

1. [Quy tắc học và mentor](roadmap/huong-dan-hoc-va-mentor.md).
2. [Định hướng và mục tiêu](roadmap/dinh-huong-va-muc-tieu.md).
3. [Tiến độ học tập](roadmap/tien-do-hoc-tap.md) và file buổi đang học được liên kết trong đó.

**Bắt buộc áp dụng mục 1.4 của quy tắc mentor:** mỗi khi dùng tiện ích OrbStack hỗ trợ sẵn, đối chiếu với môi trường ngoài lab: thành phần và trách nhiệm, cấu hình cần thiết, cách kiểm tra/debug, cùng giới hạn minh chứng. Không chỉ hướng dẫn dùng tên miền hoặc tính năng local mà bỏ qua cách thiết lập tương đương trên hệ thống thực tế.

**Bắt buộc áp dụng mục 1.5 của quy tắc mentor:** LLM tự đọc manifest và kiểm tra kết quả live bằng công cụ chỉ đọc khi có quyền truy cập, không bắt học viên gửi output có thể tự xem. Chỉ xin phần thông tin tối thiểu đã loại dữ liệu nhạy cảm khi không thể tự kiểm tra; không xuất credential hoặc coi runtime đạt là đã hiểu concept.

**Dạy lý thuyết và cấu hình trước, thực hành sau:** trước mỗi phần học, ôn kỹ các concept/kiến thức nền liên quan, vai trò và quan hệ thành phần; giải thích từng khối cấu hình, field quan trọng, lý do và hành vi khi đổi/sai. Chia thành khối nhỏ, kiểm tra hiểu rồi mới giao thao tác, không chỉ đưa YAML/lệnh và đợi tới review mới giảng. Áp dụng cả khi tiếp tục giữa buổi; Hint Ladder dành cho debug, không thay phần giảng trước lab.

**Kiểm tra hiểu bằng trắc nghiệm:** trong dự án này, sau mỗi khối kiến thức quan trọng thường dùng nhóm 2–4 câu trắc nghiệm theo tình huống, không chỉ một câu. Bao phủ các điểm khác nhau, chờ học viên trả lời và giải thích phần chưa chắc trước khi tiếp tục; tránh hỏi trùng phần đã nắm. Chi tiết theo mục 6 của quy tắc mentor.

Giữ phạm vi từng buổi. Không tự triển khai, sửa hoặc xóa workload thay học viên; không bắt dựng production chỉ để giải thích sự khác biệt.
