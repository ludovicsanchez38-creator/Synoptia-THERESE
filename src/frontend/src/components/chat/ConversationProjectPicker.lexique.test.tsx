/**
 * B-1367 (persona Hugo, cycle 13) : le même objet portait plusieurs noms.
 * Le rail dit « Projets », la conversation disait « Dossier de cette
 * conversation » ; l'absence de projet s'appelait « Documents généraux » dans
 * la conversation et « Aucun projet » dans le formulaire de document, pendant
 * que « Dossier synchronisé » désigne, dans l'écran du projet, un dossier du
 * disque. Un mot par objet : « Projet », et « Aucun projet » pour l'absence.
 * Le libellé garde ce qu'il promettait (C1) : les fichiers suivent le projet,
 * le carnet reste partagé.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  listProjects: vi.fn().mockResolvedValue([{ id: 'projet-a', name: 'API client Orion' }]),
  setConversationProject: vi.fn(),
  createConversation: vi.fn(),
}));
vi.mock('../../services/api', () => apiMocks);

import { ConversationProjectPicker } from './ConversationProjectPicker';

describe('B-1367 : le projet s’appelle projet', () => {
  it('le sélecteur nomme le projet, et l’absence « Aucun projet »', async () => {
    render(<ConversationProjectPicker conversationId="conv-1" projectId={null} />);
    const choix = await screen.findByRole('combobox', { name: /^Projet de cette conversation : fichiers rattachés, carnet partagé$/ });
    await waitFor(() => expect(screen.getByRole('option', { name: 'API client Orion' })).toBeInTheDocument());

    expect(screen.getByRole('option', { name: 'Aucun projet (documents généraux)' })).toBeInTheDocument();
    expect(choix.textContent).not.toMatch(/Dossier/);
  });

  it('un projet rattaché mais non relu se nomme aussi « projet »', async () => {
    apiMocks.listProjects.mockResolvedValueOnce([]);
    render(<ConversationProjectPicker conversationId="conv-1" projectId="projet-inconnu" />);

    expect(await screen.findByRole('option', { name: 'Projet rattaché (nom non lu)' })).toBeInTheDocument();
  });
});
