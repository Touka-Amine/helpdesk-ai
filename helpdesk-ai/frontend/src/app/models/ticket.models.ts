export type Statut = 'Ouvert' | 'En cours' | 'Résolu' | 'Fermé';

export interface Ticket {
  id: number;
  titre: string;
  description: string;        // ← manquant
  statut: Statut;
  filiale: string;
  created_at: string;
  priorite?: string;
  equipement?: string;
}

export interface CreateTicketRequest {
  titre: string;
  description: string;
  priorite: string;
  filiale: string;
  equipement: string;
}

export interface ApproveTicketRequest {
  statut: Statut;
  message_client?: string;
  note_interne?: string;
}

export interface TicketHistoryEntry {
  id: number;
  ticket_id: number;
  action: string;
  created_at: string;
  auteur?: string;
}

// ⚠️ Champs à vérifier contre api/schemas/ticket_schemas.py — non confirmés
export const STATUT_CFG: Record<Statut, { label: string; color: string }> = {
  'Ouvert':   { label: 'Ouvert',   color: '#b45309' }, // amber
  'En cours': { label: 'En cours', color: '#0f766e' }, // teal
  'Résolu':   { label: 'Résolu',   color: '#15803d' },
  'Fermé':    { label: 'Fermé',    color: '#6b7280' },
};

export const FILIALES = ['OTBS', 'Siège', 'Agence Nord', 'Agence Sud']; // ⚠️ à confirmer
export type TicketCategory =
  | 'Microsoft'
  | 'Réseau'
  | 'Applicatifs'
  | 'Infrastructure'
  | 'Système'
  | 'Communication'
  | 'Sécurité'
  | 'Backup';