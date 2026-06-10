/**
 * US-010 : stockage localStorage débouncé pour le middleware persist de Zustand.
 *
 * Pendant le streaming, chaque flush de phrase déclenche un set() du store,
 * donc une sérialisation JSON de TOUTES les conversations vers localStorage.
 * Ce wrapper coalesce les écritures : au plus une écriture par fenêtre de
 * `delayMs`, flush forcé à la lecture (cohérence) et au déchargement de la
 * page (pas de perte de la dernière écriture).
 */

export function createDebouncedStorage(delayMs = 400): Storage {
  let timer: ReturnType<typeof setTimeout> | null = null;
  // Map par clé (revue adversariale : un pending unique perdait la 1re
  // écriture si un second store adoptait le même wrapper)
  const pending = new Map<string, string>();

  const flush = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    for (const [key, value] of pending) {
      localStorage.setItem(key, value);
    }
    pending.clear();
  };

  if (typeof window !== 'undefined') {
    // beforeunload n'est pas fiable dans la WebView Tauri (WKWebView) :
    // pagehide et visibilitychange couvrent la fermeture/masquage réels.
    window.addEventListener('beforeunload', flush);
    window.addEventListener('pagehide', flush);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) flush();
    });
  }

  return {
    getItem(key: string): string | null {
      // Lecture cohérente : pousser l'écriture en attente d'abord
      if (pending.has(key)) flush();
      return localStorage.getItem(key);
    },
    setItem(key: string, value: string): void {
      pending.set(key, value);
      if (!timer) {
        timer = setTimeout(flush, delayMs);
      }
    },
    removeItem(key: string): void {
      pending.delete(key);
      localStorage.removeItem(key);
    },
    get length(): number {
      return localStorage.length;
    },
    clear(): void {
      pending.clear();
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      localStorage.clear();
    },
    key(index: number): string | null {
      return localStorage.key(index);
    },
  };
}
