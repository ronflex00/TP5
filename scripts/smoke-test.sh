#!/usr/bin/env bash
# Vérifications réelles : NE PAS prétendre à un PASS avant exécution Docker.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v docker >/dev/null || { echo "Docker absent" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl absent" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python absent" >&2; exit 1; }
[[ -s certs/local-ca.crt ]] || { echo "Créer le certificat local d'abord" >&2; exit 1; }

get_http() { curl --noproxy '*' --fail --silent --show-error --max-time 8 "$@"; }
http_status() { curl --noproxy '*' --silent --output /dev/null --write-out '%{http_code}' --max-time 8 "$@"; }
assert_has() { [[ "$1" == *"$2"* ]] || { echo "ECHEC contenu attendu : $2" >&2; exit 1; }; }
assert_status() { [[ "$1" == "$2" ]] || { echo "ECHEC statut: attendu $2, obtenu $1" >&2; exit 1; }; }

printf '[1] Conteneurs Docker\n'
docker compose ps
printf '[2] Routage HTTP par nom d hôte\n'
body1="$(get_http -H 'Host: app1.localhost' http://127.0.0.1/)"
assert_has "$body1" 'App1 - Instance'
body2="$(get_http -H 'Host: app2.localhost' http://127.0.0.1/)"
assert_has "$body2" 'App2 - Bonjour'
assert_status "$(http_status -H 'Host: inconnu.localhost' http://127.0.0.1/)" 404
printf '[3] Dashboard et API locale\n'
assert_status "$(http_status http://127.0.0.1:8080/dashboard/)" 200
routers="$(get_http http://127.0.0.1:8080/api/http/routers)"
services="$(get_http http://127.0.0.1:8080/api/http/services)"
ROUTERS="$routers" SERVICES="$services" python3 - <<'PY'
import json, os
r = json.loads(os.environ['ROUTERS'])
s = json.loads(os.environ['SERVICES'])
assert any(i.get('name', '').startswith('app1@') for i in r), 'router app1 non découvert'
assert any(i.get('name', '').startswith('app2@') for i in r), 'router app2 non découvert'
assert any(i.get('name') == 'app1-svc@docker' for i in s), 'service app1-svc absent'
print('Routers App1/App2 et service App1 visibles')
PY

printf '[4] Load Balancing deux instances App1\n'
reponses=''
for _ in $(seq 1 20); do
  reponses+="$(get_http -H 'Host: app1.localhost' http://127.0.0.1/)"
done
assert_has "$reponses" 'App1 - Instance A'
assert_has "$reponses" 'App1 - Instance B'
printf 'Les deux backends A/B ont répondu.\n'

printf '[5] Validation HTTPS avec certificat CA (AUCUN -k)\n'
assert_has "$(get_http --cacert certs/local-ca.crt --resolve 'app1.localhost:443:127.0.0.1' https://app1.localhost/)" 'App1 - Instance'
assert_has "$(get_http --cacert certs/local-ca.crt --resolve 'app2.localhost:443:127.0.0.1' https://app2.localhost/)" 'App2 - Bonjour'

printf '[6] Ports et identité des conteneurs\n'
python3 scripts/verify-docker-runtime.py

if [[ "${TP5_TEST_ADMIN:-0}" == 1 ]]; then
  printf '[7] Application 3 privée (profil evolution attendu)\n'
  assert_status "$(http_status --cacert certs/local-ca.crt --resolve 'app3.localhost:443:127.0.0.1' https://app3.localhost/)" 401
  if [[ -z "${TP5_ADMIN_PASSWORD:-}" ]]; then
    read -r -s -p 'Mot de passe App3 : ' TP5_ADMIN_PASSWORD
    echo
  fi
  assert_has "$(get_http --cacert certs/local-ca.crt --resolve 'app3.localhost:443:127.0.0.1' -u "admin:$TP5_ADMIN_PASSWORD" https://app3.localhost/)" 'App3 - Zone protegee'
  unset TP5_ADMIN_PASSWORD
fi
printf '\nPASS : les vérifications demandées par ce script ont réussi sur cette machine.\n'
printf 'Restent à faire séparément : test réseau depuis une machine non autorisée, inspection de la santé en situation de panne et revue des logs.\n'
