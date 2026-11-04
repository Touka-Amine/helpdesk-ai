import { Component, inject } from '@angular/core';
import { ThemeService } from '../../../core/services/theme.service';

/**
 * Bascule clair / sombre des ecrans d'authentification.
 *
 * Elle se pose juste sous le bouton de validation de chaque ecran, la ou le
 * regard se trouve deja, pour que le choix se fasse avant d'entrer ses
 * identifiants. Un composant plutot que du balisage recopie cinq fois : la
 * connexion, la creation de compte, le mot de passe oublie, la reinitialisation
 * et le changement de mot de passe affichent exactement le meme bouton.
 *
 * Le reglage est celui de toute l'application, le meme que celui de la barre
 * laterale une fois connecte, et il est retenu sur le poste.
 */
@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  template: `
    <button type="button" (click)="theme.toggle()"
      class="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg
             border border-outline-variant/50 bg-surface-container-lowest text-on-surface-variant
             font-label-md text-label-md hover:bg-surface-container transition-colors"
      [attr.aria-pressed]="theme.isDark()"
      [title]="theme.isDark() ? 'Passer en mode clair' : 'Passer en mode sombre'">
      <span class="material-symbols-outlined text-[18px]">{{ theme.isDark() ? 'light_mode' : 'dark_mode' }}</span>
      {{ theme.isDark() ? 'Mode clair' : 'Mode sombre' }}
    </button>
  `,
})
export class ThemeToggle {
  theme = inject(ThemeService);
}
