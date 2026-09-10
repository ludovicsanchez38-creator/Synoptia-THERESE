/**
 * Cycle 6, lecteur D86 (HomeCommands.tsx) : « Déplacer » et « Supprimer »
 * d'une commande perso vivaient dans un conteneur `hidden group-hover:flex`
 * (display:none hors survol). Au clavier, ces actions n'existaient pas.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({
    commands: [{
      id: 'user-relance', name: 'relance', description: 'Relancer un client', icon: 'mail', category: 'production',
      source: 'user', is_editable: true, show_on_home: true, show_in_slash: true, sort_order: 1,
    }],
    fetchCommands: vi.fn(),
    updateCommand: vi.fn(),
    deleteCommand: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

import { HomeCommands } from './HomeCommands';

describe('D86 : les actions d’une commande perso existent hors survol', () => {
  it('« Déplacer » et « Supprimer » sont des boutons nommés, dans un conteneur qui n’est pas display:none', async () => {
    render(<HomeCommands onPromptSelect={() => {}} />);
    fireEvent.click(screen.getByRole('button', { name: /Produire/ }));
    // AnimatePresence mode="wait" : la catégorie s'affiche après la sortie de la grille.
    const deplacer = await screen.findByRole('button', { name: 'Déplacer' });
    const supprimer = screen.getByRole('button', { name: 'Supprimer' });
    for (const bouton of [deplacer, supprimer]) {
      expect(bouton.closest('.hidden')).toBeNull();
    }
  });

  it('Grok 0.70.0 P2 : invisibles hors survol, les actions ne sont pas cliquables dans le vide', async () => {
    render(<HomeCommands onPromptSelect={() => {}} />);
    fireEvent.click(screen.getByRole('button', { name: /Produire/ }));
    const deplacer = await screen.findByRole('button', { name: 'Déplacer' });
    const conteneur = deplacer.closest('.opacity-0') as HTMLElement | null;
    expect(conteneur).not.toBeNull();
    expect(conteneur?.className).toMatch(/\bpointer-events-none\b/);
    expect(conteneur?.className).toMatch(/group-hover\/cmd:pointer-events-auto/);
    expect(conteneur?.className).toMatch(/focus-within:pointer-events-auto/);
  });
});
