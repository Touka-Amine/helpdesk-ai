/** Alias pour la catégorie de ticket (chaîne libre côté backend) */
export type TicketCategory = string;

/** Statuts valides — alignés sur VALID_STATUSES dans api/routers/tickets.py */
export type Statut =
  | 'En attente'
  | 'Prise en Charge'
  | 'Résolu'
  | 'Rejeté'
  | 'Problème';

/** Listes de choix pour les champs finaux corrigibles par l'admin (écran de clôture) */
export const PRIORITE_OPTIONS = ['Faible', 'Modéré', 'Urgent', 'Critique'];
export const CLASSIFICATION_OPTIONS = ['Demande', 'Incident', 'Problème', 'Changement'];
export const CATEGORIE_OPTIONS = [
  'Applicatifs', 'Backup', 'Communication', 'Infrastructure',
  'Microsoft', 'Réseau', 'Système', 'Sécurité',
];

/** Correspond à ticket_to_dict() dans api/services/ticket_service.py */
export interface Ticket {
  id: number;
  cid: string;
  demandeur_nom: string;
  demandeur_email: string;
  titre: string;
  description: string;
  priorite_saisie: string;
  priorite_predite: string;
  priorite_finale: string | null;
  filiale: string;
  equipement: string;
  statut: Statut;
  categorie_predite: string;
  categorie_finale: string;
  confiance: number | null;
  solution_rag: string;
  knowledge_rag: string;
  rag_score: number | null;
  created_at: string;
  date_resolution: string | null;
  temps_ecoule: string | null;
  commentaire_client: string;
  commentaire_interne: string;
  classification: string;
  classification_predite: string;
  classification_finale: string | null;
  assigne_a: string | null;
  feedback_vote: 'up' | 'down' | null;
  feedback_comment: string;
}

export interface CreateTicketRequest {
  titre: string;
  description: string;
  priorite?: string;
  filiale?: string;
  equipement?: string;
}

/** Correspond à ApproveRequest dans api/schemas/ticket_schemas.py */
export interface ApproveTicketRequest {
  statut: Statut;
  categorie_finale?: string;
  priorite_finale?: string;
  classification_finale?: string;
  assigne_a?: string;
  commentaire?: string;
  commentaire_client?: string;
  commentaire_interne?: string;
}

/** Correspond à la réponse de GET /tickets/{id}/history */
export interface TicketHistoryEntry {
  id: number;
  champ: string;
  ancienne_valeur: string | null;
  nouvelle_valeur: string | null;
  timestamp: string;
  par: string;
}

export interface AdminCreateTicketRequest {
  titre: string;
  description: string;
  priorite?: string;
  filiale?: string;
  equipement?: string;
  demandeur_user_id?: number;
  demandeur_nom?: string;
  demandeur_prenom?: string;
  demandeur_email?: string;
}

/** Correspond à RagSynthesisOut dans api/schemas/ticket_schemas.py */
export interface RagSynthesis {
  text: string;
  source: 'ollama' | 'fallback' | 'none';
}

/** Correspond à ChatMessage dans api/schemas/ticket_schemas.py */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

/** Correspond à ChatResponseOut dans api/schemas/ticket_schemas.py */
export interface ChatResponse {
  reply: string;
  source: 'ollama' | 'fallback' | 'none';
}

/** Une pastille : la couleur du texte, celle du fond, et l'icone qui l'accompagne.
 *  Les couleurs sont des variables du theme (styles.css), donc redefinies en mode
 *  sombre sans que le composant ait a s'en soucier. */
export interface Pastille { label?: string; color: string; bg: string; icon: string }

export const STATUT_CFG: Record<Statut, { label: string; color: string; bg: string; icon: string }> = {
  'En attente':      { label: 'En attente',      color: 'var(--statut-attente)',  bg: 'var(--statut-attente-bg)',  icon: 'hourglass_top' },
  'Prise en Charge': { label: 'Prise en Charge', color: 'var(--statut-charge)',   bg: 'var(--statut-charge-bg)',   icon: 'engineering' },
  'Résolu':          { label: 'Résolu',          color: 'var(--statut-resolu)',   bg: 'var(--statut-resolu-bg)',   icon: 'check_circle' },
  'Rejeté':          { label: 'Rejeté',          color: 'var(--statut-rejete)',   bg: 'var(--statut-rejete-bg)',   icon: 'cancel' },
  'Problème':        { label: 'Problème',        color: 'var(--statut-probleme)', bg: 'var(--statut-probleme-bg)', icon: 'error' },
};

/**
 * Couleurs vives des statuts, pour les repères qui doivent se lire d'un coup
 * d'oeil : l'anneau du tableau de bord et les onglets de la file d'approbation.
 *
 * Orange pour ce qui attend, bleu pour ce qui est en cours, vert pour ce qui est
 * clôturé, rouge pour ce qui est rejeté. Des teintes de milieu de gamme, lisibles
 * sur fond clair comme sur fond sombre. Les pastilles de statut des listes
 * gardent les teintes de STATUT_CFG, plus douces, qui suivent le thème.
 */
export const COULEURS_STATUT: Record<Statut, string> = {
  'En attente': '#f97316',
  'Prise en Charge': '#3b82f6',
  'Résolu': '#22c55e',
  'Rejeté': '#ef4444',
  'Problème': '#a855f7',
};

export const FILIALES = ['EOT', 'FUBA', 'HELIOFLEX', 'OTBS', 'OTH', 'OTMA', 'TC', 'TPI', 'TTEI'];

/** Pastille par defaut : une valeur absente ou inconnue reste lisible plutot que
 *  de casser la grille. */
export const PASTILLE_DEFAUT: Pastille = { color: 'var(--cat-autre)', bg: 'var(--cat-autre-bg)', icon: 'label' };

export const PRIORITE_CFG: Record<string, Pastille> = {
  'Faible':   { color: 'var(--prio-faible)',   bg: 'var(--prio-faible-bg)',   icon: 'south' },
  'Modéré':   { color: 'var(--prio-modere)',   bg: 'var(--prio-modere-bg)',   icon: 'drag_handle' },
  'Urgent':   { color: 'var(--prio-urgent)',   bg: 'var(--prio-urgent-bg)',   icon: 'priority_high' },
  'Critique': { color: 'var(--prio-critique)', bg: 'var(--prio-critique-bg)', icon: 'warning' },
};

export const CATEGORIE_CFG: Record<string, Pastille> = {
  'Applicatifs':    { color: 'var(--cat-applicatifs)',    bg: 'var(--cat-applicatifs-bg)',    icon: 'desktop_windows' },
  'Backup':         { color: 'var(--cat-backup)',         bg: 'var(--cat-backup-bg)',         icon: 'backup' },
  'Communication':  { color: 'var(--cat-communication)',  bg: 'var(--cat-communication-bg)',  icon: 'forum' },
  'Infrastructure': { color: 'var(--cat-infrastructure)', bg: 'var(--cat-infrastructure-bg)', icon: 'dns' },
  'Microsoft':      { color: 'var(--cat-microsoft)',      bg: 'var(--cat-microsoft-bg)',      icon: 'grid_view' },
  'Réseau':         { color: 'var(--cat-reseau)',         bg: 'var(--cat-reseau-bg)',         icon: 'lan' },
  'Système':        { color: 'var(--cat-systeme)',        bg: 'var(--cat-systeme-bg)',        icon: 'memory' },
  'Sécurité':       { color: 'var(--cat-securite)',       bg: 'var(--cat-securite-bg)',       icon: 'shield' },
};

export function prioriteCfg(nom: string | null | undefined): Pastille {
  return PRIORITE_CFG[(nom ?? '').trim()] ?? PASTILLE_DEFAUT;
}

export function categorieCfg(nom: string | null | undefined): Pastille {
  return CATEGORIE_CFG[(nom ?? '').trim()] ?? PASTILLE_DEFAUT;
}

/** Seuil de confiance du modele en production (models/model_metadata.json,
 *  confidence_threshold). En dessous, la classification est jugee incertaine et
 *  doit etre verifiee par un administrateur. Le moniteur hors ligne utilise la
 *  meme valeur ; l'ecran de monitoring la relit dans l'API quand elle est
 *  disponible. */
export const SEUIL_CONFIANCE = 0.60;

/** Correspondance RAG en dessous de laquelle un ticket est un cas nouveau
 *  (NOVELTY_THRESHOLD dans api/routers/tickets.py). */
export const SEUIL_NOUVEAUTE_RAG = 0.5;

/**
 * Lit une date renvoyee par l'API.
 *
 * Les colonnes DateTime de api/db/models.py ne portent pas de fuseau : la base
 * garde l'heure UTC, et l'API la serialise sans marqueur ("2026-09-17T21:10:06").
 * `new Date()` interprete alors cette chaine comme une heure locale, ce qui
 * decale tous les affichages de l'ecart du poste (une heure en Tunisie) et rend
 * un ticket qui vient d'arriver plus vieux qu'il ne l'est. On ajoute donc le Z
 * quand aucun fuseau n'est present.
 */
export function dateTicket(iso: string | null | undefined): Date {
  if (!iso) return new Date(NaN);
  const avecFuseau = /([zZ]|[+-]\d{2}:?\d{2})$/.test(iso);
  return new Date(avecFuseau ? iso : iso + 'Z');
}

/**
 * Le jour d'un horodatage, au format AAAA-MM-JJ du poste.
 *
 * C'est ce que renvoie un champ `<input type="date">`, donc le format dans
 * lequel les filtres par calendrier comparent. Le jour est celui de l'heure
 * locale : un ticket reçu à minuit dix appartient au jour que l'administrateur
 * a sous les yeux, pas au jour UTC.
 */
export function jourTicket(iso: string | null | undefined): string {
  const d = dateTicket(iso);
  if (Number.isNaN(d.getTime())) return '';
  const deuxChiffres = (n: number) => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${deuxChiffres(d.getMonth() + 1)}-${deuxChiffres(d.getDate())}`;
}

/** Couleur d'une confiance : vert au-dessus du seuil, ambre entre 40 % et le
 *  seuil, rouge en dessous de 40 %. Variables du theme, donc lisibles dans les
 *  deux modes. */
export function couleurConfiance(c: number | null | undefined, seuil = SEUIL_CONFIANCE): string {
  if (c == null) return 'var(--color-outline)';
  if (c >= seuil) return 'var(--statut-resolu)';
  if (c >= 0.40) return 'var(--statut-attente)';
  return 'var(--statut-rejete)';
}
