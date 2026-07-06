import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import {
  AdminUser,
  AdminUserCreateRequest,
  AdminUserCreateResponse,
} from '../models/auth.models';

export interface ModelInfo {
  model_name: string;
  f1_macro_ml_seul: number;
  f1_macro_avec_heuristiques: number;
  accuracy_test: number;
  confidence_threshold: number;
  classes: string[];
  train_size: number;
  test_size: number;
  dataset_note: string;
  known_weaknesses: string[];
}

@Injectable({ providedIn: 'root' })
export class AdminApiService {
  private readonly base = `${environment.apiUrl}/admin`;

  constructor(private http: HttpClient) {}

  getUsers() {
    return this.http.get<AdminUser[]>(`${this.base}/users`);
  }

  createUser(payload: AdminUserCreateRequest) {
    return this.http.post<AdminUserCreateResponse>(`${this.base}/users`, payload);
  }

  updateUser(userId: number, payload: { role?: string; is_active?: boolean }) {
    return this.http.patch<AdminUser>(`${this.base}/users/${userId}`, payload);
  }

  getModelInfo() {
    return this.http.get<ModelInfo>(`${this.base}/model-info`);
  }
}
