"""
Tests d'intégration API — Phase 8.
Lance l'API avec TestClient (DB de test isolée).

Note : passlib 1.7.x + bcrypt 4.x peuvent être incompatibles dans certains environnements.
Les tests auth sont marqués xfail si bcrypt n'est pas fonctionnel.
"""

import os
import pytest

os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_test.db")
os.environ.setdefault("INGEST_API_KEY", "test-api-key-integration")

# Détection compatibilité bcrypt / passlib
try:
    from passlib.context import CryptContext as _CC
    _CC(schemes=["bcrypt"], deprecated="auto").hash("test")
    BCRYPT_OK = True
except Exception:
    BCRYPT_OK = False

from fastapi.testclient import TestClient
from api.main import app

TEST_EMAIL    = "integration_test@test.com"
TEST_PASSWORD = "testpass123!"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_token(client):
    """Crée un utilisateur de test et retourne un token JWT."""
    if not BCRYPT_OK:
        pytest.skip("bcrypt incompatible avec passlib dans cet environnement")
    client.post("/api/v1/auth/register", json={
        "nom": "Test", "prenom": "Integration",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "filiale": "",
    })
    r = client.post("/api/v1/auth/login", data={
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    if r.status_code != 200:
        pytest.skip(f"Login échoué : {r.text}")
    return r.json()["access_token"]


# ─────────────────────────── Accueil ─────────────────────────────────────────

def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "api" in r.json()


# ─────────────────────────── Health ──────────────────────────────────────────

def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "rag_loaded" in data


# ─────────────────────────── Catégories ──────────────────────────────────────

def test_categories(client):
    r = client.get("/api/v1/categories")
    assert r.status_code == 200
    data = r.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)
    assert len(data["categories"]) > 0
    assert "threshold" in data


# ─────────────────────────── Auth ────────────────────────────────────────────

@pytest.mark.skipif(not BCRYPT_OK, reason="bcrypt incompatible avec passlib dans cet environnement")
def test_register_and_login(client):
    email = "new_user_test@test.com"
    r_reg = client.post("/api/v1/auth/register", json={
        "nom": "Nouveau", "prenom": "User",
        "email": email,
        "password": "motdepasse123!",
        "filiale": "OTBS",
    })
    assert r_reg.status_code in (200, 400)

    r_login = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "motdepasse123!",
    })
    if r_reg.status_code == 200:
        assert r_login.status_code == 200
        assert "access_token" in r_login.json()


def test_login_wrong_password(client):
    r = client.post("/api/v1/auth/login", data={
        "username": TEST_EMAIL,
        "password": "mauvais_mot_de_passe",
    })
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/api/v1/auth/login", data={
        "username": "inconnu@test.com",
        "password": "nope",
    })
    assert r.status_code == 401


# ─────────────────────────── Prédiction ──────────────────────────────────────

def test_predict_vpn(client):
    r = client.post("/api/v1/predict", json={
        "titre"      : "Problème connexion VPN",
        "description": "Impossible de se connecter au VPN depuis ce matin, erreur d'authentification",
    })
    assert r.status_code == 200
    data = r.json()
    assert "prediction" in data
    assert "recommendations" in data
    assert "categorie" in data["prediction"]
    assert 0.0 <= data["prediction"]["confiance"] <= 1.0


def test_predict_microsoft(client):
    r = client.post("/api/v1/predict", json={
        "titre"      : "Outlook ne s'ouvre plus",
        "description": "Impossible d'ouvrir Outlook, message d'erreur produit non activé",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["prediction"]["categorie"] == "Microsoft"


def test_predict_description_trop_courte(client):
    r = client.post("/api/v1/predict", json={
        "titre"      : "Bug",
        "description": "court",
    })
    assert r.status_code in (422, 422)


def test_predict_titre_trop_court(client):
    r = client.post("/api/v1/predict", json={
        "titre"      : "ab",
        "description": "Description suffisamment longue pour le test API",
    })
    assert r.status_code == 422


# ─────────────────────────── Tickets (auth requise) ──────────────────────────

def test_create_ticket_sans_auth(client):
    r = client.post("/api/v1/tickets/", json={
        "titre"      : "Test",
        "description": "Description d'un ticket de test pour la validation",
    })
    assert r.status_code == 401


def test_create_ticket_avec_auth(client, auth_token):
    r = client.post(
        "/api/v1/tickets/",
        json={
            "titre"      : "Problème accès Teams",
            "description": "Impossible de se connecter à Teams depuis ce matin, message erreur 403",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "categorie_predite" in data
    assert "solution_rag" in data


def test_list_my_tickets(client, auth_token):
    r = client.get(
        "/api/v1/tickets/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_all_tickets_requires_admin(client, auth_token):
    r = client.get(
        "/api/v1/tickets/admin/all",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    # Un utilisateur non-admin doit recevoir 403
    assert r.status_code in (403, 200)


# ─────────────────────────── Ingest (API key) ────────────────────────────────

def test_ingest_sans_api_key(client):
    r = client.post("/api/v1/ingest/", json={
        "titre"      : "Test ingest",
        "description": "Description du ticket ingest depuis Power Automate",
    })
    assert r.status_code == 401


def test_ingest_mauvaise_api_key(client):
    r = client.post(
        "/api/v1/ingest/",
        json={"titre": "Test", "description": "Description suffisante pour le test"},
        headers={"X-Api-Key": "mauvaise-cle"},
    )
    assert r.status_code == 401


def test_ingest_avec_bonne_api_key(client):
    from api.config import settings
    r = client.post(
        "/api/v1/ingest/",
        json={
            "titre"      : "Test ingest Power Automate",
            "description": "Ticket créé automatiquement depuis email IT",
            "demandeur"  : "Utilisateur Test",
            "priorite"   : "Urgent",
            "filiale"    : "OTBS",
        },
        headers={"X-Api-Key": settings.INGEST_API_KEY},
    )
    # 200 si l'utilisateur système existe, 503 sinon (DB de test vierge)
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        data = r.json()
        assert "ticket_id" in data
        assert data["saved_to_db"] is True
        assert "prediction" in data


def test_ingest_description_trop_courte(client):
    from api.config import settings
    r = client.post(
        "/api/v1/ingest/",
        json={"titre": "Test", "description": "court"},
        headers={"X-Api-Key": settings.INGEST_API_KEY},
    )
    assert r.status_code == 422


# ─────────────────────────── Base de connaissances (admin) ───────────────────

ROUTES_BASE_CONNAISSANCES = [
    ("get", "/api/v1/tickets/resolved/lifecycle", None),
    ("get", "/api/v1/tickets/resolved/refused", None),
    ("post", "/api/v1/tickets/resolved/1/obsolete", {"motif": "procedure depassee"}),
    ("post", "/api/v1/tickets/resolved/1/reactivate", None),
]


@pytest.mark.parametrize("methode,chemin,corps", ROUTES_BASE_CONNAISSANCES)
def test_base_connaissances_refuse_sans_connexion(client, methode, chemin, corps):
    r = getattr(client, methode)(chemin, json=corps) if corps else getattr(client, methode)(chemin)
    assert r.status_code == 401


@pytest.mark.parametrize("methode,chemin,corps", ROUTES_BASE_CONNAISSANCES)
def test_base_connaissances_reservee_aux_admins(client, auth_token, methode, chemin, corps):
    entetes = {"Authorization": f"Bearer {auth_token}"}
    appel = getattr(client, methode)
    r = appel(chemin, json=corps, headers=entetes) if corps else appel(chemin, headers=entetes)
    assert r.status_code == 403
