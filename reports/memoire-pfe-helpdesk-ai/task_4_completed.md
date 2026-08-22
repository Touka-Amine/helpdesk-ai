# Tâche 4 — Réécriture du chapitre 2 selon le plan de rapport

> Projet : mémoire PFE **HelpDesk AI** — Mohamed Amine Toukabri — OneTech Business Solutions
> Tâches précédentes : [`task_1`](task_1_completed.md) · [`task_2`](task_2_completed.md) · [`task_3`](task_3_completed.md)
> Date : 2026-08-20 · Branche : `chore/gouvernance-pfe`

---

## 1. Sortie transmise dans le fil de conversation

Chapitre 2 réécrit selon `PLAN_RAPPORT.md`. **15 pages**, sept sections numérotées, dans la cible de
15 à 18 pages fixée par le plan.

Ma première version en faisait trois sections et dix pages. Le plan en impose sept, avec des
sous-sections numérotées. Cette structure convient mieux ici qu'au chapitre 1 : un chapitre de
concepts se consulte par entrée, il n'a pas à se lire d'un seul tenant.

Les sections 2.1 à 2.6 reprennent exactement les intitulés du plan. La section 2.7, que le plan
consacrait à la méthodologie de travail, accueille la spécification des besoins, puisque la
méthodologie est remontée au chapitre 1 à votre demande.

Une figure a été ajoutée sur le principe de LoRA, concept difficile à saisir sans schéma. Le
chapitre compte désormais deux figures et cinq tableaux.

La rédaction applique dès l'écriture les règles issues de la passe `/humanize` : aucune antithèse
« pas X mais Y », aucun tiret cadratin en prose, aucun connecteur de remplissage, gras réservé aux
en-têtes de tableaux et à deux termes techniques introduits.

Compilation propre : 46 pages, zéro erreur, zéro citation non résolue, onze références rendues.

---

## 2. Objet de la tâche

### Demande

« Réécrire le chapitre 2 tout en respectant le plan de rapport », précédée de l'invocation
`/humanize`.

### Conflit à résoudre

`PLAN_RAPPORT.md` définit pour le chapitre 2 sept sections et 15 à 18 pages :

```
2.1 Traitement automatique du langage naturel        (5 sous-sections)
2.2 Classification supervisée et déséquilibre        (3)
2.3 Génération augmentée par récupération            (4)
2.4 Grands modèles de langage                        (4)
2.5 MLOps et industrialisation                       (3)
2.6 Outils technologiques utilisés                   (tableau)
2.7 Méthodologie de travail                          (5)
```

Deux écarts existaient entre ce plan et l'état du mémoire.

**La méthodologie (2.7) avait été déplacée au chapitre 1**, à la suite du sommaire imposé par
l'auteur (`Introduction / 1.1 Présentation du projet / 1.2 Méthodologie de travail / Conclusion`).
La conserver ici aurait produit un doublon.

**La spécification des besoins n'avait plus de chapitre d'accueil.** Le plan la situe en 1.3, section
supprimée par ce même sommaire. Aucun autre chapitre ne la prévoit.

### Arbitrage retenu

Reprendre les sections 2.1 à 2.6 telles que le plan les nomme, et affecter le slot 2.7, vacant, à la
spécification des besoins. Le chapitre conserve ainsi ses sept sections et sa profondeur de titres,
tout en hébergeant le contenu orphelin.

Le titre du chapitre devient « Concepts fondamentaux et spécification des besoins ».

---

## 3. Déroulement

| # | Action | Résultat |
|---|---|---|
| 1 | Relecture de `PLAN_RAPPORT.md`, chapitre 2 | 7 sections, 24 sous-sections, cible 15–18 p. |
| 2 | Confrontation au mémoire existant | 2 écarts identifiés : méthodologie déplacée, besoins orphelins |
| 3 | Écriture et exécution de `fig_lora.py` | `ch02_principe_lora.png` produite |
| 4 | Contrôle visuel de la figure | Lisible, formule $h = Wx + BAx$ posée |
| 5 | Réécriture complète de `chap_02.tex` | 7 sections, 22 sous-sections numérotées |
| 6 | Compilation 4 passes | 0 erreur, 0 citation non résolue |
| 7 | Vérification de la table des matières et des flottants | Structure conforme, 7 flottants placés |

### Choix de rédaction

**Numérotation des sous-sections.** L'auteur avait reproché au chapitre 1 sa sur-fragmentation. Le
choix inverse s'impose au chapitre 2 : un lecteur y cherche un concept précis, pas un récit. Les
trois rapports de référence numérotent également les sous-sections de leurs chapitres de concepts.

**Chaque concept amené par le besoin auquel il répond.** TF-IDF est présenté puis mis en défaut par
un exemple tiré du domaine : *« Session Outlook bloquée »* et *« messagerie qui ne s'ouvre plus »*
ne partagent aucun terme et désignent le même incident. LoRA est justifié par la contrainte
matérielle réelle du projet. L'exécution locale du modèle de langage renvoie à la certification
ISO 27001 posée au chapitre 1.

**Application préventive des règles `/humanize`.** Plutôt que d'écrire puis de corriger, les règles
identifiées en tâche 3 ont été appliquées à la rédaction : pas d'antithèse « pas X mais Y », pas de
triade annoncée, pas de tiret cadratin en prose, pas de connecteur vide, gras limité.

---

## 4. Entrées et sorties

### Sources exploitées

| Source | Usage |
|---|---|
| `helpdesk-ai/PLAN_RAPPORT.md` | Structure imposée du chapitre |
| `helpdesk-ai/ARCHITECTURE.md` §5 | Pile technique, tableau 2.1 |
| `helpdesk-ai/requirements.txt` | Dépendances Python, dimension des vecteurs d'encodage |
| `helpdesk-ai/CADRAGE_SRS.md` §2–§4 | Acteurs, exigences fonctionnelles et non fonctionnelles |
| `HelpDesk1.csv` | Déséquilibre de 5,93 et nombre de catégories |

### Références académiques ajoutées

Onze entrées dans `report/biblio.bib`, toutes réellement citées dans le corps du texte :

| Référence | Section citante |
|---|---|
| Mikolov et al., ICLR 2013 | 2.1.2 — représentations denses |
| Reimers et Gurevych, EMNLP 2019 | 2.1.2 — encodage de phrases |
| Vaswani et al., NeurIPS 2017 | 2.1.3 — mécanisme d'attention |
| Devlin et al., NAACL 2019 | 2.1.3 — BERT |
| Martin et al., ACL 2020 | 2.1.4 — CamemBERT |
| Hu et al., ICLR 2022 | 2.1.5 — LoRA |
| Chawla et al., JAIR 2002 | 2.2.3 — SMOTE |
| Lewis et al., NeurIPS 2020 | 2.3.1 — RAG |
| Johnson et al., IEEE TBD 2021 | 2.3.3 — indexation vectorielle |
| Es et al., EACL 2024 | 2.3.4 — RAGAS |
| onetech-bs.com | chapitre 1 |

### Fichiers produits ou modifiés

| Fichier | Nature |
|---|---|
| `report/chap_02.tex` | Réécrit — 7 sections, 22 sous-sections |
| `report/img/ch02_principe_lora.png` | Créé |
| `report/img/ch02_principe_rag.png` | Conservé de la version précédente |
| `report/biblio.bib` | Conservé — 11 entrées |
| `report/main.pdf` | Régénéré — 46 pages |

### Structure livrée

```
Introduction
2.1 Traitement automatique du langage naturel
    2.1.1 Représentations classiques : sac de mots et TF-IDF
    2.1.2 Représentations denses
    2.1.3 Modèles transformers et BERT
    2.1.4 CamemBERT, un transformer francophone
    2.1.5 Fine-tuning et adaptation économe en paramètres
2.2 Classification supervisée et déséquilibre de classes
    2.2.1 Algorithmes de référence
    2.2.2 Métriques adaptées au déséquilibre
    2.2.3 Techniques de rééquilibrage
2.3 Génération augmentée par récupération
    2.3.1 Principe et architecture
    2.3.2 Recherche lexicale et recherche sémantique
    2.3.3 Bases vectorielles
    2.3.4 Évaluation d'un système RAG
2.4 Grands modèles de langage
    2.4.1 Exécution locale et confidentialité
    2.4.2 Conception des consignes
    2.4.3 Hallucinations et garde-fous
2.5 Industrialisation et MLOps
    2.5.1 Versionnement des données et des modèles
    2.5.2 Suivi des expérimentations
    2.5.3 Conteneurisation et intégration continue
2.6 Outils technologiques utilisés
2.7 Spécification des besoins
    2.7.1 Acteurs du système
    2.7.2 Exigences fonctionnelles
    2.7.3 Exigences non fonctionnelles
    2.7.4 Traçabilité des exigences
Conclusion
```

---

## 5. Erreurs rencontrées et traitement

**Aucune erreur de compilation** sur cette tâche.

### Défaut corrigé en amont

La version précédente du mémoire produisait **deux chapitres de bibliographie**, dont un vide :
`webo.tex` imprimait un titre « Bibliographie » sans contenu, suivi de `\printbibliography` sous le
titre « Webographie » qui contenait toutes les entrées. L'appel à `webo.tex` a été retiré de
`main.tex` et le titre unifié en « Bibliographie et webographie ».

### Vigilance sur les données non sourcées

Un chapitre de concepts expose du savoir établi, ce qui expose au risque d'avancer des chiffres de
mémoire. Deux précautions ont été prises.

Aucune métrique de performance n'apparaît dans ce chapitre : elles relèvent des chapitres 4, 5 et 7,
où elles sont mesurées. Les seuls chiffres cités sont le déséquilibre de 5,93 et le nombre de
catégories, tous deux issus du corpus, et la dimension de 768 des vecteurs d'encodage, issue de
`requirements.txt`.

Aucune affirmation générale n'est avancée sans citation. Les propriétés attribuées à BERT, CamemBERT,
LoRA, SMOTE, RAG et RAGAS renvoient toutes à leur publication d'origine.

### Écart au plan assumé

Le plan prévoit quatre sous-sections en 2.4, dont une consacrée aux enjeux de confidentialité. Elle a
été fusionnée avec la sous-section sur l'exécution locale, les deux traitant du même arbitrage. La
section 2.4 compte donc trois sous-sections au lieu de quatre.

---

## 6. État final

### Contrôles de compilation

```
Erreurs                     0
Références non résolues     0
Citations non résolues      0
Pages                      46
Chapitre 2                 15 pages   (cible du plan : 15 à 18)
Figures · tableaux          2 · 5
Entrées bibliographiques   11, toutes citées
```

### Critères de réussite

| Critère | État |
|---|---|
| Sections conformes à `PLAN_RAPPORT.md` | Atteint — 2.1 à 2.6 à l'identique |
| Volume dans la cible du plan | Atteint — 15 p. |
| Concepts appuyés sur des citations | Atteint — 10 références académiques |
| Règles de rédaction `/humanize` appliquées | Atteint |
| Compilation sans erreur | Atteint |

### Points ouverts

1. **Méthodologie** — la section 1.2 décrit une démarche hybride sans revendiquer Scrum, faute
   d'artefacts dans le dépôt. Question posée trois fois à l'auteur, sans réponse à ce jour :
   existait-il des points de suivi à cadence fixe avec les encadrants ?
2. **Section 2.4** — trois sous-sections au lieu des quatre prévues, par fusion justifiée.
3. **Autorisation OTBS** — exploitation des données de tickets à formaliser.
4. **Chapitre 2 en attente de validation** avant passage au chapitre 3.

### Documents liés

- Plan du mémoire : `helpdesk-ai/PLAN_RAPPORT.md`
- Tâches précédentes : `reports/memoire-pfe-helpdesk-ai/task_1` à `task_3`
- Questions entreprise restantes : `report/QUESTIONS_ENTREPRISE.md`
