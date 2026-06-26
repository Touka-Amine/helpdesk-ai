import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { CategoriesResponse } from '../models/metadata.models';

@Injectable({ providedIn: 'root' })
export class MetadataApiService {
  constructor(private http: HttpClient) {}

  getCategories() {
    return this.http.get<CategoriesResponse>(`${environment.apiUrl}/categories`);
  }
}
