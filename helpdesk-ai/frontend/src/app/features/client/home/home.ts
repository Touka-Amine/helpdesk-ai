import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { Ticket, Statut, STATUT_CFG } from '../../../models/ticket.models';

const CATEGORY_ICONS: Record<string, string> = {
  Réseau: 'wifi',
  Sécurité: 'security',
  Applicatifs: 'apps',
  Backup: 'backup',
  Communication: 'forum',
  Infrastructure: 'dns',
  Microsoft: 'window',
  Système: 'settings',
};

const STATUT_BADGE_CLASSES: Record<Statut, string> = {
  'En attente': 'bg-amber-100 text-amber-700',
  'Prise en Charge': 'bg-blue-100 text-blue-700',
  Résolu: 'bg-green-100 text-green-700',
  Rejeté: 'bg-red-100 text-red-700',
  Problème: 'bg-purple-100 text-purple-700',
};

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit {
  private ticketApi = inject(TicketApiService);
  private auth = inject(AuthService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);
  statutCfg = STATUT_CFG;

  userFirstName = computed(() => this.auth.currentUser()?.prenom ?? '');
  totalCount = computed(() => this.tickets().length);
  recentTickets = computed(() => this.tickets().slice(0, 3));

  avgConfidencePercent = computed(() => {
    const withConf = this.tickets().filter((t) => t.confiance != null);
    if (withConf.length === 0) return null;
    const sum = withConf.reduce((acc, t) => acc + (t.confiance as number), 0);
    return Math.round((sum / withConf.length) * 100);
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

  categoryIcon(t: Ticket): string {
    const cat = t.categorie_finale || t.categorie_predite;
    return CATEGORY_ICONS[cat] ?? 'confirmation_number';
  }

  statutBadgeClass(s: Statut): string {
    return STATUT_BADGE_CLASSES[s];
  }

  formatDateShort(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  timeAgo(iso: string): string {
    const diffMs = Date.now() - new Date(iso).getTime();
    const min = Math.floor(diffMs / 60000);
    if (min < 1) return "à l'instant";
    if (min < 60) return `il y a ${min} min`;
    const h = Math.floor(min / 60);
    if (h < 24) return `il y a ${h} h`;
    const d = Math.floor(h / 24);
    if (d === 1) return 'hier';
    if (d < 7) return `il y a ${d} jours`;
    return this.formatDateShort(iso);
  }
}
