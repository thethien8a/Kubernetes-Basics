#!/usr/bin/env bash
set -euo pipefail

runtime_root="$HOME/.local/share/k8s-practice/lesson30"
runtime_dir="$runtime_root/spark-4.0.2-java17"
java_url="https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21.1%2B2/OpenJDK17U-jre_aarch64_mac_hotspot_17.0.21.1_2.tar.gz"
spark_url="https://archive.apache.org/dist/spark/spark-4.0.2/spark-4.0.2-bin-hadoop3.tgz"
java_sha256="398046289ca1acef2d3800d74c55a31f08b2fee32a17ee7c1c4e4ad7489f8311"
spark_sha512="309ec3e0ed805d2bb560d85d521868640e6743efca079e33800766003bc1d290dcf2dcaed97840d11a900273d59d7df98e9a0764ccc7b1698ba12c2e57781539"

mkdir -p "$runtime_root"
lock_dir="$runtime_root/.prepare-runtime.lock"
if ! mkdir "$lock_dir"; then
  printf 'Cannot acquire the lab runtime setup lock: %s\n' "$lock_dir" >&2
  exit 1
fi

staging=""
cleanup() {
  if [[ -n "$staging" ]]; then
    rm -rf -- "$staging"
  fi
  rmdir "$lock_dir"
}
trap cleanup EXIT

if [[ ! -e "$runtime_dir" ]]; then
  staging=$(mktemp -d "$runtime_root/.prepare-runtime.XXXXXX")
  mkdir -p "$staging/runtime/java" "$staging/runtime/spark"

  curl --fail --location --retry 2 --output "$staging/java.tar.gz" "$java_url"
  printf '%s  %s\n' "$java_sha256" "$staging/java.tar.gz" | shasum -a 256 -c -

  curl --fail --location --retry 2 --output "$staging/spark.tgz" "$spark_url"
  printf '%s  %s\n' "$spark_sha512" "$staging/spark.tgz" | shasum -a 512 -c -

  tar -xzf "$staging/java.tar.gz" -C "$staging/runtime/java" --strip-components 1
  tar -xzf "$staging/spark.tgz" -C "$staging/runtime/spark" --strip-components 1
  test -x "$staging/runtime/java/Contents/Home/bin/java"
  test -x "$staging/runtime/spark/bin/spark-submit"
  # Publish both tool directories together, so a retry never finds a partial install.
  mv "$staging/runtime" "$runtime_dir"
fi

java_home="$runtime_dir/java/Contents/Home"
spark_home="$runtime_dir/spark"
"$java_home/bin/java" -version
JAVA_HOME="$java_home" SPARK_HOME="$spark_home" SPARK_CONF_DIR="$spark_home/conf" \
  "$spark_home/bin/spark-submit" --version
