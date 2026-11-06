# Comment exécuter HelpDesk AI

Guide d'installation et d'exécution, écrit pour quelqu'un qui découvre le projet et
qui part d'un poste vierge. Chaque commande a été vérifiée sur un clone ne contenant
que les fichiers du dépôt.

HelpDesk AI est une plateforme de support informatique qui qualifie automatiquement
un ticket déposé en texte libre et lui associe les cas déjà résolus les plus proches.
Tout s'exécute sur l'infrastructure de l'entreprise : aucune donnée de ticket ne sort
du réseau.

---

## Avant de commencer : ce qui fonctionne, et ce qui demande des fichiers séparés

Le dépôt distribue le code, jamais les données réelles. Un clone fonctionne donc
partiellement, et c'est voulu.

| | Depuis un simple clone |
|---|---|
| L'API démarre et sert des prédictions | **oui** |
| La classification automatique des tickets | **oui**, modèle v1 chargé depuis le registre |
| L'interface web, portail et console d'administration | **oui** |
| La recherche de cas comparables | **dégradée**, repli lexical, voir plus bas |
| Le réentraînement et l'évaluation des modèles | **non**, jeux de données absents |
| La compilation du mémoire LaTeX | **non**, une figure est absente |

Trois fichiers restent hors du dépôt parce qu'ils contiennent des données à caractère
personnel : noms de demandeurs, consultants nommés, codes de filiale.

| Fichier | Ce qu'il débloque |
|---|---|
| `helpdesk-ai/models/semantic_rag/knowledge_base.parquet` | la recherche sémantique de cas comparables |
| `helpdesk-ai/data/splits/*.csv` | le réentraînement et l'évaluation |
| `report/img/ch01_organigramme.pdf` | la compilation du mémoire |

**Demandez-les à Mohamed Amine Toukabri**, par un canal interne, jamais par le dépôt.
Posez-les aux chemins indiqués, rien d'autre à faire.

---

## Prérequis

| Outil | Version | Pourquoi |
|---|---|---|
| Git | une version récente | récupérer le dépôt |
| Docker Desktop | avec Docker Compose v2 | voie recommandée, tout tourne en conteneur |
| Python | **3.11** | voie manuelle uniquement, c'est la version des images et de l'intégration continue |
| Node.js | **20** | voie manuelle uniquement, pour le frontend Angular |

Comptez **8 Go de RAM** disponibles. Le modèle de langage local en consomme à lui seul
près de 3 Go pendant une synthèse.

---

## Étape 1 — Récupérer le projet

```bash
git clone https://github.com/Touka-Amine/helpdesk-ai.git
cd helpdesk-ai
```

Le dépôt pèse 37 Mo. Vous arrivez sur la branche `main`, qui porte l'état complet.

---

## Étape 2 — Créer le fichier de configuration

Le fichier `.env` n'est pas dans le dépôt, c'est lui qui porte les mots de passe.
Partez de l'exemple fourni :

```bash
cp helpdesk-ai/.env.example helpdesk-ai/.env
```

Ouvrez `helpdesk-ai/.env` et remplacez les **quatre valeurs marquées `REMPLACER__`** :

| Clé | Ce qu'il faut y mettre |
|---|---|
| `SECRET_KEY` | une chaîne aléatoire, elle signe les jetons de session |
| `POSTGRES_PASSWORD` | le mot de passe de la base, que vous choisissez |
| `INGEST_API_KEY` | une chaîne aléatoire, elle protège le point d'entrée des tickets par courriel |
| `SMTP_PASSWORD` | le mot de passe du compte d'envoi, **laissez tel quel** si vous ne branchez pas la messagerie |

Pour produire une valeur aléatoire correcte :

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Le reste du fichier a des valeurs par défaut utilisables telles quelles. Sans compte
SMTP configuré, tout fonctionne sauf la réinitialisation de mot de passe par courriel.

---

## Étape 3 — Démarrer, voie Docker (recommandée)

Depuis la racine du dépôt :

```bash
docker compose -f helpdesk-ai/docker/docker-compose.yml up --build
```

Quatre conteneurs démarrent : `ollama`, `postgres`, `api`, `frontend`. La première
construction prend une dizaine de minutes, le temps de télécharger les images et
d'installer les dépendances Python.

| Service | Adresse |
|---|---|
| Interface web | http://localhost:8081 |
| Documentation interactive de l'API | http://localhost:8000/docs |
| Contrôle de santé | http://localhost:8000/api/v1/health |

### Étape 3 bis — Télécharger le modèle de langage

**Cette étape est obligatoire et elle n'est pas automatique.** Le conteneur Ollama
démarre vide. Sans modèle, l'assistant de rédaction reste muet, le reste fonctionne.

Dans un second terminal, une fois les conteneurs lancés :

```bash
docker compose -f helpdesk-ai/docker/docker-compose.yml exec ollama ollama pull llama3.2:3b
```

Deux gigaoctets à télécharger, une seule fois : le volume `ollama-data` les conserve.

### Arrêter

```bash
docker compose -f helpdesk-ai/docker/docker-compose.yml down
```

Ajoutez `-v` pour supprimer aussi les données de la base et le modèle téléchargé.

---

## Étape 4 — Vérifier que tout est en place

```bash
curl http://localhost:8000/api/v1/health
```

La réponse doit indiquer `model_loaded: true`. Ouvrez ensuite http://localhost:8081,
créez un compte, déposez un ticket : une catégorie et un indice de confiance
s'affichent dans la console d'administration.

Au démarrage, le journal de l'API affiche une ligne qui mérite d'être comprise :

```
[predictor] models/best_pipeline.pkl absent, repli sur le registre, version 1.
```

C'est normal sur un clone. `best_pipeline.pkl` est une copie de travail, exclue du
dépôt ; le service charge alors la version promue du registre de modèles, qui est
versionnée, elle. Le résultat est identique.

```
RAG sémantique non disponible (knowledge_base.parquet) — repli lexical actif
```

Normal également tant que le fichier de base de connaissances ne vous a pas été remis.
La recherche de cas comparables fonctionne, en mode lexical, moins précis que le mode
sémantique.

---

## Voie manuelle, sans Docker

Utile pour développer, avec rechargement à chaud.

### L'API

```bash
cd helpdesk-ai
python -m venv venv
```

Activez l'environnement, `venv\Scripts\activate` sous Windows ou
`source venv/bin/activate` sous Linux et macOS, puis :

```bash
pip install -r requirements.txt
```

Les versions sont épinglées : vous obtiendrez exactement celles contre lesquelles le
projet a été validé. Ne les relâchez pas sans raison, le modèle servi est sérialisé
avec une version précise de scikit-learn.

PostgreSQL doit tourner et `DB_URL` pointer dessus dans votre `.env`. Puis :

```bash
uvicorn api.main:app --reload --port 8000
```

### Le frontend

```bash
cd helpdesk-ai/frontend
npm ci
npm start
```

L'interface répond sur http://localhost:4200 et attaque l'API sur le port 8000.
Utilisez `npm ci` et non `npm install` : la première respecte `package-lock.json`,
la seconde peut en changer.

---

## Lancer les tests

```bash
cd helpdesk-ai
pytest tests/ --ignore=tests/test_api_integration.py -v
```

C'est la commande exacte de l'intégration continue. **198 tests passent** sur un clone
sans les fichiers de données. `test_api_integration.py` est écarté parce qu'il exige
le pipeline complet, absent du dépôt.

Couverture :

```bash
pytest tests/ --ignore=tests/test_api_integration.py --cov=api --cov=src
```

Qualité du code, avec la version utilisée par l'intégration continue :

```bash
ruff check src/ api/ tests/ scripts/ --ignore E501,E402
```

---

## Si quelque chose ne marche pas

**Les conteneurs démarrent puis s'arrêtent.** Regardez `docker compose logs api`.
La cause la plus fréquente est un `.env` absent ou une variable PostgreSQL vide :
la composition refuse de démarrer sans `POSTGRES_USER`, `POSTGRES_PASSWORD` et
`POSTGRES_DB`.

**Le port 8000 ou 8081 est déjà pris.** Un autre service l'occupe. Changez la partie
gauche dans `docker-compose.yml`, par exemple `"8090:8000"`.

**L'assistant ne répond rien.** Le modèle Ollama n'a pas été téléchargé, revenez à
l'étape 3 bis. Vérifiez avec :

```bash
docker compose -f helpdesk-ai/docker/docker-compose.yml exec ollama ollama list
```

**Les suggestions de résolution semblent pauvres.** Attendu tant que
`knowledge_base.parquet` n'est pas en place. Le moteur sémantique est alors inactif.

**`pip install` échoue sous Python 3.12 ou 3.13.** Les versions épinglées visent la
**3.11**, celle des images Docker. Créez l'environnement virtuel avec une 3.11.

**Un avertissement `InconsistentVersionWarning` de scikit-learn apparaît.** Le modèle
du registre a été sérialisé avec scikit-learn 1.6.1 et l'environnement en installe une
version plus récente. Le modèle se charge et répond, mais ce point reste à arbitrer par
l'auteur du projet avant une mise en service réelle.

---

## Organisation du dépôt

```
helpdesk-ai/
  api/              service FastAPI : routes, services, accès aux données
  src/              chaîne de traitement, modèles, RAG, registre, supervision
  frontend/         application Angular, portail et console d'administration
  models/registry/  versions de modèles promues, avec leur lignée et leurs métriques
  metrics/          relevés d'évaluation, au format JSON
  scripts/          mesures, campagnes comparatives, vérifications
  tests/            suite de tests
  docker/           composition et images
report/             sources LaTeX du mémoire, figures, diagrammes
```

À lire ensuite : `README.md` à la racine pour le contexte et les résultats mesurés,
`helpdesk-ai/MLOPS.md` pour le registre de modèles et la promotion,
`helpdesk-ai/TESTING.md` pour la stratégie de test.

---

## Contact

Pour les fichiers de données, un accès, ou une question sur une mesure du mémoire :
**Mohamed Amine Toukabri**, auteur du projet.
