import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule, FormBuilder, Validators } from '@angular/forms';
import { AdminApiService } from '../../../api/admin-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { AdminUser } from '../../../models/auth.models';
import { FILIALES } from '../../../models/ticket.models';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './users.html',
  styleUrl: './users.css',
})
export class Users implements OnInit {
  private adminApi = inject(AdminApiService);
  private auth = inject(AuthService);
  private fb = inject(FormBuilder);

  currentUserId = this.auth.currentUser()?.id;
  filiales = FILIALES;

  users = signal<AdminUser[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  roleFilter = signal<'' | 'admin' | 'client'>('');

  showCreateForm = signal(false);
  creating = signal(false);
  createError = signal<string | null>(null);
  createdResult = signal<{ nom: string; prenom: string; email: string; temp_password: string } | null>(null);

  filtered = computed(() => {
    const role = this.roleFilter();
    return this.users().filter(u => !role || u.role === role);
  });

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

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading.set(true);
    this.adminApi.getUsers().subscribe({
      next: (data) => { this.users.set(data); this.loading.set(false); },
      error: () => { this.error.set('Impossible de charger les utilisateurs.'); this.loading.set(false); },
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
