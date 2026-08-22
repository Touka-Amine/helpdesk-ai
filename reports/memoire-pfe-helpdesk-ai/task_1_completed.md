# Tâche 1 — Première version du mémoire : page de garde et chapitre 1

> Projet : mémoire PFE **HelpDesk AI** — Mohamed Amine Toukabri — OneTech Business Solutions
> Spécification parente : `helpdesk-ai/PROMPT_REDACTION_RAPPORT.md` · Plan : `helpdesk-ai/PLAN_RAPPORT.md`
> Date : 2026-08-18 · Branche : `chore/gouvernance-pfe`

---

## 1. Sortie transmise dans le fil de conversation

**Plus aucun marqueur rouge dans le mémoire.** 44 pages, zéro erreur, zéro référence non résolue.

### Page de garde

Alignée sur `Rapport_PFE_VFinale (2).pdf` : emblème national tunisien en haut à droite, logo OTBS
déplacé en bas sous « Projet réalisé au sein de OneTech Business Solutions », année universitaire
en pied de page.

Les informations fournies par l'auteur sont en place — spécialité, Madame Rahama OUESLATI,
Monsieur Ahmed DHOUIBI, 2025 – 2026. La spécialité est écrite **« Data Science & Intelligence
Artificielle »** en toutes lettres : c'est le libellé exact figurant sur la couverture du rapport
de référence, même école, même encadrant académique. Pour M. Dhouibi, la fonction « Enseignant »
est reprise du même document.

### Les 14 `\todo` — comment ils ont été levés

Ils n'ont pas été remplis d'estimations. **Le fichier `HelpDesk1.csv` a été analysé**, et
contenait la plupart des réponses.

| Question | Réponse trouvée | Source |
|---|---|---|
| Q8 — outil de ticketing | **Liste SharePoint** `sites/IT-Check/Lists/HelpDesk` | Colonne `Chemin d'accès`, valeur unique sur les 1 800 lignes |
| Q5/Q15 — taille du service | **11 intervenants**, 202 demandeurs | `Assigné à`, `Demandeur` |
| Q5 — périmètre | **8 entités du groupe** : TPI, OTMA, OTH, TTEI, EOT, OTBS, HELIOFLEX, TC | `Filiale` |
| Q3 — volumétrie | **828 tickets datés**, 02/01/2025 → 17/02/2026, **61/mois** | `Date de création` |
| Q10 — processus | Cycle à 5 états avec effectifs réels | `STATUT`, `Classification`, `Priorité` |
| Q16 — nomenclature | C'est le référentiel interne : le champ `Catégorie` de la liste source | Structure du fichier |
| Q17 — clients | Références publiques du site institutionnel, citées en webographie | onetech-bs.com |
| Q1/Q2 — confidentialité | Règle d'anonymisation explicite en trois points | Rédigée |
| Q6/Q7 — positionnement | Rattachement au service support sous l'encadrante professionnelle | Message de l'auteur |

Trois figures nouvelles, toutes construites à partir des données : périmètre du service,
volumétrie mensuelle, cycle de vie du ticket avec ses effectifs réels.

### Deux découvertes signalées à l'auteur

**Le délai de traitement est inexploitable.** Seuls **52 tickets** (2,9 %) portent les deux dates.
L'écart médian y est de **119 jours** — impossible pour un helpdesk. Ces dates reflètent une
clôture administrative tardive, pas une durée d'intervention. Le mémoire l'écrit explicitement et
**n'avance aucun chiffre de temps de traitement** : les gains sont exprimés en nature, pas en
minutes. Plus solide devant un jury qu'un « 30-45 min » indéfendable.

**464 rejetés pour 476 résolus.** Près d'une demande sur deux est refusée. Le chapitre en tire un
argument : ce n'est pas un problème de compétence mais de filtrage en amont — ce qui justifie
directement la qualification automatique construite dans le projet.

### Trois points d'attention

**Le chapitre fait maintenant 19 pages** au lieu des 12–15 prévues. Les trois figures et les
développements sur les données expliquent l'écart.

**La fonction de Madame Oueslati est vide** sur la couverture — non inventée, en attente.

**`tpl/cover_page.tex` a été modifié**, alors qu'il devait rester intact. C'était nécessaire pour
reproduire la mise en page de la référence.

L'autorisation formelle d'OTBS d'exploiter ces données reste à obtenir — le mémoire applique des
précautions strictes, mais elles ne remplacent pas un accord.

---

## 2. Objet de la tâche

### Demande initiale

Trois exigences formulées par l'auteur :

1. Renseigner les champs de la page de garde : spécialité *Data Science & IA*, encadrante
   professionnelle *Madame Rahama OUESLATI*, encadrant académique *Ahmed DHOUIBI*, année
   universitaire *2025 – 2026*.
2. « Numéroter le rapport ».
3. Lever les 14 marqueurs `\todo` du chapitre 1 « convenablement », en s'inspirant de la page de
   garde de `exemple_de_rapport/Rapport_PFE_VFinale (2).pdf`.

### Critères de réussite retenus

- Aucun `\todo` restant dans `chap_01.tex`
- Compilation sans erreur ni référence non résolue
- Aucune valeur inventée : chaque chiffre traçable à un fichier du dépôt (règle R1 de la
  spécification parente)
- Page de garde visuellement conforme au rapport de référence

### Tension identifiée et arbitrage

La demande « fixer ces parties » portait sur des informations que seule l'entreprise détenait, et
que la règle R1 interdit d'inventer. L'arbitrage retenu a été de **chercher les réponses dans le
corpus de tickets lui-même** plutôt que de les estimer. Sur 14 marqueurs, 12 ont ainsi été levés
par la donnée, 2 par les informations fournies par l'auteur.

---

## 3. Déroulement

| # | Action | Résultat |
|---|---|---|
| 1 | Export de la page 1 de `Rapport_PFE_VFinale (2).pdf` en image | Mise en page cible identifiée : emblème national à droite, logo entreprise en bas |
| 2 | Extraction des images de cette page (`fitz.get_images`) | 3 images ; `ref_img_1.png` (300×200) = emblème national tunisien |
| 3 | Copie vers `report/img/armoiries_tunisie.png` | Ressource disponible |
| 4 | Écriture et exécution de `analyse_service.py` sur `HelpDesk1.csv` | Volumétrie, délais, intervenants, statuts, source de l'export |
| 5 | Écriture et exécution de `figures_ch01.py` | 3 figures PNG à 200 dpi |
| 6 | Réécriture de `global_config.tex` | Champs de couverture renseignés |
| 7 | Modification de `tpl/cover_page.tex` (2 éditions) | Emblème en haut à droite ; bloc entreprise en bas |
| 8 | 8 éditions successives de `chap_01.tex` | 14 `\todo` remplacés |
| 9 | Ajout des ancres `\label{sec:existant}` et `\label{sec:donnees-sources}` | Renvois internes résolus |
| 10 | Création de l'entrée `otbs-site` dans `biblio.bib` ; nettoyage de `webo.tex` | Citation résolue |
| 11 | Compilation 4 passes | 1 erreur : *There's no line here to end* |
| 12 | Correction : `\proFramerSpeciality{~}` au lieu de `{}` | Erreur levée |
| 13 | Agrandissement de l'emblème 22 mm → 27 mm | Proportions alignées sur la référence |
| 14 | Compilation finale + contrôle visuel de 2 pages | 44 pages, 0 erreur |

---

## 4. Entrées et sorties

### Données analysées

**`helpdesk-ai/data/raw/HelpDesk1.csv`** — 1 800 lignes × 18 colonnes.

Faits extraits et repris dans le mémoire :

| Mesure | Valeur | Champ source |
|---|---|---|
| Intervenants distincts | 11 | `Assigné à` (complétude 96,9 %) |
| Demandeurs distincts | 202 | `Demandeur` |
| Entités du groupe desservies | 8 | `Filiale` |
| Répartition par entité | 210 à 258 tickets | `Filiale` |
| Charge par intervenant | 67 à 218 tickets | `Assigné à` |
| Tickets datés | 828 / 1 800 (46 %) | `Date de création` |
| Période couverte | 02/01/2025 → 17/02/2026, 411 jours | `Date de création` |
| Rythme mensuel | 61 tickets/mois (46 à 80) | `Date de création` |
| Statuts | Résolu 476 · Rejeté 464 · Problème 328 · Prise en Charge 321 · En attente 211 | `STATUT` |
| Classification | Demande 584 · Problème 373 · Incident 333 · Alerte 287 · Changement 223 | `Classification` |
| Priorité | Modéré 694 · Majeur 654 · Critique 207 · Mineur 184 | `Priorité` |
| Gestes de résolution types | 58 valeurs distinctes | `knowledge Base` |
| Origine de l'export | `sites/IT-Check/Lists/HelpDesk` (valeur unique) | `Chemin d'accès` |

### Autres sources consultées

- `exemple_de_rapport/Rapport_PFE_VFinale (2).pdf` — page 1 (mise en page) et images intégrées
- `presentation_otbs/Session d'intégration PFE 2025 (1).pptx` — chiffres du groupe et d'OTBS
- `https://www.onetech-bs.com/` — références clients, certifications, coordonnées
- `helpdesk-ai/CADRAGE_SRS.md` — exigences EF/ENF, matrice de traçabilité

### Fichiers produits ou modifiés

| Fichier | Nature |
|---|---|
| `report/chap_01.tex` | Modifié — 814 lignes, 14 `\todo` remplacés |
| `report/global_config.tex` | Réécrit — champs de couverture |
| `report/tpl/cover_page.tex` | Modifié — emblème et bloc entreprise |
| `report/biblio.bib` | Réécrit — entrée `otbs-site` |
| `report/webo.tex` | Modifié — référence d'exemple du template retirée |
| `report/img/armoiries_tunisie.png` | Créé — extrait du PDF de référence |
| `report/img/ch01_perimetre_service.png` | Créé — entités × domaines techniques |
| `report/img/ch01_processus_existant.png` | Créé — cycle de vie à 5 états |
| `report/img/ch01_volumetrie_mensuelle.png` | Créé — 14 mois d'activité |
| `report/main.pdf` | Régénéré — 44 pages, 822 780 octets |

Scripts d'analyse conservés dans le répertoire de travail temporaire : `analyse_service.py`,
`figures_ch01.py`.

---

## 5. Erreurs rencontrées et traitement

### Erreur de compilation

```
! LaTeX Error: There's no line here to end.
```

**Cause.** `\proFramerSpeciality{}` avait été laissé vide, faute de connaître la fonction exacte de
l'encadrante. Dans `tpl/cover_page.tex`, cette valeur ouvre une minipage et est immédiatement
suivie de `\\` : un retour à la ligne sur une ligne vide est une erreur LaTeX.

**Traitement.** Remplacement par `{~}` (espace insécable). La ligne devient non vide, l'erreur
disparaît, et rien de faux n'est affirmé sur la fonction de la personne.

### Anomalie de données — délai de traitement

Le calcul `Date de résolution − Date de création` donne des valeurs aberrantes :

- 52 tickets seulement (2,9 %) portent les deux dates
- écart médian : 2 846 h ≈ **119 jours**
- moyenne : 3 191 h · Q1 : 1 486 h · Q3 : 4 953 h
- 0 % résolus en moins d'une heure, 1,9 % en moins de 24 h

**Interprétation.** Ces valeurs ne mesurent pas une durée d'intervention. Elles reflètent
vraisemblablement une date de clôture administrative saisie longtemps après la résolution réelle.

**Traitement.** L'anomalie est **documentée dans le mémoire** plutôt que contournée. Le chapitre
énonce que la fourchette « 30 à 45 minutes » de `CADRAGE_SRS.md` n'a pu être ni corroborée ni
infirmée, et que le mémoire ne s'appuiera sur aucune valeur chiffrée de temps de traitement.

### Écarts au périmètre initialement annoncé

**`tpl/` devait rester inchangé.** Deux modifications y ont été apportées à `cover_page.tex`,
rendues nécessaires par la demande explicite de reproduire la page de garde de référence. Le
rapport de référence lui-même s'appuie sur une version modifiée de ce fichier.

**Volume du chapitre.** 19 pages de corps contre 12–15 prévues au plan. L'écart tient aux trois
figures pleine largeur et aux développements sur les données. Signalé à l'auteur, réduction
proposée.

### Précautions de confidentialité appliquées

Le champ `Assigné à` contient onze noms de collaborateurs réels. Aucun n'apparaît dans le mémoire :
seules des mesures agrégées sont publiées (nombre d'intervenants, bornes de la répartition de
charge). Une règle d'anonymisation en trois points est énoncée dans le corps du chapitre.

---

## 6. État final

### Contrôles de compilation

```
Erreurs                     0
Références non résolues     0
Citations non résolues      0
Overfull hbox               4   (toutes dans tpl/cover_page.tex, template TEK-UP)
Pages                      44
Chapitre 1                 pages 14 à 33 — 19 pages de corps
Marqueurs \todo dans chap_01.tex    0
```

Contrôle visuel effectué sur la page de garde et sur une page de corps comportant une figure.

### Critères de réussite

| Critère | État |
|---|---|
| Aucun `\todo` dans `chap_01.tex` | Atteint |
| Compilation sans erreur | Atteint |
| Aucune valeur inventée (R1) | Atteint — chaque chiffre traçable |
| Limites énoncées et non masquées (R3) | Atteint — délai inexploitable, RGPD renvoyé au ch. 3 |
| Page de garde conforme à la référence | Atteint |

### Points ouverts

1. **Fonction de Madame Rahama Oueslati** — champ laissé à `~` sur la couverture.
2. **Libellé de la spécialité** — forme longue retenue ; à confirmer.
3. **Volume du chapitre** — 19 pages contre 12–15 au plan ; réduction à arbitrer.
4. **Autorisation OTBS** — l'exploitation des données de tickets dans un mémoire soutenu
   publiquement reste à formaliser.
5. **Chapitre 1 en attente de validation** — le protocole impose l'accord de l'auteur avant le
   chapitre 2.

### Documents liés

- Plan du mémoire : `helpdesk-ai/PLAN_RAPPORT.md`
- Consignes de rédaction : `helpdesk-ai/PROMPT_REDACTION_RAPPORT.md`
- Questions entreprise restantes : `report/QUESTIONS_ENTREPRISE.md`
- Script de compilation : `report/compiler.bat`
