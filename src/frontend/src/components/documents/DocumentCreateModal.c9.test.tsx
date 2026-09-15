/**
 * B-765 (cycle 9) : pendant la création, « Annuler » restait actif et la
 * fermeture n'empêchait pas onCreated d'ouvrir l'atelier une fois la réponse
 * arrivée. Pendant l'appel, la modale ne se ferme pas ; une fois créée, elle
 * n'ouvre l'atelier qu'une fois.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({ listProjects: vi.fn().mockResolvedValue([]) }));

import { useDocumentStore } from '../../stores/documentStore';
import { DocumentCreateModal } from './DocumentCreateModal';

describe('DocumentCreateModal - B-765, la création en cours ne se laisse pas annuler', () => {
  beforeEach(() => vi.clearAllMocks());

  it('désactive Annuler et Fermer pendant l’appel, puis ouvre l’atelier une seule fois', async () => {
    let resoudre!: (v: { id: string } | null) => void;
    const createDocument = vi.fn(() => new Promise<{ id: string } | null>((r) => { resoudre = r; }));
    useDocumentStore.setState({ createDocument: createDocument as never, clearError: vi.fn(), error: null } as never);
    const onClose = vi.fn();
    const onCreated = vi.fn();

    render(<DocumentCreateModal isOpen onClose={onClose} onCreated={onCreated} />);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Compte rendu' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));
    await waitFor(() => expect(createDocument).toHaveBeenCalledTimes(1));

    expect(screen.getByRole('button', { name: 'Annuler' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Fermer' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(onClose).not.toHaveBeenCalled();

    resoudre({ id: 'doc-1' });
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('doc-1'));
    expect(onCreated).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
