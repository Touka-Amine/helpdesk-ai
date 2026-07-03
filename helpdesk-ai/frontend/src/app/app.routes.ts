import { Routes } from '@angular/router';

import { ClientLayout } from './layout/client-layout/client-layout';
import { AdminLayout } from './layout/admin-layout/admin-layout';

import { Login } from './features/auth/login/login';
import { Register } from './features/auth/register/register';

import { Home } from './features/client/home/home';
import { NewTicket } from './features/client/new-ticket/new-ticket';
import { MyTickets } from './features/client/my-tickets/my-tickets';
import { TicketDetailClient } from './features/client/ticket-detail/ticket-detail';
import { Profile } from './features/client/profile/profile';

import { Dashboard } from './features/admin/dashboard/dashboard';
import { TicketList } from './features/admin/ticket-list/ticket-list';
import { TicketDetail } from './features/admin/ticket-detail/ticket-detail';
import { ApprovalQueue } from './features/admin/approval-queue/approval-queue';
import { Notifications } from './features/admin/notifications/notifications';
import { Users } from './features/admin/users/users';

import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'client/my-tickets', pathMatch: 'full' },

  // ── Auth ──────────────────────────────────────────────────────────────────
  { path: 'auth/login',    component: Login },
  { path: 'auth/register', component: Register },

  // ── Espace client (auth requise) ──────────────────────────────────────────
  {
    path: 'client',
    component: ClientLayout,
    canActivate: [authGuard],
    children: [
      { path: 'home',         component: Home },
      { path: 'new-ticket',   component: NewTicket },
      { path: 'my-tickets',   component: MyTickets },
      { path: 'tickets/:id',  component: TicketDetailClient },
      { path: 'profile',      component: Profile },
      { path: '', redirectTo: 'my-tickets', pathMatch: 'full' },
    ],
  },

  // ── Espace admin (rôle admin requis) ──────────────────────────────────────
  {
    path: 'admin',
    component: AdminLayout,
    canActivate: [adminGuard],
    children: [
      { path: 'dashboard',      component: Dashboard },
      { path: 'approval-queue', component: ApprovalQueue },
      { path: 'tickets',        component: TicketList },
      { path: 'tickets/:id',    component: TicketDetail },
      { path: 'notifications',  component: Notifications },
      { path: 'users',          component: Users },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    ],
  },

  { path: '**', redirectTo: 'client/my-tickets' },
];
