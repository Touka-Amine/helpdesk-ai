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

  feedback        = signal<'up' | 'down' | null>(null);
  feedbackSent    = signal(false);
  showFeedbackForm = signal(false);
  feedbackComment = signal('');

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

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
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

  sendFeedback(vote: 'up' | 'down'): void {
    this.feedback.set(vote);
    if (vote === 'down') {
      this.showFeedbackForm.set(true);
    } else {
      this.feedbackSent.set(true);
    }
  }

  submitFeedbackComment(): void {
    // TODO: POST /api/v1/tickets/{id}/feedback quand l'endpoint sera créé
    console.log('Feedback:', this.feedback(), '|', this.feedbackComment());
    this.showFeedbackForm.set(false);
    this.feedbackSent.set(true);
  }

  formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  goBack(): void {
    this.router.navigate(['/client/my-tickets']);
  }
}
