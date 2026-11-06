#!/usr/bin/env bash
# Ce script vérifie qu'un service sans label ne gagne aucune route.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
docker compose --profile audit up -d non-expose
container_id="$(docker compose --profile audit ps -q non-expose)"
for _ in $(seq 1 30); do
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container_id")"
  [[ "$health" == "healthy" ]] && break
  [[ "$health" == "unhealthy" ]] && { echo "non-expose est unhealthy" >&2; exit 1; }
  sleep 1
done
[[ "${health:-}" == "healthy" ]] || { echo "Délai dépassé pour le healthcheck non-expose" >&2; exit 1; }
curl --noproxy '*' -fsS http://127.0.0.1:8080/api/http/routers | python3 -c '
import json,sys
routers=json.load(sys.stdin)
bad=[r.get("name","") for r in routers if "non-expose" in r.get("name", "")]
assert not bad, f"Route involontaire détectée: {bad}"
print("PASS: aucun router pour non-expose")
'
