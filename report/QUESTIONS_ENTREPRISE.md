# Questions à poser à OTBS — liste consolidée et unique

> À transmettre **en une seule fois** à l'encadrant professionnel.
> Établie après dépouillement du PPTX d'intégration, du site www.onetech-bs.com et des
> fichiers du dépôt. Ne figurent ici que les informations **introuvables** dans ces trois sources.
> Date : 2026-08-18 · **Point de situation au 2026-09-08** · Mémoire PFE HelpDesk AI — M. A. Toukabri

---

## Point de situation au 2026-09-08 — ce que l'absence de réponses coûte aujourd'hui

Le questionnaire n'a toujours pas été transmis. La rédaction a avancé sans lui : l'introduction
et les chapitres 1 à 4 sont écrits, 77 pages compilent sans erreur. Le prix payé est mesurable.

| Effet | Détail |
|---|---|
| **Chapitre 1 sous sa cible** | 8 pages rédigées pour une cible de 12 à 15. Les sous-sections prévues sur l'organisation du service (Q5), le positionnement du stagiaire (Q6) et le processus antérieur (Q10) sont absentes ou réduites à une phrase |
| **Chiffres d'ouverture non confirmés** | Le temps de traitement de 30 à 45 minutes (Q4) et la volumétrie (Q3) sont cités comme ordres de grandeur. Ce sont les chiffres qui justifient l'existence du projet |
| **Page de garde provisoire** | Les noms des encadrants (Q7, Q12) sont renseignés sous réserve dans `global_config.tex` |
| **Publication du corpus en suspens** | Sans réponse à Q1 et Q2, aucun extrait de ticket réel ni statistique nominative ne peut figurer au mémoire. Les chapitres 3 et 4 ont été rédigés en n'exposant que des agrégats |
| **Chapitre 7 amputé** | Sans Q20, la section « étude utilisateur » se limite à l'étude légère menée en interne |
| **Risque suivi** | Ce point est enregistré comme **R-26** dans [../helpdesk-ai/RISKS.md](../helpdesk-ai/RISKS.md) |

**Priorité si une seule occasion se présente** : Q1, Q2, Q3, Q4, Q5, Q7, Q9. Ces sept réponses
débloquent le chapitre 1, l'introduction, la conclusion et la page de garde.

---

## A. BLOQUANT — la rédaction s'arrête sans ces réponses

| # | Question | Sert à | Pourquoi c'est bloquant |
|---|---|---|---|
| Q1 | Ai-je l'autorisation d'exploiter les données de tickets réels d'OTBS dans un mémoire déposé et soutenu publiquement ? | Ch. 3.2, 3.6 · transversal | Le corpus est le cœur du mémoire. Sans autorisation écrite, aucun extrait ni statistique ne peut être publié. |
| Q2 | Quels champs doivent être anonymisés ou retirés ? Le fichier source contient `Demandeur`, `Assigné à`, `Filiale`, `CID` — donc des noms de collaborateurs et des identifiants de filiales. | Ch. 3.2.2, 3.6.2 · captures d'écran | Détermine ce qui peut apparaître dans les tableaux, les figures et les copies d'écran. |
| Q3 | Quelle est la volumétrie réelle de tickets traitée par le service : par jour, par semaine ou par mois ? | Ch. 1.2.2 · Introduction générale | C'est le chiffre qui justifie l'existence même du projet. |
| Q4 | Le temps de traitement moyen d'un ticket est-il bien de **30 à 45 minutes** ? Cette fourchette figure dans `CADRAGE_SRS.md` mais y est marquée « à confirmer ». | Ch. 1.2.2 · Introduction · Conclusion | Chiffre cité en ouverture du mémoire ; s'il est faux, tout le raisonnement sur le gain attendu tombe. |
| Q5 | Comment le service IT / Support est-il organisé ? Combien de personnes, quels niveaux (N1/N2/N3), quel rattachement hiérarchique ? Un organigramme même simplifié suffirait. | Ch. 1.1.3 · Figure 1.x | Le plan prévoit une sous-section et une figure dédiées. |
| Q6 | Où étais-je positionné dans cette organisation : quelle équipe, quel rattachement, quel périmètre de mission ? | Ch. 1.1.4 | Sous-section obligatoire dans les deux rapports de référence. |
| Q7 | Quels sont le **nom exact et la fonction** de mon encadrant professionnel chez OTBS ? | Page de garde · Signatures · Remerciements | Figure sur la couverture et sur la page d'autorisation de dépôt. |
| Q8 | Quel outil de ticketing était utilisé avant le projet ? Le fichier exporté comporte les colonnes `Type d'élément` et `Chemin d'accès`, typiques d'un export de liste SharePoint — est-ce bien la source ? | Ch. 1.2.2, 1.2.3 · Ch. 3.2.1 | Le plan consacre une sous-section entière aux données sources et à l'étude de l'existant. |
| Q9 | Quelles sont les **dates exactes** de début et de fin de stage ? | Page de garde · Ch. 2.7.4 (planning, diagramme de Gantt) | Le planning en sprints doit être daté, pas relatif. |
| Q10 | Quel est le processus de traitement d'un ticket **avant** le projet, étape par étape : réception, qualification, affectation, résolution, clôture ? Existe-t-il des SLA formels ? | Ch. 1.2.2 · Figure 1.x | Sans ce processus, l'« étude de l'existant » se résume à une affirmation non étayée. |

---

## B. BLOQUANT — côté école (TEK-UP), pas OTBS

| # | Question | Sert à |
|---|---|---|
| Q11 | Intitulé exact du diplôme et de la filière. | Page de garde |
| Q12 | Nom et fonction exacte de l'encadrant académique — je pars sur **Monsieur Ahmed Dhouibi**, à confirmer. | Page de garde · Signatures · Remerciements |
| Q13 | Année universitaire à afficher (2025–2026 ?). | Page de garde |
| Q14 | Date prévue de la soutenance. | Planning · Conclusion |

---

## C. SOUHAITABLE — améliore nettement le rendu, contournable

| # | Question | Sert à |
|---|---|---|
| Q15 | Effectif exact du service IT / Support. | Ch. 1.1.3 |
| Q16 | Les 8 catégories de tickets (Microsoft, Réseau, Système, Sécurité, Infrastructure, Applicatifs, Backup, Communication) correspondent-elles à un référentiel interne officiel, et qui les a définies ? | Ch. 1.2.3 · Ch. 3.2.3 |
| Q17 | Puis-je citer nommément les clients et partenaires affichés sur le site public (Attijari Bank, BIAT, UBCI, STB, TopNet, Four Seasons, Banque Zitouna ; Microsoft, Red Hat, NetApp, Trend Micro…) ? | Ch. 1.1.2 |
| Q18 | Existe-t-il un logo OTBS en haute définition et une charte graphique ? Le logo actuel a été extrait du PPTX d'intégration. | Page de garde · `report/img/` |
| Q19 | Le projet a-t-il vocation à être déployé en interne ? Sous quelles conditions ? | Conclusion · Perspectives |
| Q20 | Des utilisateurs du service ont-ils testé l'application ? Un retour, même informel, serait précieux. | Ch. 7.6.2 (étude utilisateur) |
| Q21 | Puis-je citer les chiffres publics du groupe et d'OTBS relevés sur le site et dans le PPTX (150 collaborateurs, 300+ clients, 100+ projets/an, 37 MDT / 11 M€, 40 ans ; groupe : 4 500+ collaborateurs, 325 M€ en 2023, 50+ pays) ? | Ch. 1.1.1, 1.1.2 |
| Q22 | Y a-t-il des contraintes particulières à respecter dans la présentation d'OTBS (formulation officielle, éléments à ne pas mentionner) ? | Ch. 1.1 |

---

## Ce que je n'ai PAS besoin de demander — déjà collecté

**Depuis le PPTX d'intégration (12 diapositives)**
Slogan « PARTNER IN YOUR DIGITAL TRANSFORMATION » · OneTech Group : 40 ans, 325 M€ de
chiffre d'affaires en 2023, 50+ pays, 4 500+ collaborateurs, secteurs automobile / énergie /
industrie, métiers câble, mécatronique et TIC · OTBS : 40 ans, 150 collaborateurs, 300+ clients,
100+ projets par an, 37 MDT (11 M€), présence Afrique–Europe · les six lignes de métier ·
carte des implantations (figure récupérée) · règlement interne (télétravail, horaires, matériels,
accès, assiduité, conduite, badges, parking, pause) · politique qualité et sécurité
(confidentialité, sauvegarde, bureau propre, Wi-Fi, monitoring, vigilance) · logo (extrait) ·
adresse de support support.otbs@onetech-group.com

**Depuis www.onetech-bs.com**
Positionnement « premier intégrateur leader dans les solutions IT et Télécom » · le détail des
offres de services · certifications ISO 9001 et ISO 27001 · démarche en quatre étapes
(diagnostic, choix de la solution, déploiement, maintenance) · partenaires technologiques ·
références clients · siège 16 rue des Entrepreneurs, 2035 Charguia II, Tunis ·
(+216) 39 140 000 · contact.otbs@onetech-group.com

**Depuis le dépôt**
Problématique, questions de recherche, hypothèses, objectifs SMART, 17 exigences
fonctionnelles, 14 exigences non fonctionnelles, matrice de traçabilité, personas, workflow du
ticket, architecture, décisions techniques, résultats de tous les modèles, métriques RAG,
résultats de tests.
