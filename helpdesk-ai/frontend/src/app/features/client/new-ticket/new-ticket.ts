import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { AuthService } from '../../../core/services/auth.service';
import { CreateTicketRequest } from '../../../models/ticket.models';

interface ChipOption {
  value: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-new-ticket',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './new-ticket.html',
  styleUrl: './new-ticket.css',
})
export class NewTicket {
  private fb = inject(FormBuilder);
  private ticketApi = inject(TicketApiService);
  private auth = inject(AuthService);
  private router = inject(Router);

  submitting = signal(false);
  errorMsg = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  // Options simples, sans jargon : servent a la fois a guider l'utilisateur
  // et a enrichir le texte envoye au modele de classification.
  equipements: ChipOption[] = [
    { value: 'Ordinateur ou portable', label: 'Ordinateur / portable', icon: 'computer' },
    { value: 'Imprimante', label: 'Imprimante', icon: 'print' },
    { value: 'Téléphone ou mobile', label: 'Téléphone / mobile', icon: 'smartphone' },
    { value: 'Logiciel ou application', label: 'Logiciel / application', icon: 'apps' },
    { value: 'Réseau, Wifi ou VPN', label: 'Réseau / Wifi / VPN', icon: 'wifi' },
    { value: '', label: 'Autre / je ne sais pas', icon: 'help' },
  ];

  delais: ChipOption[] = [
    { value: "À l'instant", label: "À l'instant", icon: 'bolt' },
    { value: "Depuis aujourd'hui", label: "Depuis aujourd'hui", icon: 'today' },
    { value: 'Depuis plusieurs jours', label: 'Depuis plusieurs jours', icon: 'date_range' },
  ];

  form = this.fb.group({
    titre: ['', [Validators.required, Validators.minLength(3)]],
    equipement: [''],
    depuisQuand: [''],
    details: [''],
  });

  submit(): void {
    this.errorMsg.set(null);
    this.successMsg.set(null);

    if (this.form.invalid) {
      this.errorMsg.set('Merci de décrire votre problème.');
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.value;
    const payload: CreateTicketRequest = {
      titre: (v.titre ?? '').trim(),
      description: this.composeDescription(),
      filiale: this.auth.currentUser()?.filiale ?? '',
      equipement: v.equipement || '',
    };

    this.submitting.set(true);
    this.ticketApi.createTicket(payload).subscribe({
      next: () => {
        this.submitting.set(false);
        this.successMsg.set('Votre demande a bien été envoyée !');
        this.form.reset({ titre: '', equipement: '', depuisQuand: '', details: '' });
        setTimeout(() => this.router.navigate(['/client/my-tickets']), 1200);
      },
      error: (err: any) => {
        this.submitting.set(false);
        this.errorMsg.set(`Une erreur est survenue (${err.status}). Veuillez réessayer.`);
      },
    });
  }

  selectChip(control: 'equipement' | 'depuisQuand', value: string): void {
    const current = this.form.get(control)?.value;
    this.form.patchValue({ [control]: current === value ? '' : value });
  }

  cancel(): void {
    this.router.navigate(['/client/home']);
  }

  /**
   * Compose une description en français naturel à partir des réponses guidées,
   * pour donner au modèle un texte proche de ce qu'il voit à l'entraînement
   * plutôt que des paires clé/valeur brutes.
   */
  private composeDescription(): string {
    const v = this.form.value;
    const parts: string[] = [];

    const details = (v.details ?? '').trim();
    if (details) parts.push(details);

    if (v.equipement) parts.push(`Équipement concerné : ${v.equipement}.`);
    if (v.depuisQuand) parts.push(`${v.depuisQuand}.`);

    return parts.length > 0 ? parts.join(' ') : 'Aucun détail supplémentaire fourni.';
  }
}
