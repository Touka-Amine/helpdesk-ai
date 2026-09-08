# TESTING.md — Stratégie et plan de tests

> Source de vérité : [PLAN.md](PLAN.md). Dernière mise à jour : **2026-08-22** (industrialisation
> MLOps). Résultats détaillés et traçabilité par exigence : [CADRAGE_SRS.md](CADRAGE_SRS.md) §5.
>
> **133 tests passent** (`python -m pytest tests/ -q`, 2 min 12 s — mesure du 2026-09-08). Pour une exécution rapide pendant
> le développement, `pytest -m "not slow"` exclut les tests qui chargent
> sentence-transformers ou font tourner ChromaDB.
>
> ⚠️ Les fonctionnalités ajoutées entre le 2026-07-16 et le 2026-07-29 (boucle RAG live,
> refonte du workflow de traitement des tickets, migration PostgreSQL/ChromaDB) n'avaient
> **aucun test automatisé**. Le RAG live et le stockage vectoriel sont désormais couverts
> (§3.6) ; les transitions de statut de `approve_ticket()` restent non testées. Voir R-18 dans
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

### 3.1 Unitaires (105 tests — `tests/test_*.py`)
- [x] `clean_text()` et `build_text_for_*` (cas accents, URLs, IP, vides) — `test_preprocess.py` (16)
- [x] Heuristiques (mots-clés → catégorie) — `test_heuristics.py` (8)
- [x] RAG lexical : retrieval, seuils, fallback, déduplication — `test_rag_engine.py` (8)
- [x] RAG hybride : fusion de scores, save/restore — `test_hybrid_engine.py` (9)
- [x] Registre de modèles : enregistrement, promotion, rejet, rollback, lineage, amorçage — `test_model_registry.py` (11)
- [x] Contrôle qualité des connaissances : refus des suggestions IA, longueur, recopie, quasi-doublons — `test_kb_quality.py` (14)
- [x] Porte de promotion : gain minimum, effondrement d'une classe, classes sans support, accuracy — `test_promotion_gate.py` (11)
- [x] Collecte : éligibilité, force de l'étiquette, format corpus, non-export du demandeur — `test_collect.py` (14)
- [x] Construction du dataset : fusion, anti-fuite (titre, description, doublon), versionnement — `test_build_dataset.py` (7)
- [x] Robustesse de la porte : idempotence du stage après suppression des sorties par DVC, refus d'arbitrer sur une métrique absente — `test_promote_idempotence.py` (7)
- [ ] Schémas Pydantic (validation entrée/sortie) — pas de tests dédiés (couverts indirectement par les tests d'intégration)

### 3.2 Intégration (18/18 tests — `test_api_integration.py`)
- [x] `POST /tickets` → prédiction + RAG + persistance
- [x] Auth (register/login/JWT, RBAC) — bloqué par bug bcrypt/passlib jusqu'au correctif Phase 12
- [ ] Workflow d'approbation (transitions de statut valides/invalides) — pas de test dédié aux transitions
- [ ] Historique (`TicketHistory`) — pas de test dédié
- [x] `/ingest` (après correction) — 4 tests (API key, validation)

### 3.3 End-to-end
- [x] Test manuel navigateur (login client réel) — Phase 12, a révélé le bug bcrypt
- [x] **Cycle MLOps complet** — `scripts/mlops_e2e_demo.py` : base de production simulée (60 tickets
      résolus, historique d'admin réaliste) → collecte → dataset versionné → entraînement →
      porte de promotion → registre, puis restauration de l'état du dépôt
- [ ] Parcours complet automatisé création→validation→résolution→restitution — non automatisé, seulement manuel

### 3.4 Tests IA / modèle
- [x] Métriques mesurées en Phase 12 : F1-macro=0.685, rappel Sécurité=0.364 — ⚠️ **valeurs d'avant l'audit des règles du 2026-08-22 ; le pipeline est depuis à 0.5829**. Également non représentatif, voir R-14 dans [RISKS.md](RISKS.md) (split de test ne couvrant que 5 catégories sur 8 : Applicatifs, Backup et Communication absentes)
- [x] **F1-macro sur les classes évaluables = 0.822** (5 classes ayant du support, mesure de Phase 12). Écart avec 0.685
      entièrement dû aux trois classes à support nul, dont la F1 vaut 0.0 par construction
- [x] **Jeu de test gelé** (`data/reference/`, empreinte SHA-256 vérifiée à chaque exécution de
      `split.py`) — condition nécessaire pour que comparer deux modèles ait un sens
- [x] Précision, rappel, support et matrice de confusion par classe — `metrics/ml_eval.json`,
      `metrics/confusion_matrix_candidate.json`
- [ ] Test de calibration (ECE sous seuil) — non fait ; couverture/précision du seuil de routage restées à l'état d'estimation (EF-05)
- [x] Tests RAG (RAGAS simplifié) sur jeu d'évaluation — `metrics/rag_eval.json` (Phase 7)

### 3.5 Évaluation RAG rejouable (`src/pipeline/rag_eval.py`, stage DVC)
- [x] Les **trois** moteurs mesurés sur le même jeu de 80 requêtes issues du test, dont le moteur
      hybride réellement servi en production, jamais évalué auparavant :
      P@3 = **0.354** (hybride), 0.292 (sémantique), 0.154 (lexical)
- [x] Interrogation avec `allow_fallback=True`, la configuration de production. L'évaluation
      précédente mesurait une configuration inutilisée et renvoyait zéro résultat
- [ ] **Jeu annoté absent** — protocole `proxy` (« même catégorie = pertinent ») par défaut, dont le
      rappel n'est pas interprétable et est donc laissé à `null`. Voir R-22.
      `python src/pipeline/rag_eval.py --build-template` génère les 80 requêtes à annoter

### 3.6 Cycle de vie des connaissances (`test_vector_store_lifecycle.py`, 9 tests, marqués `slow`)
- [x] Solution rédigée par un admin indexée avec ses métadonnées de cycle de vie
- [x] **Suggestion IA refusée** et absente de la base — ferme le chemin d'auto-contamination (R-04)
- [x] Quasi-doublon : la nouvelle entrée remplace l'ancienne, marquée `superseded`, rien n'est supprimé
- [x] `query_similar()` n'expose ni les entrées remplacées ni les obsolètes
- [x] Marquage obsolète réversible, statistiques ne comptant que les entrées actives
- [x] Instantané versionné et comparaison entre deux états

### 3.7 Performance
- [x] Latence prédiction P95 ≤ 300 ms — **non atteint** (330ms séquentiel → 15s à c=20), cause identifiée, `scripts/load_test.py` + `metrics/load_test.json`
- [ ] Latence RAG (avec génération) P95 ≤ 3 s — non isolable (génération template-based, pas de LLM externe)
- [x] Débit sous charge — mesuré à 3 niveaux de concurrence (1/5/20), dégradation forte documentée

## 4. Critères de passage (gates)
- Couverture de tests : **74 % en local** (`pytest --cov=src --cov=api`, 59 tests, cible ≥ 70 %
  atteinte) mais **22 % seulement reproductible en CI** (41 tests unitaires : `test_api_integration.py`
  exclu car `models/best_pipeline.pkl` est gitignoré et absent d'un clone frais). Le gate n'est
  donc pas encore vérifié automatiquement par la CI telle que configurée aujourd'hui.
  *2026-09-08 : la suite compte 133 tests (125 au 2026-08-22, puis les tests d'idempotence de la
  promotion et la non-régression de l'audit des règles). La couverture n'a pas été remesurée ; les
  chiffres ci-dessus datent de la Phase 12 et sont donc désormais un plancher.*
- **Gate de promotion d'un modèle** (`src/pipeline/promote.py`, voir [MLOPS.md](MLOPS.md) §3.5) —
  un modèle candidat ne remplace la production que s'il gagne au moins 0.005 sur la métrique
  principale, ne fait perdre plus de 0.05 à aucune classe ayant du support, et ne dégrade pas
  l'accuracy. Les deux modèles sont réévalués dans la même exécution sur le jeu de test gelé.
  Vérifié en pratique : un candidat identique au modèle en service est **rejeté**, et la
  production est restaurée intacte.
- Toute exigence (SRS) a au moins un test associé : voir matrice complète dans
  [CADRAGE_SRS.md](CADRAGE_SRS.md) §5 — 9/17 EF et 5/14 ENF pleinement atteints, le reste
  partiel/non fait/backlog (assumé, pas oublié).
- Aucun test cassé avant de marquer une tâche « Terminé » (cf. DoD) — respecté tout au long de la Phase 12.
