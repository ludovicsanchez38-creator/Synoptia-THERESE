/**
 * THÉRÈSE v2 - Sanitisation des messages d'erreur (US-008 / RES5-c)
 *
 * L'ErrorBoundary affichait `error.message` brut, qui peut contenir des chemins
 * absolus (arborescence du disque) et de très longues stack traces techniques.
 * On masque les chemins et on tronque, sans perdre l'info utile au diagnostic
 * (le détail complet reste dans la console via console.error).
 */
const MAX_LEN = 200;

export function sanitizeErrorMessage(message: string, maxLen = MAX_LEN): string {
  if (!message) return '';
  let cleaned = message
    // Chemins absolus macOS/Linux
    .replace(/(?:\/Users\/|\/home\/|\/var\/|\/tmp\/)[^\s]+/g, '[chemin]')
    // Chemins absolus Windows
    .replace(/[A-Za-z]:\\[^\s]+/g, '[chemin]');
  if (cleaned.length > maxLen) {
    cleaned = cleaned.slice(0, maxLen) + '…';
  }
  return cleaned;
}
