import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket, Statut, STATUT_CFG } from '../../../models/ticket.models';

const STATUT_BADGE_CLASSES: Record<Statut, string> = {
  'En attente': 'bg-amber-100 text-amber-700',
  'Prise en Charge': 'bg-blue-100 text-blue-700',
  Résolu: 'bg-green-100 text-green-700',
  Rejeté: 'bg-red-100 text-red-700',
  Problème: 'bg-purple-100 text-purple-700',
};

@Component({
  selector: 'app-my-tickets',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './my-tickets.html',
  styleUrl: './my-tickets.css',
})
export class MyTickets implements OnInit {
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  statutFilter = signal<'Tous' | Statut>('Tous');
  searchFilter = signal('');

  statutOptions: ('Tous' | Statut)[] = ['Tous', ...(Object.keys(STATUT_CFG) as Statut[])];
  statutCfg = STATUT_CFG;

  filtered = computed(() => {
    let result = this.tickets();
    const statut = this.statutFilter();
    const search = this.searchFilter().toLowerCase().trim();

    if (statut !== 'Tous') {
      result = result.filter((t) => t.statut === statut);
    }
    if (search) {
      result = result.filter(
        (t) => t.titre.toLowerCase().includes(search) || String(t.id).includes(search)
      );
    }
    return result;
  });

  totalCount = computed(() => this.tickets().length);
  enAttenteCount = computed(() => this.tickets().filter((t) => t.statut === 'En attente').length);
  resoluCount = computed(() => this.tickets().filter((t) => t.statut === 'Résolu').length);

  cetteSemaineCount = computed(() => {
    const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    return this.tickets().filter((t) => new Date(t.created_at).getTime() >= weekAgo).length;
  });

  tauxResolution = computed(() => {
    const total = this.totalCount();
    return total > 0 ? Math.round((this.resoluCount() / total) * 100) : null;
  });

  delaiMoyenHeures = computed(() => {
    const resolus = this.tickets().filter((t) => t.statut === 'Résolu' && t.date_resolution);
    if (resolus.length === 0) return null;
    const totalMs = resolus.reduce(
      (acc, t) => acc + (new Date(t.date_resolution!).getTime() - new Date(t.created_at).getTime()),
      0
    );
    return Math.round(totalMs / resolus.length / 3600000);
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
      error: () => {
        this.error.set('Impossible de charger vos tickets.');
        this.loading.set(false);
      },
    });
  }

  goToNewTicket(): void {
    this.router.navigate(['/client/new-ticket']);
  }

  goToDetail(id: number): void {
    this.router.navigate(['/client/tickets', id]);
  }

  statutBadgeClass(s: Statut): string {
    return STATUT_BADGE_CLASSES[s];
  }

  formatDateTime(iso: string): string {
    const d = new Date(iso);
    const now = new Date();
    const time = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

    if (d.toDateString() === now.toDateString()) return `Aujourd'hui, ${time}`;

    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString()) return `Hier, ${time}`;

    return `${d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}, ${time}`;
  }
}
