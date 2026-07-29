# TESTING.md — Stratégie et plan de tests

> Source de vérité : [PLAN.md](PLAN.md). Dernière mise à jour : **2026-07-05** (Phase 12).
> Résultats détaillés et traçabilité par exigence : [CADRAGE_SRS.md](CADRAGE_SRS.md) §5.
>
> ⚠️ Les fonctionnalités ajoutées entre le 2026-07-16 et le 2026-07-29 (boucle RAG live,
> refonte du workflow de traitement des tickets, migration PostgreSQL/ChromaDB) n'ont **aucun
> test automatisé** — vérifiées uniquement en direct (curl + navigateur). Voir R-18 dans
> [RISKS.md](RISKS.md).

## 1. Pyramide de tests
```
        E2E (peu)      → parcours client/admin complet
     Intégration       → API + BDD + modèle + RAG
  Unitaires (beaucoup) → preprocessing, services, RAG, schémas
```

## 2. Outils
- **pytest** (+ `pytest-cov`) pour Python.
- **httpx / TestClient FastAPI** pour les tests d'API.
- **Vitest** (déjà présent) pour le frontend Angular.
- **Locust** (ou k6) pour les tests de charge.
- **RAGAS** pour l'évaluation du RAG (Phase 7).

## 3. Tests par couche

### 3.1 Unitaires (41 tests — `tests/test_*.py`)
- [x] `clean_text()` et `build_text_for_*` (cas accents, URLs, IP, vides) — `test_preprocess.py` (16)
- [x] Heuristiques (mots-clés → catégorie) — `test_heuristics.py` (8)
- [x] RAG lexical : retrieval, seuils, fallback, déduplication — `test_rag_engine.py` (8)
- [x] RAG hybride : fusion de scores, save/restore — `test_hybrid_engine.py` (9)
- [ ] Schémas Pydantic (validation entrée/sortie) — pas de tests dédiés (couverts indirectement par les tests d'intégration)

### 3.2 Intégration (18/18 tests — `test_api_integration.py`)
- [x] `POST /tickets` → prédiction + RAG + persistance
- [x] Auth (register/login/JWT, RBAC) — bloqué par bug bcrypt/passlib jusqu'au correctif Phase 12
- [ ] Workflow d'approbation (transitions de statut valides/invalides) — pas de test dédié aux transitions
- [ ] Historique (`TicketHistory`) — pas de test dédié
- [x] `/ingest` (après correction) — 4 tests (API key, validation)

### 3.3 End-to-end
- [x] Test manuel navigateur (login client réel) — Phase 12, a révélé le bug bcrypt
- [ ] Parcours complet automatisé création→validation→résolution→restitution — non automatisé, seulement manuel

### 3.4 Tests IA / modèle
- [x] Métriques mesurées : F1-macro=0.685, rappel Sécurité=0.364 — ⚠️ non représentatif, voir R-14 dans [RISKS.md](RISKS.md) (split de test sans exemples Backup/Communication)
- [ ] Test de calibration (ECE sous seuil) — non fait ; couverture/précision du seuil de routage restées à l'état d'estimation (EF-05)
- [x] Tests RAG (RAGAS simplifié) sur jeu d'évaluation — `metrics/rag_eval.json` (Phase 7)

### 3.5 Performance
- [x] Latence prédiction P95 ≤ 300 ms — **non atteint** (330ms séquentiel → 15s à c=20), cause identifiée, `scripts/load_test.py` + `metrics/load_test.json`
- [ ] Latence RAG (avec génération) P95 ≤ 3 s — non isolable (génération template-based, pas de LLM externe)
- [x] Débit sous charge — mesuré à 3 niveaux de concurrence (1/5/20), dégradation forte documentée

## 4. Critères de passage (gates)
- Couverture de tests : **74 % en local** (`pytest --cov=src --cov=api`, 59 tests, cible ≥ 70 %
  atteinte) mais **22 % seulement reproductible en CI** (41 tests unitaires : `test_api_integration.py`
  exclu car `models/best_pipeline.pkl` est gitignoré et absent d'un clone frais). Le gate n'est
  donc pas encore vérifié automatiquement par la CI telle que configurée aujourd'hui.
- Toute exigence (SRS) a au moins un test associé : voir matrice complète dans
  [CADRAGE_SRS.md](CADRAGE_SRS.md) §5 — 9/17 EF et 5/14 ENF pleinement atteints, le reste
  partiel/non fait/backlog (assumé, pas oublié).
- Aucun test cassé avant de marquer une tâche « Terminé » (cf. DoD) — respecté tout au long de la Phase 12.
