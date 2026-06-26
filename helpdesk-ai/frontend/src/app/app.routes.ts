import { Routes } from '@angular/router';

// --- IMPORTS DES LAYOUTS ---
import { ClientLayout } from './layout/client-layout/client-layout';
import { AdminLayout } from './layout/admin-layout/admin-layout'; // <-- L'IMPORT MANQUANT ÉTAIT ICI !

// --- IMPORTS CLIENT ---
import { NewTicket } from './features/client/new-ticket/new-ticket';
import { MyTickets } from './features/client/my-tickets/my-tickets';
import { Profile } from './features/client/profile/profile';
import { Home } from './features/client/home/home';

// --- IMPORTS ADMIN ---
import { Dashboard } from './features/admin/dashboard/dashboard';
import { TicketList } from './features/admin/ticket-list/ticket-list';
import { ApprovalQueue } from './features/admin/approval-queue/approval-queue';
import { Notifications } from './features/admin/notifications/notifications';
import { Users } from './features/admin/users/users';

export const routes: Routes = [
  // Redirection par défaut (Page d'accueil de l'application)
  { path: '', redirectTo: 'client/my-tickets', pathMatch: 'full' },
  
  // --- ESPACE CLIENT ---
  {
    path: 'client',
    component: ClientLayout,
    children: [
      { path: 'home', component: Home },
      { path: 'new-ticket', component: NewTicket },
      { path: 'my-tickets', component: MyTickets },
      { path: 'profile', component: Profile },
    ],
  },
  
  // --- ESPACE ADMIN ---
  {
    path: 'admin',
    component: AdminLayout,
    children: [
      { path: 'dashboard', component: Dashboard },
      { path: 'approval-queue', component: ApprovalQueue },
      { path: 'tickets', component: TicketList },
      { path: 'notifications', component: Notifications },
      { path: 'users', component: Users },
    ],
  },
];