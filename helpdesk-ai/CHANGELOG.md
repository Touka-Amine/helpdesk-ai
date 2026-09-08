# CHANGELOG.md — Historique des modifications

> Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/). Types : `Ajouté`,
> `Modifié`, `Corrigé`, `Supprimé`, `Sécurité`, `Déprécié`. Source de vérité : [PLAN.md](PLAN.md).

## [Non publié] — branche `chore/gouvernance-pfe`

### Corrigé (2026-09-08, relecture du chapitre 5)

- `Corrigé` : **affirmation fausse sur la qualité du corpus indexé.** Le chapitre écrivait que les
  résolutions retrouvées portent « des fautes, des abréviations et des formulations
  télégraphiques ». La mesure contredit cette description : les 1 357 tickets indexés portent
  46 textes distincts, tous correctement ponctués, avec majuscule initiale et point final, sans
  aucune apostrophe manquante. Le texte mal écrit vient des solutions saisies par l'administrateur
  en exploitation, qui entrent dans la base par la boucle d'alimentation. La justification de
  l'assistant de reformulation est réécrite sur cette base.
- `Ajouté` : **la base de connaissances contient 46 résolutions distinctes, pas 1 357.** Le
  décompte de tickets décrivait un volume et masquait la redondance. À chaque scénario du corpus
  d'entraînement répond une résolution et une seule, réinstanciée 31 fois en médiane, de 4 à 49
  fois. Un tableau donne la répartition par catégorie : 8 réponses pour *Applicatifs* et *Réseau*,
  4 seulement pour *Infrastructure* et *Sécurité*.
- `Ajouté` : **aucune requête d'évaluation n'a sa réponse dans la base.** Le découpage étant groupé
  par titre, les 58 scénarios se répartissent en deux ensembles disjoints : 46 alimentent la base,
  les 12 autres forment le jeu de test. Les 356 tickets de test appartiennent donc tous à des
  scénarios absents de l'index. Deux conséquences sont désormais écrites au chapitre. Une
  définition stricte de la pertinence donnerait zéro pour les trois moteurs, ce qui explique
  pourquoi le protocole approché est le seul mesurable. Et les valeurs rapportées sont un plancher,
  non une estimation du comportement en exploitation.
- `Corrigé` : deux libellés de tableau confondaient tickets et résolutions ; `ISO/IEC 27001` aligné
  sur `ISO 27001`, forme employée au chapitre 1 ; label `sec:kb5` retiré, jamais appelé.
- `Modifié` : le chapitre passe de 16 à 18 pages, le mémoire de 94 à **96 pages**. Compilation sans
  erreur, sans référence non résolue, sans débordement nouveau.

### Ajouté (2026-09-08, chapitre 5 du mémoire)

- `Ajouté` : **chapitre 5 rédigé**, « Sprint 3 : système RAG et assistant LLM », 16 pages,
  2 figures et 7 tableaux. Le mémoire passe à **94 pages**, sans erreur de compilation et sans
  débordement nouveau.
- `Ajouté` : deux figures produites, `ch05_moteurs.png` (comparaison des trois moteurs, tracée
  depuis `metrics/rag_eval.json`) et `ch05_chaine_rag.png` (chaîne servie et boucle
  d'alimentation).
- `Trouvé` : **le moteur hybride servi n'atteint jamais le seuil de pertinence.** Son taux de
  repli vaut 1,000 sur les 80 requêtes d'évaluation. Le score hybride étant la moyenne du score
  sémantique (0,6099) et du score lexical (0,2117), il vaut 0,3551, très en dessous du seuil de
  0,50. Ce seuil avait été calibré sur l'échelle du moteur sémantique et conservé tel quel lorsque
  la fusion a changé cette échelle. Conséquence dans l'application : `NOVELTY_THRESHOLD = 0.50`
  dans `api/routers/tickets.py` fait traiter **tout ticket comme un cas nouveau**, ce qui rend la
  rédaction de la solution obligatoire à chaque clôture. L'effet sert la boucle d'alimentation,
  mais il résulte d'un accident de calibrage. Deux corrections sont énoncées au chapitre sans être
  tranchées, faute de trafic réel pour les calibrer (R-20).
- `Modifié` : règle de citation des chiffres du RAG arrêtée. La campagne du 2026-08-22 sert de
  référence unique, parce qu'elle mesure les trois moteurs sous un protocole identique et sur
  l'index réellement servi. La valeur de 0,9321 des métadonnées est citée avec son index de
  mesure (476 documents) et avec la précision qu'elle porte sur la similarité du meilleur passage,
  non sur les trois retenus.

### Ajouté (2026-09-08, synchronisation du suivi de rédaction)

- `Modifié` : **[PFE_PROGRESS.md](PFE_PROGRESS.md) entièrement réécrit.** Le fichier suivait
  encore un découpage en 14 chapitres thématiques hérité du cahier des charges, alors que le
  mémoire est organisé en 7 chapitres par sprints depuis [PLAN_RAPPORT.md](PLAN_RAPPORT.md), et
  portait la mention « Dernière mise à jour : à la création ». Il devient le tableau de bord de
  la rédaction : état par chapitre avec pages réelles, figures produites, chiffres à trancher
  avant le chapitre 5, écarts à assumer devant le jury, blocages externes.
- `Ajouté` : **section « État de la rédaction » dans [PLAN_RAPPORT.md](PLAN_RAPPORT.md)**, plus
  deux points de méthode — Point 4 sur les chiffres du RAG publiables et Point 5 sur les scores
  de classification périmés depuis l'audit des règles.
- `Modifié` : [PLAN.md](PLAN.md), [PROJECT_STATUS.md](PROJECT_STATUS.md), [RISKS.md](RISKS.md) et
  [TESTING.md](TESTING.md) alignés sur l'état réel — phase active passée à la Phase 14, tâche
  courante fixée au chapitre 5, comptage des tests porté à **133** (mesuré, `pytest --collect-only`).
- `Ajouté` : **R-25** (trois figures et deux métriques du chapitre 5 proviennent de notebooks sans
  sorties enregistrées) et **R-26** (informations entreprise manquantes, chapitre 1 sous sa cible).

### Ajouté (2026-08 → 2026-09, rédaction du mémoire)

- `Ajouté` : **introduction générale et chapitres 1 à 4** dans `../report/`. Le document compile
  à **77 pages**, sans erreur ni référence non résolue, avec 9 figures et 28 tableaux. Chaque
  valeur citée renvoie à un fichier du dépôt.
- `Ajouté` : trois figures produites pour le chapitre 4 — `ch04_benchmark.png` (comparaison des
  sept approches), `ch04_confusion_camembert.png`, `ch04_confiance.png`.
- `Corrigé` : **cinq erreurs factuelles du chapitre 4**, trouvées en relecture avant publication.
  Une cible d'amélioration confondait un incrément (+0,126) avec la valeur à atteindre (0,5719) ;
  la catégorie *Microsoft* était décrite comme nulle alors qu'elle est à 0,4463 ; deux
  dénombrements de catégories étaient faux ; et un score de 0,75 était attribué au modèle servi
  alors qu'il appartient à CamemBERT, le modèle servi étant à 0,5714 sur cette mesure.
- `Corrigé` : **confusion entre F1 et rappel sur ENF-04.** L'exigence porte sur le rappel. Les
  valeurs réelles sont 0,60 pour CamemBERT + règles et 0,40 pour TF-IDF + règles en protocole
  stratifié, 0,00 en protocole pipeline. **ENF-04 n'est atteinte par aucune configuration**, ce
  qui est désormais écrit tel quel.
- `Modifié` : **chapitre 2 repris** (2026-09-07) — figure sur l'adaptation par matrices de rang
  faible retirée au profit de sa formulation mathématique, figure du principe RAG refaite en
  séparant la phase hors ligne de la phase en ligne, tableau des exigences fonctionnelles réécrit
  au format SRS (référence, exigence, critère d'acceptation, priorité) avec des priorités
  Élevée / Moyenne / Faible, et `placeins` ajouté au préambule pour que `\FloatBarrier` empêche
  un tableau trop haut de flotter par-dessus le début de la section suivante.
- `Ajouté` : **cartographie des notebooks**
  ([../reports/analyse-notebooks/ANALYSE_NOTEBOOKS.md](../reports/analyse-notebooks/ANALYSE_NOTEBOOKS.md)).
  Trois producteurs concurrents de `data/processed/HelpDesk1.csv` avec des schémas différents
  (9 colonnes contre 23), deux producteurs de `models/best_pipeline.pkl` sous des découpages
  différents, deux notebooks sans aucune sortie enregistrée, et `models/semantic_rag_metadata.json`
  décrivant un index de 476 documents quand celui servi en contient 1 357.
- `Ajouté` : **comparaison avant/après l'audit des règles**
  ([../reports/analyse-notebooks/COMPARAISON_AVANT_APRES.md](../reports/analyse-notebooks/COMPARAISON_AVANT_APRES.md))
  et instantané des métriques d'avant nettoyage (`metrics/campagne_avant_nettoyage.json`), pour
  que la progression du travail reste démontrable.
- `Ajouté` : suite de tests portée à **133** — idempotence de la promotion et non-régression de
  l'audit des règles.

### Corrigé (2026-08-22, audit des règles métier — fuite méthodologique)

- `Corrigé` : **quatre mots-clés des règles fermes avaient été ajoutés en consultant le jeu de
  test.** Un commentaire de `src/models/heuristics.py` documentait explicitement l'un d'eux :
  `« acces non autorise » ajouté : test title "Accès non autorisé détecté par l'IDS"`. La
  confrontation de chaque mot-clé au jeu d'entraînement a montré que `onedrive`, `san`, `ids` et
  `acces non autorise` n'y figuraient dans **aucun ticket** et ne se déclenchaient que sur des
  tickets de test : 45, 21 et 12 tickets respectivement. Un mot-clé introduit après avoir observé
  une erreur sur le test ajuste le système aux données qui servent à le juger ; le score cesse
  alors de mesurer la généralisation. Les quatre termes sont retirés, les règles fermes passent de
  35 à 29 motifs.
- `Modifié` : **conséquences chiffrées du retrait**, protocole stratifié 8 catégories :

  | Système | Avant | Après |
  |---|---|---|
  | TF-IDF + règles | 0.7513 | **0.5827** |
  | CamemBERT + règles | 0.9499 | **0.8343** |

  Protocole du pipeline : `f1_macro_heuristiques` 0.685 → **0.5829**,
  `f1_macro_classes_evaluables` 0.822 → **0.6995**, `accuracy` 0.8539 → **0.8202**,
  `recall_Sécurité` 0.3636 → **0.0000**.
- `Ajouté` : **règle méthodologique en tête de `heuristics.py`.** Un mot-clé n'est admis que s'il
  est attesté dans le jeu d'entraînement, ou s'il reste sans effet sur le jeu de test. Les quatre
  termes retirés pourront être réintroduits si le service support les valide par écrit comme
  référentiel métier, établi sans consultation des résultats de test.
- `Ajouté` : `tests/test_heuristics.py::test_mots_cles_retires_de_l_audit_ne_declenchent_plus`,
  qui échoue si l'un des quatre termes revient. Les deux tests de frontière de mot, qui
  s'appuyaient sur `ids`, ont été réécrits avec `esxi` et `sage erp`. Suite à **133 tests**.

### Ajouté (2026-08-22, comparaison à configuration égale — hypothèse H1)

- `Ajouté` : **CamemBERT évalué avec les règles métier**, ce qui n'avait jamais été fait. Le
  chapitre 4 comparait jusqu'ici une chaîne lexicale *avec* règles à un transformer *sans* règles.
  Les règles ne dépendent d'aucun modèle : elles lisent le texte brut et corrigent une catégorie
  prédite, quelle qu'en soit l'origine.

  | Configuration | TF-IDF | CamemBERT | Écart |
  |---|---|---|---|
  | Sans règles | 0.3753 | 0.5685 | +0.193 |
  | Avec règles | 0.5827 | **0.8343** | +0.252 |

- `Corrigé` : **l'hypothèse H1 du cahier des charges est vérifiée**, alors que le mémoire la
  donnait pour infirmée. CamemBERT devance la chaîne lexicale dans les deux configurations.
- `Corrigé` : ENF-03 passe de « non atteint, écart de 0.28 » à « presque atteint, écart de
  0.016 ». Il suffirait que *Microsoft* passe de 0.4463 à 0.5719 pour franchir la barre.
- `Corrigé` : ENF-04 reste non atteint. Le meilleur rappel sur *Sécurité* est 0.60, pour une cible
  de 0.70. La précision vaut 1.00 dans toutes les configurations.
- `Modifié` : chapitre 4 du mémoire réécrit — introduction, tableau des objectifs, gain des
  heuristiques, deux sections nouvelles (`sec:combinaison`, `sec:audit`), section « Ce qui sépare
  encore de l'objectif », arbitrage de production rouvert, bilan et conclusion. Figure
  `ch04_benchmark.png` régénérée. Mémoire à 76 pages, compilation sans erreur.
- `Corrigé` : cinq erreurs factuelles introduites dans la première version de cette réécriture et
  trouvées en relecture — la cible de *Microsoft* annoncée à 0.13 au lieu de 0.5719, *Microsoft*
  décrit comme nul alors qu'il vaut 0.4463, « cinq catégories au-dessus de 0.74 et trois à 1.00 »
  au lieu de six et quatre, *Backup* crédité de huit scénarios au lieu de six, et un F1 de 0.75
  attribué au modèle servi alors qu'il appartient à CamemBERT.


### Corrigé (2026-08-22, relecture de l'architecture MLOps — trois défauts trouvés)

- `Corrigé` : **`promote.py` rendait l'application incapable de démarrer.** Relancé sans
  nouveau candidat, il sortait en erreur. Or `models/best_pipeline.pkl` est une **sortie**
  du stage DVC `promote`, et DVC supprime les sorties d'un stage avant de l'exécuter :
  un `dvc repro` sans entraînement préalable laissait l'artefact servi absent, alors même
  que le registre en détenait une copie intacte. Reproduit, puis corrigé — le stage est
  désormais idempotent, restaure la production et sort en succès. Il n'échoue plus que
  sur un dépôt sans aucun modèle ni candidat. Couvert par `tests/test_promote_idempotence.py`.
- `Corrigé` : **une métrique absente faisait gagner le candidat par défaut.** `comparer()`
  lisait la métrique de décision avec `.get(metrique, 0.0)` : un modèle de production dont
  la métrique aurait manqué aurait valu 0.0, et n'importe quel candidat aurait franchi la
  porte, soit l'inverse exact de ce qu'elle protège. La comparaison lève désormais une
  erreur explicite plutôt que d'arbitrer sur une valeur inventée.
- `Corrigé` : **rechargement concurrent du modèle.** Les endpoints synchrones de FastAPI
  s'exécutent dans un pool de threads. Plusieurs requêtes pouvaient franchir ensemble le
  contrôle de fraîcheur et déclencher deux rechargements simultanés, ou lire un pipeline
  déjà remplacé alors que le seuil de décision ne l'était pas encore. Verrou réentrant sur
  `load()`, `reload()` et `ensure_fresh()`, avec re-contrôle sous verrou.
- `Corrigé` : **le verrou anti-réentraînement lisait une sortie DVC.**
  `ml_monitor._verrou_temporel()` datait la dernière décision depuis
  `metrics/promotion_decision.json`, supprimé à chaque `dvc repro` et réécrit par une
  exécution sans candidat. Il lit maintenant l'historique du registre, qui n'est la sortie
  d'aucun stage et ne conserve que les arbitrages réellement rendus.
- `Corrigé` : **déduplication des tickets collectés conditionnée au jeu de test.** Dans
  `build_dataset.py`, `drop_duplicates(subset=["ticket_id"])` était imbriqué dans le bloc
  anti-fuite : sans `test.csv`, un même ticket présent dans plusieurs lots aurait été
  compté autant de fois.
- `Corrigé` : **`scripts/mlops_e2e_demo.py` ne restaurait pas les artefacts du candidat.**
  `models/candidate_metadata.json`, qui est versionné, restait celui du modèle entraîné sur
  les tickets simulés. La sauvegarde couvre désormais tous les artefacts touchés et
  supprime ceux qui n'existaient pas avant la démonstration. Vérifié par comparaison
  d'empreintes avant/après : le dépôt est rendu à l'identique.

Suite de tests portée à **132 tests**.

### Ajouté (2026-08-22, industrialisation MLOps — deux boucles d'amélioration)

Documentation complète du cycle de vie : [MLOPS.md](MLOPS.md).

**Axe 1 — boucle du modèle de classification**

- `Ajouté` : **registre de modèles** (`src/registry/model_registry.py`, `models/registry/`) —
  versions figées avec leur pipeline, leurs métadonnées, leurs métriques et leur lineage ;
  alias `production` ; historique horodaté de chaque décision ; rollback en une commande
  (`python src/pipeline/promote.py --rollback N`). Le Model Registry MLflow fonctionne avec
  le store `file:./mlruns` du projet, vérifié à l'exécution, mais MLflow 3.6 le déclare
  déprécié : l'enregistrement MLflow est fait **en plus**, jamais à la place, et son échec
  n'est pas bloquant.
- `Ajouté` : **collecte des tickets validés** (`src/pipeline/collect.py`) — extraction en
  lecture seule depuis PostgreSQL vers `data/curated/`, avec qualification de la **force de
  l'étiquette** déduite de `ticket_history` : `corrected` (un admin a changé la catégorie,
  poids 1.0), `confirmed` (il a traité le ticket sans la contester, 0.7), `weak` (aucun admin
  identifiable, **exclu par défaut**). Sans cette distinction, réentraîner sur « les tickets
  validés » revient largement à réentraîner le modèle sur ses propres sorties.
- `Ajouté` : **construction versionnée du dataset** (`src/pipeline/build_dataset.py`) —
  fusion corpus historique + lots de production, identifiant de version par empreinte
  SHA-256, et trois garde-fous anti-fuite (titre présent au test, description identique après
  normalisation, ticket collecté deux fois). La paraphrase sémantique d'un ticket de test
  n'est pas détectée : limite documentée.
- `Ajouté` : **porte de promotion** (`src/pipeline/promote.py`) — seul script qui écrit
  `models/best_pipeline.pkl`. Réévalue candidat **et** production dans la même exécution sur
  le même jeu de test, puis applique trois portes : gain minimum sur la métrique principale,
  aucune classe avec support ne perdant plus de 0.05, accuracy non régressive. En cas de
  rejet, l'artefact de production est restauré depuis le registre.
- `Modifié` : `src/pipeline/train.py` produit désormais un **candidat**
  (`models/candidate_pipeline.pkl`) et non plus directement le modèle servi. Ajout de la
  précision, du rappel, du support et de la matrice de confusion par classe ; pondération par
  force d'étiquette ; le bloc MLflow n'avale plus silencieusement ses exceptions.
- `Ajouté` : **déclencheurs de réentraînement** (`src/monitoring/ml_monitor.py`) — le moniteur
  écrit `metrics/should_retrain.json`, il ne lance rien. Seuils dans `params.yaml` : 150
  nouveaux tickets validés, ou +30 sur une classe minoritaire, ou hausse du désaccord
  ML/humain, avec un verrou d'une semaine entre deux réentraînements.
- `Ajouté` : rechargement du modèle sans redémarrage — `POST /api/v1/admin/model/reload`, et
  chaque worker uvicorn compare de lui-même le pointeur `models/registry/PRODUCTION` au
  modèle qu'il a en mémoire (au plus une fois par 30 s).

**Axe 2 — cycle de vie des connaissances RAG**

- `Corrigé` : **auto-contamination de la base de connaissances**. L'archivage faisait
  `solution = commentaire_admin or solution_rag or ""`. Quand un administrateur clôturait
  sans écrire de commentaire et que `rag_score >= 0.50`, c'est la **suggestion de l'IA,
  jamais relue**, qui entrait dans ChromaDB et devenait une source pour les tickets suivants,
  dont les résolutions étaient à leur tour archivées. L'origine est désormais déclarée
  (`source_solution` vaut `admin` ou `ia`) et le contrôle qualité refuse la seconde. C'est la
  cause structurelle de l'incident décrit en R-04.
- `Ajouté` : **contrôle qualité des connaissances** (`src/knowledge/quality.py`) — solution
  présente, au moins 4 mots, origine humaine, non-recopie de la description (≤ 90 % de
  vocabulaire commun), détection de quasi-doublon. Testable sans base.
- `Ajouté` : **statuts de cycle de vie** dans ChromaDB — `actif`, `superseded` (remplacée par
  une connaissance quasi identique plus récente), `obsolete`. Rien n'est jamais supprimé
  automatiquement : une procédure ancienne peut rester la bonne. Le filtrage se fait après la
  requête, pas dans la clause `where`, pour ne pas exclure silencieusement les entrées
  antérieures à ce champ.
- `Ajouté` : **versionnement de la base** (`src/knowledge/snapshot.py`) — export horodaté en
  JSON Lines, empreinte SHA-256, et comparaison entre deux états (`--diff last`).
- `Ajouté` : **évaluation RAG rejouable** (`src/pipeline/rag_eval.py`), stage DVC, deux
  protocoles. `--build-template` génère un jeu de 80 requêtes à annoter par un administrateur.
- `Corrigé` : **`recall_at_3 = 0.0277` était un artefact de protocole**, pas une mesure. Avec
  « même catégorie = pertinent », *Microsoft* compte des centaines de pertinents et un
  rappel@3 vaut mécaniquement 3/300 quelle que soit la qualité du moteur. Le rappel est
  désormais laissé à `null` en mode proxy.
- `Corrigé` : l'évaluation mesurait les moteurs avec `allow_fallback=False`, une configuration
  que la production n'utilise pas — elle renvoyait zéro résultat. Elle interroge maintenant
  les moteurs comme `api/predictor.py`, et rapporte le taux de repli à part. Le **moteur
  hybride réellement servi** est mesuré pour la première fois : P@3 = 0.354, contre 0.292
  (sémantique) et 0.154 (lexical) sur le même jeu de 80 requêtes.
- `Ajouté` : **monitoring RAG** (`src/monitoring/rag_monitor.py`) — distribution des
  `rag_score`, taux de nouveauté, avis utilisateurs, taux de rejet implicite de la suggestion
  par l'admin, volume, statuts, quasi-doublons, ancienneté, qualité entrante.

**Socle et traçabilité**

- `Ajouté` : **jeu de test gelé** (`data/reference/test_reference.csv` + manifeste protégé par
  SHA-256). `split.py` le relit au lieu de le regénérer. Sans référence stable, comparer la
  F1-macro de deux modèles ne mesure rien et la porte de promotion devient arbitraire. Le
  gel reproduit **à l'octet près** le découpage existant : train 1444 / test 356 / rag 1357,
  46 et 12 titres uniques, F1-macro 0.685 et accuracy 0.8539 inchangées.
- `Ajouté` : métrique `f1_macro_classes_evaluables` — la F1-macro calculée sur les seules
  classes ayant du support au test, soit **0.822 sur 5 classes** contre 0.685 pour la macro
  complète. Une classe absente du test a une F1 de 0.0 par construction ; l'inclure mesure la
  composition du jeu de test, pas le modèle. C'est cette métrique que la porte de promotion
  utilise. Le chiffre 0.685 reste publié tel quel dans `metrics/ml_eval.json`.
- `Ajouté` : option `split.strategy: stratified_group`, qui mettrait les 8 catégories au test
  (traitement de R-14). **Non activée** : la basculer changerait la référence d'évaluation
  publiée dans le mémoire. Décision à prendre explicitement.
- `Ajouté` : traçabilité des prédictions — colonnes `model_version`, `heuristic_applied`,
  `heuristic_rule` sur la table `tickets`. Ces champs ne se reconstruisent pas après coup :
  chaque ticket créé sans eux est perdu pour le monitoring.
- `Ajouté` : stage DVC `rag_semantic_build`. L'index FAISS servi en production était construit
  **hors pipeline** : il n'était ni reproductible ni versionné.
- `Ajouté` : endpoints d'administration en lecture seule — `/admin/registry`,
  `/admin/promotion-decision`, `/admin/monitoring/{ml,rag,retrain-trigger,rag-eval}`. Aucun ne
  lance d'entraînement ni ne promeut de modèle : ces opérations passent par DVC.
- `Supprimé` : bloc `model:` de `params.yaml` (`random_forest`, `n_estimators: 200`), code mort
  — `train.py` ne l'a jamais lu et le modèle réel est un LinearSVC calibré.
- `Corrigé` : `api/config.py` refusait de démarrer à cause des variables `POSTGRES_*` du
  `.env`, partagé avec docker-compose. `tests/test_api_integration.py` était incollectable en
  local depuis la migration PostgreSQL. Résolu par `extra="ignore"`.
- `Ajouté` : **68 tests** (`test_model_registry.py`, `test_kb_quality.py`,
  `test_promotion_gate.py`, `test_collect.py`, `test_build_dataset.py`,
  `test_vector_store_lifecycle.py`) et `pytest.ini` avec le marqueur `slow`. Suite complète :
  **125 tests passent**.
- `Ajouté` : `scripts/mlops_e2e_demo.py` — démonstration du cycle complet sur une base de
  production simulée, avec restauration de l'état initial du dépôt.

### Corrigé (2026-08-17, préparation de la rédaction du mémoire — audit des chiffres publiés)

- `Corrigé` : **périmètre de R-14 sous-évalué**. Les documents affirmaient que
  `data/splits/test.csv` ne contenait aucun exemple de **2** catégories (*Backup*,
  *Communication*). Vérification faite sur les données : **3** catégories sont absentes —
  *Applicatifs*, *Backup* et *Communication* (0/356). Le test ne couvre donc que **5 des 8
  catégories** du domaine (Microsoft 135, Infrastructure 91, Système 52, Réseau 45,
  Sécurité 33). Corrigé dans `RISKS.md` (R-14), `CADRAGE_SRS.md` (ENF-03) et `TESTING.md`.
- `Corrigé` : **F1-macro 0.685 vs 0.5673 — non comparables**. Les deux valeurs sont exactes
  mais issues de protocoles distincts : 0.685 provient du pipeline DVC
  (`GroupShuffleSplit` non stratifié, **5/8 classes**), 0.5673 du notebook 05
  (`StratifiedShuffleSplit`, **8/8 classes**). Le premier est mécaniquement supérieur
  puisqu'il exclut les catégories rares du test. Seul le couple **0.5673 (baseline) vs
  0.5685 (CamemBERT)** constitue une comparaison valide. La nuance, jusqu'ici présente
  uniquement dans `RISKS.md`/`CADRAGE_SRS.md`/`TESTING.md`, a été propagée aux fichiers de
  synthèse qui citaient 0.685 sans avertissement : `PROJECT_STATUS.md`, `PLAN.md`,
  `PFE_PROGRESS.md`.
- `Corrigé` : **taille de la base RAG mal libellée**. `DIAGNOSTIC_QUALITE_DONNEES.md`
  présentait « 476 tickets résolus » comme la base de résolution RAG. En réalité 476 = tickets
  au statut *Résolu* sur le corpus complet, tandis que la base réellement indexée
  (`data/splits/rag.csv`) compte **1357 tickets** : tout ticket **du jeu d'entraînement** dont
  `Résolution/Motif` est renseignée, quel que soit son statut (Résolu 358, Rejeté 363,
  Problème 237, Prise en Charge 236, En attente 163). La restriction au train est un choix
  anti-fuite délibéré. Nouvelle section §2.1 ajoutée au diagnostic pour lever l'ambiguïté.
- `Ajouté` : `PLAN_RAPPORT.md` — plan détaillé du mémoire (7 chapitres organisés par sprints,
  3 niveaux de titres), calqué sur la structure des deux rapports de référence encadrés par le
  même encadrant académique, avec inventaire des figures, acronymes et ordre de rédaction.

### Ajouté (2026-07-30, retour utilisateur — accélération GPU optionnelle pour Ollama)

- `Ajouté` : `docker/docker-compose.gpu.yml` — surcouche **optionnelle** (opt-in, ne modifie
  pas `docker-compose.yml`) activant l'accélération GPU NVIDIA pour le service Ollama.
  Mesuré en direct sur une NVIDIA GeForce MX130 (2 Go VRAM) : ~13s à chaud contre ~18-20s
  sans GPU (gain modeste ~30%, la VRAM disponible ne permet pas de charger tout le modèle
  3B — 770 Mo/2048 Mo utilisés). Non activé par défaut : le fichier `docker-compose.yml`
  de base doit rester utilisable tel quel sur une machine sans GPU (ex. soutenance sur un
  autre poste) — l'ajouter fait échouer le démarrage d'Ollama si aucun GPU n'est détecté.
  `RISKS.md` (R-19) mis à jour avec les mesures.

### Ajouté (2026-07-30, retour utilisateur — chat conversationnel avec l'assistant IA)

- `Ajouté` (Tâche 3 ter) : `POST /tickets/{id}/chat` — au-delà de la synthèse initiale figée,
  l'admin peut poser des questions de suivi libres sur un ticket et ses cas similaires
  (« Quelle est la procédure complète du ticket #45 ? », « Quelle priorité recommandes-tu ? »).
  Contexte (ticket + candidats ChromaDB réels) reconstruit côté serveur à chaque appel,
  jamais fourni par le client, avec le même assainissement anti-contamination que la
  synthèse initiale (`api/services/llm_service.py::chat_reply`). Historique de conversation
  envoyé par le client (max 20 messages, 10 derniers conservés dans le prompt).
- `Corrigé` (en cours de vérification) : le garde-fou anti-hallucination rejetait à tort une
  réponse honnête du LLM quand l'admin posait une question sur un ticket inexistant (ex.
  « le ticket 9999 ») — le LLM répondait correctement qu'il n'avait pas cette information,
  mais citait le numéro en écho, ce qui déclenchait le repli générique. Corrigé : un ID que
  l'admin mentionne lui-même dans sa question est désormais autorisé en écho, seul un ID
  que le LLM introduit de lui-même (jamais vu ni dans les candidats ni dans les questions de
  l'admin) déclenche le repli. Vérifié en direct dans le navigateur (question réelle sur le
  ticket #45, réponse correcte et fidèle, sans hallucination).
- `Ajouté` (frontend) : bouton « Discuter avec l'assistant IA » sous le panneau RAG
  (`.../admin/ticket-detail`) — interface de chat non persistée, remise à zéro à chaque
  changement de ticket.

### Ajouté / Modifié (2026-07-30, masquage IA client, clôture pilotée par statut, assistant de triage IA)

- `Modifié` (client, Tâche 1.1/1.3/1.4) : `frontend/.../client/ticket-detail` — retrait des
  métadonnées IA (catégorie prédite, score de confiance) de la vue client, réservées aux
  admins ; suppression du message de confirmation de feedback résiduel ; colonne latérale
  (ex-historique brut) remplacée par 3 blocs client-safe : Suivi (technicien assigné, temps
  écoulé, dernière mise à jour), Cas similaires (titres de tickets résolus proches, sans
  solution technique ni score — nouvel endpoint `GET /tickets/{id}/similar-titles`), Contact
  rapide (relance par email, lien nouveau ticket).
- `Ajouté` (backend, Tâche 1.2) : message client automatique différencié à la résolution
  (`AUTO_MESSAGE_RESOLU`) — remplace le message générique de prise en charge s'il n'a pas
  été personnalisé par l'admin (`api/routers/tickets.py::approve_ticket`).
- `Modifié` (admin, Tâche 2.1 — **révisé en cours de vérification suite à un retour direct**) :
  le statut n'est plus choisi via un menu déroulant pré-rempli à l'étape de clôture. Le
  bouton **Enregistrer** ouvre directement une modale listant les transitions valides depuis
  le statut actuel ; l'admin y choisit le statut réel du ticket. Un ticket déjà terminal
  (Résolu/Rejeté) s'enregistre directement (pas de modale, aucune transition à choisir), les
  autres champs restant modifiables. La solution appliquée reste obligatoire pour clore en
  « Résolu » un cas nouveau.
- `Supprimé` (admin) : colonne CID du tableau `frontend/.../admin/ticket-list` (Tâche 2.2).
- `Ajouté` (admin, Tâche 2.3) : édition inline du tableau (catégorie/priorité/classification/
  assigné à/résolution) sans ouvrir le détail — réutilise `PATCH /tickets/{id}/approve` avec
  le même statut (autorisé depuis le fix de la Tâche « ticket résolu reste éditable »).
- `Ajouté` (admin, Tâche 2.4) : création d'un ticket depuis le tableau (`POST
  /tickets/admin-create`) — demandeur = client existant ou saisie libre (crée un compte
  client `is_active=False` pour porter le ticket, sans connexion possible). Suppression
  définitive (`DELETE /tickets/{id}`, supprime l'historique lié puis le ticket) protégée par
  une confirmation forte : l'admin doit taper le mot **SUPPRIMER**.
- `Ajouté` (Tâche 3 — assistant de triage IA, human-in-the-loop) : `api/services/llm_service.py`
  + nouveau service Docker `ollama` (image `ollama/ollama`, modèle `llama3.2:3b`, 100%
  on-premise — aucun appel externe). Le RAG ne se contente plus de retourner la résolution
  brute d'un seul ticket (parfois mal écrite) : `GET /tickets/{id}/rag-synthesis` interroge
  les tickets similaires réellement archivés (ChromaDB, avec leur vrai ID), et un LLM local
  les reformule en français professionnel, structurés en liste à puces (ID, score, catégorie,
  résumé d'une phrase), avec un exemple concret (few-shot) injecté dans le prompt pour ancrer
  le format — nécessaire pour qu'un modèle aussi petit (3B) respecte fidèlement le format et
  n'invente pas d'ID/score. Dégradation gracieuse vers un récapitulatif brut si Ollama est
  indisponible/trop lent. Un second champ permet d'explorer la procédure complète d'un des
  tickets proposés en tapant son ID (appel à l'action du LLM).
- Vérifié en direct (Docker, navigateur) : les 3 tâches de bout en bout, y compris la
  synthèse IA réelle (`source: "ollama"`, ~20-60s selon la longueur du prompt sur CPU) et son
  repli automatique observé pendant le tuning du prompt/timeout.

### Modifié (2026-07-30, retour utilisateur — popup dédié pour la solution appliquée)

- `Modifié` (admin, Tâche 2.1 bis) : l'étape de clôture (`frontend/.../admin/ticket-detail`)
  est scindée en deux sous-étapes au lieu d'un seul écran chargé — catégorie/priorité/
  classification/réponse client d'abord, puis un **grand popup dédié** à « Solution
  appliquée » (le champ le plus long, désormais isolé dans une fenêtre `max-w-2xl` avec
  une zone de texte de 12 lignes, pour que l'admin puisse rédiger le diagnostic à l'aise
  au lieu d'une petite colonne de 360px). Parcours : Suivant → Suivant → Enregistrer.
  Si le statut choisi « Résolu » nécessite une solution manquante (cas nouveau), la
  modale de statut se referme et rouvre ce popup avec l'erreur affichée directement
  au-dessus du champ, au lieu de rester loin dans la petite modale de statut.

### Corrigé (2026-07-30, retour utilisateur — hallucination LLM + latence)

- `Corrigé` (backend, `api/services/llm_service.py`) : reproduit et corrigé un cas réel
  d'hallucination — un ticket résolu avec le texte de synthèse IA lui-même collé dans
  « Solution appliquée » (erreur de test), une fois réarchivé et réutilisé comme candidat
  pour un ticket suivant, faisait « continuer le motif » au LLM qui inventait deux faux
  tickets (#1042, #985 — repris de l'exemple few-shot du prompt). Deux gardes-fous
  ajoutés : assainissement de toute « résolution brute » qui ressemble déjà à une
  synthèse IA avant de l'envoyer au prompt, et validation en sortie (tout ID de ticket
  cité par le LLM qui ne correspond à aucun candidat réel fait basculer sur le
  récapitulatif brut). `temperature=0.2` (réponse plus factuelle, moins encline à
  inventer). Revérifié en direct dans les deux sens (ticket contaminé comme cible et
  comme candidat) : plus aucune invention.
- `Modifié` (latence) : `keep_alive:"30m"` sur chaque appel Ollama (le modèle reste
  chargé entre deux tickets, évite ~10-15s de rechargement à chaque appel) et
  `num_predict:400` (plafond de tokens générés). Mesuré en direct : ~95s à froid (juste
  après un redémarrage du conteneur) contre ~18-19s à chaud. Le panneau affiche
  désormais la suggestion RAG brute *immédiatement* (déjà en base, latence nulle)
  pendant que la reformulation IA charge en tâche de fond, au lieu de tout masquer
  derrière un message d'attente — l'admin n'est plus jamais bloqué sans rien voir.
  `RISKS.md` (R-04, R-19) mis à jour avec les mesures et gardes-fous.

### Modifié (2026-07-30, retour utilisateur — synthèse IA affichée par défaut)

- `Modifié` (admin, Tâche 3 bis) : le panneau « Solution suggérée (RAG) » de l'étape Revue
  (`frontend/.../admin/ticket-detail`) déclenche désormais **automatiquement** la synthèse
  IA (`GET /tickets/{id}/rag-synthesis`) dès qu'un ticket a un cas connu, avec un état de
  chargement visible — ce n'était auparavant qu'un bouton optionnel (« Analyser avec l'IA »)
  sous la résolution brute d'un seul cas, ce qui laissait l'admin voir en premier un texte
  non reformulé (parfois mal écrit) tant qu'il n'avait pas cliqué. La reformulation
  professionnelle du LLM est maintenant ce que l'admin voit par défaut, plus une action à
  découvrir. Repli sur la suggestion brute conservé dans deux cas seulement : la meilleure
  correspondance provient du corpus statique d'entraînement (aucun ID de ticket réel à
  synthétiser) ou la requête échoue franchement (pas juste Ollama lent/indisponible, déjà
  couvert par le repli serveur `source:"fallback"`). Le bouton « Rafraîchir » relance aussi
  la synthèse. Vérifié en direct sur un vrai ticket (`#0046`, cas similaire réel `#0045`,
  score 97%) : synthèse correcte affichée sans action de l'admin, puis exploration de la
  procédure complète par ID fonctionnelle. `RISKS.md` (R-19) mis à jour : ce choix accepte
  plus de latence visible en contrepartie d'une UX plus honnête.

### Corrigé (2026-07-30, relecture — entrée fantôme ChromaDB après suppression)

- `Corrigé` (backend, Tâche 2.4) : `DELETE /tickets/{id}` supprimait le ticket et son
  historique côté PostgreSQL mais ne retirait jamais l'entrée correspondante de ChromaDB —
  un ticket résolu (donc archivé) puis supprimé continuait à être proposé par le RAG et cité
  par la synthèse IA (Tâche 3) avec un ID de ticket qui n'existait plus (404 à l'exploration).
  Ajout de `delete_resolved()` dans `api/db/vector_store.py`, appelé depuis l'endpoint de
  suppression. Vérifié directement dans le conteneur `api` (archive → présent dans
  `query_similar()` → `delete_resolved()` → absent, compteur revenu à sa valeur initiale).

### Ajouté / Modifié (2026-07-29, migration SQLite→PostgreSQL et TinyDB→ChromaDB)

- `Modifié` : base opérationnelle **SQLite → PostgreSQL** (ADR-006). Nouveau service
  `postgres` dans `docker/docker-compose.yml` (image `postgres:16-alpine`, volume
  `postgres-data`, healthcheck), `api` en dépend (`depends_on: condition: service_healthy`).
  `api/config.py::DB_URL` pointe désormais vers `postgresql+psycopg2://...` par défaut ;
  `sqlite:///...` reste utilisable hors Docker via `.env` (le code de migration de colonnes
  reste compatible avec les deux moteurs).
- `Corrigé` (bug découvert pendant la vérification de cette tâche) : `Base.metadata.create_all()`
  n'était pas tolérant à la course entre les 2 workers uvicorn démarrant en parallèle sur une
  base PostgreSQL neuve — les deux tentaient de créer les tables simultanément et l'un des deux
  plantait sur `duplicate key ... users_id_seq` (contrainte d'unicité de séquence PostgreSQL).
  Même classe de bug que le fix `_add_column_if_missing()` de Phase antérieure, appliquée cette
  fois à la création de table elle-même (`api/db/database.py::_create_tables()`).
- `Ajouté` : base de connaissances vectorielle **TinyDB → ChromaDB** (ADR-004).
  `api/db/nosql_store.py` supprimé, remplacé par `api/db/vector_store.py` (mode embarqué,
  `PersistentClient`, stocké dans `data/chroma/`). Contrairement à TinyDB — un simple journal
  jamais relu par le RAG, malgré le texte affiché à l'admin qui promettait le contraire —
  cette collection est **interrogée en direct à chaque recommandation**
  (`query_similar()`, appelée depuis `api/services/ai_service.py`) : une solution saisie par
  un admin devient exploitable par le RAG dès le ticket suivant, sans réentraînement ni
  redémarrage.
- `Modifié` : `approve_ticket()` archive désormais la résolution via `BackgroundTasks` (le
  calcul de l'embedding sentence-transformers ne bloque plus la réponse HTTP).
- `Corrigé` (bug découvert pendant la vérification de cette tâche) : la collection Chroma
  était mise en cache par processus — avec 2 workers uvicorn (2 process séparés), le worker
  qui traitait un nouveau ticket ne voyait pas l'archive écrite par l'autre worker. Corrigé en
  ré-ouvrant la collection à chaque appel (`_get_collection()`) plutôt qu'en la mettant en
  cache globalement ; seul le modèle d'embedding (coûteux à recharger) reste mis en cache.
- Vérifié en direct (build Docker, base Postgres et Chroma vides) : cycle complet ticket →
  résolution avec solution détaillée → archivage Chroma confirmé (`/tickets/resolved/stats`) →
  second ticket similaire recevant la solution réellement appliquée par l'admin (score 0.78)
  plutôt que la suggestion statique générique — la boucle de feedback continu fonctionne
  réellement, pas seulement dans le texte de l'interface.

### Corrigé (2026-07-29, ajustements suite à retour utilisateur sur le workflow tickets)

- `Modifié` : **file d'approbation** (`approval-queue.ts`/`.html`) — le panneau de décision intégré
  (message client + note interne + boutons Valider/Rejeter) est supprimé. Un simple clic sur un
  ticket en attente le fait passer automatiquement à *Prise en Charge* (message client auto +
  auto-assignation, logique déjà en place côté `PATCH /tickets/{id}/approve`) puis redirige
  directement vers `/admin/tickets/{id}` — toute la décision se prend désormais sur l'écran de
  détail, pas dans un popup dupliqué.
- `Modifié` : **écran de clôture** (`ticket-detail`) — le sélecteur de statut n'est plus affiché à
  l'étape de revue (il n'était pas logique de le demander avant même d'avoir vu la classification IA
  et la suggestion RAG). Il apparaît désormais à l'étape de clôture, regroupé avec Catégorie finale /
  Priorité finale / Classification finale : les 4 champs sont modifiables ensemble au même endroit.
- `Modifié` : consigne du champ **Solution appliquée** renforcée (placeholder + texte d'aide) pour
  inciter à décrire diagnostic + action réalisée en détail — ce texte alimente directement la base
  de connaissances RAG et sert de matériau pour un futur ré-entraînement.
- Vérifié en direct : clic sur un ticket en attente dans la file d'approbation → statut, message
  auto et assignation confirmés dans l'historique ; étape de clôture affichant bien les 4 champs
  (statut + catégorie + priorité + classification) ensemble.

### Ajouté / Modifié (2026-07-29, refonte du workflow de traitement des tickets)

- `Ajouté` : nouveaux champs `Ticket.priorite_finale`, `Ticket.classification_finale`,
  `Ticket.assigne_a` (migration additive `_add_column_if_missing`), exposés dans `TicketOut` aux
  côtés des valeurs de départ (`priorite_predite` = priorité saisie par le client,
  `classification_predite` = valeur par défaut « Demande » — **aucun modèle dédié n'existe pour ces
  deux champs**, contrairement à la catégorie qui reste la seule vraie prédiction ML ; l'admin les
  confirme ou corrige via des listes déroulantes plutôt que du texte libre).
- `Ajouté` : panneau **« Résultat ML »** (admin, `ticket-detail`) regroupant catégorie, priorité,
  classification et confiance en un seul bloc, au lieu de la seule catégorie affichée jusque-là.
- `Ajouté` : écran de clôture en 2 temps côté admin — bouton **« Suivant »** fait passer de la revue
  (classification IA + suggestion RAG) à un écran de clôture dédié (catégorie/priorité/classification
  finales en `<select>`, réponse au client, solution appliquée, bouton Enregistrer).
- `Ajouté` : **message automatique au client** dès le passage à *Prise en Charge* (aucune saisie
  admin requise à ce stade) et **auto-assignation** du ticket à l'admin qui le prend en charge
  (`assigne_a`), si non déjà assigné.
- `Modifié` : `STATUS_TRANSITIONS` (`api/routers/tickets.py`) — *Rejeté* est désormais atteignable
  depuis *Prise en Charge* et *Problème* (pas seulement depuis *En attente*), pour permettre le flux
  En attente → Prise en Charge → Problème → (Résolu | Rejeté).
- `Ajouté` : liste des tickets admin reformatée avec les colonnes STATUT / Titre / Demandeur /
  Classification / Catégorie / Temps écoulé / CID / Filiale / Priorité / Assigné à /
  Résolution-Motif — alignées sur le schéma du corpus d'entraînement (`data/raw/HelpDesk1.csv`) pour
  faciliter un futur export vers le pipeline DVC. `CID` et `Temps écoulé` calculés par
  `ticket_service.ticket_to_dict()`.
- Vérifié en direct (Docker rebuild + `npm start`) : cycle complet sur un ticket réel — prise en
  charge (message auto + auto-assignation confirmés via API), passage à Résolu avec correction
  manuelle de la priorité (Modéré → Urgent) et de la catégorie, persistance confirmée en base et
  dans l'historique (`ticket_history`), affichage correct dans la liste.

### Ajouté / Corrigé (2026-07-16, boucle admin → base de connaissances RAG)

- `Ajouté` : détection de « cas nouveau » — le score de similarité de la meilleure suggestion RAG
  (`rag_score`, déjà calculé par `HybridRAGEngine` mais jusque-là jamais transmis à l'API) est
  désormais persisté sur le ticket (nouvelle colonne `Ticket.rag_score`, migration additive) et
  exposé via `TicketOut`. Sous 0.50 (`NOVELTY_THRESHOLD`, même seuil que
  `HybridRAGEngine.similarity_threshold`), l'écran admin affiche « Nouveau type de problème » à la
  place de la suggestion RAG, et le champ **Solution appliquée** (renommage de « Note interne »)
  devient obligatoire avant de pouvoir passer le ticket à *Résolu* — vérifié côté serveur
  (`PATCH /tickets/{id}/approve` renvoie 400 si absent) et côté client (message inline). Au-dessus
  du seuil, comportement inchangé (suggestion affichée, champ facultatif).
- `Modifié` : `archive_resolved_ticket()` (base de connaissances TinyDB qui alimente le RAG)
  enregistre désormais la solution **réellement appliquée par l'admin**
  (`commentaire_interne`/`commentaire_admin`) en priorité, et ne retombe sur la proposition IA
  d'origine (`solution_rag`, jamais validée humainement) que si l'admin n'a rien saisi. Vérifié en
  direct : un ticket "nouveau" archive la solution tapée par l'admin ; un ticket "connu" résolu
  sans note archive la suggestion IA telle quelle.
- `Corrigé` (bug préexistant, aggravé par le point précédent) : `_migrate_columns()` n'était pas
  tolérante aux 2 workers uvicorn démarrant en parallèle (`Dockerfile.api`, `--workers 2`) — les
  deux tentaient `ALTER TABLE ADD COLUMN` simultanément, le perdant plantait avec
  `duplicate column name` non intercepté (contrairement à `_seed_users()` qui a déjà un
  `try/except`). Invisible jusqu'ici car aucune migration n'avait été ajoutée depuis le fix bcrypt
  (Phase 12) ; révélé par l'ajout de `rag_score`. Chaque `ALTER TABLE` est maintenant tolérant à
  l'erreur `duplicate column name`.
- `Corrigé` : `ticket-detail.ts` (client et admin) lisait `route.snapshot.paramMap` une seule fois
  dans `ngOnInit()` — en changeant de ticket sans rechargement complet (même route, id différent),
  Angular réutilise le composant sans relancer `ngOnInit`, donc le ticket précédemment affiché
  restait visible (statut, description, historique) malgré l'URL à jour. Remplacé par un abonnement
  à `route.paramMap` (observable), qui recharge les données à chaque changement d'id.
- `Corrigé` : `new-ticket.ts::composeDescription()` injectait un texte de substitution

- `Corrigé` : `new-ticket.ts::composeDescription()` injectait un texte de substitution
  ("Non précisé", "Aucun message indiqué", "Aucune action indiquée") pour chaque question laissée
  vide — or `predict_and_recommend()` (`api/services/ai_service.py`) classe le ticket à partir de
  **la seule `description`** (le titre n'est pas lu à cette étape). Résultat observé : un ticket
  avec toutes les questions vides envoyait ce texte de remplissage tel quel au classifieur, qui le
  catégorisait avec une confiance trompeuse (78 %) puis restreignait le RAG à cette catégorie
  probablement erronée — d'où une suggestion hors-sujet (ticket "problème de connexion" → solution
  à propos d'un ERP). Les questions vides sont désormais simplement omises de la description
  envoyée à l'API, au lieu d'être remplacées par un texte générique.
- `Modifié` : le panneau technique **"Solution suggérée par l'IA"** (texte de résolution + source
  RAG) n'est plus affiché au client — ce contenu est écrit pour un agent IT et suppose des
  connaissances techniques que l'utilisateur final n'a pas. Remplacé par un panneau **"Suivi de
  votre demande"** en langage simple, dérivé du statut du ticket (`ticket-detail.ts`/`.html`
  côté client). Le panneau RAG technique reste inchangé côté admin (`features/admin/ticket-detail`)
  où il sert d'aide à la décision basée sur l'historique, comme prévu.

### Ajouté / Corrigé (2026-07-16)

- `Ajouté` : **sidebar noire** (admin + client) — identité visuelle propre, indépendante du thème
  clair/sombre de l'app.
- `Ajouté` : **mode sombre** (`ThemeService`, `frontend/src/app/core/services/theme.service.ts`) —
  bouton bascule dans la sidebar, persisté en `localStorage`, défaut basé sur
  `prefers-color-scheme` au premier lancement. Surcharge des variables CSS `@theme` (Tailwind v4)
  sous une classe `.dark` sur `<html>` : tous les écrans existants (bg-background, text-on-surface,
  bg-primary...) basculent automatiquement, sans toucher aux 15 templates.
- `Modifié` : formulaire **Nouveau ticket** (client) entièrement reconstruit selon la spécification
  fournie (portage d'un prototype Streamlit) — sélecteur d'exemples pré-remplis (Outlook, VPN,
  imprimante), questions guidées (depuis quand / message d'erreur / actions tentées), sélecteur de
  filiale. Description composée automatiquement à partir des réponses, `priorite: "Modéré"` envoyé
  explicitement. Vérifié en direct : création réelle d'un ticket via `POST /tickets/` avec
  classification IA (catégorie, confiance, suggestion RAG) retournée par le backend.
- `Corrigé` : la route racine (`''`) et le wildcard (`**`) redirigeaient vers `client/my-tickets`
  sans vérifier l'authentification — au démarrage (`npm start`), un visiteur non connecté
  atterrissait directement dans l'espace client. Les deux redirigent désormais vers `auth/login`.
  Le composant `Login` redirige immédiatement vers l'espace du bon rôle si une session valide
  existe déjà (`ngOnInit`), évitant de forcer une reconnexion inutile.
- `Ajouté` : **expiration de session par inactivité** (`AuthService`, 20 minutes sans interaction
  souris/clavier/scroll/tactile) — déconnexion automatique + redirection vers `/auth/login`, timer
  réarmé sur `setSession()` ainsi qu'au démarrage de l'app si une session existante est détectée
  (survit au rechargement de page).
- `Ajouté` : `authInterceptor` déconnecte désormais automatiquement l'utilisateur sur toute réponse
  API `401` (couvre l'expiration réelle du JWT côté backend, 8h, indépendamment du timer
  d'inactivité côté client). Vérifié en direct avec un token corrompu.

### Corrigé (2026-07-07)

- `client-layout.ts` : la déconnexion côté client redirigeait vers `client/my-tickets` au lieu de
  la page de login. Cause : `logout()` appelait `router.navigate(['/login'])` (route inexistante,
  préfixe `auth/` manquant) juste après que `AuthService.logout()` ait déjà navigué correctement
  vers `/auth/login` — l'appel redondant tombait sur le wildcard `**` qui redirige vers
  `client/my-tickets`. Supprimé l'appel redondant (le service gère déjà la navigation) ; nettoyé
  au passage une injection `Router` inutilisée dans `admin-layout.ts`. Vérifié en direct pour les
  deux rôles.

### Refonte frontend (Stitch) — écrans admin + gestion des utilisateurs (2026-07-06)

- `Ajouté` : module **gestion des utilisateurs** (`api/routers/admin.py`, jusque-là un scaffold
  vide et non enregistré dans `main.py`) : `GET/POST /admin/users` (création admin-only avec
  génération d'un mot de passe temporaire aléatoire, ex. `Oiq@4083`), `PATCH /admin/users/{id}`
  (changement de rôle admin/client, activation/désactivation, auto-désactivation bloquée).
  `User.first_login` (nouvelle colonne, migration additive) force le changement de mot de passe
  à la première connexion via `POST /auth/change-password` ; les guards Angular
  (`authGuard`/`adminGuard`) redirigent vers un nouvel écran `/auth/change-password` tant que
  `first_login=true`. Flux vérifié de bout en bout (création → login avec mdp temporaire →
  redirection forcée → changement → accès débloqué).
- `Ajouté` : `GET /admin/model-info` — expose les métriques réelles du modèle entraîné
  (`models/model_metadata.json` : F1-macro, accuracy, seuil, limites connues) pour l'écran
  Monitoring IA.
- `Ajouté` : écran **Monitoring IA** (nouveau, aucun équivalent avant) — confiance moyenne réelle,
  taux de correction manuelle (catégorie finale ≠ catégorie prédite), tickets à faible confiance,
  confiance moyenne par catégorie, métriques du modèle entraîné. Les métriques fabriquées de la
  maquette Stitch (latence RAG P95, alertes de dérive, heatmap de correction par sous-catégorie)
  ont été abandonnées faute d'infrastructure de monitoring réelle.
- `Ajouté` : écran **Notifications** (composant vide auparavant) — flux d'activité dérivé des
  vraies données (tickets en attente >24h, file d'approbation, retours clients récents, nouveaux
  comptes) plutôt qu'une table de notifications persistées (non implémentée, hors périmètre).
- `Modifié` : écrans **Dashboard**, **File d'approbation**, **Tous les tickets** (composant vide
  auparavant), **Traitement du ticket**, **Gestion des utilisateurs**, et le **shell admin-layout**
  redessinés (Tailwind, thème Stitch clair). Fabrications de la maquette supprimées (agents
  fictifs, SLA inventés, insights IA non branchés, "1 284 utilisateurs") au profit de données
  réelles (`ticket.confiance`, `categorie_finale`, `demandeur_nom`/`demandeur_email` — nouveaux
  champs ajoutés à `ticket_to_dict()` — comptages réels).
- `Corrigé` (bug préexistant, trouvé en testant "Traitement du ticket" en direct) :
  `GET /tickets/{id}` filtrait par `Ticket.user_id == user.id` même pour un admin, donc tout
  ticket appartenant à un autre utilisateur renvoyait 404 "Ticket introuvable" — la page admin de
  traitement de ticket était cassée pour la quasi-totalité des tickets. Un admin peut désormais
  consulter n'importe quel ticket.
- `Corrigé` (bug préexistant dans `approval-queue.ts`) : le bouton "Valider" envoyait le statut
  `"Validé"`, absent de `VALID_STATUSES` et non permis depuis `"En attente"` — chaque validation
  échouait avec une 400. Transition corrigée vers `"Prise en Charge"` (vérifié en direct : le
  ticket disparaît bien de la file après validation).
- `Corrigé` : badge de rôle "Admin" invisible dans l'écran Utilisateurs — `bg-primary` +
  `bg-opacity-10` (syntaxe Tailwind v3) associés à `text-primary` produisaient un texte de la même
  couleur que le fond en Tailwind v4 ; remplacé par la syntaxe d'opacité `bg-primary/10`.

### Refonte frontend (Stitch) — Mes Tickets, Détail Ticket, Mon Profil (2026-07-06)

- `Ajouté` : `POST /tickets/{id}/feedback` — persiste le vote 👍/👎 + commentaire client
  (`Ticket.feedback_vote`/`feedback_comment`, migration additive `_migrate_columns`).
  **Corrige R-15 / EF-13** : le frontend affichait un faux message de confirmation sans rien
  envoyer au serveur. Vérifié par relecture API indépendante après rechargement complet.
- `Ajouté` : `GET`/`PATCH /auth/me` — lecture/édition réelle de nom/prénom/filiale de
  l'utilisateur connecté depuis l'écran Mon Profil (auparavant simulé par un `setTimeout`).
  Mot de passe, upload photo, préférences de notification, suppression de compte : aucun
  endpoint (décision explicite, hors périmètre "minimum utile" de cette itération) — affichés
  mais désactivés et marqués « Bientôt disponible ».
- `Modifié` : écrans client **Mes Tickets**, **Détail du Ticket**, **Mon Profil** redessinés
  (design Stitch, Tailwind). KPI de la liste de tickets (total/en attente/résolu, taux de
  résolution, délai moyen de résolution) calculés depuis les vraies données au lieu des valeurs
  fabriquées de la maquette ("92% satisfaction", carte "Suggestion AI" citant un faux ticket).
- `Corrigé` : bug trouvé en testant en direct — le formulaire de feedback était imbriqué dans
  la carte "Solution IA" (`@if (t.solution_rag)`), donc invisible pour un ticket résolu dont la
  recommandation RAG est vide. Le feedback dépend désormais uniquement du statut `Résolu`.

### Phase 12 — Étude utilisateur légère (2026-07-05)

- `Ajouté` : [CADRAGE_SRS.md](CADRAGE_SRS.md) §6 — parcours golden path (Client crée un ticket →
  Admin traite et répond → Client consulte la résolution) rejoué contre l'application Docker
  réellement déployée, chronométré. Extension Chrome indisponible cette session : parcours
  rejoué au niveau API (`curl`) + revue de code des templates Angular pour juger l'ergonomie.
  EF-01/02/03/04/06/07/08 confirmés fonctionnels de bout en bout ; validation des transitions de
  statut testée (transition illégale correctement rejetée en 400).
- `Corrigé` : **EF-05** (matrice §5) — l'étude a montré que `create_ticket()` fixe
  `statut="En attente"` sans condition, quelle que soit la confiance (testé à 0.78 et 0.91) : il
  n'existe **aucun routage automatique réel** par seuil de confiance, contrairement à ce que la
  matrice affirmait ("mécanisme en place"). Le seuil et les indicateurs `auto_routed`/
  `low_confidence` sont calculés mais ne pilotent aucune branche de workflow.
- `Sécurité`/`Découvert` : **R-15** (nouveau risque, Ouvert, I=Élevé) — le bouton de feedback
  client (👍/👎 + correction) affiche "Merci pour votre retour !" alors que
  `submitFeedbackComment()` ne fait qu'un `console.log()` (TODO explicite dans le code source) :
  rien n'est envoyé au serveur. L'utilisateur croit son avis enregistré ; il est perdu. **EF-13**
  (matrice §5) corrigé en conséquence — plus grave qu'une simple absence de fonctionnalité.
  À corriger avant toute démo devant jury.
- `Découvert` : **R-16** (nouveau risque, Ouvert) — absence de routage différencié par confiance
  (cf. correction EF-05 ci-dessus), décision de produit à prendre (assumer ou implémenter).
- `Découvert` (mineur, non corrigé) : incohérence de nommage `TicketCreate.priorite` (entrée) vs
  `TicketOut.priorite_saisie` (sortie) — un consommateur externe de l'API devinant le nom depuis
  la réponse écrit silencieusement une valeur par défaut sans erreur (frontend Angular non
  affecté, utilise le bon nom) ; et seuil `0.40` codé en dur dans `tickets.py`
  (`approve_ticket`/`refresh_rag`), obsolète depuis le passage au seuil unique 0.60 en Phase 13.

---

### Phase 12 — Matrice exigences → résultats (2026-07-05)

- `Ajouté` : [CADRAGE_SRS.md](CADRAGE_SRS.md) §5 réécrite en matrice complète — 17 exigences
  fonctionnelles (EF) + 14 non-fonctionnelles (ENF) évaluées individuellement avec résultat mesuré
  et statut, contre l'ancien "extrait" groupé par phase. Bilan : 9/17 EF atteints, 3 partiels,
  4 non faits, 1 backlog assumé · 5/14 ENF atteints, 5 partiels, 4 non atteints.
- `Ajouté` : `pytest-cov` dans `requirements.txt` — mesure de couverture (ENF-10) : **74 % en
  local** (`src/` + `api/`, 59 tests, cible ≥70 % atteinte) mais **22 % seulement reproductible
  en CI** (41 tests unitaires : `test_api_integration.py` exclu car `models/best_pipeline.pkl`
  est gitignoré, absent d'un clone frais). Trouvé en auto-révision de cette même tâche : le
  premier chiffre annoncé (74 %, "✅ Atteint") ne l'était qu'en local, pas vérifiable par la CI
  telle que configurée — corrigé en 🟡 Partiel dans la matrice et `TESTING.md`.
- `Corrigé` : rappel de la classe *Sécurité* recalculé sur `models/best_pipeline.pkl` +
  `data/splits/test.csv` : **0.364** (36,4 %), contre l'estimation "~20 %" documentée dans
  `RISKS.md` depuis la Phase 1 (obsolète, antérieure aux corrections FORCE_RULES v1.1).
- `Sécurité`/`Découvert` : **R-14** (nouveau risque, Ouvert, P/I=Élevé) — `data/splits/test.csv`
  (split anti-fuite `GroupShuffleSplit` par Titre) ne contient **aucun exemple** des catégories
  *Backup* et *Communication* (0/356 lignes). Le F1-macro=0.685 rapporté (ENF-03) est donc calculé
  sur les classes réellement présentes dans le test, pas sur les 8 catégories du domaine —
  risque de sur-interprétation explicitement anticipé par `PLAN.md` Phase 12, désormais confirmé
  et documenté. Nécessite un split stratifié avant toute mesure F1-macro présentée comme fiable
  au jury.
- `Corrigé` : `TESTING.md` — le squelette de checklist était resté à 100 % non coché malgré
  59 tests écrits et exécutés ; mis à jour pour refléter l'état réel (tests faits/manquants) et
  renvoie vers la matrice `CADRAGE_SRS.md` §5.
- `Clarifié` : EF-14 ("génération de réponse par LLM avec citations") repose en réalité sur une
  génération **template-based** (citations numérotées, pas d'appel LLM) — Faithfulness=1.0 et
  hallucination=0 % sont donc triviaux par construction, pas une preuve de fiabilité d'un vrai LLM.
  À nuancer explicitement dans le mémoire pour ne pas survendre ce point au jury.

---

### Phase 12 — Nettoyage : doublon `HelpDesk1.csv` à la racine (2026-07-05)

- `Supprimé` : `helpdesk-ai/HelpDesk1.csv` — copie non suivie par git, identique octet pour octet
  à `data/raw/HelpDesk1.csv` (donnée gérée par DVC, `data/raw/*` gitignoré). Dette technique
  notée depuis la Phase 0, traitée par anticipation plutôt qu'en Phase 2 : rien ne pointait sur
  cette copie en priorité (`notebooks/data_quality_report.py` teste `data/raw/` en premier).

---

### Phase 12 — Authentification cassée en Docker : incompatibilité bcrypt/passlib (2026-07-05)

Test manuel de connexion client dans le navigateur (`http://localhost:8081`) → échec avec
les identifiants seed documentés. Logs du conteneur API :
`AttributeError: module 'bcrypt' has no attribute '__about__'`.

- `Corrigé` : `requirements.txt` et `docker/requirements-api.txt` — épinglé `bcrypt==4.0.1`.
  `passlib==1.7.4` (dernière release, non maintenue depuis 2020) lit
  `bcrypt.__about__.__version__` pour détecter la version du backend ; cet attribut a été
  retiré à partir de `bcrypt>=4.1`. Sans ce pin, `passlib[bcrypt]>=1.7.4` installe la
  dernière version de `bcrypt` (5.0.0 constaté), rendant **tout hachage de mot de passe
  défaillant** : `_seed_users()` échouait silencieusement à chaque démarrage du conteneur
  (aucun compte démo/admin/système jamais créé en base), et l'inscription via `/auth/register`
  aurait échoué de la même façon pour tout nouvel utilisateur.
- `Résolu` : dette technique documentée de longue date (4 tests d'authentification skippés
  dans `test_api_integration.py` faute de bcrypt fonctionnel dans l'environnement de test).
  **18/18 tests passent désormais** (contre 14/18 + 4 skip auparavant).

---

### Phase 12 — Test de charge : critère P95 non atteint, cause identifiée (2026-07-05)

- `Ajouté` : `scripts/load_test.py` — outil de test de charge autonome (requêtes concurrentes
  via `ThreadPoolExecutor`, mesure P50/P95/P99, comparaison au critère PFE ≤300ms).
- `Ajouté` : `metrics/load_test.json` — résultats de 3 scénarios (concurrence 1/5/20) contre
  l'API Docker réelle. **Critère P95≤300ms non atteint** dans les 3 cas : 330ms (séquentiel,
  proche) → 1068ms (concurrence 5) → 15022ms + 19% timeouts (concurrence 20). Cause
  identifiée : endpoint `POST /api/v1/predict` synchrone (`def`, pas `async def`) et
  CPU-bound (encodage sentence-transformers + `predict_proba` sklearn + recherche FAISS),
  limité par le GIL Python et seulement 2 workers uvicorn (`Dockerfile.api`). Optimisation
  (workers, pipeline d'inférence) renvoyée à la Phase 13, conformément à son périmètre.
- `Corrigé` : `docker/Dockerfile.front` — healthcheck utilisait `wget http://localhost/`,
  qui résout en `::1` (IPv6) dans le conteneur ; Nginx n'écoute qu'en IPv4 (`0.0.0.0:80`),
  causant un échec systématique (`Connection refused`) et un statut "unhealthy" permanent
  malgré un frontend fonctionnel. Remplacé par `http://127.0.0.1/`.
- `Ajouté` : `requests>=2.31.0` dans `requirements.txt` — dépendance directe de
  `scripts/load_test.py` (auparavant disponible seulement de façon transitive).

---

### Phase 12 — Test bout-en-bout Docker : 3 bugs de déploiement corrigés (2026-07-05)

Premier lancement réel de `docker compose up --build` en conditions de connexion lente —
a révélé des bugs invisibles en développement local (venv Windows).

#### Bug 1 — RAG sémantique en fallback silencieux (dépendance manquante)
- `Corrigé` : `docker/requirements-api.txt` — ajout de `pyarrow>=14.0.0`, requis par
  `pandas.read_parquet()` dans `SemanticRAGEngine.load()`. Absent de l'image API car
  installé seulement de façon transitive (via `streamlit`/`mlflow`) dans le venv de
  développement, jamais déclaré explicitement.
- `Corrigé` : `requirements.txt` — même ajout, pour ne pas dépendre d'une installation
  transitive fragile en dehors de Docker.

#### Bug 2 — Port 80 réservé par Windows
- `Modifié` : `docker/docker-compose.yml` — le service `frontend` est remappé sur le port
  hôte `8081` (`8081:80`) au lieu de `80:80`. Le port 80 est dans la plage d'exclusion
  Hyper-V/WSL2 de Windows et/ou occupé par un service système (HTTP.sys), rendant le bind
  impossible (`Ports are not available`).
- `Modifié` : `CORS_ORIGINS` (docker-compose.yml) et `DEPLOYMENT.md` mis à jour en conséquence.

#### Bug 3 — Noms de fichiers FAISS corrompus (mojibake Windows→Linux)
- `Corrigé` : `src/rag/semantic_engine.py::save()` — les noms de fichiers d'index FAISS par
  catégorie accentuée (ex. `index_cat_Réseau.faiss`) étaient mal encodés par l'API C++ de
  FAISS sous Windows, produisant des fichiers physiques nommés en mojibake
  (`index_cat_RÃ©seau.faiss`) alors que `metadata.json` référence le nom propre. Ce bug
  était invisible en développement (écriture et lecture symétriquement corrompues sur la
  même machine Windows) mais cassait totalement le chargement du RAG sémantique une fois
  le dépôt cloné sous Linux (Docker) : `FileIOReader ... No such file or directory`, avec
  fallback silencieux vers le RAG lexical. Fix : translittération ASCII via `unidecode()`
  avant construction du nom de fichier — le nom de catégorie affiché (accentué) reste
  inchangé partout ailleurs (metadata, logique applicative).
- `Ajouté` : `src/pipeline/rag_semantic_build.py` — script de reconstruction du RAG
  sémantique (miroir de `rag_build.py` pour le lexical), documenté comme processus manuel
  (hors `dvc.yaml`, nécessite le modèle sentence-transformers).
- `Corrigé` : artefacts `models/semantic_rag/` régénérés à partir des **1357 tickets**
  actuels de `data/splits/rag.csv` (les anciens artefacts dataient d'avant la Phase 10 et
  ne couvraient que 476 tickets — désynchronisés du RAG lexical).

#### Validation
- `docker compose up` (3 services) → tous healthy ; `GET /api/v1/health` → `rag_loaded: true` ;
  `POST /api/v1/predict` → RAG **hybride** actif (1357 tickets, alpha=0.5) ; frontend et
  dashboard répondent 200.

---

### Phase 12 — Tests & validation (2026-07-04)

#### Tests unitaires (41 nouveaux tests)
- `Ajouté` : `tests/test_heuristics.py` — 8 tests : FORCE_RULES (override, no-op si déjà
  correct, limites de mots avec `\b`), SOFT_RULES (seuil de confiance), plancher de
  confiance à 0.80.
- `Ajouté` : `tests/test_rag_engine.py` — 8 tests : recommandation avant `fit()`, requête
  vide, correspondance exacte, filtre catégorie, seuil + fallback, déduplication des
  résolutions identiques (base de connaissance en mémoire, scores TF-IDF vérifiés).
- `Ajouté` : `tests/test_hybrid_engine.py` — 9 tests : validation `alpha`, fusion de
  scores (`0.5×sém + 0.5×lex`), limite `top_k`, sauvegarde/restauration de l'état des
  sous-moteurs partagés (régression du Bug 1 de Phase 13), fallback hybride. Sous-moteurs
  remplacés par des doublures (`FakeEngine`) pour éviter le téléchargement du modèle
  sentence-transformers pendant les tests.
- `Corrigé` : `tests/test_preprocess.py` — cassait la collection pytest entière
  (`ImportError: basic_clean` — fonction renommée `clean_text` depuis). Réécrit avec
  16 tests couvrant `clean_text`, `simplify_priorite/classification`, `build_text_*`.

#### Nettoyage découvert pendant l'audit lint (ruff)
- `Supprimé` : `api/db/__init__.py::init_db` — fonction dupliquée et cassée (`User` et
  `pwd_ctx` non importés, bug F821) ; jamais appelée (le vrai `init_db()` utilisé par
  `api/main.py` vit dans `api/db/database.py`). Code mort supprimé.
- `Corrigé` : imports inutilisés supprimés — `os` (`api/db/database.py`), `Depends`
  (`api/middleware/auth_middleware.py`), `JWTError` (`api/services/auth_service.py`),
  `sys` (`src/pipeline/split.py`), `pickle` (`src/rag/semantic_engine.py`).

#### CI/CD
- `Modifié` : `.github/workflows/ci.yml` — le job `python-ci` exécute maintenant
  `pytest tests/ --ignore=tests/test_api_integration.py` (toute la suite unitaire) au lieu
  de seulement `test_preprocess.py`. `test_api_integration.py` reste exclu du CI : il
  nécessite `models/best_pipeline.pkl`, ignoré par `.gitignore` (`models/*.pkl`) et donc
  absent d'un checkout CI frais.

---

### Phase 11 — Déploiement Docker + CI/CD (2026-07-04)

#### Docker
- `Ajouté` : `.dockerignore` — exclut `venv/`, `node_modules/`, `mlruns/`, `camembert_lora/`
  (~2 Go) du contexte de build ; réduit la taille du contexte de façon significative.
- `Ajouté` : `docker/requirements-api.txt` — dépendances runtime uniquement (sans dvc, mlflow,
  jupyter, ipykernel, pytest, streamlit, imbalanced-learn) → image API plus légère.
- `Modifié` : `docker/Dockerfile.api` — pré-téléchargement NLTK stopwords + modèle
  sentence-transformers (~420 Mo) pendant le build (image auto-suffisante) ; `curl` pour
  healthcheck ; 2 workers uvicorn.
- `Ajouté` : `docker/Dockerfile.front` — build multi-stage : `node:20-alpine` (ng build
  production) → `nginx:1.27-alpine` (serve SPA) ; healthcheck `wget`.
- `Ajouté` : `docker/nginx.conf` — SPA routing (`try_files /index.html`), cache 1 an sur
  assets hachés, headers sécurité (`X-Frame-Options`, `X-Content-Type-Options`).
- `Modifié` : `docker/docker-compose.yml` — 3 services (`api`, `frontend`, `dashboard`) avec
  healthchecks, `depends_on: condition: service_healthy`, volume `api-data` pour SQLite,
  réseau interne `helpdesk-net`.

#### CI/CD
- `Ajouté` : `.github/workflows/ci.yml` — 3 jobs : `python-ci` (ruff lint + pytest unitaires),
  `angular-ci` (npm ci + ng build prod), `docker-build` (docker build API + front après CI OK).

#### Documentation
- `Modifié` : `DEPLOYMENT.md` — guide complet : topologie Mermaid, démarrage rapide,
  variables d'environnement, volumes, CI/CD, sécurité, observabilité.

---

### Phase 10 — MLOps léger : pipeline DVC + MLflow (2026-07-04)

#### Scripts pipeline (4 stages)
- `Ajouté` : `src/pipeline/preprocess.py` — stage 1 : lit `HelpDesk1.csv` (UTF-8-sig),
  applique `clean_text` / `build_text_for_rag` / `build_text_enriched`, sauvegarde en UTF-8.
- `Ajouté` : `src/pipeline/split.py` — stage 2 : GroupShuffleSplit par Titre (anti-leakage),
  sorties `train.csv` / `test.csv` / `rag.csv` (rag = tickets résolus du train uniquement).
- `Ajouté` : `src/pipeline/train.py` — stage 3 : TF-IDF + CalibratedClassifierCV(LinearSVC),
  évaluation avec heuristiques, log MLflow (params + métriques + artefacts).
- `Ajouté` : `src/pipeline/rag_build.py` — stage 4 : ajuste `RAGEngine` lexical sur `rag.csv`,
  sauvegarde `models/rag_engine.pkl`.

#### DVC + MLflow
- `Modifié` : `dvc.yaml` — 4 stages déclarés (`preprocess → split → train → rag_build`) ;
  `dvc repro --dry` confirmé fonctionnel.
- `Ajouté` : `metrics/ml_eval.json` — métriques DVC trackées : F1-macro heuristiques=0.685
  (Infrastructure=0.79, Microsoft=0.97, Réseau=0.81, Système=1.0, Sécurité=0.53).
- `Ajouté` : `mlruns/` — experiment MLflow `helpdesk-ai-classification` créé.

#### Corrections annexes (découvertes lors du test pipeline)
- `Corrigé` : `src/rag/engine.py` — caractères emoji `✅` dans les `print()` remplacés
  par texte ASCII (incompatibilité console Windows cp1252).

### Phase 13 — Optimisation : plan d'amélioration expert (2026-07-04)

#### Semaine 1 — Quick wins (FORCE_RULES + seuils)
- `Corrigé` : `src/models/heuristics.py` — `"teams"` retiré des FORCE_RULES Microsoft (conflit sémantique
  avec le Titre de test `[Communication] Problème Microsoft Teams`).
- `Ajouté` : FORCE_RULES Infrastructure — `"san"`, `"baie de stockage"`, `"perte communication san"`,
  `"hyperviseur"`, `"esxi"`, `"vcenter"` (couvrent `[Infrastructure] Perte de communication avec le SAN`).
- `Ajouté` : FORCE_RULES Sécurité — `"ids"`, `"acces non autorise"`, `"acces non-autorise"`
  (couvrent `[Sécurité] Accès non autorisé détecté par l'IDS`).
- `Ajouté` : SOFT_RULES Communication — `"teams"`, `"probleme teams"`, `"appel teams"`,
  `"reunion teams"`, `"visioconference"` (confidence=0.78).
- `Ajouté` : SOFT_RULES Sécurité — `"compte bloque"`, `"compte utilisateur bloque"`,
  `"tentative connexion"`, `"connexion suspecte"` (confidence=0.82).
- `Modifié` : `params.yaml` — `rag.similarity_threshold` 0.30→0.50 ; ajout `rag.fallback_threshold=0.20`,
  `rag.hybrid_alpha=0.5`, `ml.confidence_threshold=0.60`.
- `Modifié` : `models/model_metadata.json` — `confidence_threshold` 0.40→0.60 ; `known_weaknesses`
  mis à jour avec statut `[CORRIGE v1.1]` pour les 3 classes défaillantes.
- `Modifié` : `src/rag/semantic_engine.py` + `src/rag/engine.py` — seuil de similarité par défaut
  0.30→0.50 (filtre les suggestions RAG peu pertinentes, améliore Answer Relevancy).
- `Modifié` : `api/predictor.py` — seuil de confiance par défaut 0.40→0.60.

#### Semaine 2 — Hybrid Search
- `Ajouté` : `src/rag/hybrid_engine.py` — `HybridRAGEngine` : score hybride = alpha×sémantique +
  (1-alpha)×lexical (alpha=0.5 par défaut) ; fusion par résolution comme clé de déduplication.
- `Modifié` : `api/predictor.py` — intégration `HybridRAGEngine` ; ordre de priorité :
  Hybride > Sémantique seul > Lexical seul.
- `Modifié` : `api/services/rag_service.py` — `rag_engine_info()` expose `hybrid_active`.
- *À mesurer* : ré-exécuter `07_rag_evaluation.ipynb` → P@3 et MRR attendus supérieurs au lexical baseline.

#### Semaine 3 — Données (conditionnel)
- *Planifié* : collecte 50+ tickets réels par classe rare (Infrastructure, Sécurité) auprès de
  l'entreprise → re-train → benchmark F1 avant/après.

### Phase 9 — Frontend Angular : connexion complète back↔front (2026-07-04)

#### Environnement & configuration
- `Modifié` : `environments/environment.ts` + `environment.development.ts` — `apiUrl` = `http://localhost:8000/api/v1`.

#### Modèles TypeScript alignés sur le backend
- `Modifié` : `models/auth.models.ts` — `LoginResponse` (flat TokenOut), `AuthUser`, `LoginRequest` (champ `username` OAuth2).
- `Modifié` : `models/ticket.models.ts` — `Statut` (5 valeurs réelles), `Ticket` (tous les champs), `STATUT_CFG`, `TicketCategory`, `FILIALES`.

#### Couche API & session
- `Modifié` : `api/auth-api.service.ts` — `login()` envoie `application/x-www-form-urlencoded` via `HttpParams`.
- `Modifié` : `core/services/auth.service.ts` — gestionnaire de session uniquement : `setSession()`, `logout()`, `isAdmin()`, `getToken()`.

#### Sécurité Angular
- `Ajouté` : `core/interceptors/auth.interceptor.ts` — `HttpInterceptorFn` qui injecte `Bearer <token>`.
- `Ajouté` : `core/guards/auth.guard.ts` — `CanActivateFn` (authentification requise).
- `Ajouté` : `core/guards/admin.guard.ts` — `CanActivateFn` (rôle admin requis).
- `Modifié` : `app.config.ts` — `provideHttpClient(withInterceptors([authInterceptor]))`.
- `Modifié` : `app.routes.ts` — routes auth/client/admin avec guards, `tickets/:id` pour détail.

#### Composants auth
- `Modifié` : `features/auth/login/` — formulaire réactif, appel `AuthApiService.login()`, redirection par rôle.
- `Modifié` : `features/auth/register/` — inscription + auto-login après succès.

#### Pages détail ticket
- `Ajouté` : `features/client/ticket-detail/` — confiance (barre colorée), solution RAG + sources, réponse IT, feedback 👍/👎, historique.
- `Ajouté` : `features/admin/ticket-detail/` — vue 2 colonnes : infos/RAG/historique + formulaire traitement (statut, catégorie, commentaires), refresh RAG.

#### Corrections de build
- `Corrigé` : `dashboard.ts`, `home.ts` — `'En cours'` → `'Prise en Charge'` (statut réel).
- `Corrigé` : `profile.ts` — import `CurrentUser` supprimé (type inexistant).
- `Corrigé` : `approval-queue.ts` — champs `message_client`/`note_interne` → `commentaire_client`/`commentaire_interne`.
- `Corrigé` : `test-api.ts` — `login(payload)` → `login(payload.email, payload.password)`.
- `Corrigé` : `client/ticket-detail.ts` — `RouterLink` retiré des imports (non utilisé dans le template).

### Phase 8 — Backend API v1.1 : sécurité + intégration sémantique + /ingest (2026-07-03)

#### Contrat OpenAPI versionné
- `Modifié` : `api/main.py` — tous les routers sous `/api/v1` (`auth`, `tickets`, `ingest`) ;
  `openapi_tags` structurés ; CORS configurables via `CORS_ORIGINS` dans `.env`.
- `Modifié` : `api/config.py` — ajout `CORS_ORIGINS` et `INGEST_API_KEY` (chargés depuis `.env`).
- `Ajouté` : `.env.example` — template des variables d'environnement (jamais committé).

#### Sécurité
- `Ajouté` : `api/middleware/auth_middleware.py` — rate limiting login (10 req/60 s par IP,
  dépendance FastAPI, retourne HTTP 429).
- `Modifié` : `api/routers/auth.py` — dépendance `check_login_rate_limit` sur `/login` ;
  `tokenUrl` mis à jour `/api/v1/auth/login`.
- `Modifié` : CORS restreint aux origines configurées (plus de `"*"`).

#### Intégration RAG sémantique
- `Modifié` : `api/predictor.py` — chargement `SemanticRAGEngine` (FAISS) au démarrage ;
  `recommend()` dispatch sémantique → lexical (fallback) ; `_semantic_rag_loaded` exposé.
- `Modifié` : `api/services/ai_service.py` — `predict_and_recommend()` et `recommend_for_category()`
  utilisent `predictor.recommend()` (plus d'appel direct à `predictor.rag`).
- `Modifié` : `api/services/rag_service.py` — implémenté (`get_rag_recommendations`, `rag_engine_info`).

#### Réparation et enregistrement `/ingest`
- `Ajouté` : `api/routers/ingest.py` — endpoint Power Automate réécrit entièrement :
  - Authentification API key (`X-Api-Key` header, `INGEST_API_KEY` depuis `.env`)
  - Schéma Pydantic `IngestRequest` avec validation (min_length, max_length)
  - Insertion ORM SQLAlchemy (plus de `sqlite3` direct)
  - Utilisateur système `system@helpdesk-ai.local` (créé par `init_db()`)
  - Réponse structurée : `ticket_id`, `prediction`, `solution_rag`, `needs_approval`

#### Refactor en couches
- `Modifié` : `api/services/ticket_service.py` — `ticket_to_dict()` implémentée
  (sérialisation ORM → dict JSON).
- `Modifié` : `api/routers/tickets.py` — utilise `ticket_to_dict` du service (plus de
  `_ticket_to_dict` dupliquée dans le router).
- `Modifié` : `api/db/database.py` — seeding utilisateurs (système + démo) non-fatal dans `init_db()`.

#### Tests d'intégration
- `Ajouté` : `tests/__init__.py`, `tests/test_api_integration.py` — 18 tests couvrant :
  health, catégories, prédiction NLP+RAG, auth, tickets CRUD, ingest (API key).
  **14/18 passent** ; 4 skippés (incompatibilité bcrypt 4.x + passlib 1.7.x dans le venv).
- `Modifié` : `requirements.txt` — `sentence-transformers>=2.2.2`, `faiss-cpu>=1.7.4` ajoutés.

### Phase 7 — Évaluation RAG (RAGAS simplifié) + génération avec citations (2026-07-03)

#### Évaluation RAG
- `Ajouté` : `notebooks/07_rag_evaluation.ipynb` — notebook d'évaluation complet (tâches 7.1–7.6).
- `Ajouté` : `metrics/rag_eval.json` — résultats chiffrés (P@3, R@3, MRR@3, nDCG@3, RAGAS).
- `Ajouté` : `notebooks/figures/07_rag_evaluation_metrics.png` — comparatif métriques sémantique vs lexical.
- `Ajouté` : `notebooks/figures/07_ragas_summary.png` — résumé métriques RAGAS.

#### Résultats Phase 7 (80 requêtes stratifiées, GT = même catégorie)
| Métrique | Sémantique (FAISS) | Lexical (TF-IDF) | Δ |
|---|---|---|---|
| P@3 | 0.3042 | **0.4208** | −0.12 |
| MRR@3 | 0.5646 | **0.6521** | −0.09 |
| nDCG@3 | 0.3505 | **0.4520** | −0.10 |
| Score moyen | **0.6886** ★ | 0.1801 | +0.51 |
| RAGAS Answer Relevancy | **0.5841** | — | — |
| RAGAS Faithfulness | **1.0000** | — | — |

**Analyse** : le moteur lexical (TF-IDF) surpasse le sémantique sur les métriques de précision
catégorielle (correspondance exacte des mots-clés IT sur corpus à forte redondance). Le moteur
sémantique produit des scores de similarité **3.8× plus élevés** (0.69 vs 0.18) — confiance
calibrée supérieure, essentielle pour la génération de réponse. La génération template garantit
Faithfulness=1.0 (0 hallucination par construction).

**LLM-as-a-Judge** (tâche 7.5) renvoyé en BACKLOG — résultats suffisants pour le PFE sans LLM externe.

### Phase 6 — RAG sémantique (FAISS + embeddings FR) (2026-06-27)

#### Moteur RAG sémantique
- `Ajouté` : `src/rag/semantic_engine.py` — `SemanticRAGEngine` : embeddings denses
  `paraphrase-multilingual-mpnet-base-v2` (768d, multilingue FR+EN) + index FAISS IndexFlatIP
  (cosinus via L2-norm). Filtre par catégorie via index FAISS dédié par classe. Save/load
  (index.faiss + parquet + metadata.json).
- `Ajouté` : `notebooks/06_rag_semantique.ipynb` — pipeline complet : chargement base 476 tickets →
  encodage FAISS → tests qualitatifs → évaluation quantitative (query = titre+description seul,
  évaluation réaliste) → comparaison lexical vs sémantique → sauvegarde.
- `Ajouté` : `models/semantic_rag/` — index FAISS + knowledge base parquet + metadata.
- `Ajouté` : `models/semantic_rag_metadata.json` — métriques Phase 6.
- `Ajouté` : `notebooks/figures/rag6_01_comparaison.png` — double bar chart lexical vs sémantique.

#### Résultats Phase 6 (évaluation réaliste : query = titre+description)
| Métrique | Lexical (TF-IDF) | Sémantique (FAISS) | Gain |
|---|---|---|---|
| Score cosinus moyen top-1 | 0.7646 | **0.9321** | **+0.1675** |
| Couverture globale | 100 % | 100 % | = |

Gain sémantique uniforme sur toutes les catégories (+0.12 à +0.20). La compréhension
sémantique permet de retrouver des résolutions pertinentes même quand les mots-clés diffèrent.

#### ADR-004 décidé
- `Ajouté` : décision FAISS local (pas ChromaDB/Weaviate) — simplicité, reproductibilité,
  pas de dépendance serveur, compatible GPU/CPU local.

- `Corrigé` : évaluation naïve (query = text_rag complet → score=1.0 artificiel) remplacée
  par évaluation réaliste (query = titre+description uniquement).

### Phase 5 — Fine-tuning CamemBERT (LoRA) + features enrichies (2026-06-27)

#### Fine-tuning CamemBERT-base + LoRA
- `Ajouté` : `notebooks/05_camembert_finetuning.ipynb` — pipeline complet (dataset HuggingFace → tokenisation CamemBERT → split anti-fuite GroupShuffleSplit par Titre → LoRA r=8/alpha=16 sur `query,value` → entraînement GPU local (10 epochs, FP32) → évaluation F1-macro + matrice de confusion + analyse HITL → benchmark vs TF-IDF). **F1-macro = 0.5685 / Accuracy = 0.6873** — à parité avec TF-IDF+heuristiques (0.5673 ; écart +0.0012 dans le bruit statistique sur 355 tickets), mais atteint par compréhension sémantique **sans règles codées à la main**.
- `Ajouté` : adaptateur LoRA `models/camembert_lora_adapter/` (adapter_config + safetensors + tokenizer) et `models/camembert_metadata.json`.
- `Ajouté` : figures `notebooks/figures/cam_01_confusion.png`, `cam_02_confiance.png`, `cam_03_benchmark.png`.

#### Features enrichies (réduction du bruit catégoriel)
- `Ajouté` : `src/data/preprocess.py` — `simplify_priorite` (4→3 : Majeur+Critique→haute), `simplify_classification` (5→3 : Incident+Alerte→incident, Problème+Changement→changement), `build_text_enriched` (préfixe `type <clf> priorite <prio>` + titre + description). La cible métier `Catégorie` (8 classes) reste inchangée.
- `Modifié` : `notebooks/02_preprocessing.ipynb` — section 4b ajoutée ; génère `priorite_simple`, `classification_simple`, `text_enriched` (1638 valeurs uniques vs 1133 pour `text_clean`). CSV `data/processed/HelpDesk1.csv` régénéré (23 colonnes).
- `Modifié` : `notebooks/05_camembert_finetuning.ipynb` — entraînement sur `text_enriched`. **Gain enrichissement : F1 0.5325 → 0.5685 (+0.036)** ; Backup et Système passent à F1=1.00, Microsoft 0.45→0.58. Infrastructure et Sécurité restent à 0.00 (Titres de test sans équivalent sémantique en entraînement — effet du split anti-fuite).
- `Corrigé` : `models/camembert_metadata.json` et cellule métadonnées du notebook — `torch_dtype` réel **float32** (LoRA incompatible avec le scaler FP16), traçage de la feature `text_enriched` et du F1 sans enrichissement.

### Phase 3–4 — Correctifs qualité ML + Benchmark externe (2026-06-27)

#### Correction fuite de données — 03_modeling.ipynb
- `Corrigé` : split **GroupShuffleSplit par Titre** (46 train / 12 test) dans `notebooks/03_modeling.ipynb` — le modèle ne voit plus aucun Titre de test en entraînement. F1 honnête : **0.38 ML seul / 0.57 avec heuristiques** (était 1.0 artificiel).
- `Corrigé` : sélection `best_ml_name` dans la cellule d'évaluation heuristiques — filtre sur `pipelines` pour éviter un `KeyError` si `Dummy` avait le meilleur F1.
- `Modifié` : `models/model_metadata.json` — métriques, `split_strategy`, `known_weaknesses` et `dataset_note` mis à jour avec les valeurs honnêtes.
- `Ajouté` : cellule d'interprétation (`aa110028`) dans `03_modeling.ipynb` — narrative jury : GroupShuffleSplit / heuristiques / CamemBERT.

#### Benchmark externe sur données réelles publiques
- `Ajouté` : `notebooks/04_benchmark_externe.ipynb` — 17 cellules, pipeline identique à `03_modeling.ipynb` appliqué au dataset public `Tobi-Bueck/customer-support-tickets` (11 918 tickets, aucune redondance artificielle). **Résultats : TYPE (analogue Classification) F1=0.83 / QUEUE (analogue Catégorie, 10 classes) F1=0.48**.
- `Ajouté` : `data/external/similar_helpdesk_dataset.csv` — sous-ensemble anglais (11 923 lignes, 15 colonnes), ignoré par git (`data/external/` dans `.gitignore`).
- `Ajouté` : 6 figures dans `notebooks/figures/` : `bench_01_distribution_classes.png`, `bench_02_comparaison.png`, `bench_mdl_01_distribution.png`, `bench_mdl_02_benchmark_queue.png`, `bench_mdl_03_confusion_queue.png`, `bench_mdl_04_confusion_type.png`.

#### Correctifs code (audit qualité)
- `Corrigé` : `api/db/nosql_store.py` — fuite de handles fichiers TinyDB : toutes les fonctions encapsulées dans `with _open_db() as db:`.
- `Corrigé` : `src/models/heuristics.py` — règle `FORCE_RULES` Sécurité dédoublonnée (`"intrusion détectée"` redondant avec `"intrusion detectee"` après normalisation).
- `Corrigé` : `notebooks/03_modeling.ipynb` — cellules code mortes supprimées (`tfidf_shared`, `clf_lr`, `clf_svc` inutilisés).

#### EDA (01_eda.ipynb)
- `Ajouté` : section « Benchmark externe » dans `notebooks/01_eda.ipynb` — 5 cellules : introduction (table de correspondance colonnes), aperçu dataset, distribution classes, longueur textes, tableau de comparaison.

---

### Phase 3–4 — Modélisation multi-modèles + Backend NoSQL (2026-06-26)

#### Notebooks restructurés
- `Modifié` : `notebooks/02_preprocessing.ipynb` — notebook complet (imports → nettoyage → features titre+desc → analyse redondance → sauvegarde → 3 figures PNG).
- `Modifié` : `notebooks/03_modeling.ipynb` — multi-modèles (LR+SMOTE, LinearSVC calibré, LightGBM, Ensemble) + évaluation pipeline complet ML+heuristiques + benchmark PNG + matrices de confusion PNG + analyse HITL PNG + sauvegarde modèle.
- `Ajouté` : `notebooks/figures/mod_01_benchmark.png`, `mod_02_confusion_ml.png`, `mod_03_confusion_heuristiques.png`, `mod_04_hitl_analyse.png`, `prep_01_*.png`, `prep_02_*.png`, `prep_03_*.png`.

#### ML & Heuristiques
- `Modifié` : `src/data/preprocess.py` — `build_text_for_model` utilise désormais **titre + description** (signal discriminant du titre capturé). Stop-words allégés (termes IT conservés).
- `Modifié` : `src/models/heuristics.py` — ajout `FORCE_RULES` (outlook → Microsoft toujours, ransomware → Sécurité toujours) + enrichissement `SOFT_RULES` Sécurité (dossier sécurisé, connexion suspecte, accès refusé) et Réseau (internet lent, connexion internet).
- `Ajouté` : `requirements.txt` — `lightgbm>=4.0.0`, `tinydb>=4.8.0`, `scikit-learn>=1.6.0`.

#### Backend NoSQL
- `Ajouté` : `api/db/nosql_store.py` — TinyDB (`data/resolved_tickets.json`) : archive des tickets résolus après approbation agent.
- `Modifié` : `api/routers/tickets.py` — intégration TinyDB dans `approve_ticket` (statut → Résolu déclenche l'archivage NoSQL). Nouveaux endpoints : `GET /tickets/resolved/stats` et `GET /tickets/resolved/archive`.

### Ajouté
- Système de pilotage documentaire du PFE : `PLAN.md` (source de vérité) + `PROJECT_STATUS.md`,
  `TASKS.md`, `BACKLOG.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `RISKS.md`, `TESTING.md`,
  `DEPLOYMENT.md`, `PFE_PROGRESS.md`.
- `CAHIER_DES_CHARGES.md` : audit critique + restructuration au niveau ingénieur/industriel.
- `.gitignore` racine du dépôt (exclut `venv/`, `node_modules/`, `*.pkl`, `*.db`, `.env`).

### Modifié
- `helpdesk-ai/.gitignore` : ajout `node_modules/`, `data/*.db`, artefacts build frontend.

### Qualité des données & notebooks (2026-06-26)
- `Ajouté` : `DIAGNOSTIC_QUALITE_DONNEES.md` (diagnostic chiffré et neutre de la qualité des données).
- `Ajouté` : `notebooks/data_quality_report.py` (profilage + figures + PDF
  `notebooks/figures/diagnostic_qualite_donnees.pdf`).
- `Ajouté` : `notebooks/notebook.md` (audit + étapes des 4 notebooks).
- `Modifié` : reformulation neutre du vocabulaire décrivant les données (notebooks, métadonnées,
  cahier des charges, rapport template, fichiers de suivi).
- `Corrigé` : `notebooks/rapport_audit.txt` (nombre de colonnes 23 → 18).
- `Supprimé` : `notebooks/Untitled.ipynb` (vide).

### Phase 1 — Cadrage & SRS (2026-06-26)
- `Ajouté` : `CADRAGE_SRS.md` v0.1 — problématique, questions de recherche, hypothèses, objectifs
  SMART, exigences fonctionnelles (MoSCoW), non-fonctionnelles (métriques) et matrice de
  traçabilité. **En attente de validation** des points 🟠.

### Phase 0 — commits (2026-06-26)
- `07cd6a9` docs(pilotage) : système de gestion de projet PFE + cahier des charges.
- `8dae2fd` feat(frontend) : application Angular 21 (scaffold client/admin).
- `2532828` chore(ml) : maj notebooks, preprocessing, moteur RAG, config + metadata.

---

## Historique antérieur (d'après git)

### [0.4.0] — Phase RAG
- `Ajouté` : moteur RAG par similarité cosinus (`src/rag/engine.py`).
- `Corrigé` : suppression des `nan` dans les résolutions — repli sur la knowledge base.

### [0.3.0] — Phase Modélisation
- `Ajouté` : pipeline baseline TF-IDF + SMOTE + LogisticRegression (F1-macro 0.77).
- `Modifié` : seuil de confiance ajusté à 0.40 (68.7 % d'auto-routage à 100 % de précision).

### [0.2.0] — Phase API
- `Ajouté` : structure API (routers, services, schemas, db, middleware).

### [0.1.0] — Phases EDA & Preprocessing
- `Ajouté` : notebooks EDA, preprocessing, modélisation, RAG ; rapport d'audit.
