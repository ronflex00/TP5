# Rapport de validation finale - TP5 Traefik DevTech

**Date :** 6 novembre 2026, Europe/Paris

**Environnement :** Arch Linux, Docker client 29.9.3, Engine 29.8.2, Compose 5.7.0, Traefik 3.7.17, Python 3.14.9, OpenSSL 3.6.5.

**Périmètre :** projet `TP5_Traefik_DevTech` uniquement. Les mots de passe, hashes et clés privées sont exclus de cette preuve.

Le rapport Word a été régénéré avec ces résultats. Aucun convertisseur DOCX vers PDF n'étant installé sur ce poste, le PDF fourni reste le document original du kit ; le présent fichier Markdown constitue le complément runtime faisant foi pour les observations locales.

## Synthèse

| Contrôle | Résultat observé | Statut |
|---|---|---|
| Configuration Compose | `docker compose ... config --quiet`, code 0 | PASS |
| Tests Python | 45 tests réussis | PASS |
| Scripts Bash | Tous valides avec `bash -n` | PASS |
| Traefik | Version 3.7.17, provider Docker actif | PASS |
| Conteneurs | Traefik actif ; cinq Nginx `healthy` pendant l'audit | PASS |
| App1 HTTP | Page App1 A ou B | PASS |
| App2 HTTP | `App2 - Bonjour depuis App2` | PASS |
| Hôte inconnu | HTTP 404 | PASS |
| Dashboard/API | Dashboard 200 ; routers/services attendus présents | PASS |
| Load balancing | Deux backends API ; 30 requêtes : A=15, B=15 | PASS |
| Arrêt App1B | 10 requêtes : A=10, B=0 | PASS |
| Reprise App1B | 30 requêtes : A=15, B=15 | PASS |
| Ports Nginx | Aucun port hôte publié | PASS |
| Service sans opt-in | Aucun router `non-expose` | PASS |
| HTTPS App1/App2 | HTTP 200 avec CA locale, sans `-k` | PASS |
| App3 sans auth | HTTP 401 | PASS |
| App3 avec auth | HTTP 200 | PASS |
| En-têtes de sécurité | nosniff, DENY, no-referrer | PASS |
| Alias d'en-tête | `X_Auth_User` rejeté HTTP 400 | PASS |
| Accès distant dashboard/API | Aucune seconde machine disponible | NON TESTÉ |
| Scan Trivy | Outil non installé | NON TESTÉ |
| Haute disponibilité hôte | Architecture mono-hôte | NON TESTÉ / hors périmètre |
| État final | Compose `down`, aucun conteneur TP5 restant ; réseau `frontend` conservé | PASS |

## Commandes et observations principales

### Routage et découverte

```text
curl -H 'Host: app1.localhost' http://127.0.0.1/  -> App1 - Instance A/B
curl -H 'Host: app2.localhost' http://127.0.0.1/  -> App2 - Bonjour depuis App2
curl -H 'Host: inconnu.localhost' ...              -> 404
GET /api/http/routers                               -> app1, app1secure, app2, app2secure, app3secure
GET /api/http/services                              -> app1-svc avec 2 serveurs
```

### Load balancing et résilience

```text
30 requêtes, état normal        -> A=15, B=15
App1B arrêté, 10 requêtes       -> A=10, B=0
App1B redémarré, 30 requêtes    -> A=15, B=15
```

Ces résultats démontrent la continuité lors de l'arrêt d'un conteneur, pas la haute disponibilité de l'hôte Docker ni de Traefik.

### TLS et application privée

Le certificat a été vérifié avec `openssl verify` puis par curl avec `--cacert certs/local-ca.crt` et `--resolve`, sans option `-k`. Il couvre `app1.localhost`, `app2.localhost`, `app3.localhost` et `admin.localhost`, et expire le 6 novembre 2027.

App3 a répondu 401 sans en-tête Authorization et 200 avec les identifiants valides saisis/générés localement. Aucun mot de passe n'a été écrit dans les preuves ou le dépôt.

### Sécurité runtime

Pour App1, App1B, App2, App3 et `non-expose`, l'inspection Docker a confirmé : aucun port hôte, aucun socket Docker, utilisateur `101:101`, racine en lecture seule, `cap_drop=ALL`, `no-new-privileges` et état `healthy`. Les ports Traefik 80/443/8080 sont liés uniquement à `127.0.0.1`.

Le socket Docker de Traefik reste un risque important : le suffixe `:ro` protège le point de montage, mais ne rend pas l'API Docker elle-même accessible en lecture seule. Un socket-proxy filtré reste recommandé en production.

## Anomalies corrigées

1. Traefik 3.5.2 utilisait l'API Docker 1.24, refusée par Engine 29 : passage à Traefik 3.7.17.
2. `cap_drop=ALL` empêchait la lecture des fichiers locaux 0600 : ajout limité de `DAC_READ_SEARCH`.
3. Avertissement d'usurpation d'en-têtes Nginx : ajout de `aliasHeadersStrategy: reject`.
4. Absence de `htpasswd` sur l'hôte : repli vers l'image Apache officielle, mot de passe transmis sur stdin.
5. Temporisation fixe du test `non-expose` : remplacement par une attente bornée du healthcheck.

## Publication Git

Le SHA du commit et le résultat du push sont établis après la génération de ce fichier (un commit ne peut pas contenir de façon auto-référente son propre SHA). Ils doivent être relevés avec `git rev-parse HEAD` et `git ls-remote origin refs/heads/main` après publication.
