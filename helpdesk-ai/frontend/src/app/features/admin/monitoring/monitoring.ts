import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { TicketsStore } from '../../../core/services/tickets-store';
import { ThemeService } from '../../../core/services/theme.service';
import {
  Ticket, PRIORITE_OPTIONS, categorieCfg, prioriteCfg, dateTicket,
} from '../../../models/ticket.models';

/**
 * KPIs.
 *
 * L'écran ne vit que sur les tickets, relus en direct dans le magasin partagé :
 * activité du support, répartitions et tendances. Aucun rapport produit hors
 * ligne n'est affiché ici, ils restent dans les fichiers metrics/ et dans le
 * mémoire.
 *
 * Quand une mesure n'a pas de base, l'écran l'écrit (« non mesurable ») au lieu
 * d'afficher un zéro qui laisserait croire à un résultat.
 */

type Periode = 7 | 30 | 90;

const JOUR = 86_400_000;

/** Les couleurs des graphiques viennent des jetons --viz-* de styles.css, réglés
 *  pour le mode clair et pour le mode sombre et vérifiés dans les deux. */

/** Quatre familles bien distinctes deux à deux, quel que soit l'ordre des barres. */
const COULEUR_CLASSIFICATION: Record<string, string> = {
  'Demande': 'var(--viz-bleu)',
  'Incident': 'var(--viz-rouge)',
  'Changement': 'var(--viz-vert)',
  'Problème': 'var(--viz-ambre)',
};

/** La gravité va du froid au chaud : Critique ressort dans les deux modes. */
const COULEUR_PRIORITE: Record<string, string> = {
  'Faible': 'var(--viz-bleu)',
  'Modéré': 'var(--viz-vert)',
  'Urgent': 'var(--viz-ambre)',
  'Critique': 'var(--viz-rouge)',
};

/**
 * Le pas d'une rampe d'une seule teinte pour une valeur rapportée au maximum :
 * des tranches égales, de 1 (discret) à `nbPas` (le plus marqué). Deux valeurs
 * égales reçoivent donc la même couleur.
 */
function pasDeRampe(nom: 'bleu' | 'orange', nbPas: number, part: number): string {
  const pas = Math.min(nbPas, Math.max(1, Math.ceil(part * nbPas)));
  return `var(--viz-${nom}-${pas})`;
}

export interface Barre { libelle: string; n: number; pct: number; couleur: string }

/** Une catégorie et le temps qu'elle coûte. `heures` reste null tant qu'aucun
 *  ticket de cette catégorie n'a été clôturé sur la période : une moyenne sur
 *  rien n'est pas zéro. */
export interface LigneDelai {
  libelle: string;
  heures: number | null;
  n: number;
  pct: number;
  couleur: string;
}

@Component({
  selector: 'app-monitoring',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './monitoring.html',
  styleUrl: './monitoring.css',
})
export class Monitoring implements OnInit, OnDestroy {
  private store = inject(TicketsStore);
  private theme = inject(ThemeService);

  tickets = this.store.tickets;
  chargement = this.store.chargement;
  derniereMaj = this.store.derniereMaj;

  periodes: Periode[] = [7, 30, 90];
  periode = signal<Periode>(30);

  private detacher?: () => void;

  ngOnInit(): void {
    this.detacher = this.store.suivre();
  }

  ngOnDestroy(): void {
    this.detacher?.();
  }

  rafraichir(): void {
    this.store.rafraichir();
  }

  heureMaj(): string {
    return this.store.libelleMaj();
  }

  // ── Période ──────────────────────────────────────────────────────────────────

  /** Relu à chaque sondage du magasin et à chaque changement de période. */
  private bornes = computed(() => {
    this.tickets();
    const fin = Date.now();
    const duree = this.periode() * JOUR;
    return { fin, debut: fin - duree, debutAvant: fin - 2 * duree };
  });

  /** Les dates de l'API sont en UTC sans fuseau : `dateTicket` remet le Z avant
   *  de comparer, sinon un ticket reçu peu après minuit tombe la veille et sort
   *  de la fenêtre choisie. */
  private entre(iso: string | null | undefined, apres: number, jusqua: number): boolean {
    if (!iso) return false;
    const t = dateTicket(iso).getTime();
    return t > apres && t <= jusqua;
  }

  ticketsPeriode = computed(() => {
    const b = this.bornes();
    return this.tickets().filter(t => this.entre(t.created_at, b.debut, b.fin));
  });

  // ── Activité du support ───────────────────────────────────────────

  recus = computed(() => this.ticketsPeriode().length);
  recusAvant = computed(() => {
    const b = this.bornes();
    return this.tickets().filter(t => this.entre(t.created_at, b.debutAvant, b.debut)).length;
  });

  private closPeriode = computed(() => {
    const b = this.bornes();
    return this.tickets().filter(t => this.entre(t.date_resolution, b.debut, b.fin));
  });
  clotures = computed(() => this.closPeriode().length);
  cloturesAvant = computed(() => {
    const b = this.bornes();
    return this.tickets().filter(t => this.entre(t.date_resolution, b.debutAvant, b.debut)).length;
  });

  enAttente = computed(() => this.tickets().filter(t => t.statut === 'En attente').length);

  variationRecus = computed(() => this.variation(this.recus(), this.recusAvant()));
  variationClotures = computed(() => this.variation(this.clotures(), this.cloturesAvant()));

  /** Variation en pourcentage ; sans période précédente comparable, pas de chiffre. */
  private variation(actuel: number, avant: number): number | null {
    if (avant === 0) return null;
    return Math.round(((actuel - avant) / avant) * 100);
  }

  tempsMoyen = computed(() => {
    const clos = this.closPeriode();
    if (!clos.length) return null;
    const heures = clos.reduce((s, t) => s + this.heuresDeTraitement(t), 0);
    return heures / clos.length;
  });

  // ── Répartitions et tendances sur la période ──────────────────────

  /** La catégorie retenue : celle que l'administrateur a confirmée, sinon celle
   *  que le modèle a proposée. */
  private categorieDe(t: Ticket): string {
    return t.categorie_finale || t.categorie_predite || 'Non classé';
  }

  parCategorie = computed<Barre[]>(() =>
    this.repartir(this.ticketsPeriode(), t => this.categorieDe(t), nom => categorieCfg(nom).color));

  /** Demande, Incident, Problème, Changement. Le champ est renseigné à chaque
   *  dépôt et n'apparaissait sur aucun écran. */
  parClassification = computed<Barre[]>(() =>
    this.repartir(
      this.ticketsPeriode(),
      t => (t.classification_finale || t.classification_predite || t.classification || 'Non renseignée').trim(),
      nom => COULEUR_CLASSIFICATION[nom] ?? 'var(--cat-autre)'));

  /** Une seule teinte, plus soutenue pour la filiale la plus sollicitée : la
   *  couleur confirme le classement au lieu de décorer. */
  parFiliale = computed<Barre[]>(() => {
    const barres = this.repartir(this.ticketsPeriode(), t => t.filiale || 'Non renseignée', () => '');
    const maxi = Math.max(1, ...barres.map(b => b.n));
    return barres.map(b => ({ ...b, couleur: pasDeRampe('bleu', 5, b.n / maxi) }));
  });

  /** Les quatre niveaux de l'application, dans leur ordre, même vides. */
  parPriorite = computed<Barre[]>(() => {
    const l = this.ticketsPeriode();
    const total = l.length || 1;
    const niveaux = PRIORITE_OPTIONS.map(p => {
      const n = l.filter(t => (t.priorite_finale || t.priorite_predite) === p).length;
      return { libelle: p, n, pct: n / total, couleur: COULEUR_PRIORITE[p] ?? prioriteCfg(p).color };
    });
    const autres = l.filter(t => !PRIORITE_OPTIONS.includes(t.priorite_finale || t.priorite_predite)).length;
    if (autres) niveaux.push({ libelle: 'Non renseignée', n: autres, pct: autres / total, couleur: 'var(--cat-autre)' });
    return niveaux;
  });

  private repartir(l: Ticket[], cle: (t: Ticket) => string, couleur: (nom: string) => string): Barre[] {
    const total = l.length || 1;
    const comptes = new Map<string, number>();
    for (const t of l) comptes.set(cle(t), (comptes.get(cle(t)) ?? 0) + 1);
    return [...comptes.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([libelle, n]) => ({ libelle, n, pct: n / total, couleur: couleur(libelle) }));
  }

  /** Temps passé entre la réception et la clôture d'un ticket, en heures. */
  private heuresDeTraitement(t: Ticket): number {
    return (dateTicket(t.date_resolution).getTime() - dateTicket(t.created_at).getTime()) / 3_600_000;
  }

  /**
   * Temps moyen de traitement, catégorie par catégorie.
   *
   * Toutes les catégories reçues sur la période figurent dans la liste, y
   * compris celles dont aucun ticket n'a encore été clôturé : elles affichent
   * « non mesurable » plutôt qu'un zéro qui se lirait comme une réponse
   * instantanée.
   */
  delaiParCategorie = computed<LigneDelai[]>(() => {
    const cumul = new Map<string, { somme: number; n: number }>();
    for (const t of this.ticketsPeriode()) {
      const c = this.categorieDe(t);
      if (!cumul.has(c)) cumul.set(c, { somme: 0, n: 0 });
    }
    for (const t of this.closPeriode()) {
      const c = this.categorieDe(t);
      const e = cumul.get(c) ?? { somme: 0, n: 0 };
      e.somme += this.heuresDeTraitement(t);
      e.n++;
      cumul.set(c, e);
    }
    const lignes = [...cumul.entries()].map(([libelle, e]) => ({
      libelle,
      heures: e.n ? e.somme / e.n : null,
      n: e.n,
      pct: 0,
      couleur: '',
    }));
    // Un orange de plus en plus marqué à mesure que le délai s'allonge : les
    // catégories lentes ressortent d'un coup d'oeil.
    const maxi = Math.max(0, ...lignes.map(l => l.heures ?? 0));
    for (const l of lignes) {
      l.pct = maxi && l.heures != null ? (l.heures / maxi) * 100 : 0;
      l.couleur = pasDeRampe('orange', 4, l.pct / 100);
    }
    return lignes.sort((a, b) => (b.heures ?? -1) - (a.heures ?? -1));
  });

  // ── Graphiques ──────────────────────────────────────────────────────────────
  // Chart.js dessine sur un canvas et ne lit pas les variables CSS : on les résout
  // au moment du rendu, et le mode (clair ou sombre) fait partie des dépendances.

  private resoudre(couleur: string): string {
    const m = couleur.match(/^var\((--[^)]+)\)$/);
    if (!m) return couleur;
    return getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim() || '#888888';
  }

  evolution = computed<ChartData<'line'>>(() => {
    this.theme.isDark();
    const b = this.bornes();
    const jours = this.periode();
    const arrivees = new Map<string, number>();
    const clotures = new Map<string, number>();
    for (const t of this.tickets()) {
      const a = dateTicket(t.created_at).toDateString();
      arrivees.set(a, (arrivees.get(a) ?? 0) + 1);
      if (t.date_resolution) {
        const c = dateTicket(t.date_resolution).toDateString();
        clotures.set(c, (clotures.get(c) ?? 0) + 1);
      }
    }
    const labels: string[] = [];
    const serieA: number[] = [];
    const serieC: number[] = [];
    for (let i = jours - 1; i >= 0; i--) {
      const d = new Date(b.fin - i * JOUR);
      labels.push(d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }));
      serieA.push(arrivees.get(d.toDateString()) ?? 0);
      serieC.push(clotures.get(d.toDateString()) ?? 0);
    }
    const primaire = this.resoudre('var(--color-primary)');
    const vert = this.resoudre('var(--statut-resolu)');
    return {
      labels,
      datasets: [
        { label: 'Arrivées', data: serieA, borderColor: primaire, backgroundColor: primaire,
          tension: 0.35, pointRadius: jours > 30 ? 0 : 3, borderWidth: 2 },
        { label: 'Clôtures', data: serieC, borderColor: vert, backgroundColor: vert,
          tension: 0.35, pointRadius: jours > 30 ? 0 : 3, borderWidth: 2 },
      ],
    };
  });

  /**
   * Stock de tickets ouverts, jour par jour.
   *
   * Pour chaque graduation de la période, on compte les tickets déjà reçus à cet
   * instant et pas encore clôturés. La courbe des flux dit combien arrivent et
   * combien partent, celle-ci dit si l'écart se creuse.
   */
  private serieStock = computed<{ labels: string[]; valeurs: number[] }>(() => {
    const b = this.bornes();
    const jours = this.periode();
    const vies = this.tickets().map(t => ({
      debut: dateTicket(t.created_at).getTime(),
      fin: t.date_resolution ? dateTicket(t.date_resolution).getTime() : null,
    }));
    const labels: string[] = [];
    const valeurs: number[] = [];
    for (let i = jours - 1; i >= 0; i--) {
      const instant = b.fin - i * JOUR;
      labels.push(new Date(instant).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }));
      valeurs.push(vies.filter(v => v.debut <= instant && (v.fin === null || v.fin > instant)).length);
    }
    return { labels, valeurs };
  });

  stockOuvert = computed<ChartData<'line'>>(() => {
    this.theme.isDark();
    const { labels, valeurs } = this.serieStock();
    const ambre = this.resoudre('var(--statut-attente)');
    return {
      labels,
      datasets: [
        { label: 'Tickets ouverts', data: valeurs, borderColor: ambre, backgroundColor: ambre,
          tension: 0.35, pointRadius: this.periode() > 30 ? 0 : 3, borderWidth: 2 },
      ],
    };
  });

  /** Dernier point de la courbe : ce qui est ouvert à cet instant. */
  stockActuel = computed(() => {
    const v = this.serieStock().valeurs;
    return v.length ? v[v.length - 1] : 0;
  });

  private variationStock = computed(() => {
    const v = this.serieStock().valeurs;
    return v.length ? v[v.length - 1] - v[0] : 0;
  });

  libelleStock(): string {
    const v = this.variationStock();
    if (v === 0) return 'autant qu’au début de la période';
    if (v > 0) return `${v} de plus qu’au début de la période`;
    return `${-v} de moins qu’au début de la période`;
  }

  optionsEvolution = computed<ChartConfiguration<'line'>['options']>(() => {
    this.theme.isDark();
    const texte = this.resoudre('var(--color-on-surface-variant)');
    const grille = this.resoudre('var(--color-outline-variant)');
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', align: 'end',
          labels: { color: texte, usePointStyle: true, boxWidth: 8, boxHeight: 8 } },
      },
      scales: {
        x: { ticks: { color: texte, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: texte, precision: 0 }, grid: { color: grille } },
      },
    };
  });

  anneauPriorite = computed<ChartData<'doughnut'>>(() => {
    this.theme.isDark();
    const niveaux = this.parPriorite();
    return {
      labels: niveaux.map(n => n.libelle),
      datasets: [{
        data: niveaux.map(n => n.n),
        backgroundColor: niveaux.map(n => this.resoudre(n.couleur)),
        borderColor: this.resoudre('var(--color-surface-container-lowest)'),
        borderWidth: 3,
      }],
    };
  });

  optionsAnneau: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: { legend: { display: false } },
  };

  // ── Mise en forme ───────────────────────────────────────────────────────────

  pct(x: number | null | undefined, decimales = 0): string {
    if (x == null) return '—';
    return `${(x * 100).toFixed(decimales).replace('.', ',')} %`;
  }

  duree(heures: number | null): string {
    if (heures == null) return '—';
    if (heures < 1) return `${Math.round(heures * 60)} min`;
    if (heures < 48) return `${heures.toFixed(1).replace('.', ',')} h`;
    return `${(heures / 24).toFixed(1).replace('.', ',')} j`;
  }

  variationTexte(v: number): string {
    return `${v > 0 ? '+' : ''}${v} %`;
  }
}
