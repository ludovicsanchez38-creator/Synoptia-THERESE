import { getCurrentWindow } from '@tauri-apps/api/window';
import { isTauri } from './utils';

/**
 * Démarre le déplacement de la fenêtre sans cadre depuis une barre custom.
 *
 * À brancher sur `onMouseDown` de la barre de titre de la coque. Ignore les
 * clics non gauches et ceux sur un élément interactif (bouton, lien, champ)
 * pour ne pas voler leurs clics. No-op hors Tauri (navigateur de dev).
 */
export function startWindowDrag(event: React.MouseEvent): void {
  if (event.button !== 0 || !isTauri()) return;
  const target = event.target as HTMLElement;
  if (target.closest('button, a, input, select, textarea, [role="button"]')) return;
  try {
    void getCurrentWindow().startDragging();
  } catch {
    // Fenêtre Tauri indisponible : déplacement ignoré.
  }
}
