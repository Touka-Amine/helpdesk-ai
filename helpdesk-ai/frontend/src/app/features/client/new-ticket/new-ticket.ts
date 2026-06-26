import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { CreateTicketRequest } from '../../../models/ticket.models';

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

  submitting = signal(false);
  errorMsg = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  form = this.fb.group({
    titre: ['', [Validators.required, Validators.minLength(3)]],
    actions: [''],
    priorite: ['Modéré'],
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
      description: v.actions || 'Aucun détail supplémentaire fourni.',
      priorite: v.priorite ?? 'Modéré',
      filiale: '', // ⚠️ à confirmer : récupérer depuis le profil utilisateur connecté ?
      equipement: '',
    };

    this.submitting.set(true);
    this.ticketApi.createTicket(payload).subscribe({
      next: () => {
        this.submitting.set(false);
        this.successMsg.set('Votre demande a bien été envoyée !');
        this.form.reset({ titre: '', actions: '', priorite: 'Modéré' });
        setTimeout(() => this.router.navigate(['/client/my-tickets']), 1200);
      },
      error: (err: any) => {
        this.submitting.set(false);
        this.errorMsg.set(`Une erreur est survenue (${err.status}). Veuillez réessayer.`);
      },
    });
  }
}