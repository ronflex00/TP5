#!/usr/bin/env python3
"""Génère un rapport Word modifiable (python-docx)."""
from pathlib import Path
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"RAPPORT_TP5_DEVTECH_TRAEFIK.docx"
NAVY=RGBColor(15, 45, 68)
BLUE=RGBColor(24, 100, 163)
GRAY=RGBColor(94, 113, 127)
LIGHT=RGBColor(232,241,247)

D=Document()
sec=D.sections[0]
sec.page_height=Cm(29.7);sec.page_width=Cm(21)
sec.top_margin=Cm(1.7);sec.bottom_margin=Cm(1.65)
sec.left_margin=Cm(1.85);sec.right_margin=Cm(1.85)
sec.header_distance=Cm(0.65);sec.footer_distance=Cm(.65)
styles=D.styles
normal=styles['Normal'];normal.font.name='Aptos';normal.font.size=Pt(9.25);normal.font.color.rgb=NAVY
normal.paragraph_format.space_after=Pt(5)
normal.paragraph_format.line_spacing=1.13
for sname,size,spb,spa in [('Title',25,0,12),('Heading 1',15,13,7),('Heading 2',11.6,9,5),('Heading 3',10.2,7,3)]:
    style=styles[sname]
    style.font.name='Aptos Display' if sname in ('Title','Heading 1') else 'Aptos'
    style.font.size=Pt(size);style.font.bold=True;style.font.color.rgb=NAVY if sname!='Heading 3' else BLUE
    style.paragraph_format.space_before=Pt(spb)
    style.paragraph_format.space_after=Pt(spa)
    style.paragraph_format.keep_with_next=True

header=sec.header.paragraphs[0]
header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=header.add_run('DEVTECH SOLUTIONS   /   TP5   /   TRAEFIK & SECURITE')
run.bold=True;run.font.size=Pt(7.5);run.font.color.rgb=BLUE
footer=sec.footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=footer.add_run('TP5  •  Laboratoire pédagogique  |  Page ')
run.font.size=Pt(8);run.font.color.rgb=GRAY
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

def title(t):D.add_heading(t,0)
def h1(t):D.add_heading(t,1)
def h2(t):D.add_heading(t,2)
def h3(t):D.add_heading(t,3)
def p(t='',boldlead=None):
    x=D.add_paragraph()
    if boldlead and t.startswith(boldlead):x.add_run(boldlead).bold=True;x.add_run(t[len(boldlead):])
    else:x.add_run(t)
    return x

def mini(t):
    x=D.add_paragraph();x.style='Normal'
    x.paragraph_format.space_after=Pt(5)
    r=x.add_run(t);r.bold=True;r.font.color.rgb=BLUE;r.font.size=Pt(8.5)

def shade(cell,color='E8F1F7'):
    tcPr=cell._tc.get_or_add_tcPr()
    shd=OxmlElement('w:shd');shd.set(qn('w:fill'),color);tcPr.append(shd)

def table(headers,rows,widths=None):
    t=D.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.autofit=False
    if widths:
        for i,w in enumerate(widths):t.columns[i].width=Cm(w)
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i];c.text=str(h);shade(c,'D5E8F5');c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in c.paragraphs[0].runs:run.bold=True;run.font.size=Pt(8);run.font.color.rgb=NAVY
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):
            c=cells[i];c.text=str(v);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.TOP
            if widths:c.width=Cm(widths[i])
            for para in c.paragraphs:
                para.paragraph_format.space_after=Pt(1)
                para.paragraph_format.line_spacing=1.02
                for run in para.runs:run.font.size=Pt(7.7)
        if len(t.rows)%2==0:
            for c in cells:shade(c,'F6F9FB')
    D.add_paragraph().paragraph_format.space_after=Pt(1)
    return t

def bullet(t):
    x=D.add_paragraph(t,style='List Bullet');x.paragraph_format.space_after=Pt(3);return x

def caption(t):
    x=D.add_paragraph(t);x.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in x.runs:r.italic=True;r.font.size=Pt(7.5);r.font.color.rgb=GRAY

# Couverture
D.add_paragraph('\n')
x=D.add_paragraph();x.alignment=WD_ALIGN_PARAGRAPH.LEFT
r=x.add_run('RAPPORT TECHNIQUE  |  DEVOPS & CYBERSECURITE');r.bold=True;r.font.color.rgb=BLUE;r.font.size=Pt(10.5)
D.add_paragraph('')
title('TP5 - Reverse Proxy et\nLoad Balancing avec Traefik')
x=D.add_paragraph('DevTech Solutions   •   Docker Compose   •   Nginx   •   HTTPS et sécurité')
x.paragraph_format.space_after=Pt(28)
for r in x.runs:r.font.size=Pt(12);r.font.color.rgb=GRAY
D.add_picture(str(ROOT/'docs/schema/architecture.png'),width=Cm(17))
caption('Architecture du laboratoire : une entrée Traefik, trois applications, deux instances App1.')
D.add_paragraph('')
table(['Données de remise','Détails'],[
    ('Établissement / équipe','À renseigner'),
    ('Auteur(s)','À renseigner'),
    ('Date','6 novembre 2026 (validation locale)'),
    ('Périmètre','5 exercices, 21 questions, cartographie de sécurité, Docker Compose, tests'),
    ('Statut technique','45 tests statiques réussis ; Docker, routage, TLS et BasicAuth validés'),
],widths=[4.6,12.1])
p('Document de laboratoire validé localement avec Docker. Le scan Trivy et le test depuis une seconde machine restent explicitement non testés.')
D.add_page_break()

h1('1. Objectif et choix d’architecture')
p('Le sujet demande de remplacer plusieurs ports applicatifs par un point d’entrée unique Traefik et de démontrer le routage HTTP/HTTPS, la découverte Docker, la répartition entre deux backends, puis l’authentification et les protections de sécurité.')
p('Le système livré comprend Traefik 3.7.17 et quatre conteneurs Nginx : App1 A, App1 B, App2 et App3 (profil evolution). App1 A/B répondent au même nom app1.localhost et partagent un service logique ; App2 répond sur app2.localhost ; App3 est protégée en HTTPS sur app3.localhost.')
mini('Point de sécurité central : aucune application Nginx ne publie de port sur l’hôte ; seuls les ports de Traefik 80, 443 et 8080 sont liés à 127.0.0.1.')
h2('Architecture technique')
table(['Composant','Fonction','Port / exposition'],[
    ('Traefik','Reverse proxy, router, TLS, dashboard/API','Hôte 127.0.0.1:80 / :443 / :8080'),
    ('App1 / App1B','Deux instances Nginx pour la répartition','Docker 8080, aucun port hôte'),
    ('App2','Deuxième application indépendante','Docker 8080, aucun port hôte'),
    ('App3 (profil evolution)','Troisième application avec BasicAuth','HTTPS via Traefik uniquement'),
    ('Réseau frontend','Communication Traefik <-> services Docker','Réseau partagé, segmentation cible non appliquée'),
    ('CA locale + htpasswd','Certificat local et hash BCrypt hors Git','Fichiers créés par scripts, jamais livrés'),
],widths=[3.6,7.5,5.6])
h2('Concepts à expliquer')
for t in [
'EntryPoint : port d’entrée réseau (80 ou 443).',
'Router : règle de correspondance, par exemple Host(app1.localhost).',
'Service : backend logique contenant une ou plusieurs instances.',
'Middleware : traitement transversal, par exemple BasicAuth, en-têtes de sécurité ou redirection HTTPS.',
'Provider Docker : découverte des conteneurs autorisés par leurs labels.',
'Provider File : charge le certificat TLS et les middlewares décrits en YAML.',
]:bullet(t)

h1('2. Réalisation des cinq exercices')
h2('Exercice 1 — Déploiement initial')
p('Le réseau frontend est créé par bootstrap.sh s’il n’existe pas. Traefik lit config/traefik.yaml et publie les ports 80, 443 et 8080 uniquement sur l’interface loopback. Le dashboard a répondu HTTP 200 à l’adresse http://127.0.0.1:8080/dashboard/.')
p('La différence essentielle : l’entrypoint reçoit la requête sur un port ; le router applique une règle Host et désigne un service.')
h2('Exercice 2 — Routage par nom d’hôte')
p('App1 et App2 possèdent le label traefik.enable=true. Leurs routers distinguent app1.localhost et app2.localhost, bien qu’ils partagent le port 80 de Traefik. Le port Nginx interne est 8080 : l’image non privilégiée utilise ce port plutôt que 80, ce qui constitue un durcissement documenté par rapport à l’exemple du PDF.')
p('Commandes : curl --noproxy "*" -H "Host: app1.localhost" http://127.0.0.1/ ; même test pour app2.localhost ; consulter /api/http/routers et /api/http/services.')
h2('Exercice 3 — Répartition App1 A/B')
p('Deux conteneurs Nginx servent des réponses différentes : « App1 - Instance A » et « App1 - Instance B ». L’API a confirmé deux backends dans app1-svc@docker. Trente requêtes ont donné A=15 et B=15 ; pendant l’arrêt d’App1B, dix requêtes sur dix ont été servies par App1A, puis la répartition 15/15 est revenue après reprise.')
p('Le routage choisit l’application ; le load balancing choisit une instance au sein de l’application. Les healthchecks aident à écarter une instance indisponible.')
h2('Exercice 4 — Sécurité du reverse proxy')
p('Traefik est configuré avec exposedByDefault=false, et seul un label d’activation autorise une route Docker. Le service non-expose, lancé à part, sert à vérifier ce principe. Le dashboard/API n’est publié qu’en local. Aucune information d’authentification n’est placée dans les labels.')
p('Il reste deux risques majeurs du laboratoire : api.insecure=true n’authentifie pas les utilisateurs locaux ; docker.sock:ro protège le montage mais ne limite pas les opérations de l’API Docker. Une solution de production nécessiterait un dashboard sécurisé et un proxy de socket filtré.')
h2('Exercice 5 — Évolution et HTTPS')
p('App3 peut être activée avec docker compose --profile evolution up -d app3. Elle dispose d’un router HTTPS et d’un middleware BasicAuth lisant un fichier BCrypt exclu du dépôt. Le certificat couvre app1.localhost, app2.localhost et app3.localhost. La confiance est validée par curl --cacert, sans désactiver la vérification TLS.')
p('La variante cible prévoit une segmentation des réseaux applicatifs, l’authentification du dashboard, des healthchecks et une architecture multi-hôtes pour la disponibilité. Le réseau frontend partagé de ce laboratoire n’isole pas les applications les unes des autres.')
h1('3. Cartographie exploitable pour la sécurité')
p('La section 20 du sujet demande de relier chaque composant, son exposition, le risque, la protection attendue et la preuve de validation. Le tableau de référence détaillé est disponible dans docs/ARCHITECTURE_SECURITE.md.')
items=[
('Entrée 80/443','Interception, accès illicite','HTTPS certifié, exposition limitée','curl --cacert et tests réseau','P1'),
('Dashboard/API','Divulgation de topologie','Loopback au TP ; VPN/auth en prod','Accès local oui ; externe refusé','P1'),
('API Docker','Compromission potentielle hôte','Socket-proxy filtré (cible prod)','Inspection mounts/endpoints','P1'),
('App1/App1B','Panne, contournement','Aucun port hôte, healthcheck','inspect + test panne','P1'),
('App2/App3','Exposition involontaire','Opt-in, auth et segmentation','404/401/200, réseau','P1'),
('Configurations','Routage illégitime','Git/revue, secrets exclus','diff et contrôle secrets','P1'),
('Certificats et hash','Fuite de clés, expiration','0600, TLS validé, rotation','stat, openssl verify','P1'),
('Images et conteneurs','CVE, privilèges excessifs','Non-root, read_only, scanner','inspect, scan à exécuter','P1'),
('Logs','Données sensibles, manque de traces','Rétention et accès limités','Échantillons expurgés','P2'),
('Hôte et proxy','Point unique de panne','Redondance et restauration cible','Test panne multi-hôtes','P2'),
]
table(['Zone','Risque','Protection','Preuve','P.'],items,widths=[2.5,3.3,5.3,4.3,1.3])
h2('Cible de segmentation (proposition, non déployée)')
D.add_picture(str(ROOT/'docs/schema/cible-segmentation.png'),width=Cm(15.6))
caption('Cible : Traefik raccordé aux réseaux applicatifs distincts ; backend App1 redondé.')
p('Les deux instances App1 du laboratoire restent sur un seul hôte Docker : elles améliorent la répartition et peuvent tolérer l’arrêt d’un conteneur, mais ne résistent pas à une panne complète de cet hôte.')
h1('4. Vérification et statut réel')
p('Les tests statiques et runtime ont été réellement exécutés le 6 novembre 2026 sur Arch Linux avec Docker Engine 29.8.2, Compose 5.7.0 et Traefik 3.7.17.')
table(['Contrôle','Résultat établi','Limite'],[
('pytest local','45 tests statiques réussis','Complété par les tests runtime'),
('Bash/Compose/Python','bash -n, compose config, compileall : PASS','Validation locale'),
('Certificat et HTTPS','OpenSSL OK ; App1/App2 200 avec --cacert','CA locale de laboratoire'),
('BasicAuth App3','401 sans auth ; 200 avec auth valide','Secret exclu du rapport et de Git'),
('Routage HTTP','App1/App2 corrects ; hôte inconnu 404','Routes HTTP conservées pour le TP'),
('Load balancing','2 backends ; 30 requêtes A=15/B=15','Un seul hôte Docker'),
('Sécurité runtime','UID 101, aucun port/socket, read_only, caps','Socket Traefik direct encore sensible'),
('API/dashboard refus distant','NON TESTÉ','Requiert une seconde machine'),
('Scan d’images Trivy','NON TESTÉ','Outil absent'),
],widths=[4.5,7.0,5.2])
h2('Commandes de validation exécutées')
for cmd in [
'./scripts/bootstrap.sh',
'./scripts/smoke-test.sh',
'./scripts/check-unlabeled.sh',
'docker compose --profile evolution up -d app3',
'TP5_TEST_ADMIN=1 ./scripts/smoke-test.sh',
'docker compose --profile evolution --profile audit down',
]:
    x=D.add_paragraph(style='Normal');r=x.add_run(cmd);r.font.name='Consolas';r.font.size=Pt(8.7)
p('Le détail expurgé se trouve dans docs/preuves/RAPPORT_VALIDATION_FINALE.md. Aucun mot de passe, hash ou clé privée n’est inclus.')

h1('5. Questions de compréhension corrigées')
text=(ROOT/'QUESTIONS_REPONSES.md').read_text(encoding='utf-8')
qa=re.findall(r'^\*\*(\d+)\.\s+([^*]+)\*\*\n(.+?)(?=^\*\*\d+\.\s|\Z)',text,re.M|re.S)
assert len(qa)==21,len(qa)
for number,question,answer in qa:
    h3(f'{number}. {question.strip()}')
    p(answer.strip().replace('`',''))

h1('6. Limites, recommandations et sources')
for t in [
'Le test du dashboard/API depuis une seconde machine n’a pas été réalisé faute de seconde machine disponible.',
'Le port 8080 en mode api.insecure=true n’est protégé que par une liaison à loopback dans le laboratoire ; en production, supprimer ce mode et ajouter des protections d’administration.',
'Le socket Docker monté en lecture seule reste un point de confiance majeur ; préférer un proxy de socket avec endpoints limités.',
'Le certificat de laboratoire n’est pas une certification publique ; la confiance est donnée explicitement à curl par une CA locale contrôlée.',
'Le réseau frontend commun n’est pas une segmentation, et deux instances sur un hôte ne constituent pas une haute disponibilité multi-hôtes.',
'Les images ne sont pas verrouillées par digest et aucun scan Trivy n’a été exécuté dans ce kit ; ces mesures restent à réaliser pour un autre niveau d’assurance.',
]:bullet(t)
p('Références : sujet TP5 DevTech Solutions (26 pages, sections 18 à 20) ; documentation officielle Traefik 3.7 Docker provider ; Traefik File Provider/TLS ; Traefik BasicAuth ; documentation NGINX Unprivileged. Liens précis disponibles dans le README du projet.')
p('Rendu : sources Docker et YAML, scripts, HTML, tests statiques, correction des 5 exercices, réponses aux 21 questions, schémas SVG et rapport Word modifiable. Aucun secret généré n’est inclus dans l’archive.')

D.core_properties.title='TP5 - Reverse Proxy et Load Balancing avec Traefik'
D.core_properties.subject='DevTech Solutions - DevOps et sécurité'
D.core_properties.author='Équipe étudiante - à compléter'
D.save(OUT)
print(f'CREATED {OUT} | Questions: {len(qa)}')
