import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export interface CurrentUser {
  id: number;
  email: string;
  role: 'client' | 'admin';
  nom?: string;
}

interface LoginResponse {
  access_token: string;
  user: CurrentUser;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private base = `${environment.apiUrl}/auth`;

  private userSignal = signal<CurrentUser | null>(this.readUserFromStorage());

  login(email: string, password: string) {
    return this.http.post<LoginResponse>(`${this.base}/login`, { email, password }).pipe(
      // on stocke dès la réception, via subscribe côté composant ou tap ici si tu importes 'tap'
    );
  }

  setSession(token: string, user: CurrentUser): void {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify(user));
    this.userSignal.set(user);
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    this.userSignal.set(null);
  }

  currentUser(): CurrentUser | null {
    return this.userSignal();
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private readUserFromStorage(): CurrentUser | null {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  }
}