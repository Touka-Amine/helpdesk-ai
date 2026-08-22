# PFE_PROGRESS.md — Suivi académique du mémoire

> Suivi des livrables académiques (mémoire, diagrammes, soutenance). Chapitres alignés sur
> [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md). Source de vérité projet : [PLAN.md](PLAN.md).
> Dernière mise à jour : *à la création*.

## 1. Avancement des chapitres du mémoire

| # | Chapitre | Phase(s) source | État | Notes |
|---|---|---|---|---|
| 1 | Introduction générale | 1 | 🟡 | Ébauché via `CADRAGE_SRS.md` (problématique, objectifs) |
| 2 | État de l'art & existant | 1 | 🟡 | Synthèse dans `CADRAGE_SRS.md` + cahier des charges |
| 3 | Analyse & spécification des besoins | 1 | 🟡 | EF/ENF + traçabilité dans `CADRAGE_SRS.md` |
| 4 | Conception & architecture | — | 🟡 | S'appuie sur [ARCHITECTURE.md](ARCHITECTURE.md) |
| 5 | Données & gouvernance | 2 | 🔴 | RGPD, qualité, DVC |
| 6 | Modélisation IA (NLP) | 3,4,5 | 🔴 | Baseline et CamemBERT+LoRA terminés côté code — chapitre pas encore rédigé. **Comparaison à citer : 0,5673 (baseline) vs 0,5685 (CamemBERT)**, même split stratifié 8 classes. Le 0,685 du protocole DVC ne couvre que 5/8 classes (R-14) et ne doit pas servir de base de comparaison |
| 7 | Système RAG | 6,7 | 🔴 | Sémantique + RAGAS |
| 8 | LLM, fine-tuning & prompting | 5,7 | 🔴 | LoRA, prompts, guardrails |
| 9 | MLOps & LLMOps | 10 | 🔴 | DVC, MLflow, monitoring |
| 10 | Développement applicatif | 8,9 | 🟡 | API + front |
| 11 | Déploiement & infrastructure | 11 | 🔴 | Docker, CI/CD |
| 12 | Évaluation & validation | 12 | 🔴 | Résultats, benchmark |
| 13 | Gestion de projet | 0 | 🟡 | Planning, risques |
| 14 | Conclusion & perspectives | 14 | 🔴 | Limites, backlog |

## 2. Diagrammes à produire
- [ ] Diagramme de contexte
- [ ] C4 (contexte / conteneurs / composants)
- [ ] Cas d'utilisation (UML)
- [ ] Diagramme d'activité (workflow ticket)
- [ ] Diagramme de séquence (création → prédiction → RAG → validation)
- [ ] Diagramme d'états (statut ticket)
- [ ] Diagramme de classes (User, Ticket, TicketHistory, Feedback, KBDocument)
- [ ] Diagramme de déploiement
- [ ] Pipelines (données / MLOps / RAG / fine-tuning)
- [ ] Matrice de confusion + courbes (PR, calibration)
- [ ] Gantt (planning 6 mois)

## 3. Livrables jury
- [ ] Mémoire (PDF)
- [ ] Cahier des charges (✅ rédigé, à finaliser)
- [ ] Code source + README reproductible
- [ ] Démonstration (live + vidéo de secours)
- [ ] Slides de soutenance
- [ ] Annexes (model cards, data card, ADR, contrat OpenAPI, résultats RAGAS)

## 4. Échéances relatives (stage 6 mois)
| Mois | Jalon académique |
|---|---|
| 1 | Cadrage validé, chapitres 1–3 ébauchés |
| 2 | Données + baseline documentées (ch. 5–6) |
| 3 | Fine-tuning CamemBERT rédigé (ch. 6) |
| 4 | RAG + évaluation rédigés (ch. 7–8) |
| 5 | App + MLOps + déploiement rédigés (ch. 9–11) |
| 6 | Évaluation finale (ch. 12), conclusion, mémoire complet, soutenance |
