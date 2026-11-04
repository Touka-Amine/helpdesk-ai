import { Component, OnDestroy, OnInit, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { TicketsStore } from '../../../core/services/tickets-store';
import { ThemeService } from '../../../core/services/theme.service';
import { COULEURS_STATUT, STATUT_CFG, Statut, dateTicket } from '../../../models/ticket.models';

/** Une part de l'anneau des statuts, telle que la légende l'affiche. */
export interface PartStatut { statut: Statut; libelle: string; n: number; pct: number; couleur: string }

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit, OnDestroy {
  private store = inject(TicketsStore);
  private router = inject(Router);
  private theme = inject(ThemeService);

  /** La liste vient du magasin partagé, relu toutes les quinze secondes : un
   *  ticket déposé par un client apparaît sur le tableau de bord sans recharger. */
  tickets = this.store.tickets;
  loading = this.store.chargement;
  private detacher?: () => void;

  /** Teintes des statuts, les mêmes que dans « Tous les tickets » : un compteur
   *  « En attente » a la même icône et la même couleur partout. */
  statutCfg = STATUT_CFG;

  totalCount = computed(() => this.tickets().length);
  enAttenteCount = computed(() => this.tickets().filter(t => t.statut === 'En attente').length);
  resoluCount = computed(() => this.tickets().filter(t => t.statut === 'Résolu').length);

  confianceMoyenne = computed(() => {
    const withConf = this.tickets().filter(t => t.confiance != null);
    if (!withConf.length) return null;
    const sum = withConf.reduce((acc, t) => acc + (t.confiance ?? 0), 0);
    return Math.round((sum / withConf.length) * 100);
  });

  delaiMoyenHeures = computed(() => {
    const resolus = this.tickets().filter(t => t.statut === 'Résolu' && t.date_resolution);
    if (!resolus.length) return null;
    const totalH = resolus.reduce((acc, t) => {
      const debut = new Date(t.created_at).getTime();
      const fin = new Date(t.date_resolution!).getTime();
      return acc + (fin - debut) / 3_600_000;
    }, 0);
    return totalH / resolus.length;
  });

  delaiMoyenLabel = computed(() => {
    const h = this.delaiMoyenHeures();
    if (h == null) return '—';
    return h < 1 ? `${Math.round(h * 60)} min` : `${h.toFixed(1)} h`;
  });

  ticketsPrioritaires = computed(() =>
    this.tickets()
      .filter(t => t.statut === 'En attente')
      .sort((a, b) => dateTicket(a.created_at).getTime() - dateTicket(b.created_at).getTime())
      .slice(0, 5)
  );

  /**
   * Les parts de l'anneau, une par statut présent, dans l'ordre du cycle de vie.
   *
   * Chaque statut garde sa couleur (COULEURS_STATUT, ticket.models.ts). Auparavant les couleurs
   * étaient distribuées dans l'ordre d'apparition des statuts : le vert pouvait
   * tomber sur « Rejeté » un jour et sur « Résolu » le lendemain, et seul le
   * survol permettait de savoir quoi était quoi.
   */
  repartitionStatuts = computed<PartStatut[]>(() => {
    const total = this.tickets().length || 1;
    return (Object.keys(STATUT_CFG) as Statut[])
      .map(statut => {
        const n = this.tickets().filter(t => t.statut === statut).length;
        return { statut, libelle: STATUT_CFG[statut].label, n, pct: n / total, couleur: COULEURS_STATUT[statut] };
      })
      .filter(p => p.n > 0);
  });

  /** Chart.js dessine sur un canvas et ne lit pas les variables CSS : on les
   *  résout au rendu, et le mode clair ou sombre fait partie des dépendances. */
  private resoudre(couleur: string): string {
    const m = couleur.match(/^var\((--[^)]+)\)$/);
    if (!m) return couleur;
    return getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim() || '#888888';
  }

  statutChartData = computed<ChartData<'doughnut'>>(() => {
    this.theme.isDark();
    const parts = this.repartitionStatuts();
    return {
      labels: parts.map(p => p.libelle),
      datasets: [{
        data: parts.map(p => p.n),
        backgroundColor: parts.map(p => this.resoudre(p.couleur)),
        // Un liseré de la couleur de la carte détache les parts les unes des autres.
        borderColor: this.resoudre('var(--color-surface-container-lowest)'),
        borderWidth: 2,
      }],
    };
  });

  categorieChartData = computed<ChartData<'bar'>>(() => {
    const counts: Record<string, number> = {};
    for (const t of this.tickets()) {
      const cat = t.categorie_finale || t.categorie_predite || 'Non classé';
      counts[cat] = (counts[cat] || 0) + 1;
    }
    return {
      labels: Object.keys(counts),
      datasets: [{
        data: Object.values(counts),
        backgroundColor: '#4f46e5',
        borderRadius: 4,
        barThickness: 24,
      }],
    };
  });

  volumeChartData = computed<ChartData<'line'>>(() => {
    const days: string[] = [];
    const today = new Date();
    for (let i = 13; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      days.push(d.toISOString().slice(0, 10));
    }
    const creesParJour: Record<string, number> = Object.fromEntries(days.map(d => [d, 0]));
    const resolusParJour: Record<string, number> = Object.fromEntries(days.map(d => [d, 0]));
    for (const t of this.tickets()) {
      const cKey = t.created_at?.slice(0, 10);
      if (cKey in creesParJour) creesParJour[cKey]++;
      if (t.date_resolution) {
        const rKey = t.date_resolution.slice(0, 10);
        if (rKey in resolusParJour) resolusParJour[rKey]++;
      }
    }
    return {
      labels: days.map(d => new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })),
      datasets: [
        { label: 'Créés', data: days.map(d => creesParJour[d]), borderColor: '#3525cd', backgroundColor: 'rgba(53,37,205,0.1)', fill: true, tension: 0.3, pointRadius: 2 },
        { label: 'Résolus', data: days.map(d => resolusParJour[d]), borderColor: '#565e74', borderDash: [5, 5], tension: 0.3, pointRadius: 0 },
      ],
    };
  });

  chartOptionsLine: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: '#e4e1ee' } },
      x: { grid: { display: false } },
    },
  };

  chartOptionsDoughnut: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: { legend: { display: false } },
  };

  chartOptionsBar: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { stepSize: 1 } },
      y: { grid: { display: false } },
    },
  };

  ngOnInit(): void {
    this.detacher = this.store.suivre();
  }

  ngOnDestroy(): void {
    this.detacher?.();
  }

  /** L'API renvoie l'heure UTC sans fuseau : `dateTicket` remet le Z, sinon un
   *  ticket qui vient d'arriver paraît attendre depuis plus d'une heure. */
  timeAgo(iso: string): string {
    const diffMin = Math.round((Date.now() - dateTicket(iso).getTime()) / 60000);
    if (diffMin < 60) return `Il y a ${diffMin} min`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `Il y a ${diffH} h`;
    return `Il y a ${Math.round(diffH / 24)} j`;
  }

  goToTicket(id: number): void {
    this.router.navigate(['/admin/tickets', id]);
  }
}
