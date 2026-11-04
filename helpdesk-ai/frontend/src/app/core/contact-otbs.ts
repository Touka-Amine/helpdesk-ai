/**
 * Coordonnees d'OTBS affichees cote demandeur : pied de page, actions rapides,
 * relance d'un ticket et ecrans de connexion. Un seul endroit a modifier si
 * l'adresse du support change.
 */
export const CONTACT_OTBS = {
  adresse: '16, Rue des Entrepreneurs, 2035 Charguia II, Tunis – Tunisie',
  telephone: '(+216) 39 140 000',
  /** Forme attendue par un lien `tel:`, sans espaces ni parentheses. */
  telephoneLien: '+21639140000',
  courriel: 'contact.otbs@onetech-group.com',
} as const;
