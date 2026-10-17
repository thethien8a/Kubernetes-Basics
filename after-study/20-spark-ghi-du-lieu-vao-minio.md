# Tổng kết buổi 20 — Spark đọc CSV, ghi Parquet vào SILO

**Ngày học:** 2026-10-16–2026-10-17, giờ Việt Nam. **Ngày chốt:** 2026-10-17. **Trạng thái:** Hoàn thành. **Tiến độ khi chốt:** 20/28.

[Challenge gốc](../roadmap/buoi-hoc/20-spark-ghi-du-lieu-vao-minio.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Script](../spark-buoi20.py) · [Job submit](../yaml/spark-buoi20-submit.yaml) · [Master/Workers](../yaml/spark-buoi16.yaml) · [Fixture CSV](../orders.csv) · [Policy mẫu](../yaml/spark-buoi20-policy.json) · [Hội thoại học](https://ampcode.com/threads/T-01a142c4-666d-73ce-8e13-c50259e6e827)

> Chốt bằng cả checkpoint concept đã trả lời đúng và runtime: Job Complete/exit 0, task trên hai Workers, đọc lại Parquet đúng toàn bộ hai dòng và tổng 46.60. Không chỉ dựa vào Console có object, `_SUCCESS`, Master FINISHED hoặc tổng đúng. Mentor kiểm tra chỉ đọc, không submit/chạy lại/dọn workload; ngoại lệ đã được học viên yêu cầu cụ thể là cập nhật riêng access-key trong Secret, không thay mật khẩu.

## 1. Kiến trúc và đường dữ liệu

Đây vẫn là **Spark Standalone trong Kubernetes**, không phải Spark Native Kubernetes. Driver nằm trong Pod của Job vì `--deploy-mode client`; Executors là tiến trình do Worker daemon khởi chạy bên trong Worker containers, không phải Executor Pods riêng.

```diagram
┌──────────────────┐     xin tài nguyên     ┌──────────────┐
│ Job Pod / Driver │───────────────────────→│ Spark Master │
└────────┬─────────┘                        └──────┬───────┘
         │ task/result                            │ yêu cầu
         │                                        │ khởi chạy
         ▼                                        ▼
┌─────────────────────────────────────────────────────────┐
│ Worker Pods: Executor 0 và Executor 1                    │
└──────────────────────────┬──────────────────────────────┘
                           │ S3A I/O
                           ▼
                  ┌─────────────────┐
                  │ SILO API :9000  │
                  └─────────────────┘
```

Driver cũng có thể list/đọc metadata và thực hiện I/O cần cho kế hoạch/commit; vì vậy **cả Driver và Executors** cần connector, đường mạng và credential phù hợp. Master điều phối tài nguyên, không phải proxy chuyển nội dung CSV/Parquet. Driver gọi được storage chưa chứng minh Executor gọi được.

Các khối Job giữ từ Buổi 18:

- `POD_IP` lấy từ `status.podIP` bằng Downward API; script quảng bá `spark.driver.host=POD_IP`, bind `0.0.0.0`. Địa chỉ bind không phải địa chỉ để Executors gọi; loopback không nhận kết nối từ Worker Pod khác.
- ConfigMap `spark-buoi20-code` trong `default`, key `spark-buoi20.py`, mount read-only tại `/opt/spark/app`, tạo đúng đường dẫn script `/opt/spark/app/spark-buoi20.py`. Đổi key hoặc mountPath mà không đổi đường dẫn args có thể làm thiếu script.
- Driver/Executor heap `512m`, mỗi Executor 1 core, tổng Executor cores tối đa 2; Driver container request `250m`/`512Mi`, limit 1 CPU/`1Gi`. Đây là hai tầng ngân sách khác nhau như [Buổi 19](19-hai-tang-resource-management.md), không lấy container limit làm heap hoặc cộng CPU Driver vào pool Executors.

## 2. Endpoint khác object URI

| Thành phần | Giá trị dùng trong lab | Vai trò |
|---|---|---|
| S3 API endpoint | `http://minio:9000` | Địa chỉ HTTP để S3A/SDK gửi request trong namespace `default`. |
| Console | Service port `9001`, Ingress host `silo.pro.thien` | Giao diện quản trị/object browser, không phải endpoint S3A. |
| Input URI | `s3a://de-lab/buoi20/input/orders.csv` | Bucket `de-lab`, object key `buoi20/input/orders.csv`. |
| Output URI đã kiểm chứng | `s3a://de-lab/buoi20/output/orders/run-001/` | Prefix của Parquet dataset, không phải tên một file duy nhất. |

- `s3a://` chọn Hadoop S3A filesystem; bucket/key không nằm trong filesystem riêng của Driver hoặc Worker.
- Prefix là phần đầu của object key, không phải thư mục POSIX trên node. Parquet dataset có thể gồm nhiều part objects và marker; không suy số part files bằng số Workers.
- File chỉ nằm ở `/tmp` trong Driver Pod không tự xuất hiện tại Worker Pods. Chọn input S3 để các tiến trình cần đọc có nguồn chung; mount filesystem chung là một phương án khác nhưng phải cấu hình cho mọi nơi cần dùng.

### Các property kết nối trong `spark-submit`

| Property | Giá trị | Lý do và giới hạn |
|---|---|---|
| `spark.hadoop.fs.s3a.endpoint` | `http://minio:9000` | Gọi API nội bộ, không dùng Console hoặc wildcard domain Mac. |
| `spark.hadoop.fs.s3a.path.style.access` | `true` | Bucket nằm trong URL path; không cần DNS kiểu `de-lab.minio`. |
| `spark.hadoop.fs.s3a.connection.ssl.enabled` | `false` | HTTP trong lab, không phải bỏ kiểm tra chứng chỉ HTTPS. |
| `spark.hadoop.fs.s3a.endpoint.region` | `us-east-1` | Signing region của client; không tự chuyển dữ liệu sang AWS. |
| `spark.hadoop.fs.s3a.aws.credentials.provider` | `software.amazon.awssdk.auth.credentials.EnvironmentVariableCredentialsProvider` | Đọc AWS env của tiến trình thực hiện I/O. |

Prefix `spark.hadoop.` chuyển property sang Hadoop configuration; không phải field của Service, không tạo DNS/bucket hoặc bật TLS ở server.

Ví dụ path-style: bucket `warehouse`, key `raw/events.csv` cho URL dạng `http://minio:9000/warehouse/raw/events.csv`. Virtual-hosted-style có dạng `http://warehouse.minio:9000/raw/events.csv`, cần DNS/routing và hỗ trợ storage phù hợp.

**Region:** lượt chạy cuối chứng minh request với signing region `us-east-1` dùng được với cấu hình storage hiện tại. Không chứng minh persisted server region được đặt chính xác thành giá trị đó; chưa đọc cấu hình nhạy cảm trên PVC. Không dùng việc thiếu region env để kết luận server không có override.

**TLS ngoài lab:** server/frontend phải thực sự phục vụ HTTPS, chứng chỉ đúng hostname, các JVM Driver/Executor phải tin CA. Mac/browser tin CA riêng chưa đủ; đổi client sang HTTPS không tự bật TLS server. Đây là giải thích tham khảo, chưa triển khai TLS trong buổi này.

## 3. Connector JVM và dependency

Image cấu hình: `docker.io/library/spark:4.1.3-python3`. Inventory JAR đã kiểm tra có Hadoop client **3.4.2**, nhưng image ban đầu không có S3A/AWS SDK classes cần thiết.

```text
--packages org.apache.hadoop:hadoop-aws:3.4.2
--conf spark.jars.ivy=/tmp/ivy
```

- Ghép `hadoop-aws` theo **Hadoop client**, không theo số phiên bản Spark hoặc tự lấy AWS SDK mới nhất. Spark resolve dependency bắc cầu và đưa JAR vào classpath Driver/Executors.
- PySpark DataFrame đọc/ghi qua JVM/Hadoop S3A. `pip install boto3` không bổ sung connector cho `spark.read`/`write`.
- `--packages` và `--conf` đặt trước đường dẫn script trong args của `spark-submit`.
- Ivy là cơ chế resolve/cache dependency. User image UID 185 có passwd home `/nonexistent`, còn `/tmp` ghi được, nên chọn `/tmp/ivy` thay vì phụ thuộc `~/.ivy2`. Cache này chứa JAR, không phải output S3 hay nơi lưu credential; Pod mới không được bảo đảm kế thừa cache Pod cũ.

Hai lựa chọn đã so sánh: `--packages` đơn giản và phù hợp lab nhưng cần repository/mirror truy cập được khi cache thiếu; đóng JAR đã ghép phiên bản vào image dễ tái lập/offline hơn nhưng cần build/phân phối image đúng. Không build image mới trong buổi này. Logs lượt cuối có dependency `org.apache.hadoop#hadoop-aws;3.4.2` và application thực sự I/O thành công.

## 4. Identity, policy và Secret

### Identity của storage khác identity Kubernetes

- Với native user SILO đã đối chiếu source Console, username dùng làm access-key ID, password làm secret key. Không cần thêm child service account chỉ để có cặp credential.
- Tên dự kiến ban đầu là `spark-buoi20`; học viên xác nhận tên đúng cần dùng là **`spark-buoi-20`**. Mentor cập nhật riêng field access-key trong Secret theo yêu cầu cụ thể, giữ nguyên secret-key.
- Kubernetes Secret cung cấp dữ liệu cho container, không tạo user hoặc tự cấp quyền bucket. Kubernetes ServiceAccount/RBAC cũng không tự trở thành quyền S3.
- `automountServiceAccountToken: false` chỉ tắt tự mount token API Kubernetes; không chặn kubelet cấp Secret env cho Pod.

Không mở `credentials.json` hoặc dùng lại key cũ học viên yêu cầu bỏ qua; không đọc/giải mã/in mật khẩu. Ignore file khỏi Git không tự giới hạn policy hay thu hồi credential, và không chứng minh lịch sử Git không chứa nó.

### Injection cho Driver và Workers

Secret: `default/spark-s3-credentials`, type `Opaque`, đúng hai key không rỗng.

| Biến env container | `secretKeyRef.key` | Nơi khai báo |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | `access-key` | Driver Job và Worker Deployment. |
| `AWS_SECRET_ACCESS_KEY` | `secret-key` | Driver Job và Worker Deployment. |

Hai ref cùng dùng Secret `spark-s3-credentials` trong namespace của Pod. `env.name` là tên SDK đọc, `secretKeyRef.name` chọn Secret, `.key` chọn dữ liệu nguồn; không đặt credential literal vào args/SparkConf/YAML.

- Driver env không tự được Spark sao chép tùy ý sang Executors. Executor con trong Standalone kế thừa Worker env; Worker cần ref riêng. Không cần cấp AWS env cho Master chỉ để điều phối application này.
- Sửa Secret không tự cập nhật env của tiến trình/Pod cũ. Sau cập nhật, học viên đã rollout Worker: generation=observed=5, hai Pod mới Ready; kiểm tra boolean trên cả hai xác nhận access-key khớp yêu cầu và secret-key hiện diện, không in giá trị.
- **Giới hạn:** mọi application chung Workers có thể kế thừa/đọc credential Worker. Đây là lựa chọn lab một người, không phải isolation theo application cho multi-tenant.

### Policy mẫu và phạm vi quyền

[Policy JSON](../yaml/spark-buoi20-policy.json) là policy storage, không phải manifest để `kubectl apply`:

| Resource | Các Allow action |
|---|---|
| `arn:aws:s3:::de-lab` | `GetBucketLocation`, `ListBucket`, `ListBucketMultipartUploads`. |
| `arn:aws:s3:::de-lab/*` | `GetObject`, `PutObject`, `DeleteObject`, `AbortMultipartUpload`, `ListMultipartUploadParts`. |

`Version: 2012-10-17` là phiên bản ngôn ngữ policy; mỗi Statement kết hợp Effect/Action/Resource. Bucket-level action khác object-level action; ListBucket không thay GetObject để đọc bytes. ARN là cú pháp policy, không đổi endpoint sang AWS.

Policy này **bucket-wide, bao gồm cả input**, không phải chỉ output prefix hay least privilege tuyệt đối. Quyền DeleteObject/multipart phục vụ đường ghi/cleanup nhưng vẫn có khả năng xóa input. Allow hẹp thêm vào user có Allow rộng khác không tự thu hẹp quyền; user mới được hướng dẫn chỉ gắn `spark-buoi20-rw`, không group/policy rộng khác. Key con của root không hạn chế riêng có thể kế thừa quyền rộng; key mới không tự đồng nghĩa quyền hẹp.

Học viên báo đã tạo policy/user và upload fixture. Lượt cuối chứng minh credential hiện tại đủ cho các thao tác thực sự dùng trong pipeline; **chưa audit toàn bộ quyền hiệu lực, test từ chối bucket khác hoặc xác thực độc lập cấu hình IAM trên Console**.

## 5. Hợp đồng CSV → Parquet

Fixture `orders.csv` 77 bytes:

```csv
order_id,quantity,unit_price
101,2,12.50
205,0,99.00
309,3,7.20
412,-1,40.00
```

Schema: `order_id INT, quantity INT, unit_price DECIMAL(10,2)`.

- `DECIMAL(10,2)` có tổng 10 chữ số, 2 chữ số thập phân; dùng giá trị thập phân cho tiền thay binary floating point.
- `header=true` xử lý dòng header; `enforceSchema=false` giữ schema và kiểm header theo vị trí/case sensitivity, không tự reorder cột theo tên.
- `mode=FAILFAST` báo lỗi khi parser gặp record corrupt; không thay business validation. Ít/nhiều token không mặc định đều là corrupt, null cần quy tắc riêng khi dữ liệu thực yêu cầu; column pruning có thể ảnh hưởng field được parse.

Transform dùng Spark SQL expressions, không Python UDF:

```python
result = orders.filter(F.col("quantity") > 0).withColumn(
    "amount", F.col("quantity") * F.col("unit_price")
)
```

Kết quả đã đọc lại từ Parquet:

| order_id | quantity | unit_price | amount |
|---|---:|---:|---:|
| 101 | 2 | 12.50 | 25.00 |
| 309 | 3 | 7.20 | 21.60 |

Đúng **hai dòng**, tổng **46.60**. Kỳ vọng đã được tính độc lập bằng Python `csv`/`Decimal`; lọc nhầm `>= 0` cho **ba dòng nhưng cùng tổng 46.60**, nên tổng đơn lẻ không đủ.

Transformation xây kế hoạch; `write.parquet` là action kích hoạt tính, nên lỗi parse input có thể chỉ lộ tại write, không tự kết luận là lỗi quyền ghi. Lazy evaluation không có nghĩa mọi API read đều chưa I/O: metadata/listing có thể xảy ra sớm.

Script ghi xong mới `spark.read.parquet(output_uri)`, sort/collect fixture nhỏ, so đủ bốn field của cả hai dòng và tổng; sai thì raise, đúng mới in kết quả. `collect()` gom toàn bộ kết quả về Driver, không dùng làm chiến lược validation mặc định cho dataset lớn; tăng Worker RAM không tự bảo vệ Driver khỏi OOM.

## 6. Commit output và chạy lại

Job chọn `spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version=1`. Source/default Spark đã đối chiếu dùng SQLHadoopMapReduceCommitProtocol và ParquetOutputCommitter/FileOutputCommitter; inventory image không có hai Spark cloud-committer classes để mặc định suy ra đã auto dùng cloud committer. Hadoop 3.4.2 mặc định algorithm 2; **algorithm 1 là lựa chọn explicit của lab**, không phải default. Logs runtime cuối xác nhận algorithm **1**.

- V1 giữ task output dưới `_temporary`, job commit merge/rename ra đích rồi cleanup/marker theo default.
- Rename S3A được mô phỏng bằng copy rồi delete, không nguyên tử cả prefix. Driver chết giữa commit có thể để lại dataset thiếu part; không bảo đảm rollback về rỗng.
- Consistent listing không biến nhiều object thành một transaction. Classic v1 chỉ dùng cho fixture nhỏ, một writer, prefix mới, không reader đọc khi đang commit; các điều kiện này vẫn không làm nó production-safe.
- S3A-specific committers có thể tránh rename nhưng cần integration/phụ thuộc và kiểm chứng tương thích storage. Buổi này chưa triển khai/test magic/staging committer trên SILO.
- `errorifexists` từ chối đích đã tồn tại, không phải distributed lock. Hai writer cần prefix riêng hoặc điều phối phù hợp; không suy Kubernetes tự serialize ghi S3.

### Chạy lại Job khác với retry một action

Job terminal Failed với `backoffLimit: 0`/`restartPolicy: Never` không chạy lại chỉ vì apply cùng manifest. Hai cách: tạo Job tên mới để giữ lịch sử, hoặc xóa Job đã dừng rồi tạo lại cùng tên. Xóa Job/Pod không đồng nghĩa xóa ConfigMap, Secret hoặc objects S3.

Trước lần chạy tiếp phải xem lỗi và tình trạng đích, chọn prefix chưa dùng thay vì mặc định overwrite/xóa output cũ. Đổi script local cần cập nhật ConfigMap; ConfigMap không tự đồng bộ từ file Mac.

Các lệnh tham khảo đã giải thích, **không phải yêu cầu chạy lại sau khi buổi đã đạt**:

```bash
kubectl --context orbstack -n default create configmap spark-buoi20-code \
  --from-file=spark-buoi20.py --dry-run=client -o yaml \
  | kubectl --context orbstack -n default apply -f -

kubectl --context orbstack -n default delete job spark-submit-buoi20 --wait=true
kubectl --context orbstack -n default create -f yaml/spark-buoi20-submit.yaml
kubectl --context orbstack -n default wait \
  --for=condition=complete job/spark-submit-buoi20 --timeout=600s
```

Timeout của `wait` chỉ dừng chờ, không tự dừng Job. Job không đặt TTL để còn evidence cho review; không tự dọn resource khi chưa được yêu cầu.

**Lượt đã chứng minh thực tế dùng `run-001/`**, không phải `run-002/` đã gợi ý cho rerun. Không có đủ evidence lịch sử để kết luận prefix cũ đã được xử lý thế nào; không sửa lại lịch sử hoặc khẳng định mọi lần trước chưa ghi gì.

## 7. Minh chứng runtime khi chốt

Mentor kiểm tra chỉ đọc ở `orbstack/default` lúc **16:28 ngày 2026-10-17 (+07)**:

| Kiểm tra | Kết quả |
|---|---|
| Job mới | `spark-submit-buoi20`, UID `3cfefed5-40e0-4271-af08-d674f039278b`, Complete=True. |
| Thời gian Job | Tạo/start 16:13:53; completion 16:14:43, giờ Việt Nam. |
| Pod Driver | `spark-submit-buoi20-lf79q`, IP `192.168.194.99`, Succeeded, exit 0/Completed, 0 restarts; container kết thúc 16:14:39. |
| Spark application | `app-20261017091425-0005`, tên `buoi20-csv-to-parquet`; Master ghi FINISHED. |
| Executors thực hiện task | Executor 0 trên Worker `.97`; Executor 1 trên Worker `.96`, có task-completion events ở cả hai. |
| ConfigMap/code | `spark-buoi20-code` có key `spark-buoi20.py`, code bytes khớp file local; có readback/assertions trước RESULT. |
| Job config | Client mode, hadoop-aws 3.4.2, các S3A/Ivy/algorithm flags, hai Secret refs và code mount khớp dự kiến. |
| Sau application | Hai Workers ALIVE/Ready/0 restarts, Spark used cores/memory=0, active apps rỗng; MinIO/Master/Workers Ready 1/1, 1/1, 2/2. |

Logs được lọc allowlist trong bộ nhớ, không lưu/dump raw logs hoặc credential. Các dòng dữ liệu giả đã đối chiếu:

```text
SAVED_ROW order_id=101 quantity=2 unit_price=12.50 amount=25.00
SAVED_ROW order_id=309 quantity=3 unit_price=7.20 amount=21.60
OUTPUT=s3a://de-lab/buoi20/output/orders/run-001/
RESULT rows=2 total=46.60
```

Chuỗi bằng chứng là code đã triển khai có readback/assertions → application chạy trên Workers → kết quả Parquet đã lưu khớp kỳ vọng → container exit 0/Job Complete. Không submit thêm application hoặc dùng credential riêng để list/read storage thay học viên trong lượt review.

**Lỗi cũ:** từng có Job Failed/BackoffLimitExceeded; Pod cũ không còn khi kiểm tra rerun. Học viên đã yêu cầu sửa tên access-key rồi rollout/chạy lại, nhưng mentor chưa có Driver logs của lượt lỗi cũ để xác nhận access-key là nguyên nhân duy nhất. Không suy Master FINISHED một mình là thành công của toàn pipeline; registry cũng còn entries của các application trước.

## 8. Debug theo tầng

| Symptom | Kiểm tra trước |
|---|---|
| `ClassNotFoundException: S3AFileSystem` | Connector JAR/classpath, phiên bản Hadoop, phân phối dependency Driver/Executors; không đổi credential để chữa thiếu class. |
| Không resolve dependency | DNS/egress/TLS/proxy/repository hoặc mirror, cache Ivy và quyền ghi; storage chạy local không bảo đảm tải dependency được. |
| Không resolve endpoint/kết nối API | Hostname thật client gọi → Service/EndpointSlice/port 9000 → mạng Pod/server; phân biệt Console 9001. |
| TLS/certificate error | Server có phục vụ HTTPS không, hostname/SAN và CA trust trong JVM của cả hai phía Spark. |
| Lỗi xác thực/quyền S3 | Mã lỗi cụ thể, identity, Secret refs/env đã refresh, signing region, policy/resource; Pod Ready không chứng minh quyền ghi. |
| Output đã tồn tại hoặc Job terminal | Tình trạng prefix/lỗi trước, giữ evidence, dùng run-specific prefix và Job mới; không mặc định overwrite hoặc xóa data. |
| Có object nhưng dữ liệu sai | Đọc lại Parquet, kiểm IDs/count/từng field/tổng; không chỉ nhìn marker hoặc số file. |

Chỉ dùng metadata/ref/presence/match boolean khi kiểm Secret/env; không dump Secret YAML/data, toàn bộ env/SparkConf hoặc logs có thể lộ bí mật. Hint Ladder dành cho debug sau quan sát, không thay phần giảng trước lab.

## 9. OrbStack làm giúp ↔ hệ thống ngoài lab

- **Đường application:** `minio`/`spark-master-svc` là DNS Service trong namespace `default`, do DNS cluster như CoreDNS phục vụ; Service chọn backend qua selector/EndpointSlice, mạng Pod do CNI/hạ tầng thực thi. Không phụ thuộc Mac phân giải `*.k8s.orb.local`.
- **Ngoài lab:** self-managed cần DNS cluster/mạng Pod hoạt động; managed service có thể chuẩn bị các thành phần nền nhưng người vận hành vẫn cấu hình Service, namespace/FQDN, NetworkPolicy/firewall và storage endpoint phù hợp. Cả Driver lẫn Workers cần route tới API storage. Với cách dùng `--packages` này, tiến trình submit cần tới repository/mirror khi cache thiếu, còn Spark phân phối JAR cho Executors; không mặc định mỗi Worker phải tự resolve từ Maven. Không bắt dựng platform mới để học phần này.
- **UI từ máy lab:** Master UI qua Ingress `spark.k8s.orb.local`; domain/networking local OrbStack giúp host truy cập. Ngoài lab cần đường vào controller/LB, DNS A/AAAA hoặc CNAME và firewall/routing phù hợp. UI mở được từ Mac không chứng minh máy khác truy cập được hoặc Executor có quyền S3.
- **Credential:** Secret/env là Kubernetes chuẩn, không phải OrbStack tự cấp quyền storage. Hệ thống nhiều người cần trust boundary/identity và cách cấp credential phù hợp; không dùng chung Worker env như isolation theo application.
- **TLS/images/dependencies:** chuẩn bị HTTPS/CA trust, registry/pull policy/quyền và kiến trúc image, repository/mirror hoặc image dựng sẵn; không mặc định image/JAR trên Mac có ở mọi node.
- **Dữ liệu:** storage object vẫn phụ thuộc disk/PVC/backend của SILO. Thành công lab một node không chứng minh HA, backup, node failure recovery hoặc atomic publication.

Các đối chiếu ngoài lab là giải thích/cấu hình tham khảo, không phải triển khai hoặc kiểm thử production đã thực hiện.

## 10. Review đã đạt và kết luận

| Checkpoint | Câu trả lời đã đạt | Mental model đã kiểm tra |
|---|---|---|
| URI/đường I/O | 1.A/2.B | URI khác endpoint; Driver gọi được chưa đủ cho Executors. |
| Connector | 1.B/2.A/3.C | Classpath/JAR, ghép phiên bản Hadoop, resolve repository trước S3 I/O. |
| Endpoint/path-style/TLS | 1.B/2.B/3.C | Bucket trong URL path, client không tự bật TLS, JVM phải tin CA. |
| Region/credential | 1.B/2.A/3.C | Signing không tự đổi endpoint, env ở Driver/Workers, policy quyết định quyền. |
| YAML/hợp đồng dữ liệu | 1.B/2.C/3.A | Tắt token không chặn Secret env, filesystem Driver không tự chia sẻ, tổng đúng chưa đủ. |
| Code | 1.C/2.A/3.B | Header theo vị trí, lazy/action, collect về Driver. |
| Policy | 1.B/2.C/3.A | Resource cho object, DeleteObject bao input, key mới không tự có quyền hẹp. |
| Commit | 1.C/2.A/3.B | Copy/delete không atomic, commit dở có output thiếu, errorifexists không phải lock. |

Không hỏi lại chỉ để đủ số câu: concept đã review đạt trước thực hành, nay có runtime/readback đáp ứng challenge. **Buổi 20 hoàn thành, tổng 20/28.** Chờ học viên bắt đầu [Buổi 21 — Debugging Challenge #2](../roadmap/buoi-hoc/21-debugging-2.md), chưa tự mở bài mới hoặc dọn workload/data.

Chưa thực hành: production/TLS/HA, isolation đa tenant, audit/negative permission tests, fault injection giữa commit, concurrent writers, S3A-specific committers, dataset lớn hoặc benchmark. Các file học tập vẫn local/chưa commit/push tại lúc chốt; application/output đã được học viên triển khai trong lab và mentor kiểm chứng.

## Tài liệu tham khảo

- [Spark 4.1.3 — CSV options](https://spark.apache.org/docs/4.1.3/sql-data-sources-csv.html).
- [Spark 4.1.3 — Parquet writer](https://spark.apache.org/docs/4.1.3/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.parquet.html).
- [Spark 4.1.3 — collect](https://spark.apache.org/docs/4.1.3/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.collect.html).
- [Spark 4.1.3 — configuration, Ivy và custom Hadoop properties](https://spark.apache.org/docs/4.1.3/configuration.html).
- [Spark 4.1.3 — dependency management](https://spark.apache.org/docs/4.1.3/submitting-applications.html#advanced-dependency-management).
- [Hadoop AWS 3.4.2 — connector](https://hadoop.apache.org/docs/r3.4.2/hadoop-aws/tools/hadoop-aws/index.html#Getting_Started).
- [Hadoop S3A 3.4.2 — connection/TLS](https://hadoop.apache.org/docs/r3.4.2/hadoop-aws/tools/hadoop-aws/connecting.html).
- [Hadoop S3A 3.4.2 — third-party stores/region](https://hadoop.apache.org/docs/r3.4.2/hadoop-aws/tools/hadoop-aws/third_party_stores.html).
- [Hadoop S3A 3.4.2 — committers và giới hạn rename](https://hadoop.apache.org/docs/r3.4.2/hadoop-aws/tools/hadoop-aws/committers.html).
- [Kubernetes — Secret env injection](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/).
- [Kubernetes — Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/).
- [Console source đã đối chiếu: username/password → accessKey/secretKey](https://github.com/pgsty/silo-console/blob/1360e26d976d/web-app/src/screens/Console/Users/thunk/AddUsersThunk.tsx#L40-L54).
