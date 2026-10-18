# Buổi 21 — Debugging Challenge #2

[Challenge](../roadmap/buoi-hoc/21-debugging-2.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Job ca A](../yaml/spark-buoi21-a.yaml) · [Job ca B](../yaml/spark-buoi21-b.yaml) · [Script ca B](../spark-buoi21-b.py) · [Hội thoại học](https://ampcode.com/threads/T-01a14937-b751-764f-8bc2-960a53717ca2)

**Hoàn thành ngày 2026-10-18; học từ 2026-10-17 đến 2026-10-18, giờ Việt Nam (+07). Tổng 21/28 buổi.**

Học viên tự triển khai, tìm và sửa hai lỗi độc lập trong Job submit. Mentor chuẩn bị scaffold, kiểm tra chỉ đọc và lưu tài liệu; không sửa/apply/restart workload, thay Secret hoặc dọn dữ liệu thay học viên. Không cần cố gây hết mọi lỗi được liệt kê trong challenge để chốt buổi.

## 1. Phương pháp điều tra đã thực hành

1. Xác định thất bại ở tầng Kubernetes, kết nối Spark hay I/O storage.
2. Gắn evidence với đúng Job UID, Pod owner UID, thời gian và Spark application ID nếu application đã khởi tạo.
3. Đọc lỗi cụ thể phía trước câu tổng kết, đối chiếu manifest với cấu hình thực tế.
4. Chọn phép kiểm tra phân biệt các giả thuyết, không đổi đồng thời endpoint, credential và RAM.
5. Sửa tối thiểu, tạo Job mới, giữ evidence cũ và nghiệm thu lại kết quả ứng dụng.

`Failed`, `BackoffLimitExceeded` và exit code 1 cho biết trạng thái thất bại, không chỉ ra riêng lỗi Spark/S3. Application name cũng không nhận diện duy nhất một lượt chạy: ca A tái sử dụng script có tên application của Buổi 18 nhưng có Job/application ID mới.

## 2. Ca A — Driver gọi nhầm cổng UI của Master

**Symptom:** Driver báo `All masters are unresponsive! Giving up.`; exception sớm hơn là `IllegalArgumentException: Too large frame`.

Đường kết nối trong Job lỗi dùng `spark://spark-master-svc:8080`. Service tồn tại nhưng `8080` phục vụ HTTP UI; Spark Standalone đăng ký application qua RPC `7077`. Tên host đúng hoặc cổng có listener chưa bảo đảm đúng giao thức.

```diagram
Trước: Driver ──→ Master UI  :8080 ──→ lỗi giao thức
Sau:   Driver ━━▶ Master RPC :7077 ──→ Executors ──→ tổng 300
```

Học viên sửa `--master` trong Job sang `spark://spark-master-svc:7077`, giữ code/resources và tạo Job mới. Không đổi Service, mở Ingress cho RPC hoặc tăng RAM để chữa lỗi frame.

| Evidence | Kết quả |
|---|---|
| Lượt lỗi | Job `spark-submit-buoi21-a-hptbm`, Pod `spark-submit-buoi21-a-hptbm-6qjpt`; exit 1, Job Failed/BackoffLimitExceeded, không DeadlineExceeded. |
| Lượt phục hồi | Job `spark-submit-buoi21-a-ws2t2`, UID `7d169ba4-e24a-4027-ad25-d05060b48944`. |
| Pod phục hồi | `spark-submit-buoi21-a-ws2t2-m65vs`, IP `192.168.194.101`, Succeeded/exit 0, 0 restarts. |
| Application | `app-20261017141738-0006`, có `RESULT total=300` và task hoàn thành trên cả hai Workers `.96`/`.97`. |
| Thời gian | Job Complete lúc 21:18:17 ngày 2026-10-17 (+07). |

Lỗi đã được đối chiếu trước khi sửa. Khi kiểm tra recovery, Job lỗi A không còn trong query; không suy ra ai xóa hoặc nguyên nhân resource biến mất. Master FINISHED một mình không thay bằng chứng kết quả/tác vụ của đúng application.

## 3. Ca B — Thiếu connector S3A trên JVM

Học viên xác định đúng lỗi từ:

```text
ClassNotFoundException: Class org.apache.hadoop.fs.s3a.S3AFileSystem not found
```

`s3a://` chọn Hadoop S3A filesystem. PySpark DataFrame đọc/ghi qua JVM; `S3AFileSystem` không phải module Python. `pip install boto3` không sửa classpath của `spark.read`/`write`.

Mentor đối chiếu đúng lượt lỗi: Job không có `--packages`/`--jars`; ConfigMap khớp code local; image cùng digest đã inventory có Hadoop client **3.4.2** nhưng thiếu S3A classes. Application đã khởi tạo qua Master RPC 7077 rồi mới lỗi filesystem. Chưa có bằng chứng credential/policy sai hoặc Maven tải thất bại khi dependency còn chưa được khai báo.

```diagram
Trước: Driver ──→ thiếu class S3A ──→ dừng trước pipeline S3
Sau:   Driver ━━▶ nạp connector  ──→ CSV → Parquet → đọc lại
```

Học viên bổ sung vào `.spec.template.spec.containers[name=submit].args`, trước đường dẫn script:

```yaml
- --packages
- org.apache.hadoop:hadoop-aws:3.4.2
```

- Ghép phiên bản theo **Hadoop client 3.4.2**, không lấy số phiên bản Spark 4.1.3 làm phiên bản `hadoop-aws`.
- Spark resolve dependency bắc cầu và phân phối JAR cho Driver/Executors. Cấu hình Ivy `/tmp/ivy` đã có từ Buổi 20; Pod mới không được bảo đảm kế thừa cache Pod cũ.
- `--packages` ít thay đổi, hợp lab nhưng cần truy cập repository/mirror khi cache thiếu. Đóng JAR đúng phiên bản vào image giúp tái lập/offline hơn nhưng cần build/phân phối image; không làm trong buổi này.
- Không cần sửa Python/tạo lại ConfigMap vì code không đổi; cũng không đổi Secret/IAM hoặc Workers để chữa thiếu class.

### Minh chứng trước/sau

Mentor kiểm tra chỉ đọc ở `orbstack/default` lúc **00:17–00:22 ngày 2026-10-18 (+07)**:

| Kiểm tra | Lượt lỗi | Lượt phục hồi |
|---|---|---|
| Job | `spark-submit-buoi21-b-pgn85` | `spark-submit-buoi21-b-zcsff` |
| Job UID | `0343d80e-ffaf-4d39-bbc4-cbbaa62dcef2` | `75f90d94-5d85-400b-866c-c5165f3857b9` |
| Pod | `spark-submit-buoi21-b-pgn85-qlvlh` | `spark-submit-buoi21-b-zcsff-2tj2c` |
| Pod IP | `192.168.194.102` | `192.168.194.103` |
| Application | `app-20261017164909-0007` | `app-20261017171359-0008` |
| Dependency | Không khai báo `--packages`/`--jars` | `hadoop-aws:3.4.2`; logs có dependency resolve đúng phiên bản. |
| Container / Job | Exit 1/Error; Failed/BackoffLimitExceeded | Exit 0/Completed, 0 restarts; Complete=True. |
| Thời gian container | 23:49:06–23:49:11 ngày 2026-10-17 | 00:13:36–00:14:12 ngày 2026-10-18 |
| Thời gian Job terminal | Failed 23:49:16 ngày 2026-10-17 | Complete 00:14:16 ngày 2026-10-18 |
| Output evidence | Không RESULT/SAVED_ROW; target không chứng minh đã ghi | Đọc lại Parquet khớp đủ hai dòng và tổng 46.60. |

Pod owner UID khớp Job, code ConfigMap `spark-buoi21-b-code` khớp source có readback/assertions, Driver cùng image digest giữa hai lượt. Trước đọc logs đã kiểm env chỉ gồm Downward API và Secret refs; không đọc/giải mã/in credential, dump toàn bộ env hoặc lưu raw logs.

## 4. Nghiệm thu dữ liệu và execution

Input vẫn là `s3a://de-lab/buoi20/input/orders.csv`. Output riêng của lượt thành công:

```text
s3a://de-lab/buoi21/output/orders/app-20261017171359-0008/
```

Script dùng `errorifexists`, ghi xong đọc lại chính prefix đó và so toàn bộ row trước khi in kết quả. Các marker thực tế:

```text
SAVED_ROW order_id=101 quantity=2 unit_price=12.50 amount=25.00
SAVED_ROW order_id=309 quantity=3 unit_price=7.20 amount=21.60
RESULT rows=2 total=46.60
```

Kỳ vọng còn được mentor tính độc lập từ fixture local bằng `csv`/`Decimal`. Chỉ kiểm tổng là chưa đủ: lọc nhầm `quantity >= 0` cho ba dòng nhưng vẫn tổng 46.60. `OUTPUT_TARGET` chỉ in đích dự kiến; bằng chứng ghi đúng đến từ source đã triển khai có readback/assertions, các SAVED_ROW/RESULT và exit 0 của đúng lượt.

Logs cấp Executor 0 trên `.97` và Executor 1 trên `.96`; **năm task-completion của lượt B đều ở Executor 0/Worker `.97`**, mỗi task set quan sát được có một task. Không nhầm việc được cấp Executor với thực sự chạy task hoặc tuyên bố lượt B dùng task trên cả hai Workers. Ca A đã có bằng chứng task trên cả hai; không sửa pipeline/chạy lại chỉ để ép phân phối đều.

Master ghi đúng application B mới FINISHED. Sau application, hai Workers ALIVE, mỗi Worker quảng bá 1 core/512 MiB, used cores/memory bằng 0 và active applications bằng 0. Master, hai Worker Pods và MinIO Ready/0 restarts ở snapshot review. Đây là trạng thái tại thời điểm kiểm tra, không phải đo peak RAM hoặc chứng minh không thể OOM.

## 5. Cấu hình vòng đời và an toàn rerun

- `metadata.generateName` tạo tên Job mới ở mỗi `create`; không dùng `apply` để mong Job terminal tự chạy lại. Tên mới giữ evidence của lượt trước.
- `backoffLimit: 0` giới hạn retry cấp Job; `restartPolicy: Never` không restart container trong Pod. Hai field không tắt mọi retry nội bộ Spark hoặc giải thích lỗi gốc.
- `activeDeadlineSeconds` là 180 ở A, 600 ở B; ngân sách tính từ Job start, không chỉ thời gian Spark tính toán. Nếu bị DeadlineExceeded, phải xem điều gì xảy ra trước hạn, không coi deadline là nguyên nhân ứng dụng duy nhất.
- Không TTL để giữ Job/Pod cho review. Xóa Job/Pod không đồng nghĩa xóa objects S3; không tự dọn workload/data khi chưa được yêu cầu.
- ConfigMap cung cấp code được mount, không tự sửa `spark-submit` args hoặc đồng bộ khi file Mac thay đổi.
- Prefix ca B theo application ID tách khỏi output Buổi 20 và các lần B khác; không dùng overwrite/xóa dữ liệu để che lỗi rerun.

Hai tầng resource Kubernetes và Spark đã review ở [Buổi 19](19-hai-tang-resource-management.md). Buổi 21 không thay requests/limits/heap hoặc cố tạo OOM; không gọi exit 137 một mình là bằng chứng OOM.

## 6. OrbStack làm giúp ↔ cấu hình ngoài lab

- Đường `spark-master-svc:7077` và `minio:9000` là Service DNS trong namespace `default`, không phải domain UI trên Mac. DNS cluster như CoreDNS phân giải tên, Service/EndpointSlice chọn backend và mạng Pod/CNI cung cấp đường kết nối.
- Ngoài lab cần đối chiếu namespace hoặc FQDN, Service `port`/`targetPort`, EndpointSlice Ready, listener/giao thức, routing và policy/firewall từ đúng tiến trình gọi. Self-managed phải chuẩn bị thành phần nền; managed Kubernetes có thể cung cấp một phần, không tự cấu hình endpoint ứng dụng đúng.
- Mentor dùng UI JSON qua `spark.k8s.orb.local` để đối chiếu registry. OrbStack giúp đường DNS/network local tới UI; ngoài lab cần controller đúng IngressClass, backend rule, LB/NodePort hoặc đường vào tương ứng, DNS tới địa chỉ đó và firewall/routing phù hợp. DNS có sẵn không tự cấp load balancer; mở UI từ Mac không chứng minh Driver RPC hay S3 I/O.
- Với `--packages`, tiến trình submit cần tới repository/mirror khi thiếu cache; Spark phân phối JAR cho Executors, không mặc định mỗi Worker tự resolve Maven. Image/JAR trên Mac không tự xuất hiện ở mọi node; phương án image dựng sẵn cần registry/pull access/kiến trúc CPU phù hợp.

Các đối chiếu ngoài lab là cấu hình/mental model tham khảo, chưa triển khai hoặc kiểm thử cloud/on-prem trong buổi này.

## 7. Review đã đạt và giới hạn

| Phần | Minh chứng đã có |
|---|---|
| Phân biệt trạng thái Job với nguyên nhân ứng dụng | Checkpoint 1.B; hai failure/recovery thực tế. |
| Khoanh vùng DNS trước quyền storage khi UnknownHostException | Checkpoint 2.A; tình huống lý thuyết, không inject lỗi DNS thật. |
| Không lấy RESULT của app cũ cho Job mới | Checkpoint 3.C; đối chiếu UID/Pod/application ở các lượt. |
| Ca A | Học viên xác định đường Driver–Master và tự sửa RPC; runtime tổng 300 đạt. |
| Ca B | Học viên dẫn đúng ClassNotFoundException, xác định thiếu JAR và tự bổ sung; runtime/readback đạt. |

Connector/endpoint/Secret/commit đã review concept ở [Buổi 20](20-spark-ghi-du-lieu-vao-minio.md), resource ở Buổi 19; không hỏi lại để đủ số câu. Cộng với phần dựng Spark, phân vai, UI và submit đã đạt ở các buổi trước, đủ tiêu chí tuần 3. **Chốt Buổi 21, tổng 21/28; chờ bắt đầu Buổi 22 — Airflow.**

Chưa thực hành ở Buổi 21: cố tình làm Worker mất registration, phá DNS/UI/credential, gây OOM, audit/negative permission tests, đo peak/benchmark, atomic publication/HA hoặc fault injection giữa commit. Classic committer v1 và credential chung Worker vẫn mang giới hạn đã ghi ở Buổi 20; readback thành công không chứng minh production-safe, least privilege đầy đủ hoặc isolation đa tenant.

Tài liệu/scaffold và bản sửa của học viên còn local/chưa commit/push tại lúc chốt. Application/output do học viên chạy trong lab đã được mentor kiểm chứng; không dọn hoặc submit lại thay học viên.

## Tham khảo

- [Spark 4.1.3 — Standalone](https://spark.apache.org/docs/4.1.3/spark-standalone.html).
- [Spark 4.1.3 — dependency management](https://spark.apache.org/docs/4.1.3/submitting-applications.html#advanced-dependency-management).
- [Hadoop AWS 3.4.2 — S3A connector](https://hadoop.apache.org/docs/r3.4.2/hadoop-aws/tools/hadoop-aws/index.html#Getting_Started).
- [Kubernetes — Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/).
