# api/predictor.py

import joblib
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from data.preprocess import build_text_for_model, build_text_for_rag
from rag.engine import RAGEngine
from rag.semantic_engine import SemanticRAGEngine
from rag.hybrid_engine import HybridRAGEngine

MODEL_PATH   = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_pipeline.pkl')
RAG_PATH     = os.path.join(os.path.dirname(__file__), '..', 'models', 'rag_engine.pkl')
META_PATH    = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_metadata.json')
SEM_RAG_DIR  = os.path.join(os.path.dirname(__file__), '..', 'models', 'semantic_rag')
# Pointeur ecrit par src/registry/model_registry.py a chaque promotion ou rollback.
POINTER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'registry', 'PRODUCTION')

# Intervalle minimal entre deux verifications du pointeur, en secondes. Le controle
# est un simple open() sur un fichier de quelques octets, mais le faire a chaque
# prediction serait du gaspillage sans benefice : une promotion prise en compte en
# moins de trente secondes est largement suffisante.
FRESHNESS_CHECK_INTERVAL = 30.0

PARAMS_PATH = os.path.join(os.path.dirname(__file__), '..', 'params.yaml')

# Valeurs de repli si params.yaml est absent de l'image : elles doivent rester
# identiques a celles du fichier, sans quoi le service mesure une configuration
# et en sert une autre.
RAG_DEFAUTS = {"top_k": 3, "similarity_threshold": 0.35, "hybrid_alpha": 0.5}


def _params_rag() -> dict:
    """
    Parametres du RAG lus depuis params.yaml.

    Ils y sont lus plutot que codes en dur pour que le moteur servi et le moteur
    evalue par src/pipeline/rag_eval.py partagent une seule source. Le seuil avait
    ete recopie a la main dans ce fichier, et rien ne garantissait qu'il suive une
    recalibration du pipeline.
    """
    try:
        import yaml
        with open(PARAMS_PATH, encoding="utf-8") as f:
            rag = (yaml.safe_load(f) or {}).get("rag") or {}
        return {cle: rag.get(cle, defaut) for cle, defaut in RAG_DEFAUTS.items()}
    except Exception:
        return dict(RAG_DEFAUTS)


class Predictor:
    """
    Singleton — chargé une seule fois au démarrage de l'API.
    Moteur de prédiction : pipeline ML (TF-IDF + classificateur sklearn).
    Moteur RAG : SemanticRAGEngine (FAISS + paraphrase-multilingual-mpnet-base-v2)
                 avec fallback sur RAGEngine lexical (TF-IDF) si FAISS indisponible.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
            cls._instance._semantic_rag_loaded = False
            cls._instance.model_version = None
            cls._instance._last_freshness_check = 0.0
            # Les endpoints synchrones de FastAPI s'executent dans un pool de threads :
            # plusieurs requetes peuvent traverser ensemble ensure_fresh() et declencher
            # deux rechargements concurrents, ou lire un pipeline deja remplace alors que
            # le seuil ne l'est pas encore. Verrou reentrant parce que reload() appelle
            # load(), qui prend le meme verrou.
            cls._instance._lock = threading.RLock()
        return cls._instance

    # ── Version en service et fraicheur ──────────────────────────────────────

    @staticmethod
    def _read_pointer():
        """Version designee par le registre comme etant en production, ou None."""
        try:
            with open(POINTER_PATH, encoding='utf-8') as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return None

    def ensure_fresh(self):
        """
        Recharge le modele si le registre pointe vers une autre version.

        L'API tourne avec plusieurs workers uvicorn (processus separes). Un
        rechargement declenche par l'endpoint /admin/model/reload n'atteint que le
        worker qui a traite la requete ; les autres continueraient de servir
        l'ancien modele jusqu'au prochain redemarrage. Chaque worker compare donc
        lui-meme le pointeur du registre a la version qu'il a en memoire.
        """
        # Controle hors verrou : le cas courant est « rien a faire », il ne doit pas
        # serialiser les requetes.
        if time.time() - self._last_freshness_check < FRESHNESS_CHECK_INTERVAL:
            return False

        with self._lock:
            # Re-controle sous verrou : plusieurs threads ont pu franchir le test
            # ci-dessus avant que le premier n'ait mis a jour l'horodatage.
            if time.time() - self._last_freshness_check < FRESHNESS_CHECK_INTERVAL:
                return False
            self._last_freshness_check = time.time()

            version = self._read_pointer()
            if version is None or version == self.model_version:
                return False

            print(f"Nouvelle version en production detectee : v{version} "
                  f"(worker sur v{self.model_version}) — rechargement")
            self.reload()
            return True

    def reload(self):
        """Recharge les artefacts depuis le disque. Idempotent."""
        with self._lock:
            self._loaded = False
            self._semantic_rag_loaded = False
            self.load()
            return self.model_version

    def info(self) -> dict:
        """Etat du modele servi — expose par GET /api/v1/admin/model-info."""
        return {
            'loaded'        : self._loaded,
            'model_version' : self.model_version,
            'registry_points_to': self._read_pointer(),
            'model_name'    : getattr(self, 'metadata', {}).get('model_name'),
            'threshold'     : getattr(self, 'threshold', None),
            'classes'       : getattr(self, 'classes', []),
            'dataset_version': getattr(self, 'metadata', {}).get('dataset_version'),
            'trained_at'    : getattr(self, 'metadata', {}).get('trained_at'),
            'semantic_rag'  : self._semantic_rag_loaded,
        }

    def load(self):
        # Sous verrou de bout en bout : le chargement remplace pipeline, seuil, classes
        # et version en plusieurs affectations. Sans cela, une requete concurrente peut
        # lire un pipeline deja remplace alors que le seuil ne l'est pas encore, et
        # appliquer un seuil de decision qui ne correspond pas au modele interroge.
        with self._lock:
            if self._loaded:
                return
            self._load_unlocked()

    def _load_unlocked(self):
        print("Chargement des modèles ML et RAG...")

        # Pickle compat: notebooks sauvegardés avec __main__.RAGEngine
        import __main__
        __main__.RAGEngine = RAGEngine

        self.pipeline = joblib.load(MODEL_PATH)
        self.rag = joblib.load(RAG_PATH)

        with open(META_PATH, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        # Seuil relevé 0.40→0.60 (Semaine 1 amélioration) : ~70% routage auto à ~85% précision
        self.threshold = self.metadata.get('confidence_threshold', 0.60)
        self.classes   = self.metadata.get('classes', [])
        self.model_version = self._read_pointer()
        self._last_freshness_check = time.time()

        # ── RAG hybride (sémantique FAISS + lexical TF-IDF) — prioritaire ───────
        # Ordre de préférence : Hybride > Sémantique seul > Lexical seul
        try:
            self.semantic_rag = SemanticRAGEngine.load(SEM_RAG_DIR)
            # Construire le moteur hybride en réutilisant semantic_rag déjà chargé.
            # Les réglages viennent de params.yaml, pas d'une copie locale.
            prag = _params_rag()
            self.hybrid_rag = HybridRAGEngine(
                alpha=prag["hybrid_alpha"],
                top_k=prag["top_k"],
                similarity_threshold=prag["similarity_threshold"],
            )
            self.hybrid_rag._sem = self.semantic_rag
            self.hybrid_rag._lex = self.rag
            self.hybrid_rag._fitted = True
            self._semantic_rag_loaded = True
            n_docs = len(self.semantic_rag.knowledge_base)
            a = prag["hybrid_alpha"]
            print(f"RAG hybride actif — {n_docs} tickets | alpha={a} "
                  f"(sem×{a} + lex×{round(1 - a, 2)}) | seuil={prag['similarity_threshold']}")
        except Exception as e:
            print(f"RAG sémantique non disponible ({e}) — fallback lexical actif")
            self.semantic_rag = None
            self.hybrid_rag = None
            self._semantic_rag_loaded = False

        self._loaded = True
        version = f"v{self.model_version}" if self.model_version is not None else "hors registre"
        print(f"Pipeline ML charge — {len(self.rag.knowledge_base)} tickets, "
              f"seuil={self.threshold}, modele {version}")

    def predict(self, titre: str, description: str) -> dict:
        """
        Prédit la catégorie via le pipeline ML (TF-IDF + classificateur).

        Le texte est construit par `build_text_for_model`, c'est-à-dire titre puis
        description, exactement comme la colonne `text_clean` du corpus sur laquelle
        le modèle a été entraîné. N'envoyer que la description le privait du champ
        le plus discriminant : sur le jeu de test gelé, l'exactitude tombait de
        44,7 % à 31,7 % et la confiance moyenne de 0,46 à 0,41.
        """
        text_clean = build_text_for_model(titre, description)
        proba      = self.pipeline.predict_proba([text_clean])[0]
        pred_idx   = proba.argmax()
        categorie  = self.pipeline.classes_[pred_idx]
        confiance  = float(proba[pred_idx])
        return {
            'categorie'     : categorie,
            'confiance'     : round(confiance, 4),
            'auto_routed'   : confiance >= self.threshold,
            'low_confidence': confiance < self.threshold,
        }

    def recommend(
        self,
        titre: str,
        description: str,
        categorie: str | None,
        allow_fallback: bool = True,
    ) -> list:
        """
        Recommandations RAG — moteur sémantique (FAISS) en priorité,
        fallback lexical (TF-IDF) si FAISS indisponible.
        """
        text_rag = build_text_for_rag(description, titre=titre)

        # Priorité : Hybride > Sémantique > Lexical
        if self._semantic_rag_loaded and self.hybrid_rag is not None:
            return self.hybrid_rag.recommend(
                query_text=text_rag,
                category_filter=categorie,
                allow_fallback=allow_fallback,
            )

        if self._semantic_rag_loaded and self.semantic_rag is not None:
            return self.semantic_rag.recommend(
                query_text=text_rag,
                category_filter=categorie,
                allow_fallback=allow_fallback,
            )

        return self.rag.recommend(
            query_text=text_rag,
            category_filter=categorie,
            allow_fallback=allow_fallback,
        )


predictor = Predictor()
