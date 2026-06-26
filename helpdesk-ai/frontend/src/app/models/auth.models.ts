// ⚠️ Champs déduits des routes Swagger (/auth/register, /auth/login) et de
// RESUME_PROJET_PFE.md — à corriger une fois api/schemas/auth_schemas.py
// ou /openapi.json consultés.

export type UserRole = 'client' | 'admin';

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string; // ⚠️ nom de champ à confirmer
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthUser {
  id: number;
  email: string;
  full_name?: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string; // ⚠️ à confirmer — FastAPI/OAuth2 utilise parfois "access_token" + "token_type"
  token_type?: string; // ⚠️ souvent "bearer"
  user: AuthUser;
}
