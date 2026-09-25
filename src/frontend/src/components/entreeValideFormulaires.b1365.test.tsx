/**
 * B-1365 : Entrée valide les formulaires Contact, Projet, Section et Dossier
 * (voir lib/entreeValide.ts).
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers } from '../lib/escapeStack';
import { useContactsStore } from '../stores/contactsStore';
import { ContactModal } from './memory/ContactModal';
import { OutlineTree } from './documents/OutlineTree';

describe('B-1365 : Entrée valide les formulaires', () => {
  beforeEach(() => _clearEscapeHandlers());
  afterEach(() => cleanup());

  it('nouveau contact : Entrée dans « Prénom » crée la fiche', async () => {
    const createContact = vi.fn().mockResolvedValue(undefined);
    useContactsStore.setState({ createContact });
    render(<ContactModal isOpen onClose={vi.fn()} contact={null} />);
    const prenom = screen.getByLabelText(/Prénom/);
    fireEvent.change(prenom, { target: { value: 'Zoé' } });
    fireEvent.keyDown(prenom, { key: 'Enter' });
    await waitFor(() => expect(createContact).toHaveBeenCalledTimes(1));
  });

  it('nouvelle section : Entrée dans le titre ajoute la section', () => {
    const onCreateSection = vi.fn();
    render(
      <OutlineTree
        sections={[]} activeSectionId={null} isLoading={false} error={null}
        onSelect={vi.fn()} onReorder={vi.fn()} onCreateSection={onCreateSection} onGenerateOutline={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /Ajouter une section/ }));
    const titre = screen.getByLabelText('Titre de la nouvelle section');
    fireEvent.change(titre, { target: { value: 'Contexte' } });
    fireEvent.keyDown(titre, { key: 'Enter' });
    expect(onCreateSection).toHaveBeenCalledTimes(1);
  });
});
