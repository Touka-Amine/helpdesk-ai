import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthApiService } from '../../../api/auth-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { AuthShell } from '../auth-shell/auth-shell';
import { ThemeToggle } from '../theme-toggle/theme-toggle';
import { ContactSupport } from '../contact-support/contact-support';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, AuthShell, ThemeToggle, ContactSupport],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login implements OnInit {
  private fb      = inject(FormBuilder);
  private authApi = inject(AuthApiService);
  private auth    = inject(AuthService);
  private router  = inject(Router);

  loading      = signal(false);
  errorMsg     = signal<string | null>(null);
  showPassword = signal(false);

  ngOnInit(): void {
    // Session deja valide (token present, pas de changement de mdp requis) :
    // on saute l'ecran de login et on redirige directement selon le role.
    if (this.auth.isAuthenticated() && !this.auth.needsPasswordChange()) {
      this.redirectByRole();
    }
  }

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
        if (res.first_login) {
          this.router.navigate(['/auth/change-password']);
        } else {
          this.redirectByRole();
        }
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

  private redirectByRole(): void {
    this.router.navigate(this.auth.isAdmin() ? ['/admin/dashboard'] : ['/client/my-tickets']);
  }
}
