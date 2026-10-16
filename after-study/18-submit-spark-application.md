# Tổng kết buổi 18 — Submit Spark application

**Ngày học:** 2026-10-15–2026-10-16, giờ Việt Nam. **Ngày chốt:** 2026-10-16. **Trạng thái:** Hoàn thành sau thực hành và review. **Tiến độ khi chốt:** 18/28.

[Challenge gốc](../roadmap/buoi-hoc/18-submit-spark-application.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Code demo](../spark-buoi18.py) · [Job submit](../yaml/spark-buoi18-submit.yaml) · [Master/Workers](../yaml/spark-buoi16.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a13d72-5993-764d-976a-fd9e459845ef)

> Học viên không muốn submit qua Jupyter, nên dùng Kubernetes Job riêng để chạy spark-submit. Học viên tự triển khai và chạy application; mentor chuẩn bị scaffold, kiểm tra cấu hình/dry-run và đọc kết quả live. Mentor không submit, apply, thay TTL, restart hoặc xóa workload thay học viên.

## 1. Challenge và kết quả

Submit PySpark application vào Spark Standalone đang chạy trong Kubernetes, xác định Driver/Executors và vai trò Master/Worker; kiểm chứng phép tính chứ không chỉ nhìn trạng thái FINISHED.

Application dùng DataFrame lấy ID từ 1 đến 10, lọc số chẵn, nhân 10 rồi tính tổng. Kỳ vọng độc lập: **20 + 40 + 60 + 80 + 100 = 300**.

Minh chứng được mentor đọc sáng 2026-10-16, context `orbstack`, namespace `default`:

- ConfigMap `spark-buoi18-code` có duy nhất key `spark-buoi18.py`, nội dung khớp file local; Pod mount read-only tại `/opt/spark/app`.
- Pod `spark-submit-buoi18-qdc7q` chạy image `docker.io/library/spark:4.1.3-python3` với đúng args trong manifest. Driver logs có `MASTER=spark://spark-master-svc:7077`, `APP_ID=app-20261016021031-0002` và `DRIVER_HOST=192.168.194.92`.
- Executor 0 được cấp trên Worker `.81`, Executor 1 trên Worker `.80`; mỗi Executor 1 core/512 MiB. Worker daemon logs xác nhận nhận yêu cầu khởi chạy đúng Executor của application này.
- Driver logs ghi task 0 và task 1 của stage 0 hoàn thành trên hai Executor khác nhau; task tổng hợp stage 2 hoàn thành trên Executor 0. Có thực thi phân tán, không chỉ đăng ký application.
- Logs in **`RESULT total=300`**, giữ application 30 giây, rồi `SparkContext is stopping with exitCode 0` và `Successfully stopped SparkContext`.
- Container chạy 09:10:29–09:11:05 (+07), thoát mã `0`, reason `Completed`, 0 restarts; Pod phase `Succeeded`. Job có condition `Complete`, completionTime 09:11:10 (+07).
- Sau application, Master và hai Workers vẫn `ALIVE`; active applications 0, mỗi Worker có coresused/memoryused 0. Master registry giữ application đúng ID ở state `FINISHED`.

Đạt thực hành buổi 18. Các bản ghi `TestDF` hoặc lượt `buoi18-client` cũ không được dùng thay bằng chứng kết quả của lượt này.

## 2. Hai luồng: cấp tài nguyên và thực thi task

```diagram
Cấp tài nguyên:
Driver ──▶ Master ──▶ Worker daemon ──▶ khởi chạy Executor

Thực thi:
Driver ◀────────── task / kết quả ──────────▶ Executor
```

| Thành phần | Vai trò trong bài | Vị trí và vòng đời |
|---|---|---|
| Driver | Điều khiển application, lập lịch task và nhận kết quả. | Trong Pod submit vì client mode; kết thúc cùng lượt chạy application. |
| Master | Quản lý tài nguyên Spark Standalone, cấp tài nguyên cho application. | Master Pod dùng chung; không phải nơi trực tiếp thực hiện DataFrame task. |
| Worker daemon | Quảng bá tài nguyên, khởi chạy và quản lý Executor processes. | Worker Pod dùng chung; không dừng chỉ vì một application kết thúc. |
| Executor | Thực hiện task, lưu dữ liệu trung gian/cache khi cần. | Tiến trình bên trong Worker Pod; thuộc application, không phải Pod riêng trong mô hình này. |

Master/Worker daemon không làm proxy cho từng task hoặc kết quả. Kubernetes Job controller theo dõi tiến trình submit kết thúc, không thay Spark Driver lập lịch task.

Đây là **Spark Standalone bên trong Kubernetes**, không phải Spark Native Kubernetes. Trong bài này, Driver không yêu cầu Kubernetes API tạo Executor Pods; vì vậy Pod submit tắt `automountServiceAccountToken`.

## 3. Vì sao vẫn là client deploy mode?

Manifest gọi công cụ `spark-submit` với:

```text
--master spark://spark-master-svc:7077
--deploy-mode client
```

- `spark-submit` là công cụ khởi chạy/submit application; tên công cụ không tự quyết định cluster deploy mode.
- `--master spark://...` chọn cluster manager Spark Standalone.
- `--deploy-mode client` giữ Driver ở môi trường chạy spark-submit, ở đây là Pod của Job, không phải laptop.
- Client mode vẫn thực thi phân tán: Driver trong Pod submit, Executors trên hai Workers.

Deploy mode thuộc từng lượt submit, không phải chế độ chung của cả hệ thống. Với Spark 4.1.3, CLI submit trực tiếp file Python vào Standalone không hỗ trợ cluster deploy mode; không đánh đồng giới hạn này với Spark Native Kubernetes hoặc mọi cách dùng REST/wrapper đã thảo luận trước đó. Buổi này không thực hành các đường thay thế đó.

## 4. Cấu hình quan trọng và quan hệ tham chiếu

| Field/khối | Giá trị, ý nghĩa và giới hạn |
|---|---|
| `kind: Job` | Quản lý một lượt chạy application tới khi kết thúc; khác Deployment duy trì daemon. Một Kubernetes Job không đồng nghĩa một Spark job phát sinh từ action. |
| `spec.backoffLimit: 0` | Không tự retry bằng Pod mới khi lượt chạy thất bại trong cấu hình bài này. |
| `spec.template.spec.restartPolicy: Never` | Không restart container đã kết thúc trong cùng Pod. Đây không phải chính sách xóa Pod. |
| `spec.ttlSecondsAfterFinished: 300` | Cấu hình hiện tại cho Job đủ điều kiện tự dọn 300 giây sau Complete hoặc Failed; ở cấp Job spec, không trong Pod template. Ban đầu scaffold không TTL để giữ logs review. |
| Image và args | Image cung cấp Spark/Python; giữ ENTRYPOINT của image và gọi `/opt/spark/bin/spark-submit` foreground để kết quả tiến trình gắn với vòng đời container. |
| `volumes[].configMap.name` | Trỏ `spark-buoi18-code`, nơi chứa code demo nhỏ, không nhạy cảm. Không cần PVC cho code này. |
| `volumeMounts[].name`/`mountPath` | Nối với volume `application`; directory `/opt/spark/app` cộng key `spark-buoi18.py` tạo đường dẫn args cuối `/opt/spark/app/spark-buoi18.py`. |
| `POD_IP`/Downward API | Lấy `status.podIP` của chính Pod submit; không hard-code IP thay đổi theo Pod. |
| `spark.driver.host` | Script dùng POD_IP làm địa chỉ quảng bá để Executor gọi về Driver. |
| `spark.driver.bindAddress` | `0.0.0.0` để listener nhận kết nối qua các interface của Pod; wildcard bind không phải địa chỉ đích để quảng bá. |
| `--driver-memory 512m` | Heap JVM Driver, không phải tổng RAM của Python/JVM/native trong container. |
| `--executor-memory 512m` | Heap mỗi Executor; override mặc định 1g để vừa ngân sách 512 MiB mà từng Worker quảng bá. Spark không tự giảm heap chỉ vì Worker nhỏ. |
| `--executor-cores 1` | Mỗi Executor được cấp 1 Spark core. |
| `--total-executor-cores 2` | Giới hạn tổng cores cho Executors của application, không bao gồm CPU Driver. Không có nghĩa application chỉ có đúng hai task suốt vòng đời. |
| Driver container resources | Requests 250m CPU/512Mi RAM, limits 1 CPU/1Gi RAM; phải chừa RAM cho phần ngoài heap. Không lấy việc demo nhỏ chạy được làm bảo đảm sizing cho job lớn. |

ConfigMap mount không phải bind-mount thư mục Mac. Sửa file repo không tự cập nhật nội dung ConfigMap đang lưu trong cluster. Script chỉ dùng `range`, filter/select và aggregate bằng biểu thức JVM, không dùng Python RDD/UDF; `.first()` lấy kết quả aggregate và kích hoạt thực thi.

## 5. Kết thúc tiến trình khác xóa object

- `0/1 Completed` là bình thường với Pod batch đã chạy xong: không còn container Ready, nhưng không tự có nghĩa là thất bại. Phải đối chiếu exit code và Job status.
- Không đặt TTL thì Job không được TTL-after-finished controller tự xóa; giữ object giúp kiểm tra trạng thái và logs còn khả dụng.
- TTL tính từ khi Job đạt Complete hoặc Failed, không từ lúc sửa field và không từ AGE của Pod. Hết TTL là đủ điều kiện dọn, không cam kết xóa đúng từng giây.
- Khi dọn Job theo cơ chế này, các Pod thuộc Job được dọn theo; Master/Worker Deployments và ConfigMap code độc lập không thuộc vòng đời đó.
- Worker logs của lượt này có Executor state `KILLED`, exitStatus 143 sau yêu cầu kill lúc Driver stop. Trong chuỗi đã kiểm chứng này, đó là shutdown của Executor sau kết quả đúng/Driver exit 0, không phải bằng chứng Job thất bại. Không suy ra mọi dòng KILLED đều vô hại.

Kiểm tra lại khoảng 09:24 (+07): Job và Pod submit nêu trên không còn trong API, ConfigMap vẫn tồn tại và hai Workers còn ALIVE. Trạng thái này phù hợp TTL 300 giây đã đọc trước đó, nhưng không có audit/event để kết luận chính xác ai xóa hoặc thời điểm xóa. Mentor không thực hiện thao tác dọn. Không giả định còn đọc được logs bằng tên Pod đã bị xóa; chưa thiết lập log tập trung hoặc Spark History Server.

## 6. Lệnh tham khảo và thứ tự debug

Luồng được giao để **học viên tự thực hiện**, không phải yêu cầu chạy lại application sau buổi:

```bash
set -o pipefail
kubectl --context orbstack -n default create configmap spark-buoi18-code \
  --from-file=spark-buoi18.py --dry-run=client -o yaml |
  kubectl --context orbstack -n default apply -f - &&
kubectl --context orbstack -n default apply \
  --dry-run=server --validate=strict -f yaml/spark-buoi18-submit.yaml &&
kubectl --context orbstack -n default apply -f yaml/spark-buoi18-submit.yaml &&
kubectl --context orbstack -n default logs -f job/spark-submit-buoi18 \
  --pod-running-timeout=120s
```

ConfigMap pipeline thực sự lưu code, server dry-run Job chỉ kiểm tra schema/admission, apply Job mới có thể tạo lượt chạy. Re-apply cùng Job đã Complete không tự tạo application mới. Exit code của lệnh xem logs không thay được exit code container/Job status.

Debug theo lớp: Pod Events/image/resources → ConfigMap/key/mount/args → DNS Service/EndpointSlice/Master RPC → Driver advertised/bind address và kết nối ngược từ Executor → Driver/Worker logs đúng app ID → task/kết quả → container exit code/Job conditions. Trước đọc logs/exec, đối chiếu spec và input; không dump env, SparkConf, Secret hoặc service-account token.

## 7. Review và nhầm lẫn đã xử lý

- Networking: học viên chọn đúng scenario Executor không đăng ký được Driver thì chưa thể nhận task. Ban đầu nhầm quảng bá `0.0.0.0`; đã được giải thích wildcard bind khác địa chỉ đích, sau đó chọn đúng scenario bind loopback không nhận được kết nối từ Pod khác.
- Job retry: học viên chọn B, Driver thoát 1 với Never/backoffLimit 0 thì không tự restart container hoặc retry bằng Pod mới trong bài này.
- Mount: học viên chọn A, nếu mountPath giả định là `/demo` và key giữ nguyên thì args phải dùng `/demo/spark-buoi18.py`. Không đổi mount thật `/opt/spark/app` theo scenario.
- Đã giải đáp vì sao Executor dùng 512 MiB thay vì default 1g, vì sao chạy trong Pod vẫn là client mode, và vì sao Completed chưa đồng nghĩa bị xóa. Đây là phần được giảng, không ghi thành học viên tự suy luận toàn bộ cấu hình.
- Review cuối ngày 2026-10-16: học viên trả lời **1.A**, Driver gửi task trực tiếp tới Executor; **2.B**, Worker daemon thuộc cluster dùng chung còn Executor thuộc application. Cả hai đúng. Kết hợp minh chứng runtime và các checkpoint trước, chốt buổi 18 hoàn thành.

## 8. OrbStack làm giúp ↔ hệ thống ngoài lab

- Job, ConfigMap mount, Downward API và TTL là cơ chế Kubernetes chuẩn, không phải chức năng Jupyter hoặc domain OrbStack. Job controller theo dõi hoàn thành; TTL-after-finished controller thực hiện dọn khi được cấu hình. Ngoài lab phải xác nhận các controller hoạt động; sau TTL vẫn còn object thì kiểm tra conditions, field TTL, finalizers và controller, không chỉ xóa tay để che symptom.
- `spark-master-svc` là Service DNS nội bộ: CoreDNS/cluster resolver cùng kubelet clusterDNS/clusterDomain/dnsPolicy và Service/EndpointSlice phải đúng. CNI/routing/firewall/policy phải cho submit gọi Master 7077 và Executor gọi về Driver RPC/block manager. Domain `*.k8s.orb.local` không tạo đường callback này; Ingress Master UI không thay Spark RPC.
- Image `4.1.3-python3` dùng IfNotPresent: node có cache có thể dùng lại, node khác cần pull được image đúng kiến trúc từ registry với quyền phù hợp. Không giả định image trên Mac có ở mọi node. ConfigMap được kubelet mount, không dựa vào thư mục chia sẻ Mac hoặc storage provisioner.
- Ngoài lab cần chọn requests/limits và ngân sách Worker/Executor theo tài nguyên node, mức dùng thực và phần ngoài heap; managed cluster có thể chuẩn bị runtime/DNS/CNI, nhưng không tự sửa một cấu hình Spark quảng bá quá khả năng container. Muốn tự dọn nhanh mà vẫn review lâu dài cần lưu logs/kết quả ở nơi độc lập với Pod.

**Giới hạn:** chỉ kiểm chứng demo SQL/DataFrame nhỏ trên OrbStack; chưa thử Python UDF/RDD, Spark Native Kubernetes, REST Python wrapper, HA, node failure, mạng ngoài lab, load sizing hoặc ghi dữ liệu MinIO. Không coi job chạy đúng là đã kiểm chứng các khả năng đó.

## Bước tiếp theo và tài liệu

[Buổi 19 — Hai tầng resource management](../roadmap/buoi-hoc/19-hai-tang-resource-management.md): bắt đầu bằng lý thuyết/cấu hình thật, phân biệt requests/limits của container với tài nguyên Worker quảng bá và nhu cầu mỗi Executor. Chưa thay hoặc thử phá giới hạn tài nguyên để tạo OOM/throttling.

- [Spark 4.1.3 cluster overview](https://spark.apache.org/docs/4.1.3/cluster-overview.html).
- [Spark 4.1.3 submitting applications](https://spark.apache.org/docs/4.1.3/submitting-applications.html).
- [Spark 4.1.3 configuration: memory, cores và networking](https://spark.apache.org/docs/4.1.3/configuration.html).
- [Spark 4.1.3 Standalone resource allocation và Executor scheduling](https://spark.apache.org/docs/4.1.3/spark-standalone.html).
- [Kubernetes Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [TTL-after-finished](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/) và [ConfigMap volume](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/).
