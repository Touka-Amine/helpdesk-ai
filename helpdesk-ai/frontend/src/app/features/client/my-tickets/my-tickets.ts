import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket, Statut, STATUT_CFG } from '../../../models/ticket.models';

@Component({
  selector: 'app-my-tickets',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './my-tickets.html',
  styleUrl: './my-tickets.css',
})
export class MyTickets implements OnInit {
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  statutFilter = signal<'Tous' | Statut>('Tous');
  searchFilter = signal('');

  statutOptions: ('Tous' | Statut)[] = ['Tous', ...(Object.keys(STATUT_CFG) as Statut[])];
  statutCfg = STATUT_CFG;

  filtered = computed(() => {
    let result = this.tickets();
    const statut = this.statutFilter();
    const search = this.searchFilter().toLowerCase().trim();

    if (statut !== 'Tous') {
      result = result.filter((t) => t.statut === statut);
    }
    if (search) {
      result = result.filter(
        (t) => t.titre.toLowerCase().includes(search) || String(t.id).includes(search)
      );
    }
    return result;
  });

  ngOnInit(): void {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading.set(true);
    this.ticketApi.getMyTickets().subscribe({
      next: (data: Ticket[]) => {
        this.tickets.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Impossible de charger vos tickets.');
        this.loading.set(false);
      },
    });
  }

  goToNewTicket(): void {
    this.router.navigate(['/client/new-ticket']);
  }

  goToDetail(id: number): void {
    this.router.navigate(['/client/tickets', id]);
  }

  formatDateShort(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }
}