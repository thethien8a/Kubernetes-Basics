#!/usr/bin/env bash
set -euo pipefail
umask 077

OPENSSL=/usr/bin/openssl
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TLS_DIR="$HOME/.local/share/k8s-practice/lesson16-tls"

if [[ ! -x "$OPENSSL" ]]; then
  printf 'Required executable not found: %s\n' "$OPENSSL" >&2
  exit 1
fi

# Refuse reuse so rerunning cannot replace keys or evidence from an earlier attempt.
if [[ -e "$TLS_DIR" || -L "$TLS_DIR" ]]; then
  printf 'Refusing to overwrite existing path: %s\n' "$TLS_DIR" >&2
  exit 1
fi

mkdir -p -- "$(dirname -- "$TLS_DIR")"
mkdir -m 700 -- "$TLS_DIR"

# Unencrypted keys are limited to this disposable lab and protected by local permissions.
"$OPENSSL" genrsa -out "$TLS_DIR/ca.key" 2048
"$OPENSSL" req -new -x509 -sha256 -days 7 \
  -key "$TLS_DIR/ca.key" \
  -config "$SCRIPT_DIR/ca.cnf" \
  -out "$TLS_DIR/ca.crt"

"$OPENSSL" genrsa -out "$TLS_DIR/server.key" 2048
"$OPENSSL" req -new -sha256 \
  -key "$TLS_DIR/server.key" \
  -config "$SCRIPT_DIR/server.cnf" \
  -out "$TLS_DIR/server.csr"

"$OPENSSL" x509 -req -sha256 -days 2 \
  -in "$TLS_DIR/server.csr" \
  -CA "$TLS_DIR/ca.crt" \
  -CAkey "$TLS_DIR/ca.key" \
  -CAcreateserial \
  -extfile "$SCRIPT_DIR/server.cnf" \
  -extensions v3_server \
  -out "$TLS_DIR/server.crt"

"$OPENSSL" verify -purpose sslserver \
  -CAfile "$TLS_DIR/ca.crt" "$TLS_DIR/server.crt"

"$OPENSSL" x509 -in "$TLS_DIR/server.crt" \
  -noout -subject -issuer -dates

"$OPENSSL" x509 -in "$TLS_DIR/server.crt" -noout -text |
  awk '/X509v3 Subject Alternative Name/ {getline; sub(/^[[:space:]]+/, ""); print "SAN=" $0}'

printf 'Files created in: %s\n' "$TLS_DIR"
printf 'No Kubernetes resources or system trust settings were changed.\n'
