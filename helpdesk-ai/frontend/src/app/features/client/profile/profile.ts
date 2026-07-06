import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthApiService } from '../../../api/auth-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { FILIALES } from '../../../models/ticket.models';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class Profile implements OnInit {
  private authApi = inject(AuthApiService);
  private authService = inject(AuthService);
  private fb = inject(FormBuilder);

  filiales = FILIALES;
  loading = signal(true);
  saving = signal(false);
  saveMsg = signal<string | null>(null);
  email = signal('');

  form = this.fb.group({
    nom: ['', Validators.required],
    prenom: ['', Validators.required],
    filiale: [''],
  });

  ngOnInit(): void {
    this.authApi.getMe().subscribe({
      next: (u) => {
        this.form.patchValue({ nom: u.nom, prenom: u.prenom, filiale: u.filiale });
        this.email.set(u.email);
        this.loading.set(false);
      },
      error: () => {
        const cached = this.authService.currentUser();
        if (cached) {
          this.form.patchValue({ nom: cached.nom, prenom: cached.prenom, filiale: cached.filiale });
        }
        this.loading.set(false);
      },
    });
  }

  initials(): string {
    const v = this.form.get('prenom')?.value || this.form.get('nom')?.value || '?';
    return v.charAt(0).toUpperCase();
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    this.saveMsg.set(null);
    const v = this.form.value;
    this.authApi.updateMe({ nom: v.nom!, prenom: v.prenom!, filiale: v.filiale ?? '' }).subscribe({
      next: (u) => {
        this.authService.updateLocalUser({ nom: u.nom, prenom: u.prenom, filiale: u.filiale });
        this.saving.set(false);
        this.saveMsg.set('Modifications enregistrées.');
      },
      error: () => {
        this.saving.set(false);
        this.saveMsg.set("Erreur lors de l'enregistrement.");
      },
    });
  }
}
