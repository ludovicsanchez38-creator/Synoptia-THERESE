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
  // Une barre finale ne change pas le dossier. Ne pas développer ~ ni
  // convertir les barres inverses : sous POSIX, ces noms peuvent être distincts.
  // C:/ est une racine de lecteur, C: un chemin relatif à ce lecteur.
  if (/^[a-z]:\/+$/i.test(dataDir)) return `${dataDir.slice(0, 2)}/`;
  return dataDir.replace(/\/+$/, '') || (dataDir ? '/' : '');
}

function isDefaultDataDir(dataDir: string): boolean {
  return /(^|[\\/])\.therese[\\/]?$/.test(dataDir);
}

export type DataProfileIsolationResult = 'unchanged' | 'initialized' | 'switched';

export function isolateDataProfilePersistence(
  dataDir: string,
  options?: { reload?: () => void; canonicalDataDir?: string; verifiedAliases?: string[]; profileIdentity?: string },
): DataProfileIsolationResult {
  const normalizedDataDir = normalizeDataDir(options?.canonicalDataDir ?? dataDir);
  if (!normalizedDataDir) {
    throw new Error('Le dossier de donnees backend est vide.');
  }

  const previousDataDir = localStorage.getItem(DATA_PROFILE_STORAGE_KEY);
  // Le marqueur et la file portent désormais l'identité observée à leur
  // création. Résoudre aujourd'hui un ancien chemin ne prouve pas sa cible hier.
  const currentProfile = options?.profileIdentity ?? normalizedDataDir;
  // Le dossier historique peut être un lien : son chemin configuré garde la
  // règle de migration, son identité canonique sert aux nouvelles écritures.
  const historicalProfile = !options?.profileIdentity && isDefaultDataDir(normalizeDataDir(dataDir));
  migrateConsentOutbox(previousDataDir || (historicalProfile ? normalizedDataDir : ''));
  const sameProfile = (id: string) => options?.profileIdentity
    ? id === currentProfile
    : normalizeDataDir(id) === normalizedDataDir
      && (options?.verifiedAliases === undefined || options.verifiedAliases.includes(id));
  const unchanged = previousDataDir !== null && sameProfile(previousDataDir);
  // Garder le marqueur courant, mais reprendre aussi les files conservées
  // sous une ancienne graphie lors d'un aller-retour par un autre profil.
  reconcileConsentOutboxes(
    unchanged ? previousDataDir : currentProfile,
    storedDataProfiles().filter(sameProfile),
  );
  if (unchanged) return 'unchanged';

  // Migration de l'installation historique : avant ce garde, le marqueur
  // n'existait pas. Les caches presents appartiennent au profil canonique
  // ~/.therese. On les conserve uniquement pour ce profil par defaut.
  if (previousDataDir === null && historicalProfile) {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, currentProfile);
    return 'initialized';
  }

  // Le helper desarme aussi les ecritures Zustand debouncées et purge le
  // sessionStorage. Sans cela, `pagehide` reecrirait therese-chat au reload.
  purgeLocalPersistence({ profileSwitch: true });
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, currentProfile);
  options?.reload?.();
  return 'switched';
}
