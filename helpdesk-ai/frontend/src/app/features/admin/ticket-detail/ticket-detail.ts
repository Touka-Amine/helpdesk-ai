import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import {
  Ticket, STATUT_CFG, TicketHistoryEntry,
  Statut, ApproveTicketRequest,
} from '../../../models/ticket.models';

// Meme seuil que NOVELTY_THRESHOLD cote backend (api/routers/tickets.py)
const NOVELTY_THRESHOLD = 0.5;

const TRANSITIONS: Record<Statut, Statut[]> = {
  'En attente':      ['Prise en Charge', 'Rejeté'],
  'Prise en Charge': ['Résolu', 'Problème', 'En attente'],
  'Problème':        ['Prise en Charge', 'Résolu'],
  'Résolu':          [],
  'Rejeté':          [],
};

@Component({
  selector: 'app-ticket-detail',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './ticket-detail.html',
  styleUrl: './ticket-detail.css',
})
export class TicketDetail implements OnInit {
  private route     = inject(ActivatedRoute);
  private router    = inject(Router);
  private ticketApi = inject(TicketApiService);
  private fb        = inject(FormBuilder);

  ticket   = signal<Ticket | null>(null);
  history  = signal<TicketHistoryEntry[]>([]);
  loading  = signal(true);
  saving   = signal(false);
  error    = signal<string | null>(null);
  success  = signal<string | null>(null);

  statutCfg = STATUT_CFG;
  availableStatuts = signal<Statut[]>([]);

  // Aucun cas historique proche : la solution appliquee devient obligatoire
  // avant de resoudre, car c'est elle qui alimentera la base de connaissances.
  isNovelCase = computed(() => {
    const s = this.ticket()?.rag_score;
    return s == null || s < NOVELTY_THRESHOLD;
  });

  form = this.fb.group({
    statut:            ['', Validators.required],
    categorie_finale:  [''],
    commentaire_client:    [''],
    commentaire_interne:   [''],
  });

  ngOnInit(): void {
    // route.paramMap (observable) plutot que route.snapshot : la navigation d'un
    // ticket vers un autre reutilise le meme composant (meme route), donc un
    // snapshot lu une seule fois au demarrage laisserait afficher le ticket
    // precedent tant que la page n'est pas rechargee manuellement.
    this.route.paramMap.subscribe((params) => {
      const id = Number(params.get('id'));
      this.loadTicket(id);
    });
  }

  private loadTicket(id: number): void {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    this.history.set([]);
    this.ticketApi.getMyTicketDetail(id).subscribe({
      next: (t) => {
        this.ticket.set(t);
        this.loading.set(false);
        this.form.patchValue({
          statut: t.statut,
          categorie_finale: t.categorie_finale,
          commentaire_client: t.commentaire_client,
          commentaire_interne: t.commentaire_interne,
        });
        this.availableStatuts.set(TRANSITIONS[t.statut] ?? []);
        this.ticketApi.getTicketHistory(id).subscribe({
          next: (h) => this.history.set(h),
          error: () => {},
        });
      },
      error: () => {
        this.error.set('Ticket introuvable.');
        this.loading.set(false);
      },
    });
  }

  save(): void {
    if (this.form.invalid || !this.ticket()) return;
    this.error.set(null);
    this.success.set(null);
    const v = this.form.value;

    if (v.statut === 'Résolu' && this.isNovelCase() && !(v.commentaire_interne ?? '').trim()) {
      this.error.set(
        "Aucun cas similaire connu pour ce ticket : décrivez la solution appliquée dans « Solution appliquée » avant de le marquer comme résolu.",
      );
      return;
    }

    this.saving.set(true);
    const payload: ApproveTicketRequest = {
      statut: v.statut as Statut,
      categorie_finale: v.categorie_finale ?? undefined,
      commentaire_client: v.commentaire_client ?? undefined,
      commentaire_interne: v.commentaire_interne ?? undefined,
    };
    this.ticketApi.approveTicket(this.ticket()!.id, payload).subscribe({
      next: () => {
        this.saving.set(false);
        this.success.set('Ticket mis à jour avec succès.');
        this.ticket.update(t => t ? { ...t, statut: payload.statut } : t);
        this.availableStatuts.set(TRANSITIONS[payload.statut] ?? []);
      },
      error: (err) => {
        this.saving.set(false);
        this.error.set(err.error?.detail ?? 'Erreur lors de la mise à jour.');
      },
    });
  }

  refreshRag(): void {
    if (!this.ticket()) return;
    this.ticketApi.refreshRag(this.ticket()!.id).subscribe({
      next: (updated: any) => {
        this.ticket.update(t => t ? { ...t, solution_rag: updated.solution_rag, knowledge_rag: updated.knowledge_rag, rag_score: updated.rag_score } : t);
        this.success.set('Recommandation RAG rafraîchie.');
      },
      error: () => this.error.set('Erreur lors du rafraîchissement RAG.'),
    });
  }

  formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  confPct(c: number | null): number {
    return c != null ? Math.round(c * 100) : 0;
  }

  confianceColor(c: number | null): string {
    if (c == null) return '#9ca3af';
    const p = c * 100;
    if (p >= 70) return '#15803d';
    if (p >= 40) return '#b45309';
    return '#dc2626';
  }
}
