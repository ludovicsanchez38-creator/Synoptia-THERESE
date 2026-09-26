/**
 * B-975 (cycle 11, 23/09/2026, ronde B du ZERO_CHECK) : après Échap dans
 * « Supprimer le projet ? » ou « Nouveau document », le focus tombait sur la
 * page (BODY) au lieu de revenir au bouton qui avait ouvert le dialogue.
 *
 * Même piège que B-278 : `autoFocus` est posé par React pendant le commit,
 * avant l'effet de `useDialogFocusTrap` ; au moment de sa capture, le focus
 * est déjà dans le dialogue, et le déclencheur n'est jamais mémorisé.
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useEffect, useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Project } from '../../services/api';

const api = vi.hoisted(() => ({ listProjects: vi.fn(), deleteProject: vi.fn() }));
vi.mock('../../services/api', () => api);
vi.mock('./ProjectModal', () => ({ ProjectModal: () => null }));

import { _clearEscapeHandlers, pushEscapeHandler, runTopEscapeHandler } from '../../lib/escapeStack';
import { useDocumentStore } from '../../stores/documentStore';
import { DocumentCreateModal } from '../documents/DocumentCreateModal';
import { ProjectsPanel } from './ProjectsPanel';

const PROJET: Project = {
  id: 'projet-b975', name: 'Chantier Ardent', description: null, contact_id: null, status: 'active',
  budget: null, notes: null, tags: null, created_at: '2026-09-23T10:00:00Z', updated_at: '2026-09-23T10:00:00Z',
};

describe('B-975 : Échap rend le focus au bouton qui a ouvert le dialogue', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listProjects.mockResolvedValue([PROJET]);
  });
  afterEach(() => { cleanup(); _clearEscapeHandlers(); });

  it('« Supprimer ce projet ? » : focus sur Annuler à l’ouverture, retour au bouton Supprimer après Échap', async () => {
    render(<ProjectsPanel />);
    const declencheur = await screen.findByRole('button', { name: `Supprimer ${PROJET.name}` });
    declencheur.focus();
    fireEvent.click(declencheur);
    const dialogue = screen.getByRole('dialog', { name: 'Supprimer ce projet ?' });
    await waitFor(() => expect(dialogue).toContainElement(document.activeElement as HTMLElement));

    act(() => { runTopEscapeHandler(); });
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Supprimer ce projet ?' })).toBeNull());
    await waitFor(() => expect(document.activeElement).toBe(declencheur));
  });

  it('« Nouveau document » : focus sur le titre à l’ouverture, retour au bouton après Échap', async () => {
    useDocumentStore.setState({ createDocument: vi.fn() as never, clearError: vi.fn(), error: null } as never);
    function Hote() {
      const [ouvert, setOuvert] = useState(false);
      // Échap vient de la pile unifiée, tenue par le parent (commentaire de la modale).
      useEffect(() => (ouvert ? pushEscapeHandler(() => setOuvert(false)) : undefined), [ouvert]);
      return (
        <>
          <button type="button" onClick={() => setOuvert(true)}>Nouveau document</button>
          <DocumentCreateModal isOpen={ouvert} onClose={() => setOuvert(false)} onCreated={vi.fn()} />
        </>
      );
    }
    render(<Hote />);
    const declencheur = screen.getByRole('button', { name: 'Nouveau document' });
    declencheur.focus();
    fireEvent.click(declencheur);
    await waitFor(() => expect(screen.getByLabelText(/Titre/)).toHaveFocus());

    act(() => { runTopEscapeHandler(); });
    await waitFor(() => expect(screen.queryByLabelText(/Titre/)).toBeNull());
    await waitFor(() => expect(document.activeElement).toBe(declencheur));
  });
});
