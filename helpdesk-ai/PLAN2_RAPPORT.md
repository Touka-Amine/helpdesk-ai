# PLAN DU RAPPORT PFE

## Titre du projet

**Plateforme intelligente d’analyse, de classification et d’assistance à la résolution de tickets informatiques**

---

# Introduction générale

- Contexte général du projet
- Problématique
- Objectifs du projet
- Solution proposée
- Méthodologie générale
- Organisation du rapport

---

# Chapitre 1 — Contexte général et présentation du projet

## 1.1 Présentation de l’organisme d’accueil

- Présentation de l’entreprise
- Présentation du service informatique
- Activités et rôle du service concerné

## 1.2 Contexte du projet

- Gestion des tickets informatiques
- Processus actuel de traitement
- Difficultés rencontrées
- Limites de l’existant

## 1.3 Problématique

- Identification du problème
- Enjeux liés à la classification et au traitement des tickets
- Problématique principale du projet

## 1.4 Objectifs du projet

- Objectif général
- Objectifs spécifiques
- Résultats attendus

## 1.5 Solution proposée

- Présentation générale de la plateforme
- Principe de fonctionnement
- Apport de l’intelligence artificielle
- Périmètre du projet

## 1.6 Méthodologie de travail

- Méthodologie adoptée
- Organisation du projet
- Principales étapes de réalisation

## Conclusion du chapitre

---

# Chapitre 2 — Analyse des besoins et conception de la solution

## 2.1 Analyse des besoins

### 2.1.1 Identification des acteurs

### 2.1.2 Besoins fonctionnels

### 2.1.3 Besoins non fonctionnels

## 2.2 Analyse fonctionnelle

### 2.2.1 Diagramme de contexte

### 2.2.2 Diagramme de cas d’utilisation

### 2.2.3 Description des principaux cas d’utilisation

## 2.3 Conception du système

### 2.3.1 Architecture générale de la solution

### 2.3.2 Diagramme de classes

### 2.3.3 Diagramme de séquence du traitement d’un ticket

### 2.3.4 Diagramme d’états du ticket

## 2.4 Choix technologiques

- Backend
- Frontend
- Base de données
- Technologies d’intelligence artificielle
- Technologies RAG
- Outils de déploiement et d’industrialisation

Les technologies doivent être présentées uniquement en fonction de leur rôle dans le projet.

## Conclusion du chapitre

---

# Chapitre 3 — Analyse et préparation des données

## 3.1 Présentation des données

- Sources des données
- Structure du corpus
- Variables disponibles
- Catégories de tickets
- Volume des données

## 3.2 Analyse exploratoire des données

- Distribution des catégories
- Analyse de la longueur des textes
- Analyse des titres et descriptions
- Qualité des données
- Déséquilibre des classes
- Redondance éventuelle

## 3.3 Préparation des données

- Nettoyage des données
- Normalisation
- Traitement des textes
- Gestion des valeurs problématiques
- Enrichissement du texte

## 3.4 Préparation du corpus pour la classification

- Définition de la variable cible
- Séparation entraînement / validation / test
- Prévention de la fuite de données
- Gestion du déséquilibre

## 3.5 Préparation des connaissances pour le RAG

- Sélection des informations pertinentes
- Nettoyage et structuration
- Constitution de la base de connaissances
- Différence entre dataset ML et base de connaissances

## Conclusion du chapitre

---

# Chapitre 4 — Développement et évaluation du système de classification

## 4.1 Formulation du problème de classification

- Définition de la tâche
- Variable cible
- Classes considérées
- Métriques d’évaluation

## 4.2 Approche basée sur TF-IDF

### 4.2.1 Vectorisation des textes

### 4.2.2 Modèles de classification testés

### 4.2.3 Évaluation des modèles

## 4.3 Amélioration par les heuristiques métier

- Motivation
- Principe des règles métier
- Règles appliquées
- Impact sur les performances

## 4.4 Approche basée sur CamemBERT et LoRA

### 4.4.1 Justification du choix de CamemBERT

### 4.4.2 Principe de LoRA

### 4.4.3 Configuration de l’entraînement

### 4.4.4 Résultats obtenus

## 4.5 Comparaison des approches

- Comparaison des performances
- Analyse des résultats
- Avantages et limites de chaque approche

Présenter les résultats principaux dans un tableau comparatif.

## 4.6 Sélection du modèle final

- Critères de sélection
- Modèle retenu
- Justification du choix
- Gestion de la confiance de prédiction
- Routage automatique et validation humaine

## Conclusion du chapitre

---

# Chapitre 5 — Système RAG et assistance intelligente

## 5.1 Présentation du système RAG

- Objectif du RAG dans la plateforme
- Principe général
- Flux de recherche et de génération

## 5.2 Construction de la base de connaissances

- Sources utilisées
- Préparation des connaissances
- Indexation
- Gestion des connaissances historiques et dynamiques

## 5.3 Mise en œuvre de la recherche

### 5.3.1 Recherche lexicale

### 5.3.2 Recherche sémantique

### 5.3.3 Recherche hybride

### 5.3.4 Comparaison des approches

## 5.4 Évaluation du RAG

- Protocole d’évaluation
- Critères et métriques
- Résultats
- Analyse des résultats
- Limites de l’évaluation

## 5.5 Intégration du LLM

- Rôle du LLM
- Modèle utilisé
- Construction du prompt
- Génération de la solution
- Contrôle du contexte fourni au modèle
- Gestion des hallucinations

## 5.6 Apprentissage continu

- Validation des tickets
- Enrichissement des connaissances
- Réutilisation des tickets validés
- Principe d’amélioration progressive du système

## Conclusion du chapitre

---

# Chapitre 6 — Développement et intégration de la plateforme

## 6.1 Architecture applicative

- Organisation du backend
- Organisation du frontend
- Base de données
- Services IA
- Communication entre les composants

## 6.2 Développement du backend

- API REST
- Gestion des tickets
- Gestion des utilisateurs
- Intégration du modèle de classification
- Intégration du RAG
- Intégration du LLM

## 6.3 Développement du frontend

- Interface de création des tickets
- Interface de consultation
- Interface de suivi
- Interface de validation
- Interface d’administration

## 6.4 Workflow de traitement d’un ticket

Présenter le workflow global :

**Création du ticket  
→ Classification  
→ Recherche de connaissances  
→ Proposition de solution  
→ Validation humaine  
→ Résolution  
→ Archivage / enrichissement**

## 6.5 Intégration des composants

- Intégration du pipeline IA
- Intégration de la base de données
- Intégration des services externes
- Communication entre les différents composants

## 6.6 Exemple complet de traitement

Présenter un exemple réel ou représentatif montrant le parcours d’un ticket dans la plateforme.

## Conclusion du chapitre

---

# Chapitre 7 — Industrialisation, tests et validation

## 7.1 Conteneurisation et déploiement

- Docker
- Docker Compose
- Services déployés
- Configuration de l’environnement

## 7.2 Mise en place du MLOps

- Versionnement des données avec DVC
- Suivi des expériences avec MLflow
- Gestion des versions du modèle
- Pipeline d’entraînement
- Évaluation avant promotion
- Principe de réentraînement contrôlé

## 7.3 Tests de la solution

- Tests unitaires
- Tests d’intégration
- Tests fonctionnels
- Tests du pipeline IA
- Tests de l’API
- Tests de l’interface

## 7.4 Validation de la solution

- Vérification des exigences
- Résultats obtenus
- Performances du système
- Analyse des résultats
- Comparaison avec les objectifs initiaux

## 7.5 Limites du système

- Limites liées aux données
- Limites du modèle de classification
- Limites du RAG
- Limites du LLM
- Limites de l’infrastructure
- Limites de l’évaluation

## 7.6 Perspectives

- Amélioration du modèle
- Enrichissement des données
- Amélioration du RAG
- Automatisation du réentraînement
- Monitoring
- Évolutions futures de la plateforme

## Conclusion du chapitre

---

# Conclusion générale

## 1. Synthèse du travail réalisé

## 2. Réponse à la problématique

## 3. Principaux résultats obtenus

## 4. Apports du projet

## 5. Limites

## 6. Perspectives d’évolution

---

# Bibliographie

Références scientifiques, articles, ouvrages et publications utilisés dans le projet.

---

# Webographie

Sources web utilisées pour les technologies, frameworks et outils.

---

# Liste des figures

---

# Liste des tableaux

---

# Liste des acronymes

---

# Annexes

Les annexes peuvent contenir :

- détails techniques importants ;
- configurations ;
- extraits de résultats ;
- exemples supplémentaires ;
- captures d’écran complémentaires ;
- éléments qui seraient trop détaillés dans le corps du mémoire.

---

# Règles générales de rédaction

## 1. Niveau de détail

Le rapport doit être suffisamment détaillé pour démontrer le travail d’ingénierie réalisé, mais ne doit pas devenir une documentation technique exhaustive.

Éviter les sous-sections inutiles.

Ne pas créer plusieurs niveaux de titres pour une idée simple.

Privilégier généralement une profondeur maximale de trois niveaux :

```text
4.1
4.1.1
4.1.2