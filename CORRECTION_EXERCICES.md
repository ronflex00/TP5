# TP5 - Corrigé des cinq exercices pratiques

**Source :** énoncé DevTech Solutions, section 18, pages 22-23. Les procédures ci-dessous ont été confrontées à une exécution Docker réelle le 6 novembre 2026 ; les observations détaillées se trouvent dans `docs/preuves/RAPPORT_VALIDATION_FINALE.md`.

## Exercice 1 - Déploiement initial

1. **Créer frontend** : `docker network create frontend` ou `./scripts/bootstrap.sh` (idempotent).
2. **Déployer Traefik** : `docker compose up -d traefik` après génération du certificat et du fichier de hash.
3. **Dashboard** : `http://127.0.0.1:8080/dashboard/` ; route d'administration limitée à la loopback.
4. **Ports** : `docker compose ps` puis `docker inspect tp5-traefik`. Attendu : 80/443/8080 sur `127.0.0.1`, aucun port Nginx sur l'hôte.
5. **EntryPoint vs Router** : l'EntryPoint reçoit le trafic sur un port ; le Router applique une règle `Host(...)` pour le diriger vers un service.

## Exercice 2 - Routage par Host

1. **Apps** : App1 et App2 sont des conteneurs Nginx avec des pages HTML reconnaissables.
2. **Labels** : `traefik.enable=true`, `routers.*.rule`, `routers.*.entrypoints`, `services.*.loadbalancer.server.port=8080`.
3. **App1** : `curl --noproxy '*' -H 'Host: app1.localhost' http://127.0.0.1/` doit contenir `App1 - Instance`.
4. **App2** : `curl --noproxy '*' -H 'Host: app2.localhost' http://127.0.0.1/` doit contenir `App2 - Bonjour`.
5. **Dashboard/API** : `http://127.0.0.1:8080/api/http/routers` et `/api/http/services` doivent montrer App1 et App2 et leurs services.

**Réponse de principe :** les deux applications peuvent utiliser le même port hôte 80 car le Router regarde l'en-tête HTTP `Host`. Le routage n'est pas une authentification : l'en-tête peut être choisi par le client.

## Exercice 3 - Load Balancing

1. **Deuxième instance** : le service `app1b` est inclus avec son propre dossier.
2. **Réponse différente** : pages `App1 - Instance A` et `App1 - Instance B`.
3. **API** : `app1-svc@docker` a montré deux backends fonctionnels lors de la validation.
4. **Répétition** : 30 requêtes ont produit 15 réponses A et 15 réponses B ; arrêt d'App1B : 10 réponses A sur 10, puis retour à 15/15 après reprise.
5. **Différence** : le routage sélectionne le service App1 parmi plusieurs applications ; le load balancing répartit la charge parmi ses instances.

**Disponibilité :** si une instance devient indisponible, les autres peuvent continuer à répondre si elles restent saines et si le mécanisme de healthcheck fonctionne. Deux conteneurs sur le même hôte ne protègent pas contre la panne de celui-ci.

## Exercice 4 - Sécurité

1. **`api.insecure: true`** : expose une interface de diagnostic sans authentification native, risquant de révéler des routes et informations internes. Ici le port 8080 est lié uniquement à `127.0.0.1`, protection locale qui n'équivaut pas à un contrôle d'accès multi-utilisateurs.
2. **Socket Docker** : accès très sensible à l'API du daemon, pouvant faciliter la compromission de l'hôte en cas d'abus. Le suffixe `:ro` n'empêche pas l'envoi de requêtes dangereuses à l'API Docker.
3. **Dashboard sécurisé** : en production, `api.insecure=false`, route `api@internal` HTTPS derrière authentification, VPN ou réseau d'administration, journalisation, contrôles d'accès réseau.
4. **Opt-in** : `exposedByDefault=false` et `traefik.enable=true` interdisent la création automatique d'une route pour chaque conteneur découvert. Tester `non-expose` (`./scripts/check-unlabeled.sh`). Cela n'empêche pas un opérateur Docker privilégié d'ajouter le label.
5. **TLS/certificat** : `tls=true` active TLS sur la route mais ne garantit ni le nom correct du certificat ni sa confiance par le client. Le test `curl --cacert certs/local-ca.crt ...` vérifie signature et nom **sans `-k`**.

## Exercice 5 - Évolution de l'architecture

**Architecture proposée :** trois applications App1, App2 et App3 derrière Traefik ; App1 dispose de deux instances A/B. HTTP pour la validation initiale, HTTPS local vérifié sur 443, et App3 privée accessible seulement en HTTPS avec le middleware `admin-auth@file`. Le dashboard est accessible seulement sur `127.0.0.1:8080` en laboratoire.

**Configurations utiles :**

- `docker-compose.yml` : routers App1, App2, App3, ports backend 8080, `exposedByDefault=false`, healthchecks Nginx, réseau frontend.
- `config/traefik.yaml` : entryPoints web 80 et websecure 443, providers Docker/fichier.
- `config/dynamic/https.yaml` : certificat local, version TLS minimum 1.2, en-têtes, BasicAuth externe, redirection HTTP->HTTPS définie (non activée sur les routes du TP).
- `scripts/generate-local-certs.sh` : CA locale et certificat valide pour les sous-domaines `.localhost`.
- `scripts/generate-auth.sh` : fichier `.htpasswd` BCrypt local et ignoré par Git.
- `scripts/smoke-test.sh` et `scripts/verify-docker-runtime.py` : preuves de routage, TLS et isolation.

**Politique de santé / disponibilité :** healthchecks Docker, healthcheck Traefik pour App1, possibilité de retirer un backend défaillant, limites d'une infrastructure mono-hôte, nécessité d'autres hôtes pour tolérer une panne du serveur.

**Segmentation cible** : ne pas conserver un seul réseau `frontend` pour des applications de sensibilités différentes en production. Utiliser des réseaux `proxy-app1`, `proxy-app2`, `proxy-app3` séparés avec Traefik comme seul membre commun et des restrictions supplémentaires pour les flux backend. Ce point est proposé, pas déployé dans le laboratoire.

**Risques à ne pas masquer** : socket Docker, dashboard mode insecure, tags non verrouillés, CA uniquement locale, absence de validation opérationnelle du poste utilisateur au moment de génération.
