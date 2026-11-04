"""Parcours "mot de passe oublie" — jeton a usage unique envoye par courriel.

Ce que ces tests etablissent :
  * l'endpoint de demande ne permet pas de savoir si une adresse a un compte ;
  * le jeton n'est jamais conserve en clair dans la base ;
  * il ne sert qu'une fois, il expire, et une nouvelle demande annule la precedente ;
  * le mot de passe change reellement, et l'ancien cesse de fonctionner ;
  * une messagerie absente ou en panne ne fait pas echouer la requete.

Le courriel n'est jamais reellement envoye : l'expedition est remplacee par une
capture qui releve le lien, seul moyen d'obtenir le jeton en clair cote test.
"""

import os
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_reset_test.db")
os.environ.setdefault("INGEST_API_KEY", "test-api-key-reset")

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
from api.db.models import PasswordReset, User  # noqa: E402
from api.main import app  # noqa: E402
from api.routers import auth as routeur_auth  # noqa: E402
from api.services.auth_service import empreinte_jeton  # noqa: E402

MDP_INITIAL = "MotDePasseInitial1!"
MDP_NOUVEAU = "MotDePasseNouveau2!"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _sans_plafond():
    """Vide le compteur de limitation entre deux tests.

    La limitation porte sur l'adresse IP, et tous les tests partagent celle du
    client de test : sans cette remise a zero, le sixieme appel de la suite
    echouerait pour une raison sans rapport avec ce qu'il verifie. Le plafond
    lui-meme est eprouve par test_le_plafond_de_demandes_s_applique.
    """
    from api.middleware import auth_middleware

    auth_middleware._reset_requests.clear()
    yield
    auth_middleware._reset_requests.clear()


@pytest.fixture
def liens(monkeypatch):
    """Remplace l'envoi du courriel par une capture des liens produits."""
    captures: list[str] = []

    def _capturer(destinataire, lien, prenom=""):
        captures.append(lien)
        return True

    # Le routeur a importe la fonction par son nom : c'est la reference du
    # module routeur qu'il faut remplacer, pas celle du module mail_service.
    monkeypatch.setattr(routeur_auth, "envoyer_lien_reinitialisation", _capturer)
    return captures


@pytest.fixture
def compte(client):
    """Cree un compte neuf et renvoie son adresse."""
    email = f"reset_{datetime.utcnow().timestamp():.6f}@exemple-test.com".replace(".", "_", 1)
    reponse = client.post("/api/v1/auth/register", json={
        "nom": "Test", "prenom": "Reinitialisation",
        "email": email, "password": MDP_INITIAL, "filiale": "",
    })
    if reponse.status_code != 200:
        pytest.skip(f"Creation du compte impossible : {reponse.text}")
    yield email

    session = SessionLocal()
    try:
        utilisateur = session.query(User).filter(User.email == email).first()
        if utilisateur:
            session.query(PasswordReset).filter(
                PasswordReset.user_id == utilisateur.id
            ).delete(synchronize_session=False)
            session.delete(utilisateur)
            session.commit()
    finally:
        session.close()


def _jeton_du_lien(lien: str) -> str:
    return parse_qs(urlparse(lien).query)["token"][0]


def _demander(client, email):
    return client.post("/api/v1/auth/forgot-password", json={"email": email})


# ── Non-divulgation ───────────────────────────────────────────────────────────

def test_reponse_identique_que_le_compte_existe_ou_non(client, compte, liens):
    connue = _demander(client, compte)
    inconnue = _demander(client, "personne_sans_compte@exemple-test.com")

    assert connue.status_code == inconnue.status_code == 200
    assert connue.json() == inconnue.json()
    # Un seul lien produit : celui du compte qui existe.
    assert len(liens) == 1


def test_aucun_jeton_en_clair_dans_la_base(client, compte, liens):
    _demander(client, compte)
    jeton = _jeton_du_lien(liens[0])

    session = SessionLocal()
    try:
        assert session.query(PasswordReset).filter(
            PasswordReset.token_hash == jeton
        ).first() is None
        assert session.query(PasswordReset).filter(
            PasswordReset.token_hash == empreinte_jeton(jeton)
        ).first() is not None
    finally:
        session.close()


# ── Parcours nominal ──────────────────────────────────────────────────────────

def test_le_lien_change_le_mot_de_passe(client, compte, liens):
    _demander(client, compte)
    jeton = _jeton_du_lien(liens[0])

    reponse = client.post("/api/v1/auth/reset-password", json={
        "token": jeton, "new_password": MDP_NOUVEAU,
    })
    assert reponse.status_code == 200

    ancien = client.post("/api/v1/auth/login", data={
        "username": compte, "password": MDP_INITIAL,
    })
    nouveau = client.post("/api/v1/auth/login", data={
        "username": compte, "password": MDP_NOUVEAU,
    })
    assert ancien.status_code == 401
    assert nouveau.status_code == 200


# ── Robustesse du jeton ───────────────────────────────────────────────────────

def test_le_jeton_ne_sert_qu_une_fois(client, compte, liens):
    _demander(client, compte)
    jeton = _jeton_du_lien(liens[0])
    corps = {"token": jeton, "new_password": MDP_NOUVEAU}

    assert client.post("/api/v1/auth/reset-password", json=corps).status_code == 200
    assert client.post("/api/v1/auth/reset-password", json=corps).status_code == 400


def test_une_nouvelle_demande_annule_la_precedente(client, compte, liens):
    _demander(client, compte)
    _demander(client, compte)
    premier, second = (_jeton_du_lien(lien) for lien in liens[:2])

    perime = client.post("/api/v1/auth/reset-password", json={
        "token": premier, "new_password": MDP_NOUVEAU,
    })
    valide = client.post("/api/v1/auth/reset-password", json={
        "token": second, "new_password": MDP_NOUVEAU,
    })
    assert perime.status_code == 400
    assert valide.status_code == 200


def test_un_jeton_expire_est_refuse(client, compte, liens):
    _demander(client, compte)
    jeton = _jeton_du_lien(liens[0])

    session = SessionLocal()
    try:
        demande = session.query(PasswordReset).filter(
            PasswordReset.token_hash == empreinte_jeton(jeton)
        ).first()
        demande.expires_at = datetime.utcnow() - timedelta(minutes=1)
        session.commit()
    finally:
        session.close()

    reponse = client.post("/api/v1/auth/reset-password", json={
        "token": jeton, "new_password": MDP_NOUVEAU,
    })
    assert reponse.status_code == 400


def test_un_jeton_inconnu_est_refuse(client):
    reponse = client.post("/api/v1/auth/reset-password", json={
        "token": "jeton-qui-n-a-jamais-existe-mais-assez-long",
        "new_password": MDP_NOUVEAU,
    })
    assert reponse.status_code == 400


# ── Plafond de demandes ───────────────────────────────────────────────────────

def test_le_plafond_de_demandes_s_applique(client, liens):
    """Chaque demande declenche un courriel vers une adresse choisie par l'appelant :
    sans plafond, l'endpoint sert a inonder la boite d'un collaborateur."""
    from api.middleware import auth_middleware

    codes = [
        _demander(client, "inconnu@exemple-test.com").status_code for _ in range(6)
    ]
    assert codes[: auth_middleware._RESET_MAX] == [200] * auth_middleware._RESET_MAX
    assert codes[-1] == 429


# ── Messagerie indisponible ───────────────────────────────────────────────────

def test_une_messagerie_absente_ne_fait_pas_echouer_la_demande(client, compte, monkeypatch):
    """Sans serveur SMTP, la requete reste un succes et ne leve rien."""
    from api.services import mail_service

    monkeypatch.setattr(mail_service.settings, "SMTP_HOST", "")
    monkeypatch.setattr(mail_service.settings, "ENVIRONMENT", "development")

    assert mail_service.envoyer_lien_reinitialisation(compte, "http://x/y", "Test") is False
    assert _demander(client, compte).status_code == 200


def test_une_panne_smtp_ne_leve_pas(monkeypatch):
    """Un serveur SMTP injoignable se solde par False, jamais par une exception."""
    from api.services import mail_service

    monkeypatch.setattr(mail_service.settings, "SMTP_HOST", "smtp.invalide.local")
    monkeypatch.setattr(mail_service.settings, "SMTP_PORT", 587)
    monkeypatch.setattr(mail_service.settings, "SMTP_TIMEOUT", 0.3)

    assert mail_service.envoyer_lien_reinitialisation("a@b.c", "http://x/y", "Test") is False
