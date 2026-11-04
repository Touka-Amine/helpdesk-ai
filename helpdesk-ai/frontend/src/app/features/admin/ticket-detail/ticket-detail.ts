import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import {
  Ticket, couleurConfiance, STATUT_CFG,
  Statut, ApproveTicketRequest, ChatMessage,
  PRIORITE_OPTIONS, CLASSIFICATION_OPTIONS, CATEGORIE_OPTIONS,
} from '../../../models/ticket.models';

// Meme seuil que NOVELTY_THRESHOLD cote backend (api/routers/tickets.py)
const NOVELTY_THRESHOLD = 0.5;

// Alignees sur STATUS_TRANSITIONS dans api/routers/tickets.py
const TRANSITIONS: Record<Statut, Statut[]> = {
  'En attente':      ['Prise en Charge', 'Rejeté'],
  'Prise en Charge': ['Résolu', 'Problème', 'Rejeté', 'En attente'],
  'Problème':        ['Prise en Charge', 'Résolu', 'Rejeté'],
  'Résolu':          [],
  'Rejeté':          [],
};

@Component({
  selector: 'app-ticket-detail',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './ticket-detail.html',
  styleUrl: './ticket-detail.css',
})
export class TicketDetail implements OnInit {
  private route     = inject(ActivatedRoute);
  private router    = inject(Router);
  private ticketApi = inject(TicketApiService);
  private fb        = inject(FormBuilder);

  ticket   = signal<Ticket | null>(null);
  loading  = signal(true);
  saving   = signal(false);
  error    = signal<string | null>(null);
  success  = signal<string | null>(null);

  statutCfg = STATUT_CFG;
  availableStatuts = signal<Statut[]>([]);

  prioriteOptions = PRIORITE_OPTIONS;
  classificationOptions = CLASSIFICATION_OPTIONS;
  categorieOptions = CATEGORIE_OPTIONS;

  // Ecran en 2 temps : revue (classification IA + RAG) -> cloture (champs finaux + enregistrement)
  step = signal<'revue' | 'cloture'>('revue');

  // Confirmation de cloture (Tache 2.1) : le statut n'est plus choisi via un menu
  // deroulant dans le formulaire. "Enregistrer" ouvre directement le choix du statut
  // final (parmi les transitions valides depuis le statut actuel) une fois les autres
  // champs (categorie/priorite/classification/reponse client/solution) fixes.
  showResolveConfirm = signal(false);
  modalError = signal<string | null>(null);

  // Etape cloture scindee en 2 (retour utilisateur) : categorie/priorite/classification/
  // reponse client d'abord, puis un grand popup dedie a "Solution appliquee" (champ le
  // plus long, l'admin doit pouvoir y ecrire a l'aise plutot que dans la colonne etroite).
  showSolutionModal = signal(false);

  // Synthese IA (Tache 3, human-in-the-loop) : reformule les tickets similaires via
  // un LLM local (Ollama) plutot que d'afficher la resolution brute d'un seul cas.
  synthLoading = signal(false);
  synthText = signal<string | null>(null);
  synthSource = signal<'ollama' | 'fallback' | 'none' | null>(null);
  exploreId = signal('');
  exploreLoading = signal(false);
  exploreResult = signal<Ticket | null>(null);
  exploreError = signal<string | null>(null);

  // Chat conversationnel avec l'assistant IA (Tache 3 bis, retour utilisateur) : l'admin
  // peut poser des questions de suivi libres sur le ticket/les cas similaires, au-dela
  // de la synthese initiale figee. Historique garde en memoire (signal), pas persiste —
  // repart a zero a chaque changement de ticket, comme le reste du panneau IA. Toujours
  // visible (pas de bouton pour l'ouvrir) : l'admin doit voir d'emblee qu'il peut soit
  // chercher un ticket precis au-dessus, soit poser une question libre ici.
  chatMessages = signal<ChatMessage[]>([]);
  chatInput = signal('');
  chatLoading = signal(false);

  // Refonte "entreprise" (retour utilisateur) : le chat vit desormais dans une bulle IA
  // flottante (coin bas-droit, meme pattern que la bulle de l'accueil client) plutot que
  // dans le panneau RAG lui-meme. Le panneau RAG (synthese + explorateur) part dans une
  // popup dediee pour alleger la grille principale — memes donnees/logique qu'avant,
  // juste deplacees hors de la carte pleine page.
  chatBubbleOpen = signal(false);

  toggleChatBubble(): void {
    this.chatBubbleOpen.update((v) => !v);
  }

  // ── Ou en est le ticket ────────────────────────────────────────────────────
  // Le traitement se lit en trois temps : le ticket arrive et il est classe, il
  // est pris en charge, il est clos. L'etape se deduit du statut reel, aucun
  // compteur n'est tenu a part.

  etape = computed<1 | 2 | 3>(() => {
    const s = this.ticket()?.statut;
    if (s === 'Résolu' || s === 'Rejeté') return 3;
    if (s === 'Prise en Charge' || s === 'Problème') return 2;
    return 1;
  });

  private static readonly ETAPES = ['Reçu et classé', 'Prise en charge', 'Clôture'];

  libelleEtape = computed(() => TicketDetail.ETAPES[this.etape() - 1]);

  titreEtape(n: number): string {
    return TicketDetail.ETAPES[n - 1];
  }

  couleurEtape(n: number): string {
    const e = this.etape();
    if (n < e) return 'var(--statut-resolu)';
    if (n === e) return 'var(--color-primary)';
    return 'var(--color-outline-variant)';
  }

  /** Le rejet n'est propose que si l'API accepte la transition depuis l'etat courant. */
  peutRejeter = computed(() => this.availableStatuts().includes('Rejeté'));

  // ── Rejet depuis le panneau de traitement ──────────────────────────────────
  rejetOuvert = signal(false);
  motifRejet = signal('');

  demanderRejet(): void {
    this.motifRejet.set('');
    this.modalError.set(null);
    this.rejetOuvert.set(true);
  }

  annulerRejet(): void {
    this.rejetOuvert.set(false);
    this.modalError.set(null);
  }

  /** Le motif part dans la reponse au client : un rejet sans explication n'en est
   *  pas un. */
  confirmerRejet(): void {
    const motif = this.motifRejet().trim();
    if (!motif) {
      this.modalError.set('Indiquez le motif du rejet : il est transmis au demandeur.');
      return;
    }
    this.form.patchValue({ commentaire_client: motif });
    this.rejetOuvert.set(false);
    this.performSave('Rejeté');
  }

  /** Raccourci du panneau : ouvre la cloture et place le curseur sur l'affectation. */
  assignerACollegue(): void {
    this.step.set('cloture');
    setTimeout(() => document.getElementById('champ-assignation')?.focus());
  }

  // ── Reprise de la procedure proposee ───────────────────────────────────────
  copieFaite = signal(false);

  /** Le texte affiche : la synthese quand elle existe, la suggestion brute sinon. */
  procedureAffichee(): string {
    return (this.synthText() || this.ticket()?.solution_rag || '').trim();
  }

  copierProcedure(): void {
    const texte = this.procedureAffichee();
    if (!texte) return;
    navigator.clipboard?.writeText(texte).then(
      () => {
        this.copieFaite.set(true);
        setTimeout(() => this.copieFaite.set(false), 2000);
      },
      () => this.error.set('Copie impossible dans ce navigateur.'),
    );
  }

  /** Reprend la procedure dans la reponse au client et ouvre la cloture : l'admin
   *  ajuste le texte au lieu de le retaper. */
  insererDansReponse(): void {
    const texte = this.procedureAffichee();
    if (!texte) return;
    const actuel = (this.form.value.commentaire_client ?? '').trim();
    const separation = '\n\n';
    this.form.patchValue({ commentaire_client: actuel ? actuel + separation + texte : texte });
    this.step.set('cloture');
  }

  private static readonly TICKET_REF_RE = /ticket\s*#\s*(\d+)/gi;

  // Rendu minimal du texte genere par l'IA (gras, retours a la ligne, et mentions
  // "Ticket #N" transformees en puce cliquable qui renvoie vers "Explorer un ticket") —
  // utilise pour la synthese, le repli brut et les messages du chat, qui citent tous
  // des tickets de la meme facon.
  renderText(text: string | null | undefined): string {
    if (!text) return '';
    const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    // Pas d'attribut data-* : le sanitizer HTML d'Angular (SecurityContext.HTML, applique
    // automatiquement a [innerHTML]) retire les attributs personnalises hors allowlist —
    // seuls role/tabindex survivent. L'ID est donc repris depuis le texte visible au clic.
    const withRefs = escaped.replace(TicketDetail.TICKET_REF_RE, (_match, id) =>
      `<span class="ticket-ref" role="button" tabindex="0">Ticket #${id}</span>`);
    return withRefs.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
  }

  synthHtml = computed(() => this.renderText(this.synthText()));

  /** Delegation d'evenements pour les puces ".ticket-ref" injectees via [innerHTML]
   *  (Angular ne lie pas (click) a du HTML insere hors template) : cliquer ou activer
   *  au clavier une mention "Ticket #N" remplit et lance directement l'explorateur. La
   *  puce peut venir de la bulle de chat (surface separee) ou du contenu de la popup RAG
   *  elle-meme — dans les deux cas on ouvre/garde la popup ouverte pour que le resultat
   *  soit visible (l'input #rag-explore-input n'existe dans le DOM que si la popup l'est). */
  onTicketRefClick(event: Event): void {
    if (event instanceof KeyboardEvent && event.key !== 'Enter' && event.key !== ' ') return;
    const target = (event.target as HTMLElement).closest('.ticket-ref');
    if (!target) return;
    const id = target.textContent?.match(/\d+/)?.[0];
    if (!id) return;
    event.preventDefault();
    this.exploreId.set(id);
    this.exploreTicket();
    setTimeout(() => document.getElementById('rag-explore-input')?.scrollIntoView({ behavior: 'smooth', block: 'center' }));
  }

  // Aucun cas historique proche : la solution appliquee devient obligatoire
  // avant de resoudre, car c'est elle qui alimentera la base de connaissances.
  isNovelCase = computed(() => {
    const s = this.ticket()?.rag_score;
    return s == null || s < NOVELTY_THRESHOLD;
  });

  form = this.fb.group({
    categorie_finale:      [''],
    priorite_finale:       [''],
    classification_finale: [''],
    commentaire_client:    [''],
    commentaire_interne:   [''],
    assigne_a:             [''],
  });

  ngOnInit(): void {
    // route.paramMap (observable) plutot que route.snapshot : la navigation d'un
    // ticket vers un autre reutilise le meme composant (meme route), donc un
    // snapshot lu une seule fois au demarrage laisserait afficher le ticket
    // precedent tant que la page n'est pas rechargee manuellement.
    this.route.paramMap.subscribe((params) => {
      const id = Number(params.get('id'));
      this.loadTicket(id);
    });
  }

  private loadTicket(id: number): void {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    this.showResolveConfirm.set(false);
    this.showSolutionModal.set(false);
    this.modalError.set(null);
    this.synthText.set(null);
    this.synthSource.set(null);
    this.exploreId.set('');
    this.exploreResult.set(null);
    this.exploreError.set(null);
    this.chatMessages.set([]);
    this.chatInput.set('');
    this.chatLoading.set(false);
    this.chatBubbleOpen.set(false);
    this.rejetOuvert.set(false);
    this.motifRejet.set('');
    this.copieFaite.set(false);
    this.ticketApi.getMyTicketDetail(id).subscribe({
      next: (t) => {
        this.ticket.set(t);
        this.loading.set(false);
        this.step.set('revue');
        this.form.patchValue({
          categorie_finale: t.categorie_finale || t.categorie_predite,
          priorite_finale: t.priorite_finale || t.priorite_predite,
          classification_finale: t.classification_finale || t.classification_predite,
          commentaire_client: t.commentaire_client,
          commentaire_interne: t.commentaire_interne,
          assigne_a: t.assigne_a ?? '',
        });
        this.availableStatuts.set(TRANSITIONS[t.statut] ?? []);
        // La synthese IA (Tache 3) est desormais la suggestion affichee par defaut
        // (retour utilisateur) plutot qu'une action optionnelle en plus de la resolution
        // brute — declenchee automatiquement des qu'un cas connu existe (isNovelCase()
        // depend deja de t.rag_score, disponible juste apres ticket.set() ci-dessus).
        if (!this.isNovelCase()) {
          this.analyzeWithAI();
        }
      },
      error: () => {
        this.error.set('Ticket introuvable.');
        this.loading.set(false);
      },
    });
  }

  /** Etape 1 -> 2 : passe a l'ecran de cloture, ou le statut et les 3 colonnes
   *  (categorie/priorite/classification) sont modifiables ensemble. Le statut
   *  n'est pas demande a l'etape de revue : il est deja passe automatiquement a
   *  "Prise en Charge" des l'ouverture depuis la file d'approbation. */
  goToClosure(): void {
    this.step.set('cloture');
  }

  backToReview(): void {
    this.step.set('revue');
  }

  /** Categorie/priorite/classification/reponse client fixes -> ouvre le grand popup
   *  dedie a "Solution appliquee" (dernier sous-etape avant l'enregistrement). */
  openSolutionStep(): void {
    this.modalError.set(null);
    this.showSolutionModal.set(true);
  }

  backToClotureFields(): void {
    this.showSolutionModal.set(false);
    this.modalError.set(null);
  }

  /** Point d'entree du bouton "Enregistrer" (dans le popup Solution appliquee) : tous
   *  les champs sont deja fixes a ce stade — reste a decider le statut reel du ticket,
   *  ce qui se fait dans la modale (Tache 2.1), pas via un menu deroulant pre-rempli. */
  save(): void {
    const t = this.ticket();
    if (!t) return;
    this.error.set(null);
    this.success.set(null);
    this.modalError.set(null);
    if (!this.availableStatuts().length) {
      // Statut terminal (Resolu/Rejete) : rien a choisir, on enregistre juste les
      // corrections (categorie/priorite/...) sans changer le statut.
      this.performSave(t.statut);
      return;
    }
    this.showSolutionModal.set(false);
    this.showResolveConfirm.set(true);
  }

  /** Choix du statut final dans la modale — parmi les transitions valides depuis le
   *  statut actuel (availableStatuts()). Un passage a "Resolu" sur un cas nouveau
   *  exige une solution appliquee (meme regle que le backend) : si elle manque, on
   *  rouvre le popup Solution appliquee (plutot que d'afficher l'erreur dans la petite
   *  modale de statut, loin du champ concerne) avec le message d'erreur visible dessus. */
  pickStatut(s: Statut): void {
    const v = this.form.value;
    if (s === 'Résolu' && this.isNovelCase() && !(v.commentaire_interne ?? '').trim()) {
      this.showResolveConfirm.set(false);
      this.showSolutionModal.set(true);
      this.modalError.set(
        "Aucun cas similaire connu pour ce ticket : décrivez la solution appliquée ci-dessous avant de le marquer comme résolu.",
      );
      return;
    }
    this.showResolveConfirm.set(false);
    this.performSave(s);
  }

  cancelResolveConfirm(): void {
    this.showResolveConfirm.set(false);
    this.modalError.set(null);
    this.showSolutionModal.set(true);
  }

  /** Le statut est toujours decide via la modale de cloture : une fois enregistre,
   *  retour a la liste de tous les tickets (Tache 2.1). */
  private performSave(statut: Statut): void {
    const v = this.form.value;
    this.saving.set(true);
    const payload: ApproveTicketRequest = {
      statut,
      categorie_finale: v.categorie_finale ?? undefined,
      priorite_finale: v.priorite_finale ?? undefined,
      classification_finale: v.classification_finale ?? undefined,
      commentaire_client: v.commentaire_client ?? undefined,
      commentaire_interne: v.commentaire_interne ?? undefined,
      assigne_a: v.assigne_a ?? undefined,
    };
    this.ticketApi.approveTicket(this.ticket()!.id, payload).subscribe({
      next: () => {
        this.saving.set(false);
        this.router.navigate(['/admin/tickets']);
      },
      error: (err) => {
        this.saving.set(false);
        this.showResolveConfirm.set(false);
        this.error.set(err.error?.detail ?? 'Erreur lors de la mise à jour.');
      },
    });
  }

  /** Tâche 3 — assistant de triage IA : reformule les tickets similaires (ChromaDB)
   *  en français professionnel via un LLM local plutôt que d'afficher la résolution
   *  brute d'un seul cas. */
  analyzeWithAI(): void {
    if (!this.ticket()) return;
    this.synthLoading.set(true);
    this.synthText.set(null);
    this.exploreResult.set(null);
    this.exploreError.set(null);
    this.ticketApi.getRagSynthesis(this.ticket()!.id).subscribe({
      next: (r) => {
        this.synthLoading.set(false);
        this.synthText.set(r.text);
        this.synthSource.set(r.source);
      },
      error: () => {
        // Echec HTTP (pas juste Ollama indisponible — la degradation gracieuse vers un
        // recapitulatif brut est deja geree cote serveur avec un 200/source:"fallback").
        // On laisse synthText a null : le template retombe alors sur t.solution_rag,
        // plutot que d'afficher un message d'erreur avec l'UI d'exploration par ID
        // comme s'il s'agissait d'une synthese valide.
        this.synthLoading.set(false);
        this.synthText.set(null);
        this.synthSource.set(null);
      },
    });
  }

  /** Appel à l'action du LLM ("fournissez-moi l'ID du ticket") : affiche la
   *  procédure complète du ticket historique choisi par l'admin. */
  exploreTicket(): void {
    const raw = this.exploreId().trim().replace('#', '');
    const id = Number(raw);
    if (!raw || Number.isNaN(id)) {
      this.exploreError.set('Indiquez un ID de ticket valide.');
      return;
    }
    this.exploreLoading.set(true);
    this.exploreError.set(null);
    this.exploreResult.set(null);
    this.ticketApi.getMyTicketDetail(id).subscribe({
      next: (t) => {
        this.exploreLoading.set(false);
        this.exploreResult.set(t);
      },
      error: () => {
        this.exploreLoading.set(false);
        this.exploreError.set(`Ticket #${id} introuvable.`);
      },
    });
  }

  /** Envoie la question de l'admin + tout l'historique de la conversation — le contexte
   *  du ticket et des cas similaires est reconstruit cote serveur a chaque appel, jamais
   *  envoye par le client (cf. api/services/llm_service.py::chat_reply). */
  sendChatMessage(): void {
    const text = this.chatInput().trim();
    if (!text || this.chatLoading() || !this.ticket()) return;

    const history = [...this.chatMessages(), { role: 'user' as const, content: text }];
    this.chatMessages.set(history);
    this.chatInput.set('');
    this.chatLoading.set(true);

    this.ticketApi.chatAboutTicket(this.ticket()!.id, history).subscribe({
      next: (r) => {
        this.chatLoading.set(false);
        this.chatMessages.update((m) => [...m, { role: 'assistant', content: r.reply }]);
      },
      error: () => {
        this.chatLoading.set(false);
        this.chatMessages.update((m) => [
          ...m,
          { role: 'assistant', content: "Je n'ai pas pu répondre pour le moment. Réessayez." },
        ]);
      },
    });
  }

  refreshRag(): void {
    if (!this.ticket()) return;
    this.ticketApi.refreshRag(this.ticket()!.id).subscribe({
      next: (updated: any) => {
        this.ticket.update(t => t ? { ...t, solution_rag: updated.solution_rag, knowledge_rag: updated.knowledge_rag, rag_score: updated.rag_score } : t);
        this.success.set('Recommandation RAG rafraîchie.');
        // Le score/les candidats ont pu changer (ex: apres correction de categorie) —
        // re-declenche la synthese IA pour rester cohérent avec la suggestion affichee.
        if (!this.isNovelCase()) {
          this.analyzeWithAI();
        } else {
          this.synthText.set(null);
          this.synthSource.set(null);
        }
      },
      error: () => this.error.set('Erreur lors du rafraîchissement RAG.'),
    });
  }

  formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  confPct(c: number | null): number {
    return c != null ? Math.round(c * 100) : 0;
  }

  /** Initiales du demandeur pour la pastille de la carte, deux lettres au plus. */
  initiales(nom: string | null | undefined): string {
    const mots = (nom ?? '').trim().split(/\s+/).filter(Boolean);
    if (!mots.length) return '?';
    return (mots[0][0] + (mots[1]?.[0] ?? '')).toUpperCase();
  }

  statutLabel(s: string | null | undefined): string {
    if (!s) return '';
    return this.statutCfg[s as Statut]?.label ?? s;
  }

  confianceColor(c: number | null): string {
    return couleurConfiance(c);
  }
}
