/**
 * Cloisonne la persistance du webview par dossier de donnees backend.
 *
 * Tauri conserve le meme origin `tauri://localhost` quel que soit
 * `THERESE_DATA_DIR`. Sans garde, un profil vierge rehydrate donc les
 * conversations, evenements, comptes et brouillons du profil precedent.
 */
import { purgeLocalPersistence } from './purgeLocalData';
import { migrateConsentOutbox } from './consentSync';

export const DATA_PROFILE_STORAGE_KEY = 'therese:data-profile';

function normalizeDataDir(dataDir: string): string {
  const trimmed = dataDir.trim();
  // Une barre finale ne change pas le dossier. Ne pas développer ~ ni
  // convertir les barres inverses : sous POSIX, ces noms peuvent être distincts.
  // C:/ est une racine de lecteur, C: un chemin relatif à ce lecteur.
  if (/^[a-z]:\/+$/i.test(trimmed)) return `${trimmed.slice(0, 2)}/`;
  return trimmed.replace(/\/+$/, '') || (trimmed ? '/' : '');
}

function isDefaultDataDir(dataDir: string): boolean {
  return /(^|[\\/])\.therese[\\/]?$/.test(dataDir.trim());
}

export type DataProfileIsolationResult = 'unchanged' | 'initialized' | 'switched';

export function isolateDataProfilePersistence(
  dataDir: string,
  options?: { reload?: () => void },
): DataProfileIsolationResult {
  const normalizedDataDir = normalizeDataDir(dataDir);
  if (!normalizedDataDir) {
    throw new Error('Le dossier de donnees backend est vide.');
  }

  const previousDataDir = localStorage.getItem(DATA_PROFILE_STORAGE_KEY);
  migrateConsentOutbox(previousDataDir || (isDefaultDataDir(normalizedDataDir) ? normalizedDataDir : ''));
  // Garder le marqueur existant : les accords en attente utilisent cette clé.
  if (previousDataDir !== null && normalizeDataDir(previousDataDir) === normalizedDataDir) return 'unchanged';

  // Migration de l'installation historique : avant ce garde, le marqueur
  // n'existait pas. Les caches presents appartiennent au profil canonique
  // ~/.therese. On les conserve uniquement pour ce profil par defaut.
  if (previousDataDir === null && isDefaultDataDir(normalizedDataDir)) {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, normalizedDataDir);
    return 'initialized';
  }

  // Le helper desarme aussi les ecritures Zustand debouncées et purge le
  // sessionStorage. Sans cela, `pagehide` reecrirait therese-chat au reload.
  purgeLocalPersistence({ profileSwitch: true });
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, normalizedDataDir);
  options?.reload?.();
  return 'switched';
}
