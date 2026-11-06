# TP5 - Reverse Proxy, Load Balancing et sécurité avec Traefik

**Entreprise fictive : DevTech Solutions.** Projet de laboratoire reproductible à partir du sujet PDF « TP5 - Reverse Proxy et Load Balancing avec Traefik et Docker » (26 pages, 5 exercices, 21 questions). Il ne représente pas un déploiement de production.

## Résultat visé

```text
Machine locale (ports 127.0.0.1:80, :443, :8080)
                |
     +----------v-----------+
     | Traefik v3.7.17      |
     | Docker provider      |
     | EntryPoints 80/443   |
     +---------+------------+
               | Docker frontend (aucun port hôte des applications)
        +------+-------+-------------------+
        |              |                   |
  Host app1       Host app2         HTTPS app3.localhost
     |                |              middleware BasicAuth
  Service app1    Service app2             |
    /     \          |                  App3 Nginx
 App1 A  App1 B    App2 Nginx        (profil evolution)

Dashboard/API du laboratoire : 127.0.0.1:8080, JAMAIS en accès public.
```

## 1. Prérequis

- Linux / WSL2 / Docker Desktop avec Docker Engine et Docker Compose v2.
- Docker daemon fonctionnel, accès au socket Unix Docker ; `curl`, `openssl`, `python3`, Bash. `htpasswd` (apache2-utils) est utilisé s'il est présent ; sinon le script emploie l'image officielle `httpd:2.4-alpine` de façon éphémère.
- Ports hôte **80, 443 et 8080** libres en IPv4 sur 127.0.0.1.
- Sur Arch Linux : `sudo pacman -S docker docker-compose curl openssl apache` (adapter aux paquets installés). Sur Debian/Ubuntu : `sudo apt install docker.io docker-compose-plugin curl openssl apache2-utils` selon dépôts. Pas d'installation automatisée de paquets par ce projet.
- Le socket Docker est sensible. Exécuter ce laboratoire sur un hôte de développement de confiance, **pas** sur un daemon exposé au réseau.

## 2. Démarrage rapide (état final HTTP + HTTPS)

```bash
cd TP5_Traefik_DevTech
./scripts/bootstrap.sh
./scripts/smoke-test.sh
```

`bootstrap.sh` génère une CA locale et son certificat (sans aucune clé livrée dans le dépôt), demande un mot de passe de laboratoire pour App3 puis crée un fichier `htpasswd` **haché avec BCrypt**, crée le réseau `frontend`, vérifie Docker Compose et démarre Traefik + App1 A/B + App2.

Si les ports sont déjà utilisés, arrêter les services concernés (ne pas désactiver arbitrairement des services système).

Vérification de configuration uniquement :

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail 60 traefik
```

Accès : `http://app1.localhost`, `http://app2.localhost`, `http://127.0.0.1:8080/dashboard/`. Si votre résolution DNS de `.localhost` est différente, utiliser :

```bash
curl --noproxy '*' -H 'Host: app1.localhost' http://127.0.0.1/
curl --noproxy '*' -H 'Host: app2.localhost' http://127.0.0.1/
```

## 3. Progression exacte des exercices du sujet

### Exercice 1 — Déploiement initial

```bash
docker network inspect frontend
docker compose ps
docker compose logs traefik
curl --noproxy '*' -I http://127.0.0.1:8080/dashboard/
```

**EntryPoint** : port sur lequel Traefik reçoit la requête (80 ou 443). **Router** : règle de sélection (`Host(...)`) et association à un service.

### Exercice 2 — Routes App1 et App2

```bash
curl --noproxy '*' -H 'Host: app1.localhost' http://127.0.0.1/
curl --noproxy '*' -H 'Host: app2.localhost' http://127.0.0.1/
curl --noproxy '*' http://127.0.0.1:8080/api/http/routers
curl --noproxy '*' http://127.0.0.1:8080/api/http/services
```

Les labels des applications définissent `traefik.enable=true`, la règle `Host`, l'entrypoint et le port Nginx privé **8080**. **Écart volontaire et documenté** : l'image `nginxinc/nginx-unprivileged` utilise 8080 (au lieu du port 80 de l'exemple de cours), afin de fonctionner en **non-root**. Le port externe de Traefik demeure 80/443. Aucune application Nginx n'a de section `ports:`.

### Exercice 3 — Répartition App1 A/B

La configuration finale inclut déjà App1B ; on peut reproduire l'ajout progressif :

```bash
docker compose stop app1b  # observer App1 seule
docker compose start app1b # observer App1 A + App1 B
for i in $(seq 1 15); do curl -fsS --noproxy '*' -H 'Host: app1.localhost' http://127.0.0.1/ | grep '<h1>'; done
```

Les deux conteneurs utilisent **exactement les mêmes labels de router/service**, définis par l'ancre YAML `x-app1-labels`. Le service logique `app1-svc@docker` regroupe bien deux backends : le 6 novembre 2026, l'API en a exposé deux et 30 requêtes ont produit 15 réponses A et 15 réponses B. Pendant l'arrêt d'App1B, 10/10 réponses provenaient d'App1A ; après redémarrage, la répartition 15/15 est revenue.

- **Routage** : choisit App1 ou App2 selon `Host`.
- **Load balancing** : choisit App1A ou App1B pour les requêtes à App1.

### Exercice 4 — Contrôles de sécurité

```bash
./scripts/check-unlabeled.sh              # service sans label : aucune route
python3 scripts/verify-docker-runtime.py # ports/identité/read_only/health
curl --noproxy '*' -o /dev/null -w '%{http_code}\n' -H 'Host: inconnu.localhost' http://127.0.0.1/
```

Le dashboard/API en **mode laboratoire** est lié à **127.0.0.1:8080** ; `api.insecure=true` n'est pas acceptable pour une exposition publique. `docker.sock:ro` ne transforme PAS l'API Docker en API lecture seule. Le montage doit être remplacé ou protégé par un **socket-proxy filtrant** pour une cible de production. Un `Host(...)` **n'est pas** une authentification.

### Exercice 5 — Troisième application + HTTPS + authentification + santé

```bash
docker compose --profile evolution up -d app3
# HTTPS valide si la CA locale est explicitement approuvée PAR curl (sans -k)
curl --noproxy '*' --cacert certs/local-ca.crt --resolve app1.localhost:443:127.0.0.1 https://app1.localhost/
curl --noproxy '*' --cacert certs/local-ca.crt --resolve app2.localhost:443:127.0.0.1 https://app2.localhost/
# La route privée sans authentification doit répondre 401
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' --cacert certs/local-ca.crt --resolve app3.localhost:443:127.0.0.1 https://app3.localhost/
# Tester l'authentification (saisie interactive du mot de passe)
TP5_TEST_ADMIN=1 ./scripts/smoke-test.sh
```

Le certificat local est signé par une CA de laboratoire et non par une autorité publiquement approuvée. Le test `--cacert` est une **validation de confiance explicite**, sans contournement `-k`. `app3.htpasswd` est généré et ignoré par Git. Les healthchecks Docker sont définis pour App1, App1B, App2 et App3 ; App1 dispose en plus de checks côté Traefik. Les conteneurs sur le même hôte **ne constituent pas une haute disponibilité de l'hôte**.

Le middleware `redirect-to-https@file` est défini mais **non appliqué aux routes HTTP pédagogiques** afin que les tests du cours (HTTP) fonctionnent. Pour une mise en ligne réelle, associer ce middleware aux routes HTTP après avoir validé HTTPS, puis retirer les routes non nécessaires.

## 4. Tests de sécurité et preuves

```bash
./scripts/smoke-test.sh
./scripts/check-unlabeled.sh
python3 -m pytest -q
bash -n scripts/*.sh
```

Le script de tests ne falsifie aucun résultat : il échoue si l'une des assertions ne passe pas. Le test d'accès au dashboard depuis une **autre machine** nécessite deux machines et doit être réalisé séparément. Les tests de panne (`docker compose stop app1`) doivent se faire à un moment contrôlé pour observer le retrait du backend ; redémarrer `docker compose start app1` ensuite. Voir [grille de validation](docs/CHECKLIST_VALIDATION.md).

Les sorties de production locale peuvent être enregistrées **après expurgation** sous `preuves-locales/`. Ce dossier est ignoré par Git.

## 5. Arborescence et livrables

```text
docker-compose.yml           Traefik + Nginx App1 A/B, App2, App3 optionnelle
config/traefik.yaml         Configuration statique
config/dynamic/https.yaml   TLS, certificats, middlewares, BasicAuth
app1/, app1b/, app2/, app3/  Pages Nginx distinctes
scripts/                    Bootstrap, CA locale, bcrypt, tests
certs/, secrets/            Dossiers vides sauf README, secrets créés localement
tests/                     Tests statiques du kit
README.md                  Exécution et consignes
CORRECTION_EXERCICES.md     Correction des 5 exercices
QUESTIONS_REPONSES.md      Réponses aux 21 questions du PDF
docs/ARCHITECTURE_SECURITE.md, docs/CHECKLIST_VALIDATION.md
PROMPT_CODEX_VALIDATION.txt  Guide de validation Docker réelle sur ta machine
```

Les réponses complètes et la cartographie sécurité sont également reprises dans le rapport Word/PDF livré avec le kit.

## 6. Arrêt, nettoyage et risques résiduels

```bash
docker compose --profile evolution --profile audit down
# NE PAS ajouter -v ; le réseau frontend externe subsiste.
# Suppression facultative du réseau si non partagé : docker network rm frontend
```

**Limites majeures** : l'API Docker montée dans Traefik reste sensible, le dashboard utilise `api.insecure` en laboratoire, les cinq conteneurs restent sur un réseau partagé non segmenté, la CA TLS est locale, les images utilisent des tags (non des digests verrouillés), et il n'existe aucune haute disponibilité multi-hôtes. Les mesures de production sont décrites dans `docs/ARCHITECTURE_SECURITE.md`. La validation locale Docker a été réalisée le 6 novembre 2026 ; le scan d'images Trivy et le test depuis une seconde machine restent **NON TESTÉS**.

**Sources documentaires :** énoncé de TP5 fourni ; [Traefik Docker Provider](https://doc.traefik.io/traefik/v3.7/reference/install-configuration/providers/docker/), [Traefik TLS](https://doc.traefik.io/traefik/reference/routing-configuration/http/tls/tls-certificates/), [Traefik BasicAuth](https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/basicauth/), [NGINX Unprivileged](https://hub.docker.com/r/nginxinc/nginx-unprivileged).
