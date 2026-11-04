import { Component, OnDestroy, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { TicketsStore } from '../../../core/services/tickets-store';
import {
  Ticket, couleurConfiance, Statut, STATUT_CFG, categorieCfg, prioriteCfg,
  dateTicket, jourTicket, COULEURS_STATUT,
} from '../../../models/ticket.models';

/** Les trois piles de la file : ce qui attend une décision, ce qui a été pris en
 *  charge ou résolu, ce qui a été rejeté. Le regroupement est propre à cet écran,
 *  les statuts en base restent ceux de l'API. */
type Onglet = 'attente' | 'valides' | 'rejetes';

/**
 * Lignes montrées d'emblée dans les piles « Validés » et « Rejetés ».
 *
 * Ces deux piles ne font que grossir : au bout de quelques centaines de tickets,
 * les afficher en entier fabrique une page interminable sur un écran qui sert à
 * décider, pas à consulter l'historique. On montre donc les plus récentes, et le
 * reste s'atteint par « Afficher plus » ou par le filtre de date. La pile « En
 * attente » n'est pas limitée : elle, il faut la voir en entier.
 */
const LIGNES_TRAITEES = 4;

@Component({
  selector: 'app-approval-queue',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './approval-queue.html',
  styleUrl: './approval-queue.css',
})
export class ApprovalQueue implements OnInit, OnDestroy {
  private ticketApi = inject(TicketApiService);
  private router = inject(Router);
  private store = inject(TicketsStore);

  /** La liste vient du magasin partagé, qui la relit toutes les quinze secondes :
   *  un ticket déposé par un client arrive dans la file sans recharger la page. */
  allTickets = this.store.tickets;
  loading = this.store.chargement;
  derniereMaj = this.store.derniereMaj;
  /** Erreur d'une décision. Les erreurs de chargement viennent du magasin. */
  error = signal<string | null>(null);
  messageErreur = computed(() => this.error() ?? this.store.erreur());
  /** Identifiant du ticket dont une décision est en cours d'envoi. */
  enCours = signal<number | null>(null);

  onglet = signal<Onglet>('attente');
  recherche = signal('');
  /** Jour choisi au calendrier, au format AAAA-MM-JJ. Vide : toute la pile. */
  jour = signal('');
  /** Nombre de lignes affichées dans les piles traitées. */
  limite = signal(LIGNES_TRAITEES);
  choisiId = signal<number | null>(null);
  ragOuvert = signal(false);

  /** Les trois onglets, chacun dans la couleur de sa pile : la même que dans
   *  l'anneau du tableau de bord (COULEURS_STATUT). « Validés » regroupe la prise
   *  en charge et la clôture ; il prend le vert de la clôture. */
  readonly onglets: { cle: Onglet; libelle: string; icone: string; couleur: string }[] = [
    { cle: 'attente', libelle: 'En attente', icone: 'hourglass_top', couleur: COULEURS_STATUT['En attente'] },
    { cle: 'valides', libelle: 'Validés', icone: 'check_circle', couleur: COULEURS_STATUT['Résolu'] },
    { cle: 'rejetes', libelle: 'Rejetés', icone: 'cancel', couleur: COULEURS_STATUT['Rejeté'] },
  ];

  statutCfg = STATUT_CFG;
  cfgCategorie = categorieCfg;
  cfgPriorite = prioriteCfg;

  pendingTickets = computed(() => this.allTickets().filter(t => t.statut === 'En attente'));
  validesTickets = computed(() => this.allTickets().filter(t => t.statut === 'Prise en Charge' || t.statut === 'Résolu'));
  rejetesTickets = computed(() => this.allTickets().filter(t => t.statut === 'Rejeté'));

  /**
   * La date qui fait foi dans la pile courante : l'arrivée pour ce qui attend
   * une décision, la décision pour ce qui est déjà traité. C'est elle qui
   * ordonne la pile et que le calendrier interroge.
   */
  dateRef(t: Ticket): string {
    return this.onglet() === 'attente' ? t.created_at : (t.date_resolution || t.created_at);
  }

  /**
   * Ce que raconte la date affichée sur une ligne.
   *
   * Seule la clôture pose une date en base (`resolved_at`, api/routers/tickets.py) :
   * un ticket pris en charge ou rejeté n'a que sa date d'arrivée. La ligne dit
   * donc ce que l'on sait, au lieu de laisser croire à une date de décision.
   */
  libelleDate(t: Ticket): string {
    if (this.onglet() === 'attente' || !t.date_resolution) return 'reçu il y a';
    return 'clôturé il y a';
  }

  /** La pile de l'onglet courant, réduite par la recherche et par le jour choisi.
   *  Les piles traitées sortent la plus récente en tête ; « En attente » garde
   *  l'ordre de la file. */
  private retenus = computed(() => {
    const base = this.onglet() === 'attente' ? this.pendingTickets()
               : this.onglet() === 'valides' ? this.validesTickets()
               : this.rejetesTickets();

    const q = this.recherche().toLowerCase().trim();
    const jour = this.jour();

    let liste = base;
    if (q) {
      liste = liste.filter(t =>
        t.titre.toLowerCase().includes(q) ||
        (t.demandeur_nom || '').toLowerCase().includes(q) ||
        t.id.toString().includes(q));
    }
    if (jour) liste = liste.filter(t => jourTicket(this.dateRef(t)) === jour);

    if (this.onglet() === 'attente') return liste;
    return [...liste].sort(
      (a, b) => dateTicket(this.dateRef(b)).getTime() - dateTicket(this.dateRef(a)).getTime());
  });

  total = computed(() => this.retenus().length);

  visibles = computed(() =>
    this.onglet() === 'attente' ? this.retenus() : this.retenus().slice(0, this.limite()));

  resteAVoir = computed(() => Math.max(0, this.total() - this.visibles().length));

  /** Le ticket affiché à droite : celui qu'on a ouvert s'il est toujours dans la
   *  pile, le premier sinon. Après une décision le ticket quitte la pile et le
   *  suivant prend sa place sans qu'on ait à le demander. */
  choisi = computed<Ticket | null>(() => {
    const liste = this.visibles();
    return liste.find(t => t.id === this.choisiId()) ?? liste[0] ?? null;
  });

  private detacher?: () => void;

  ngOnInit(): void {
    this.detacher = this.store.suivre();
  }

  ngOnDestroy(): void {
    this.detacher?.();
  }

  /** Relecture immédiate, sans attendre le tour de sondage suivant. */
  rafraichir(): void {
    this.error.set(null);
    this.store.rafraichir();
  }

  /** Heure de la dernière lecture, pour que l'écran dise à quand il remonte. */
  heureMaj(): string {
    return this.store.libelleMaj();
  }

  // ── Piles, calendrier, pagination ──────────────────────────────────────────

  compte(o: Onglet): number {
    return o === 'attente' ? this.pendingTickets().length
         : o === 'valides' ? this.validesTickets().length
         : this.rejetesTickets().length;
  }

  /** Une couleur de pile éclaircie, pour le fond de l'onglet ouvert et les
   *  pastilles des onglets fermés. */
  teinte(couleur: string, pourcent: number): string {
    return `color-mix(in srgb, ${couleur} ${pourcent}%, transparent)`;
  }

  changerOnglet(o: Onglet): void {
    this.onglet.set(o);
    this.limite.set(LIGNES_TRAITEES);
    this.choisiId.set(null);
  }

  changerJour(valeur: string): void {
    this.jour.set(valeur);
    this.limite.set(LIGNES_TRAITEES);
    this.choisiId.set(null);
  }

  effacerJour(): void {
    this.changerJour('');
  }

  voirPlus(): void {
    this.limite.update(n => n + LIGNES_TRAITEES);
  }

  /** Borne haute du calendrier : on ne cherche pas dans le futur. */
  aujourdhui(): string {
    return jourTicket(new Date().toISOString());
  }

  /** Le jour choisi, écrit en toutes lettres pour la phrase sous la pile. */
  jourLisible(): string {
    const j = this.jour();
    if (!j) return '';
    const [a, m, d] = j.split('-').map(Number);
    return new Date(a, m - 1, d).toLocaleDateString('fr-FR',
      { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  }

  // ── Lecture ────────────────────────────────────────────────────────────────

  choisir(t: Ticket): void {
    this.choisiId.set(t.id);
    this.ragOuvert.set(false);
  }

  categorie(t: Ticket): string {
    return t.categorie_finale || t.categorie_predite || '';
  }

  priorite(t: Ticket): string {
    return t.priorite_finale || t.priorite_predite || '';
  }

  reference(t: Ticket): string {
    return `#${t.id.toString().padStart(4, '0')}`;
  }

  confPct(c: number | null): number {
    return c != null ? Math.round(c * 100) : 0;
  }

  /** Échelle commune à toute l'application : voir couleurConfiance. */
  confianceColor(c: number | null): string {
    return couleurConfiance(c);
  }

  /** Les horodatages de l'API sont en UTC sans fuseau : `dateTicket` remet le Z,
   *  sinon un ticket qui vient d'arriver paraît vieux d'une heure. */
  timeAgo(iso: string): string {
    const diffMin = Math.round((Date.now() - dateTicket(iso).getTime()) / 60000);
    if (diffMin < 60) return `${diffMin} min`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `${diffH} h`;
    return `${Math.round(diffH / 24)} j`;
  }

  formatDate(iso: string): string {
    const d = dateTicket(iso);
    return `${d.toLocaleDateString('fr-FR')} ${d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`;
  }

  // ── Décisions ──────────────────────────────────────────────────────────────

  /** Prend le ticket en charge puis ouvre l'écran de traitement : valider, c'est
   *  s'engager à traiter le ticket, donc on enchaîne directement sur la clôture. */
  valider(t: Ticket): void {
    this.decider(t, 'Prise en Charge', 'Impossible de prendre ce ticket en charge.', true);
  }

  /** Un ticket rejeté n'a pas de suite : on reste dans la file, sur le suivant. */
  rejeter(t: Ticket): void {
    this.decider(t, 'Rejeté', 'Impossible de rejeter ce ticket.');
  }

  /** Ouvre l'écran de traitement complet, où se font la clôture et la réponse
   *  au client. */
  ouvrir(t: Ticket): void {
    this.router.navigate(['/admin/tickets', t.id]);
  }

  private decider(t: Ticket, statut: Statut, messageErreur: string, ouvrirEnsuite = false): void {
    this.enCours.set(t.id);
    this.error.set(null);
    this.ticketApi.approveTicket(t.id, { statut }).subscribe({
      next: () => {
        this.enCours.set(null);
        this.store.majTicket(t.id, { statut });
        this.choisiId.set(null);
        if (ouvrirEnsuite) this.ouvrir(t);
      },
      error: () => {
        this.enCours.set(null);
        this.error.set(messageErreur);
      },
    });
  }
}
