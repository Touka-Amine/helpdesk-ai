import { Injectable, computed, inject, signal } from '@angular/core';
import { TicketApiService } from '../../api/ticket-api.service';
import { Ticket, dateTicket } from '../../models/ticket.models';

/** Intervalle de sondage de la liste des tickets.
 *
 *  La console d'administration relit la liste complète toutes les quinze secondes,
 *  ce qui suffit pour qu'un ticket déposé par un client apparaisse sans recharger
 *  l'application. La liste entière pèse quelques dizaines de kilo-octets, donc la
 *  relire souvent ne coûte rien ; si la base grossit beaucoup, c'est ici qu'il
 *  faudra passer à un point d'entrée plus léger côté API (un compteur ou un
 *  paramètre « depuis »). */
const SONDAGE_MS = 15_000;

/** Ce que le navigateur retient d'une session a l'autre : la date de la derniere
 *  visite du journal des arrivees, et le choix d'entendre ou non le signal. Ces
 *  deux valeurs sont propres au poste, comme le theme. */
const CLE_VU = 'admin_arrivees_vu_le';
const CLE_SON = 'admin_arrivees_son';

function lireLocal(cle: string, defaut: number): number {
  try {
    const brut = localStorage.getItem(cle);
    const valeur = brut === null ? NaN : Number(brut);
    return Number.isFinite(valeur) ? valeur : defaut;
  } catch {
    // Navigation privee ou stockage refuse : on repart des valeurs par defaut.
    return defaut;
  }
}

function ecrireLocal(cle: string, valeur: number): void {
  try {
    localStorage.setItem(cle, String(valeur));
  } catch {
    // Sans stockage, le choix vaut pour la session en cours seulement.
  }
}

/**
 * Source unique des tickets pour la console d'administration.
 *
 * Trois écrans lisaient la même liste chacun de son côté, et aucun ne la relisait
 * après le premier chargement : il fallait recharger la page pour voir un nouveau
 * ticket. Ils lisent maintenant ce magasin, qui garde la liste à jour tant qu'un
 * écran l'affiche, et qui la relit tout de suite au retour sur l'onglet.
 */
@Injectable({ providedIn: 'root' })
export class TicketsStore {
  private api = inject(TicketApiService);

  readonly tickets = signal<Ticket[]>([]);
  readonly chargement = signal(false);
  readonly erreur = signal<string | null>(null);
  readonly derniereMaj = signal<Date | null>(null);

  readonly enAttente = computed(() => this.tickets().filter(t => t.statut === 'En attente').length);

  /** Date de la derniere visite du journal des arrivees, et tickets arrives depuis.
   *  Le compteur de la cloche et la page des arrivees lisent la meme valeur, donc
   *  marquer comme vu met les deux a jour d'un coup. */
  readonly vuLe = signal<number>(lireLocal(CLE_VU, 0));
  readonly nonVus = computed(
    () => this.tickets().filter(t => dateTicket(t.created_at).getTime() > this.vuLe()).length,
  );

  /** Nombre total de tickets apparus depuis l'ouverture de la console. Sert de
   *  signal d'arrivee : la mise en page s'en sert pour le titre de l'onglet. */
  readonly arrivees = signal(0);
  readonly son = signal<boolean>(lireLocal(CLE_SON, 1) === 1);

  private abonnes = 0;
  private minuteur: ReturnType<typeof setInterval> | null = null;
  private enVol = false;
  /** Identifiants connus au tour precedent. `null` tant que rien n'a ete lu :
   *  le premier chargement ne doit pas sonner pour les tickets deja la. */
  private connus: Set<number> | null = null;
  private audio: AudioContext | null = null;

  /** Au retour sur l'onglet, on ne fait pas attendre le prochain tour de sondage. */
  private readonly auRetour = () => {
    if (document.visibilityState === 'visible') this.rafraichir();
  };

  /**
   * À appeler par un écran qui affiche les tickets. Déclenche une lecture
   * immédiate et maintient le sondage tant qu'au moins un écran est affiché.
   * Renvoie la fonction à appeler pour se détacher.
   */
  suivre(): () => void {
    this.abonnes++;
    if (this.abonnes === 1) {
      document.addEventListener('visibilitychange', this.auRetour);
      window.addEventListener('focus', this.auRetour);
      this.minuteur = setInterval(() => {
        // Un onglet caché ne sonde pas : personne ne regarde, et le retour sur
        // l'onglet déclenche de toute façon une lecture.
        if (document.visibilityState === 'visible') this.rafraichir();
      }, SONDAGE_MS);
    }
    this.rafraichir();
    return () => this.detacher();
  }

  private detacher(): void {
    this.abonnes = Math.max(0, this.abonnes - 1);
    if (this.abonnes > 0) return;
    if (this.minuteur) {
      clearInterval(this.minuteur);
      this.minuteur = null;
    }
    document.removeEventListener('visibilitychange', this.auRetour);
    window.removeEventListener('focus', this.auRetour);
  }

  /** Relit la liste. Une lecture déjà en vol fait ignorer l'appel, pour qu'un
   *  réseau lent n'empile pas les requêtes. */
  rafraichir(): void {
    if (this.enVol) return;
    this.enVol = true;
    // Le voyant de chargement ne sert qu'au tout premier affichage : un sondage
    // ne doit pas faire clignoter l'écran.
    this.chargement.set(this.tickets().length === 0);
    this.api.getAllTickets().subscribe({
      next: (liste) => {
        this.enVol = false;
        this.chargement.set(false);
        this.erreur.set(null);
        this.signalerArrivees(liste);
        this.tickets.set(liste);
        this.derniereMaj.set(new Date());
      },
      error: () => {
        this.enVol = false;
        this.chargement.set(false);
        this.erreur.set('Impossible de charger les tickets.');
      },
    });
  }

  /** Applique une modification déjà confirmée par l'API, sans attendre le
   *  prochain sondage. */
  majTicket(id: number, modif: Partial<Ticket>): void {
    this.tickets.update(liste => liste.map(t => (t.id === id ? { ...t, ...modif } : t)));
  }

  retirer(ids: number[]): void {
    this.tickets.update(liste => liste.filter(t => !ids.includes(t.id)));
  }

  /** Marque tout ce qui est arrivé comme vu : la cloche et la page retombent à zéro. */
  marquerVu(): void {
    const maintenant = Date.now();
    this.vuLe.set(maintenant);
    ecrireLocal(CLE_VU, maintenant);
  }

  /** Coupe ou remet le signal sonore. Le choix est retenu sur ce poste. */
  basculerSon(): void {
    const actif = !this.son();
    this.son.set(actif);
    ecrireLocal(CLE_SON, actif ? 1 : 0);
    if (actif) this.sonner();
  }

  /**
   * Compare la liste relue à la précédente et signale les tickets nouveaux.
   *
   * C'est le seul endroit qui voit passer chaque tour de sondage, donc le seul
   * qui peut dire « celui-là n'était pas là il y a quinze secondes ».
   */
  private signalerArrivees(liste: Ticket[]): void {
    const ids = new Set(liste.map(t => t.id));
    if (this.connus) {
      let nouveaux = 0;
      ids.forEach(id => { if (!this.connus!.has(id)) nouveaux++; });
      if (nouveaux > 0) {
        this.arrivees.update(n => n + nouveaux);
        this.sonner();
      }
    }
    this.connus = ids;
  }

  /**
   * Deux notes courtes, produites par le navigateur : aucun fichier audio à
   * livrer. Le navigateur n'autorise le son qu'après une première interaction
   * de l'utilisateur ; avant la connexion il n'y a donc rien à jouer, et après
   * elle le contexte démarre sans difficulté.
   */
  private sonner(): void {
    if (!this.son()) return;
    try {
      const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!Ctx) return;
      this.audio ??= new Ctx();
      if (this.audio.state === 'suspended') void this.audio.resume();
      for (const [frequence, retard] of [[880, 0], [1174.7, 0.11]] as const) {
        const oscillateur = this.audio.createOscillator();
        const gain = this.audio.createGain();
        const debut = this.audio.currentTime + retard;
        oscillateur.type = 'sine';
        oscillateur.frequency.setValueAtTime(frequence, debut);
        gain.gain.setValueAtTime(0.0001, debut);
        gain.gain.exponentialRampToValueAtTime(0.2, debut + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, debut + 0.16);
        oscillateur.connect(gain);
        gain.connect(this.audio.destination);
        oscillateur.start(debut);
        oscillateur.stop(debut + 0.2);
      }
    } catch {
      // Son indisponible : la console continue sans, le compteur suffit.
    }
  }

  /** Date de la dernière lecture, en toutes lettres. */
  libelleMaj(): string {
    const d = this.derniereMaj();
    if (!d) return '—';
    return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
