import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { LoginResponse, RegisterRequest, AuthUser } from '../models/auth.models';

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly base = `${environment.apiUrl}/auth`;

  constructor(private http: HttpClient) {}

  register(payload: RegisterRequest) {
    return this.http.post<AuthUser>(`${this.base}/register`, payload);
  }

  /** Le backend attend application/x-www-form-urlencoded avec champ "username" (OAuth2) */
  login(email: string, password: string) {
    const body = new HttpParams()
      .set('username', email)
      .set('password', password);
    return this.http.post<LoginResponse>(`${this.base}/login`, body.toString(), {
      headers: new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' }),
    });
  }

  getMe() {
    return this.http.get<AuthUser>(`${this.base}/me`);
  }

  updateMe(payload: { nom?: string; prenom?: string; filiale?: string }) {
    return this.http.patch<AuthUser>(`${this.base}/me`, payload);
  }

  /** Demande l'envoi d'un lien de reinitialisation. La reponse est la meme que
   *  l'adresse corresponde ou non a un compte : ne jamais en deduire l'existence
   *  du compte dans l'interface. */
  forgotPassword(email: string) {
    return this.http.post<{ message: string }>(`${this.base}/forgot-password`, { email });
  }

  /** Fixe un nouveau mot de passe a partir du jeton recu par courriel. */
  resetPassword(token: string, newPassword: string) {
    return this.http.post<{ message: string }>(`${this.base}/reset-password`, {
      token,
      new_password: newPassword,
    });
  }

  changePassword(payload: ChangePasswordRequest) {
    return this.http.post<{ message: string }>(`${this.base}/change-password`, payload);
  }
}
