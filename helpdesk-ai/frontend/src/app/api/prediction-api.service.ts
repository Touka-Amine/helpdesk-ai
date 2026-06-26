import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { PredictTicketRequest, PredictionResult } from '../models/prediction.models';

@Injectable({ providedIn: 'root' })
export class PredictionApiService {
  constructor(private http: HttpClient) {}

  predict(payload: PredictTicketRequest) {
    return this.http.post<PredictionResult>(`${environment.apiUrl}/predict`, payload);
  }
}
