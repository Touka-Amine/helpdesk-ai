import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import {
  Ticket,
  CreateTicketRequest,
  ApproveTicketRequest,
  AdminCreateTicketRequest,
  RagSynthesis,
  TicketHistoryEntry,
} from '../models/ticket.models';

// Note : Swagger confirme que les endpoints admin (approve, admin/all, history)
// sont sous /tickets/..., pas sous un routeur /admin/... séparé comme supposé
// initialement dans le mapping spec-frontend-angular.md. Un seul service couvre
// donc l'espace client ET l'espace admin pour les tickets.
@Injectable({ providedIn: 'root' })
export class TicketApiService {
  private readonly base = `${environment.apiUrl}/tickets`;

  constructor(private http: HttpClient) {}

  // --- Espace client ---
 createTicket(payload: CreateTicketRequest) {
  return this.http.post<Ticket>(`${this.base}/`, payload);
}



  getMyTickets() {
    return this.http.get<Ticket[]>(`${this.base}/me`);
  }

  getMyTicketDetail(ticketId: number) {
    return this.http.get<Ticket>(`${this.base}/${ticketId}`);
  }

  submitFeedback(ticketId: number, vote: 'up' | 'down', comment: string = '') {
    return this.http.post<Ticket>(`${this.base}/${ticketId}/feedback`, { vote, comment });
  }

  getSimilarTitles(ticketId: number) {
    return this.http.get<{ titres: string[] }>(`${this.base}/${ticketId}/similar-titles`);
  }

  // --- Espace admin ---
  getAllTickets() {
    return this.http.get<Ticket[]>(`${this.base}/admin/all`);
  }

  approveTicket(ticketId: number, payload: ApproveTicketRequest) {
    return this.http.patch<Ticket>(`${this.base}/${ticketId}/approve`, payload);
  }

  refreshRag(ticketId: number) {
    return this.http.post<Ticket>(`${this.base}/${ticketId}/refresh-rag`, {});
  }

  getTicketHistory(ticketId: number) {
    return this.http.get<TicketHistoryEntry[]>(`${this.base}/${ticketId}/history`);
  }

  adminCreateTicket(payload: AdminCreateTicketRequest) {
    return this.http.post<Ticket>(`${this.base}/admin-create`, payload);
  }

  deleteTicket(ticketId: number) {
    return this.http.delete<{ message: string; id: number }>(`${this.base}/${ticketId}`);
  }

  getRagSynthesis(ticketId: number) {
    return this.http.get<RagSynthesis>(`${this.base}/${ticketId}/rag-synthesis`);
  }
}
