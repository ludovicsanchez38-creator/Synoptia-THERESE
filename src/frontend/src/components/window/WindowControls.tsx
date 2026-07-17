import { getCurrentWindow } from '@tauri-apps/api/window';
import { isMacPlatform } from '../../lib/platform';
import { isTauri } from '../../lib/utils';

/**
 * Contrôles de fenêtre de la coque 0.40 (`decorations: false`).
 *
 * Revue 0.40 : les pastilles macOS s'affichaient telles quelles sur Windows et
 * Linux. Désormais chaque plateforme a sa convention :
 * - macOS : pastilles rouge/jaune/verte à GAUCHE de la barre ;
 * - Windows et Linux : réduire/agrandir/fermer avec glyphes à DROITE.
 *
 * La coque monte le composant aux deux extrémités avec `side` ; chaque instance
 * ne se rend que si la convention de la plateforme correspond. Rendu uniquement
 * sous Tauri ; dans un navigateur de dev, la vraie fenêtre système gère déjà
 * minimize/close, donc on n'affiche rien (finding recette Ludo 16/07).
 */
export function WindowControls({ side = 'left' }: { side?: 'left' | 'right' }) {
  if (!isTauri()) return null;
  const mac = isMacPlatform();
  if (mac !== (side === 'left')) return null;

  const run = (action: (win: ReturnType<typeof getCurrentWindow>) => Promise<unknown>) => () => {
    try {
      void action(getCurrentWindow());
    } catch {
      // Contexte sans fenêtre Tauri disponible : no-op.
    }
  };

  if (mac) {
    return (
      <div className="flex items-center gap-2" aria-label="Contrôles de la fenêtre">
        <button
          type="button"
          aria-label="Fermer la fenêtre"
          onClick={run((win) => win.close())}
          className="group h-3 w-3 rounded-full bg-[#FF5F57] transition-colors hover:bg-[#ff4136]"
        />
        <button
          type="button"
          aria-label="Réduire la fenêtre"
          onClick={run((win) => win.minimize())}
          className="group h-3 w-3 rounded-full bg-[#FEBC2E] transition-colors hover:bg-[#f5a623]"
        />
        <button
          type="button"
          aria-label="Agrandir ou restaurer la fenêtre"
          onClick={run((win) => win.toggleMaximize())}
          className="group h-3 w-3 rounded-full bg-[#28C840] transition-colors hover:bg-[#1faa35]"
        />
      </div>
    );
  }

  return (
    <div className="flex items-center" aria-label="Contrôles de la fenêtre">
      <button
        type="button"
        aria-label="Réduire la fenêtre"
        onClick={run((win) => win.minimize())}
        className="grid h-8 w-10 place-items-center rounded text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M0.5 5H9.5" stroke="currentColor" strokeWidth="1.2" />
        </svg>
      </button>
      <button
        type="button"
        aria-label="Agrandir ou restaurer la fenêtre"
        onClick={run((win) => win.toggleMaximize())}
        className="grid h-8 w-10 place-items-center rounded text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <rect x="0.6" y="0.6" width="8.8" height="8.8" stroke="currentColor" strokeWidth="1.2" />
        </svg>
      </button>
      <button
        type="button"
        aria-label="Fermer la fenêtre"
        onClick={run((win) => win.close())}
        className="grid h-8 w-10 place-items-center rounded text-text-muted transition-colors hover:bg-error-fill/90 hover:text-white"
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M0.8 0.8L9.2 9.2M9.2 0.8L0.8 9.2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}
