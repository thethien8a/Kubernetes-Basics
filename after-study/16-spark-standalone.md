# Tổng kết buổi 16 — Spark Standalone trên Kubernetes

**Ngày bắt đầu/chốt:** 2026-10-14–2026-10-15, giờ Việt Nam. **Trạng thái:** Hoàn thành sau thực hành và review. **Tiến độ:** 16/28.

[Challenge gốc](../roadmap/buoi-hoc/16-spark-standalone.md) · [Tiến độ](../roadmap/tien-do-hoc-tap.md) · [Manifest](../spark-buoi16.yaml) · [Hội thoại học](https://ampcode.com/threads/T-01a13d72-5993-764d-976a-fd9e459845ef)

> Học viên tự chỉnh manifest, triển khai và thử thay Pod Master. Mentor chỉ đọc manifest/API/logs, kiểm tra DNS và trạng thái đăng ký; không sửa/apply/restart workload thay học viên. Chưa submit Spark application, thực hành REST/Python, cấu hình recovery/HA hoặc kiểm chứng browser trên Mac trong buổi này.

## 1. Challenge và kết quả

Dựng một Spark Master và hai Spark Workers trong Kubernetes. Học viên phân biệt được Spark Worker với Kubernetes Node, Driver với Executor, địa chỉ Worker với đích Master, ngân sách Spark với giới hạn container và readiness với đăng ký Spark.

Kiểm tra chốt lúc **14:07:13 ngày 2026-10-15 (+07)**, context `orbstack`, namespace `default`:

- Deployment `spark-master` có 1/1 Ready; `spark-worker` có 2/2 Ready; ba container đều 0 restarts.
- Master trả trạng thái `ALIVE`, có đúng hai Worker `ALIVE`, tổng 2 cores và 1024 MiB được quảng bá; tài nguyên Spark đang dùng bằng 0, không có application active/completed.
- Từ Worker, `getent hosts spark-master-svc` trả ClusterIP `192.168.194.202` và tên `spark-master-svc.default.svc.cluster.local`.
- EndpointSlice Service có duy nhất Pod Master hiện tại `192.168.194.82`, Ready/serving, cổng RPC 7077 và HTTP UI 8080.
- Logs của hai Worker hiện tại chứa cả lần đăng ký ban đầu và lần đăng ký lại sau khi Master đổi Pod, không cần restart hai Worker đó.

Đạt challenge của buổi 16. Việc mở Master UI từ browser Mac thuộc buổi 17; JSON qua API proxy ở đây chỉ là phép đọc trạng thái để review.

## 2. Vai trò và hai lớp quản lý

| Thành phần | Trách nhiệm |
|---|---|
| Kubernetes Node | Máy chạy Pod; scheduler/kubelet/runtime quản lý tài nguyên và vòng đời workload Kubernetes. |
| Master Pod | Chứa Spark Master, cluster manager của Spark Standalone; ghi nhận Workers và phối hợp cấp tài nguyên cho application. Không phải Kubernetes control plane. |
| Worker Pod | Chứa Spark Worker daemon, đăng ký CPU/RAM với Master và khởi chạy tiến trình Executor/Driver khi Spark yêu cầu phù hợp deploy mode. Không phải một Kubernetes Node mới. |
| Driver | Điều phối một application, lập lịch task và nhận kết quả; không đồng nhất với Spark Master. |
| Executor | Tiến trình thực thi task của application; trong mô hình Standalone này chạy trong Worker Pod, không mặc định là Executor Pod riêng. |

```diagram
┌────────────────────────── Kubernetes ──────────────────────────┐
│                                                               │
│ ┌──────────────┐  DNS/RPC   ┌──────────────────┐   ┌─────────┐ │
│ │ Worker Pod 1 │───────────▶│ spark-master-svc │──▶│ Master  │ │
│ └──────────────┘   :7077   │ ClusterIP        │   │ Pod     │ │
│ ┌──────────────┐           │ selector         │   └─────────┘ │
│ │ Worker Pod 2 │───────────▶│ app=spark-master │               │
│ └──────────────┘           └──────────────────┘               │
└───────────────────────────────────────────────────────────────┘
```

Tăng `Deployment/spark-worker.spec.replicas` làm tăng số Worker Pod, không tự thêm Kubernetes Node. Spark Native Kubernetes là mô hình khác: Kubernetes làm cluster manager trực tiếp cho Driver/Executor Pods; chưa thực hành ở đây.

## 3. Cấu hình và các liên kết quan trọng

Manifest hiện tại dùng image `docker.io/library/spark:4.1.3-python3`; ba container báo image digest `sha256:8abe31671cf03d5bcf0c3746c31c62e76b65e450a005eafb2c017db76e56b294`. Digest là snapshot runtime, manifest vẫn dùng tag, không tuyên bố đã pin digest trong YAML.

| Khối/field | Ý nghĩa và hành vi khi đổi/sai |
|---|---|
| Deployment `replicas`/selector/template labels | Master 1, Workers 2; selector khớp nhãn Pod template. Deployment quản lý ReplicaSet, ReplicaSet duy trì số Pod. |
| Master `strategy.type: Recreate` | Trong rollout thông thường, dừng Pod cũ trước khi tạo Pod mới; có downtime, không tự cung cấp HA hoặc khôi phục trạng thái Spark. |
| Container `args` | Chạy `/opt/spark/bin/spark-class` với class Master/Worker. Đây là khởi chạy daemon, không phải submit application. |
| `POD_IP` từ `fieldRef: status.podIP` | Downward API đưa IP của chính Pod vào env; Kubernetes thay `$(POD_IP)` trong args. Không cần hard-code IP Pod vào manifest. |
| `--host $(POD_IP)` | Địa chỉ của chính Master hoặc Worker để RPC lắng nghe/quảng bá trong cấu hình này. Worker không dùng IP Master hay ClusterIP Service làm địa chỉ của bản thân. |
| Master `--port 7077`/`--webui-port 8080` | Tách RPC Spark khỏi HTTP UI. Container port declarations không tự khởi chạy listener hoặc public cổng ra Mac. |
| Worker Master URL | `spark://spark-master-svc:7077` là đích để tìm Master, khác Worker `--host`; short name dùng trong cùng namespace. |
| Worker `--port 7078`/`--webui-port 8081` | Cổng RPC và HTTP UI của Worker, không phải cổng Master. |
| Service selector | `app=spark-master` khớp label của Pod Master; tên Service là `spark-master-svc`, không bắt buộc giống tên Deployment. DNS tồn tại không chứng minh có backend đúng. |
| Service ports | `rpc`: `port: 7077`, `targetPort: rpc`; `web-ui`: `port: 8080`, `targetPort: web-ui`. TargetPort có tên tham chiếu container port cùng tên, không phải tùy ý một tên DNS. |
| Container `readinessProbe` | TCP vào port có tên `rpc`, period 5s/failure threshold 12. Probe thuộc container, ngang cấp `resources`, không thuộc PodSpec hay nằm bên trong resources. |

TCP readiness chỉ kiểm tra listener RPC đáp ứng phép nối TCP của kubelet. Worker có thể Ready nhưng chưa đăng ký Master; cần logs và registry của Master. Readiness failure không tự restart container như liveness failure.

### Ngân sách daemon, Spark và Kubernetes

| Cấu hình | Master | Mỗi Worker |
|---|---|---|
| Kubernetes requests | 100m CPU, 512Mi RAM | 250m CPU, 768Mi RAM |
| Kubernetes limits | 500m CPU, 1Gi RAM | 1 CPU, 2Gi RAM |
| `SPARK_DAEMON_MEMORY` | `256m` | `256m` |
| Spark tài nguyên quảng bá | Không phải Executor pool | `--cores 1 --memory 512M` |

Requests phục vụ scheduling; limits giới hạn sử dụng container. `SPARK_DAEMON_MEMORY` là ngân sách max heap JVM daemon trong cách launch này, không phải toàn bộ RAM tiến trình. Worker `--memory` là ngân sách quảng bá cho Spark, không làm Kubernetes tăng container memory limit; ứng dụng còn có chi phí native/off-heap/Python và tiến trình daemon. Không coi 0 restarts khi idle là kiểm chứng sizing cho job thực tế.

Tổng requests của ba Pod là 600m CPU/2Gi RAM. Trước triển khai, node arm64 có đủ allocatable cho requests này và registry có image arm64; đây không phải benchmark hoặc bảo đảm không OOM.

## 4. SparkSubmit và deploy mode: phần lý thuyết đã làm rõ

`spark-submit` là công cụ chuẩn bị cấu hình/dependencies và khởi chạy hoặc gửi application tới cluster manager. Nó khác `spark-class` dùng ở manifest để chạy Master/Worker daemon.

- **Client mode:** Driver chạy ở nơi submit application. Với PySpark, có các tiến trình JVM/Python liên quan, không nên hiểu tất cả nằm trong một process duy nhất. Nếu submit từ Pod riêng thì Driver ở Pod đó, không ở laptop chỉ vì gọi là client.
- **Standalone cluster mode:** Master chọn Worker phù hợp để khởi chạy Driver; không phải Kubernetes ngẫu nhiên đặt Driver vào một Worker Pod.
- **Giới hạn CLI PySpark:** Spark 4.1.3 vẫn chặn submit trực tiếp file `.py` bằng `spark-submit --master spark://… --deploy-mode cluster`.
- **Đường REST được tài liệu mô tả:** Master REST khởi chạy JVM class `org.apache.spark.deploy.SparkSubmit` trên Worker; SparkSubmit bên trong dùng client mode mặc định để chạy Python tại đó. Có hai lớp launch, nên không mâu thuẫn với giới hạn CLI trên. REST caller ban đầu không phải nơi chạy inner Driver. Chưa chạy thử đường này; response nhận submission không chứng minh job hoàn thành.

Master REST submission mặc định dùng cổng 6066, khác UI 8080 và RPC 7077; Service trong bài chỉ có 7077/8080. Không expose REST hoặc submit job trong buổi 16.

## 5. Worker reconnect khi Master đổi Pod

### Vấn đề và cơ chế

Học viên báo Master được tạo lại thì Workers không kết nối lại được, restart Workers giúp phục hồi. Logs của Workers trước khi sửa không còn để đối chiếu; vì vậy cơ chế retry từ mã nguồn là lời giải thích phù hợp cấu hình, không phải kết luận đã tái hiện đầy đủ nguyên nhân của sự cố gốc.

Worker lưu cả địa chỉ dùng để kết nối Master và RPC reference mà Master trả lại. Trong cấu hình một Master/không recovery này:

1. Khi mất kết nối, lần thử ngay lập tức đã tìm lại Master qua địa chỉ cấu hình.
2. Nếu lần đó thất bại, nhánh retry theo lịch mặc định có thể chọn RPC address đã nhớ, tức IP Pod Master cũ.
3. `spark.worker.preferConfiguredMasterAddress=true` đổi lựa chọn của nhánh retry sang địa chỉ kết nối được lưu, ở đây là Service `spark-master-svc:7077`.

Trong `env` của container Worker:

```yaml
- name: SPARK_WORKER_OPTS
  value: "-Dspark.worker.preferConfiguredMasterAddress=true"
```

`SPARK_WORKER_OPTS` đưa JVM system property `-D…` vào cách launch Worker bằng `spark-class`. Key mặc định false theo source Spark 4.1.3. Khi thay env trong Pod template, cần tạo Worker container mới để nhận option; phép thử dưới đây kiểm chứng lần Master replacement sau khi Workers đã nhận option, không tuyên bố việc thêm option không tạo Worker Pod mới lần đầu.

```diagram
Retry mặc định sau lần kết nối tức thời thất bại
┌────────┐      ┌────────────────────┐
│ Worker │─────▶│ Master Pod IP cũ   │  .77, đã mất
└────────┘      └────────────────────┘

Retry với preferConfiguredMasterAddress=true
┌────────┐      ┌────────────────────┐      ┌──────────────────┐
│ Worker │━━━━━▶│ Service IP .202    │─────▶│ Master Pod mới   │
└────────┘      │ spark-master-svc   │      │ IP .82           │
                └────────────────────┘      └──────────────────┘
```

Service không chuyển TCP connection cũ sang Pod mới; nó cung cấp endpoint cho kết nối mới. DNS không sửa địa chỉ RPC mà application đã giữ trong bộ nhớ. Option không biến ClusterIP thành địa chỉ bind của Master/Worker.

### Minh chứng thử lại sau sửa

Logs còn trong chính hai Worker containers hiện tại:

| Mốc giờ Việt Nam ngày 2026-10-15 | Quan sát |
|---|---|
| 13:01:11/13:01:13 | Workers `.80`/`.81` đăng ký thành công qua `spark-master-svc:7077`, trước thay Master. |
| 13:01:30 | Cả hai ghi `Disassociated` với Service và Master RPC cũ `.77:7077`; lần kết nối Service tức thời bị `Connection refused`. |
| 13:01:44/13:01:45 | Retry theo lịch attempt #1 nhắm `spark-master-svc:7077` và đăng ký thành công. |
| 14:07:13, kiểm tra chốt | Master mới `.82` nhận đúng hai Worker IDs `.80`/`.81`; hai Worker Pod giữ UID và có 0 restarts. |

| Pod hiện tại | UID | IP |
|---|---|---|
| `spark-master-6b4d849595-dbdkh` | `96e3a941-27e0-4fcd-8f16-8a8dc02fb895` | `192.168.194.82` |
| `spark-worker-58fc864978-ffx9w` | `b62e63ec-c8e4-453e-88a4-78fa565f8518` | `192.168.194.80` |
| `spark-worker-58fc864978-hp68z` | `829a1b05-a365-4526-9e8e-89c3bfc75e51` | `192.168.194.81` |

Worker IDs tương ứng là `worker-20261015060111-192.168.194.80-7078` và `worker-20261015060113-192.168.194.81-7078`. Service giữ UID `7d958cec-85e3-4afe-a041-d703a0eef5e3`, ClusterIP `192.168.194.202`; endpoint hiện trỏ Master mới.

Chỉ kiểm chứng reconnect ở một lần Master replacement với hai Workers idle. Retry có giới hạn; option không bảo đảm phục hồi khi Master down vô hạn, không giữ trạng thái Master hay bảo đảm application đang chạy tiếp tục. FILESYSTEM recovery cần recovery directory trên nguồn persistent; ZooKeeper/standby Masters giải quyết bài toán khác. Hai hướng chỉ được đối chiếu bằng lý thuyết, chưa triển khai HA/recovery.

## 6. Lỗi và review đã xử lý

- **Probe sai cấp:** server dry-run/strict từ chối `spec.template.spec.readinessProbe`; lỗi trước đó còn có probe trong resources. Học viên đưa probe đúng cấp container. Service/Worker có dòng `created (server dry run)` không nghĩa đã được tạo thật; dry-run không phải transaction nghiệm thu cả manifest hoặc minh chứng runtime.
- **Địa chỉ Worker:** ban đầu chưa hiểu `--host`; sau giải thích đã chọn IP của chính Worker (`10.42.0.21` trong ví dụ), không chọn Master.
- **Kubernetes Node/Worker:** học viên trả lời tăng Worker replicas chỉ tăng Worker Pods.
- **Driver/Executor:** học viên trả lời Driver phân task, Executor tính toán; Driver client-mode ở Pod submit. Chưa chạy application để kiểm chứng vị trí bằng runtime.
- **Service discovery:** học viên nêu DNS vẫn phân giải khi Service chưa chọn đúng backend; mentor chuẩn hóa thành kiểm tra selector/EndpointSlice, không chỉ DNS.
- **Tài nguyên:** học viên nêu Kubernetes không tự tăng RAM, quảng bá quá cao có nguy cơ vượt ngân sách cộng overhead; mentor bổ sung thuật ngữ OOMKilled.
- **Readiness:** học viên xác định Ready chỉ chứng minh probe thành công, không chứng minh đăng ký Spark.
- **Reconnect:** sau giải thích và phép thử, học viên trả lời đúng option đổi đích retry của Worker, không phải giữ IP Pod cũ hay chuyển kết nối cũ.

## 7. Commands tham khảo và thứ tự debug

Các lệnh triển khai đã được giao để **học viên tự chạy**, không phải mentor thực thi trong lượt chốt:

```bash
kubectl --context orbstack -n default apply \
  --dry-run=server --validate=strict -f spark-buoi16.yaml
kubectl --context orbstack -n default apply -f spark-buoi16.yaml
kubectl --context orbstack -n default rollout status deployment/spark-master
kubectl --context orbstack -n default rollout status deployment/spark-worker
```

Các phép kiểm tra chỉ đọc dùng trong review:

```bash
kubectl --context orbstack -n default get deployments spark-master spark-worker
kubectl --context orbstack -n default get pods \
  -l 'app in (spark-master,spark-worker)' -o wide
kubectl --context orbstack -n default get endpointslices \
  -l kubernetes.io/service-name=spark-master-svc -o yaml
kubectl --context orbstack -n default logs -l app=spark-worker \
  --all-containers=true --prefix --timestamps --tail=1200
kubectl --context orbstack -n default exec \
  spark-worker-58fc864978-ffx9w -- getent hosts spark-master-svc
kubectl --context orbstack get --raw \
  /api/v1/namespaces/default/services/http:spark-master-svc:web-ui/proxy/json/
```

Tên Pod chỉ đúng ở snapshot đã lưu; khi review sau này phải đọc inventory mới. Trước logs/exec cần kiểm tra input ứng dụng, tránh lộ credential hoặc dữ liệu job. API proxy cần quyền truy cập phù hợp và không chứng minh browser có đường vào UI.

Debug theo symptom: manifest/schema → Events/image/process → địa chỉ bind/args → DNS Service → selector/EndpointSlice/ports → routing/firewall/network policy → logs đăng ký và địa chỉ retry → registry Master. Kết nối tới Master UI không thay thế kiểm tra RPC, và RPC hoạt động không chứng minh truy cập được UI từ ngoài cluster.

## 8. OrbStack làm giúp ↔ hệ thống ngoài lab

**Trong lab:** môi trường đã chuẩn bị node/runtime, cluster DNS và mạng Pod/Service; image arm64 đã pull/chạy. Kubernetes Service DNS/ClusterIP/EndpointSlice, Downward API, requests/limits và readiness là cơ chế Kubernetes, không phải wildcard domain trên Mac. Buổi này Workers tìm Master bằng DNS trong cluster, không dựa vào `*.k8s.orb.local`.

**Ngoài lab:** cần triển khai hoặc xác nhận CNI/routing Pod–Pod/Node–Pod, Service dataplane, CoreDNS hoặc DNS cluster tương đương, kubelet `clusterDNS`/`clusterDomain` và Pod `dnsPolicy`. Managed Kubernetes có thể chuẩn bị một phần; vẫn phải kiểm tra domain, backend Ready và đường TCP RPC hai chiều cần thiết. Selector/labels, port/targetPort, host/advertise và namespace phải phù hợp; DNS trả lời được không chứng minh listener hay routing đúng. Debug resolver trong Worker → Service/EndpointSlice → cổng/process → mạng/policy, rồi địa chỉ trong logs Spark.

Mỗi node cần pull image đúng kiến trúc từ registry truy cập được; private registry cần imagePullSecrets/quyền/network thích hợp. Image sẵn trên Mac không tự có trên mọi node. Requests/limits phải tính cả daemon/Executor/Python/native overhead; snapshot idle không thay benchmark. Single Master và Recreate có downtime, không tự cấu hình recovery/HA. Spark RPC không nên public ra mạng không tin cậy chỉ để mở UI.

Chưa kiểm chứng cluster ngoài OrbStack, multi-node, node loss, application/task execution, S3/MinIO client, HA hoặc recovery state. Bước tiếp theo: [Buổi 17 — Spark networking và UI](../roadmap/buoi-hoc/17-spark-networking-va-ui.md), lý thuyết/config trước thực hành browser; chưa tính hoàn thành buổi 17.

## Tài liệu tham khảo

- [Spark 4.1.3 Standalone: ports, daemon env, REST và recovery](https://spark.apache.org/docs/4.1.3/spark-standalone.html).
- [Spark 4.1.3 submitting applications](https://spark.apache.org/docs/4.1.3/submitting-applications.html#launching-applications-with-spark-submit).
- [Source SparkSubmit: giới hạn CLI Python/Standalone cluster](https://github.com/apache/spark/blob/v4.1.3/core/src/main/scala/org/apache/spark/deploy/SparkSubmit.scala#L269-L301).
- [Source Worker: lựa chọn địa chỉ retry](https://github.com/apache/spark/blob/v4.1.3/core/src/main/scala/org/apache/spark/deploy/worker/Worker.scala#L374-L389).
- [Source config: preferConfiguredMasterAddress](https://github.com/apache/spark/blob/v4.1.3/core/src/main/scala/org/apache/spark/internal/config/Worker.scala#L77-L80).
- [Source launcher: JVM/env cho Worker](https://github.com/apache/spark/blob/v4.1.3/launcher/src/main/java/org/apache/spark/launcher/SparkClassCommandBuilder.java#L52-L107).
- [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/) · [DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) · [Downward API](https://kubernetes.io/docs/concepts/workloads/pods/downward-api/).
