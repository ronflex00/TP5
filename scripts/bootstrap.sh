#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v docker >/dev/null || { echo "Docker est indispensable pour exécuter le TP." >&2; exit 1; }
docker info >/dev/null || { echo "Démon Docker indisponible. Vérifier Docker Engine/Desktop." >&2; exit 1; }
./scripts/generate-local-certs.sh
if [[ ! -s secrets/app3.htpasswd ]]; then
  ./scripts/generate-auth.sh
fi
if ! docker network inspect frontend >/dev/null 2>&1; then
  docker network create frontend
fi
docker compose config --quiet
docker compose up -d
printf '\nServices :\n'
docker compose ps
printf '\nDashboard : http://127.0.0.1:8080/dashboard/\nApp1 : http://app1.localhost\nApp2 : http://app2.localhost\n'
printf 'Suite de tests : ./scripts/smoke-test.sh\n'
