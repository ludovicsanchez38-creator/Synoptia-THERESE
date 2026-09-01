/**
 * 01/09/2026 - Échap pendant la mise en route ne doit pas quitter THÉRÈSE.
 *
 * Trouvé par la boucle d'amélioration, confirmé dans le code : `handleClose`
 * valait `getCurrentWindow().close()` et était branché sur `onEscape` du piège
 * de focus. Aucune autre sortie clavier n'existait.
 *
 * Un nouvel utilisateur qui fait le geste réflexe de fermer une boîte de
 * dialogue quittait donc l'application entière, à son tout premier contact.
 *
 * Échap revient d'une étape, et ne fait rien sur la première.
 */
import { describe, expect, it, vi } from 'vitest';

const fenetre = vi.hoisted(() => ({ close: vi.fn(), minimize: vi.fn(), toggleMaximize: vi.fn() }));
vi.mock('@tauri-apps/api/window', () => ({ getCurrentWindow: () => fenetre }));

import { echapPendantLaMiseEnRoute } from './echapMiseEnRoute';

describe('Échap pendant la mise en route', () => {
  it('ne ferme jamais la fenêtre', () => {
    const reculer = vi.fn();
    echapPendantLaMiseEnRoute({ etape: 2, reculer, fermer: fenetre.close });
    expect(fenetre.close).not.toHaveBeenCalled();
  });

  it('revient d’une étape quand il y en a une avant', () => {
    const reculer = vi.fn();
    echapPendantLaMiseEnRoute({ etape: 2, reculer, fermer: fenetre.close });
    expect(reculer).toHaveBeenCalledTimes(1);
  });

  it('ne fait rien sur la première étape, plutôt que de quitter', () => {
    const reculer = vi.fn();
    echapPendantLaMiseEnRoute({ etape: 0, reculer, fermer: fenetre.close });
    expect(reculer).not.toHaveBeenCalled();
    expect(fenetre.close).not.toHaveBeenCalled();
  });
});
