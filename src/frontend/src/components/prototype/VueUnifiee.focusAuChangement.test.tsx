/**
 * B-1370 (personas Hugo et Zoé, cycle 13) : ⌘M depuis l'Accueil posait le
 * focus sur le titre « Contacts », mais ⌘T depuis Contacts et ⌘I depuis
 * Tâches le laissaient sur la page. La vue unifiée reste montée d'un écran à
 * l'autre ; son focus initial sur le titre ne jouait qu'au montage, et
 * l'élément focalisé de l'ancien écran disparaissait avec lui.
 */
import { act, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../tasks', () => ({ TasksPanel: () => <p>Tâches</p> }));
vi.mock('../invoices', () => ({ InvoicesPanel: () => <p>Factures</p> }));
vi.mock('../memory/MemoryPanel', () => ({
  MemoryPanel: () => <input aria-label="Rechercher un contact" />,
}));

import { PrototypeUnifiedViewCanvas } from './PrototypeUnifiedViewCanvas';

function titre() {
  return document.getElementById('prototype-unified-view-title');
}

describe('B-1370 : le focus suit le changement d’écran', () => {
  it('un focus perdu avec l’ancien écran revient au titre du nouveau', async () => {
    const { rerender } = render(<PrototypeUnifiedViewCanvas view="memory" onClose={() => {}} />);
    const champ = await screen.findByLabelText('Rechercher un contact');
    champ.focus();
    expect(document.activeElement).toBe(champ);

    await act(async () => {
      rerender(<PrototypeUnifiedViewCanvas view="tasks" onClose={() => {}} />);
    });

    expect(titre()?.textContent).toBe('Tâches');
    expect(document.activeElement).toBe(titre());
  });

  it('un focus resté sur le rail (hors de la vue) rejoint le titre', async () => {
    const rail = document.createElement('button');
    document.body.appendChild(rail);
    const { rerender } = render(<PrototypeUnifiedViewCanvas view="tasks" onClose={() => {}} />);
    rail.focus();

    await act(async () => {
      rerender(<PrototypeUnifiedViewCanvas view="invoices" onClose={() => {}} />);
    });

    expect(document.activeElement).toBe(titre());
    rail.remove();
  });

  it('un focus posé dans le nouvel écran n’est pas repris', async () => {
    const { rerender } = render(<PrototypeUnifiedViewCanvas view="tasks" onClose={() => {}} />);
    const retour = document.querySelector<HTMLButtonElement>('button[aria-label="Revenir à l’écran précédent"]');
    retour?.focus();

    await act(async () => {
      rerender(<PrototypeUnifiedViewCanvas view="invoices" onClose={() => {}} />);
    });

    expect(document.activeElement).toBe(retour);
  });
});
