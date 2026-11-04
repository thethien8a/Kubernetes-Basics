import hashlib
import json
import subprocess
from pathlib import Path


EXPECTED_UID = "02539279-ba11-446f-90bb-120a66337e38"
MANIFEST = Path(__file__).resolve().with_name("02-selector-missing.yaml")
ALLOWED_HASHES = {
    "9fddcddefa765cd38e52df48c1747143760887af5615e8c84aa5fb9e985a2e6d",
    "6f9032ed6c3c421139e19b1b4d56bd10758401a0557ab8218ae2140ba5061b62",
}
BASE = [
    "/usr/local/bin/kubectl",
    f"--kubeconfig={Path.home() / '.kube/config'}",
    "--context=k3d-de-k3d",
    "-n", "de-lab",
    "--request-timeout=10s",
]


def stop(message):
    raise SystemExit(f"Dừng: {message}")


def kubectl(*args, timeout=30):
    try:
        result = subprocess.run(
            BASE + list(args), capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired):
        stop("không chạy được kubectl hoặc đã hết thời gian; không tự thử lại.")
    if result.returncode:
        stop(f"bước {args[0]} lỗi; giữ nguyên trạng thái để mentor kiểm tra.")
    return result.stdout


def read_resource(kind, name):
    return json.loads(kubectl("get", kind, name, "-o", "json"))


def check_target():
    pod = read_resource("pod", "placement-missing")
    metadata, spec = pod["metadata"], pod["spec"]
    if (
        metadata["uid"] != EXPECTED_UID
        or metadata.get("ownerReferences")
        or metadata.get("deletionTimestamp")
        or pod.get("status", {}).get("phase") != "Pending"
        or spec.get("nodeName")
        or spec.get("schedulingGates")
        or spec.get("nodeSelector") != {"lab-pool": "missing", "lab-tier": "memory"}
    ):
        stop("Pod không còn đúng đối chứng Pending đã ghi nhận; không xóa.")


def repaired_manifest(source):
    # Refuse unrelated edits rather than rewriting learner work.
    if hashlib.sha256(source).hexdigest() not in ALLOWED_HASHES:
        stop("manifest có thay đổi ngoài một field được phép; không ghi đè.")
    return source.replace(b"    lab-pool: missing\n", b"    lab-pool: batch\n", 1)


def main():
    if read_resource("namespace", "de-lab")["status"]["phase"] != "Active":
        stop("namespace de-lab chưa Active.")
    for verb in ("create", "delete"):
        if kubectl("auth", "can-i", verb, "pods").strip() != "yes":
            stop(f"thiếu quyền {verb} Pods.")
    check_target()

    source = MANIFEST.read_bytes()
    repaired = repaired_manifest(source)
    if source != repaired:
        MANIFEST.write_bytes(repaired)
    preview = json.loads(kubectl(
        "create", "--dry-run=client", "--validate=true",
        "-f", str(MANIFEST), "-o", "json",
    ))
    if (
        preview["kind"] != "Pod"
        or preview["metadata"]["name"] != "placement-missing"
        or preview["metadata"]["namespace"] != "de-lab"
        or preview["spec"]["nodeSelector"] != {"lab-pool": "batch", "lab-tier": "memory"}
    ):
        stop("manifest chưa đúng target; không xóa Pod.")

    # Recheck identity after validation so a replacement Pod is not intentionally deleted.
    check_target()
    kubectl("delete", "pod", "placement-missing", "--wait=true",
            "--timeout=60s", "--request-timeout=0", timeout=90)
    kubectl("apply", "-f", str(MANIFEST))
    kubectl("wait", "--for=condition=Ready", "pod/placement-missing",
            "--timeout=120s", "--request-timeout=0", timeout=150)

    pod = read_resource("pod", "placement-missing")
    ready = any(c["type"] == "Ready" and c["status"] == "True"
                for c in pod["status"].get("conditions", []))
    if (
        pod["metadata"]["uid"] == EXPECTED_UID
        or pod["status"]["phase"] != "Running"
        or pod["spec"].get("nodeName") != "k3d-de-k3d-agent-0"
        or pod["spec"].get("nodeSelector") != {"lab-pool": "batch", "lab-tier": "memory"}
        or not ready
    ):
        stop("Pod mới chưa đạt placement/Ready dự kiến; không tự thử lại.")
    print("NAME               UID                                   PHASE    NODE                 READY")
    print(f"placement-missing  {pod['metadata']['uid']}  Running  k3d-de-k3d-agent-0  True")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError):
        stop("không đọc được file hoặc phản hồi hợp lệ; không tự thử lại.")
