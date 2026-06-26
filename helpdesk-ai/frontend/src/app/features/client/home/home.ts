import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket, STATUT_CFG } from '../../../models/ticket.models';

interface AiStats {
  autoRoutedPercent: number;
  avgConfidence: number;
  autoRoutedCount: number;
  totalCount: number;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit {
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);
  statutCfg = STATUT_CFG;

  totalCount = computed(() => this.tickets().length);
  enCoursCount = computed(() => this.tickets().filter(t => t.statut === 'En cours').length);
  resoluCount = computed(() => this.tickets().filter(t => t.statut === 'Résolu').length);
  recentTickets = computed(() => this.tickets().slice(0, 3));

  // ⚠️ Mock — à remplacer par un vrai appel à /predict ou un endpoint de stats agrégées
  // une fois que l'API expose ces métriques par utilisateur.
  aiStats = signal<AiStats>({
    autoRoutedPercent: 82,
    avgConfidence: 0.76,
    autoRoutedCount: 14,
    totalCount: 17,
  });

  ngOnInit(): void {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading.set(true);
    this.ticketApi.getMyTickets().subscribe({
      next: (data: Ticket[]) => {
        this.tickets.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  goToNewTicket(): void {
    this.router.navigate(['/client/new-ticket']);
  }

  goToMyTickets(): void {
    this.router.navigate(['/client/my-tickets']);
  }

  goToDetail(id: number): void {
    this.router.navigate(['/client/tickets', id]);
  }

  formatDateShort(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }
}