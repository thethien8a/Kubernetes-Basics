# Buổi 09 — Secret

**Tuần 2 — Configuration, resources và storage.**

[Mục lục](../kubernetes_data_engineer_training_roadmap.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Quy tắc mentor](../huong-dan-hoc-va-mentor.md)

## Challenge

Quản lý:

```text
POSTGRES_USER
POSTGRES_PASSWORD
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
```

## Học

- Secret
- Inject Secret vào Pod
- Secret vs ConfigMap

## Lưu ý

Không được dạy người học rằng Kubernetes Secret mặc định đồng nghĩa với “được mã hóa an toàn tuyệt đối”.

Cần nhấn mạnh:

```text
Secret là abstraction phù hợp để quản lý dữ liệu nhạy cảm trong Kubernetes,
nhưng mức bảo mật thực tế còn phụ thuộc cấu hình cluster và storage encryption.
```

---

Sau review, cập nhật [tiến độ](../tien-do-hoc-tap.md) trước khi chuyển buổi.

**Trước:** [Buổi 08](08-configmap.md) · **Tiếp:** [Buổi 10 — CPU và Memory](10-cpu-va-memory.md).
