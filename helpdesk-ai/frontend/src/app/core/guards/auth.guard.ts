import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  if (!auth.isAuthenticated()) {
    inject(Router).navigate(['/auth/login']);
    return false;
  }
  if (auth.needsPasswordChange()) {
    inject(Router).navigate(['/auth/change-password']);
    return false;
  }
  return true;
};

/** Utilisé uniquement par la route /auth/change-password : authentifié suffit, pas de re-redirection. */
export const authGuardNoPasswordCheck: CanActivateFn = () => {
  const auth = inject(AuthService);
  if (!auth.isAuthenticated()) {
    inject(Router).navigate(['/auth/login']);
    return false;
  }
  return true;
};
