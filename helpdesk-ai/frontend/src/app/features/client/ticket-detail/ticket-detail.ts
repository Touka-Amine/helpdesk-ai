import { Component, OnDestroy, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { relirePeriodiquement } from '../../../core/services/relecture';
import { CONTACT_OTBS } from '../../../core/contact-otbs';
import { Ticket, STATUT_CFG, TicketHistoryEntry } from '../../../models/ticket.models';

@Component({
  selector: 'app-ticket-detail-client',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ticket-detail.html',
  styleUrl: './ticket-detail.css',
})
export class TicketDetailClient implements OnInit, OnDestroy {
  private route     = inject(ActivatedRoute);
  private router    = inject(Router);
  private ticketApi = inject(TicketApiService);

  ticket  = signal<Ticket | null>(null);
  history = signal<TicketHistoryEntry[]>([]);
  similarTitles = signal<string[]>([]);
  loading = signal(true);
  error   = signal<string | null>(null);

  feedbackDraft       = signal<'up' | 'down' | null>(null);
  showFeedbackForm    = signal(false);
  feedbackComment     = signal('');
  submittingFeedback  = signal(false);

  statutCfg = STATUT_CFG;
  contact = CONTACT_OTBS;

  // Dernière mise à jour "conviviale" pour le bloc Suivi — dérivée de l'historique
  // (déjà accessible au client pour son propre ticket) sans en exposer le detail brut.
  derniereMaj = computed(() => {
    const h = this.history();
    return h.length ? h[h.length - 1].timestamp : this.ticket()?.created_at ?? null;
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
      this.idCourant = id;
      this.loadTicket(id);
    });
    // La reponse du technicien et le changement de statut arrivent sans recharger.
    this.arreterRelecture = relirePeriodiquement(() => this.rafraichir());
  }

  private idCourant: number | null = null;
  private arreterRelecture?: () => void;

  ngOnDestroy(): void {
    this.arreterRelecture?.();
  }

  /**
   * Relecture de fond du ticket ouvert et de son historique.
   *
   * Contrairement a `loadTicket`, elle ne remet rien a zero : un retour que le
   * demandeur est en train de rediger reste en place, et un echec passager ne
   * remplace pas le ticket affiche par un message d'erreur.
   */
  private rafraichir(): void {
    const id = this.idCourant;
    if (id === null || this.loading() || this.submittingFeedback()) return;
    this.ticketApi.getMyTicketDetail(id).subscribe({
      next: (t) => { if (this.idCourant === id) this.ticket.set(t); },
      error: () => {},
    });
    this.ticketApi.getTicketHistory(id).subscribe({
      next: (h) => { if (this.idCourant === id) this.history.set(h); },
      error: () => {},
    });
  }

  private loadTicket(id: number): void {
    this.loading.set(true);
    this.error.set(null);
    this.feedbackDraft.set(null);
    this.showFeedbackForm.set(false);
    this.feedbackComment.set('');
    this.history.set([]);
    this.similarTitles.set([]);
    this.ticketApi.getMyTicketDetail(id).subscribe({
      next: (t) => {
        this.ticket.set(t);
        this.loading.set(false);
        this.ticketApi.getTicketHistory(id).subscribe({
          next: (h) => this.history.set(h),
          error: () => {},
        });
        this.ticketApi.getSimilarTitles(id).subscribe({
          next: (r) => this.similarTitles.set(r.titres),
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

  goToNewTicket(): void {
    this.router.navigate(['/client/new-ticket']);
  }
}
