import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket, Statut, STATUT_CFG } from '../../../models/ticket.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  private ticketApi = inject(TicketApiService);

  tickets = signal<Ticket[]>([]);
  loading = signal(true);

  // --- Stats simples ---
  totalCount = computed(() => this.tickets().length);
  enAttenteCount = computed(() => this.tickets().filter(t => t.statut === 'Ouvert' as Statut || t.statut === 'En attente' as any).length);
  enCoursCount = computed(() => this.tickets().filter(t => t.statut === 'En cours').length);
  resoluCount = computed(() => this.tickets().filter(t => t.statut === 'Résolu').length);
  rejeteCount = computed(() => this.tickets().filter(t => (t.statut as any) === 'Rejeté').length);

  // ⚠️ Mock — confiance par ticket non encore exposée par /tickets/admin/all.
  // À remplacer une fois que le backend renvoie un champ `confidence` par ticket.
  avgConfidence = signal(56);
  aValiderCount = signal(3);
  revisionUrgenteCount = signal(2);

  // --- Chart "Distribution par statut" ---
  statutChartData = computed<ChartData<'bar'>>(() => {
    const counts: Record<string, number> = {};
    for (const t of this.tickets()) {
      counts[t.statut] = (counts[t.statut] || 0) + 1;
    }
    return {
      labels: Object.keys(counts),
      datasets: [{
        data: Object.values(counts),
        backgroundColor: '#2f6fb3',
        borderRadius: 4,
        barThickness: 32,
      }],
    };
  });

  // --- Chart "Distribution par catégorie" ---
  // ⚠️ Mock — la catégorie ML par ticket n'est pas encore dans `Ticket` (models/ticket.models.ts).
  // À remplacer une fois que /tickets/admin/all renvoie le champ `category`.
  categorieChartData: ChartData<'bar'> = {
    labels: ['Réseau', 'Microsoft', 'Sécurité'],
    datasets: [{
      data: [1, 3, 1],
      backgroundColor: '#f5821f',
      borderRadius: 4,
      barThickness: 32,
    }],
  };

  chartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, ticks: { stepSize: 1, color: '#6b7280' }, grid: { color: '#f1f2f5' } },
      x: { ticks: { color: '#6b7280' }, grid: { display: false } },
    },
  };

  ngOnInit(): void {
    this.loadTickets();
  }

  loadTickets(): void {
    this.loading.set(true);
    this.ticketApi.getAllTickets().subscribe({
      next: (data: Ticket[]) => {
        this.tickets.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}