import { Component, OnDestroy, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TicketApiService } from '../../../api/ticket-api.service';
import { TicketsStore } from '../../../core/services/tickets-store';
import { AdminApiService } from '../../../api/admin-api.service';
import { AdminUser } from '../../../models/auth.models';
import {
  Ticket, couleurConfiance, Statut, STATUT_CFG, categorieCfg, prioriteCfg,
  PRIORITE_OPTIONS, CLASSIFICATION_OPTIONS, CATEGORIE_OPTIONS, FILIALES, dateTicket,
} from '../../../models/ticket.models';

const DELETE_CONFIRM_WORD = 'SUPPRIMER';

/** Colonnes sur lesquelles le tableau peut être trié. */
type CleTri = 'id' | 'titre' | 'categorie' | 'priorite' | 'statut' | 'confiance' | 'created_at' | 'demandeur';

const TAILLE_PAGE = 10;

@Component({
  selector: 'app-ticket-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-list.html',
  styleUrl: './ticket-list.css',
})
export class TicketList implements OnInit, OnDestroy {
  private ticketApi = inject(TicketApiService);
  private adminApi  = inject(AdminApiService);
  private router = inject(Router);
  private store = inject(TicketsStore);

  /** La liste vient du magasin partage, relu toutes les quinze secondes : un
   *  ticket depose par un client apparait sans recharger la page. */
  tickets = this.store.tickets;
  loading = this.store.chargement;
  derniereMaj = this.store.derniereMaj;
  /** Erreur d'une action. Les erreurs de chargement viennent du magasin. */
  erreur = signal<string | null>(null);

  searchTerm = signal('');
  statutFilter = signal<Statut | ''>('');
  categorieFilter = signal<string>('');
  /** Le panneau de filtres s'ouvre sous son bouton, comme sur la maquette. */
  filtresOuverts = signal(false);

  statutCfg = STATUT_CFG;
  cfgCategorie = categorieCfg;
  cfgPriorite = prioriteCfg;
  prioriteOptions = PRIORITE_OPTIONS;
  classificationOptions = CLASSIFICATION_OPTIONS;
  categorieOptions = CATEGORIE_OPTIONS;
  filiales = FILIALES;
  statutOptions: Statut[] = ['En attente', 'Prise en Charge', 'Résolu', 'Rejeté', 'Problème'];

  // ── Tri, pagination, sélection ──────────────────────────────────────────────
  triCle = signal<CleTri>('id');
  triSens = signal<1 | -1>(-1);
  page = signal(1);
  taillePage = TAILLE_PAGE;
  selection = signal<ReadonlySet<number>>(new Set<number>());
  /** Ticket dont le menu « … » est déroulé, et l'endroit où le poser. Le menu est
   *  rendu hors du tableau : le conteneur de la grille défile horizontalement et
   *  rognerait un menu posé dans une cellule. */
  menuOuvert = signal<number | null>(null);
  menuPos = signal<{ x: number; y: number } | null>(null);
  /** Ticket dont une décision rapide est en cours d'envoi. */
  decisionEnCours = signal<number | null>(null);

  // ── Édition inline (Tâche 2.3) ──────────────────────────────────────────────
  editingId = signal<number | null>(null);
  editCategorie = signal('');
  editPriorite = signal('');
  editClassification = signal('');
  editAssigneA = signal('');
  editCommentaire = signal('');
  savingEdit = signal(false);

  // ── Création depuis le tableau (Tâche 2.4) ──────────────────────────────────
  showCreateModal = signal(false);
  creating = signal(false);
  createError = signal<string | null>(null);
  clients = signal<AdminUser[]>([]);
  demandeurMode = signal<'existing' | 'free'>('existing');
  newTitre = signal('');
  newDescription = signal('');
  newPriorite = signal(PRIORITE_OPTIONS[0]);
  newFiliale = signal(FILIALES[0]);
  newEquipement = signal('');
  newDemandeurUserId = signal<number | null>(null);
  newDemandeurNom = signal('');
  newDemandeurPrenom = signal('');
  newDemandeurEmail = signal('');

  // ── Suppression sécurisée (Tâche 2.4) ───────────────────────────────────────
  deleteTarget = signal<Ticket | null>(null);
  /** Suppression de la sélection : même confirmation, plusieurs tickets. */
  deleteSelection = signal(false);
  deleteConfirmText = signal('');
  deleting = signal(false);
  deleteConfirmWord = DELETE_CONFIRM_WORD;

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

  triees = computed(() => {
    const cle = this.triCle();
    const sens = this.triSens();
    return [...this.filtered()].sort((a, b) => {
      const va = this.valeurTri(a, cle);
      const vb = this.valeurTri(b, cle);
      if (va < vb) return -1 * sens;
      if (va > vb) return 1 * sens;
      return 0;
    });
  });

  nbPages = computed(() => Math.max(1, Math.ceil(this.triees().length / this.taillePage)));
  /** La page demandée, ramenée dans les bornes : un filtre qui réduit la liste ne
   *  doit pas laisser l'écran sur une page vide. */
  pageCourante = computed(() => Math.min(this.page(), this.nbPages()));
  pageTickets = computed(() => {
    const debut = (this.pageCourante() - 1) * this.taillePage;
    return this.triees().slice(debut, debut + this.taillePage);
  });
  premierAffiche = computed(() => this.triees().length === 0 ? 0 : (this.pageCourante() - 1) * this.taillePage + 1);
  dernierAffiche = computed(() => Math.min(this.pageCourante() * this.taillePage, this.triees().length));

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

  toutesCochees = computed(() => {
    const page = this.pageTickets();
    return page.length > 0 && page.every(t => this.selection().has(t.id));
  });

  nbFiltresActifs = computed(() => (this.statutFilter() ? 1 : 0) + (this.categorieFilter() ? 1 : 0));

  messageErreur = computed(() => this.erreur() ?? this.store.erreur());

  /** Le ticket dont le menu « … » est ouvert, s'il est toujours affiché. */
  menuTicket = computed(() => this.pageTickets().find(t => t.id === this.menuOuvert()) ?? null);

  totalCount = computed(() => this.tickets().length);
  enAttenteCount = computed(() => this.tickets().filter(t => t.statut === 'En attente').length);
  validesCount = computed(() => this.tickets().filter(t => t.statut === 'Prise en Charge' || t.statut === 'Résolu').length);
  rejetesCount = computed(() => this.tickets().filter(t => t.statut === 'Rejeté').length);

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

  deleteConfirmValid = computed(() => this.deleteConfirmText().trim().toUpperCase() === DELETE_CONFIRM_WORD);

  private detacher?: () => void;

  ngOnInit(): void {
    this.detacher = this.store.suivre();
  }

  ngOnDestroy(): void {
    this.detacher?.();
  }

  /** Relecture immediate, sans attendre le tour de sondage suivant. */
  loadTickets(): void {
    this.erreur.set(null);
    this.store.rafraichir();
  }

  heureMaj(): string {
    return this.store.libelleMaj();
  }

  // ── Lecture d'une ligne ─────────────────────────────────────────────────────

  categorie(t: Ticket): string {
    return t.categorie_finale || t.categorie_predite || '';
  }

  priorite(t: Ticket): string {
    return t.priorite_finale || t.priorite_predite || '';
  }

  reference(t: Ticket): string {
    return `#${t.id.toString().padStart(4, '0')}`;
  }

  confPct(c: number | null): number {
    return c != null ? Math.round(c * 100) : 0;
  }

  confianceColor(c: number | null): string {
    return couleurConfiance(c);
  }

  /** Date et heure, comme dans la colonne « Date création » de la maquette.
   *  L'API renvoie l'heure UTC sans fuseau : `dateTicket` remet le Z. */
  formatDateHeure(iso: string): string {
    const d = dateTicket(iso);
    const date = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    return `${date} ${d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`;
  }

  // ── Tri ──────────────────────────────────────────────────────────────────────

  private valeurTri(t: Ticket, cle: CleTri): string | number {
    switch (cle) {
      case 'id':         return t.id;
      case 'titre':      return t.titre.toLowerCase();
      case 'categorie':  return this.categorie(t).toLowerCase();
      // L'ordre des priorités est celui de la liste de référence, pas l'alphabet.
      case 'priorite':   return PRIORITE_OPTIONS.indexOf(this.priorite(t));
      case 'statut':     return t.statut;
      case 'confiance':  return t.confiance ?? -1;
      case 'created_at': return new Date(t.created_at).getTime();
      case 'demandeur':  return (t.demandeur_nom || '').toLowerCase();
    }
  }

  trier(cle: CleTri): void {
    if (this.triCle() === cle) {
      this.triSens.update(s => (s === 1 ? -1 : 1));
    } else {
      this.triCle.set(cle);
      this.triSens.set(1);
    }
    this.page.set(1);
  }

  iconeTri(cle: CleTri): string {
    if (this.triCle() !== cle) return 'unfold_more';
    return this.triSens() === 1 ? 'arrow_upward' : 'arrow_downward';
  }

  // ── Pagination ───────────────────────────────────────────────────────────────

  allerPage(p: number | '…'): void {
    if (p === '…') return;
    this.page.set(Math.min(Math.max(1, p), this.nbPages()));
    this.menuOuvert.set(null);
  }

  pagePrecedente(): void { this.allerPage(this.pageCourante() - 1); }
  pageSuivante(): void { this.allerPage(this.pageCourante() + 1); }

  // ── Sélection ────────────────────────────────────────────────────────────────

  estCochee(id: number): boolean {
    return this.selection().has(id);
  }

  cocher(t: Ticket, event: Event): void {
    event.stopPropagation();
    this.selection.update(s => {
      const copie = new Set(s);
      if (copie.has(t.id)) copie.delete(t.id); else copie.add(t.id);
      return copie;
    });
  }

  /** Coche ou décoche les tickets de la page affichée. */
  cocherPage(event: Event): void {
    event.stopPropagation();
    const page = this.pageTickets();
    const tout = this.toutesCochees();
    this.selection.update(s => {
      const copie = new Set(s);
      for (const t of page) {
        if (tout) copie.delete(t.id); else copie.add(t.id);
      }
      return copie;
    });
  }

  viderSelection(): void {
    this.selection.set(new Set<number>());
  }

  // ── Filtres ──────────────────────────────────────────────────────────────────

  majRecherche(v: string): void {
    this.searchTerm.set(v);
    this.page.set(1);
  }

  majStatut(v: Statut | ''): void {
    this.statutFilter.set(v);
    this.page.set(1);
  }

  majCategorie(v: string): void {
    this.categorieFilter.set(v);
    this.page.set(1);
  }

  resetFilters(): void {
    this.searchTerm.set('');
    this.statutFilter.set('');
    this.categorieFilter.set('');
    this.page.set(1);
  }

  goToDetail(id: number): void {
    this.router.navigate(['/admin/tickets', id]);
  }

  // ── Décisions rapides depuis la ligne ────────────────────────────────────────

  /** Les deux seules transitions permises depuis « En attente » (voir
   *  STATUS_TRANSITIONS côté API) : c'est pourquoi ces boutons n'apparaissent
   *  que sur les lignes en attente. */
  validerRapide(t: Ticket, event: Event): void {
    this.changerStatut(t, 'Prise en Charge', event);
  }

  rejeterRapide(t: Ticket, event: Event): void {
    this.changerStatut(t, 'Rejeté', event);
  }

  private changerStatut(t: Ticket, statut: Statut, event: Event): void {
    event.stopPropagation();
    this.menuOuvert.set(null);
    this.decisionEnCours.set(t.id);
    this.erreur.set(null);
    this.ticketApi.approveTicket(t.id, { statut }).subscribe({
      next: () => {
        this.decisionEnCours.set(null);
        this.store.majTicket(t.id, { statut });
      },
      error: () => {
        this.decisionEnCours.set(null);
        this.erreur.set(`Impossible de passer le ticket #${t.id} au statut « ${statut} ».`);
      },
    });
  }

  basculerMenu(t: Ticket, event: Event): void {
    event.stopPropagation();
    const bouton = event.currentTarget as HTMLElement | null;
    if (bouton) {
      const r = bouton.getBoundingClientRect();
      // Le menu fait 176 px (w-44) : on l'aligne sur le bord droit du bouton.
      this.menuPos.set({ x: Math.max(8, r.right - 176), y: r.bottom + 4 });
    }
    this.menuOuvert.update(id => (id === t.id ? null : t.id));
  }

  fermerMenu(): void {
    this.menuOuvert.set(null);
  }

  // ── Édition inline ───────────────────────────────────────────────────────────

  startEdit(t: Ticket, event: Event): void {
    event.stopPropagation();
    this.menuOuvert.set(null);
    this.editingId.set(t.id);
    this.editCategorie.set(t.categorie_finale || t.categorie_predite || '');
    this.editPriorite.set(t.priorite_finale || t.priorite_predite || '');
    this.editClassification.set(t.classification_finale || t.classification_predite || '');
    this.editAssigneA.set(t.assigne_a || '');
    this.editCommentaire.set(t.commentaire_interne || '');
  }

  cancelEdit(event: Event): void {
    event.stopPropagation();
    this.editingId.set(null);
  }

  saveEdit(t: Ticket, event: Event): void {
    event.stopPropagation();
    this.savingEdit.set(true);
    this.ticketApi.approveTicket(t.id, {
      statut: t.statut,
      categorie_finale: this.editCategorie(),
      priorite_finale: this.editPriorite(),
      classification_finale: this.editClassification(),
      assigne_a: this.editAssigneA(),
      commentaire_interne: this.editCommentaire(),
    }).subscribe({
      next: () => {
        this.savingEdit.set(false);
        this.editingId.set(null);
        this.store.majTicket(t.id, {
          categorie_finale: this.editCategorie(),
          priorite_finale: this.editPriorite(),
          classification_finale: this.editClassification(),
          assigne_a: this.editAssigneA(),
          commentaire_interne: this.editCommentaire(),
        });
      },
      error: () => {
        this.savingEdit.set(false);
      },
    });
  }

  // ── Création depuis le tableau ────────────────────────────────────────────────

  openCreateModal(): void {
    this.createError.set(null);
    this.demandeurMode.set('existing');
    this.newTitre.set('');
    this.newDescription.set('');
    this.newPriorite.set(PRIORITE_OPTIONS[0]);
    this.newFiliale.set(FILIALES[0]);
    this.newEquipement.set('');
    this.newDemandeurUserId.set(null);
    this.newDemandeurNom.set('');
    this.newDemandeurPrenom.set('');
    this.newDemandeurEmail.set('');
    this.showCreateModal.set(true);
    if (!this.clients().length) {
      this.adminApi.getUsers().subscribe({
        next: (users) => this.clients.set(users.filter(u => u.role === 'client')),
        error: () => {},
      });
    }
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
  }

  submitCreate(): void {
    this.createError.set(null);
    if (this.newTitre().trim().length < 5 || this.newDescription().trim().length < 10) {
      this.createError.set('Titre (5 caractères min.) et description (10 caractères min.) requis.');
      return;
    }
    const mode = this.demandeurMode();
    if (mode === 'existing' && !this.newDemandeurUserId()) {
      this.createError.set('Sélectionnez un client existant.');
      return;
    }
    if (mode === 'free' && (!this.newDemandeurNom().trim() || !this.newDemandeurPrenom().trim() || !this.newDemandeurEmail().trim())) {
      this.createError.set('Nom, prénom et email du demandeur sont requis.');
      return;
    }

    this.creating.set(true);
    this.ticketApi.adminCreateTicket({
      titre: this.newTitre().trim(),
      description: this.newDescription().trim(),
      priorite: this.newPriorite(),
      filiale: this.newFiliale(),
      equipement: this.newEquipement().trim(),
      demandeur_user_id: mode === 'existing' ? this.newDemandeurUserId()! : undefined,
      demandeur_nom: mode === 'free' ? this.newDemandeurNom().trim() : undefined,
      demandeur_prenom: mode === 'free' ? this.newDemandeurPrenom().trim() : undefined,
      demandeur_email: mode === 'free' ? this.newDemandeurEmail().trim() : undefined,
    }).subscribe({
      next: () => {
        this.creating.set(false);
        this.showCreateModal.set(false);
        this.loadTickets();
      },
      error: (err) => {
        this.creating.set(false);
        this.createError.set(err.error?.detail ?? 'Erreur lors de la création du ticket.');
      },
    });
  }

  // ── Suppression sécurisée ─────────────────────────────────────────────────────

  openDeleteConfirm(t: Ticket, event: Event): void {
    event.stopPropagation();
    this.menuOuvert.set(null);
    this.deleteSelection.set(false);
    this.deleteTarget.set(t);
    this.deleteConfirmText.set('');
  }

  openDeleteSelection(): void {
    if (this.selection().size === 0) return;
    this.deleteTarget.set(null);
    this.deleteSelection.set(true);
    this.deleteConfirmText.set('');
  }

  closeDeleteConfirm(): void {
    this.deleteTarget.set(null);
    this.deleteSelection.set(false);
    this.deleteConfirmText.set('');
  }

  confirmDelete(): void {
    if (!this.deleteConfirmValid()) return;

    if (this.deleteSelection()) {
      const ids = Array.from(this.selection());
      if (!ids.length) return;
      this.deleting.set(true);
      forkJoin(ids.map(id => this.ticketApi.deleteTicket(id))).subscribe({
        next: () => {
          this.deleting.set(false);
          this.store.retirer(ids);
          this.viderSelection();
          this.closeDeleteConfirm();
        },
        error: () => {
          this.deleting.set(false);
          this.erreur.set('Une partie de la sélection n\'a pas pu être supprimée.');
          this.loadTickets();
        },
      });
      return;
    }

    const t = this.deleteTarget();
    if (!t) return;
    this.deleting.set(true);
    this.ticketApi.deleteTicket(t.id).subscribe({
      next: () => {
        this.deleting.set(false);
        this.store.retirer([t.id]);
        this.selection.update(s => {
          const copie = new Set(s);
          copie.delete(t.id);
          return copie;
        });
        this.closeDeleteConfirm();
      },
      error: () => {
        this.deleting.set(false);
      },
    });
  }
}
