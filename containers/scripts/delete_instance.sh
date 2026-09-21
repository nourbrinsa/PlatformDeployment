#!/bin/bash
# Usage : delete_instance.sh <instance_id>
set -euo pipefail

fail() {
  printf '{"status":"error","message":"%s"}\n' "$1"
  exit 1
}

[ $# -eq 1 ] || fail "usage: delete_instance.sh <instance_id>"
ID="$1"
[[ "$ID" =~ ^rent-[A-Za-z0-9_-]+$ ]] || fail "invalid instance_id"
docker inspect "$ID" >/dev/null 2>&1 || fail "instance not found"

docker rm -f "$ID" >/dev/null
printf '{"status":"deleted","instance_id":"%s"}\n' "$ID"
