import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentDetail } from '../services/api/documents';
import * as api from '../services/api/documents';
import { useDocumentStore } from './documentStore';

vi.mock('../services/api/documents', async (original) => ({
  ...(await original<typeof import('../services/api/documents')>()),
  getDocument: vi.fn(),
  deleteDocument: vi.fn(),
}));

function document(id: string): DocumentDetail {
  return { id, title: id, brief: '', status: 'en_cours', project_id: null,
    contact_id: null, created_at: '', updated_at: '', sections_total: 1,
    sections_validees: 0, sections: [], pistes: [] };
}

function lectureEnAttente() {
  let terminer!: (doc: DocumentDetail) => void;
  let refuser!: (erreur: Error) => void;
  vi.mocked(api.getDocument).mockImplementationOnce(() => new Promise((resolve, reject) => {
    terminer = resolve;
    refuser = reject;
  }));
  return { terminer: (doc: DocumentDetail) => terminer(doc), refuser: () => refuser(new Error('Lecture tardive refusée')) };
}

beforeEach(() => {
  vi.resetAllMocks();
  useDocumentStore.getState().closeDocument();
  useDocumentStore.setState({ documents: [document('a'), document('b')], isLoading: false });
  vi.mocked(api.deleteDocument).mockResolvedValue({ success: true, message: 'Document supprimé.' });
});

describe('B-1848 : invalider les ouvertures abandonnées', () => {
  it.each(['fermeture', 'suppression'])('une %s empêche une lecture tardive de rouvrir le document', async (action) => {
    const lecture = lectureEnAttente();
    const ouverture = useDocumentStore.getState().openDocument('a');
    if (action === 'fermeture') useDocumentStore.getState().closeDocument();
    else await useDocumentStore.getState().deleteDocument('a');
    lecture.terminer(document('a'));
    await ouverture;
    expect(useDocumentStore.getState().currentDocument).toBeNull();
  });

  it.each(['fermeture', 'suppression'])('une %s ignore aussi une erreur de lecture tardive', async (action) => {
    const lecture = lectureEnAttente();
    const ouverture = useDocumentStore.getState().openDocument('a');
    if (action === 'fermeture') useDocumentStore.getState().closeDocument();
    else await useDocumentStore.getState().deleteDocument('a');
    lecture.refuser();
    await ouverture;
    expect(useDocumentStore.getState().error).toBeNull();
  });

  it('supprimer un autre document laisse aboutir la lecture courante', async () => {
    const lecture = lectureEnAttente();
    const ouverture = useDocumentStore.getState().openDocument('b');
    await useDocumentStore.getState().deleteDocument('a');
    lecture.terminer(document('b'));
    await ouverture;
    expect(useDocumentStore.getState().currentDocument?.id).toBe('b');
    expect(useDocumentStore.getState().isLoading).toBe(false);
  });

  it('une suppression refusée laisse le document consultable', async () => {
    const lecture = lectureEnAttente();
    const ouverture = useDocumentStore.getState().openDocument('a');
    vi.mocked(api.deleteDocument).mockRejectedValueOnce(new Error('Suppression refusée'));
    await useDocumentStore.getState().deleteDocument('a');
    lecture.terminer(document('a'));
    await ouverture;
    expect(useDocumentStore.getState().currentDocument?.id).toBe('a');
    expect(useDocumentStore.getState().documents).toHaveLength(2);
  });
});
