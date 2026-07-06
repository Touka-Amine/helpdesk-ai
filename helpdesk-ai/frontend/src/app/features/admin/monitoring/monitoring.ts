import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { TicketApiService } from '../../../api/ticket-api.service';
import { AdminApiService, ModelInfo } from '../../../api/admin-api.service';
import { Ticket } from '../../../models/ticket.models';

const CONFIDENCE_THRESHOLD = 0.40;

@Component({
  selector: 'app-monitoring',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './monitoring.html',
  styleUrl: './monitoring.css',
})
export class Monitoring implements OnInit {
  private ticketApi = inject(TicketApiService);
  private adminApi = inject(AdminApiService);
  private router = inject(Router);

  tickets = signal<Ticket[]>([]);
  modelInfo = signal<ModelInfo | null>(null);
  loading = signal(true);

  ticketsAvecConfiance = computed(() => this.tickets().filter(t => t.confiance != null));

  confianceMoyenne = computed(() => {
    const list = this.ticketsAvecConfiance();
    if (!list.length) return null;
    return Math.round((list.reduce((a, t) => a + (t.confiance ?? 0), 0) / list.length) * 100);
  });

  tauxCorrectionManuelle = computed(() => {
    const withBoth = this.tickets().filter(t => t.categorie_predite && t.categorie_finale);
    if (!withBoth.length) return null;
    const corriges = withBoth.filter(t => t.categorie_finale !== t.categorie_predite).length;
    return Math.round((corriges / withBoth.length) * 100);
  });

  ticketsFaibleConfiance = computed(() =>
    this.ticketsAvecConfiance()
      .filter(t => (t.confiance ?? 1) < CONFIDENCE_THRESHOLD)
      .sort((a, b) => (a.confiance ?? 0) - (b.confiance ?? 0))
  );

  confianceParCategorie = computed<ChartData<'bar'>>(() => {
    const sums: Record<string, { total: number; count: number }> = {};
    for (const t of this.ticketsAvecConfiance()) {
      const cat = t.categorie_finale || t.categorie_predite || 'Non classé';
      if (!sums[cat]) sums[cat] = { total: 0, count: 0 };
      sums[cat].total += (t.confiance ?? 0) * 100;
      sums[cat].count++;
    }
    const labels = Object.keys(sums);
    return {
      labels,
      datasets: [{
        data: labels.map(l => Math.round(sums[l].total / sums[l].count)),
        backgroundColor: labels.map(l => (sums[l].total / sums[l].count) < 40 ? '#dc2626' : '#4f46e5'),
        borderRadius: 4,
      }],
    };
  });

  chartOptionsBar: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, max: 100, ticks: { callback: (v) => `${v}%` } },
      x: { grid: { display: false } },
    },
  };

  ngOnInit(): void {
    this.loading.set(true);
    this.ticketApi.getAllTickets().subscribe({
      next: (data) => { this.tickets.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
    this.adminApi.getModelInfo().subscribe({
      next: (info) => this.modelInfo.set(info),
      error: () => {},
    });
  }

  confPct(c: number | null): number {
    return c != null ? Math.round(c * 100) : 0;
  }

  goToTicket(id: number): void {
    this.router.navigate(['/admin/tickets', id]);
  }
}
