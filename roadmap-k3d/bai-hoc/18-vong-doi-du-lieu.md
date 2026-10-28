# Bài 18 — Các vòng đời của dữ liệu

[Mục lục](../README.md) · [Tiến độ](../tien-do-hoc-tap.md) · [Trước](17-networkpolicy.md) · [Tiếp](19-storageclass.md)

**Đầu vào:** container restart, Pod replacement và dữ liệu giả. **Đầu ra:** chỉ được byte đang ở đâu và sự kiện nào làm mất chúng.

## 1. Khối kiến thức

- File có sẵn trong image khác file ghi vào writable layer khi container chạy. Container mới không phải bản phục hồi writable layer cũ.
- `emptyDir` thuộc vòng đời Pod, có thể chia sẻ giữa các container và giữ qua container restart trong cùng Pod; Pod bị thay thì có emptyDir mới. Nó không phải persistent storage chỉ vì có mountPath.
- PVC tham chiếu storage có vòng đời tách khỏi Pod, nhưng độ bền còn phụ thuộc backend và cách xóa. Giữ dữ liệu qua Pod replacement không chứng minh chịu mất node/disk.
- `emptyDir.medium: Memory` dùng RAM; scratch/shuffle của pipeline là nhu cầu tài nguyên riêng, không mặc định miễn phí. File log, checkpoint và dữ liệu nghiệp vụ có yêu cầu retention khác nhau.

## 2. Đọc cấu hình

| Field | Quan hệ cần kiểm |
|---|---|
| PodSpec `volumes[].emptyDir` | Nguồn volume theo Pod; đọc medium và sizeLimit, không xem nó là backup. |
| PodSpec `volumes[].persistentVolumeClaim.claimName` | Ref PVC cùng namespace; cấp storage học ở Bài 19. |
| Container `volumeMounts[].name`, `mountPath` | Nối volume name tới đường app đọc/ghi; chỉ mount đúng không bảo đảm app dùng đường đó. |
| Container `resources.requests/limits.ephemeral-storage` | Đọc nhu cầu scratch/log local, khác dung lượng PVC; enforcement phụ thuộc cách node theo dõi filesystem. |

## 3. Kiểm tra hiểu trước lab

1. Container restart nhưng Pod UID không đổi. Marker trong emptyDir có nhất thiết mất không? **A.** Có. **B.** Không, emptyDir vẫn thuộc Pod đó. **C.** Nó tự chuyển vào PVC.
2. App ghi `/tmp/result` nhưng PVC mount ở `/data`. Có thể nói output đã persistent chưa? **A.** Chưa, phải kiểm đường ghi thực tế. **B.** Rồi vì Pod có PVC. **C.** Chỉ cần tăng size claim.

## 4. Thực hành và bằng chứng

1. Học viên chạy Pod test có thư mục không mount và emptyDir; tạo marker khác nhau, không chứa sẵn trong image hoặc startup script.
2. Thử container restart có kiểm soát trong cùng Pod rồi Pod replacement ở lượt riêng; ghi UID/restart count và marker ở từng vị trí. Không dùng tên Pod làm bằng chứng cùng object.
3. Lập bảng writable layer/emptyDir/PVC với các sự kiện container restart, Pod replacement, node loss. PVC ở bước này là dự đoán để kiểm ở bài sau, không ghi đã thử.

**Đạt khi:** có đối chứng hai vòng đời và giải thích đúng vị trí ghi của ứng dụng. Không chạy chương trình làm đầy node disk để học ephemeral storage.

## 5. Cần DevOps và giới hạn lab

- Cần scratch budget, ephemeral-storage policy, nơi lưu log/checkpoint lâu dài và yêu cầu PVC nếu có. DE phân loại dữ liệu có thể tái tính với dữ liệu không thể mất.
- Volume mount chỉ là cách đưa storage vào container; loại nguồn quyết định vòng đời. K3d dùng disk/runtime của host, không đại diện failure domain độc lập.

**Nguồn:** [Volumes](https://kubernetes.io/docs/concepts/storage/volumes/), [Local ephemeral storage](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/).
