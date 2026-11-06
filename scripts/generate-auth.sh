#!/usr/bin/env bash
# BCrypt et fichier de secrets hors Git. Ne place pas de mot de passe en ligne de commande.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
umask 077
mkdir -p secrets
if [[ -n "${TP5_ADMIN_PASSWORD:-}" ]]; then
  password="$TP5_ADMIN_PASSWORD"
else
  if [[ ! -t 0 ]]; then
    echo "Saisir un mot de passe via un terminal ou exporter temporairement TP5_ADMIN_PASSWORD." >&2
    exit 1
  fi
  read -r -s -p "Mot de passe pour l'App3 privée : " password
  echo
fi
[[ ${#password} -ge 12 ]] || { echo "Utiliser au minimum 12 caractères" >&2; exit 2; }
auth_tmp="$(mktemp secrets/.app3.htpasswd.XXXXXX)"
trap 'rm -f "$auth_tmp"' EXIT
if command -v htpasswd >/dev/null; then
  printf '%s\n' "$password" | htpasswd -niBC 12 admin > "$auth_tmp"
elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  echo "htpasswd hôte absent : utilisation du conteneur Apache officiel." >&2
  docker image inspect httpd:2.4-alpine >/dev/null 2>&1 || docker pull httpd:2.4-alpine >&2
  printf '%s\n' "$password" | docker run --rm -i httpd:2.4-alpine \
    htpasswd -niBC 12 admin > "$auth_tmp"
else
  echo "Installer apache2-utils (htpasswd), ou démarrer Docker pour le repli conteneurisé." >&2
  exit 1
fi
mv "$auth_tmp" secrets/app3.htpasswd
chmod 600 secrets/app3.htpasswd
unset password TP5_ADMIN_PASSWORD || true
trap - EXIT
echo "Hash BCrypt créé dans secrets/app3.htpasswd, aucun mot de passe en clair stocké."
