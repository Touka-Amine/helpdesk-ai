import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthApiService } from '../../../api/auth-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { FILIALES } from '../../../models/ticket.models';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class Register {
  private fb      = inject(FormBuilder);
  private authApi = inject(AuthApiService);
  private auth    = inject(AuthService);
  private router  = inject(Router);

  loading  = signal(false);
  errorMsg = signal<string | null>(null);
  filiales = FILIALES;

  form = this.fb.group({
    nom:      ['', Validators.required],
    prenom:   ['', Validators.required],
    email:    ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    filiale:  [''],
  });

  submit(): void {
    this.errorMsg.set(null);
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    const v = this.form.value;
    this.loading.set(true);

    this.authApi.register({
      nom: v.nom!,
      prenom: v.prenom!,
      email: v.email!,
      password: v.password!,
      filiale: v.filiale ?? '',
    }).subscribe({
      next: () => {
        this.authApi.login(v.email!, v.password!).subscribe({
          next: (res) => {
            this.auth.setSession(res);
            this.loading.set(false);
            this.router.navigate(['/client/my-tickets']);
          },
          error: () => {
            this.loading.set(false);
            this.router.navigate(['/auth/login']);
          },
        });
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(
          err.status === 400
            ? 'Cette adresse e-mail est déjà utilisée.'
            : 'Erreur lors de la création du compte.',
        );
      },
    });
  }
}
