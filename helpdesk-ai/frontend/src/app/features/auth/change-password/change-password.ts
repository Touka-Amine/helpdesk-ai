import { Component, inject, signal } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthApiService } from '../../../api/auth-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { AuthShell } from '../auth-shell/auth-shell';
import { ThemeToggle } from '../theme-toggle/theme-toggle';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, AuthShell, ThemeToggle],
  templateUrl: './change-password.html',
  styleUrl: './change-password.css',
})
export class ChangePassword {
  private fb      = inject(FormBuilder);
  private authApi = inject(AuthApiService);
  private auth    = inject(AuthService);
  private router  = inject(Router);
  private location = inject(Location);

  loading  = signal(false);
  errorMsg = signal<string | null>(null);
  firstLogin = this.auth.needsPasswordChange();

  form = this.fb.group({
    current_password: ['', Validators.required],
    new_password:      ['', [Validators.required, Validators.minLength(6)]],
    confirm_password:  ['', Validators.required],
  });

  submit(): void {
    this.errorMsg.set(null);
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    const v = this.form.value;
    if (v.new_password !== v.confirm_password) {
      this.errorMsg.set('Les deux mots de passe ne correspondent pas.');
      return;
    }

    this.loading.set(true);
    this.authApi.changePassword({
      current_password: v.current_password!,
      new_password: v.new_password!,
    }).subscribe({
      next: () => {
        this.loading.set(false);
        this.auth.updateLocalUser({ first_login: false });
        this.router.navigate([this.auth.isAdmin() ? '/admin/dashboard' : '/client/my-tickets']);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(
          err.status === 400
            ? 'Mot de passe actuel incorrect.'
            : 'Erreur lors de la mise à jour. Veuillez réessayer.',
        );
      },
    });
  }

  /** Retour à l'écran précédent ; à défaut d'historique, à l'accueil du rôle. */
  annuler(): void {
    if (window.history.length > 1) {
      this.location.back();
    } else {
      this.router.navigate([this.auth.isAdmin() ? '/admin/dashboard' : '/client/my-tickets']);
    }
  }
}
