import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthApiService } from '../../../api/auth-api.service';
import { AuthShell } from '../auth-shell/auth-shell';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, AuthShell],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.css',
})
export class ForgotPassword {
  private fb      = inject(FormBuilder);
  private authApi = inject(AuthApiService);

  loading  = signal(false);
  envoye   = signal(false);
  errorMsg = signal<string | null>(null);
  adresse  = signal('');

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
  });

  submit(): void {
    this.errorMsg.set(null);
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    const email = this.form.value.email!;
    this.loading.set(true);

    this.authApi.forgotPassword(email).subscribe({
      next: () => {
        this.loading.set(false);
        this.adresse.set(email);
        // Le serveur repond la meme chose que le compte existe ou non. L'ecran
        // de confirmation reprend cette prudence : il ne dit pas "envoye a vous",
        // sinon l'interface trahirait ce que l'API protege.
        this.envoye.set(true);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(
          err.status === 429
            ? 'Trop de demandes. Réessayez dans quinze minutes.'
            : 'Envoi impossible pour le moment. Réessayez dans un instant.',
        );
      },
    });
  }

  recommencer(): void {
    this.envoye.set(false);
    this.form.reset();
  }
}
