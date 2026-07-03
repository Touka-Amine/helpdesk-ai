/** Alias pour la catégorie de ticket (chaîne libre côté backend) */
export type TicketCategory = string;

/** Statuts valides — alignés sur VALID_STATUSES dans api/routers/tickets.py */
export type Statut =
  | 'En attente'
  | 'Prise en Charge'
  | 'Résolu'
  | 'Rejeté'
  | 'Problème';

/** Correspond à ticket_to_dict() dans api/services/ticket_service.py */
export interface Ticket {
  id: number;
  titre: string;
  description: string;
  priorite_saisie: string;
  filiale: string;
  equipement: string;
  statut: Statut;
  categorie_predite: string;
  categorie_finale: string;
  confiance: number | null;
  solution_rag: string;
  knowledge_rag: string;
  created_at: string;
  date_resolution: string | null;
  commentaire_client: string;
  commentaire_interne: string;
  classification: string;
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

export const STATUT_CFG: Record<Statut, { label: string; color: string; bg: string }> = {
  'En attente':     { label: 'En attente',     color: '#92400e', bg: '#fef3c7' },
  'Prise en Charge':{ label: 'Prise en Charge', color: '#065f46', bg: '#d1fae5' },
  'Résolu':         { label: 'Résolu',          color: '#14532d', bg: '#bbf7d0' },
  'Rejeté':         { label: 'Rejeté',          color: '#991b1b', bg: '#fee2e2' },
  'Problème':       { label: 'Problème',        color: '#4c1d95', bg: '#ede9fe' },
};

export const FILIALES = ['OTBS', 'Siège', 'HELIOFLEX', 'Agence Nord', 'Agence Sud'];
