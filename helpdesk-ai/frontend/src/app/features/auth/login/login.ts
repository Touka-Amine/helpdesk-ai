import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthApiService } from '../../../api/auth-api.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  private fb      = inject(FormBuilder);
  private authApi = inject(AuthApiService);
  private auth    = inject(AuthService);
  private router  = inject(Router);

  loading      = signal(false);
  errorMsg     = signal<string | null>(null);
  showPassword = signal(false);

  togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  form = this.fb.group({
    email:    ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  submit(): void {
    this.errorMsg.set(null);
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    const { email, password } = this.form.value;
    this.loading.set(true);

    this.authApi.login(email!, password!).subscribe({
      next: (res) => {
        this.auth.setSession(res);
        this.loading.set(false);
        this.router.navigate(res.role === 'admin' ? ['/admin/dashboard'] : ['/client/my-tickets']);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(
          err.status === 401
            ? 'Email ou mot de passe incorrect.'
            : 'Erreur de connexion. Veuillez réessayer.',
        );
      },
    });
  }
}
