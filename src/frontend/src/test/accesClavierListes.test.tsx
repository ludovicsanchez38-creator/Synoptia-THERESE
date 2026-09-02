/**
 * B-092 : supprimer un message ou naviguer dans les fichiers au clavier.
 *
 * Deux commandes n'étaient pas des commandes :
 *  - la corbeille d'une ligne d'e-mail était un `<span role="button">` SANS
 *    tabIndex, imbriqué DANS le bouton de la ligne (imbrication interdite, et
 *    aucun ordre de tabulation possible) ;
 *  - les lignes du navigateur de fichiers étaient des `<div>` animées sans
 *    rôle ni tabIndex : ni entrer dans un dossier, ni choisir un fichier.
 *
 * Ce que la garde vérifie, et qui ne dépend pas d'une feuille de style que
 * jsdom n'applique pas : la commande est un VRAI `<button>` (c'est lui qui
 * apporte l'activation à Entrée et à Espace), il prend le focus, et il n'est
 * pas imbriqué dans un autre bouton.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useEmailStore } from '../stores/emailStore';
import { EmailList } from '../components/email/EmailList';
import { FileBrowser } from '../components/files/FileBrowser';

const { deleteEmailMessageMock, listEmailMessagesMock, getWorkingDirectoryMock } = vi.hoisted(
  () => ({
    deleteEmailMessageMock: vi.fn(),
    listEmailMessagesMock: vi.fn(),
    getWorkingDirectoryMock: vi.fn(),
  }),
);

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<typeof import('../services/api')>('../services/api');
  return {
    ...actual,
    deleteEmailMessage: deleteEmailMessageMock,
    listEmailMessages: listEmailMessagesMock,
    classifyEmail: vi.fn(),
    getWorkingDirectory: getWorkingDirectoryMock,
    indexFile: vi.fn(),
  };
});

vi.mock('@tauri-apps/plugin-fs', () => ({
  readDir: vi.fn().mockResolvedValue([
    { name: 'Dossier', isDirectory: true },
    { name: 'note.txt', isDirectory: false },
  ]),
  stat: vi.fn().mockResolvedValue({ size: 42 }),
}));

vi.mock('@tauri-apps/api/path', () => ({
  homeDir: vi.fn().mockResolvedValue('/home/ludo'),
  resolve: vi.fn(async (...parts: string[]) => parts.join('/')),
}));

vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));

vi.mock('../lib/utils', async () => {
  const actual = await vi.importActual<typeof import('../lib/utils')>('../lib/utils');
  return { ...actual, isTauri: () => true };
});

function seedEmailStore() {
  useEmailStore.setState({
    messages: [
      {
        id: 'message-1',
        thread_id: 'thread-1',
        subject: 'Contrat à valider',
        from_email: 'camille@example.fr',
        from_name: 'Camille Martin',
        to_emails: ['ludo@synoptia.fr'],
        date: '2026-07-15T08:00:00Z',
        labels: ['INBOX'],
        is_read: true,
        is_starred: false,
        is_draft: false,
        has_attachments: false,
        snippet: 'Peux-tu valider le contrat ?',
        body_plain: null,
        body_html: null,
        priority: 'medium',
      },
    ],
    currentMessageId: null,
    currentLabelId: 'INBOX',
    searchQuery: '',
    refreshCounter: 0,
    needsReauth: false,
    hasMore: false,
    pageToken: null,
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  seedEmailStore();
  listEmailMessagesMock.mockResolvedValue({
    messages: [
      {
        id: 'message-1',
        threadId: 'thread-1',
        subject: 'Contrat à valider',
        from: 'Camille Martin <camille@example.fr>',
        date: '2026-07-15T08:00:00Z',
        labelIds: ['INBOX'],
        snippet: 'Peux-tu valider le contrat ?',
        is_read: true,
        is_starred: false,
      },
    ],
  });
  deleteEmailMessageMock.mockResolvedValue({});
  getWorkingDirectoryMock.mockResolvedValue(null);
});

describe('B-092 : les commandes des listes sont atteignables au clavier', () => {
  it('la corbeille d’une ligne d’e-mail est un bouton focalisable, hors du bouton de ligne', async () => {
    render(<EmailList accountId="account-1" />);
    await screen.findByText('Contrat à valider');

    const corbeille = screen.getByTitle('Supprimer');
    expect(corbeille.tagName).toBe('BUTTON');
    expect(corbeille.closest('button')).toBe(corbeille);

    corbeille.focus();
    expect(document.activeElement).toBe(corbeille);
  });

  it('chaque ligne du navigateur de fichiers offre un bouton focalisable', async () => {
    render(<FileBrowser />);

    const dossier = await screen.findByRole('button', { name: /Dossier/ });
    expect(dossier.tagName).toBe('BUTTON');
    dossier.focus();
    expect(document.activeElement).toBe(dossier);

    const fichier = await screen.findByRole('button', { name: /note\.txt/ });
    fichier.focus();
    expect(document.activeElement).toBe(fichier);
  });

  it('activer la ligne d’un dossier y entre', async () => {
    const { readDir } = await import('@tauri-apps/plugin-fs');
    render(<FileBrowser />);

    const dossier = await screen.findByRole('button', { name: /Ouvrir le dossier Dossier/ });
    dossier.focus();
    // Un vrai <button> convertit Entrée et Espace en activation ; jsdom ne le
    // fait pas, on vérifie donc que l'activation du bouton navigue bien.
    dossier.click();

    await waitFor(() => {
      expect(readDir).toHaveBeenCalledWith('/home/ludo/Dossier');
    });
  });
});
