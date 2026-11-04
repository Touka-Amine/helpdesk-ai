import { Component, OnDestroy, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { relirePeriodiquement } from '../../../core/services/relecture';
import { CONTACT_OTBS } from '../../../core/contact-otbs';
import { Ticket, STATUT_CFG, dateTicket } from '../../../models/ticket.models';

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

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit, OnDestroy {
  private ticketApi = inject(TicketApiService);
  private auth = inject(AuthService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);
  statutCfg = STATUT_CFG;
  contact = CONTACT_OTBS;

  userFirstName = computed(() => this.auth.currentUser()?.prenom ?? '');
  totalCount = computed(() => this.tickets().length);
  recentTickets = computed(() => this.tickets().slice(0, 5));
  /** Tickets résolus sur lesquels le demandeur n'a pas encore donné son avis :
   *  le seul geste que l'application lui demande, et ce qui alimente le taux de
   *  satisfaction côté support. */
  aNoter = computed(() => this.tickets().filter((t) => t.statut === 'Résolu' && !t.feedback_vote));
  numerosANoter = computed(() =>
    this.aNoter().slice(0, 3).map((t) => '#' + t.id.toString().padStart(4, '0')).join(', '),
  );

  /** Le plus ancien ticket encore en attente d'une décision du support. */
  attenteLaPlusLongue = computed<Ticket | null>(() => {
    const attente = this.tickets().filter((t) => t.statut === 'En attente');
    if (attente.length === 0) return null;
    return attente.reduce((a, b) =>
      dateTicket(a.created_at).getTime() <= dateTicket(b.created_at).getTime() ? a : b,
    );
  });

  enTraitementCount = computed(() => this.tickets().filter((t) => t.statut === 'Prise en Charge').length);

  rienAFaire = computed(
    () => this.aNoter().length === 0 && this.attenteLaPlusLongue() === null && this.enTraitementCount() === 0,
  );

  resoluCount = computed(() => this.tickets().filter((t) => t.statut === 'Résolu').length);
  enAttenteCount = computed(() => this.tickets().filter((t) => t.statut === 'En attente').length);

  cetteSemaineCount = computed(() => {
    const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    return this.tickets().filter((t) => dateTicket(t.created_at).getTime() >= weekAgo).length;
  });

  tauxResolution = computed(() => {
    const total = this.totalCount();
    return total > 0 ? Math.round((this.resoluCount() / total) * 100) : null;
  });

  delaiMoyenHeures = computed(() => {
    const resolus = this.tickets().filter((t) => t.statut === 'Résolu' && t.date_resolution);
    if (resolus.length === 0) return null;
    const totalMs = resolus.reduce(
      (acc, t) => acc + (dateTicket(t.date_resolution).getTime() - dateTicket(t.created_at).getTime()),
      0,
    );
    return Math.round(totalMs / resolus.length / 3600000);
  });

  private arreterRelecture?: () => void;

  ngOnInit(): void {
    this.loadTickets();
    // Le changement de statut decide par un technicien s'affiche sans recharger.
    this.arreterRelecture = relirePeriodiquement(() => this.loadTickets(true));
  }

  ngOnDestroy(): void {
    this.arreterRelecture?.();
  }

  /** `silencieux` : relecture de fond, sans voyant de chargement. */
  loadTickets(silencieux = false): void {
    if (!silencieux) this.loading.set(true);
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

  /** Mes tickets, filtré sur ce qui n'est ni résolu ni rejeté. */
  goToMyTicketsEnCours(): void {
    this.router.navigate(['/client/my-tickets'], { queryParams: { statut: 'en-cours' } });
  }

  goToProfile(): void {
    this.router.navigate(['/client/profile']);
  }

  goToChangePassword(): void {
    this.router.navigate(['/auth/change-password']);
  }

  /** Ouvre le premier ticket à noter : le formulaire d'avis est sur sa fiche. */
  donnerAvis(): void {
    const premier = this.aNoter()[0];
    if (premier) this.goToDetail(premier.id);
  }

  goToDetail(id: number): void {
    this.router.navigate(['/client/tickets', id]);
  }

  categoryIcon(t: Ticket): string {
    const cat = t.categorie_finale || t.categorie_predite;
    return CATEGORY_ICONS[cat] ?? 'confirmation_number';
  }

  formatDateShort(iso: string): string {
    const d = dateTicket(iso);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  /** Durée écoulée, sans « il y a » : se lit à la suite de « en attente depuis ». */
  anciennete(iso: string): string {
    const min = Math.floor((Date.now() - dateTicket(iso).getTime()) / 60000);
    if (min < 60) return `${Math.max(1, min)} min`;
    const h = Math.floor(min / 60);
    if (h < 24) return `${h} h`;
    const j = Math.floor(h / 24);
    return j === 1 ? '1 jour' : `${j} jours`;
  }

  timeAgo(iso: string): string {
    const diffMs = Date.now() - dateTicket(iso).getTime();
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
