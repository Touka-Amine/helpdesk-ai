import { Component } from '@angular/core';
import { CommonModule } from '@angular/common'; 
import { FormsModule } from '@angular/forms'; 
import { TicketApiService } from '../../../api/ticket-api.service';

@Component({
  selector: 'app-new-ticket',
  standalone: true,
  imports: [CommonModule, FormsModule], 
  templateUrl: './new-ticket.html' 
})
export class NewTicket {                
  ticket = {
    title: '',
    description: ''
  };
  
  message = '';

  constructor(private ticketApi: TicketApiService) {}

  envoyerTicket() {
    this.message = 'Envoi en cours vers le serveur...';
    
    this.ticketApi.createTicket(this.ticket).subscribe({
      next: (res) => {
        this.message = '✅ Ticket créé avec succès !';
        this.ticket = { title: '', description: '' }; 
      },
      error: (err) => {
        this.message = '❌ Erreur : ' + (err.error?.detail || err.message);
      }
    });
  }
}