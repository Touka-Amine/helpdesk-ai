import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket } from '../../../models/ticket.models';

@Component({
  selector: 'app-approval-queue',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './approval-queue.html',
  styleUrl: './approval-queue.css',
})
export class ApprovalQueue implements OnInit {
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);

  allTickets = signal<Ticket[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  opening = signal<number | null>(null);

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
      },
      error: () => {
        this.error.set('Impossible de charger les tickets.');
        this.loading.set(false);
      },
    });
  }

  getConfidence(t: Ticket): number {
    return t.confiance ?? 0;
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

  /** Un simple clic prend le ticket en charge (statut change automatiquement) et
   *  ouvre directement l'écran de traitement complet — plus de popup de décision
   *  ici, cet écran ne sert qu'à réceptionner rapidement les tickets en attente. */
  openTicket(t: Ticket): void {
    this.opening.set(t.id);
    this.error.set(null);
    this.ticketApi.approveTicket(t.id, { statut: 'Prise en Charge' }).subscribe({
      next: () => this.router.navigate(['/admin/tickets', t.id]),
      error: () => {
        this.opening.set(null);
        this.error.set('Impossible de prendre ce ticket en charge.');
      },
    });
  }
}
