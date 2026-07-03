import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthUser, LoginResponse } from '../../models/auth.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private router = inject(Router);
  private userSignal = signal<AuthUser | null>(this.readUserFromStorage());

  setSession(response: LoginResponse): void {
    const user: AuthUser = {
      id: response.user_id,
      email: '',
      nom: response.nom,
      prenom: response.prenom,
      role: response.role,
      filiale: response.filiale,
    };
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user', JSON.stringify(user));
    this.userSignal.set(user);
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    this.userSignal.set(null);
    this.router.navigate(['/auth/login']);
  }

  currentUser(): AuthUser | null {
    return this.userSignal();
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  isAdmin(): boolean {
    return this.currentUser()?.role === 'admin';
  }

  private readUserFromStorage(): AuthUser | null {
    try {
      const raw = localStorage.getItem('user');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
}
