import { Component, inject, signal } from '@angular/core';
import { RouterOutlet, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';
import { PiedPage } from '../pied-page/pied-page';

interface Notification {
  id: number;
  message: string;
  statut: string;
}

@Component({
  selector: 'app-client-layout',
  standalone: true,
  imports: [RouterOutlet, RouterModule, CommonModule, PiedPage],
  templateUrl: './client-layout.html',
  styleUrl: './client-layout.css',
})
export class ClientLayout {
  private authService = inject(AuthService);
  theme = inject(ThemeService);

  user = this.authService.currentUser();
  notifOpen = signal(false);

  // ⚠️ Mock — à remplacer par un vrai appel /tickets/me + comparaison de statuts
  notifications = signal<Notification[]>([
    { id: 4, message: "Ticket #0004 passé à Validé", statut: 'success' },
    { id: 5, message: "Ticket #0005 passé à En attente", statut: 'warning' },
  ]);

  toggleNotif(): void {
    this.notifOpen.set(!this.notifOpen());
  }

  initials(): string {
    const name = this.user?.nom || this.user?.email || '?';
    return name.charAt(0).toUpperCase();
  }

  logout(): void {
    this.authService.logout();
  }
}