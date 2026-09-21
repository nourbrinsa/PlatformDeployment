#!/bin/bash
# Supprime les conteneurs dont la location est expirée
set -euo pipefail

NOW="$(date -u +%s)"

for id in $(docker ps -aq --filter "label=app=projet-iac"); do
  expires="$(docker inspect -f '{{ index .Config.Labels "rental.expires_at" }}' "$id")"
  if [ "$expires" -le "$NOW" ]; then
    name="$(docker inspect -f '{{.Name}}' "$id" | tr -d '/')"
    docker rm -f "$id" >/dev/null
    echo "$(date -u +%FT%TZ) removed expired instance $name"
  fi
done
