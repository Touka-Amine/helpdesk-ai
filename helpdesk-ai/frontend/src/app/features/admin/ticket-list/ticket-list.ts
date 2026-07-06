import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket, Statut, STATUT_CFG } from '../../../models/ticket.models';

@Component({
  selector: 'app-ticket-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-list.html',
  styleUrl: './ticket-list.css',
})
export class TicketList implements OnInit {
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);

  searchTerm = signal('');
  statutFilter = signal<Statut | ''>('');
  categorieFilter = signal<string>('');

  statutCfg = STATUT_CFG;

  categories = computed(() => {
    const set = new Set<string>();
    for (const t of this.tickets()) {
      const c = t.categorie_finale || t.categorie_predite;
      if (c) set.add(c);
    }
    return Array.from(set).sort();
  });

  filtered = computed(() => {
    const term = this.searchTerm().toLowerCase().trim();
    const statut = this.statutFilter();
    const categorie = this.categorieFilter();
    return this.tickets().filter(t => {
      if (statut && t.statut !== statut) return false;
      if (categorie && (t.categorie_finale || t.categorie_predite) !== categorie) return false;
      if (term && !(t.titre.toLowerCase().includes(term) || t.demandeur_nom.toLowerCase().includes(term) || t.id.toString().includes(term))) return false;
      return true;
    });
  });

  enAttenteCount = computed(() => this.tickets().filter(t => t.statut === 'En attente').length);

  delaiMoyenLabel = computed(() => {
    const resolus = this.tickets().filter(t => t.statut === 'Résolu' && t.date_resolution);
    if (!resolus.length) return '—';
    const totalH = resolus.reduce((acc, t) => {
      const debut = new Date(t.created_at).getTime();
      const fin = new Date(t.date_resolution!).getTime();
      return acc + (fin - debut) / 3_600_000;
    }, 0);
    const h = totalH / resolus.length;
    return h < 1 ? `${Math.round(h * 60)} min` : `${h.toFixed(1)} h`;
  });

  ngOnInit(): void {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading.set(true);
    this.ticketApi.getAllTickets().subscribe({
      next: (data) => {
        this.tickets.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  formatDate(iso: string): string {
    const d = new Date(iso);
    const diffH = (Date.now() - d.getTime()) / 3_600_000;
    if (diffH < 24 && d.getDate() === new Date().getDate()) {
      return `Aujourd'hui, ${d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`;
    }
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  resetFilters(): void {
    this.searchTerm.set('');
    this.statutFilter.set('');
    this.categorieFilter.set('');
  }

  goToDetail(id: number): void {
    this.router.navigate(['/admin/tickets', id]);
  }
}
