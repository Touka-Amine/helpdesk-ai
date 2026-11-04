"""Gestion des comptes par un administrateur : profil, et mots de passe hors de portee.

Ce que ces tests etablissent :
  * un administrateur modifie le nom, le prenom et la filiale d'un compte, pas son adresse ;
  * un nom vide est refuse au lieu d'effacer le nom existant ;
  * un administrateur ne peut pas changer le mot de passe d'un autre compte : la
    route n'existe pas, et le mot de passe du compte vise continue de fonctionner ;
  * un client n'a pas acces a la modification des comptes ;
  * la liste des comptes reste lisible meme si une adresse en base ne passerait
    plus la validation d'entree (cas reel : des comptes de test en .local).
"""

import os

import pytest

os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_admin_comptes_test.db")
os.environ.setdefault("INGEST_API_KEY", "test-api-key-admin-comptes")

try:
    from passlib.context import CryptContext as _CC
    _CC(schemes=["bcrypt"], deprecated="auto").hash("test")
    BCRYPT_OK = True
except Exception:
    BCRYPT_OK = False

pytestmark = pytest.mark.skipif(
    not BCRYPT_OK, reason="bcrypt incompatible avec passlib dans cet environnement"
)

from fastapi.testclient import TestClient  # noqa: E402

from api.db.database import SessionLocal  # noqa: E402
from api.db.models import User  # noqa: E402
from api.main import app  # noqa: E402
from api.services.auth_service import hash_password  # noqa: E402

ADMIN = "admin.comptes@exemple.com"
CLIENT = "client.comptes@exemple.com"
MDP = "MotDePasseTest1!"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _sans_plafond():
    """Vide le compteur de tentatives de connexion : tous les tests partagent
    l'adresse du client de test, et le plafond n'est pas ce qu'on verifie ici."""
    from api.middleware import auth_middleware

    auth_middleware._login_attempts.clear()
    yield
    auth_middleware._login_attempts.clear()


def _compte(email: str, role: str, **champs) -> int:
    """Cree ou remet a neuf un compte directement en base, et renvoie son id."""
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if u is None:
            u = User(email=email, nom="Nom", prenom="Prenom", hashed_password="", role=role)
            db.add(u)
        u.role = role
        u.nom, u.prenom, u.filiale = "Nom", "Prenom", ""
        u.hashed_password = hash_password(MDP)
        u.is_active, u.first_login = True, False
        for cle, valeur in champs.items():
            setattr(u, cle, valeur)
        db.commit()
        return u.id
    finally:
        db.close()


def _jeton(client, email: str, mdp: str = MDP) -> str:
    r = client.post("/api/v1/auth/login", data={"username": email, "password": mdp})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _entetes(jeton: str) -> dict:
    return {"Authorization": f"Bearer {jeton}"}


@pytest.fixture
def admin(client):
    _compte(ADMIN, "admin")
    return _entetes(_jeton(client, ADMIN))


@pytest.fixture
def id_client():
    return _compte(CLIENT, "client")


# ── Profil ─────────────────────────────────────────────────────────────────

def test_l_admin_modifie_le_profil(client, admin, id_client):
    r = client.patch(f"/api/v1/admin/users/{id_client}", headers=admin,
                     json={"nom": "  Nouveau  ", "prenom": "Autre", "filiale": "Filiale A"})
    assert r.status_code == 200, r.text
    corps = r.json()
    assert (corps["nom"], corps["prenom"], corps["filiale"]) == ("Nouveau", "Autre", "Filiale A")
    assert corps["email"] == CLIENT


def test_un_nom_vide_est_refuse(client, admin, id_client):
    r = client.patch(f"/api/v1/admin/users/{id_client}", headers=admin, json={"nom": "   "})
    assert r.status_code == 422
    db = SessionLocal()
    try:
        assert db.query(User).get(id_client).nom == "Nom"
    finally:
        db.close()


def test_l_adresse_n_est_pas_modifiable(client, admin, id_client):
    r = client.patch(f"/api/v1/admin/users/{id_client}", headers=admin,
                     json={"email": "detournement@exemple.com"})
    assert r.status_code == 200
    assert r.json()["email"] == CLIENT


# ── Mots de passe ──────────────────────────────────────────────────────────

def test_l_admin_ne_change_pas_le_mot_de_passe_d_un_autre(client, admin, id_client):
    """Chacun change son propre mot de passe ; aucune route ne permet a un
    administrateur de le faire pour un autre compte."""
    r = client.post(f"/api/v1/admin/users/{id_client}/reset-password", headers=admin)
    assert r.status_code in (404, 405)
    r = client.patch(f"/api/v1/admin/users/{id_client}", headers=admin,
                     json={"password": "ChoisiParLAdmin1!", "hashed_password": "x"})
    assert r.status_code == 200
    connexion = client.post("/api/v1/auth/login", data={"username": CLIENT, "password": MDP})
    assert connexion.status_code == 200


# ── Droits ─────────────────────────────────────────────────────────────────

def test_un_client_n_a_pas_acces(client, id_client):
    entetes = _entetes(_jeton(client, CLIENT))
    assert client.patch(f"/api/v1/admin/users/{id_client}", headers=entetes,
                        json={"nom": "X"}).status_code == 403


# ── Liste ──────────────────────────────────────────────────────────────────

def test_la_liste_tolere_une_adresse_reservee(client, admin):
    """Une adresse en .local ecrite directement en base faisait echouer toute la
    liste : la validation de sortie refusait la ligne, et l'ecran n'affichait
    plus personne."""
    _compte("compte.test@exemple.local", "client")
    r = client.get("/api/v1/admin/users", headers=admin)
    assert r.status_code == 200, r.text
    assert "compte.test@exemple.local" in [u["email"] for u in r.json()]
