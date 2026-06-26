import { TicketCategory } from './ticket.models';

// ⚠️ Forme exacte de la réponse de GET /categories à confirmer : tableau nu
// TicketCategory[] ou objet enveloppé { categories: [...] } ?

export type CategoriesResponse = TicketCategory[];
