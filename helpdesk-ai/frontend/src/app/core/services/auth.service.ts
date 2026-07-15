import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthUser, LoginResponse } from '../../models/auth.models';

// Duree d'inactivite (sans mouvement souris/clavier) avant deconnexion automatique.
const INACTIVITY_TIMEOUT_MS = 20 * 60 * 1000;
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'];

@Injectable({ providedIn: 'root' })
export class AuthService {
  private router = inject(Router);
  private userSignal = signal<AuthUser | null>(this.readUserFromStorage());
  private inactivityTimer: ReturnType<typeof setTimeout> | null = null;
  private activityListenersAttached = false;

  constructor() {
    if (this.isAuthenticated()) {
      this.startInactivityWatch();
    }
  }

  setSession(response: LoginResponse): void {
    const user: AuthUser = {
      id: response.user_id,
      email: '',
      nom: response.nom,
      prenom: response.prenom,
      role: response.role,
      filiale: response.filiale,
      first_login: response.first_login,
    };
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user', JSON.stringify(user));
    this.userSignal.set(user);
    this.startInactivityWatch();
  }

  needsPasswordChange(): boolean {
    return !!this.currentUser()?.first_login;
  }

  logout(): void {
    this.stopInactivityWatch();
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    this.userSignal.set(null);
    this.router.navigate(['/auth/login']);
  }

  private startInactivityWatch(): void {
    if (this.activityListenersAttached) return;
    this.activityListenersAttached = true;
    ACTIVITY_EVENTS.forEach((evt) => document.addEventListener(evt, this.resetInactivityTimer, { passive: true }));
    this.resetInactivityTimer();
  }

  private stopInactivityWatch(): void {
    if (!this.activityListenersAttached) return;
    this.activityListenersAttached = false;
    ACTIVITY_EVENTS.forEach((evt) => document.removeEventListener(evt, this.resetInactivityTimer));
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
  }

  private resetInactivityTimer = (): void => {
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
    this.inactivityTimer = setTimeout(() => this.logout(), INACTIVITY_TIMEOUT_MS);
  };

  currentUser(): AuthUser | null {
    return this.userSignal();
  }

  updateLocalUser(patch: Partial<AuthUser>): void {
    const current = this.userSignal();
    if (!current) return;
    const updated = { ...current, ...patch };
    localStorage.setItem('user', JSON.stringify(updated));
    this.userSignal.set(updated);
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
