import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthApiService } from '../api/auth-api.service';
import { MetadataApiService } from '../api/metadata-api.service';
import { PredictionApiService } from '../api/prediction-api.service';
import { TicketApiService } from '../api/ticket-api.service';

@Component({
  selector: 'app-test-api',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './test-api.html'
})
export class TestApi {
  // La variable manquante pour le HTML
  savedToken: string | null = null;
  apiResponse: any = null;

  constructor(
    private authApi: AuthApiService,
    private metadataApi: MetadataApiService,
    private predictionApi: PredictionApiService,
    private ticketApi: TicketApiService
  ) {}

  // --- La fonction manquante pour le Login ---
  testLogin() {
    this.apiResponse = 'Connexion en cours...';
    const payload = { email: "test@domain.com", password: "password123" }; // Adaptez selon votre backend
    
    this.authApi.login(payload).subscribe({
      next: (res: any) => {
        this.apiResponse = res;
        // On sauvegarde le token si la connexion réussit
        if(res && res.token) {
          this.savedToken = res.token;
          localStorage.setItem('token', res.token);
        }
      },
      error: (err) => this.apiResponse = { ERREUR: err.message, details: err.error }
    });
  }

  // --- Les fonctions existantes ---
  testCategories() {
    this.apiResponse = 'Chargement des catégories...';
    this.metadataApi.getCategories().subscribe({
      next: (res) => this.apiResponse = res,
      error: (err) => this.apiResponse = { ERREUR: err.message, details: err.error }
    });
  }

  testPrediction() {
    this.apiResponse = 'Analyse du ticket par l\'IA en cours...';
    const payload = { description: "Mon ordinateur ne s'allume plus et fait des bips." };
    this.predictionApi.predict(payload).subscribe({
      next: (res) => this.apiResponse = res,
      error: (err) => this.apiResponse = { ERREUR: err.message, details: err.error }
    });
  }

  // --- La fonction manquante pour les tickets ---
  testGetMyTickets() {
    this.apiResponse = 'Récupération des tickets...';
    this.ticketApi.getMyTickets().subscribe({
      next: (res) => this.apiResponse = res,
      error: (err) => this.apiResponse = { ERREUR: err.message, details: err.error }
    });
  }
}