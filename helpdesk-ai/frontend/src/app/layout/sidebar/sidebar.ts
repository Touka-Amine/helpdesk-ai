import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';

interface NavItem {
  label: string;
  icon: string;
  route: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatListModule],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  private authService = inject(AuthService);
  private router = inject(Router);

  navItems: NavItem[] = [
    { label: 'Mes tickets', icon: 'confirmation_number', route: '/client/my-tickets' },
    { label: 'Nouveau ticket', icon: 'add_circle', route: '/client/new-ticket' },
    { label: 'Mon profil', icon: 'person', route: '/client/profile' },
  ];

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}