import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { TicketsStore } from '../../../core/services/tickets-store';
import {
  STATUT_CFG, Ticket, categorieCfg, couleurConfiance, dateTicket, jourTicket,
} from '../../../models/ticket.models';

/** Les quatre piles du journal. Le regroupement est propre à cet écran : les
 *  statuts en base restent ceux de l'API. */
type Filtre = 'tous' | 'attente' | 'charge' | 'clos';

/** Un ticket qui attend depuis plus longtemps que cela remonte en rouge : c'est
 *  le rappel que la file d'approbation ne donne pas. Même valeur que la règle
 *  qui existait dans la version précédente de cet écran. */
const RETARD_MS = 24 * 3_600_000;

/** Le journal se lit du haut : on montre les arrivées les plus récentes et on
 *  descend à la demande. Afficher plusieurs centaines de lignes d'un coup
 *  alourdirait la page sans servir personne. */
const LIGNES_PAR_PAS = 10;

/**
 * Notifications et arrivées.
 *
 * L'écran répond à deux besoins que ni la file d'approbation ni le tableau de
 * bord ne couvrent : savoir ce qui est arrivé depuis la dernière visite, et voir
 * qui s'occupe de quoi dans l'équipe. Il ne déclenche aucune action métier :
 * « Prendre en charge » conduit à la file d'approbation, où la décision se prend
 * comme d'habitude.
 */
@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notifications.html',
  styleUrl: './notifications.css',
})
export class Notifications implements OnInit, OnDestroy {
  private store = inject(TicketsStore);
  private router = inject(Router);
  private auth = inject(AuthService);

  /** La liste vient du magasin partagé, relu toutes les quinze secondes : un
   *  ticket déposé par un client apparaît ici sans recharger la page. */
  tickets = this.store.tickets;
  chargement = this.store.chargement;
  erreur = this.store.erreur;
  son = this.store.son;
  nonVus = this.store.nonVus;

  statutCfg = STATUT_CFG;
  cfgCategorie = categorieCfg;

  filtre = signal<Filtre>('tous');
  limite = signal(LIGNES_PAR_PAS);
  /** Jour choisi au calendrier, au format AAAA-MM-JJ. Vide : tout le journal. */
  jour = signal('');

  /** La référence est figée à l'ouverture de l'écran. Sans cela, marquer comme
   *  vu ferait disparaître les repères sous les yeux de celui qui lit encore. */
  private reference = signal(this.store.vuLe());

  private detacher?: () => void;

  ngOnInit(): void {
    this.detacher = this.store.suivre();
  }

  ngOnDestroy(): void {
    this.detacher?.();
  }

  // ── Comptes ────────────────────────────────────────────────────────────────

  attente = computed(() => this.tickets().filter(t => t.statut === 'En attente'));
  enCours = computed(() => this.tickets().filter(
    t => t.statut === 'Prise en Charge' || t.statut === 'Problème'));
  clos = computed(() => this.tickets().filter(
    t => t.statut === 'Résolu' || t.statut === 'Rejeté'));

  /** Les miens et ceux des collègues, pour la phrase sous le compteur. */
  enCoursMiens = computed(() => this.enCours().filter(t => this.estAMoi(t)).length);

  enRetard = computed(() => this.attente().filter(t => this.estEnRetard(t)).length);

  // ── Journal ────────────────────────────────────────────────────────────────

  private trie = computed(() => [...this.tickets()].sort(
    (a, b) => dateTicket(b.created_at).getTime() - dateTicket(a.created_at).getTime()));

  /** Le journal, ramené au jour choisi s'il y en a un. Les pastilles comptent
   *  là-dedans : elles décrivent ce qui est sous les yeux. */
  private duJour = computed(() => {
    const j = this.jour();
    return j ? this.trie().filter(t => jourTicket(t.created_at) === j) : this.trie();
  });

  /** Ce que comptent les quatre pastilles de filtre. */
  comptes = computed(() => {
    const liste = this.duJour();
    return {
      tous: liste.length,
      attente: liste.filter(t => t.statut === 'En attente').length,
      charge: liste.filter(t => t.statut === 'Prise en Charge' || t.statut === 'Problème').length,
      clos: liste.filter(t => t.statut === 'Résolu' || t.statut === 'Rejeté').length,
    };
  });

  private retenus = computed(() => {
    const f = this.filtre();
    const base = this.duJour();
    if (f === 'attente') return base.filter(t => t.statut === 'En attente');
    if (f === 'charge') return base.filter(
      t => t.statut === 'Prise en Charge' || t.statut === 'Problème');
    if (f === 'clos') return base.filter(
      t => t.statut === 'Résolu' || t.statut === 'Rejeté');
    return base;
  });

  total = computed(() => this.retenus().length);
  visibles = computed(() => this.retenus().slice(0, this.limite()));
  resteAVoir = computed(() => Math.max(0, this.total() - this.visibles().length));

  /** Le journal se lit par jour : aujourd'hui, hier, puis la date. */
  groupes = computed(() => {
    const groupes: { jour: string; lignes: Ticket[] }[] = [];
    for (const t of this.visibles()) {
      const jour = this.libelleJour(t.created_at);
      const dernier = groupes[groupes.length - 1];
      if (dernier && dernier.jour === jour) dernier.lignes.push(t);
      else groupes.push({ jour, lignes: [t] });
    }
    return groupes;
  });

  // ── Lecture d'une ligne ────────────────────────────────────────────────────

  estNeuf(t: Ticket): boolean {
    return dateTicket(t.created_at).getTime() > this.reference();
  }

  estEnRetard(t: Ticket): boolean {
    return t.statut === 'En attente'
      && Date.now() - dateTicket(t.created_at).getTime() > RETARD_MS;
  }

  /** L'API pose `assigne_a` au format « prénom nom » de l'administrateur qui
   *  prend le ticket (api/routers/tickets.py). On compare avec le compte
   *  connecté pour dire « par vous » plutôt que de répéter son propre nom. */
  estAMoi(t: Ticket): boolean {
    const nom = (t.assigne_a ?? '').trim();
    const moi = this.nomAdmin;
    return nom !== '' && moi !== '' && nom.toLowerCase() === moi.toLowerCase();
  }

  private get nomAdmin(): string {
    const u = this.auth.currentUser();
    return u ? (`${u.prenom ?? ''} ${u.nom ?? ''}`.trim() || u.email || '') : '';
  }

  qui(t: Ticket): string {
    const nom = (t.assigne_a ?? '').trim();
    if (t.statut === 'En attente') return 'personne ne l’a pris';
    if (!nom) return t.statut === 'Résolu' ? 'clôturé' : 'en cours';
    const verbe = t.statut === 'Résolu' || t.statut === 'Rejeté' ? 'clôturé par' : 'pris en charge par';
    return `${verbe} ${this.estAMoi(t) ? 'vous' : nom}`;
  }

  categorie(t: Ticket): string {
    return t.categorie_finale || t.categorie_predite || 'Non classé';
  }

  refTicket(t: Ticket): string {
    return `#${t.id.toString().padStart(4, '0')}`;
  }

  confianceCouleur(c: number | null): string {
    return couleurConfiance(c);
  }

  timeAgo(iso: string): string {
    const minutes = Math.round((Date.now() - dateTicket(iso).getTime()) / 60000);
    if (minutes < 1) return 'à l’instant';
    if (minutes < 60) return `il y a ${minutes} min`;
    const heures = Math.round(minutes / 60);
    if (heures < 24) return `il y a ${heures} h`;
    return `il y a ${Math.round(heures / 24)} j`;
  }

  private libelleJour(iso: string): string {
    const d = dateTicket(iso);
    const jour = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
    const aujourdhui = new Date();
    const zero = new Date(aujourdhui.getFullYear(), aujourdhui.getMonth(), aujourdhui.getDate()).getTime();
    if (jour === zero) return 'Aujourd’hui';
    if (jour === zero - 86_400_000) return 'Hier';
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  /** Un ticket qui attend se décide dans la file d'approbation ; les autres
   *  s'ouvrent sur leur écran de traitement. */
  ouvrir(t: Ticket): void {
    if (t.statut === 'En attente') this.router.navigate(['/admin/approval-queue']);
    else this.router.navigate(['/admin/tickets', t.id]);
  }

  marquerVu(): void {
    this.store.marquerVu();
    this.reference.set(this.store.vuLe());
  }

  basculerSon(): void {
    this.store.basculerSon();
  }

  rafraichir(): void {
    this.store.rafraichir();
  }

  heureMaj(): string {
    return this.store.libelleMaj();
  }

  voirPlus(): void {
    this.limite.update(n => n + LIGNES_PAR_PAS);
  }

  changerFiltre(f: Filtre): void {
    this.filtre.set(f);
    this.limite.set(LIGNES_PAR_PAS);
  }

  changerJour(valeur: string): void {
    this.jour.set(valeur);
    this.limite.set(LIGNES_PAR_PAS);
  }

  effacerJour(): void {
    this.changerJour('');
  }

  /** Borne haute du calendrier : rien n'arrive dans le futur. */
  aujourdhui(): string {
    return jourTicket(new Date().toISOString());
  }

  /** Le jour choisi, en toutes lettres, pour la phrase de bas de liste. */
  jourLisible(): string {
    const j = this.jour();
    if (!j) return '';
    const [a, m, d] = j.split('-').map(Number);
    return new Date(a, m - 1, d).toLocaleDateString('fr-FR',
      { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  }
}
