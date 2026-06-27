# TASKS.md — Tâches de la phase active

> Tâches du sprint courant. Détail complet des checklists dans [PLAN.md](PLAN.md) (section 6).
> Dernière mise à jour : **2026-06-27**. **Phase active : Phase 6 — RAG sémantique.**

## 🔵 En cours / prochaine
- [ ] **Phase 7 — Évaluation RAG (RAGAS)** : construire le jeu d'évaluation (requêtes + vérités terrain)
  → mesurer Precision@k / Recall@k → RAGAS (Faithfulness, Answer Relevancy, Context Precision/Recall)
  → implémentation génération de réponse avec citations → LLM-as-a-Judge → comparatif lexical vs sémantique.

## ⚪ À faire (Phase 2 — reliquat Data Engineering & RGPD)
- [ ] Anonymisation des PII + registre de traitement RGPD
- [ ] Écrire les stages DVC (preprocess → split → rag)
- [ ] Dictionnaire de données + data card

## ✅ Terminé — Phase 6 (RAG sémantique FAISS, 2026-06-27)
- [x] ADR-004 décidé : FAISS local (pas ChromaDB/Weaviate)
- [x] `src/rag/semantic_engine.py` — `SemanticRAGEngine` FAISS + `paraphrase-multilingual-mpnet-base-v2`
- [x] `notebooks/06_rag_semantique.ipynb` — pipeline complet + évaluation réaliste (query = titre+desc)
- [x] Score cosinus top-1 : **0.93 sémantique vs 0.76 lexical (+0.17)**, couverture 100 %
- [x] Sauvegarde index + metadata + figure comparaison

## ✅ Terminé — Phase 5 (CamemBERT LoRA + features enrichies, 2026-06-27)
- [x] Features enrichies `text_enriched` (priorité 4→3, classification 5→3) dans `02_preprocessing.ipynb`
- [x] Fine-tuning CamemBERT-base + LoRA (split anti-fuite, GPU local, FP32)
- [x] Évaluation + benchmark vs TF-IDF — **F1-macro 0.5685** (gain enrichissement +0.036)
- [x] Sauvegarde adaptateur + métadonnées + figures + documentation

## ✅ Terminé — Phase 1 (Cadrage & SRS v0.1, 2026-06-26)
- [x] Problématique + questions de recherche + hypothèses
- [x] Objectifs SMART
- [x] Synthèse état de l'art
- [x] Exigences fonctionnelles (MoSCoW) + critères d'acceptation
- [x] Exigences non-fonctionnelles (métriques + vérification)
- [x] Matrice de traçabilité

## ✅ Terminé — Phase 0 (Initialisation, 2026-06-26)
- [x] Système de pilotage (11 fichiers) · `.gitignore` · DVC vérifié · 4 commits (`chore/gouvernance-pfe`)

## 📌 Dette / à traiter en Phase 2
- `helpdesk-ai/HelpDesk1.csv` (donnée brute en double à la racine) non suivi → décider DVC vs git.

---
*Règle : une seule grosse tâche à la fois. Cocher ici + dans PLAN.md + journaliser dans
[CHANGELOG.md](CHANGELOG.md) à chaque fin de tâche.*
