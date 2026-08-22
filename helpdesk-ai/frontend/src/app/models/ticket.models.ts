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

export const STATUT_CFG: Record<Statut, { label: string; color: string; bg: string }> = {
  'En attente':     { label: 'En attente',     color: '#92400e', bg: '#fef3c7' },
  'Prise en Charge':{ label: 'Prise en Charge', color: '#065f46', bg: '#d1fae5' },
  'Résolu':         { label: 'Résolu',          color: '#14532d', bg: '#bbf7d0' },
  'Rejeté':         { label: 'Rejeté',          color: '#991b1b', bg: '#fee2e2' },
  'Problème':       { label: 'Problème',        color: '#4c1d95', bg: '#ede9fe' },
};

export const FILIALES = ['EOT', 'FUBA', 'HELIOFLEX', 'OTBS', 'OTH', 'OTMA', 'TC', 'TPI', 'TTEI'];
