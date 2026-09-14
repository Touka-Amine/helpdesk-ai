# api/services/mail_service.py
"""Envoi de courriels sortants.

Un seul usage pour l'instant : le lien de reinitialisation de mot de passe.

Le service ne leve jamais d'exception vers l'appelant. Une panne de la messagerie
ne doit ni faire echouer la requete HTTP, ni reveler au demandeur si l'adresse
saisie correspond a un compte : l'API repond la meme chose dans tous les cas.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from api.config import settings

logger = logging.getLogger(__name__)

EXPEDITEUR_AFFICHE = "Helpdesk AI — OneTech Business Solutions"


def _corps_texte(prenom: str, lien: str, minutes: int) -> str:
    return (
        f"Bonjour {prenom},\n\n"
        "Vous avez demande la reinitialisation de votre mot de passe Helpdesk AI.\n\n"
        "Ouvrez le lien ci-dessous pour en choisir un nouveau :\n\n"
        f"{lien}\n\n"
        f"Ce lien expire dans {minutes} minutes et ne fonctionne qu'une fois.\n\n"
        "Si vous n'etes pas a l'origine de cette demande, ignorez ce message : "
        "votre mot de passe actuel reste valable.\n\n"
        "Helpdesk AI — support informatique, OneTech Business Solutions\n"
    )


def _corps_html(prenom: str, lien: str, minutes: int) -> str:
    # Mise en forme volontairement sobre : styles en ligne et tableau, seule
    # facon d'obtenir un rendu previsible dans Outlook, client de l'entreprise.
    return f"""\
<html>
  <body style="margin:0;padding:24px;background:#f6f7f8;
               font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#12151a;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
           style="max-width:520px;margin:0 auto;background:#ffffff;
                  border:1px solid #dcdfe4;border-radius:8px;">
      <tr>
        <td style="padding:28px 32px;">
          <p style="margin:0 0 20px;font-size:15px;">Bonjour {prenom},</p>
          <p style="margin:0 0 20px;font-size:15px;line-height:22px;">
            Vous avez demand&eacute; la r&eacute;initialisation de votre mot de passe
            Helpdesk&nbsp;AI.
          </p>
          <p style="margin:0 0 28px;">
            <a href="{lien}"
               style="display:inline-block;background:#4f46e5;color:#ffffff;
                      text-decoration:none;font-size:15px;font-weight:600;
                      padding:12px 22px;border-radius:6px;">
              Choisir un nouveau mot de passe
            </a>
          </p>
          <p style="margin:0 0 20px;font-size:13px;color:#5a6472;line-height:20px;">
            Ce lien expire dans {minutes}&nbsp;minutes et ne fonctionne qu'une fois.
            S'il a expir&eacute;, refaites une demande depuis la page de connexion.
          </p>
          <p style="margin:0;font-size:13px;color:#5a6472;line-height:20px;">
            Si vous n'&ecirc;tes pas &agrave; l'origine de cette demande, ignorez ce
            message&nbsp;: votre mot de passe actuel reste valable.
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:16px 32px;border-top:1px solid #dcdfe4;
                   font-size:12px;color:#5a6472;">
          Helpdesk AI &mdash; support informatique, OneTech Business Solutions
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def envoyer_lien_reinitialisation(destinataire: str, lien: str, prenom: str = "") -> bool:
    """Envoie le lien de reinitialisation. Renvoie True si le courriel est parti.

    Aucune valeur de secret n'apparait dans les journaux, y compris en cas
    d'echec d'authentification SMTP.
    """
    minutes = settings.RESET_TOKEN_TTL_MIN
    prenom = prenom.strip() or "bonjour"

    if not settings.messagerie_configuree():
        logger.warning(
            "Messagerie non configuree (SMTP_HOST vide) : aucun courriel envoye."
        )
        # Hors production uniquement, le lien passe dans le journal pour permettre
        # de derouler le parcours sans serveur SMTP. En production ce serait
        # deposer un jeton de reinitialisation en clair dans les logs.
        if settings.ENVIRONMENT.strip().lower() != "production":
            logger.warning("Lien de reinitialisation (mode developpement) : %s", lien)
        return False

    message = EmailMessage()
    message["Subject"] = "Reinitialisation de votre mot de passe Helpdesk AI"
    message["From"] = formataddr((EXPEDITEUR_AFFICHE, settings.SMTP_FROM))
    message["To"] = destinataire
    message.set_content(_corps_texte(prenom, lien, minutes))
    message.add_alternative(_corps_html(prenom, lien, minutes), subtype="html")

    try:
        if settings.SMTP_PORT == 465:
            # Port 465 : la session est chiffree des l'ouverture, pas de STARTTLS.
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT
            ) as serveur:
                _authentifier(serveur)
                serveur.send_message(message)
        else:
            with smtplib.SMTP(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT
            ) as serveur:
                if settings.SMTP_STARTTLS:
                    serveur.starttls()
                _authentifier(serveur)
                serveur.send_message(message)
    except (smtplib.SMTPException, OSError) as erreur:
        # str(erreur) porte le code et le message du serveur, jamais le mot de passe.
        logger.error("Envoi du courriel de reinitialisation impossible : %s", erreur)
        return False

    logger.info("Courriel de reinitialisation envoye.")
    return True


def _authentifier(serveur: smtplib.SMTP) -> None:
    if settings.SMTP_USER:
        serveur.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
