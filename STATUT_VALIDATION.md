# Statut de validation - TP5 Traefik DevTech Solutions

**Validation locale réalisée le 6 novembre 2026 (Europe/Paris) sur Arch Linux.**

## PASS

- Docker client 29.9.3, Engine 29.8.2, Compose 5.7.0 ; Traefik 3.7.17 réellement exécuté.
- `docker compose config --quiet`, `bash -n scripts/*.sh` et `compileall` : succès.
- `pytest` : **45 tests réussis**.
- Traefik, App1A, App1B, App2, App3 et le témoin `non-expose` démarrés ; toutes les applications observées `healthy`.
- Dashboard local : HTTP 200 sur `127.0.0.1:8080` ; ports 80/443/8080 liés exclusivement à `127.0.0.1`.
- Routage : App1 et App2 corrects ; domaine inconnu : HTTP 404.
- API Traefik : routers attendus présents ; `app1-svc@docker` contient deux serveurs.
- Load balancing : 30 requêtes = 15 réponses App1A et 15 App1B.
- Résilience : App1B arrêté, 10/10 réponses servies par App1A ; après reprise, 15/15.
- HTTPS App1/App2 : HTTP 200 avec `--cacert`, sans `-k` ; certificat SAN valide jusqu'au 6 novembre 2027.
- App3 : HTTP 401 sans identifiants, HTTP 200 avec identifiants valides ; aucun mot de passe journalisé ou conservé en clair.
- En-têtes : `nosniff`, `DENY`, `no-referrer` ; en-tête alias malveillant rejeté HTTP 400.
- Applications : aucun port hôte/socket Docker, UID 101:101, racine en lecture seule, `cap_drop=ALL`, `no-new-privileges`.
- Service sans opt-in : aucun router Traefik.
- État final : tous les conteneurs du projet arrêtés et supprimés proprement ; réseau externe `frontend` conservé.

## NON TESTÉ

- Refus du dashboard/API depuis une seconde machine : aucune seconde machine n'était disponible.
- Scan Trivy des images : outil non installé ; aucun résultat de scan n'est revendiqué.
- Haute disponibilité multi-hôtes et panne complète de l'hôte : hors périmètre de ce laboratoire mono-hôte.

## Corrections issues de l'exécution

- Mise à niveau de Traefik 3.5.2 vers 3.7.17 : la version initiale utilisait l'API Docker 1.24, refusée par Docker Engine 29.
- Ajout de `DAC_READ_SEARCH` après `cap_drop: ALL` pour lire les clés et le hash locaux en mode 0600 sans les rendre lisibles par tous.
- Rejet des noms d'en-têtes aliasés via `global.aliasHeadersStrategy: reject`.
- Repli BCrypt conteneurisé quand `htpasswd` n'est pas installé sur l'hôte.
- Attente bornée du healthcheck dans `check-unlabeled.sh`, au lieu d'une temporisation fixe instable.

Rapport détaillé : `docs/preuves/RAPPORT_VALIDATION_FINALE.md`.
