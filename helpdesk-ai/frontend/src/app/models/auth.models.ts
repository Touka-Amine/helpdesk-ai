export type UserRole = 'client' | 'admin' | 'system';

export interface RegisterRequest {
  nom: string;
  prenom: string;
  email: string;
  password: string;
  filiale?: string;
}

/** Le backend utilise OAuth2PasswordRequestForm — champ "username" (pas "email") */
export interface LoginRequest {
  username: string;
  password: string;
}

/** Correspond à UserOut du backend */
export interface AuthUser {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: UserRole;
  filiale: string;
}

/** Correspond à TokenOut du backend */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  nom: string;
  prenom: string;
  user_id: number;
  filiale: string;
}
