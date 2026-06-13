/**
 * Classification des erreurs d'API calendrier Google.
 *
 * BUG-109 / boucle « connexion expirée » (lcjp 12/06/2026) :
 * un 403 Google (API Calendar non activée dans le projet GCP) NE doit PAS être
 * traité comme une expiration de jeton. Sinon le CalendarPanel affiche la
 * bannière jaune « Connexion Google expirée », masque le message actionnable,
 * et chaque clic sur « Reconnecter » relance un OAuth qui réussit mais ne
 * corrige pas le 403 → boucle de reconnexion infinie.
 *
 * On garde la détection du radical « reconnect » car le vrai message backend
 * d'expiration ("OAuth credentials not found. Please reconnect your account.")
 * en dépend, mais on exclut explicitement les messages d'accès calendrier.
 */
export function isGoogleAuthError(message: string | null | undefined): boolean {
  const msg = (message || '').toLowerCase();
  // Un 403 d'accès calendrier (API non activée / accès non autorisé) n'est pas
  // une expiration de jeton : ne jamais déclencher la reconnexion sur ce cas.
  if (msg.includes('google calendar')) return false;
  return (
    msg.includes('expired') ||
    msg.includes('revoked') ||
    msg.includes('401') ||
    msg.includes('reconnect')
  );
}

export interface CalendarErrorAction {
  /** Message à afficher, ou `null` pour ne rien afficher (cache disponible). */
  error: string | null;
  /**
   * Nouvelle valeur de `needsReauth` à appliquer, ou `undefined` pour ne PAS y
   * toucher (préserver l'état courant sur une erreur générique).
   */
  needsReauth?: boolean;
}

/**
 * Décide quoi afficher pour une erreur d'API calendrier Google.
 *
 * Cas couverts :
 * - vraie expiration de jeton (401/expired/revoked/reconnect) → bannière de
 *   reconnexion (needsReauth=true) ;
 * - 403 d'accès calendrier (API non activée) → message actionnable ET on
 *   DÉSARME la bannière (needsReauth=false). Crucial (BUG-109 / lcjp) : un 403
 *   prouve que le jeton est valide (sinon ce serait un 401). Comme `needsReauth`
 *   est partagé avec l'email, une expiration Gmail antérieure peut l'avoir armé ;
 *   sans ce reset, la bannière jaune resterait, masquerait le message actionnable
 *   (rendu derrière `error && !needsReauth`) et entretiendrait la boucle de
 *   reconnexion ;
 * - autre erreur → message générique (ou `null` si du cache est disponible),
 *   sans toucher à `needsReauth`.
 */
export function classifyCalendarError(
  message: string | null | undefined,
  opts: { fallback: string; hasCache?: boolean },
): CalendarErrorAction {
  const msg = message || '';
  if (isGoogleAuthError(msg)) {
    return { error: 'Connexion Google expirée.', needsReauth: true };
  }
  if (msg.includes('Google Calendar')) {
    return { error: msg, needsReauth: false };
  }
  return { error: opts.hasCache ? null : opts.fallback };
}
