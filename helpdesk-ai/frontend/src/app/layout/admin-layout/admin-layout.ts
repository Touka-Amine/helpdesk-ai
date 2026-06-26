import { Component, inject, signal } from '@angular/core';
import { RouterOutlet, RouterModule, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [RouterOutlet, RouterModule, CommonModule],
  templateUrl: './admin-layout.html',
  styleUrl: './admin-layout.css',
})
export class AdminLayout {
  private authService = inject(AuthService);
  private router = inject(Router);

  user = this.authService.currentUser();
  pendingCount = signal(5); // ⚠️ mock — à brancher sur /tickets/admin/all filtré par statut "En attente"
  pageTitle = signal('Tableau de bord — équipe IT'); // ⚠️ à rendre dynamique selon la route active si besoin

  initials(): string {
    const name = this.user?.nom || this.user?.email || '?';
    return name.charAt(0).toUpperCase();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}