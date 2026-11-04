# Scénario de la vidéo de présentation — HelpDesk AI

Durée visée : **2 min 30** (marge jusqu'à 3 min). Format : capture d'écran 1920×1080
avec voix off, enregistrée avec OBS Studio. Les chiffres cités viennent de la table R2 de
[PROMPT_REDACTION_RAPPORT.md](PROMPT_REDACTION_RAPPORT.md).

## Préparation avant d'enregistrer

- Lancer la pile : `docker compose -f docker/docker-compose.yml up --build`, puis ouvrir
  http://localhost:8081. Le corpus local doit être présent, sinon aucune suggestion RAG
  ne s'affiche.
- **Faire un premier appel à Ollama avant l'enregistrement.** À froid, la réponse prend
  environ 95 s, contre environ 19 s une fois le modèle chargé.
- Préparer deux comptes de démonstration : un client et un administrateur.
- Créer à l'avance 3 ou 4 tickets fictifs pour que la file d'approbation et le tableau de
  bord ne soient pas vides. **Aucun nom réel ni donnée du corpus OTBS à l'écran.**
- Préparer le texte du ticket de démonstration (plan 3), par exemple :
  *« Outlook ne synchronise plus ma boîte mail depuis ce matin, message d'erreur à
  l'ouverture. »*
- Navigateur en plein écran, zoom à 110 %, notifications du système désactivées.

## Plan par plan

| # | Temps | À l'écran | Voix off |
|---|---|---|---|
| 1 | 0:00 – 0:12 | Carton titre : « HelpDesk AI », TEK-UP × OneTech Business Solutions, nom, année 2025–2026 | « HelpDesk AI : une plateforme qui classe les tickets informatiques et aide l'administrateur à les résoudre, développée chez OneTech Business Solutions. » |
| 2 | 0:12 – 0:30 | Diapositive problème : 1 800 tickets, 8 catégories, contrainte « aucune donnée ne sort » | « Le service support reçoit des tickets en français, répartis en huit catégories. Le tri est manuel, et une contrainte s'impose : aucune donnée ne doit quitter l'infrastructure. Tout tourne donc en local. » |
| 3 | 0:30 – 0:55 | Espace client : connexion, écran **Nouveau ticket**, saisie du texte préparé, envoi, puis **Mes tickets** avec le statut « En attente » | « Côté client, l'utilisateur décrit son problème en quelques lignes. Le ticket est créé avec le statut En attente, et il peut en suivre l'avancement. » |
| 4 | 0:55 – 1:10 | Espace admin : **File d'approbation**, clic sur le ticket, passage automatique en « Prise en Charge » | « Côté administrateur, un clic dans la file d'approbation prend le ticket en charge, l'assigne et prévient le client. » |
| 5 | 1:10 – 1:40 | Détail du ticket, étape **Revue** : catégorie prédite et confiance, puis la solution suggérée et sa source. Zoom sur ces deux blocs | « Le modèle propose une catégorie avec son niveau de confiance. Le moteur de recherche hybride retrouve les résolutions passées les plus proches et en tire une solution suggérée. Quand aucun cas similaire n'est assez proche, l'écran l'indique clairement : c'est un nouveau type de problème. » |
| 6 | 1:40 – 1:55 | Étape **Clôture** : correction éventuelle de la catégorie, réponse au client, popup « Solution appliquée », statut Résolu | « L'administrateur reste seul décideur : il confirme ou corrige, répond au client et enregistre la solution appliquée. Ses corrections alimentent ensuite l'amélioration du modèle. » |
| 7 | 1:55 – 2:10 | **Tableau de bord** puis **Monitoring** (rapports ML et RAG) | « Le tableau de bord suit l'activité, et le monitoring surveille la qualité des prédictions et des recherches. Un nouveau modèle ne remplace l'ancien qu'après avoir passé trois conditions, et l'ancien reste restaurable. » |
| 8 | 2:10 – 2:25 | Diapositive résultats (voir ci-dessous) | « Sur le protocole stratifié à huit catégories, CamemBERT combiné aux règles métier atteint un F1-macro de 0,83. Le moteur hybride servi obtient une précision à trois de 0,354, contre 0,292 pour le sémantique seul. » |
| 9 | 2:25 – 2:35 | Carton de fin : nom, encadrants, logos | « Merci de votre attention. » |

## Diapositive résultats (plan 8)

À garder sobre, trois lignes au maximum :

- CamemBERT + règles : **F1-macro 0,8343** (protocole stratifié, 8 catégories)
- TF-IDF + règles, pipeline servi par l'API : **F1-macro 0,5827** (même protocole)
- Recherche hybride : **P@3 = 0,354** contre 0,292 (sémantique) et 0,154 (lexical)

Si le jury pose la question, il faut pouvoir répondre : **l'API sert TF-IDF + règles,
pas CamemBERT**. Ne pas laisser croire le contraire à l'oral.

## À ne pas montrer ni dire

- Aucun extrait du corpus réel, aucun nom de demandeur, de consultant ou de filiale.
- Pas de « 0 % d'hallucination » : la fidélité de 1,0 est vraie par construction.
- Pas de F1 du pipeline DVC (0,5829) sans la mention « 5 catégories sur 8 ».
- Pas d'attente Ollama à l'écran : couper au montage si la réponse tarde.

## Montage

- Couper les temps de chargement et les saisies longues (accélérer ×2 la frappe).
- Ajouter un zoom ou un encadré sur la catégorie prédite et la solution suggérée (plan 5),
  qui sont le cœur de la démonstration.
- Sous-titres conseillés si la vidéo est diffusée sans son.
- Outils gratuits : OBS Studio pour l'enregistrement, Shotcut ou DaVinci Resolve pour le
  montage, Clipchamp (inclus dans Windows) pour un montage rapide.
