import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet, RouterModule, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { TicketApiService } from '../../api/ticket-api.service';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [RouterOutlet, RouterModule, CommonModule],
  templateUrl: './admin-layout.html',
  styleUrl: './admin-layout.css',
})
export class AdminLayout implements OnInit {
  private authService = inject(AuthService);
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);

  user = this.authService.currentUser();
  pendingCount = signal(0);

  ngOnInit(): void {
    this.ticketApi.getAllTickets().subscribe({
      next: (tickets) => this.pendingCount.set(tickets.filter(t => t.statut === 'En attente').length),
      error: () => {},
    });
  }

  initials(): string {
    const name = this.user?.prenom || this.user?.nom || this.user?.email || '?';
    return name.charAt(0).toUpperCase();
  }

  logout(): void {
    this.authService.logout();
  }
}
