import { TicketCategory } from './ticket.models';

// ⚠️ Champs déduits de la route Swagger POST /predict et de RESUME_PROJET_PFE.md
// (§3.3 seuil 0.40, §5.2 couche heuristique) — à confirmer.

export interface PredictTicketRequest {
  description: string; // ⚠️ à confirmer — probablement le texte brut du ticket
}

export interface PredictionResult {
  category: TicketCategory;
  confidence: number; // seuil de routage auto = 0.40 (RESUME §3.3)
  auto_routed: boolean; // ⚠️ nom de champ à confirmer — true si confidence ≥ 0.40
  rag_suggestion?: string; // ⚠️ /predict renvoie peut-être aussi la reco RAG, ou c'est un appel séparé
}
