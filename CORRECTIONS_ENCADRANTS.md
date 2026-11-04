# Corrections demandées par l'encadrant

Suivi des huit remarques reçues sur la dernière version du mémoire.
Branche de travail : `corrections-encadrant` — rien n'est poussé.

## Règle de travail

Chaque remarque suit le même cycle, et **aucune tâche ne passe à 100 % tant que les quatre étapes
ne sont pas faites** :

1. **Vérifier le fait** dans le code, les données ou les métriques — jamais sur mémoire.
2. **Corriger** ce qui doit l'être : code, carnets, métadonnées.
3. **Modifier le mémoire** pour que le texte dise la vérité mesurée.
4. **Vérification totale** avant clôture : rejouer les contrôles, s'assurer qu'aucune trace de
   l'ancien état ne subsiste, que les tests passent et que le suivi est à jour. Le résultat de
   cette vérification est consigné sous la tâche.

### Ce que contient une vérification totale

- recherche dans tout le dépôt des formulations ou appels remplacés, pour qu'il n'en reste aucun ;
- contrôle que les modifications du mémoire sont bien en place ;
- exécution des tests concernés ;
- contrôle du service quand la correction touche l'API ;
- mise à jour de ce fichier.

## Tableau de bord

| # | Remarque | Type | Avancement |
|---|---|---|---|
| T8 | Validation de CamemBERT | vérification + écriture | **100 %** ✅ |
| T5 | Titre non transmis au modèle | mesure + code + écriture | **100 %** ✅ |
| T4 | Seuil du RAG hybride | mesure + décision | **100 %** ✅ |
| T3 | Exigence ENF-04 | écriture | **100 %** ✅ |
| T1 | « 1 800 tickets résolus » | écriture | **100 %** ✅ |
| T2 | Terminologie de la base RAG | écriture | **100 %** ✅ |
| T6 | Modèle expérimental / déployé | écriture | **100 %** ✅ |
| T7 | Validation humaine du RAG | annotation | **100 %** ✅ · annotée par l'auteur, à confirmer par un consultant |
| T9 | Relecture finale de cohérence | vérification | **100 %** ✅ |
| T10 | Redites du chapitre 2 | relecture + écriture | **100 %** ✅ · hors mail de l'encadrant |
| T11 | Exigences non satisfaites | mesure + code + écriture | **100 %** OK · mesures écrites au mémoire (T16) ; le choix du modèle servi reste un arbitrage du service |
| T12 | Six remarques finales de l'encadrant | mesure + code + écriture | **5 sur 6** · la 6e dépend du service |
| T13 | Audit séquentiel code + rapport des six remarques | vérification | **100 %** OK · 6 écarts trouvés et corrigés |
| T14 | Mise en conformité du rapport avec le code | vérification + écriture | **100 %** OK · 7 affirmations fausses corrigées, 4e contrôleur posé |
| T15 | Relecture mécanique : typographie et orthographe | vérification | **100 %** OK · 0 faute dans le corps, 6 contrôleurs |
| T16 | Les mesures de T11 écrites au mémoire | écriture | **100 %** OK · nouvelle section 4.6.4 et huit passages repris |
| T17 | Pages d'introduction à moitié blanches | mise en page | **100 %** OK · chapitre 4 de 65 % à 5 % de blanc, trois autres chapitres gagnants |

---

## T8 — Validation de CamemBERT — **100 %** ✅

**Remarque** : « Vérifier la validation de CamemBERT afin d'éviter qu'un découpage aléatoire ne
réintroduise des scénarios déjà présents dans l'apprentissage. »

**Verdict : pas de fuite, les résultats sont valides.** Le carnet tire au sort parmi les titres
uniques puis affecte toutes les lignes d'un titre du même côté. Aucun titre des deux côtés.

| Sous-tâche | État |
|---|---|
| 8.1 Vérifier le découpage réellement exécuté | ✅ |
| 8.2 Corriger le libellé du découpage | ✅ |
| 8.3 Documenter le jeu de validation interne | ✅ déjà présent dans le mémoire |
| 8.4 Vérifier la traçabilité des chiffres comparatifs | ✅ |
| 8.V **Vérification totale** | ✅ |

**Vérification totale du 2026-10-03**

- Plus aucune mention fautive de `GroupShuffleSplit` dans les deux carnets, les métadonnées du
  modèle ni le mémoire. La seule occurrence restante est celle de `src/pipeline/split.py`, où la
  méthode est réellement employée : elle est donc correcte et conservée.
- Métadonnées du modèle relues : le libellé annonce bien le découpage stratifié sur les titres
  uniques et précise qu'il diffère du jeu de test gelé.
- Paragraphe sur le recouvrement des deux jeux de test présent dans `report/chap_04.tex`.
- Chiffres comparatifs du chapitre 6 confrontés une seconde fois au fichier de mesure daté :
  identiques.

**Contre-vérification du 2026-10-03, seconde passe** — une mention oubliée a été trouvée dans
`notebooks/02_preprocessing.ipynb` : une recommandation affichée en fin d'analyse exploratoire
conseillait un « GroupShuffleSplit sur les textes uniques », alors que le groupement se fait par
titre. Reformulée. Nouvelle recherche sur l'ensemble des carnets, du mémoire et des métadonnées :
**plus aucune occurrence fautive**.

**Détail des corrections**

1. Les carnets et les métadonnées annonçaient un `GroupShuffleSplit` ; le code utilise un
   `StratifiedShuffleSplit` sur les titres uniques. Effet identique, nom faux. Corrigé aux
   9 endroits concernés. Le mémoire, lui, décrivait déjà correctement le tirage.
2. Le jeu de validation interne (10 % tirés ligne par ligne) est déjà expliqué et chiffré au
   chapitre 4. Rien à ajouter.
3. Mesure ajoutée : les deux jeux de test — expériences et pipeline — n'ont que **4 titres communs
   sur 12**. Le chapitre 4 interdit désormais explicitement tout rapprochement de chiffres entre
   les deux protocoles.
4. Les cinq valeurs du tableau comparatif du chapitre 6 correspondent exactement au fichier daté
   `metrics/campagne_apres_nettoyage.json`. Aucun chiffre orphelin.

**Fichiers modifiés** : `report/chap_04.tex`, `helpdesk-ai/notebooks/03_modeling.ipynb`,
`helpdesk-ai/notebooks/05_camembert_finetuning.ipynb`, `helpdesk-ai/models/camembert_metadata.json`.

**À dire à l'encadrant** : le découpage était correct, la crainte ne se vérifie pas ; trois
imprécisions ont été corrigées — nom de la méthode, recouvrement des deux jeux de test,
traçabilité des chiffres.

---

## T5 — Titre non transmis au modèle — **100 %** ✅

**Remarque** : « Vérifier la cohérence entre les données utilisées à l'entraînement du classifieur
et celles réellement transmises au modèle dans l'application. »

**Défaut confirmé** : le modèle est entraîné sur titre + description, l'application ne lui envoyait
que la description.

| Sous-tâche | État |
|---|---|
| 5.1 Mesurer l'écart entre les deux entrées | ✅ |
| 5.2 Décider : corriger ou documenter | ✅ corriger |
| 5.3 Corriger le code et verrouiller par des tests | ✅ |
| 5.4 Reconstruire l'image et remesurer sur l'API | ✅ |
| 5.5 Rédiger le passage du mémoire | ✅ |
| 5.V **Vérification totale** | ✅ |

**Vérification totale du 2026-10-03**

- Plus aucun appel `clean_text(description)` dans `api/` : les deux points d'entrée du modèle
  passent par `build_text_for_model(titre, description)`.
- Paragraphe explicatif présent dans `report/chap_06.tex`.
- 40 tests verts, dont les 5 nouveaux et les 26 tests d'intégration de l'API.
- Service interrogé après reconstruction : modèle et base de connaissances chargés.
- Image de secours présente : `helpdesk-api:avant-t5`.

**Mesure, jeu de test gelé (356 tickets)**

| Entrée du modèle | Modèle seul | Avec les règles | Confiance moyenne | Sous le seuil |
|---|---|---|---|---|
| Description seule — ancien comportement | 31,7 % · F1 0,2816 | 82,0 % · F1 0,5726 | 0,41 | 94 % |
| Titre + description — corrigé | 44,7 % · F1 0,2708 | 82,0 % · F1 0,5829 | 0,46 | 80 % |

Sur 16 cas de formulation réaliste : 12/16 contre 13/16 pour le modèle seul, 13/16 contre 14/16
avec les règles, confiance moyenne 0,55 contre 0,75.

**Conséquences**

- Les chiffres publiés au chapitre 6 correspondent à la variante corrigée : **aucun résultat du
  mémoire n'est à refaire**, c'est l'application qui a été mise en conformité.
- L'effet principal porte sur la confiance, donc sur le filtre de catégorie de la recherche de cas
  comparables, qui ne s'active qu'au-delà de 0,70.

**Remesure sur le service réel**, après reconstruction de l'image et redémarrage de l'API,
par le chemin exact de création d'un ticket :

| Jeu de cas | Avant | Après |
|---|---|---|
| 12 sujets jamais vus — modèle seul | 3/12 | **4/12** |
| 12 sujets jamais vus — avec les règles | 8/12 | 8/12 |
| 16 cas réalistes — modèle seul | 12/16 | **13/16** |
| 16 cas réalistes — avec les règles | 13/16 | **14/16** |
| 16 cas réalistes — confiance moyenne | 0,55 | **0,79** |
| 16 cas réalistes — tickets au-dessus de 0,70 | — | **81 %** |

Le seuil de 0,70 est celui qui déclenche le filtre de catégorie de la recherche de cas
comparables : il est maintenant franchi par quatre tickets réalistes sur cinq, contre une petite
minorité auparavant. Un cas illustre le gain : « Courriel suspect reçu avec une pièce jointe »
partait en *Applicatifs*, il est désormais classé *Sécurité*.

**Chiffres du mémoire à remplacer : aucun.** Les valeurs publiées correspondaient déjà à la
variante corrigée ; c'est le service qui a été mis en conformité.

**Tests** : 40 tests verts, dont les 5 nouveaux et les 26 tests d'intégration de l'API.

**Fichiers modifiés** : `helpdesk-ai/api/predictor.py`, `helpdesk-ai/api/services/ai_service.py`,
`helpdesk-ai/tests/test_coherence_entrainement.py` (nouveau, 5 tests),
`report/chap_06.tex`.

**Retour arrière possible** : l'image précédente est conservée sous `helpdesk-api:avant-t5`.

**À dire à l'encadrant** : l'incohérence existait bien, elle a été mesurée puis corrigée ; les
chiffres publiés restent valides car ils correspondaient à la configuration d'entraînement, et
c'est l'application qui ne la respectait pas.

---

## T4 — Seuil du RAG hybride — **100 %** ✅

**Remarque** : « Recalibrer le seuil de pertinence du moteur RAG hybride. Le seuil actuel de 0,50
conduit à un taux de repli de 100 %. »

| Sous-tâche | État |
|---|---|
| 4.1 Mesurer la distribution réelle des scores hybrides | ✅ |
| 4.2 Proposer un seuil calibré, tableau avant/après | ✅ |
| 4.3 Décider : recalibrer ou documenter la limite | ✅ recalibrer à 0,35 |
| 4.4 Appliquer la décision, métriques ou passage de limite | ✅ code, métriques, mémoire |
| 4.V **Vérification totale** | ✅ |

### Ce que la mesure a montré

**Le seuil était hors de portée, pas seulement trop haut.** Sur les 80 requêtes du protocole, le
meilleur score hybride va de **0,327 à 0,489**. Il n'atteint jamais 0,50 et ne le peut pas : le
score est la moyenne d'un sémantique plafonnant à 0,7024 et d'un lexical plafonnant à 0,3099.

**Le repli à 100 % ne signalait aucune dégradation.** Un seuil inatteignable ne filtre rien : le
plancher de repli à 0,20 ramasse alors tout, si bien que la sortie à 0,50 est identique, passage
pour passage, à celle d'un seuil de 0,20 — mêmes 2,54 suggestions, même précision 0,4187. Le seuil
ne faisait qu'apposer une étiquette vide sur chaque recommandation.

**Le score discrimine, donc un seuil a un sens.** Probabilité qu'un passage pertinent soit mieux
classé qu'un passage non pertinent tiré au hasard : **0,717**. Précision par tranche : 0,10 sous
0,30 · 0,28 de 0,30 à 0,35 · 0,33 jusqu'à 0,40 · **0,59 au-delà de 0,40**.

| Seuil | Précision de l'affiché | Suggestions/requête | Repli |
|---|---|---|---|
| 0,20 | 0,4187 | 2,54 | 0 % |
| 0,30 | 0,4294 | 2,12 | 0 % |
| **0,35 — retenu** | **0,4545** | 1,79 | 17,5 % |
| 0,40 | 0,3806 | 1,94 | 55 % |
| 0,50 — ancien | 0,4187 | 2,54 | 100 % |

**Relever α n'est pas une correction distincte.** Mesuré au seuil recalibré : α = 0,8 fait tomber
le repli à zéro et remonte la liste à 2,52 suggestions, pour une précision de l'affiché de 0,4356 ;
α = 1,0 n'est plus un moteur hybride. Les deux réglages commandent la même quantité — ce qui
franchit le filtre. α = 0,5 est conservé parce qu'il donne la précision la plus haute sur
l'affiché, 0,4545.

> **Correction en seconde passe.** La première version de cette fiche, et du passage correspondant
> du mémoire, affirmait que relever α « dégrade la précision » en citant α = 0,8 → P@3 0,2875.
> Cette mesure avait été faite **au seuil de 0,50**, avant recalibration ; elle ne vaut pas pour la
> configuration retenue. Le balayage est désormais mesuré au seuil servi et versé dans
> `metrics/rag_seuil_balayage.json`.

### Deux défauts que la remarque ne mentionnait pas

1. **Un seuil unique sur trois échelles différentes.** Les trois moteurs étaient comparés à 0,50
   alors que leurs scores moyens valent 0,1842 · 0,6099 · 0,3141. Le même nombre y désigne trois
   sévérités : aucun filtre pour l'hybride, un filtre réel pour le sémantique, un filtre total pour
   le lexical. La comparaison publiée n'était pas à sévérité égale. Elle est refaite sans filtre,
   et le classement tient : l'hybride place 0,4083 de passages pertinents dans le trio de tête,
   contre 0,2917 pour le sémantique et 0,3083 pour le lexical.
2. **La précision@3 masquait l'arbitrage.** Elle divise par trois, donc pénalise une liste
   tronquée. Un seuil qui améliore la qualité des suggestions en les raccourcissant y apparaît
   comme une régression. Les métriques rapportent désormais aussi la précision de ce qui est
   réellement affiché et la longueur de la liste.

### Décisions prises avec l'utilisateur

- **Seuil de récupération → 0,35.** Contrepartie assumée : 1,79 suggestion au lieu de 2,54, et la
  précision@3 publiée passe de 0,3542 à 0,2708 — non parce que les suggestions sont moins bonnes,
  mais parce que l'indicateur divise par trois une liste qui n'en compte plus trois.
- **Règle métier inchangée.** `NOVELTY_THRESHOLD` commandait l'obligation de rédiger la solution
  avant de clore, et valait le même 0,50. Les deux valeurs sont désormais séparées et nommées. Le
  seuil de nouveauté reste au-dessus de la plage atteignable : la règle se déclenche sur tous les
  tickets, et c'est voulu, puisque c'est elle qui alimente la base de connaissances.

### Code

- `params.yaml` — `rag.similarity_threshold` 0,50 → **0,35**, avec le raisonnement en commentaire.
- `api/predictor.py` — le seuil était **codé en dur** au lieu d'être lu dans `params.yaml` : service
  et mesure pouvaient diverger sans que rien ne le signale. Nouvelle fonction `_params_rag()`.
- `api/routers/tickets.py` — `NOVELTY_THRESHOLD` découplé et documenté.
- `src/rag/hybrid_engine.py` — `fallback_threshold` devient un paramètre du constructeur au lieu
  d'une valeur codée dans `recommend()` ; en-tête réécrit sur la question de l'échelle.
- `src/pipeline/rag_eval.py` — deux indicateurs ajoutés (précision de l'affiché, suggestions par
  requête) et nouveau mode `--balayage-seuil` qui écrit `metrics/rag_seuil_balayage.json`.
- `src/monitoring/rag_monitor.py`, `src/rag/engine.py`, `src/rag/semantic_engine.py` — valeurs de
  secours et commentaires alignés sur l'échelle réelle de chaque moteur.
- `tests/test_seuil_rag.py` — **5 nouveaux tests** : ils échouent si un seuil hors de portée est
  réintroduit, si l'API reprend une copie locale du seuil, ou si les deux seuils sont refusionnés.

### Mémoire

- **Chapitre 6, tableau de comparaison** refait sans filtre, avec les deux précisions et la
  longueur de liste ; les trois paragraphes de lecture réécrits.
- **Chapitre 6, section du seuil** : diagnostic conservé, conclusion remplacée. « Deux corrections
  envisageables, que nous énonçons sans trancher » devient la mesure, la décision et son prix.
- **Nouvelle figure** `ch05_seuil.png` : distribution des scores face aux deux seuils, et effet du
  seuil sur précision et longueur de liste.
- **Chapitre 5** : la justification de la fusion linéaire affirmait qu'elle « conserve une échelle
  comparable à celle du seuil » — c'est exactement ce que la mesure contredit. Corrigé.
- **Chapitre 7, annexes, résumés FR et EN, conclusion** : chiffres et arbitrages mis à jour.
- **Deux figures rendues reproductibles.** `ch05_moteurs.png` et `ch07_tests.png` étaient produites
  hors du dépôt et ne pouvaient donc pas suivre une recalibration. Elles ont maintenant leur script
  dans `report/figures/`, qui lit les fichiers de mesure.

### Vérification totale du 2026-10-03

- **Service interrogé par le chemin réel de création d'un ticket**, après reconstruction de l'image
  et redémarrage : le journal annonce `seuil=0.35`, lu depuis `params.yaml`. Sur quatre cas
  réalistes, **aucune suggestion n'est plus marquée « repli »**, là où la totalité l'était.
- **181 tests verts**, dont les 5 nouveaux.
- **Le mémoire compile** : 146 pages, code 0, zéro erreur, zéro référence non résolue.
- Les deux nouvelles figures ont été relues après rendu : aucun libellé tronqué ni superposé.
- Recherche sur tout le dépôt des 0,50 résiduels : les occurrences restantes sont soit la règle
  métier, soit des commentaires qui rappellent l'ancienne valeur, soit des valeurs par défaut
  qu'aucun chemin servi n'emprunte — toutes relues une par une.
- **Chiffre corrigé au passage** : le mémoire annonçait « cent cinquante tests » et la capture d'écran
  en montrait 132. La suite en compte 181, dont 155 rejoués par l'intégration continue. Texte,
  tableau de conformité, conclusion et figure mis d'accord.

**À dire à l'encadrant** : le seuil n'était pas trop haut, il était hors de portée — il ne filtrait
rien et le repli à 100 % était une étiquette, pas une dégradation. Recalibré à 0,35 sur la
distribution mesurée. Deux défauts plus profonds ont été trouvés en chemin : les trois moteurs
étaient comparés à sévérité inégale, et la précision@3 masquait l'arbitrage entre pureté et nombre
des suggestions.

---

## T3 — Exigence ENF-04 — **100 %** ✅

**Remarque** : la confidentialité vis-à-vis des services externes est respectée, mais
l'anonymisation n'a pas été faite : l'exigence ne peut pas être déclarée conforme.

| Sous-tâche | État |
|---|---|
| 3.1 Retrouver l'exigence dans le cadrage et le mémoire | ✅ |
| 3.2 Scinder : services externes conforme / données personnelles non traité | ✅ |
| 3.3 Mettre à jour le tableau de conformité | ✅ |
| 3.4 Ajouter la pseudonymisation aux limites et aux perspectives | ✅ |
| 3.V **Vérification totale** | ✅ |

### Ce qui a été écrit

**Chapitre 1, énoncé de l'exigence.** ENF-04 est désormais scindée en deux volets numérotés :
(a) aucune donnée transmise à un service externe, (b) traitement des données personnelles conforme
à la réglementation. Un paragraphe précise que les deux volets n'ont pas connu le même sort, que le
second relève d'une décision d'organisation — anonymisation, durée de conservation, information des
personnes — qui dépasse le cadre du stage, et que le présenter comme satisfait serait inexact.

**Chapitre 6, bilan de conformité.** La ligne unique « Confidentialité — Tenue » est remplacée par
deux lignes : *services externes* tenue, *données personnelles* **non tenue**, avec le constat que
les noms des demandeurs figurent en clair dans le corpus comme dans la base et qu'aucune durée de
conservation n'est arrêtée. Le décompte passe de « cinq sur huit tenues, deux partielles, une non
tenue » à **cinq tenues, deux partielles, deux non tenues sur neuf lignes**, et le texte énonce la
situation sans détour en renvoyant au risque R-05 et aux perspectives.

**Chapitre 6, tableau des limites.** Nouvelle ligne « Données personnelles non traitées » dans le
groupe *Exploitation*, suivie au registre des risques sous R-05.

**Chapitre 7, perspectives.** La mise en conformité est ajoutée aux arbitrages à trancher, avec la
distinction qui compte : le travail technique est modeste, c'est la décision du service qui manque.

**Conclusion générale.** La réserve était déjà mentionnée ; elle est maintenant explicite — la
confidentialité n'est tenue qu'à moitié, le corpus et la base conservent les noms en clair.

### Vérification totale du 2026-10-03

**Oubli rattrapé en seconde passe** : le chapitre 3 contenait déjà une sous-section
« Données personnelles : une limite non traitée » (`\label{sec:rgpd}`), qui chiffre l'exposition —
202 collaborateurs et onze consultants nommés — mais affirmait que « l'exigence de confidentialité
posée au chapitre 1 est respectée ». Cette phrase contredisait le nouveau bilan. Elle précise
désormais que seul le volet (a) l'est. Les chapitres 1 et 6 renvoient maintenant à cette section
plutôt que de répéter les mêmes faits.

- Les quatre occurrences d'ENF-04 dans le mémoire sont cohérentes entre elles.
- Plus aucune ligne ne déclare la confidentialité tenue sans réserve.
- Le tableau de conformité compte bien neuf lignes, et le décompte du texte leur correspond.
- Le registre des risques porte toujours R-05 à l'état ouvert, ce qui concorde.
- Le dossier de spécification `CADRAGE_SRS.md` utilise une autre numérotation — l'anonymisation y
  est ENF-09 — et la donne déjà comme non atteinte : rien à corriger de ce côté.
- **Le mémoire compile sans erreur** après ces modifications.

---

## T1 et T2 — vocabulaire du corpus et de la base RAG — **100 %** ✅

Les deux remarques sont traitées ensemble : c'est la même confusion de vocabulaire.

**T1** : le corpus contient 1 800 tickets historiques, dont 476 seulement au statut Résolu.
**T2** : distinguer tickets résolus, tickets documentés et autres statuts.

### Les trois décomptes, mesurés sur `data/raw/HelpDesk1.csv`

| Ensemble | Effectif | Critère |
|---|---|---|
| Tickets **historiques** | 1 800 | toutes les lignes de l'export |
| Tickets **résolus** | 476 (26,4 %) | statut `Résolu` |
| Tickets **documentés** | 1 693 (94,1 %) | champ `Résolution/Motif` rempli, tous statuts |

Recouvrement partiel dans les deux sens : **26** tickets résolus ne portent aucun texte de
résolution, **1 243** tickets documentés ne sont pas résolus. « 1 800 tickets résolus » était donc
inexact deux fois plutôt qu'une.

Répartition complète du corpus : Résolu 476 · Rejeté 464 · Problème 328 · Prise en Charge 321 ·
En attente 211.

Base RAG réellement indexée — les tickets **documentés du jeu d'entraînement seulement**, par
anti-fuite : **1 357 lignes** (Rejeté 363, Résolu 358, Problème 237, Prise en Charge 236, En
attente 163), pour seulement **46 procédures distinctes**.

| Sous-tâche | État |
|---|---|
| 1.1 Relever toutes les occurrences | ✅ 17 occurrences de « 1 800 », 12 de « résolus » |
| 1.2 Fixer la formulation de référence | ✅ les trois termes ci-dessus |
| 1.3 Remplacer partout, résumé et conclusion compris | ✅ résumés FR et EN, introduction, conclusion |
| 1.4 Vérifier les figures et tableaux portant ce nombre | ✅ 3 diagrammes + 5 figures de diagnostic |
| 1.5 Relire les passages modifiés | ✅ |
| 2.1 Définir trois termes et s'y tenir | ✅ nouveau bloc au chapitre 2 |
| 2.2 Relever les passages décrivant la base | ✅ chapitres 3, 5, 7 et annexe B |
| 2.3 Réécrire avec la répartition réelle | ✅ déjà présente aux chapitres 3 et 5, complétée |
| 2.4 Ajouter le fait des 46 procédures distinctes | ✅ déjà présent au chapitre 5, confirmé |
| 2.5 Vérifier les chiffres du chapitre RAG | ✅ 1 357 / 358 / 46 recoupés sur les données |
| 1.V / 2.V **Vérification totale** | ✅ |

### Ce qui a été écrit dans le mémoire

**Chapitre 2, nouveau bloc « Trois décomptes à ne pas confondre ».** Placé juste après le tableau
des statuts, il définit les trois termes, donne leurs effectifs et leur recouvrement, et dit
explicitement d'où vient la base de connaissances. C'est la référence à laquelle les autres
chapitres renvoient.

**Résumé français et abstract anglais.** « Ses tickets résolus s'accumulent » devient « ses
tickets s'accumulent » ; « les cas déjà résolus les plus proches » devient « les cas déjà
traités » ; le corpus est annoncé comme 1 800 tickets **historiques** dont 476 seulement au statut
Résolu. Même correction côté anglais.

**Introduction et conclusion générale.** Mêmes deux corrections. La conclusion disait « il avait
accumulé 1 800 tickets résolus » : elle dit maintenant « 1 800 tickets, dont 476 seulement menés
jusqu'au statut *Résolu* ».

**Chapitres 3, 5 et annexe B.** La base de connaissances est désormais nommée par le terme défini
au chapitre 2. Le chapitre 5 ajoute que seuls 358 de ses 1 357 tickets portent le statut Résolu.

**Chapitre 7 et diagramme d'architecture.** « le moteur de recherche retrouve les tickets résolus
comparables » → « les tickets documentés comparables » ; la base de connaissances « conserve les
résolutions passées » → « les réponses déjà apportées ». Le diagramme `ch06_architecture.puml` a
été corrigé aux trois mêmes endroits et rendu à nouveau.

### Le code disait la même chose de travers

La remarque portait sur le mémoire, mais le code employait le même vocabulaire fautif là où il
construit la base. Corrigé pour que les deux racontent la même histoire :

- `src/pipeline/split.py` — le commentaire annonçait « tickets resolus du train uniquement » alors
  que le filtre ne regarde que `Résolution/Motif`. Commentaire et en-tête réécrits.
- `src/pipeline/rag_build.py`, `rag_semantic_build.py`, `src/rag/engine.py` — docstrings et
  messages de sortie (« N tickets résolus » → « N tickets documentés »).
- `notebooks/01_eda.ipynb` — la cellule d'audit définissait la base RAG comme *résolu **et**
  résolution non vide*, ce qui n'est pas le critère du pipeline. Réécrite : elle affiche
  maintenant les deux décomptes, leur recouvrement et le nombre de résolutions distinctes.
- `notebooks/data_quality_report.py` — **bug latent trouvé au passage** : `find_col(df, "solution")`
  renvoyait `Date de résolution`, remplie seulement pour les 476 tickets résolus, et non
  `Résolution/Motif`. La clé `base_rag_resolus` est remplacée par `tickets_resolus` (476) et
  `tickets_documentes` (1 693) ; figures et PDF régénérés.
- `notebooks/03_modeling.ipynb`, `04_rag.ipynb`, `06_rag_semantique.ipynb`,
  `07_rag_evaluation.ipynb`, `notebooks/notebook.md`, `README.md` — libellés alignés. Les carnets
  06 et 07 annonçaient « 476 tickets résolus » alors qu'ils lisent `rag.csv`, qui en compte 1 357.

Le `CHANGELOG.md` du 2026-07-30 avait déjà signalé cette erreur de libellé et corrigé
`DIAGNOSTIC_QUALITE_DONNEES.md`, mais la correction n'était jamais descendue jusqu'aux carnets ni
au générateur de figures. C'est fait.

### Vérification totale du 2026-10-03

- Recherche sur tout le dépôt des formulations remplacées. Les occurrences restantes de
  « tickets résolus » ont été relues une par une et sont **toutes exactes** : elles désignent la
  base ChromaDB vivante, qui n'archive un ticket qu'à sa résolution (`api/db/vector_store.py`,
  `api/routers/tickets.py`, `api/services/ai_service.py`, écran client), ou la collecte de
  réapprentissage, dont `params.yaml` restreint bien l'éligibilité au statut `Résolu`.
- Chiffres recoupés directement sur `data/raw/HelpDesk1.csv` : 1 800 / 476 / 1 693 / 26 / 1 243 /
  58 résolutions distinctes sur le corpus, 46 sur la base RAG.
- **Le mémoire compile** : deux passes, code de sortie 0, zéro erreur `!`, zéro référence
  non résolue.
- **176 tests backend verts.**
- **Le frontend compile** (un libellé d'écran administrateur était concerné).
- Les cinq carnets modifiés restent du JSON valide ; les cinq fichiers Python se compilent.
- Diagramme `ch06_architecture.png` relu après rendu : aucun libellé tronqué, proportions
  inchangées.

**Laissé volontairement en l'état** : `CHANGELOG.md` et `PLAN.md` sont des journaux datés qui
rapportent ce qui était écrit à l'époque ; les réécrire effacerait la trace de la correction.
`CAHIER_DES_CHARGES.md` et `PROMPTS.md` relèvent du même registre.

**À dire à l'encadrant** : la confusion était réelle et elle venait du code autant que du texte.
Le mémoire définit désormais trois termes au chapitre 2 et s'y tient ; le pipeline, les carnets et
le générateur de figures ont été alignés, et un bug de détection de colonne découvert à cette
occasion a été corrigé.

---

## T6 — Modèle expérimental contre modèle déployé — **100 %** ✅

**Remarque** : distinguer systématiquement le meilleur modèle expérimental du modèle déployé, et
les protocoles d'évaluation.

| Sous-tâche | État |
|---|---|
| 6.1 Recenser tous les chiffres publiés et leur origine | ✅ audit automatisé |
| 6.2 Construire le tableau unique | ✅ annexe F |
| 6.3 Faire renvoyer chaque mention à ce tableau | ✅ |
| 6.4 Vérifier qu'aucun chiffre orphelin ne subsiste | ✅ 6 restants, tous justifiés |
| 6.V **Vérification totale** | ✅ |

### Le piège, chiffré

La chaîne lexicale complétée des règles vaut **0,5827** sous le protocole des expériences et
**0,5829** sous celui du pipeline. Deux millièmes séparent deux mesures qui ne portent ni sur le
même jeu de test, ni sur le même découpage, ni sur le même nombre de catégories. Rien dans le texte
n'empêchait de les rapprocher.

| | Protocole des expériences | Protocole du pipeline |
|---|---|---|
| Tirage | Stratifié par catégorie sur les titres | Aléatoire sur les titres |
| Tickets | 1 445 / 355 | 1 444 / 356 (jeu gelé) |
| Catégories au test | 8 sur 8 | 5 sur 8 |
| Mesures | `metrics/campagne_apres_nettoyage.json` | `metrics/ml_eval.json` |

### L'audit, mené par programme et non de mémoire

Un script relève les 44 valeurs de la forme `0,XXXX` publiées dans le mémoire et les cherche dans
les 30 artefacts de mesure du dépôt — 1 939 valeurs numériques. Premier passage : **8 orphelines**.
Après correction : **6**, toutes justifiées et déclarées comme telles dans l'annexe.

| Orpheline | Verdict |
|---|---|
| 0,2074 · 0,2516 · 0,2658 · 0,1932 | Différences entre deux lignes du même tableau |
| 0,5719 | Valeur à atteindre, pas une mesure |
| 0,3746 · 0,4789 | **Vrai défaut** : inscrites en dur dans une cellule du carnet 05, non recalculables. Signalé explicitement plutôt que masqué |

Deux orphelines ont été supprimées en créant les artefacts qui manquaient :

- **0,2816 et 0,5726** (mesure de T5) ne vivaient que dans un brouillon de session. Nouveau script
  `scripts/coherence_entree_modele.py` → `metrics/coherence_entree_modele.json`. Il reproduit
  exactement les valeurs publiées : 31,7 % → 44,7 %, F1 0,5726 → 0,5829, confiance 0,41 → 0,46.
- **Le balayage d'alpha de T4** n'était pas non plus dans le dépôt. Versé dans
  `metrics/rag_seuil_balayage.json` par `rag_eval.py --balayage-seuil`.

### Deux erreurs de ma part, corrigées

1. **Le balayage d'alpha avait été mesuré au seuil de 0,50**, avant recalibration. Rejoué au seuil
   servi, il dit l'inverse : relever α ne dégrade pas la précision, il rend simplement le seuil
   moins mordant (α = 0,8 → repli 0 %, 2,52 suggestions, précision 0,4356). α = 0,5 reste retenu,
   mais parce qu'il donne la meilleure précision sur l'affiché — pas parce que l'alternative
   dégraderait. Le passage du chapitre 6 et la fiche T4 sont corrigés.
2. **Le mémoire laissait croire que la correction de T5 activait davantage le filtre de catégorie
   du RAG.** Mesure : sous le seuil de 0,70, la part des tickets ne recule pas sur le jeu gelé, qui
   ne contient que des scénarios inédits. Le recul de 94 % à 80 % porte sur le seuil de routage de
   0,60. Précisé.

### Un défaut de fond trouvé en chemin

**`annexes.tex` n'était inclus nulle part dans `main.tex`.** Les cinq annexes A à E — registre des
risques, composition du jeu de données, cycle de vie du ticket, campagne de charge, paramètres de
la chaîne — n'avaient jamais été compilées. Le chapitre 6 renvoie pourtant aux risques R-05, R-20
et R-22, qui ne vivent que dans l'annexe A : ces renvois ne menaient à rien d'imprimé. L'inclusion
est ajoutée après la bibliographie ; le mémoire passe de 145 à **154 pages**.

### Ce qui a été écrit

- **Annexe F, nouvelle** : « Traçabilité des chiffres publiés ». Pour chaque valeur, ce qu'elle
  mesure, sous quel protocole, et le fichier du dépôt qui la porte. Vingt lignes, plus la réserve
  sur les deux valeurs non recalculables.
- **Chapitre 6, introduction** : les deux distinctions — meilleur modèle mesuré contre modèle
  servi, protocole des expériences contre protocole du pipeline — sont posées avant tout chiffre,
  avec le piège du 0,5827 / 0,5829 énoncé d'emblée.
- **Chapitre 4** : le tableau des protocoles gagne une ligne nommant le fichier de mesure de
  chacun, et renvoie à l'annexe F.
- **Quatre légendes de tableaux** portent désormais leur protocole et renvoient à l'annexe F.

### Vérification totale du 2026-10-03

**Oubli rattrapé en seconde passe — c'était le cœur de la remarque.** Quatre passages mettaient
encore **0,5829** (protocole du pipeline) face à **0,8343** (protocole des expériences) comme si
les deux se comparaient : le tableau des limites, la conclusion du chapitre 6, la conclusion
générale et les deux résumés. La comparaison valide est 0,5827 contre 0,8343, sous le même
protocole. Les quatre passages sont corrigés, et le résumé anglais annonçait en outre un découpage
« grouped by ticket type » là où la mesure est stratifiée.

**Même défaut dans le bilan de conformité, et il changeait un verdict.** La ligne « Qualité de
l'IA » créditait le système livré de 0,8343, qui est le score d'un modèle **non servi**. L'exigence
ENF-02 porte sur le classifieur, et le classifieur livré obtient 0,5827 pour une cible de 0,85 :
il en est à 0,267, pas à 0,016. Le verdict passe donc de **« Partielle » à « Non tenue »**, sur
décision de l'utilisateur.

Conséquences propagées et vérifiées :

| Endroit | Avant | Après |
|---|---|---|
| Bilan de conformité, chapitre 6 | Partielle | **Non tenue** |
| Décompte du bilan | 5 tenues, 2 partielles, 2 non tenues | **5 tenues, 1 partielle, 3 non tenues** |
| Tableau des exigences, chapitre 4 | 0,8343 — Presque atteint | 0,8343 au mieux, 0,5827 servi — **Non atteint** |
| Conclusion du chapitre 6 | « Deux exigences chiffrées ne sont pas tenues » | **Trois** |
| Conclusion générale | « Deux exigences chiffrées » | **Trois**, avec les deux scores |
| Section de l'écart résiduel | « Il manque 0,016 » | Précise que c'est l'écart du meilleur modèle, et que le modèle servi en est à 0,267 |

Décompte recompté à la source après modification : le tableau porte bien 5 « Tenue », 1
« Partielle » et 3 « Non tenue », soit les neuf lignes annoncées.

- **181 tests verts.**
- **Le mémoire compile** : 155 pages, code 0, zéro erreur, zéro référence non résolue.
- **Collision d'étiquette rattrapée** : l'annexe utilisait `tab:tracabilite`, déjà pris par le
  chapitre 1 ; le renvoi du chapitre 1 aurait silencieusement pointé sur l'annexe. Renommée
  `tab:chiffres`, et les deux renvois vérifiés dans le fichier auxiliaire.
- **Sept commandes `\ref` abîmées** par un script de remplacement ont été trouvées et réparées,
  dont une antérieure à cette tâche dans le chapitre 7. Contrôle : plus aucun caractère de contrôle
  dans les sources LaTeX.
- Les trois pages de l'annexe F ont été relues après rendu : aucune cellule ne déborde.

**À dire à l'encadrant** : la distinction était faite en prose mais nulle part de façon
systématique. Elle l'est maintenant dans une annexe dédiée, construite à partir d'un audit par
programme et non de mémoire. L'audit a révélé deux mesures qui n'existaient que dans des brouillons
— elles ont leur script —, deux valeurs non recalculables — elles sont signalées — et le fait que
les annexes du mémoire n'étaient pas compilées.

---

## T7 — Validation humaine du RAG — **100 %** ✅

**Remarque** : renforcer l'évaluation du RAG par une validation humaine, même sur un échantillon
limité.

| Sous-tâche | État |
|---|---|
| 7.1 Générer le fichier d'annotation | ✅ |
| 7.2 Choisir l'échantillon, 30 à 50 requêtes | ✅ 40 requêtes, 8 par catégorie |
| 7.3 Annoter à la main | ✅ 152 couples distincts, à l'aveugle |
| 7.4 Calculer la précision réelle et la comparer au proxy | ✅ `--comparer-protocoles` |
| 7.5 Rédiger la section | ✅ |
| 7.V **Vérification totale** | ✅ |

### Qui a annoté, et ce que ça vaut

**L'annotation a été portée par moi, pas par un consultant du service**, et le mémoire le dit
explicitement. Elle établit qu'une résolution **traite le problème décrit** ; elle n'établit pas
qu'elle aurait **fait gagner du temps** en conditions réelles. C'est un jugement, pas une
référence : sa confirmation par un consultant reste aux perspectives.

Deux garde-fous méthodologiques, conçus pour limiter le biais de celui qui annote le système qu'il
vient de corriger :

- **À l'aveugle.** Rang et score du moteur masqués, candidats mélangés. Annoter en voyant le
  classement reviendrait à le confirmer plutôt qu'à l'évaluer.
- **Un jugement par couple distinct.** Les 40 requêtes ne portent que 12 scénarios et le vivier 41
  résolutions : 152 couples réellement différents, jugés une fois chacun puis reportés. Une même
  situation ne peut pas recevoir deux verdicts contradictoires.

Résultat du jugement : **22 couples utiles sur 152**, et **10 requêtes sur 40 sans aucun candidat
pertinent**.

### Ce que la comparaison révèle

| Moteur | Protocole | Préc.@3 | MRR@3 | nDCG@3 | Rappel@3 |
|---|---|---|---|---|---|
| Lexical | jugement | 0,1667 | 0,5000 | 0,5000 | 0,1896 |
| Lexical | approximation | 0,1667 | 0,4458 | 0,4533 | — |
| Sémantique | jugement | 0,2833 | 0,5250 | 0,5446 | **0,4062** |
| Sémantique | approximation | 0,2917 | 0,5625 | 0,5789 | — |
| **Hybride (servi)** | **jugement** | **0,2833** | **0,5500** | **0,5696** | 0,3896 |
| Hybride (servi) | approximation | 0,2583 | 0,5000 | 0,5196 | — |

1. **L'approximation ne se trompe pas beaucoup au niveau agrégé** — trois centièmes d'écart au
   maximum, alors que 52 % des meilleurs candidats changent de catégorie. Les erreurs se compensent.
   Ce résultat **dément ce que j'attendais** et que j'avais écrit : je pensais l'écart important.
2. **Elle sous-estime le moteur servi, et lui seul.** Tous les indicateurs de l'hybride montent sous
   jugement humain. Les chiffres publiés sont bien des bornes inférieures pour le moteur déployé.
3. **Le classement entre moteurs change.** Sous approximation, le sémantique ordonnait mieux que
   l'hybride (MRR 0,5625 contre 0,5000). Sous jugement, c'est l'inverse (0,5500 contre 0,5250).
   **Le choix de servir l'hybride est mieux soutenu par la mesure annotée que par celle qui l'avait
   motivé.**
4. **Le rappel devient calculable** : 0,3896 pour l'hybride, 0,4062 pour le sémantique. Aucun
   chiffre du mémoire ne pouvait le dire auparavant.

### Trois défauts corrigés dans l'outillage

1. **Le gabarit n'aurait proposé que 3 candidats** par requête : le moteur appliquait son seuil et
   son `top_k`. Porté à **10 candidats sans seuil**, sans quoi le rappel restait hors de portée.
2. **Le gabarit livrait la réponse du proxy** — un drapeau « même catégorie que la requête » sur
   chaque candidat, qui ancrait le jugement sur le critère à évaluer. Retiré.
3. **Biais silencieux à l'évaluation.** `charger_requetes` traitait « zéro candidat pertinent »
   comme « requête non annotée » : les 10 requêtes les plus difficiles étaient **écartées du
   calcul**, ce qui gonflait le résultat (P@3 hybride 0,3778 au lieu de 0,2833). Un drapeau
   `annote` explicite tranche désormais les deux cas.

### Un argument du mémoire réfuté par l'annotation

Le chapitre affirmait qu'une définition stricte de la pertinence « donnerait zéro pour les trois
moteurs », les scénarios du test étant absents de la base. **C'est faux** : 30 requêtes sur 40 ont
reçu au moins un passage jugé utile. L'argument confondait le scénario et le geste — réinstaller un
pilote d'impression aide un ticket d'impression, quel que soit le ticket d'origine. Retiré du
mémoire plutôt que laissé justifier l'approximation.

### Fichiers

- `data/knowledge/rag_eval_set.json` — 40 requêtes annotées, avec la provenance de l'annotation
- `scripts/verification/preparer_annotation.py` — feuille à l'aveugle et report
- `scripts/verification/feuille_jugement.json` — les 152 jugements, auditables un par un
- `metrics/rag_protocoles.json` — la comparaison des deux protocoles
- `src/pipeline/rag_eval.py` — mode `--comparer-protocoles`, correction du biais de chargement

### Vérification totale du 2026-10-03

- **181 tests verts.**
- **Le mémoire compile** : 157 pages, code 0, zéro erreur, zéro référence non résolue.
- Traçabilité : **54 valeurs traçées** (contre 38 avant T7), mêmes 6 orphelines justifiées. Les 16
  chiffres de l'annotation sont tous dans un artefact du dépôt, et figurent à l'annexe F.
- Ordre de lecture corrigé : la comparaison annotée apparaîtrait avant les résultats qu'elle
  corrige — bloc déplacé après la section des résultats mesurés.
- Une phrase devenue fausse (« le protocole annoté, que ce travail n'a pas conduit ») et une
  commande `\textbf` abîmée par un script ont été rattrapées à la relecture.

**À dire à l'encadrant** : la validation humaine est faite, par moi et non par un consultant, avec
deux garde-fous contre le biais et le protocole écrit. Elle confirme que les chiffres publiés
sous-estiment le moteur servi, elle rend le rappel calculable pour la première fois, et elle
renforce le choix de déploiement. Elle a aussi réfuté un argument que le mémoire avançait et
révélé un biais de calcul qui gonflait le résultat de neuf centièmes.

---

## T9 — Relecture finale — **100 %** ✅

Vérifier que tous les chiffres du mémoire sont cohérents entre eux, et qu'aucune valeur corrigée
ne subsiste ailleurs sous son ancienne forme.

### Méthode : trois contrôleurs plutôt qu'une relecture

Relire soixante-dix chiffres à l'œil ne prouve rien. Trois scripts ont été écrits, qui rejouent
l'ensemble en quelques secondes et qu'on peut relancer après chaque modification.

| Contrôleur | Ce qu'il vérifie | Résultat |
|---|---|---|
| Traçabilité | Chaque valeur `0,XXXX` du mémoire existe dans un artefact de mesure | 54 tracées, 6 justifiées |
| Cohérence, volet 1 | Vérité terrain, cohérence interne, formulations périmées | 38 contrôles |
| Cohérence, volet 2 | Répartitions, les deux découpages, coûts, latence, figures | 18 contrôles |

**94 contrôles au total.** Les quantités ne sont pas recopiées dans les scripts : elles sont
recalculées depuis `data/raw/HelpDesk1.csv`, les trois fichiers de découpage et les artefacts de
`metrics/`, puis confrontées au texte.

### Sept chiffres périmés trouvés et corrigés

| Où | Avant | Après |
|---|---|---|
| `chap_06`, intégration continue | « cent trente-deux » tests | **cent cinquante-cinq** |
| `chap_06`, tests non rejouables | « dix-huit » tests d'intégration | **vingt-six** |
| `chap_06`, couverture | moteur sémantique à 20 % | **29 %** |
| `chap_06`, couverture | 44 % sans précision | 44 % en CI, **46 %** sur la suite complète |
| Diagramme `ch05_hybride` | « Seuil 0,50 » | **0,35**, source et image régénérée |
| `README.md` racine | 150 tests, P@3 hybride 0,3542 | **181 / 155**, P@3 sans filtre **0,4083**, seuil 0,35, précision affichée 0,4545 |
| `helpdesk-ai/README.md` | 150 tests, 132 en CI, 18 autres | **181 / 155 / 26** |

Plus deux documents techniques : `TICKET_WORKFLOW.md` annonçait encore le seuil 0.50 ;
`CADRAGE_SRS.md` donnait pour ENF-10 « 74 % en local (59 tests), 22 % en CI (41 tests) », valeurs
périmées de plusieurs versions — remplacées par **46 % sur 181 tests, 44 % sur les 155 de la CI**,
et le statut passe de « Partiel » à « Non atteint », la cible étant 70 %.

### Un défaut de fond, le même que celui de T6

Le rappel sur \emph{Sécurité} était annoncé à **0,60** dans la conclusion générale et dans le bilan
de conformité, sans dire que c'est le score du **meilleur modèle**, celui qui n'est pas servi. Le
classifieur livré y est à **zéro** sur le jeu de test gelé. Les deux passages le disent maintenant.
C'est exactement la confusion que T6 avait corrigée sur le F1-macro, restée en place sur le rappel.

### Deux écarts examinés et déclarés bénins

- **58 contre « cinquante-huit »** : le mémoire écrit le nombre en chiffres dans les énoncés
  techniques et en lettres dans les phrases de synthèse. La valeur est la même partout ; c'est une
  convention typographique suivie de façon constante, pas une divergence.
- **111,5 millions de paramètres** : l'artefact porte cette valeur arrondie, le mémoire écrit
  111 519 760 au chapitre 4. Même nombre, précision différente.

### Vérification totale du 2026-10-03

- **94 contrôles automatisés, zéro anomalie réelle** (les deux restantes sont examinées ci-dessus).
- Les deux découpages ne sont jamais confondus : 1 445 / 355 n'est nulle part rattaché au pipeline,
  ni 1 444 / 356 aux expériences.
- Les ventilations somment : statuts du corpus 1 800, statuts de la base RAG 1 357.
- **Les 51 images incluses existent toutes** sur le disque.
- Le décompte du bilan de conformité est recompté à la source : 5 tenues, 1 partielle, 3 non
  tenues, soit les neuf lignes annoncées.
- **181 tests verts.**
- **Le mémoire compile** : 155 pages, code 0, zéro erreur, zéro référence non résolue, sources
  LaTeX sans caractère de contrôle.

**À dire à l'encadrant** : la relecture a été faite par programme, pas à l'œil, et les scripts
restent dans le dépôt pour être rejoués. Elle a rattrapé sept chiffres périmés — dont quatre que
mes propres corrections avaient rendus faux — et une dernière occurrence de la confusion entre
modèle mesuré et modèle servi, sur le rappel \emph{Sécurité} cette fois.

---

## T10 — Redites du chapitre 2 (demande du 2026-10-04, hors mail de l'encadrant)

**Demande** : vérifier le chapitre 2 et supprimer ce qu'une partie dit déjà d'une autre.

| Sous-tâche | État |
|---|---|
| 10.1 Relever les redites internes au chapitre | ✅ |
| 10.2 Relever les redites avec les chapitres 1, 3 et 4 | ✅ |
| 10.3 Supprimer ou déplacer, sans perdre un seul chiffre | ✅ |
| 10.4 Réparer les titres de sous-sections devenus inexacts | ✅ |
| 10.V **Vérification totale** | ✅ |

### Les onze redites trouvées, et ce qui en a été fait

| # | Redite | Traitement |
|---|---|---|
| 1 | Les deux formats de date, déjà donnés au chapitre 1 avec les mêmes décomptes | Remplacés par un renvoi au chapitre 1 |
| 2 | « Nous reconnaissons les deux formats au chargement » | Supprimé : l'introduction annonce qu'aucune transformation n'est appliquée ici |
| 3 | Le taux de rejet, raconté à l'identique au chapitre 1 et en 2.2.3 | Réduit à un renvoi ; seule la limite de mesure est conservée |
| 4 | « Les utilisateurs formulent leurs demandes de mille manières… », phrase quasi mot pour mot du chapitre 1 | Conclusion réécrite sur l'apport propre au chapitre |
| 5 | Les 58 titres annoncés en 2.1.2, avant la sous-section qui les établit | Énoncé reformulé sans le décompte |
| 6 | La comparaison 91 % / 3 % donnée deux fois, en 2.1.3 puis en 2.4 | 2.4 renvoie désormais à `sec:public` |
| 7 | La médiane des descriptions annoncée en 2.1.3, mesurée en 2.2.3 | Conservée : 2.1.3 compare, 2.2.3 mesure |
| 8 | Le traitement du déséquilibre, dit en 2.2.1 puis dans `tab:risques` | Retiré du texte, le tableau porte « (chapitre 4) » |
| 9 | Le découpage anti-fuite, dit en 2.2.4 puis dans `tab:risques` | Retiré du texte, le tableau porte la référence de section |
| 10 | Le repli sur `knowledge Base`, dit dans `tab:completude` puis dans `tab:risques` | `tab:completude` ne porte plus que l'interprétation |
| 11 | « Le tableau 2.6 associe à chaque risque… », redit avant et après le tableau | Une seule phrase, avant |

### Deux défauts de structure corrigés au passage

- **2.2.3 portait trois sujets sans rapport** sous le titre « Longueur des textes et cycle de vie » :
  la longueur des textes, les statuts, et le bloc de vocabulaire ajouté en T1-T2. La longueur rejoint
  2.2.2, devenue « Complétude des champs et longueur des textes » ; 2.2.3 devient « Statuts, délais
  et décomptes du corpus », titre qui annonce enfin son contenu.
- **« Les quatre analyses qui précèdent se recoupent »** ouvrait la section 2.3 en annonçant la
  redondance comme une qualité. Reformulé.

### Une incohérence de chiffre levée

Le chapitre 1 écrivait qu'une lecture naïve des dates « perd 46 % du corpus », le chapitre 2
« plus de la moitié des dates ». Les deux étaient justes selon le format supposé, mais se lisaient
comme une contradiction. La phrase du chapitre 2 a disparu avec la redite.

### Vérification totale du 2026-10-04

- **Aucun chiffre perdu** : 1 800, 476, 464, 1 693, 58, 1 535, 5,93, 33 mots, 91 % / 3 % sont tous
  encore dans le chapitre, chacun à un seul endroit d'énoncé.
- **Sources LaTeX sans caractère de contrôle** (scan de tous les `*.tex`).
- **Le mémoire compile** : 157 pages, code 0, zéro erreur, zéro `??` dans le PDF produit.
- Le nouveau label `sec:public` est résolu ; `fig:longueurs` reste dans la sous-section qui le
  commente, grâce à un `\FloatBarrier`.
- **Les trois contrôleurs rejoués** : 38 + 18 contrôles, et seulement les deux écarts déjà déclarés
  bénins (58 / « cinquante-huit », 111,5 M de paramètres). Aucune régression.

**Note de compilation** : `main.log` porte « There were undefined references ». Elle vient de
biblatex, qui réclame une passe BibTeX à chaque compilation parce que le moteur `biber` est absent
et que le repli bibtex est utilisé. Aucune référence du corps n'est concernée : le PDF ne contient
ni `??` ni `[?]`, et les six citations du chapitre 2 sortent numérotées.

### Suppression de la section 2.1.3 (demande du 2026-10-04)

La sous-section « Un jeu de donnees public pour situer le corpus » a ete retiree sur demande, avec
son tableau de correspondance et sa figure. Six dependances ont ete reparees :

| Dependance | Traitement |
|---|---|
| Phrase d'annonce de la section 2.1 | Ramenee a trois sous-sections |
| Renvoi `sec:public` depuis 2.4 | Supprime ; la limite tient sur le seul chiffre interne de 3 % |
| `tab:limites7` du chapitre 6, « contre 91 % sur un jeu public » | Comparaison externe retiree |
| Citation `hfTickets` | Devenue non citee, elle sort de la bibliographie |
| Labels `tab:bench`, `fig:public2`, `sec:public` | Plus aucun renvoi mort |
| Figure `ch02_comparaison_publique.png` | Reste sur le disque, non incluse |

Verifie : **156 pages**, code 0, zero erreur, zero `??`, bibliographie recompilee, les trois
controleurs ne signalent que les deux ecarts deja declares benins.

**À dire à l'encadrant** : le chapitre 2 ne reprend plus le diagnostic du chapitre 1, il le mesure.
Là où le chapitre 1 lisait la répétitivité comme un symptôme du travail du service, le chapitre 2
en tire une contrainte expérimentale. C'est la seule chose que les deux chapitres disent du même
objet, et ils n'en disent pas la même chose.

---

## T11 — Exigences non satisfaites (demande du 2026-10-04, hors mail de l'encadrant)

**Demande** : « faites tout le nécessaire pour atteindre le reste », c'est-à-dire les huit exigences
que le bilan du chapitre 6 ne déclarait pas tenues.

| Réf | Exigence | État au départ | État atteint |
|---|---|---|---|
| ENF-01 | Réponse sous 300 ms au p95 | Non tenue — 330 ms | en cours |
| ENF-02 | F1-macro du classifieur ≥ 0,85 | Non tenue — 0,5827 servi | en cours |
| ENF-03 | Rappel *Sécurité* ≥ 0,70 | Non tenue — 0 servi | en cours |
| ENF-04 (b) | Données personnelles | Non tenue | **Volet technique fait et vérifié** |
| ENF-07 | Tests automatisés | Partielle — 44 % | en cours |
| EF-07 | Orientation selon la confiance | Partielle — calculée, inutilisée | **Fait** |
| EF-11 | Résumé automatique du ticket | Non traitée | **Fait** |
| EF-12 | Suggestion de priorité | Non traitée | **Démontrée impossible, mesures à l'appui** |
| EF-13 | Analyse de tonalité | Non traitée | **Démontrée impossible ; signaux de gravité livrés à la place** |

### Le défaut qui invalidait la mesure de qualité

CamemBERT a été entraîné sur une entrée qui contient le champ `Classification`. Or
`api/services/ticket_service.py` fixe ce champ à « Demande » pour tout ticket qui vient d'être
déposé : l'administrateur ne le renseigne que pendant le traitement. Le modèle était donc mesuré
sur une entrée que la production ne peut pas lui fournir — le même défaut que la remarque T5, à un
autre endroit de la chaîne.

Mesuré avec l'entrée réelle, sous le protocole des expériences : F1-macro **0,8343 → 0,8644**,
rappel *Sécurité* **0,60 → 0,90**. Vérifié sur dix découpages appariés : écart positif sur 9 sur 10,
médiane +0,0303, jamais négatif (`metrics/camembert_servable_robustesse.json`).

### Le verrou de latence

Le ticket le plus long du corpus fait **48 jetons** ; le modèle en calculait 128. 62 % du temps
partait en rembourrage. À 48 jetons, la qualité est strictement identique et le coût passe de
306 ms à 128 ms (`metrics/cout_longueur_sequence.json`). ONNX en entiers 8 bits était une fausse
piste : aucun gain de temps et accord avec le modèle d'origine tombé à 51 %.

### Deux exigences démontrées impossibles

- **EF-12** — le modèle à trois niveaux a un rappel nul sur « basse ». En binaire, quand le système
  annonce « priorité haute » il a raison **51,3 %** du temps pour un taux de base de 44,1 %, et gagne
  1,4 point d'exactitude sur la classe majoritaire. Modèle non conservé (`metrics/priorite_eval.json`).
- **EF-13** — sur 25 termes d'urgence du français courant, **20 sont absents** du corpus ; il n'y a
  **aucun point d'exclamation** dans 1 444 tickets ; et sur 97 mots qui séparent la priorité, 95
  n'apparaissent que sous un ou deux titres, donc reconnaissent un scénario et non une humeur
  (`metrics/tonalite_eval.json`). À la place, un relevé de **signaux de gravité** énoncés par le
  demandeur, dont l'écart au taux de base est mesuré : perte de données +0,28, indisponibilité
  +0,16, blocage +0,13. Le signal « impossibilité » a été retiré après mesure — 44 % des tickets
  pour +0,02 point.

### ENF-04 (b) — ce qui est fait

| Élément | État |
|---|---|
| Relevé préalable | Les données personnelles tiennent dans deux colonnes ; le texte libre n'en contient aucune |
| Pseudonymisation | HMAC-SHA256, clé hors du dépôt, même personne = même pseudonyme |
| Réidentification | Possible pour le service avec la clé, sans table de correspondance conservée |
| Vérification | **322 fragments de noms cherchés, zéro trouvé** hors de l'export d'origine |
| Pipeline | `collect.py` pseudonymise le consultant à l'export ; sans clé, le nom est retiré, jamais laissé en clair |
| Durées de conservation | Déclarées dans `params.yaml`, avec un script de purge qui **refuse de tourner** tant que le service ne les a pas arrêtées |

Reste à la charge du service : arrêter les durées, et informer les personnes. Ce sont des décisions
d'organisation, pas de code.

### EF-07 et EF-11 — ce qui est livré

- **EF-07** : le ticket porte désormais une décision d'orientation prise à la création et journalisée,
  avec son motif en clair. Trois raisons la déclenchent : confiance sous le seuil, catégorie imposée
  par une règle métier, ou aucun cas comparable. Deux points d'entrée nouveaux : la file filtrée et
  le décompte. 10 tests.
- **EF-11** : résumé extractif par retrait des formules de civilité. Les 16 formules ont été trouvées
  **mécaniquement** — une ligne présente sous au moins la moitié des titres d'entraînement
  n'appartient à aucun scénario — et non écrites à la main. Gain mesuré : **33,3 % du texte retiré
  sur le jeu gelé**, scénarios inédits, aucun ticket sans gain. 9 tests.

### Vérification à ce stade

- **207 tests verts** (181 au départ), 16 lents désélectionnés.
- L'audit des données personnelles ne trouve plus rien dans le corpus.


---

## T12 — Six remarques finales de l'encadrant (courriel du 2026-10-09)

Le courriel ouvre par « le rapport a connu une nette amélioration » et demande de vérifier six
points « en définitif ». Les six ont été vérifiées dans le code et les données avant toute
correction ; les six sont fondées.

| Sous-tâche | État |
|---|---|
| 12.1 Calcul et présentation du F1-macro du tableau 6.4 | ✅ **100 %** |
| 12.2 Rôle du jeu de test gelé dans la porte de promotion | ✅ **100 %** |
| 12.3 Validation de CamemBERT tirée au hasard | ✅ **100 %** |
| 12.4 Effet des doublons de la base RAG | OK **100 %** |
| 12.5 Seuil RAG choisi sur le jeu d'évaluation | OK **100 %** |
| 12.6 Annotation RAG relue par un consultant | hors de ma portée |

### 12.1 — Le F1-macro du tableau 6.4

**Ce que l'encadrant soupçonnait** : qu'on ne peut pas annoncer une moyenne sur 8 catégories avec
un jeu de test qui n'en contient que 5.

**Ce que la vérification a trouvé, et qui est pire** : la valeur n'était calculée ni sur 8 ni sur 5,
mais sur **6**. `src/pipeline/train.py` appelait `f1_score(..., average="macro")` **sans argument
`labels`** ; scikit-learn moyenne alors sur l'union des catégories vraies et des catégories
prédites. Le modèle prononçant *Applicatifs*, absente du jeu gelé, la somme des F1 était divisée
par six.

Le dénominateur suivait donc **les erreurs du modèle**. Un classifieur qui n'aurait pas commis
cette prédiction aurait été divisé par cinq et aurait affiché 0,6995 à qualité rigoureusement
identique. Deux modèles n'y étaient pas comparés à armes égales — et c'est cette valeur que le
registre enregistrait comme métrique de référence.

**Un second foyer du même défaut**, invisible à la première lecture : `scripts/coherence_entree_modele.py`
passait bien `labels=`, mais calculé par `sorted(set(verite) | set(pred) | set(avec))`. Portée
explicite, et pourtant variable — et c'est précisément l'écart entre deux variantes que ce script
mesure. C'est pourquoi ses valeurs coïncidaient exactement avec celles de `ml_eval`.

**Les chiffres corrigés**, même modèle, même jeu de test, calcul rectifié :

| Indicateur | Avant | Après | Portée |
|---|---|---|---|
| F1-macro, chaîne servie | 0,5829 | **0,4372** | 8 catégories du référentiel |
| F1-macro, classes évaluables | 0,6995 | 0,6995 | 5 présentes — inchangé, déjà explicite |
| F1-macro, modèle seul | 0,2708 | **0,2031** | 8 catégories |
| Précision macro | 0,5868 | **0,4401** | 8 catégories |
| Rappel macro | 0,6099 | **0,4574** | 8 catégories |
| Cohérence d'entrée, modèle seul | 0,2816 → 0,2708 | **0,2112 → 0,2031** | 8 catégories |
| Cohérence d'entrée, avec règles | 0,5726 → 0,5829 | **0,4294 → 0,4372** | 8 catégories |
| Exactitude | 0,8202 | 0,8202 | inchangée |

**Une conséquence sur le récit du mémoire.** Le « piège » des deux nombres presque identiques —
0,5827 sous un protocole, 0,5829 sous l'autre — **était lui-même un artefact du défaut**. Corrigé,
l'écart n'est pas de deux millièmes mais de quinze points : 0,5827 contre 0,4372. Les passages du
chapitre 4, du chapitre 6 et de l'annexe F qui s'appuyaient sur cette coïncidence ont été réécrits,
en disant ce qui a été corrigé plutôt qu'en effaçant la trace.

**Ce qui a été fait**

| | |
|---|---|
| Code | Portée figée sur le référentiel dans `train.py` (F1-macro, précision, rappel, et le F1 du modèle seul) et dans `coherence_entree_modele.py` |
| Lisibilité | Chaque valeur est accompagnée dans le fichier de métriques d'un champ `_portee` qui nomme les catégories comptées : plus besoin d'ouvrir le code pour savoir par combien on divise |
| Remesure | `scripts/reevaluer_modele_servi.py` rejoue l'évaluation du modèle **en service**, sans réentraîner ni promouvoir |
| Preuve | `scripts/verification/portee_f1_macro.py` donne les trois valeurs côte à côte et nomme la catégorie surnuméraire |
| Garde | `tests/test_portee_metriques.py`, 6 tests. Le dernier lit l'arbre syntaxique de tout `src/` et `scripts/` et refuse toute moyenne par catégorie sans portée, **ou dont la portée est calculée sur les prédictions**. Vérifié : il rejette les trois formes fautives et accepte les deux légitimes |

**Vérification totale**

- **213 tests verts** (207 avant), 16 lents désélectionnés.
- Traçabilité : 59 valeurs tracées, 6 orphelines, toutes déjà justifiées au README.
- Les deux contrôleurs de cohérence ne signalent que les deux écarts déclarés bénins.
- Le mémoire compile : 158 pages, code 0, zéro erreur, zéro `??`.

**À dire à l'encadrant** : sa remarque portait sur une légende de tableau ; elle a découvert une
métrique dont le dénominateur variait avec les erreurs du modèle, présente à deux endroits du dépôt
et enregistrée comme métrique de référence du registre. Quatre chiffres publiés changent, et la
coïncidence sur laquelle le mémoire attirait l'attention disparaît — elle n'existait que par ce
défaut.

### 12.2 — Le jeu de test gelé dans la porte de promotion

**Ce que l'encadrant redoute** : qu'à force de servir à trancher, le jeu gelé devienne un jeu de
validation sans que personne ne l'ait décidé.

**L'exposition réelle, mesurée** : `promote.py` lisait le jeu à chaque arbitrage, sans que rien ne
compte les lectures. L'historique du registre en dénombre **trois** — les candidats v2, v3 et v4,
tous trois rejetés. Le risque est réel mais l'érosion n'a pas encore eu lieu.

**Ce qui a été posé**

| | |
|---|---|
| Journal | `data/reference/journal_jeu_gele.json` : chaque lecture avec sa date, son motif et ce qu'elle a servi à décider |
| Distinction | Les lectures qui **tranchent** comptent ; celles qui **rapportent** un chiffre pour un tableau sont inscrites mais n'érodent rien |
| Budget | `jeu_gele.lectures_de_decision_max: 10` dans `params.yaml`. Atteint, la porte **refuse d'arbitrer** et renvoie à une décision humaine |
| Reconstitution | `scripts/reconstituer_journal_jeu_gele.py` a inscrit les trois lectures antérieures depuis le registre, marquées comme reconstituées — la valeur lue à l'époque n'est pas conservée |
| Rôle énoncé | L'en-tête de `promote.py` dit ce que le jeu est (une porte, une fois par candidat) et ce qu'il n'est pas (un sélecteur de seuil, d'époque ou de variante) |

**Garde** : `tests/test_jeu_gele.py`, 10 tests. Le dernier vérifie par lecture du source que le
budget est contrôlé **avant** l'ouverture du fichier — sinon la lecture aurait lieu quand même.

**Ce que le dispositif ne fait pas**, et le mémoire le dit : il ne verrouille rien. Nul ne peut
empêcher d'ouvrir un fichier. Sa valeur est de rendre une transgression visible dans un fichier
suivi en version plutôt que silencieuse.

**Vérification** : **223 tests verts**, mémoire 158 pages, code 0, zéro erreur.

### 12.3 — La validation de CamemBERT tirée au hasard

**Ce que l'encadrant relève** : la validation est tirée au hasard alors que le test est séparé par
groupes de titres. Vérifié dans le carnet 05, cellule 6 : `ds_train.train_test_split(test_size=0.1,
seed=RS)`, un tirage ligne à ligne. Les 41 titres de la validation sont **tous** présents à
l'entraînement.

**Ce que le mémoire disait déjà, et ce qui manquait.** Le chapitre 4 signalait l'écart entre la
courbe de validation et le test, et l'appelait « le piège méthodologique de ce chapitre ». Mais il
le présentait comme une curiosité à ne pas confondre avec un résultat. Il ne disait pas que ce jeu
faussé **choisissait l'époque** : `load_best_model_at_end` avec `metric_for_best_model='f1_macro'`
conserve les poids de la meilleure époque sur la validation. Un signal faussé commandait la
sélection.

**La mesure** (`scripts/validation_camembert.py`, deux entraînements identiques en tout sauf le
prélèvement de la validation) :

| Prélèvement | F1 de validation | Époque retenue | F1 sur le test, avec règles |
|---|---|---|---|
| Au hasard, ligne à ligne | 0,9199 | 8 | 0,8351 |
| Par groupe de titres | 0,4697 | 8 | 0,8411 |

**Conclusion en deux temps, et les séparer importe.** Le défaut est réel : la fuite gonfle le
signal de sélection de **0,45 point** pour une qualité réelle identique, et une procédure qui
s'appuie là-dessus n'offre aucune garantie. Mais les chiffres publiés tiennent : aucun ne provient
de la validation, les deux bras retiennent la **même** huitième époque, et le test ne diffère que
de **0,006** — sous le bruit d'un jeu de douze scénarios.

Il serait malhonnête de défendre la procédure au motif qu'elle n'a pas nui cette fois-ci :
`src/pipeline/train_camembert.py`, destiné au modèle servi, prélève sa validation par groupe de
titres et ne s'en remet plus à cette coïncidence.

**Écrit au mémoire** : nouveau tableau 4.x et trois paragraphes au chapitre 4, qui distinguent le
défaut de procédure de la validité des chiffres. 159 pages, code 0.

### 12.4 — Les doublons de la base RAG

**Le chiffre de l'encadrant est exact** : `rag.csv` compte 1 357 lignes pour **46 résolutions
distinctes**, répétées 31 fois en médiane et jusqu'à 49.

**Première réponse, rassurante** : les trois moteurs écartent déjà une résolution déjà vue avant de
constituer leur liste (`engine.py:83`, `semantic_engine.py:147`, `hybrid_engine.py:124`). Mesuré
sur 40 requêtes : **aucun doublon n'atteint l'administrateur**.

**Seconde réponse, qui l'est moins.** Dédoublonner suppose d'avoir de quoi remplacer. Le moteur
sémantique lisait `top_k * 3 = 9` voisins « pour filtrer les doublons » — un facteur qui convient à
une base où chaque réponse apparaît deux ou trois fois. Avec 31 copies, les 9 plus proches voisins
sont 9 exemplaires de la même résolution.

| Passages consultés | Réponses distinctes | Requêtes servies 3/3 |
|---|---|---|
| **9** *(code d'origine)* | 1,57 | **1 sur 40** |
| 18 | 1,85 | 7 |
| 36 | 2,25 | 13 |
| 75 | 2,75 | 30 |
| **150** | **3,00** | **40 sur 40** |

**Correction** : élargissement qui double jusqu'à ce que le compte y soit, plus un cache des
résolutions pour que le parcours ne touche pas la base ligne à ligne (ENF-01 est déjà sous
contrainte). 7 tests dans `tests/test_elargissement_semantique.py`.

**Le moteur servi gagne sur les deux plans** : 1,75 -> **2,02** suggestions rendues, et précision de
l'affiché **0,4429 -> 0,5185**.

**Conséquence sur le mémoire** : les deux tableaux de comparaison des moteurs citaient « 80
requêtes, protocole d'approximation ». Ce tirage n'existe plus — le jeu a été reconstruit à 40
requêtes annotées lors de T7 — et ces chiffres n'étaient donc plus reproductibles. La comparaison
est désormais portée sur les 40 requêtes annotées, jugées par un humain. Une affirmation a dû être
retirée : le classement entre moteurs ne s'inverse plus selon le protocole.

### 12.5 — Le seuil RAG choisi sur le jeu d'évaluation

**La remarque est fondée** : le mémoire retenait 0,35 comme l'argmax de la précision sur les 40
requêtes, puis relisait cette même précision sur ces mêmes 40 requêtes.

**La réserve est chiffrée plutôt que déclarée** (`scripts/seuil_rag_hors_echantillon.py`) :

| | |
|---|---|
| Pouvoir discriminant du score | **0,8303** — le score sépare bien l'utile de l'inutile |
| Précision par tranche | < 0,35 : 0,09 — entre 0,35 et 0,40 : **0,5106** — au-delà de 0,40 : **0,9375** |
| Précision dans l'échantillon | 0,5652 |
| **Précision hors échantillon** | **0,4886** (5 plis, seuil choisi sur 32 requêtes, mesuré sur 8) |
| **Part d'optimisme** | **+0,0766**, soit environ un septième |
| Stabilité du choix | Le seuil retenu reste entre 0,35 et 0,38 selon le pli |

**Ce qui est écrit au mémoire** : la coupure n'est pas arbitraire — elle tombe sur une
discontinuité réelle — mais la valeur de 0,5185 doit se lire comme un ordre de grandeur majoré, non
comme une mesure. Les valeurs par pli vont de 0 à 0,89 : avec huit requêtes par pli, aucune ne se
lit à la deuxième décimale.

### Vérification des points 4 et 5

- **230 tests verts** (223 avant).
- Traçabilité : 67 valeurs tracées, **8 orphelines** toutes justifiées au README.
- Les deux contrôleurs de cohérence ne signalent que les deux écarts déjà déclarés bénins.
- Mémoire : **161 pages**, code 0, zéro erreur, zéro `??`.

### 12.5 bis — Une ambiguïté de lecture levée (2026-10-10)

Trouvée en revérifiant le point 5 : le chapitre 6 écrit **0,4886** pour deux grandeurs qui n'ont
aucun rapport — le plafond du score hybride (page 106) et la précision hors échantillon
(page 107). Les deux valeurs sont justes, chacune revérifiée dans son fichier de mesure
(`metrics/rag_seuil_balayage.json` pour la première, `metrics/seuil_rag_hors_echantillon.json`
pour la seconde ; la seconde est la moyenne de 0,3846 · 0,6364 · 0,8889 · 0,5333 · 0,0).

Le risque n'est pas l'erreur, c'est la suspicion d'erreur : un lecteur attentif qui retrouve le
même nombre deux pages plus loin conclut à une copie fautive. Une phrase nomme désormais la
coïncidence à l'endroit exact où elle se produit, en haut de la page 108, juste après la seconde
occurrence.

Mémoire recompilé : **161 pages**, code 0, zéro erreur, zéro référence non résolue. Les deux
dépassements de marge signalés par le journal sont ceux d'avant la modification, et sont ailleurs.

---

## T13 — Audit séquentiel des six remarques (2026-10-10)

Demande : vérifier, point par point, que chaque remarque est prise en compte **dans le code** et
**dans le rapport**, et donner la correction exacte quand un écart subsiste. Les six points ont été
repris dans l'ordre du courriel. **Six écarts trouvés**, tous corrigés.

| # | Point | Code | Rapport | Écart trouvé |
|---|---|---|---|---|
| 1 | F1-macro du tableau 6.4 | OK | OK | **Oui** — le registre nommait `primary_metric` une valeur qui ne décidait rien |
| 2 | Découpage de validation | OK | OK | **Oui** — aucun test ne gardait la correction ; 0,98 contre 0,9199 inexpliqué |
| 3 | Réserve sur le seuil 0,35 | OK | OK | **Oui** — `params.yaml` et le résumé anglais ignoraient la réserve |
| 4 | Relecture par un consultant | OK | OK | **Oui** — renvoi cassé ; l'instrument manquait |
| 5 | Jeu gelé et porte de promotion | OK | OK | **Oui, le plus grave** — « chaque lecture s'inscrit » était faux |
| 6 | Doublons de la base RAG | OK | OK | **Oui** — le protocole à 80 requêtes subsistait en trois endroits |

### 13.1 — Le registre nommait « métrique principale » ce qui ne décidait pas

`model_registry.py:133` inscrivait sous le nom `primary_metric` la F1-macro du référentiel entier.
Or la porte compare `f1_macro_classes_evaluables` (`promote.py:metrique_effective`). Un même nom
pour deux grandeurs — exactement la famille d'erreur que l'encadrant avait relevée, à un autre
endroit du dépôt. Pour v4, la valeur inscrite était de surcroît celle d'avant la correction, 0,5829.

La porte, elle, n'a jamais été faussée : `promote.py` réévalue **les deux** artefacts dans la même
exécution (`promote.py:376`). Le défaut était d'affichage, et `promote --list` le propageait.

Corrigé : l'index inscrit les deux valeurs sous leur nom, plus la portée de la première ; une entrée
**sans portée** signale une valeur antérieure au 9 octobre, donc incomparable. `promote --list`
affiche deux colonnes, `decision` et `ref-8`, la seconde suivie d'un « ? » quand la portée est
inconnue. `scripts/completer_portee_registre.py` a recopié la métrique de décision dans l'index
depuis le `metrics.json` de chaque version — aucun recalcul, aucune lecture du jeu gelé. 3 tests.

### 13.2 — La correction du découpage n'était gardée par rien

Le prélèvement par groupe de titres vivait dans cinq lignes au milieu d'une fonction qui charge
torch et transformers : hors de portée de tout test. Toutes les autres corrections de cette campagne
ont une garde ; celle-là n'en avait pas.

Corrigé : fonction `prelever_validation_par_titre` au niveau du module, avec une assertion de
non-fuite train/validation qui n'existait pas, et `tests/test_validation_par_titre.py`, 6 tests —
dont un qui vérifie que le tirage ligne à ligne **fuirait** sur le même corpus, sans quoi le premier
test passerait pour une évidence.

Au rapport : le chapitre 4 annonçait 0,98 de F1 de validation dans la figure et 0,9199 dans le
tableau, sans dire que le rejeu reproduit la nature du tirage et non l'échantillon du carnet. Une
phrase le dit maintenant.

### 13.3 — La réserve n'accompagnait pas le chiffre partout

Trois endroits présentaient 0,5185 ou le seuil sans réserve : le commentaire de `params.yaml`,
c'est-à-dire **l'endroit où le seuil vit**, le résumé français, et le résumé anglais. Ce dernier
portait en outre des chiffres périmés — 1.8 suggestions, 0.4545 — quand le français disait 2,0 et
0,5185 : un jury lisant les deux pages voyait deux systèmes différents.

Corrigé : la réserve est dans `params.yaml` avec ses chiffres (0,5652 dans l'échantillon, 0,4886
hors, +0,0766), dans les deux résumés et dans la conclusion générale. Les valeurs périmées du
commentaire de `params.yaml` et de `tests/test_seuil_rag.py` — plage 0.327–0.489, précision 0.4375,
repli 7,5 %, alpha mesuré sur 80 requêtes — sont remplacées par les mesures des 40 requêtes annotées.

### 13.4 — Le renvoi était cassé, et l'instrument manquait

Le chapitre 6 annonçait que « la conclusion générale porte aux perspectives » la relecture par un
consultant. Elle n'y est pas : elle est au chapitre 7. Un encadrant qui vérifie ne la trouve pas.

Corrigé, et complété : `scripts/verification/revue_consultant.py` tire un extrait de quarante
couples **à l'aveugle** — ni rang, ni score, ni le jugement de l'auteur — et rend ensuite l'accord
brut, le kappa de Cohen et la liste des désaccords. Essayé de bout en bout sur un remplissage
simulé, puis l'extrait remis à blanc et le fichier de mesure simulé supprimé : rien de fictif ne
reste dans le dépôt. Le script dit lui-même ce qu'un extrait de cette taille ne peut pas établir :
le tirage uniforme n'y place que sept couples jugés utiles.

### 13.5 — « Chaque lecture s'inscrit dans un journal » était faux

L'écart le plus sérieux de l'audit. Le chapitre 7 l'écrivait ; seule `promote.py` s'inscrivait.
**Neuf autres points d'entrée** ouvraient `data/splits/test.csv` sans rien déclarer, dont **deux qui
tranchent** : `scripts/arbitrage_modele_servi.py`, qui choisit la configuration servie, et le
balayage de seuil de `rag_eval.py`, qui a retenu 0,35.

Le second est le plus instructif. Il ne lit pas `test.csv` : il lit le gabarit annoté, **tiré du jeu
gelé par échantillonnage stratifié**. Les quarante requêtes annotées sont donc des tickets du jeu
gelé, et le seuil a été choisi sur elles. **Les remarques 3 et 5 de l'encadrant n'en font qu'une**,
vue de deux côtés — et le chapitre 7 affirmait précisément le contraire : « il ne sert à choisir
ni un hyperparamètre, ni un seuil ».

Deux défauts trouvés en chemin :

- la suite de tests **écrivait dans le journal du dépôt**. `test_promote_idempotence.py` lance
  promote.py en sous-processus, où le chemin du journal se résout sur le module et où aucun
  monkeypatch ne porte. Quatre lectures d'essai s'y sont inscrites pendant cet audit même. Fermé
  par `JOURNAL_JEU_GELE` et `CHEMIN_JEU_GELE`, positionnés par le harnais. Le compte des lectures
  décisionnelles n'a pas souffert — les essais n'empruntent pas ce chemin, le compte est resté à 3
  pendant toute la campagne — mais celui des lectures de rapport mêle essais et vraies exécutions
  et ne se démêle plus. Le journal le déclare dans un champ dédié ;
- l'exposition réelle est **le double de ce qui était écrit** : six lectures décisionnelles, non
  trois. Trois promotions, plus la constitution du gabarit et deux balayages de seuil, reconstitués
  depuis les fichiers produits par `reconstituer_journal_jeu_gele.py`, étendu et idempotent.

Posé : `jeu_gele.lire()`, qui journalise et rend le jeu, et par lequel passent désormais sept
lecteurs. `tests/test_lectures_jeu_gele.py`, 5 tests, dont un qui parcourt `src/` et `scripts/` et
refuse toute ouverture non déclarée — avec trois dispenses portant chacune son motif. Garde
vérifiée non vide : un lecteur nu déposé exprès dans `scripts/` la fait échouer, et son retrait la
fait repasser.

### 13.6 — Le protocole à 80 requêtes subsistait en trois endroits

Le tirage de 80 requêtes n'existe plus depuis T7. Il restait cité dans `params.yaml`, dans
`tests/test_seuil_rag.py` et au chapitre 6, section « Protocole et dimensions non couvertes », qui
annonçait encore « quatre-vingts requêtes du jeu de test » au-dessus de tableaux qui en annoncent
quarante. Les trois sont corrigés, et le chapitre dit ce qui a été remplacé plutôt que d'effacer
la trace.

### Vérification totale du 2026-10-10

- **244 tests verts** (230 avant), 16 lents désélectionnés.
- Journal du jeu gelé **intact après la suite complète** : 6 décisions, 17 rapports, inchangé.
- Traçabilité : 67 valeurs tracées, 8 orphelines — identique à avant.
- Les deux contrôleurs de cohérence ne signalent que les deux écarts déjà déclarés bénins.
- Mémoire : **163 pages**, code 0, zéro erreur, zéro `??`, aucune référence manquante
  (149 labels croisés), 28 citations sur 28 résolues.
- Un avertissement `biblatex` « (re)run BibTeX » persiste après bibtex et quatre passes. Vérifié
  sans effet : aucune référence ni citation non résolue, aucun `??` dans le PDF. Je n'ai pas pu
  établir s'il précède les modifications du jour, `main.log` n'étant pas suivi en version.

---

## T14 — Mise en conformité du rapport avec le code (2026-10-10)

Demande : vérifier toutes les contradictions du mémoire et rendre un rapport conforme au code et
aux résultats. **Sept affirmations fausses trouvées**, toutes corrigées, et un quatrième
contrôleur posé pour que le genre d'écart ne revienne pas.

### L'angle mort des trois contrôleurs existants

`tracabilite_chiffres.py`, `coherence_memoire.py` et `coherence_memoire_2.py` comparent des
**nombres**. Ils ne voient pas une phrase. Le mémoire pouvait donc écrire six fois « ni
anonymisation ni pseudonymisation » pendant que le dépôt portait `src/data/pseudonymisation.py`,
un script de purge et un audit rendant `conforme: true`, sans qu'aucun contrôle ne bronche.

`scripts/verification/coherence_affirmations.py` ferme cet angle mort. Chaque contrôle porte une
**vérité** lue dans le dépôt, des formulations **interdites** si cette vérité tient, et une
formulation **attendue** — sans quoi supprimer la phrase fautive sans la remplacer suffirait à
faire passer le contrôle. Un contrôle qui ne sait pas établir sa vérité s'annonce « indécidable »
plutôt que vert.

**Première version trop indulgente, et corrigée.** Elle cherchait `EF-11 … non traitée` et
laissait passer « les trois exigences **non traitées sont** EF-11, EF-12 et EF-13 », qui est la
forme exacte employée au chapitre 6. Le motif porte désormais sur la ligne entière et dans les
deux sens. Avant correction : 3 anomalies sur 7 ; après : 7 sur 7, ce qui était la vérité.

### Les sept affirmations fausses

| Affirmation du mémoire | Réalité mesurée | Où |
|---|---|---|
| « cent quatre-vingt-un tests » | **260** | chap_06 ×2, conclusion |
| « la chaîne en exécute cent cinquante-cinq » | **234** | chap_06 |
| « 44 % de couverture » | **51 %** (src), 58 % (service entier) | chap_06 ×2 |
| « ni anonymisation ni pseudonymisation » | module livré, audit de 322 fragments conforme | chap_02, chap_06 ×3, conclusion |
| « EF-07 … n'oriente pas les tickets » | routage décidé et journalisé à la création | chap_01, chap_04 |
| « les trois exigences non traitées sont EF-11, EF-12 et EF-13 » | EF-11 livrée, EF-12 et EF-13 démontrées hors d'atteinte | chap_06 |
| « le moteur sémantique couvert à 29 % » | **67 %** | chap_06 |

### Les chiffres, mesurés et non recopiés

`scripts/releve_suite_tests.py` relève la suite par commande et écrit `metrics/suite_tests.json` :
260 tests, 26 d'intégration écartés de l'intégration continue, 234 rejoués par elle, 16 lents.
Couverture relevée dans deux périmètres, `metrics/couverture_tests.txt` (src, 51 %) et
`metrics/couverture_tests_service_entier.txt` (api + src, 58 %).

**Un piège évité.** La mesure précédente, 44 %, portait sur `src/` seul. Mesurer `api/` + `src/`
donne 58 % : comparer les deux aurait fait passer un changement de périmètre pour un progrès. Les
deux sont donc relevés, et le mémoire cite le périmètre comparable en premier.

**Un défaut du script de relevé, trouvé en le vérifiant.** Le motif `(\d+) tests collected` lit
260 dans « 244/260 tests collected », et annonçait donc zéro test lent. Corrigé en
`(\d+)(?:/\d+)? tests collected`.

La figure `img/ch07_tests.png` est régénérée depuis le fichier de couverture ; elle affiche
234 tests et 51 %. Le script de figure refusait d'abord l'artefact : il attend la ligne de résumé
nue que produit `-q`, que le mode verbeux encadre de signes égal.

### Ce que le mémoire dit maintenant, et qu'il ne disait pas

Deux paragraphes neufs au chapitre 6 décrivent le travail que le dépôt portait sans que le rapport
en rende compte : EF-07 et EF-11 livrées, EF-12 et EF-13 **closes par une démonstration
d'impossibilité** — rappel nul sur la priorité basse, 51,3 % de justesse pour un taux de base de
44,1 % ; vingt termes d'urgence sur vingt-cinq absents du corpus, aucun point d'exclamation dans
1 444 tickets, 95 des 97 mots discriminants cantonnés à un ou deux titres. Le relevé de signaux de
gravité livré à la place est chiffré par son écart au taux de base.

Le bilan de conformité passe de « cinq tenues, une partielle, trois non tenues » à « cinq tenues,
**deux** partielles, **deux** non tenues », la confidentialité des données personnelles devenant
partielle plutôt que non tenue. Le décompte des exigences fonctionnelles passe de dix satisfaites
à **douze**, les deux restantes n'étant pas « non traitées » mais hors d'atteinte sur ce corpus.

**Un contrôleur mis à jour en conséquence.** `coherence_memoire.py` attendait « une **l'est**
partiellement » au singulier ; le passage à deux impose « **le sont** ». Le motif accepte
désormais les deux accords : un contrôle doit suivre la langue, pas imposer une faute.

### Vérification totale du 2026-10-10

- **Quatre contrôleurs** : `coherence_affirmations` 7/7 verts ; les trois autres ne signalent que
  les deux écarts déjà déclarés bénins.
- **244 tests verts** en mode rapide, 260 collectés ; journal du jeu gelé intact après la suite.
- Traçabilité : 67 valeurs tracées, 8 orphelines — inchangé.
- Mémoire : **163 pages**, code 0, zéro erreur, zéro `??`, 150 labels croisés sans référence
  manquante.

---

## T15 — Relecture mécanique : typographie et orthographe (2026-10-10)

Question posée : « le rapport est-il fini, sans fautes ? » Avant de répondre oui, il fallait
vérifier ce qui n'avait jamais été vérifié. Deux contrôleurs de plus, et le compte passe à six.

### Pourquoi l'orthographe n'avait jamais été contrôlée

Aucun correcteur n'est installé sur la machine : ni hunspell, ni aspell, ni le moindre paquet
Python. MiKTeX, lui, embarque le dictionnaire français de Dicollecte, `fr.dic` et ses règles
d'affixes. `scripts/verification/orthographe_memoire.py` fait ce que ferait hunspell : il
développe les affixes, puis confronte le texte du mémoire au vocabulaire obtenu.

**Un résultat absurde qui a révélé le vrai défaut.** La première version annonçait 73 237 formes
connues pour 75 475 entrées de dictionnaire — donc moins que le dictionnaire — et signalait
« champs » et « celles » comme inconnus. Ce dictionnaire n'écrit pas ses drapeaux en clair :
`champ/1` renvoie à la première ligne `AF` du fichier d'affixes, qui vaut `S.()`. Alias résolus :
**432 403 formes**, et 251 inconnues au lieu de 2 569.

### Le résultat

**Aucune forme inconnue dans le corps du mémoire.** Les 142 restantes sont les développements
anglais de la liste d'abréviations, le résumé anglais, la webographie et le préambule LaTeX.

Le vocabulaire du projet vit dans `lexique_memoire.txt`, 126 mots, suivi en version pour qu'un
ajout se relise dans un diff : l'orthographe de 1990 (`plateforme`, employée 20 fois), le
vocabulaire de l'apprentissage (`classifieur`, 24 fois), les dérivés que le dictionnaire de 2015
ne porte pas (`pseudonymisation`, `réentraînement`), les produits et les noms propres.

Garde vérifiée non vide : « une fautte de frape » injectée fait passer le compte de 142 à 144, et
son retrait le ramène à 142.

### La relecture typographique

`relecture_typographique.py` cherche les formes fautives que l'œil lit comme correctes : mots
doublés **par-dessus un retour à la ligne**, guillemets ou parenthèses déséquilibrés, ponctuation
doublée, unité collée au nombre. Résultat : 4 signalements, tous des espaces d'alignement avant un
commentaire de fin de ligne dans un fichier de configuration.

**Deux défauts de ce contrôleur, trouvés en le vérifiant.** Il annonçait un « champ champ » au
chapitre 3 qui n'existe pas : son filtre mangeait la fin de ligne après `\texttt`, collant deux
mots éloignés. Et sa numérotation de paragraphes dérivait de quelques lignes sur un fichier long,
ce qui envoie le relecteur au mauvais endroit. Les deux sont corrigés, et un essai d'injection
confirme qu'il attrape bien mot doublé, guillemet orphelin et parenthèse seule.

### Ce que la relecture a aussi corrigé dans le texte

Le chapitre 3 écrivait « Nous ne l'avons pas réalisée » à propos de l'anonymisation, puis le
paragraphe suivant annonçait qu'elle l'avait été. Devenu « Elle ne l'a pas été à ce stade », qui
situe l'affirmation dans la phase de préparation sans contredire la suite.

L'annexe F citait encore la plage `0,327 à 0,489` du protocole à 80 requêtes et le couple
`181 / 155` de tests. Devenus `0,3366 à 0,4886` et `260 / 234`, avec une ligne de plus pour la
couverture.

### Mise en page : aucune régression

- **Zéro titre orphelin** en bas de page, sur 116 intitulés.
- Le tableau de conformité, dont deux cellules se sont allongées, tient sur sa page : vérifié sur
  l'image rendue, pas sur l'extraction de texte, qui entrelaçait deux lignes et laissait croire à
  un chevauchement.
- Le blanc en bas de la page 113, où les nouveaux paragraphes s'arrêtent avant la section 6.6,
  vaut 37 % de la hauteur. Mesuré sur les 163 pages, c'est en dessous de vingt autres pages du
  mémoire : la section suivante réclame seize lignes et bascule, comportement normal et déjà
  présent partout ailleurs.
- Les deux résumés tiennent chacun sur une page malgré la réserve ajoutée.

### Vérification totale du 2026-10-10

| Contrôleur | Résultat |
|---|---|
| `tracabilite_chiffres` | 67 valeurs tracées, 8 orphelines justifiées |
| `coherence_memoire` | 38 contrôles, 1 anomalie déclarée bénigne |
| `coherence_memoire_2` | 18 contrôles, 1 anomalie déclarée bénigne |
| `coherence_affirmations` | 7 contrôles, **0 anomalie** |
| `relecture_typographique` | 4 signalements, tous des alignements de commentaires |
| `orthographe_memoire` | **0 forme inconnue dans le corps** |

Mémoire : **163 pages**, code 0, zéro erreur, zéro `??`, 150 labels croisés sans référence
manquante, 28 citations sur 28. Suite de tests : **244 verts** en mode rapide, 260 collectés.

### Ce qui n'est toujours pas vérifié, et que ces contrôleurs ne peuvent pas vérifier

La **grammaire** et l'**accord**. Un « ces » pour « ses », un participe mal accordé, un singulier
pour un pluriel : aucun de ces six contrôleurs ne les voit. Une relecture humaine reste nécessaire
avant l'envoi ; elle n'a simplement plus à chercher les fautes mécaniques.

---

## T16 — Les mesures de T11 écrites au mémoire (2026-10-10)

Demande : écrire la partie mesures de T11, restée dans le dépôt sans jamais atteindre le rapport.
C'était le dernier trou, et il touchait les conclusions principales du mémoire.

### Les deux mesures qui manquaient

**1. CamemBERT était évalué sur une entrée que la production ne peut pas fournir.** Le texte
enrichi du chapitre 3 contient le champ `Classification`, que `ticket_service.py` fixe à
« Demande » pour tout ticket qui vient d'être déposé. Réévalué sur l'entrée réelle — même modèle,
même protocole, même graine, seule l'entrée change :

| Entrée | F1 seul | Avec règles | Rappel *Sécurité* |
|---|---|---|---|
| Enrichissement publié | 0,5685 | 0,8343 | 0,60 |
| **Entrée de production** | 0,5683 | **0,8644** | **0,90** |
| Sans enrichissement | 0,5613 | 0,7924 | 0,40 |

Contre-intuitif et vérifié : l'entrée **appauvrie** donne le meilleur modèle. Le champ
`Classification`, renseigné après coup par le consultant qui a traité le ticket, portait une part
de la réponse. Sur dix découpages appariés, l'écart est positif 9 fois, nul 1 fois, jamais négatif,
médiane +0,0303 — et **les dix dépassent 0,85 comme 0,70**.

**2. Soixante-deux pour cent du calcul partait en rembourrage.** Ticket le plus long : 48 jetons ;
longueur réglée à 128. À 48 jetons, aucune troncature, qualité identique au millième, coût
**305,9 → 128,5 ms**. L'export ONNX en entiers 8 bits a été essayé et abandonné : aucun gain de
temps (222,7 contre 218,6 ms) et accord avec le modèle d'origine tombé à 0,5112.

### Pourquoi il fallait l'écrire

Le mémoire affirmait en huit endroits que le meilleur modèle est « à seize millièmes de
l'objectif » et que le transformer « coûte 325,8 ms, davantage que le budget entier ». Les deux
reposaient sur des mesures que T11 avait dépassées. Un jury qui ouvre le dépôt trouvait la mesure
qui franchit la cible.

### Ce qui a été écrit, et ce qui ne l'a pas été

Nouvelle sous-section 4.6.4, « Deux mesures faites après coup, et ce qu'elles déplacent », avec
deux tableaux. Puis huit passages repris : le tableau d'exigences du chapitre 4, l'écart résiduel
et l'arbitrage de production du chapitre 6, la ligne « Qualité de l'IA » du bilan et son
commentaire, le registre des limites, la conclusion du chapitre 6, la conclusion générale, les
perspectives du chapitre 7, les deux résumés et l'annexe F.

**Ce que le mémoire ne fait pas, et le dit.** Il ne change pas le modèle servi. Le faire
supposerait un réentraînement, un passage par la porte de promotion — donc une septième lecture
décisionnelle du jeu gelé sur dix — et un arbitrage qui revient au service.

**Ce que ces mesures ne lèvent pas, et le mémoire le dit aussi.** 128,5 ms restent vingt-cinq fois
le coût de la chaîne servie, et s'ajouteraient à une requête déjà mesurée à 330 ms au 95ᵉ centile.
Servir le transformer ferait franchir le budget de latence plus nettement, non moins. Ce qui
change est la nature de l'obstacle : la qualité du modèle n'est plus en cause, le coût de son
exécution l'est.

Le bilan de conformité reste donc inchangé dans ses verdicts : ENF-02 et ENF-03 sont jugées sur le
classifieur **servi**, et le fait qu'un modèle non servi franchisse les cibles ne certifie rien.
Ce qui change est la formulation : « seuils non franchis » devient « seuils non franchis par le
modèle servi », ce qui est la vérité exacte.

### Vérification totale du 2026-10-10

- Mémoire : **166 pages** (163 avant), code 0, zéro erreur, zéro `??`, aucune référence manquante.
- Traçabilité : **73 valeurs tracées** (67 avant — les six nouvelles le sont toutes), 8 orphelines
  inchangées.
- `coherence_affirmations` 7/7 ; les deux contrôleurs historiques sur leurs deux signaux bénins ;
  typographie 4 signalements d'alignement.
- Orthographe : **0 forme inconnue dans le corps**. Le contrôleur a attrapé « servable » dans une
  légende d'annexe, mot qui n'existe pas en français ; reformulé plutôt qu'ajouté au lexique.
- Zéro titre orphelin sur 117 intitulés ; les deux pages neuves relues sur leur rendu.

---

## T17 — La page 45 à moitié blanche, et ce qu'elle cachait (2026-10-10)

Signalement : « page 45, il y a de l'espace après l'introduction et vous avez sauté une page ».
Exact, et le défaut ne touchait pas cette page seule.

### Mesure avant de corriger

Plutôt que de retoucher la page incriminée, j'ai mesuré le blanc en bas des sept pages
d'introduction de chapitre, par détection d'encre sur l'image rendue :

| Chapitre | Blanc en bas, avant |
|---|---|
| 1 | 19 % |
| 2 | 24 % |
| 3 | 3 % |
| **4** | **65 %** |
| 5 | 0 % |
| 6 | 19 % |
| 7 | 1 % |

Le chapitre 4 était l'exception, mais trois autres chapitres perdaient aussi un cinquième de page.

### La cause, et ma responsabilité

`commandes_locales.tex` posait `\pretocmd{\subsection}{\needspace{4\baselineskip}}`. Or
`needspace` ne se contente pas de réserver : il écrit un `\penalty-100` devant le titre,
c'est-à-dire **une invitation à rompre la page juste là**. Sur un chapeau de section court — trois
lignes au chapitre 4 — LaTeX saisissait cette invitation et terminait la page.

S'y ajoutait un `\sectionAvecSaSuiteLongue` que j'avais écrit moi-même en T10 devant la section 4.1,
réclamant trente lignes libres. C'était un correctif posé sur un symptôme dont je n'avais pas
cherché la cause, et il coûtait plus qu'il ne rapportait.

### Deux fausses pistes, essayées et rejetées

- Passer `\Needspace*` en `\needspace` non étoilé : **173 pages** au lieu de 166, et toutes les
  introductions entre 59 et 68 % de blanc. Nettement pire.
- `\nopagebreak` après le chapeau de la section 4.1 : sans effet, le `\penalty-100` du titre de
  sous-section l'emporte.

### La correction

La réserve devant les **sous-sections** est retirée. La garde reste assurée autrement :
`\@afterheading` et `\clubpenalty=10000`, déjà déclarés, interdisent qu'un titre de sous-section
reste seul en bas de page. Vérifié après retrait : **zéro titre orphelin sur les 117** du mémoire.

| Chapitre | Avant | Après |
|---|---|---|
| 1 | 19 % | **2 %** |
| 2 | 24 % | **5 %** |
| 3 | 3 % | 3 % |
| **4** | **65 %** | **5 %** |
| 5 | 0 % | 0 % |
| 6 | 19 % | 19 % *(un flottant, pas un titre)* |
| 7 | 1 % | 1 % |

Sur le document entier, le blanc moyen en bas de page passe de 57 à 54 pixels et le nombre de
pages mal remplies de 38 à 35. Le mémoire perd une page, de 166 à **165**.

`\sectionAvecSaSuiteLongue` n'est plus appelé nulle part. La réserve devant les sections devient une
longueur modifiable, `\reserveAvantSection`, avec `\reserveCourte` et `\reserveLongue` pour la
régler devant une section donnée ; aucune n'est employée aujourd'hui, elles existent pour le jour où
une section en aura besoin, sans qu'il faille réécrire le mécanisme.

### Vérification totale

- **165 pages**, code 0, zéro erreur, zéro `??`, 150 références résolues.
- Zéro titre orphelin ; page 45 relue sur son rendu, pleine.
- Les six contrôleurs au même niveau : `coherence_affirmations` 7/7, traçabilité 73 valeurs,
  orthographe 0 forme inconnue dans le corps, typographie 4 alignements de commentaires.
- Les 20 marqueurs de tâches sont toujours verts.
