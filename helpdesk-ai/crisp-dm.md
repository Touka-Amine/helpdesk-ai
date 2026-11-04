# crisp-dm.md — Plan du mémoire HelpDesk AI, organisé par phases CRISP-DM

> **Principe.** CRISP-DM est la méthodologie unique du projet. Les sept chapitres suivent ses six
> phases, chacun gardant un titre académique plutôt que le nom d'une phase. Le rattachement est
> porté dans la table des matières par un bandeau, dans l'introduction de chaque chapitre par une
> phrase, et ici par le tableau de correspondance.
>
> Refonte appliquée le 2026-09-15. Ce fichier décrit le plan **tel qu'il est écrit** : chaque
> section citée existe dans `../report/chap_0*.tex`.
>
> **146 pages**, 0 erreur, 0 référence cassée. Cible inscrite dans
> [PLAN_RAPPORT.md](PLAN_RAPPORT.md) : 110 à 135 pages.

---

## 1. Correspondance phases → chapitres → travaux

| Phase CRISP-DM | Chapitre | Travaux |
|---|---|---|
| **1 · Compréhension du métier** | 1 | contexte, service support, problématique, positionnement, exigences, méthodologie |
| **2 · Compréhension des données** | 2 | provenance, schéma, exploration, qualité, redondance, risques |
| **3 · Préparation des données** | 3 | nettoyage, variables, découpage anti-fuite, base de connaissances, gouvernance |
| **4 · Modélisation** | 4 et 5 | classifieur d'un côté, moteur de recherche et assistant de l'autre |
| **5 · Évaluation** | 6 | comparaison, sélection, mesure du RAG, tests, campagne de charge, conformité, limites |
| **6 · Déploiement** | 7 | architecture, UML, application, conteneurisation, chaîne d'apprentissage, perspectives |

---

## 2. Structure d'ensemble

```text
INTRODUCTION GÉNÉRALE

PHASE 1 — COMPRÉHENSION DU MÉTIER
    Chapitre 1 — Contexte général du projet

PHASE 2 — COMPRÉHENSION DES DONNÉES
    Chapitre 2 — Exploration et compréhension des données

PHASE 3 — PRÉPARATION DES DONNÉES
    Chapitre 3 — Préparation et construction des données

PHASE 4 — MODÉLISATION
    Chapitre 4 — Classification automatique des tickets
    Chapitre 5 — RAG et assistance à la résolution

PHASE 5 — ÉVALUATION
    Chapitre 6 — Évaluation et validation de la solution

PHASE 6 — DÉPLOIEMENT
    Chapitre 7 — Conception, intégration, industrialisation et déploiement

CONCLUSION GÉNÉRALE
```

---

## 3. Deux partis pris à défendre

### Les concepts sont exposés là où ils servent

Le mémoire n'a pas de chapitre d'état de l'art séparé. Les concepts ouvrent le chapitre qui les
mobilise : la représentation du texte et la classification déséquilibrée en tête du chapitre 4, la
génération augmentée par récupération et les modèles de langage en tête du chapitre 5,
l'industrialisation en tête du chapitre 7. Le lecteur rencontre chaque notion au moment où elle
sert, plutôt que quarante pages avant.

### La modélisation occupe deux chapitres, l'évaluation un seul

Le travail a produit **deux moteurs**, un classifieur et un moteur de recherche. La phase de
modélisation se dédouble donc en chapitres 4 et 5. La phase d'évaluation les réunit au chapitre 6,
avec les tests et le bilan de conformité, ce qui permet de comparer les deux moteurs et le système
entier sous un même regard.

---

## 4. Le plan, chapitre par chapitre

### Chapitre 1 — Contexte général du projet
> Phase 1 — Compréhension du métier

| Section | Contenu |
|---|---|
| Introduction | ce que le chapitre couvre et d'où viennent ses sources |
| 1.1 Présentation de l'organisme d'accueil | groupe OneTech, filiale OTBS, organisation interne et cadre de confidentialité |
| 1.2 Cadre du projet | étude de l'existant, limites de l'existant et solutions du marché, problématique, solution proposée et périmètre |
| 1.3 Analyse et spécification des besoins | objectifs du projet, acteurs, besoins fonctionnels, besoins non fonctionnels |
| 1.4 Méthodologie de travail | comparaison des démarches, démarche retenue : CRISP-DM |
| Conclusion | ce que le chapitre établit et ce que le suivant ouvre |


Structure calquée sur les rapports de référence du dossier `exemple_de_rapport` : quatre sections numérotées encadrées par une introduction et une conclusion, deux à quatre sous-sections chacune, aucun titre de niveau trois. Les observations du service (ticketing, périmètre, volumétrie, outil de suivi, cycle de vie, répétitivité, limites du diagnostic) sont réunies sous « Étude de l'existant » et repérées par des chapeaux en gras, au lieu de porter chacune un numéro de sous-section.

### Chapitre 2 — Exploration et compréhension des données
> Phase 2 — Compréhension des données

| Section | Contenu |
|---|---|
| Introduction | ce que le chapitre couvre |
| 2.1 Présentation des données | provenance et mode de collecte, schéma et variable cible, jeu de données public de comparaison |
| 2.2 Analyse exploratoire des données | distribution des catégories, complétude des champs, longueur des textes, redondance du corpus |
| 2.3 Diagnostic de qualité et risques | synthèse du diagnostic, risques identifiés et traitements retenus |
| 2.4 Limites du corpus | représentativité, ce que les mesures ne permettent pas de conclure |
| Conclusion | ce que le chapitre établit |

### Chapitre 3 — Préparation et construction des données
> Phase 3 — Préparation des données

| Section | Contenu |
|---|---|
| 3.1 Préparation des données | nettoyage textuel, valeurs problématiques, variables construites |
| 3.2 Préparation du corpus pour la classification | séparation anti-fuite, composition des jeux, déséquilibre résiduel |
| 3.3 Préparation des connaissances pour le RAG | constitution de la base, distincte du jeu d'apprentissage |
| 3.4 Gouvernance et reproductibilité | versionnement, données personnelles |

### Chapitre 4 — Classification automatique des tickets
> Phase 4 — Modélisation

| Section | Contenu |
|---|---|
| Introduction | ce que le chapitre couvre |
| 4.1 Concepts mobilisés | représentations du texte, transformers et CamemBERT, adaptation économe en paramètres |
| 4.2 Classification supervisée et déséquilibre de classes | algorithmes de référence, métriques, techniques de rééquilibrage |
| 4.3 Formulation du problème et protocole d'évaluation | métrique retenue, découpage des expériences, référence plancher |
| 4.4 Approche fondée sur TF-IDF | vectorisation et modèles testés, évaluation |
| 4.5 Amélioration par les heuristiques métier | les deux niveaux de règles, gain mesuré |
| 4.6 Approche fondée sur CamemBERT et LoRA | choix du modèle et contrainte matérielle, entraînement, résultats |
| Conclusion | ce que le chapitre établit |

### Chapitre 5 — RAG et assistance à la résolution
> Phase 4 — Modélisation

| Section | Contenu |
|---|---|
| Introduction | ce que le chapitre couvre |
| 5.1 Concepts mobilisés | génération augmentée par récupération, bases vectorielles et évaluation, grands modèles de langage |
| 5.2 Présentation du système RAG | la chaîne retenue, vue d'ensemble |
| 5.3 Construction de la base de connaissances | composition et format des résolutions, volume indexé et coût de la contrainte anti-fuite |
| 5.4 Mise en œuvre de la recherche | les trois moteurs, comparaison des approches |
| 5.5 Intégration du modèle de langage | modèle exécuté sur site, conception du prompt, garde-fous et repli |
| 5.6 Apprentissage continu | d'un journal à une base interrogée, contrôle qualité et cycle de vie |
| Conclusion | ce que le chapitre établit |

### Chapitre 6 — Évaluation et validation de la solution
> Phase 5 — Évaluation

| Section | Contenu |
|---|---|
| Introduction | ce que le chapitre couvre |
| 6.1 Comparaison des approches | tableau d'ensemble et combinaison manquante, audit des règles et origine de l'écart |
| 6.2 Sélection du modèle final | modèle retenu pour la production, calibration de la confiance et routage |
| 6.3 Évaluation du RAG | protocole et dimensions non couvertes, résultats mesurés, le seuil jamais atteint |
| 6.4 Tests de la solution | périmètre, nature des tests, zones non couvertes, couverture mesurée |
| 6.5 Validation de la solution | temps de réponse non tenu, bilan de conformité |
| 6.6 Limites du système | seize limites groupées par origine |
| Conclusion | ce que le chapitre établit |

### Chapitre 7 — Conception, intégration, industrialisation et déploiement
> Phase 6 — Déploiement

| Section | Contenu |
|---|---|
| Introduction | ce que le chapitre couvre |
| 7.1 Industrialisation et MLOps | versionnement des données et des modèles, suivi des expérimentations, conteneurisation et intégration continue |
| 7.2 Outils technologiques utilisés | technologies retenues et motif de leur choix |
| 7.3 Architecture applicative | les quatre couches et les flux qui les traversent |
| 7.4 Conception et modélisation UML | contexte et cas d'utilisation, classes, les deux moments décisifs du cycle, états du ticket, choix de conception et lacunes |
| 7.5 Développement du backend | organisation en couches du service |
| 7.6 Développement du frontend | accès à la plateforme, portail du demandeur, console d'administration et validation humaine |
| 7.7 Workflow global de traitement d'un ticket | le parcours complet, du dépôt à l'enrichissement de la base |
| 7.8 Conteneurisation et déploiement | topologie déployée, volumes, ports publiés |
| 7.9 Chaîne d'apprentissage automatisé | pipeline reproductible et ce qu'il exclut, porte de promotion et réentraînement contrôlé |
| 7.10 Perspectives | classées par ce qu'elles exigent |
| Conclusion | ce que le chapitre établit |

---

## 5. Règles maintenues

**R1** aucune métrique inventée ; toute valeur renvoie à un fichier du dépôt.
**R2** les valeurs invalidées n'apparaissent que dans le passage qui explique leur invalidation.
**R3** les limites du travail sont énoncées plutôt que masquées.

**Conventions de mise en page**, contrôlées automatiquement après chaque modification :

1. une section s'ouvre par un paragraphe, jamais directement sur un sous-titre ;
2. une figure est annoncée par une phrase, puis relue par un paragraphe placé après ;
3. un titre n'est jamais imprimé seul en bas de page ;
4. la légende d'un tableau est au-dessus, celle d'une figure en dessous ;
5. tout flottant est appelé au moins une fois par le texte ;
6. chaque chapitre nomme dans son introduction la phase qu'il porte ;
7. chaque conclusion de chapitre annonce ce que le suivant reprend.

---

## 6. État

| Élément | État |
|---|---|
| Sept chapitres alignés sur les six phases | ✅ |
| Six bandeaux de phase dans la table des matières | ✅ |
| Chaque chapitre nomme sa phase en introduction | ✅ |
| Quatorze introductions et conclusions de chapitre réécrites | ✅ |
| Liste des chapitres de l'introduction générale refaite | ✅ |
| Renvois entre chapitres remappés | ✅ 74 vérifiés un par un |
| Compilation | ✅ 146 pages, 0 erreur, 0 référence cassée |
| Contrôles de mise en page | ✅ 0 titre collé, 0 flottant orphelin, 0 section vide |
| Volume sous 135 pages | ⬜ 146, onze pages au-dessus |
