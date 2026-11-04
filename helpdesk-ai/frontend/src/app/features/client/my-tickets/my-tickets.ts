import { Component, OnDestroy, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { relirePeriodiquement } from '../../../core/services/relecture';
import { Ticket, Statut, STATUT_CFG, dateTicket } from '../../../models/ticket.models';

/** Les 5 tickets les plus récents par page. */
const TAILLE_PAGE = 5;

@Component({
  selector: 'app-my-tickets',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './my-tickets.html',
  styleUrl: './my-tickets.css',
})
export class MyTickets implements OnInit, OnDestroy {
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  /** « En cours » regroupe tout ce qui n'est ni résolu ni rejeté. */
  statutFilter = signal<'Tous' | 'En cours' | Statut>('Tous');
  searchFilter = signal('');

  statutOptions: ('Tous' | 'En cours' | Statut)[] = ['Tous', 'En cours', ...(Object.keys(STATUT_CFG) as Statut[])];
  statutCfg = STATUT_CFG;

  filtered = computed(() => {
    let result = this.tickets();
    const statut = this.statutFilter();
    const search = this.searchFilter().toLowerCase().trim();

    if (statut === 'En cours') {
      result = result.filter((t) => t.statut !== 'Résolu' && t.statut !== 'Rejeté');
    } else if (statut !== 'Tous') {
      result = result.filter((t) => t.statut === statut);
    }
    if (search) {
      result = result.filter(
        (t) => t.titre.toLowerCase().includes(search) || String(t.id).includes(search)
      );
    }
    return [...result].sort(
      (a, b) => dateTicket(b.created_at).getTime() - dateTicket(a.created_at).getTime(),
    );
  });

  // ── Pagination, même logique que Tous les tickets ──────────────────────────
  page = signal(1);
  taillePage = TAILLE_PAGE;

  nbPages = computed(() => Math.max(1, Math.ceil(this.filtered().length / this.taillePage)));
  /** La page demandée, ramenée dans les bornes : une relecture qui réduit la
   *  liste ne doit pas laisser l'écran sur une page vide. */
  pageCourante = computed(() => Math.min(this.page(), this.nbPages()));
  pageTickets = computed(() => {
    const debut = (this.pageCourante() - 1) * this.taillePage;
    return this.filtered().slice(debut, debut + this.taillePage);
  });
  premierAffiche = computed(() => this.filtered().length === 0 ? 0 : (this.pageCourante() - 1) * this.taillePage + 1);
  dernierAffiche = computed(() => Math.min(this.pageCourante() * this.taillePage, this.filtered().length));

  /** Numéros de page affichés : les premiers, les derniers, et une ellipse entre
   *  les deux quand la liste est longue. */
  pagesAffichees = computed<(number | '…')[]>(() => {
    const total = this.nbPages();
    const courante = this.pageCourante();
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    const pages: (number | '…')[] = [];
    const proches = new Set([1, 2, total, courante - 1, courante, courante + 1]);
    for (let p = 1; p <= total; p++) {
      if (proches.has(p)) pages.push(p);
      else if (pages[pages.length - 1] !== '…') pages.push('…');
    }
    return pages;
  });

  allerPage(p: number | '…'): void {
    if (p === '…') return;
    this.page.set(Math.min(Math.max(1, p), this.nbPages()));
  }

  pagePrecedente(): void { this.allerPage(this.pageCourante() - 1); }
  pageSuivante(): void { this.allerPage(this.pageCourante() + 1); }

  /** Un nouveau filtre repart de la première page. */
  majRecherche(valeur: string): void {
    this.searchFilter.set(valeur);
    this.page.set(1);
  }

  majStatut(valeur: 'Tous' | 'En cours' | Statut): void {
    this.statutFilter.set(valeur);
    this.page.set(1);
  }

  totalCount = computed(() => this.tickets().length);
  enAttenteCount = computed(() => this.tickets().filter((t) => t.statut === 'En attente').length);
  resoluCount = computed(() => this.tickets().filter((t) => t.statut === 'Résolu').length);

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
      (acc, t) => acc + (new Date(t.date_resolution!).getTime() - new Date(t.created_at).getTime()),
      0
    );
    return Math.round(totalMs / resolus.length / 3600000);
  });

  private arreterRelecture?: () => void;

  ngOnInit(): void {
    // L'accueil ouvre la liste déjà filtrée (« Mes tickets en cours »).
    if (this.route.snapshot.queryParamMap.get('statut') === 'en-cours') this.statutFilter.set('En cours');
    this.loadTickets();
    // Les statuts de la liste suivent les decisions des techniciens sans recharger.
    this.arreterRelecture = relirePeriodiquement(() => this.loadTickets(true));
  }

  ngOnDestroy(): void {
    this.arreterRelecture?.();
  }

  /** `silencieux` : relecture de fond, sans voyant de chargement ni message
   *  d'erreur pour un echec passager ; la liste affichee reste en place. */
  loadTickets(silencieux = false): void {
    if (!silencieux) this.loading.set(true);
    this.ticketApi.getMyTickets().subscribe({
      next: (data: Ticket[]) => {
        this.tickets.set(data);
        this.error.set(null);
        this.loading.set(false);
      },
      error: () => {
        if (!silencieux) this.error.set('Impossible de charger vos tickets.');
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

  /** Date et heure, au même format que la colonne « Date création » de Tous les
   *  tickets. L'API renvoie l'heure UTC sans fuseau : `dateTicket` remet le Z,
   *  sinon l'heure affichée retarde d'une heure. */
  formatDateHeure(iso: string): string {
    const d = dateTicket(iso);
    const date = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    return `${date} ${d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`;
  }
}
