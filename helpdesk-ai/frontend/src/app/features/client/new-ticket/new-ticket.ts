import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { CreateTicketRequest, FILIALES } from '../../../models/ticket.models';

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
  private router = inject(Router);

  filiales = FILIALES;
  submitting = signal(false);
  errorMsg = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  form = this.fb.group({
    titre: ['', [Validators.required, Validators.minLength(5)]],
    quand: [''],
    message: [''],
    actions: [''],
    filiale: [FILIALES[0], Validators.required],
  });

  submit(): void {
    this.errorMsg.set(null);
    this.successMsg.set(null);

    if (this.form.invalid) {
      this.errorMsg.set('Merci de décrire le problème en au moins 5 caractères.');
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.value;
    const payload: CreateTicketRequest = {
      titre: (v.titre ?? '').trim(),
      description: this.composeDescription(),
      priorite: 'Modéré',
      filiale: v.filiale ?? '',
      equipement: '',
    };

    this.submitting.set(true);
    this.ticketApi.createTicket(payload).subscribe({
      next: () => {
        this.submitting.set(false);
        this.successMsg.set("Ticket envoyé avec succès ! L'équipe IT vous répondra rapidement.");
        this.resetForm();
        setTimeout(() => this.router.navigate(['/client/my-tickets']), 1200);
      },
      error: (err: any) => {
        this.submitting.set(false);
        this.errorMsg.set(`Erreur ${err.status}. Veuillez réessayer.`);
      },
    });
  }

  cancel(): void {
    this.router.navigate(['/client/home']);
  }

  // N'injecte que les reponses reellement fournies : un champ laisse vide ne doit
  // pas se traduire par un texte "Non precise" envoye tel quel au classifieur IA,
  // qui ne lit que ce champ description (pas le titre) pour predire la categorie.
  private composeDescription(): string {
    const v = this.form.value;
    const parts: string[] = [];

    const quand = (v.quand ?? '').trim();
    const message = (v.message ?? '').trim();
    const actions = (v.actions ?? '').trim();
    if (quand) parts.push(`Depuis quand ? ${quand}`);
    if (message) parts.push(`Message d'erreur : ${message}`);
    if (actions) parts.push(`Actions déjà tentées : ${actions}`);

    if (parts.length === 0) {
      return `${(v.titre ?? '').trim()}. Aucun détail complémentaire fourni par l'utilisateur.`;
    }
    return parts.join('\n');
  }

  private resetForm(): void {
    this.form.reset({
      titre: '',
      quand: '',
      message: '',
      actions: '',
      filiale: FILIALES[0],
    });
  }
}
