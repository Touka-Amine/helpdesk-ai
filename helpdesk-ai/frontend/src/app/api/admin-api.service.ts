import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import {
  AdminUser,
  AdminUserCreateRequest,
  AdminUserCreateResponse,
} from '../models/auth.models';

export interface ModelInfo {
  model_name: string;
  f1_macro_ml_seul: number;
  f1_macro_avec_heuristiques: number;
  accuracy_test: number;
  confidence_threshold: number;
  classes: string[];
  train_size: number;
  test_size: number;
  dataset_note: string;
  known_weaknesses: string[];
}

// ── Rapports de monitoring, produits hors ligne et lus tels quels par l'API ──
// Chaque rapport peut manquer : l'API renvoie alors { disponible: false, motif }.

export interface RapportIndisponible { disponible?: false; motif?: string }

/** metrics/ml_monitor.json (src/monitoring/ml_monitor.py). */
export interface RapportML {
  disponible?: boolean;
  motif?: string;
  generated_at?: string;
  fenetre_jours?: number;
  n_tickets_total?: number;
  desaccord?: { n_tickets_valides?: number; taux_pct?: number | null; note?: string };
  confiance?: { moyenne: number; mediane: number; p10: number; part_sous_seuil: number; seuil: number };
  derive_distribution?: { psi?: number | null; n_production?: number; lecture?: string; avertissement?: string };
  non_mesurable?: string[];
}

/** Un déclencheur de réentraînement (params.yaml, section retrain). */
export interface Declencheur {
  nom: string;
  valeur: number | null;
  seuil: number | null;
  declenche: boolean;
  justification?: string;
}

/** metrics/should_retrain.json : une recommandation, jamais une action. */
export interface EtatReentrainement {
  disponible?: boolean;
  motif?: string;
  generated_at?: string;
  should_retrain?: boolean;
  declencheurs?: Declencheur[];
  verrou_temporel?: { bloque?: boolean; motif?: string; derniere_promotion?: string; min_days_between_retrains?: number };
}

/** metrics/promotion_decision.json. Ses metriques_production sont celles du modèle
 *  en production réévalué sur le jeu de test de référence : ce sont les chiffres
 *  qui font foi, pas ceux de models/model_metadata.json, antérieurs au registre. */
export interface DecisionPromotion {
  disponible?: boolean;
  motif?: string;
  at?: string;
  resultat?: string;
  version_candidate?: number;
  version_production_precedente?: number;
  n_test?: number;
  metriques_production?: Record<string, number>;
}

export interface Registre {
  disponible?: boolean;
  aliases?: { production?: number };
}

/** metrics/rag_monitor.json. */
export interface RapportRag {
  disponible?: boolean;
  motif?: string;
  generated_at?: string;
  production?: { n_tickets?: number };
  base_connaissances?: { disponible?: boolean; total?: number; note?: string };
  non_mesurable?: string[];
}

/** metrics/rag_eval.json. */
export interface EvaluationRag {
  disponible?: boolean;
  motif?: string;
  generated_at?: string;
  protocole?: string;
  avertissement_protocole?: string;
  moteurs?: { hybride?: { precision_at_3?: number; n_requetes?: number } };
}

@Injectable({ providedIn: 'root' })
export class AdminApiService {
  private readonly base = `${environment.apiUrl}/admin`;

  constructor(private http: HttpClient) {}

  getUsers() {
    return this.http.get<AdminUser[]>(`${this.base}/users`);
  }

  createUser(payload: AdminUserCreateRequest) {
    return this.http.post<AdminUserCreateResponse>(`${this.base}/users`, payload);
  }

  updateUser(userId: number, payload: {
    role?: string; is_active?: boolean; nom?: string; prenom?: string; filiale?: string;
  }) {
    return this.http.patch<AdminUser>(`${this.base}/users/${userId}`, payload);
  }

  getModelInfo() {
    return this.http.get<ModelInfo>(`${this.base}/model-info`);
  }

  getRapportML() {
    return this.http.get<RapportML>(`${this.base}/monitoring/ml`);
  }

  getEtatReentrainement() {
    return this.http.get<EtatReentrainement>(`${this.base}/monitoring/retrain-trigger`);
  }

  getDecisionPromotion() {
    return this.http.get<DecisionPromotion>(`${this.base}/promotion-decision`);
  }

  getRegistre() {
    return this.http.get<Registre>(`${this.base}/registry`);
  }

  getRapportRag() {
    return this.http.get<RapportRag>(`${this.base}/monitoring/rag`);
  }

  getEvaluationRag() {
    return this.http.get<EvaluationRag>(`${this.base}/monitoring/rag-eval`);
  }
}
