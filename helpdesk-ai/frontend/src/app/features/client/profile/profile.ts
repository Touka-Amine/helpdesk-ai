import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { FILIALES } from '../../../models/ticket.models';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class Profile implements OnInit {
  private authService = inject(AuthService);
  private fb = inject(FormBuilder);

  filiales = FILIALES;
  saving = signal(false);
  saveMsg = signal<string | null>(null);
  photoUrl = signal<string | null>(null); // ⚠️ pas d'upload réel branché encore

  form = this.fb.group({
    nom: [''],
    email: ['', [Validators.required, Validators.email]],
    telephone: [''],
    filiale: [FILIALES[0]],
  });

  ngOnInit(): void {
    const u = this.authService.currentUser();
    if (u) {
      this.form.patchValue({
        nom: u.nom ?? '',
        email: u.email,
        // ⚠️ telephone / filiale absents de CurrentUser actuellement — à ajouter
        // une fois que /auth/me ou /tickets/me renvoie ces champs
      });
    }
  }

  initials(): string {
    const v = this.form.get('nom')?.value || this.form.get('email')?.value || '?';
    return v.charAt(0).toUpperCase();
  }

  onPhotoSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    // ⚠️ Aperçu local seulement — aucun upload réel tant que l'endpoint backend n'existe pas
    const reader = new FileReader();
    reader.onload = () => this.photoUrl.set(reader.result as string);
    reader.readAsDataURL(file);
  }

  save(): void {
    this.saving.set(true);
    this.saveMsg.set(null);
    // ⚠️ Pas d'appel réseau réel — endpoint PATCH /auth/me ou /users/me non confirmé
    setTimeout(() => {
      this.saving.set(false);
      this.saveMsg.set('Modifications enregistrées (simulation — backend à brancher).');
    }, 600);
  }
}