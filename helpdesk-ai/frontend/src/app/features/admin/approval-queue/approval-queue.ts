import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket, ApproveTicketRequest, Statut } from '../../../models/ticket.models';

@Component({
  selector: 'app-approval-queue',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './approval-queue.html',
  styleUrl: './approval-queue.css',
})
export class ApprovalQueue implements OnInit {
  private ticketApi = inject(TicketApiService);

  allTickets = signal<Ticket[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  submitting = signal(false);

  selectedTicket = signal<Ticket | null>(null);
  messageClient = signal('');
  noteInterne = signal('');

  pendingTickets = computed(() =>
    this.allTickets().filter(t => t.statut === 'En attente')
  );

  ngOnInit(): void {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading.set(true);
    this.error.set(null);
    this.ticketApi.getAllTickets().subscribe({
      next: (data: Ticket[]) => {
        this.allTickets.set(data);
        this.loading.set(false);
        // sélectionne le premier ticket en attente par défaut
        if (this.pendingTickets().length > 0 && !this.selectedTicket()) {
          this.selectTicket(this.pendingTickets()[0]);
        }
      },
      error: () => {
        this.error.set('Impossible de charger les tickets.');
        this.loading.set(false);
      },
    });
  }

  selectTicket(t: Ticket): void {
    this.selectedTicket.set(t);
    this.messageClient.set('');
    this.noteInterne.set('');
  }

  getConfidence(t: Ticket): number {
    return t.confiance ?? 0;
  }
  getCategory(t: Ticket): string {
    return t.categorie_finale || t.categorie_predite || 'Non classé';
  }
  getRagSuggestion(t: Ticket): string {
    return t.solution_rag || 'Aucune suggestion disponible pour ce ticket.';
  }

  isAutoRouted(t: Ticket): boolean {
    return this.getConfidence(t) >= 0.40;
  }

  timeAgo(iso: string): string {
    const diffMin = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (diffMin < 60) return `${diffMin} min`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `${diffH} h`;
    return `${Math.round(diffH / 24)} j`;
  }

  approve(): void {
    const t = this.selectedTicket();
    if (!t) return;
    this.submit(t, 'Prise en Charge' as Statut);
  }

  reject(): void {
    const t = this.selectedTicket();
    if (!t) return;
    this.submit(t, 'Rejeté' as Statut);
  }

  private submit(t: Ticket, statut: Statut): void {
    const payload: ApproveTicketRequest = {
      statut,
      commentaire_client: this.messageClient() || undefined,
      commentaire_interne: this.noteInterne() || undefined,
    };

    this.submitting.set(true);
    this.ticketApi.approveTicket(t.id, payload).subscribe({
      next: () => {
        this.submitting.set(false);
        this.loadTickets();
        this.selectedTicket.set(null);
      },
      error: (err: any) => {
        this.submitting.set(false);
        this.error.set(`Erreur lors de la mise à jour (${err.status}).`);
      },
    });
  }

  refreshRag(): void {
    const t = this.selectedTicket();
    if (!t) return;
    this.ticketApi.refreshRag(t.id).subscribe({
      next: () => this.loadTickets(),
      error: () => this.error.set('Impossible de rafraîchir la suggestion RAG.'),
    });
  }
}