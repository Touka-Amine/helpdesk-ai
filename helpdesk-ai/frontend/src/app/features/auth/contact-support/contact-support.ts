import { Component } from '@angular/core';
import { CONTACT_OTBS } from '../../../core/contact-otbs';

/**
 * Ligne « Besoin d'aide ? » en bas des ecrans d'authentification.
 *
 * C'est la que les coordonnees servent le plus : sans compte, sans mot de passe
 * ou avec un lien expire, on n'a aucun autre moyen de joindre le support.
 */
@Component({
  selector: 'app-contact-support',
  standalone: true,
  template: `
    <div class="mt-stack-lg text-center font-body-md text-[13px] text-on-surface-variant">
      <p class="text-outline">Besoin d'aide pour vous connecter ?</p>
      <!-- Pas de separateur : sur un ecran etroit les deux liens passent l'un sous
           l'autre et un point resterait seul en bout de ligne. -->
      <p class="mt-1 flex flex-wrap items-center justify-center gap-x-gutter gap-y-1">
        <a [href]="'tel:' + contact.telephoneLien" class="inline-flex items-center gap-1 hover:text-primary hover:underline">
          <span class="material-symbols-outlined text-primary text-[16px]">call</span>
          {{ contact.telephone }}
        </a>
        <a [href]="'mailto:' + contact.courriel" class="inline-flex items-center gap-1 hover:text-primary hover:underline">
          <span class="material-symbols-outlined text-primary text-[16px]">mail</span>
          {{ contact.courriel }}
        </a>
      </p>
    </div>
  `,
})
export class ContactSupport {
  contact = CONTACT_OTBS;
}
