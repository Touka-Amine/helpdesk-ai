import { Component, OnDestroy, OnInit, effect, inject } from '@angular/core';
import { RouterOutlet, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { TicketsStore } from '../../core/services/tickets-store';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [RouterOutlet, RouterModule, CommonModule],
  templateUrl: './admin-layout.html',
  styleUrl: './admin-layout.css',
})
export class AdminLayout implements OnInit, OnDestroy {
  private authService = inject(AuthService);
  private store = inject(TicketsStore);
  theme = inject(ThemeService);

  user = this.authService.currentUser();

  /** Le compteur de la barre latérale suit le magasin : il se met à jour tout seul
   *  quand un client dépose un ticket, sans recharger l'application. */
  pendingCount = this.store.enAttente;

  /** Tickets arrivés depuis la dernière visite du journal. C'est ce que la cloche
   *  affiche, sur toutes les pages de la console. */
  nonVus = this.store.nonVus;

  private detacher?: () => void;
  private readonly titreDeBase = document.title;

  constructor() {
    // Le compteur passe dans le titre de l'onglet : un ticket qui arrive se voit
    // même quand l'administrateur travaille dans une autre fenêtre.
    effect(() => {
      const n = this.nonVus();
      document.title = n > 0 ? `(${n}) ${this.titreDeBase}` : this.titreDeBase;
    });
  }

  ngOnInit(): void {
    // La console garde la liste à jour tant qu'un écran d'administration est ouvert.
    this.detacher = this.store.suivre();
  }

  ngOnDestroy(): void {
    this.detacher?.();
  }

  initials(): string {
    const name = this.user?.prenom || this.user?.nom || this.user?.email || '?';
    return name.charAt(0).toUpperCase();
  }

  logout(): void {
    this.authService.logout();
  }
}
