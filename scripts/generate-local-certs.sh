#!/usr/bin/env bash
# Certificat TLS du laboratoire, jamais destiné à la production.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
umask 077
command -v openssl >/dev/null || { echo "openssl introuvable" >&2; exit 1; }
mkdir -p certs
if [[ -e certs/local-ca.key || -e certs/localhost.key ]] && [[ "${1:-}" != "--force" ]]; then
  if [[ -s certs/local-ca.crt && -s certs/localhost.crt && -s certs/local-ca.key && -s certs/localhost.key ]]; then
    echo "Certificats locaux déjà présents. --force pour les régénérer (invalide la confiance précédente)."
    exit 0
  fi
  echo "Certificats partiels : examiner certs/ puis utiliser --force si nécessaire." >&2; exit 2
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
openssl req -x509 -newkey rsa:3072 -nodes -sha256 -days 1095 \
  -subj "/CN=DevTech Lab Local CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -keyout certs/local-ca.key -out certs/local-ca.crt >/dev/null 2>&1
cat > "$tmp/host-ext.cnf" <<'EOF'
subjectAltName = DNS:app1.localhost,DNS:app2.localhost,DNS:app3.localhost,DNS:admin.localhost
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
EOF
openssl req -new -newkey rsa:3072 -nodes -sha256 \
  -subj "/CN=app1.localhost" -keyout certs/localhost.key -out "$tmp/localhost.csr" >/dev/null 2>&1
openssl x509 -req -sha256 -days 365 \
  -in "$tmp/localhost.csr" -CA certs/local-ca.crt -CAkey certs/local-ca.key \
  -CAcreateserial -out certs/localhost.crt -extfile "$tmp/host-ext.cnf" >/dev/null 2>&1
openssl verify -CAfile certs/local-ca.crt certs/localhost.crt
openssl x509 -in certs/localhost.crt -noout -checkhost app1.localhost
openssl x509 -in certs/localhost.crt -noout -checkhost app2.localhost
chmod 600 certs/local-ca.key certs/localhost.key
chmod 644 certs/local-ca.crt certs/localhost.crt
rm -f certs/local-ca.srl
echo "Certificat signé localement généré. Pour vérifier HTTPS : curl --cacert certs/local-ca.crt ... (sans -k)."
echo "ATTENTION : ne jamais ajouter certs/*.key au dépôt Git."
