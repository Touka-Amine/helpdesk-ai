# Cycle de vie MLOps — HelpDesk AI

Ce document décrit les deux boucles d'amélioration du système, ce qu'elles font,
ce qu'elles refusent de faire, et ce qu'elles ne savent pas mesurer.

Il décrit le code réellement présent dans le dépôt. Quand une capacité n'existe
pas encore ou dépend d'une donnée que le système ne collecte pas, c'est écrit.

---

## 1. Vue d'ensemble

Deux boucles partent du même point, les tickets validés par un administrateur dans
PostgreSQL, et ne se rejoignent jamais.

```
                    PostgreSQL — vérité métier
                    tickets + ticket_history
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
   BOUCLE CLASSIFICATION            BOUCLE CONNAISSANCE
   collect.py                       quality.py
   build_dataset.py                 vector_store.py
   train.py        → candidat       snapshot.py
   promote.py      → PORTE          rag_eval.py
   registry        → production     rag_monitor.py
            │                               │
            ▼                               ▼
   models/best_pipeline.pkl          ChromaDB resolved_tickets
```

**Frontières que rien ne franchit.** ChromaDB ne devient jamais un jeu
d'entraînement. Le dataset ML ne devient jamais une base de connaissances. Un même
ticket validé alimente les deux, avec deux traitements différents : vers le ML il
devient `(text_clean, Catégorie, poids)`, vers le RAG il devient
`(embedding, solution, métadonnées)`.

---

## 2. Les sept états d'une donnée

| État | Où | Qui le produit |
|---|---|---|
| collectée | `tickets` dans PostgreSQL | l'application |
| éligible | filtre de `collect.py` | statut résolu, approbateur, description exploitable |
| validée | `data/curated/validated_*.csv` | filtre sur la force de l'étiquette |
| utilisée pour l'entraînement | `data/splits/train_current.csv` | `build_dataset.py` |
| modèle entraîné | `models/candidate_pipeline.pkl` | `train.py` |
| modèle évalué | `metrics/ml_eval_candidate.json` | `train.py`, sur le jeu de test gelé |
| modèle en production | `models/best_pipeline.pkl` | `promote.py`, et lui seul |

---

## 3. Boucle 1 — Classification

### 3.1 La force de l'étiquette

Un ticket « validé » ne porte pas forcément une étiquette fiable. `collect.py` en
distingue trois qualités, déduites de `ticket_history` :

| Force | Détection | Poids | Ce que ça vaut |
|---|---|---|---|
| `corrected` | un admin a changé `categorie_finale` (`changed_by` renseigné) | 1.0 | un expert a tranché |
| `confirmed` | un admin a traité le ticket sans toucher la catégorie | 0.7 | il l'a vue et ne l'a pas contestée |
| `weak` | résolu sans admin identifiable | 0.3, **exclu par défaut** | rien ne prouve qu'un humain ait regardé |

Sans cette distinction, réentraîner sur « les tickets validés » revient largement à
réentraîner le modèle sur ses propres sorties. La boucle amplifierait ses erreurs
au lieu de les corriger. C'est le piège principal de tout apprentissage continu, et
`collect.include_weak_labels` vaut `false` pour cette raison.

### 3.2 Le jeu de test gelé

`data/reference/test_reference.csv`, protégé par une empreinte SHA-256 vérifiée à
chaque exécution de `split.py`.

Avant cette version, `dvc repro` regénérait `test.csv` à chaque passage. Dès que
des tickets de production enrichissent le corpus, le jeu de test change à chaque
itération, et comparer la F1-macro du modèle v2 à celle du v1 ne mesure plus rien.
La porte de promotion deviendrait arbitraire.

Créer une référence v2 est une décision explicite : supprimer le manifeste, changer
`split.strategy`, relancer. Le manifeste garde trace de ce qui a été gelé et quand.

**Limite connue et assumée.** La référence actuelle ne couvre que 5 catégories sur
8. `Applicatifs`, `Backup` et `Communication` n'ont aucun ticket de test, leur F1
vaut 0.0 par construction. C'est pourquoi la métrique de décision est
`f1_macro_classes_evaluables`, calculée sur les seules classes ayant du support.
Sur le corpus actuel : 0.6995 sur 5 classes, contre 0.5829 pour la macro complète (valeurs postérieures à l'audit des règles du 2026-08-22).
Basculer `split.strategy` sur `stratified_group` corrigerait ce défaut au prix d'un
changement de la référence publiée.

### 3.3 Anti-fuite

`build_dataset.py` écarte toute ligne de production qui porterait un titre du jeu de
test, ou une description identique après normalisation. Les tickets de production
ont des titres libres, saisis par le client : rien ne garantit qu'ils ne recopient
pas un scénario de test.

**Ce qui n'est pas détecté** : une paraphrase sémantique d'un ticket de test. La
détecter demanderait d'encoder le jeu de test à chaque construction, et exposer le
jeu de test au processus de sélection est précisément ce qu'un jeu gelé cherche à
éviter.

### 3.4 Déclenchement du réentraînement

`src/monitoring/ml_monitor.py` **écrit un rapport, ne lance rien**. La décision
reste humaine. Il n'y a aucun ordonnanceur dans le projet, et c'est délibéré.

| Déclencheur | Seuil | Pourquoi cette valeur |
|---|---|---|
| nouveaux tickets validés | ≥ 150 | réparti sur 8 classes, en dessous l'apport par classe reste sous le bruit d'échantillonnage du test à 356 lignes |
| gain sur une classe minoritaire | ≥ 30 | +30 sur `Sécurité` (73 tickets) est un gain de 40 %, détectable |
| hausse du désaccord ML/humain | référence + 10 pts | dégradation mesurée en production |
| verrou | 1 par semaine max | empêche le cas dégénéré même si les seuils sont mal calibrés |

Le déclencheur de désaccord reste **inactif** tant que
`monitoring.disagreement_baseline` vaut `null`. Conclure à une dérive sans point de
comparaison serait une invention. Fixez ce référentiel après une première période
d'exploitation.

### 3.5 La porte de promotion

`promote.py` est le seul script qui écrit `models/best_pipeline.pkl`.

Les deux modèles sont **réévalués dans la même exécution** sur le même jeu de test.
Comparer deux chiffres calculés sur deux jeux différents ne veut rien dire.

| Porte | Règle |
|---|---|
| métrique principale | gain ≥ `promotion.min_improvement` (0.005) |
| régression par classe | aucune classe avec support ne perd plus de 0.05 |
| accuracy | ne régresse pas |

La deuxième porte existe pour un cas précis : une F1-macro peut progresser
globalement pendant qu'une classe minoritaire s'effondre.

En cas de rejet, l'artefact de production est **restauré** depuis le registre. DVC
supprime les sorties d'un stage avant de l'exécuter ; sans cette restauration,
`models/best_pipeline.pkl` serait absent après un rejet et l'API ne démarrerait plus.

**Le stage est idempotent.** Relancé sans nouveau candidat, il restaure la production
et sort en succès plutôt qu'en erreur. Sortir en erreur laissait l'artefact servi
absent, puisque DVC l'avait déjà supprimé, alors même que le registre en détenait une
copie intacte : l'application ne démarrait plus. Il n'échoue que dans un cas, un dépôt
sans aucun modèle ni candidat, où il n'y a effectivement rien à restaurer.

**Une métrique manquante interrompt l'arbitrage.** Si la métrique de décision est
absente des métriques de l'un des deux modèles, la comparaison lève une erreur au lieu
de la lire comme un zéro. Sans ce contrôle, un modèle de production dont la métrique
serait absente vaudrait 0.0 et tout candidat gagnerait par défaut, soit l'inverse exact
de ce que cette porte protège.

### 3.6 Le registre et le rollback

`models/registry/` contient l'index, et pour chaque version le pipeline figé, ses
métadonnées, ses métriques et son lineage.

```bash
python src/pipeline/promote.py --list
```

```bash
python src/pipeline/promote.py --rollback 2 --reason "régression constatée"
```

**Pourquoi un registre dans le dépôt plutôt que celui de MLflow.** Le Model
Registry de MLflow fonctionne avec le store `file:./mlruns` du projet, vérifié à
l'exécution : une version y est bien créée. Mais MLflow 3.6 le déclare déprécié et
annonce son retrait au profit d'un backend SQL. Faire reposer la promotion et le
rollback dessus adosserait une fonction critique à une API en fin de vie, et migrer
vers SQLite orphelinerait les 53 runs existants.

`promote.py` enregistre **en plus** dans MLflow quand c'est possible, sans que son
échec ne bloque quoi que ce soit. Pour basculer sur un backend SQL :

```bash
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
```

`models/registry/` n'est la sortie d'aucun stage DVC, délibérément : DVC l'effacerait
à chaque `dvc repro promote` et le projet perdrait tout son historique de versions.

### 3.7 Rechargement sans redémarrage

Une promotion écrit `models/registry/PRODUCTION`. Chaque worker uvicorn compare ce
pointeur au modèle qu'il a en mémoire, au plus une fois toutes les 30 secondes, et
se recharge seul s'il est en retard. `POST /api/v1/admin/model/reload` force
l'opération sur le worker qui traite l'appel.

---

## 4. Boucle 2 — Cycle de vie des connaissances

### 4.1 Le contrôle qualité

`src/knowledge/quality.py`, point de passage obligé entre « un ticket a été résolu »
et « cette résolution devient une référence ».

| Contrôle | Règle |
|---|---|
| `solution_presente` | une connaissance sans solution n'apprend rien |
| `longueur_minimale` | ≥ 4 mots. « ok », « fait » ne sont pas des connaissances |
| `origine_humaine` | la solution doit venir d'un humain |
| `non_recopie` | ≤ 90 % de vocabulaire commun avec la description |
| `doublon_proche` | ≥ 0.95 de similarité déclenche une mise à jour, pas un rejet |

**Le défaut corrigé.** L'archivage faisait auparavant
`solution = commentaire_admin or solution_rag or ""`. Quand un administrateur
clôturait sans écrire de commentaire et que le score RAG dépassait le seuil de
nouveauté, c'est la **suggestion de l'IA, jamais relue**, qui entrait dans la base.
Elle devenait ensuite une source pour les tickets suivants, dont les résolutions
étaient à leur tour archivées. Le RAG se nourrissait de ses propres sorties.

L'origine est maintenant déclarée (`source_solution` vaut `admin` ou `ia`) et le
contrôle refuse la seconde. Un rejet n'efface rien : le ticket reste dans
PostgreSQL, seule son entrée dans la base vectorielle est refusée.

### 4.2 Statuts

| Statut | Effet |
|---|---|
| `actif` | proposé par le RAG |
| `superseded` | remplacé par une connaissance quasi identique plus récente |
| `obsolete` | signalé par le monitoring |

Rien n'est jamais supprimé automatiquement : une procédure ancienne peut rester la
bonne. Le filtrage se fait en Python après la requête, pas dans la clause `where` de
Chroma, parce que les entrées écrites avant l'introduction de ce champ n'ont pas de
`statut` et qu'un filtre côté base les exclurait silencieusement.

### 4.3 Versionnement

ChromaDB n'a pas de notion de version. `src/knowledge/snapshot.py` en exporte un
instantané horodaté en JSON Lines, versionnable par DVC.

```bash
python src/knowledge/snapshot.py
python src/knowledge/snapshot.py --diff last
```

Cela permet de savoir ce que la base contenait à une date donnée, donc
d'interpréter une évaluation passée, et de reconstruire la collection si le volume
Docker est perdu.

### 4.4 Évaluation

`src/pipeline/rag_eval.py`, deux protocoles.

**annoté** — la pertinence est désignée par un administrateur. Seul protocole qui
autorise à parler de rappel.

```bash
python src/pipeline/rag_eval.py --build-template --n-queries 80
```

Produit `data/knowledge/rag_eval_set.json` : 80 requêtes issues du jeu de test, avec
pour chacune les dix meilleurs candidats du moteur. Un administrateur ne garde dans
`pertinents` que les solutions qui auraient réellement aidé. Compter environ une
demi-journée.

**proxy** — à défaut d'annotation, est pertinent tout ticket de la même catégorie.

Ce protocole a un défaut structurel. `Microsoft` compte plusieurs centaines de
tickets, donc plusieurs centaines de « pertinents ». Un rappel@3 y vaut
mécaniquement 3/300 quelle que soit la qualité du moteur. Le `recall_at_3` de
**0.0277** qui figurait dans `metrics/rag_eval.json` est un artefact du protocole,
pas une mesure du système. En mode proxy, le rappel est donc laissé à `null`.
Afficher un chiffre connu comme non interprétable serait le fabriquer.

L'évaluation interroge les moteurs avec `allow_fallback=True`, la valeur utilisée en
production. Le taux de repli est rapporté à part : il distingue « le moteur a
répondu » de « le moteur a trouvé quelque chose au-dessus du seuil de pertinence ».

---

## 5. Monitoring

### 5.1 Mesurable avec les données existantes

**Modèle**
- taux de désaccord ML/humain — `categorie_predite != categorie_finale` sur les
  tickets validés. Meilleur indicateur disponible de la performance réelle
- distribution des catégories, comparée au corpus d'entraînement (PSI)
- distribution des confiances
- taux d'application des heuristiques et règles déclenchées
- dérive lexicale — part des mots de production absents du vocabulaire TF-IDF. Ces
  mots sont littéralement invisibles pour le modèle
- performance par version de modèle

**RAG**
- distribution des `rag_score`, taux de nouveauté
- `feedback_vote` des utilisateurs
- rejet implicite — part des tickets où la solution écrite par l'admin diffère de la
  suggestion. L'admin a vu la suggestion et a écrit autre chose
- volume, statuts, quasi-doublons, ancienneté, qualité entrante

### 5.2 Non mesurable, et qui ne doit pas être inventé

- **La F1 réelle en production.** Sur les tickets où l'admin n'a pas touché à la
  catégorie, l'étiquette est une confirmation par omission. Le taux de désaccord en
  est un minorant, pas un équivalent.
- **Quelle recommandation parmi les trois l'admin a utilisée.** Aucun événement de
  clic ou de sélection n'est journalisé.
- **Les contradictions entre connaissances.** Seuls les quasi-doublons sont
  détectés, ce qui est différent.
- **La dérive sémantique** au-delà du vocabulaire : les embeddings des tickets de
  production ne sont pas conservés.
- **Le taux d'heuristiques avant l'instrumentation** : la colonne n'existait pas.

---

## 6. Commandes

```bash
python src/monitoring/ml_monitor.py
```

```bash
python src/pipeline/collect.py
```

```bash
dvc repro
```

```bash
python src/pipeline/promote.py --list
```

```bash
python src/knowledge/snapshot.py
```

```bash
python scripts/mlops_e2e_demo.py
```

### Endpoints d'administration, en lecture seule

| Route | Contenu |
|---|---|
| `GET /api/v1/admin/registry` | versions, alias, historique des décisions |
| `GET /api/v1/admin/promotion-decision` | dernière décision, porte par porte |
| `GET /api/v1/admin/monitoring/ml` | rapport du moniteur ML |
| `GET /api/v1/admin/monitoring/rag` | rapport du moniteur RAG |
| `GET /api/v1/admin/monitoring/retrain-trigger` | état des déclencheurs |
| `GET /api/v1/admin/monitoring/rag-eval` | dernière évaluation RAG |
| `POST /api/v1/admin/model/reload` | applique une promotion sans redémarrer |

Aucun endpoint ne lance d'entraînement ni ne promeut de modèle. Ces opérations
passent par le pipeline DVC, hors de l'API, pour rester tracées et volontaires.

---

## 7. Ce que le pipeline DVC ne contient pas, et pourquoi

`src/pipeline/collect.py` lit PostgreSQL, dont l'état ne peut pas être haché par
DVC. En faire un stage avec `data/curated` en sortie serait pire que l'omettre :
DVC supprime les sorties d'un stage avant de l'exécuter, ce qui effacerait
l'historique des lots collectés.

`src/monitoring/*.py` lisent la production, pas le corpus. Ils rapportent, ils ne
transforment rien.

`models/registry/` n'est la sortie d'aucun stage, pour la même raison. C'est ce qui en
fait le **journal de référence des décisions** : `metrics/promotion_decision.json` ne
porte que la dernière décision et disparaît à chaque `dvc repro`, tandis que
l'historique du registre conserve chaque promotion, chaque rejet et chaque rollback
avec son motif. Le verrou anti-réentraînement de `ml_monitor.py` lit donc cet
historique, et non le fichier de métrique.

---

## 8. Points restant à traiter

1. **Aucun trafic de production.** La base historique contient 5 tickets de test.
   Les deux boucles sont fonctionnelles et testées, mais aucune n'a encore de
   données réelles à traiter. Les seuils de `params.yaml` sont des points de départ
   à calibrer sur le volume observé.
2. **`monitoring.disagreement_baseline` vaut `null`.** À fixer après une première
   période d'exploitation.
3. **Le jeu annoté du RAG n'existe pas.** Tant qu'il manque, les métriques de
   pertinence restent indicatives.
4. **La référence de test ne couvre que 5 catégories sur 8.** Décision à prendre :
   la garder, ou basculer sur `stratified_group` et republier les chiffres.
5. **Données personnelles.** `collect.py` n'exporte pas le champ `Demandeur`, mais
   les descriptions peuvent contenir des noms. L'anonymisation n'est pas traitée.
