/**
 * Cloisonne la persistance du webview par dossier de donnees backend.
 *
 * Tauri conserve le meme origin `tauri://localhost` quel que soit
 * `THERESE_DATA_DIR`. Sans garde, un profil vierge rehydrate donc les
 * conversations, evenements, comptes et brouillons du profil precedent.
 */
import { purgeLocalPersistence } from './purgeLocalData';
import { migrateConsentOutbox, reconcileConsentOutboxes, storedDataProfiles } from './consentSync';

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
  options?: { reload?: () => void; canonicalDataDir?: string; verifiedAliases?: string[] },
): DataProfileIsolationResult {
  const normalizedDataDir = normalizeDataDir(options?.canonicalDataDir ?? dataDir);
  if (!normalizedDataDir) {
    throw new Error('Le dossier de donnees backend est vide.');
  }

  const previousDataDir = localStorage.getItem(DATA_PROFILE_STORAGE_KEY);
  // Le dossier historique peut être un lien : son chemin configuré garde la
  // règle de migration, son identité canonique sert aux nouvelles écritures.
  const historicalProfile = isDefaultDataDir(normalizeDataDir(dataDir));
  migrateConsentOutbox(previousDataDir || (historicalProfile ? normalizedDataDir : ''));
  const sameProfile = (id: string) => normalizeDataDir(id) === normalizedDataDir
    || options?.verifiedAliases?.includes(id) === true;
  const unchanged = previousDataDir !== null && sameProfile(previousDataDir);
  // Garder le marqueur courant, mais reprendre aussi les files conservées
  // sous une ancienne graphie lors d'un aller-retour par un autre profil.
  reconcileConsentOutboxes(
    unchanged ? previousDataDir : normalizedDataDir,
    storedDataProfiles().filter(sameProfile),
  );
  if (unchanged) return 'unchanged';

  // Migration de l'installation historique : avant ce garde, le marqueur
  // n'existait pas. Les caches presents appartiennent au profil canonique
  // ~/.therese. On les conserve uniquement pour ce profil par defaut.
  if (previousDataDir === null && historicalProfile) {
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
