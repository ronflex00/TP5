#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
./scripts/bootstrap.sh
./scripts/smoke-test.sh
./scripts/check-unlabeled.sh
docker compose --profile evolution up -d app3
printf '\nPour tester App3 avec authentification, saisir : TP5_TEST_ADMIN=1 ./scripts/smoke-test.sh\n'
