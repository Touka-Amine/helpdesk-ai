# TASKS.md — Tâches de la phase active

> Tâches du sprint courant. Détail complet des checklists dans [PLAN.md](PLAN.md) (section 6).
> Dernière mise à jour : **2026-06-26**. **Phase active : Phase 1 — Cadrage & SRS (en validation).**

## 🔵 En cours / en attente de toi
- [ ] **Valider les points 🟠 du [CADRAGE_SRS.md](CADRAGE_SRS.md)** : entreprise d'accueil, données
  réelles, contraintes RGPD, date de soutenance, périmètre des EF optionnelles, choix LLM.

## ⚪ À faire (Phase 2 — Data Engineering & RGPD, aperçu)
- [ ] Audit qualité (doublons, NaN, déséquilibre, fuite)
- [ ] Anonymisation des PII + registre de traitement RGPD
- [ ] Écrire les stages DVC (preprocess → split → rag)
- [ ] Dictionnaire de données + data card
- [ ] Décider DVC vs git pour `HelpDesk1.csv`

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
