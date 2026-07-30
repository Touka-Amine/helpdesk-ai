import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { AdminApiService } from '../../../api/admin-api.service';
import { AdminUser } from '../../../models/auth.models';
import {
  Ticket, Statut, STATUT_CFG,
  PRIORITE_OPTIONS, CLASSIFICATION_OPTIONS, CATEGORIE_OPTIONS, FILIALES,
} from '../../../models/ticket.models';

const DELETE_CONFIRM_WORD = 'SUPPRIMER';

@Component({
  selector: 'app-ticket-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-list.html',
  styleUrl: './ticket-list.css',
})
export class TicketList implements OnInit {
  private ticketApi = inject(TicketApiService);
  private adminApi  = inject(AdminApiService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);

  searchTerm = signal('');
  statutFilter = signal<Statut | ''>('');
  categorieFilter = signal<string>('');

  statutCfg = STATUT_CFG;
  prioriteOptions = PRIORITE_OPTIONS;
  classificationOptions = CLASSIFICATION_OPTIONS;
  categorieOptions = CATEGORIE_OPTIONS;
  filiales = FILIALES;

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

  deleteConfirmValid = computed(() => this.deleteConfirmText().trim().toUpperCase() === DELETE_CONFIRM_WORD);

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

  // ── Édition inline ───────────────────────────────────────────────────────────

  startEdit(t: Ticket, event: Event): void {
    event.stopPropagation();
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
        this.tickets.update(list => list.map(x => x.id === t.id ? {
          ...x,
          categorie_finale: this.editCategorie(),
          priorite_finale: this.editPriorite(),
          classification_finale: this.editClassification(),
          assigne_a: this.editAssigneA(),
          commentaire_interne: this.editCommentaire(),
        } : x));
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
    this.deleteTarget.set(t);
    this.deleteConfirmText.set('');
  }

  closeDeleteConfirm(): void {
    this.deleteTarget.set(null);
    this.deleteConfirmText.set('');
  }

  confirmDelete(): void {
    const t = this.deleteTarget();
    if (!t || !this.deleteConfirmValid()) return;
    this.deleting.set(true);
    this.ticketApi.deleteTicket(t.id).subscribe({
      next: () => {
        this.deleting.set(false);
        this.tickets.update(list => list.filter(x => x.id !== t.id));
        this.closeDeleteConfirm();
      },
      error: () => {
        this.deleting.set(false);
      },
    });
  }
}
