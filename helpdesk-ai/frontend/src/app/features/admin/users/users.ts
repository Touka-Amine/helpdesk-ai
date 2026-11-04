import { Component, OnDestroy, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AdminApiService } from '../../../api/admin-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { relirePeriodiquement } from '../../../core/services/relecture';
import { AdminUser } from '../../../models/auth.models';
import { FILIALES } from '../../../models/ticket.models';

/** Comptes affichés par page, les plus récents d'abord, comme dans Tous les tickets. */
const TAILLE_PAGE = 10;

/** Ce que la fenêtre du mot de passe provisoire affiche à la création d'un compte. */
interface MotDePasseProvisoire {
  nom: string;
  prenom: string;
  email: string;
  temp_password: string;
}

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './users.html',
  styleUrl: './users.css',
})
export class Users implements OnInit, OnDestroy {
  private adminApi = inject(AdminApiService);
  private auth = inject(AuthService);
  private fb = inject(FormBuilder);
  private router = inject(Router);

  currentUserId = this.auth.currentUser()?.id;
  filiales = FILIALES;

  users = signal<AdminUser[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  roleFilter = signal<'' | 'admin' | 'client'>('');

  showCreateForm = signal(false);
  creating = signal(false);
  createError = signal<string | null>(null);
  createdResult = signal<MotDePasseProvisoire | null>(null);

  /** Recherche par nom, prénom ou adresse. */
  recherche = signal('');
  page = signal(1);
  taillePage = TAILLE_PAGE;

  /** Modification du profil : le compte ouvert dans la fenêtre, s'il y en a un. */
  enEdition = signal<AdminUser | null>(null);
  enregistrement = signal(false);
  erreurEdition = signal<string | null>(null);

  /** La liste réduite par le rôle et par la recherche, la plus récente en tête. */
  filtered = computed(() => {
    const role = this.roleFilter();
    const q = this.recherche().toLowerCase().trim();
    return this.users()
      .filter(u => !role || u.role === role)
      .filter(u => !q
        || `${u.prenom} ${u.nom}`.toLowerCase().includes(q)
        || `${u.nom} ${u.prenom}`.toLowerCase().includes(q)
        || u.email.toLowerCase().includes(q))
      .sort((a, b) => b.id - a.id);
  });

  // ── Pagination, sur le modèle de Tous les tickets ─────────────────────────

  nbPages = computed(() => Math.max(1, Math.ceil(this.filtered().length / TAILLE_PAGE)));
  /** La page demandée, ramenée dans les bornes : un filtre qui réduit la liste ne
   *  doit pas laisser l'écran sur une page vide. */
  pageCourante = computed(() => Math.min(this.page(), this.nbPages()));
  pageUtilisateurs = computed(() => {
    const debut = (this.pageCourante() - 1) * TAILLE_PAGE;
    return this.filtered().slice(debut, debut + TAILLE_PAGE);
  });
  premierAffiche = computed(() => this.filtered().length === 0 ? 0 : (this.pageCourante() - 1) * TAILLE_PAGE + 1);
  dernierAffiche = computed(() => Math.min(this.pageCourante() * TAILLE_PAGE, this.filtered().length));

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

  chercher(valeur: string): void {
    this.recherche.set(valeur);
    this.page.set(1);
  }

  totalCount = computed(() => this.users().length);
  adminCount = computed(() => this.users().filter(u => u.role === 'admin').length);
  clientCount = computed(() => this.users().filter(u => u.role === 'client').length);

  form = this.fb.group({
    nom: ['', Validators.required],
    prenom: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    role: ['client', Validators.required],
    filiale: [''],
  });

  private arreterRelecture?: () => void;

  ngOnInit(): void {
    this.loadUsers();
    // Un compte cree par inscription ou par un collegue apparait sans recharger.
    this.arreterRelecture = relirePeriodiquement(() => this.loadUsers(true));
  }

  ngOnDestroy(): void {
    this.arreterRelecture?.();
  }

  /** `silencieux` : relecture de fond, sans voyant de chargement ni message
   *  d'erreur pour un echec passager ; la liste affichee reste en place. */
  loadUsers(silencieux = false): void {
    if (!silencieux) this.loading.set(true);
    this.adminApi.getUsers().subscribe({
      next: (data) => { this.users.set(data); this.error.set(null); this.loading.set(false); },
      error: () => {
        if (!silencieux) this.error.set('Impossible de charger les utilisateurs.');
        this.loading.set(false);
      },
    });
  }

  openCreateForm(): void {
    this.form.reset({ role: 'client', filiale: '' });
    this.createError.set(null);
    this.showCreateForm.set(true);
  }

  closeCreateForm(): void {
    this.showCreateForm.set(false);
  }

  submitCreate(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const v = this.form.value;
    this.creating.set(true);
    this.createError.set(null);
    this.adminApi.createUser({
      nom: v.nom!, prenom: v.prenom!, email: v.email!,
      role: v.role as 'admin' | 'client', filiale: v.filiale || '',
    }).subscribe({
      next: (res) => {
        this.creating.set(false);
        this.showCreateForm.set(false);
        this.createdResult.set({
          nom: res.user.nom, prenom: res.user.prenom, email: res.user.email,
          temp_password: res.temp_password,
        });
        this.loadUsers();
      },
      error: (err) => {
        this.creating.set(false);
        this.createError.set(err.status === 400 ? 'Cet email est déjà utilisé.' : 'Erreur lors de la création.');
      },
    });
  }

  closeCreatedResult(): void {
    this.createdResult.set(null);
  }

  // ── Modifier le profil ──────────────────────────────────────────────────

  editForm = this.fb.group({
    nom: ['', Validators.required],
    prenom: ['', Validators.required],
    filiale: [''],
  });

  ouvrirEdition(u: AdminUser): void {
    this.editForm.reset({ nom: u.nom, prenom: u.prenom, filiale: u.filiale || '' });
    this.erreurEdition.set(null);
    this.enEdition.set(u);
  }

  fermerEdition(): void {
    this.enEdition.set(null);
  }

  enregistrerEdition(): void {
    const u = this.enEdition();
    if (!u) return;
    if (this.editForm.invalid) { this.editForm.markAllAsTouched(); return; }
    const v = this.editForm.value;
    this.enregistrement.set(true);
    this.erreurEdition.set(null);
    this.adminApi.updateUser(u.id, {
      nom: (v.nom ?? '').trim(), prenom: (v.prenom ?? '').trim(), filiale: v.filiale ?? '',
    }).subscribe({
      next: (maj) => {
        this.enregistrement.set(false);
        this.users.update(list => list.map(x => x.id === maj.id ? maj : x));
        this.enEdition.set(null);
      },
      error: (err) => {
        this.enregistrement.set(false);
        this.erreurEdition.set(err.status === 422
          ? 'Le nom et le prénom ne peuvent pas être vides.'
          : 'Impossible d’enregistrer les modifications.');
      },
    });
  }

  // ── Mot de passe ────────────────────────────────────────────────────────

  /**
   * Chacun change son propre mot de passe, l'administrateur comme les autres :
   * aucun écran ne permet de choisir ou de réinitialiser celui d'un autre
   * compte. Le bouton n'existe que sur la ligne de l'administrateur connecté
   * et ouvre l'écran habituel, qui demande l'ancien mot de passe.
   */
  changerMonMotDePasse(): void {
    this.router.navigate(['/auth/change-password']);
  }

  toggleActive(u: AdminUser): void {
    this.adminApi.updateUser(u.id, { is_active: !u.is_active }).subscribe({
      next: (updated) => this.users.update(list => list.map(x => x.id === updated.id ? updated : x)),
      error: () => this.error.set("Impossible de modifier le statut de cet utilisateur."),
    });
  }

  toggleRole(u: AdminUser): void {
    const newRole = u.role === 'admin' ? 'client' : 'admin';
    this.adminApi.updateUser(u.id, { role: newRole }).subscribe({
      next: (updated) => this.users.update(list => list.map(x => x.id === updated.id ? updated : x)),
      error: () => this.error.set("Impossible de modifier le rôle de cet utilisateur."),
    });
  }
}
