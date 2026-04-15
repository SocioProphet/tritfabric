#!/usr/bin/env bash
set -euo pipefail
ROOT=$(dirname "$0")
OUT_DIR="$ROOT/../out"
REPORT_MD="$OUT_DIR/report.md"
PDF="$OUT_DIR/report.pdf"
SIG="$OUT_DIR/report.sig"
KEY="${1:-signing_key.pem}"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc is required to render PDF" >&2
  exit 2
fi

pandoc "$REPORT_MD" -o "$PDF"

# Sign with OpenSSL (PKCS#1 v1.5 SHA-256). Generate key with: openssl genrsa -out signing_key.pem 2048
openssl dgst -sha256 -sign "$KEY" -out "$SIG" "$PDF"
openssl base64 -in "$SIG" -out "$SIG.b64"

echo "PDF: $PDF"
echo "SIG: $SIG (.b64)"
