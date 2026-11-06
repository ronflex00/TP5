# TP5 - Les 21 questions de compréhension corrigées

**Source :** section 19 du sujet (pages 23-24). Réponses concises adaptées à une interrogation orale.

**1. Qu'est-ce qu'un reverse proxy ?**
Un serveur qui reçoit les requêtes des clients puis les transmet aux applications appropriées. Il centralise l'entrée du trafic et masque les adresses internes des backends.

**2. Quelle est la différence entre un reverse proxy et un Load Balancer ?**
Un reverse proxy sert d'intermédiaire et route les requêtes. Un load balancer répartit le trafic entre plusieurs instances d'un service. Traefik peut remplir les deux rôles.

**3. Quel est le rôle de Traefik dans une architecture Docker ?**
Traefik découvre les conteneurs autorisés, configure leurs routes à partir des labels et répartit les requêtes vers les bons services.

**4. Quelle est la différence entre configuration statique et dynamique ?**
La statique initialise Traefik (entrypoints, providers, API). La dynamique décrit les routers, services, middlewares et paramètres TLS des routes.

**5. À quoi sert un provider ?**
À fournir à Traefik des informations de configuration. Le provider Docker lit les labels des conteneurs ; le provider file charge la configuration d'un fichier.

**6. Quel est le rôle d'un entrypoint ?**
C'est l'adresse/port réseau par lequel entre le trafic, par exemple web sur le port 80 ou websecure sur 443.

**7. Quelle différence entre un router et un service ?**
Le router décide quelle règle correspond à la requête (`Host(...)`) ; le service représente le backend vers lequel envoyer cette requête.

**8. Pourquoi utilise-t-on des labels Docker ?**
Pour déclarer les routes, ports internes et middlewares directement dans la définition des conteneurs et permettre la découverte automatique par Traefik.

**9. Quel est l'intérêt de `exposedByDefault: false` ?**
Éviter qu'un conteneur quelconque devienne automatiquement accessible par Traefik. Seuls ceux explicitement étiquetés `traefik.enable=true` peuvent être routés.

**10. Comment Traefik découvre-t-il automatiquement un nouveau conteneur ?**
Le provider Docker surveille les événements/états du daemon Docker, lit les labels des conteneurs autorisés et actualise la configuration dynamique.

**11. Quelle différence entre routage et Load Balancing ?**
Le routage choisit l'application, le load balancing choisit l'une des instances disponibles de cette même application.

**12. Pourquoi surveiller la santé des backends ?**
Pour éviter d'envoyer des requêtes vers une instance indisponible et améliorer la continuité du service. Un healthcheck ne remplace pas un plan de haute disponibilité multi-hôtes.

**13. Pourquoi protéger le dashboard ?**
Il révèle la topologie, les routes, les services et leur configuration. Un accès non autorisé facilite la reconnaissance et pourrait augmenter les risques opérationnels.

**14. Pourquoi un router TLS ne garantit-il pas à lui seul un certificat valide ?**
Parce que `tls=true` ne garantit pas que le certificat soit signé par une autorité approuvée, qu'il corresponde au nom demandé ou qu'il soit encore valide. Il faut vérifier la chaîne de confiance.

**15. Comment ajouter une instance backend sans changer le point d'entrée client ?**
Ajouter un deuxième conteneur au même service logique de Traefik (ou augmenter ses réplicas) ; le client conserve `app1.localhost` et son port habituel.

**16. Pourquoi `Host(...)` ne constitue-t-il pas une authentification ?**
Parce que n'importe quel client peut envoyer un en-tête Host. La règle sélectionne un router, elle ne prouve pas l'identité ni les permissions du client.

**17. Pourquoi `docker.sock:ro` ne garantit-il pas une API Docker en lecture seule ?**
Parce que `:ro` s'applique au montage du fichier socket, pas aux méthodes HTTP autorisées sur l'API Docker. Un client capable d'utiliser le socket peut toujours envoyer des opérations sensibles selon ses droits.

**18. Pourquoi protéger l'API autant que le dashboard ?**
L'API expose elle aussi des informations internes de routage et d'état. Limiter seulement l'interface visuelle ne suffit pas ; les endpoints JSON doivent recevoir les mêmes protections.

**19. Quelle différence entre réseau partagé et segmentation réseau ?**
Un réseau partagé permet aux conteneurs de se joindre. La segmentation répartit les composants en réseaux séparés et limite les communications aux flux nécessaires afin de réduire les mouvements latéraux.

**20. Pourquoi deux instances sur le même hôte ne suffisent-elles pas à la haute disponibilité ?**
Parce qu'une panne de l'hôte Docker, de son réseau ou du proxy peut arrêter simultanément les deux instances. La haute disponibilité exige d'éliminer les points de défaillance communs.

**21. Quelles preuves permettent de vérifier qu'un contrôle de sécurité fonctionne ?**
Les configurations seules ne suffisent pas : montrer des tests et résultats réels. Par exemple API/dashboard refusés depuis une machine non autorisée, aucun port Nginx publié, 404 hôte inconnu, conteneur non étiqueté absent des routes, certificat TLS validé sans `-k`, BasicAuth 401/200, tests de santé et traces expurgées.
