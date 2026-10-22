import { act, fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { DocumentWorkspace } from './DocumentWorkspace';
import { useDocumentStore } from '../../stores/documentStore';
import * as api from '../../services/api/documents';
vi.mock('../../services/api/documents', async (original) => ({ ...await original<typeof import('../../services/api/documents')>(), getDocument: vi.fn() }));
it('B-1064 : une erreur de lecture annonce un échec et permet de réessayer', async () => {
  vi.mocked(api.getDocument).mockRejectedValue(new Error('Lecture impossible (500)'));
  useDocumentStore.setState({ currentDocument: null, isLoading: false, error: null });
  render(<DocumentWorkspace documentId="document-factice" onBack={vi.fn()} />);
  await act(() => useDocumentStore.getState().openDocument('document-factice'));
  expect(screen.getByRole('alert')).toHaveTextContent('Lecture impossible');
  expect(screen.queryByText('Chargement du document...')).toBeNull();
  vi.mocked(api.getDocument).mockClear();
  fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
  expect(api.getDocument).toHaveBeenCalledWith('document-factice');
});

it.each(['Erreur réseau', 'Réponse 500', 'Réponse 502', 'Document supprimé', 'Accès refusé', 'Délai dépassé', 'Service indisponible', 'Réponse illisible', 'Connexion interrompue', 'Lecture interrompue'])('Rejeu B-1064 : %s', async (message) => {
  vi.mocked(api.getDocument).mockRejectedValue(new Error(message));
  useDocumentStore.setState({ currentDocument: null, isLoading: false, error: null });
  render(<DocumentWorkspace documentId="rejeu" onBack={vi.fn()} />);
  await act(() => useDocumentStore.getState().openDocument('rejeu'));
  expect(screen.getByRole('alert')).toHaveTextContent(message);
  expect(screen.queryByText('Chargement du document...')).toBeNull();
  vi.mocked(api.getDocument).mockResolvedValue({ id: 'rejeu', title: 'Document relu', sections: [], pistes: [] } as unknown as api.DocumentDetail);
  await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Réessayer' })));
  expect(screen.getByText('Document relu')).toBeInTheDocument();
});
