import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TicketApiService } from '../../../api/ticket-api.service';
import { CreateTicketRequest, FILIALES } from '../../../models/ticket.models';

interface Exemple {
  label: string;
  titre: string;
  quand: string;
  message: string;
  actions: string;
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
  private router = inject(Router);

  filiales = FILIALES;
  submitting = signal(false);
  errorMsg = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  // Exemples adaptes au format questions, pour aider les utilisateurs peu a l'aise
  // avec la redaction d'un ticket a comprendre ce qui est attendu dans chaque champ.
  exemples: Exemple[] = [
    { label: '— Saisie libre —', titre: '', quand: '', message: '', actions: '' },
    {
      label: "Outlook ne s'ouvre plus",
      titre: "Impossible d'ouvrir Outlook",
      quand: 'Ce matin, vers 9h',
      message: '« Outlook ne peut pas se connecter au serveur »',
      actions: "J'ai redémarré mon ordinateur, mais rien n'a changé.",
    },
    {
      label: 'VPN ne se connecte pas',
      titre: 'Problème de connexion VPN',
      quand: 'Depuis hier soir 18h',
      message: "« Échec d'authentification »",
      actions: "J'ai ressaisi mon mot de passe, redémarré la box, testé en 4G.",
    },
    {
      label: 'Imprimante bloquée',
      titre: "L'imprimante du bureau ne répond plus",
      quand: 'Depuis ce matin 8h30',
      message: '« Hors ligne »',
      actions: "J'ai éteint et rallumé l'imprimante, vérifié les câbles.",
    },
  ];

  form = this.fb.group({
    exemple: [this.exemples[0].label],
    titre: ['', [Validators.required, Validators.minLength(5)]],
    quand: [''],
    message: [''],
    actions: [''],
    filiale: [FILIALES[0], Validators.required],
  });

  appliquerExemple(label: string): void {
    const ex = this.exemples.find((e) => e.label === label) ?? this.exemples[0];
    this.form.patchValue({
      titre: ex.titre,
      quand: ex.quand,
      message: ex.message,
      actions: ex.actions,
    });
  }

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

  private composeDescription(): string {
    const v = this.form.value;
    const quand = (v.quand ?? '').trim() || 'Non précisé';
    const message = (v.message ?? '').trim() || 'Aucun message indiqué';
    const actions = (v.actions ?? '').trim() || 'Aucune action indiquée';
    return `Depuis quand ? ${quand}\nMessage d'erreur : ${message}\nActions déjà tentées : ${actions}`;
  }

  private resetForm(): void {
    this.form.reset({
      exemple: this.exemples[0].label,
      titre: '',
      quand: '',
      message: '',
      actions: '',
      filiale: FILIALES[0],
    });
  }
}
