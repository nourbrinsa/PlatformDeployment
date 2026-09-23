#!/bin/bash
# Usage : create_instance.sh <user_id> <distribution> <duree_minutes>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/../docker"
HOST_ADDRESS="${HOST_ADDRESS:-localhost}"

fail() {
  printf '{"status":"error","message":"%s"}\n' "$1"
  exit 1
}

# 1. Vérifier les paramètres
[ $# -eq 3 ] || fail "usage: create_instance.sh <user_id> <distribution> <duration_minutes>"
USER_ID="$1"; DISTRIBUTION="$2"; DURATION="$3"

[[ "$USER_ID" =~ ^[A-Za-z0-9_-]+$ ]] || fail "invalid user_id"
[[ "$DURATION" =~ ^[0-9]+$ ]] || fail "duration must be a number"
[ "$DURATION" -ge 1 ] && [ "$DURATION" -le 1440 ] || fail "duration must be between 1 and 1440"

case "$DISTRIBUTION" in
  ubuntu) BASE_IMAGE="ubuntu:24.04" ;;
  debian) BASE_IMAGE="debian:12" ;;
  *) fail "unsupported distribution: $DISTRIBUTION" ;;
esac

# 2. Construire l'image (rapide si déjà en cache)
IMAGE="ssh-$DISTRIBUTION"
docker build -q --build-arg BASE_IMAGE="$BASE_IMAGE" -t "$IMAGE" "$DOCKER_DIR" >/dev/null \
  || fail "image build failed"

# 3. Générer nom, mot de passe, date d'expiration
NAME="rent-${USER_ID}-$(openssl rand -hex 3)"
PASSWORD="$(openssl rand -hex 8)"
EXPIRES_EPOCH="$(date -u -d "+${DURATION} minutes" +%s)"
EXPIRES_AT="$(date -u -d "@${EXPIRES_EPOCH}" +%Y-%m-%dT%H:%M:%SZ)"

# 4. Lancer le conteneur (Docker choisit un port libre avec -p 22)
docker run -d --name "$NAME" \
  -e USER_PASSWORD="$PASSWORD" \
  -p 22 \
  --memory 256m \
  --cpus 0.5 \
  --pids-limit 100 \
  --restart unless-stopped \
  --label app=projet-iac \
  --label rental.owner="$USER_ID" \
  --label rental.distribution="$DISTRIBUTION" \
  --label rental.expires_at="$EXPIRES_EPOCH" \
  "$IMAGE" >/dev/null || fail "could not start container"

# 5. Récupérer le port choisi par Docker
SSH_PORT="$(docker port "$NAME" 22/tcp | head -n1 | sed 's/.*://')"

# 6. Renvoyer le JSON du contrat
printf '{"status":"running","instance_id":"%s","distribution":"%s","host":"%s","ssh_port":%s,"ssh_user":"student","ssh_password":"%s","expires_at":"%s"}\n' \
  "$NAME" "$DISTRIBUTION" "$HOST_ADDRESS" "$SSH_PORT" "$PASSWORD" "$EXPIRES_AT"
