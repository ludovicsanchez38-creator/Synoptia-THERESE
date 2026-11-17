import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { DocumentsList } from './DocumentsList';
import { useDocumentStore } from '../../stores/documentStore';
import * as api from '../../services/api/documents';
import type { DocumentDetail } from '../../services/api/documents';

vi.mock('../../services/api/documents', async original => ({
  ...await original<typeof api>(),
  listDocuments: vi.fn(), getDocument: vi.fn(), createDocument: vi.fn(), generateOutline: vi.fn(),
}));
vi.mock('../../services/api', async original => ({
  ...await original<typeof import('../../services/api')>(),
  listProjects: vi.fn().mockResolvedValue([]),
}));
vi.mock('../../services/api/processingTasks', () => ({
  listerTraitements: vi.fn().mockResolvedValue([]), annulerTraitement: vi.fn(),
}));

function document(id: string): DocumentDetail {
  return { id, title: `Document ${id}`, brief: '', status: 'en_cours', project_id: null, contact_id: null,
    sections_total: 0, sections_validees: 0, sections: [], pistes: [], created_at: '', updated_at: '' };
}

beforeEach(() => {
  vi.clearAllMocks();
  useDocumentStore.getState().closeDocument();
  useDocumentStore.setState({ documents: [], createModalRequested: false, ouvertureDemandee: null });
  vi.mocked(api.listDocuments).mockResolvedValue([document('b')]);
  vi.mocked(api.createDocument).mockResolvedValue(document('a'));
  vi.mocked(api.getDocument).mockReset().mockImplementation(async id => document(id));
  vi.mocked(api.generateOutline).mockReset().mockResolvedValue([]);
});

it.each(['réussite', 'refus'])('R2-5 : fermer la création empêche son suivi tardif après %s de la lecture', async (issue) => {
  let terminer!: () => void;
  vi.mocked(api.getDocument).mockImplementationOnce(() => new Promise((resolve, reject) => {
    terminer = () => issue === 'réussite' ? resolve(document('a')) : reject(new Error('Lecture abandonnée'));
  }));
  render(<DocumentsList />);
  await screen.findByText('Document b');
  fireEvent.click(screen.getByRole('button', { name: 'Nouveau document' }));
  const dialogue = await screen.findByRole('dialog', { name: 'Nouveau document' });
  fireEvent.change(within(dialogue).getByLabelText(/Titre/), { target: { value: 'Document a' } });
  fireEvent.click(within(dialogue).getByRole('button', { name: 'Créer' }));
  await waitFor(() => expect(terminer).toBeTypeOf('function'));
  fireEvent.click(screen.getByRole('button', { name: 'Retour aux documents' }));
  fireEvent.click(await screen.findByText('Document b'));
  await waitFor(() => expect(useDocumentStore.getState().currentDocument?.id).toBe('b'));
  await act(async () => { terminer(); });

  expect(api.generateOutline).not.toHaveBeenCalled();
  expect(useDocumentStore.getState().currentDocument?.id).toBe('b');
  expect(useDocumentStore.getState().isLoading).toBe(false);
  expect(useDocumentStore.getState().outlineGeneration).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Générer la trame' }));
  await waitFor(() => expect(api.generateOutline).toHaveBeenCalledWith('b', expect.any(String)));
});

it.each(['atelier ouvert', 'atelier fermé puis rouvert'])('R3-7 : la reprise de lecture respecte la création dans l’%s', async (navigation) => {
  vi.mocked(api.getDocument).mockRejectedValueOnce(new Error('Lecture initiale refusée'));
  render(<DocumentsList />);
  await screen.findByText('Document b');
  fireEvent.click(screen.getByRole('button', { name: 'Nouveau document' }));
  const dialogue = await screen.findByRole('dialog', { name: 'Nouveau document' });
  fireEvent.change(within(dialogue).getByLabelText(/Titre/), { target: { value: 'Document a' } });
  fireEvent.click(within(dialogue).getByRole('button', { name: 'Créer' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Lecture initiale refusée');
  expect(api.generateOutline).not.toHaveBeenCalled();

  if (navigation === 'atelier ouvert') {
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
  } else {
    fireEvent.click(screen.getByRole('button', { name: 'Retour aux documents' }));
    fireEvent.click(await screen.findByText('Document a'));
  }
  await waitFor(() => expect(useDocumentStore.getState().currentDocument?.id).toBe('a'));
  if (navigation === 'atelier ouvert') {
    await waitFor(() => expect(api.generateOutline).toHaveBeenCalledTimes(1));
    expect(api.generateOutline).toHaveBeenCalledWith('a', expect.any(String));
    await act(async () => { await useDocumentStore.getState().openDocument('a'); });
    expect(api.generateOutline).toHaveBeenCalledTimes(1);
  } else {
    expect(api.generateOutline).not.toHaveBeenCalled();
  }
});
