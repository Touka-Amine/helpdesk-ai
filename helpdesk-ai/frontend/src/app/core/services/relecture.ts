/** Même rythme que le magasin des tickets de la console (tickets-store.ts). */
export const RELECTURE_MS = 15_000;

/**
 * Relance `lire` à intervalle régulier tant que l'onglet est visible, et tout de
 * suite quand l'utilisateur revient sur l'onglet.
 *
 * Sert aux écrans qui ne passent pas par le magasin partagé des tickets : la
 * liste des utilisateurs, et les écrans du demandeur. Sans cela, un nouveau
 * compte ou la réponse d'un technicien n'apparaissaient qu'en rechargeant la
 * page. Un onglet caché ne relit rien : personne ne regarde, et le retour sur
 * l'onglet déclenche de toute façon une lecture.
 *
 * Renvoie la fonction qui arrête tout, à appeler dans `ngOnDestroy`.
 */
export function relirePeriodiquement(lire: () => void, intervalleMs = RELECTURE_MS): () => void {
  const siVisible = () => {
    if (document.visibilityState === 'visible') lire();
  };
  const minuteur = setInterval(siVisible, intervalleMs);
  document.addEventListener('visibilitychange', siVisible);
  window.addEventListener('focus', siVisible);
  return () => {
    clearInterval(minuteur);
    document.removeEventListener('visibilitychange', siVisible);
    window.removeEventListener('focus', siVisible);
  };
}
