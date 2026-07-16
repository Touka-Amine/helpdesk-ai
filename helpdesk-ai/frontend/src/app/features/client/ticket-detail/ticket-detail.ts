import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket, STATUT_CFG, TicketHistoryEntry } from '../../../models/ticket.models';

@Component({
  selector: 'app-ticket-detail-client',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ticket-detail.html',
  styleUrl: './ticket-detail.css',
})
export class TicketDetailClient implements OnInit {
  private route     = inject(ActivatedRoute);
  private router    = inject(Router);
  private ticketApi = inject(TicketApiService);

  ticket  = signal<Ticket | null>(null);
  history = signal<TicketHistoryEntry[]>([]);
  loading = signal(true);
  error   = signal<string | null>(null);

  feedbackDraft       = signal<'up' | 'down' | null>(null);
  showFeedbackForm    = signal(false);
  feedbackComment     = signal('');
  submittingFeedback  = signal(false);

  statutCfg = STATUT_CFG;

  confiance = computed(() => {
    const c = this.ticket()?.confiance;
    return c != null ? Math.round(c * 100) : null;
  });

  confianceColor = computed(() => {
    const c = this.confiance();
    if (c == null) return '#9ca3af';
    if (c >= 70)  return '#15803d';
    if (c >= 40)  return '#b45309';
    return '#dc2626';
  });

  // La solution RAG (texte technique destine a un agent IT) n'est pas affichee au
  // client, qui n'a pas les connaissances pour l'interpreter. On lui montre a la
  // place un message de suivi simple, base sur le statut.
  suiviMessage = computed(() => {
    switch (this.ticket()?.statut) {
      case 'En attente':
        return "Votre demande a bien été reçue et automatiquement classée. Un technicien va l'examiner très prochainement.";
      case 'Prise en Charge':
        return 'Votre demande est en cours de traitement par notre équipe IT.';
      case 'Problème':
        return 'Un point de blocage a été identifié sur votre demande, notre équipe IT y travaille activement.';
      case 'Rejeté':
        return 'Cette demande a été clôturée par notre équipe IT.';
      default:
        return 'Votre demande a bien été reçue.';
    }
  });

  suiviIcon = computed(() => {
    switch (this.ticket()?.statut) {
      case 'En attente': return 'schedule';
      case 'Prise en Charge': return 'build';
      case 'Problème': return 'report';
      case 'Rejeté': return 'block';
      default: return 'info';
    }
  });

  ngOnInit(): void {
    // route.paramMap (observable) plutot que route.snapshot : naviguer d'un ticket
    // a un autre reutilise le meme composant, un snapshot fige laisserait le
    // ticket precedent affiche tant que la page n'est pas rechargee.
    this.route.paramMap.subscribe((params) => {
      const id = Number(params.get('id'));
      this.loadTicket(id);
    });
  }

  private loadTicket(id: number): void {
    this.loading.set(true);
    this.error.set(null);
    this.feedbackDraft.set(null);
    this.showFeedbackForm.set(false);
    this.feedbackComment.set('');
    this.history.set([]);
    this.ticketApi.getMyTicketDetail(id).subscribe({
      next: (t) => {
        this.ticket.set(t);
        this.loading.set(false);
        this.ticketApi.getTicketHistory(id).subscribe({
          next: (h) => this.history.set(h),
          error: () => {},
        });
      },
      error: () => {
        this.error.set('Ticket introuvable ou accès refusé.');
        this.loading.set(false);
      },
    });
  }

  selectFeedback(vote: 'up' | 'down'): void {
    this.feedbackDraft.set(vote);
    this.showFeedbackForm.set(true);
  }

  submitFeedback(): void {
    const t = this.ticket();
    const vote = this.feedbackDraft();
    if (!t || !vote) return;

    this.submittingFeedback.set(true);
    this.ticketApi.submitFeedback(t.id, vote, this.feedbackComment().trim()).subscribe({
      next: (updated) => {
        this.ticket.set(updated);
        this.submittingFeedback.set(false);
        this.showFeedbackForm.set(false);
      },
      error: () => {
        this.submittingFeedback.set(false);
      },
    });
  }

  formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  printTicket(): void {
    window.print();
  }

  goBack(): void {
    this.router.navigate(['/client/my-tickets']);
  }
}
