# Tổng kết buổi 19 — Hai tầng resource management

**Ngày học/chốt:** 2026-10-16, giờ Việt Nam. **Trạng thái:** Hoàn thành yêu cầu phân tích và review. **Tiến độ khi chốt:** 19/28.

[Challenge gốc](../roadmap/buoi-hoc/19-hai-tang-resource-management.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Master/Workers](../yaml/spark-buoi16.yaml) · [Job submit tham chiếu](../yaml/spark-buoi18-submit.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a14291-11b0-747f-b661-3b6279bdcb52)

> Buổi này yêu cầu phân tích hai case tài nguyên, không yêu cầu triển khai cấu hình sai hoặc cố gây OOM/throttling. Minh chứng gồm đối chiếu manifest, resource/registry live, cgroup đã đọc và các câu review học viên trả lời đúng. Các case 4 CPU/8 cores và 4 GiB/8 GiB là giả định, không phải thí nghiệm quá tải đã chạy. Mentor không sửa, apply, scale, restart workload hoặc submit lại application.

## 1. Mental model: ngân sách Spark không thay giới hạn container

Đây là Spark Standalone chạy bên trong Kubernetes: Executor là tiến trình trong Worker container, không phải Executor Pod riêng. Driver của demo client mode nằm trong Pod submit riêng.

```diagram
┌───────────────────────────────────────────┐
│ Kubernetes: Worker container              │
│ CPU/RAM limits dùng chung cho:            │
│   Worker daemon + Executor processes      │
│   bộ nhớ ngoài heap/Python khi có         │
└───────────────────────────────────────────┘
                    ▲
                    │ yêu cầu Worker daemon
                    │ khởi chạy Executor
┌───────────────────┴───────────────────────┐
│ Spark Master cấp theo ngân sách Worker    │
│ quảng bá và yêu cầu của application       │
└───────────────────────────────────────────┘
```

- Kubernetes scheduler dùng requests để xét chỗ đặt Pod. Requests không phải trần sử dụng; CPU request cũng ảnh hưởng tỷ trọng chia CPU khi tranh chấp.
- Kubelet/runtime cấu hình giới hạn; kernel Linux thực thi qua cgroups. Giới hạn container bao các tiến trình bên trong, không cấp một limit riêng cho từng Executor.
- Spark Master cấp tài nguyên theo inventory Worker và cấu hình application. Worker `--cores`/`--memory` không tự đồng bộ với Kubernetes limits.
- Một Executor phải vừa tài nguyên Spark còn lại trên một Worker; không cộng RAM hai Workers để tạo một heap lớn hơn trên một máy.

## 2. Cấu hình thật dùng để đối chiếu

| Field/khối | Giá trị trong lab | Ý nghĩa |
|---|---|---|
| Worker container `resources.requests.cpu` | `250m` | 0,25 CPU dùng cho scheduling và tỷ trọng CPU khi tranh chấp; không ghim core vật lý riêng. |
| Worker container `resources.requests.memory` | `768Mi` | Ngân sách xét chỗ đặt Pod, không phải trần RAM. |
| Worker container `resources.limits.cpu` | `"1"` | Quota thời gian CPU tương đương 1 CPU, dùng chung cho daemon/Executors. |
| Worker container `resources.limits.memory` | `2Gi` | Giới hạn RAM chung của container, gồm cả phần ngoài heap. |
| Worker args `--cores` | `1` | Ngân sách Spark cores quảng bá. |
| Worker args `--memory` | `512M` | Ngân sách cấp Executor, registry hiển thị 512 MiB; không phải RAM thực đang dùng. |
| Worker env `SPARK_DAEMON_MEMORY` | `256m` | Heap JVM Worker daemon, tách khỏi pool cấp Executor nhưng vẫn dùng RAM trong cùng container. |
| Submit `--executor-memory` | `512m` | Heap JVM của từng Executor, không phải tổng RAM tiến trình. |
| Submit `--executor-cores` | `1` | Spark cores cấp cho từng Executor. |
| Submit `--total-executor-cores` | `2` | Giới hạn tổng cores cho Executors của application, không gồm CPU Driver. |
| Driver container | Request `250m`/`512Mi`, limit `1` CPU/`1Gi`; Driver heap `512m` | Driver có ngân sách riêng trong Pod submit, không cộng vào pool Worker. |

Heap là vùng nhớ JVM quản lý cho đối tượng; cấu hình heap là mức tối đa, không phải RSS hoặc lượng RAM đã dùng ngay. Tổng RAM còn có daemon, bộ nhớ native/ngoài heap và Python processes nếu application sử dụng chúng. Không lấy toàn bộ container limit làm heap hoặc mặc định một tỷ lệ headroom đủ cho mọi job.

## 3. Case CPU: limit 4 CPU nhưng Worker quảng bá 8 cores

Giả định đủ RAM, application đã được cấp Executor 8 cores và có tám task tính toán nặng sẵn sàng; mỗi task cần 1 Spark core.

- Spark có thể cho tám task cùng ở trạng thái chạy theo ngân sách đã khai báo.
- Mọi tiến trình trong container vẫn chia chung quota tương đương 4 CPU. Khi dùng hết quota trong chu kỳ, kernel tạm ngừng cho chạy tiếp: CPU throttling.
- Khai báo 8 cores không tạo thêm CPU, không ghim tám core riêng và không bắt buộc OOMKilled chỉ vì CPU vượt quota.
- Không suy ra thời gian job chậm chính xác hai lần: còn phụ thuộc tính chất task, I/O, daemon và tranh chấp tài nguyên.

Với `spark.task.cpus=1` mặc định, Executor 2 cores có tối đa hai slot task khi không có ràng buộc tài nguyên khác. Container limit 4 CPU không tự tăng Executor đó lên bốn slot. Có mười task chờ thì chúng chạy lần lượt qua các slot; số task cả application khác số task đồng thời.

## 4. Case RAM: limit 4 GiB nhưng Worker quảng bá 8 GiB

Giả định đủ cores và pool Spark đang rảnh:

- Master có thể chấp nhận cấp Executor heap `6g` theo inventory Worker `8G`; Master không dùng container limit `4Gi` để tự giảm heap hoặc tự sửa inventory này.
- Kubernetes không tự tăng limit. Khi tổng RAM thực dùng chạm giới hạn và không cấp thêm được, kernel có thể OOM-kill tiến trình trong container.
- Không kết luận OOM xảy ra ngay lúc submit chỉ vì Worker quảng bá 8 GiB hoặc heap được cấu hình 6 GiB; khai báo không đồng nghĩa RAM đã được sử dụng hết.
- Không khẳng định mọi OOM đều làm toàn Worker Pod restart. Executor là tiến trình bên trong container; cần đối chiếu trạng thái, logs và số liệu bộ nhớ thay vì chỉ nhìn restart count.

Hai hướng cân cấu hình:

1. **Giữ container limit, giảm ngân sách Worker/heap Executor và chừa headroom:** ít tốn RAM, hợp lab nhỏ khi vẫn đáp ứng job; có thể phải giảm mức song song hoặc chia nhỏ công việc.
2. **Cấp container ngân sách lớn hơn:** điều chỉnh requests/limits phù hợp khả năng node và workload khác; tốn RAM hơn, vẫn phải tính daemon/ngoài heap, không chỉ tăng heap.

Ưu tiên hướng thứ nhất cho lab nếu đáp ứng bài, rồi đo mức dùng thực. Hạ request đơn thuần không làm application tự dùng ít RAM. Heap bằng toàn bộ container limit không phải cấu hình bảo đảm an toàn.

## 5. Minh chứng và giới hạn

Các phép kiểm tra ở context `orbstack`, namespace `default`:

- Snapshot 09:37 ngày 2026-10-16: Master Ready 1/1, Workers 2/2; ba Pod Running/Ready, 0 restarts. Registry Master/hai Workers ALIVE, mỗi Worker 1 core/512 MiB, coresused/memoryused 0, active applications 0.
- Snapshot chốt 10:25:38 cùng ngày: Master 1/1, Workers 2/2; vẫn ba Pod trên, IP Master `.82`, Workers `.80`/`.81`, 0 restarts. Deployment resources/Worker args/daemon heap và registry tiếp tục khớp bảng cấu hình trên; active applications 0, mỗi Worker used 0.
- Cgroup v2 của một Worker đã được đọc ở lượt trước trong ngày: `memory.max=2147483648` (2 GiB), `cpu.max=100000 100000` (quota tương đương 1 CPU). Không đo lại cgroup ở snapshot chốt hoặc coi đây là số RAM/CPU thực dùng.
- [Buổi 18](18-submit-spark-application.md) đã kiểm chứng hai Executor 1 core/512 MiB thực hiện task và trả kết quả 300. Đây là minh chứng đã lưu của demo nhỏ, không phải lượt submit mới hoặc bằng chứng sizing cho mọi application.

`memoryused` trong registry là ngân sách Spark đã cấp, không phải RSS hoặc RAM cgroup. Không có active application/used 0 không có nghĩa daemon không dùng RAM.

**Chưa thực hành trong buổi này:** hai cấu hình sai 4/8, benchmark throttling, gây OOM, đo peak, Python UDF/RDD, nhiều application tranh chấp, failure hoặc vận hành ngoài OrbStack. Không cần thử phá giới hạn để hoàn thành yêu cầu phân tích của buổi.

## 6. Kiểm tra và debug theo tầng

Các lệnh tham khảo chỉ đọc, không phải yêu cầu triển khai/chạy lại demo:

```bash
kubectl --context orbstack -n default get deployment spark-worker
kubectl --context orbstack -n default get pods -l app=spark-worker
kubectl --context orbstack -n default describe pod <worker-pod>
```

- **Pod Pending/Insufficient resources:** kiểm tra requests, node allocatable và Events; không lấy Worker memory quảng bá để giải thích scheduling Pod.
- **Application không được cấp Executor:** kiểm tra inventory còn trống ở từng Worker, heap/cores mỗi Executor và giới hạn application. Container còn RAM không có nghĩa Spark pool còn đủ.
- **Task chậm/nghi CPU throttling:** đối chiếu CPU limit/cgroup, CPU thực dùng, mức song song và tính chất task; không chỉ nhìn số cores trên UI.
- **Executor mất/nghi RAM:** đối chiếu heap/pool với limit, RAM thực, trạng thái tiến trình và logs đúng application; không mặc định mọi lỗi mất Executor đều do OOM.

Trước đọc logs/exec phải kiểm tra spec/input để tránh lộ Secret hoặc dữ liệu ứng dụng. Không dump env, SparkConf hoặc credential.

## 7. OrbStack làm giúp ↔ hệ thống ngoài lab

OrbStack cung cấp node Linux/runtime của lab. Scheduler, kubelet/runtime/kernel cgroups và Spark Master/Worker vẫn có trách nhiệm riêng như trên; không phụ thuộc wildcard domain Mac hoặc Ingress UI.

Ngoài lab, self-managed hoặc managed cluster đều cần requests/limits phù hợp node allocatable, ngân sách toàn hệ thống và application thực tế. Nhà cung cấp có thể chuẩn bị node/runtime nhưng không tự cân Worker args với container limits. Tăng RAM VM/node cũng không tự sửa `--memory`, tăng CPU node không tự sửa `--cores`.

Kiểm tra desired spec và Pod thực tế, giới hạn cgroup, inventory Spark rồi mức dùng/logs theo symptom. Các kiểm tra lab xác nhận một cấu hình nhỏ trên một node, không bảo đảm hiệu năng, độ ổn định hoặc tài nguyên production.

## 8. Review đã đạt và bước tiếp theo

- **RAM nền tảng — 1.B/2.A/3.C:** Executor 768 MiB không vừa Worker 512 MiB; chỉ tăng container limit không tự tăng Spark pool; vượt memory request chưa bắt buộc OOMKilled.
- **CPU — 1.B/2.A:** tám Spark cores vẫn chia quota 4 CPU; Executor 2 cores với `spark.task.cpus=1` có tối đa hai task đồng thời trong giả định của câu hỏi.
- **RAM quá limit — 1.B/2.C:** Spark có thể cấp theo inventory nhưng RAM thực có nguy cơ OOM; cần cân pool/heap, chừa RAM cho daemon/ngoài heap và kiểm tra mức dùng.

Đạt yêu cầu phân tích hai case của Buổi 19; chốt 19/28. Bắt đầu lý thuyết [Buổi 20 — Spark ghi dữ liệu vào MinIO](../roadmap/buoi-hoc/20-spark-ghi-du-lieu-vao-minio.md): endpoint S3 khác object URI, bucket/key/prefix và đường dữ liệu Driver/Executors. Chưa cấu hình connector/credential hoặc ghi object trong Buổi 19.

## Tài liệu tham khảo

- [Kubernetes v1.35 requests/limits](https://v1-35.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/).
- [Spark Standalone 4.1.3: Worker resources và Executor scheduling](https://spark.apache.org/docs/4.1.3/spark-standalone.html).
- [Spark 4.1.3 configuration: memory, cores và task CPUs](https://spark.apache.org/docs/4.1.3/configuration.html).
