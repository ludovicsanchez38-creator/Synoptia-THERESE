import { useSyncExternalStore } from 'react';

const KEY = 'therese-auto-update-check';
const CHANGED = 'therese:auto-update-check-changed';

export function automaticUpdateChecks(): boolean {
  try { return localStorage.getItem(KEY) !== 'false'; }
  catch { return false; }
}

export function setAutomaticUpdateChecks(enabled: boolean): void {
  localStorage.setItem(KEY, String(enabled));
  window.dispatchEvent(new Event(CHANGED));
}

function subscribe(listener: () => void): () => void {
  window.addEventListener(CHANGED, listener);
  window.addEventListener('storage', listener);
  return () => {
    window.removeEventListener(CHANGED, listener);
    window.removeEventListener('storage', listener);
  };
}

export function useAutomaticUpdateChecks(): boolean {
  return useSyncExternalStore(subscribe, automaticUpdateChecks, () => false);
}

/** Dernière garde après les imports et vérifications asynchrones. */
export async function checkAutomaticUpdate() {
  if (!automaticUpdateChecks()) return null;
  const { check } = await import('@tauri-apps/plugin-updater');
  if (!automaticUpdateChecks()) return null;
  return check();
}
