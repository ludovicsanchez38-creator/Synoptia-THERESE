import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as api from '../services/api/documents';
import { useDocumentStore } from './documentStore';

vi.mock('../services/api/documents', async (original) => ({
  ...(await original<typeof import('../services/api/documents')>()),
  generateOutline: vi.fn(),
}));

beforeEach(() => {
  vi.resetAllMocks();
  useDocumentStore.getState().closeDocument();
  useDocumentStore.setState({ isLoading: false, documents: [] });
});

describe('B-1849 : fermer libère le chargement de la trame', () => {
  it.each(['réussite', 'échec'])('ne reste pas occupé après la fermeture et une %s tardive', async (issue) => {
    let terminer!: () => void;
    vi.mocked(api.generateOutline).mockImplementationOnce(() => new Promise((resolve, reject) => {
      terminer = () => issue === 'réussite' ? resolve([]) : reject(new Error('Trame refusée'));
    }));
    const generation = useDocumentStore.getState().generateOutline('a');
    expect(useDocumentStore.getState().isLoading).toBe(true);
    useDocumentStore.getState().closeDocument();
    const chargementApresFermeture = useDocumentStore.getState().isLoading;
    terminer();
    await generation;
    expect(chargementApresFermeture).toBe(false);
    expect(useDocumentStore.getState().isLoading).toBe(false);
    expect(useDocumentStore.getState().error).toBeNull();
  });

  it('la fin de la trame détachée ne libère pas le chargement de la suivante', async () => {
    let terminerA!: () => void;
    let terminerB!: () => void;
    vi.mocked(api.generateOutline)
      .mockImplementationOnce(() => new Promise(resolve => { terminerA = () => resolve([]); }))
      .mockImplementationOnce(() => new Promise(resolve => { terminerB = () => resolve([]); }));
    const a = useDocumentStore.getState().generateOutline('a');
    useDocumentStore.getState().closeDocument();
    const b = useDocumentStore.getState().generateOutline('b');
    terminerA();
    await a;
    expect(useDocumentStore.getState().isLoading).toBe(true);
    expect(useDocumentStore.getState().outlineGeneration?.documentId).toBe('b');
    terminerB();
    await b;
    expect(useDocumentStore.getState().isLoading).toBe(false);
  });
});
