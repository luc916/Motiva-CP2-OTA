#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
CLI="${ARDUINO_CLI:-arduino-cli}"
args=()
if [[ -n "${ARDUINO_CONFIG:-}" ]]; then
  args+=(--config-file "$ARDUINO_CONFIG")
fi
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
mkdir -p evidencias
for versao in 1 2; do
  "$CLI" "${args[@]}" compile --fqbn esp32:esp32:esp32 \
    --build-path "$build_dir/v$versao" "firmware_v$versao" \
    2>&1 | tee "evidencias/compilacao-v$versao.txt"
  cp "$build_dir/v$versao/firmware_v$versao.ino.bin" "firmware_v$versao.bin"
done
cp firmware_v1/firmware_v1.ino wokwi/sketch.ino
python3 - <<'PY'
from pathlib import Path
import hashlib
p=Path('.')
nomes=['firmware_v1.bin','firmware_v2.bin','version.json',
       'firmware_v1/firmware_v1.ino','firmware_v2/firmware_v2.ino']
(p/'evidencias/SHA256SUMS.txt').write_text(''.join(
    hashlib.sha256((p/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in nomes))
PY
