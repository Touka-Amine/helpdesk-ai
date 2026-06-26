# TESTING.md — Stratégie et plan de tests

> Squelette à enrichir (Phase 12). Source de vérité : [PLAN.md](PLAN.md). Dernière mise à jour :
> *à la création*.

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

### 3.1 Unitaires
- [ ] `clean_text()` et `build_text_for_*` (cas accents, URLs, IP, vides)
- [ ] Heuristiques (mots-clés → catégorie)
- [ ] RAG : retrieval, seuils, fallback, déduplication
- [ ] Schémas Pydantic (validation entrée/sortie)

### 3.2 Intégration
- [ ] `POST /tickets` → prédiction + RAG + persistance
- [ ] Auth (register/login/JWT, RBAC)
- [ ] Workflow d'approbation (transitions de statut valides/invalides)
- [ ] Historique (`TicketHistory`)
- [ ] `/ingest` (après correction)

### 3.3 End-to-end
- [ ] Création ticket (client) → validation (admin) → résolution → restitution (client)

### 3.4 Tests IA / modèle
- [ ] Non-régression des métriques (F1-macro ≥ seuil)
- [ ] Test de calibration (ECE sous seuil)
- [ ] Tests RAG (RAGAS) sur jeu d'évaluation

### 3.5 Performance
- [ ] Latence prédiction P95 ≤ 300 ms
- [ ] Latence RAG (avec génération) P95 ≤ 3 s
- [ ] Débit cible sous charge

## 4. Critères de passage (gates)
- Couverture unitaire cible : à définir (ex. ≥ 70 % sur `src/` et `api/services/`).
- Toute exigence (SRS) a au moins un test associé (matrice de traçabilité).
- Aucun test cassé avant de marquer une tâche « Terminé » (cf. DoD).
