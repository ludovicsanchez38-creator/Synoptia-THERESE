/**
 * J0 (31/07/2026) - Le panneau guidé doit rendre la main en se démontant.
 *
 * `HomeCommands` annonce `onGuidedPanelChange(true)` quand l'utilisateur ouvre
 * une commande guidée. La coque (`PrototypeChatSurface`) s'en sert pour MASQUER
 * le composeur pendant la saisie guidée.
 *
 * Le `false` n'était annoncé que par `handleClose`, c'est-à-dire par une
 * fermeture explicite. Or `HomeCommands` n'est monté que tant que la
 * conversation est VIDE (`MessageList.tsx:153`) : dès qu'un message y apparaît,
 * ou que l'utilisateur bascule sur une conversation existante, le composant est
 * démonté sans jamais rendre la main.
 *
 * Conséquence pour l'utilisateur : le composeur reste masqué et il ne peut plus
 * écrire du tout — il faut relancer l'application.
 */
import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { HomeCommands } from './HomeCommands';

vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({
    commands: [],
    fetchCommands: vi.fn(),
    updateCommand: vi.fn(),
    deleteCommand: vi.fn(),
    isLoading: false,
  }),
}));

describe('HomeCommands - reprise de la main sur le composeur', () => {
  it('annonce la fin du panneau guidé quand il est démonté', () => {
    const surChangement = vi.fn();
    const { unmount } = render(
      <HomeCommands onPromptSelect={() => {}} onGuidedPanelChange={surChangement} />
    );

    unmount();

    expect(surChangement).toHaveBeenCalledWith(false);
  });
});
