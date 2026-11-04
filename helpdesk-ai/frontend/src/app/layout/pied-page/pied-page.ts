import { Component } from '@angular/core';
import { CONTACT_OTBS } from '../../core/contact-otbs';

/**
 * Pied de page de l'espace demandeur.
 *
 * Il suit le contenu et defile avec lui, plutot que de rester colle en bas de
 * l'ecran : il ne prend aucune hauteur aux listes. L'espace admin n'en a pas,
 * l'admin etant lui-meme le support.
 */
@Component({
  selector: 'app-pied-page',
  standalone: true,
  template: `
    <footer class="mx-container-padding mb-stack-md pt-stack-md pb-stack-sm border-t border-outline-variant/40
                   flex flex-wrap items-center justify-between gap-x-gutter gap-y-stack-md
                   font-body-md text-[13px] text-on-surface-variant">
      <div class="flex items-center gap-2 text-outline">
        <span class="w-7 h-7 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-[16px]">support_agent</span>
        </span>
        <span class="font-semibold text-on-surface">Helpdesk AI</span>
        <span aria-hidden="true">·</span>
        <span>© {{ annee }} OTBS</span>
      </div>

      <address class="not-italic flex flex-wrap items-center gap-x-gutter gap-y-stack-sm">
        <span class="inline-flex items-center gap-1.5">
          <span class="material-symbols-outlined text-primary text-[18px]">location_on</span>
          {{ contact.adresse }}
        </span>
        <a [href]="'tel:' + contact.telephoneLien"
          class="inline-flex items-center gap-1.5 text-on-surface hover:text-primary hover:underline">
          <span class="material-symbols-outlined text-primary text-[18px]">call</span>
          {{ contact.telephone }}
        </a>
        <a [href]="'mailto:' + contact.courriel"
          class="inline-flex items-center gap-1.5 text-on-surface hover:text-primary hover:underline">
          <span class="material-symbols-outlined text-primary text-[18px]">mail</span>
          {{ contact.courriel }}
        </a>
      </address>
    </footer>
  `,
})
export class PiedPage {
  contact = CONTACT_OTBS;
  annee = new Date().getFullYear();
}
