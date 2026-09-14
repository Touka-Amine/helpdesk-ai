import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AuthApiService } from '../../../api/auth-api.service';
import { AuthShell } from '../auth-shell/auth-shell';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, AuthShell],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.css',
})
export class ResetPassword {
  private fb      = inject(FormBuilder);
  private authApi = inject(AuthApiService);
  private route   = inject(ActivatedRoute);

  /** Jeton porte par le lien recu par courriel. */
  private token = this.route.snapshot.queryParamMap.get('token') ?? '';

  lienAbsent   = signal(this.token.length === 0);
  loading      = signal(false);
  reussi       = signal(false);
  errorMsg     = signal<string | null>(null);
  showPassword = signal(false);

  form = this.fb.group({
    new_password:     ['', [Validators.required, Validators.minLength(6)]],
    confirm_password: ['', Validators.required],
  });

  togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  submit(): void {
    this.errorMsg.set(null);
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    const v = this.form.value;
    if (v.new_password !== v.confirm_password) {
      this.errorMsg.set('Les deux mots de passe ne correspondent pas.');
      return;
    }

    this.loading.set(true);
    this.authApi.resetPassword(this.token, v.new_password!).subscribe({
      next: () => {
        this.loading.set(false);
        this.reussi.set(true);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(
          err.status === 400
            ? 'Ce lien est invalide ou a expiré. Refaites une demande depuis la page de connexion.'
            : 'Mise à jour impossible pour le moment. Réessayez dans un instant.',
        );
      },
    });
  }
}
