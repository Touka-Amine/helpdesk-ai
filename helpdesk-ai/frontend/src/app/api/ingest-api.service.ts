import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

// Endpoint déclenché par le flux Power Automate (création de ticket par email),
// probablement jamais appelé depuis l'interface Angular elle-même.
// Présent ici pour la complétude du mapping API documenté dans spec-frontend-angular.md.
@Injectable({ providedIn: 'root' })
export class IngestApiService {
  constructor(private http: HttpClient) {}

  ingestFromEmail(payload: unknown) {
    return this.http.post(`${environment.apiUrl}/ingest`, payload);
  }
}
