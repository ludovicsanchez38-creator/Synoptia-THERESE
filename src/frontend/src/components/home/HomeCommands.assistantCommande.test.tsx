/**
 * B-636 (persona Sophie, c4) : « Produire » → « Créer une commande » empilait
 * deux composeurs. L'assistant se lançait par une commande `rfc` dont
 * l'exécution appelait `onStartRFC()` PUIS `onClose()` : la fermeture
 * annonçait `onGuidedPanelChange(false)` et la coque réaffichait le composeur
 * du chat sous celui de l'assistant. L'état « panneau guidé » doit suivre ce
 * qui est réellement affiché.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({
    commands: [],
    fetchCommands: vi.fn(),
    updateCommand: vi.fn(),
    deleteCommand: vi.fn(),
    isLoading: false,
  }),
}));

vi.mock('../rfc/RFCWizard', () => ({
  RFCWizard: ({ onClose }: { onClose: () => void }) => (
    <div data-testid="assistant-commande">
      <button type="button" onClick={onClose}>Fermer l’assistant</button>
    </div>
  ),
}));

import { HomeCommands } from './HomeCommands';

describe('B-636 : un seul composeur pendant l’assistant de création de commande', () => {
  it('tant que l’assistant est affiché, le panneau guidé reste annoncé actif', async () => {
    const surChangement = vi.fn();
    render(<HomeCommands onPromptSelect={() => {}} onGuidedPanelChange={surChangement} />);

    fireEvent.click(screen.getByRole('button', { name: /Produire/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Créer une commande/ }));
    expect(await screen.findByTestId('assistant-commande')).toBeInTheDocument();

    const dernier = surChangement.mock.calls.at(-1)?.[0];
    expect(dernier).toBe(true);
  });

  it('à la fermeture de l’assistant, le panneau guidé rend la main', async () => {
    const surChangement = vi.fn();
    render(<HomeCommands onPromptSelect={() => {}} onGuidedPanelChange={surChangement} />);

    fireEvent.click(screen.getByRole('button', { name: /Produire/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Créer une commande/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Fermer l’assistant/ }));

    expect(screen.queryByTestId('assistant-commande')).toBeNull();
    expect(surChangement.mock.calls.at(-1)?.[0]).toBe(false);
  });
});
