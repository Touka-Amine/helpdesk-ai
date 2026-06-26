import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { MyTickets } from './my-tickets';
import { TicketApiService } from '../../../api/ticket-api.service';
import { Ticket } from '../../../models/ticket.models';
 
describe('MyTickets', () => {
  let component: MyTickets;
  let fixture: ComponentFixture<MyTickets>;
  let ticketApiSpy: jasmine.SpyObj<TicketApiService>;
 
  const mockTickets: Ticket[] = [
    {
      id: 1,
      client_name: 'Amine Toukabri',
      description: 'VPN inaccessible depuis ce matin',
      category: 'Réseau',
      confidence: 0.82,
      status: 'pending',
      created_at: '2026-06-01T10:00:00Z',
    },
  ];
 
  beforeEach(async () => {
    ticketApiSpy = jasmine.createSpyObj('TicketApiService', ['getMyTickets']);
 
    await TestBed.configureTestingModule({
      imports: [MyTickets],
      providers: [{ provide: TicketApiService, useValue: ticketApiSpy }],
    }).compileComponents();
  });
 
  it('charge et affiche les tickets au démarrage', () => {
    ticketApiSpy.getMyTickets.and.returnValue(of(mockTickets));
 
    fixture = TestBed.createComponent(MyTickets);
    component = fixture.componentInstance;
    fixture.detectChanges();
 
    expect(component.loading()).toBe(false);
    expect(component.tickets().length).toBe(1);
    expect(component.tickets()[0].category).toBe('Réseau');
  });
 
  it("affiche un message d'erreur si l'appel échoue", () => {
    ticketApiSpy.getMyTickets.and.returnValue(throwError(() => ({ status: 500 })));
 
    fixture = TestBed.createComponent(MyTickets);
    component = fixture.componentInstance;
    fixture.detectChanges();
 
    expect(component.loading()).toBe(false);
    expect(component.error()).toContain('Erreur 500');
  });
 
  it('bascule l’état déplié au clic sur toggleExpand', () => {
    ticketApiSpy.getMyTickets.and.returnValue(of(mockTickets));
 
    fixture = TestBed.createComponent(MyTickets);
    component = fixture.componentInstance;
    fixture.detectChanges();
 
    expect(component.isExpanded(1)).toBe(false);
    component.toggleExpand(1);
    expect(component.isExpanded(1)).toBe(true);
    component.toggleExpand(1);
    expect(component.isExpanded(1)).toBe(false);
  });
});