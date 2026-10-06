#!/bin/bash
# Usage : get_status.sh <instance_id>
set -euo pipefail

fail() {
  printf '{"status":"error","message":"%s"}\n' "$1"
  exit 1
}

[ $# -eq 1 ] || fail "usage: get_status.sh <instance_id>"
ID="$1"
[[ "$ID" =~ ^rent-[A-Za-z0-9_-]+$ ]] || fail "invalid instance_id"

# Un conteneur inexistant n'est pas une erreur : c'est le statut "absent"
if ! docker inspect "$ID" >/dev/null 2>&1; then
  printf '{"status":"absent","instance_id":"%s"}\n' "$ID"
  exit 0
fi

STATE="$(docker inspect -f '{{.State.Status}}' "$ID")"
if [ "$STATE" = "running" ]; then STATUS="running"; else STATUS="stopped"; fi

printf '{"status":"%s","instance_id":"%s"}\n' "$STATUS" "$ID"
