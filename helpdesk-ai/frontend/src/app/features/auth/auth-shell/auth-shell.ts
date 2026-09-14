import { Component } from '@angular/core';

/**
 * Cadre commun aux ecrans d'authentification : panneau de marque OneTech a
 * gauche, contenu projete a droite.
 *
 * Pourquoi un composant et non du balisage recopie : le panneau reprend la
 * classe du bouton de validation (bg-primary-container). Duplique sur quatre
 * ecrans, ce fond finit par diverger des le premier ajustement. Ici il n'existe
 * qu'une fois.
 *
 * Sous 1024 px le panneau lateral n'a plus la place d'exister. Il ne disparait
 * pas pour autant : il devient un bandeau horizontal, de la meme couleur, pour
 * que l'identite soit presente a toutes les largeurs.
 */
@Component({
  selector: 'app-auth-shell',
  standalone: true,
  template: `
    <div class="min-h-screen w-full flex flex-col lg:flex-row">

      <!-- Bandeau compact — en dessous de 1024 px -->
      <div class="lg:hidden bg-primary-container flex items-center justify-center py-stack-lg">
        <div class="w-24 h-24 bg-white rounded-xl flex items-center justify-center p-3
                    shadow-[0_10px_30px_-8px_rgba(0,0,0,0.45)]">
          <img src="onetech-logo.png" alt="OneTech Business Solutions" class="w-full h-auto" />
        </div>
      </div>

      <!-- Panneau lateral — a partir de 1024 px -->
      <div class="hidden lg:flex lg:w-1/2 flex-col items-center justify-center
                  relative overflow-hidden bg-primary-container">
        <div class="w-52 h-52 bg-white rounded-2xl flex items-center justify-center p-6
                    shadow-[0_18px_50px_-12px_rgba(0,0,0,0.45)]">
          <img src="onetech-logo.png" alt="OneTech Business Solutions" class="w-full h-auto" />
        </div>
        <p class="text-on-primary-container font-body-md text-body-md mt-10 tracking-wide">
          Portail de support IT
        </p>
      </div>

      <!-- Contenu de l'ecran -->
      <div class="relative flex-1 flex items-center justify-center bg-surface px-4 py-stack-lg">
        <ng-content></ng-content>
      </div>
    </div>
  `,
})
export class AuthShell {}
