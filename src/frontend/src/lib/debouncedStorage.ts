/**
 * US-010 : stockage localStorage débouncé pour le middleware persist de Zustand.
 *
 * Pendant le streaming, chaque flush de phrase déclenche un set() du store,
 * donc une sérialisation JSON de TOUTES les conversations vers localStorage.
 * Ce wrapper coalesce les écritures : au plus une écriture par fenêtre de
 * `delayMs`, flush forcé à la lecture (cohérence) et au déchargement de la
 * page (pas de perte de la dernière écriture).
 */

// BUG-153 (F1 revue) : pendant la purge RGPD, le flush de fermeture
// (pagehide, déclenché par le reload de la purge) RÉÉCRIVAIT les écritures
// en attente après la suppression des clés. Kill switch global : la purge
// désarme toutes les instances et coupe toute écriture jusqu'au reload.
let persistenceDisabled = false;
const instances: Array<() => void> = [];

export function discardAllPendingWrites(): void {
  persistenceDisabled = true;
  for (const discard of instances) discard();
}

/** Réservé aux tests : réarme la persistance (en prod, seul le reload le fait). */
export function __resetPersistenceForTests(): void {
  persistenceDisabled = false;
  instances.length = 0;
}

/**
 * Le stockage du navigateur, s'il existe encore.
 *
 * Une écriture différée peut se déclencher APRÈS la disparition de sa cible :
 * un environnement de test démonté, un contexte sans stockage, un navigateur
 * qui refuse l'accès (fenêtre privée, données de site bloquées) où le simple
 * accesseur lève. Trouvé par la CI de la 0.54.0 : les 1075 tests passaient et
 * vitest sortait quand même en 1 sur un `ReferenceError` hors de tout test.
 *
 * Rendre nul plutôt que lever : une écriture perdue est un désagrément, une
 * exception non capturée casse la fenêtre entière.
 */
function stockage(): Storage | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage;
  } catch {
    return null;
  }
}

export function createDebouncedStorage(delayMs = 400): Storage {
  let timer: ReturnType<typeof setTimeout> | null = null;
  // Map par clé (revue adversariale : un pending unique perdait la 1re
  // écriture si un second store adoptait le même wrapper)
  const pending = new Map<string, string>();

  const discard = () => {
    pending.clear();
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  };
  instances.push(discard);

  const flush = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    if (persistenceDisabled) {
      pending.clear();
      return;
    }
    const cible = stockage();
    if (cible) {
      for (const [key, value] of pending) {
        cible.setItem(key, value);
      }
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
      return stockage()?.getItem(key) ?? null;
    },
    setItem(key: string, value: string): void {
      if (persistenceDisabled) return;
      pending.set(key, value);
      if (!timer) {
        timer = setTimeout(flush, delayMs);
      }
    },
    removeItem(key: string): void {
      pending.delete(key);
      stockage()?.removeItem(key);
    },
    get length(): number {
      return stockage()?.length ?? 0;
    },
    clear(): void {
      pending.clear();
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      stockage()?.clear();
    },
    key(index: number): string | null {
      return stockage()?.key(index) ?? null;
    },
  };
}
