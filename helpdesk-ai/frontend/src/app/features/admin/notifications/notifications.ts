import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { AdminApiService } from '../../../api/admin-api.service';
import { Ticket } from '../../../models/ticket.models';
import { AdminUser } from '../../../models/auth.models';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notifications.html',
  styleUrl: './notifications.css',
})
export class Notifications implements OnInit {
  private ticketApi = inject(TicketApiService);
  private adminApi = inject(AdminApiService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  users = signal<AdminUser[]>([]);
  loading = signal(true);

  pendingTickets = computed(() =>
    this.tickets()
      .filter(t => t.statut === 'En attente')
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
  );

  longWaitingTickets = computed(() =>
    this.pendingTickets().filter(t => (Date.now() - new Date(t.created_at).getTime()) > 24 * 3_600_000)
  );

  recentFeedback = computed(() =>
    this.tickets()
      .filter(t => t.feedback_vote)
      .sort((a, b) => b.id - a.id)
      .slice(0, 5)
  );

  recentUsers = computed(() =>
    this.users()
      .filter(u => (Date.now() - new Date(u.created_at).getTime()) < 7 * 24 * 3_600_000)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  );

  ngOnInit(): void {
    this.loading.set(true);
    this.ticketApi.getAllTickets().subscribe({
      next: (data) => { this.tickets.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
    this.adminApi.getUsers().subscribe({
      next: (data) => this.users.set(data),
      error: () => {},
    });
  }

  timeAgo(iso: string): string {
    const diffMin = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (diffMin < 60) return `Il y a ${diffMin} min`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `Il y a ${diffH} h`;
    return `Il y a ${Math.round(diffH / 24)} j`;
  }

  goToTicket(id: number): void {
    this.router.navigate(['/admin/tickets', id]);
  }
}
