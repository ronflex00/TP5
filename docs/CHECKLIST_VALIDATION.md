# Checklist de validation TP5 - Résultats du 6 novembre 2026

| Référence | Test concret | Preuve / commande | Statut observé |
|---|---|---|---|
| EX1-01 | Réseau frontend existe | `docker network inspect frontend` | PASS |
| EX1-02 | Traefik démarre sans erreur bloquante | `docker compose ps`, logs | PASS |
| EX1-03 | Dashboard local accessible | curl `127.0.0.1:8080/dashboard/` | PASS - 200 |
| EX1-04 | Ports limités à 127.0.0.1 | `verify-docker-runtime.py` | PASS |
| EX2-01 | App1 et App2 accessibles via Host | `smoke-test.sh` | PASS |
| EX2-02 | Routes et services présents dans API | API routers/services | PASS |
| EX2-03 | Hôte inconnu renvoie 404 | curl Host inconnu | PASS - 404 |
| EX3-01 | Deux instances App1 visibles | API `app1-svc@docker` | PASS - 2 |
| EX3-02 | Les deux instances répondent | 30 requêtes | PASS - A=15, B=15 |
| EX3-03 | Arrêt d'App1B laisse App1A actif | stop/curl/start | PASS - A=10, B=0 ; reprise 15/15 |
| EX4-01 | Aucun Nginx ne publie un port hôte | Docker inspect | PASS |
| EX4-02 | Conteneur sans opt-in non routé | `check-unlabeled.sh` | PASS |
| EX4-03 | API/dashboard refusés depuis machine distante | seconde machine | NON TESTÉ |
| EX4-04 | Absence de secrets dans labels et fichiers suivis | tests + revue Git | PASS |
| EX5-01 | Certificat signé et nom vérifié | OpenSSL + curl sans `-k` | PASS |
| EX5-02 | App3 répond 401 sans identifiants | curl HTTPS | PASS - 401 |
| EX5-03 | App3 répond 200 avec bons identifiants | smoke test sécurisé | PASS - 200 |
| EX5-04 | Healthchecks définis et healthy | Compose + inspect | PASS |
| SEC-01 | Docker socket absent de toutes les applications | inspection mounts | PASS |
| SEC-02 | Nginx non-root et durci | runtime verifier | PASS |
| SEC-03 | Noms d'en-têtes aliasés rejetés | curl `X_Auth_User` | PASS - 400 |
| SEC-04 | Trivy ou autre scan d'images | rapport d'analyse | NON TESTÉ |
| DOC-01 | Réponses aux 21 questions | tests statiques | PASS |
| DOC-02 | Matrice de sécurité section 20 | tests statiques | PASS |
| FIN-01 | Arrêt propre du projet | Compose `down` sans `-v` | PASS - aucun conteneur TP5 restant |

Les secrets générés (`certs/*`, `secrets/*`) et l'environnement `.venv` restent exclus de Git. Le test distant et la haute disponibilité de l'hôte ne sont pas déduits des contrôles locaux.
