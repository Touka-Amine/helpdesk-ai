import { Routes } from '@angular/router';

import { ClientLayout } from './layout/client-layout/client-layout';
import { AdminLayout } from './layout/admin-layout/admin-layout';

import { Login } from './features/auth/login/login';
import { Register } from './features/auth/register/register';
import { ChangePassword } from './features/auth/change-password/change-password';
import { ForgotPassword } from './features/auth/forgot-password/forgot-password';
import { ResetPassword } from './features/auth/reset-password/reset-password';

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
import { Monitoring } from './features/admin/monitoring/monitoring';

import { authGuard, authGuardNoPasswordCheck } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'auth/login', pathMatch: 'full' },

  // ── Auth ──────────────────────────────────────────────────────────────────
  { path: 'auth/login',    component: Login },
  { path: 'auth/register', component: Register },
  { path: 'auth/change-password', component: ChangePassword, canActivate: [authGuardNoPasswordCheck] },
  // Parcours "mot de passe oublie" : ces deux ecrans sont ouverts sans session,
  // c'est precisement leur raison d'etre. Le jeton du courriel tient lieu de preuve.
  { path: 'auth/forgot-password', component: ForgotPassword },
  { path: 'auth/reset-password',  component: ResetPassword },

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
      { path: 'monitoring',     component: Monitoring },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    ],
  },

  { path: '**', redirectTo: 'auth/login' },
];
