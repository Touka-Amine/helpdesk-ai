import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) {
    router.navigate(['/auth/login']);
    return false;
  }
  if (!auth.isAdmin()) {
    router.navigate(['/client/my-tickets']);
    return false;
  }
  return true;
};
