import { getCurrentWindow } from '@tauri-apps/api/window';
import { isTauri } from '../../lib/utils';

/**
 * Pastilles de contrôle de fenêtre façon macOS, câblées à l'API Tauri.
 *
 * La coque 0.40 tourne dans une fenêtre `decorations: false` : la barre de
 * titre système est masquée, il faut donc recréer les contrôles. Rendu
 * uniquement sous Tauri ; dans un navigateur de dev, la vraie fenêtre système
 * gère déjà minimize/close, donc on n'affiche rien pour éviter une fausse
 * affordance (finding recette Ludo 16/07).
 */
export function WindowControls() {
  if (!isTauri()) return null;

  const run = (action: (win: ReturnType<typeof getCurrentWindow>) => Promise<unknown>) => () => {
    try {
      void action(getCurrentWindow());
    } catch {
      // Contexte sans fenêtre Tauri disponible : no-op.
    }
  };

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
