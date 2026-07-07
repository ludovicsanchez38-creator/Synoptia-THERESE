import { describe, it, expect, beforeEach, vi } from 'vitest';
import { waitFor } from '@testing-library/react';
import type {
  DocumentDetail,
  DocumentResponse,
  DocumentSection,
  DraftStreamChunk,
} from '../services/api/documents';

vi.mock('../services/api/documents', () => {
  class ReorderConflictError extends Error {
    code: string;
    missing_ids: string[];
    unknown_ids: string[];
    constructor(body: { code: string; message: string; missing_ids: string[]; unknown_ids: string[] }) {
      super(body.message);
      this.name = 'ReorderConflictError';
      this.code = body.code;
      this.missing_ids = body.missing_ids;
      this.unknown_ids = body.unknown_ids;
    }
  }
  return {
    listDocuments: vi.fn(),
    getDocument: vi.fn(),
    createDocument: vi.fn(),
    deleteDocument: vi.fn(),
    generateOutline: vi.fn(),
    createSection: vi.fn(),
    updateSection: vi.fn(),
    reorderSections: vi.fn(),
    draftSection: vi.fn(),
    validateSection: vi.fn(),
    exportDocument: vi.fn(),
    listPistes: vi.fn(),
    createPiste: vi.fn(),
    updatePiste: vi.fn(),
    ReorderConflictError,
  };
});

import {
  listDocuments,
  getDocument,
  createDocument,
  deleteDocument,
  generateOutline,
  createSection,
  updateSection,
  reorderSections,
  draftSection,
  validateSection,
  exportDocument,
  listPistes,
  createPiste,
  updatePiste,
  ReorderConflictError,
} from '../services/api/documents';
import { useDocumentStore } from './documentStore';

const makeSection = (over: Partial<DocumentSection> = {}): DocumentSection => ({
  id: 's1',
  document_id: 'd1',
  title: 'Introduction',
  brief: 'Poser le contexte',
  order: 10,
  depth: 0,
  content: '',
  summary: '',
  status: 'vide',
  orphan: false,
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:00:00Z',
  ...over,
});

const makeDocument = (over: Partial<DocumentResponse> = {}): DocumentResponse => ({
  id: 'd1',
  title: 'Proposition Client X',
  brief: 'Une proposition commerciale',
  status: 'en_cours',
  project_id: null,
  contact_id: null,
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:00:00Z',
  sections_total: 0,
  sections_validees: 0,
  ...over,
});

const makeDetail = (over: Partial<DocumentDetail> = {}): DocumentDetail => ({
  ...makeDocument(),
  sections: [],
  pistes: [],
  ...over,
});

describe('documentStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDocumentStore.setState({
      documents: [],
      currentDocument: null,
      sectionActive: null,
      isStreaming: false,
      isLoading: false,
      error: null,
      createModalRequested: false,
    });
  });

  describe('loadDocuments', () => {
    it('peuple documents et bascule isLoading', async () => {
      vi.mocked(listDocuments).mockResolvedValueOnce([makeDocument()]);
      const p = useDocumentStore.getState().loadDocuments();
      expect(useDocumentStore.getState().isLoading).toBe(true);
      await p;
      expect(useDocumentStore.getState().isLoading).toBe(false);
      expect(useDocumentStore.getState().documents).toHaveLength(1);
    });

    it('pose une erreur affichable en cas d\'échec, sans planter', async () => {
      vi.mocked(listDocuments).mockRejectedValueOnce(new Error('Impossible de contacter le serveur'));
      await useDocumentStore.getState().loadDocuments();
      expect(useDocumentStore.getState().error).toBe('Impossible de contacter le serveur');
      expect(useDocumentStore.getState().isLoading).toBe(false);
    });
  });

  describe('openDocument', () => {
    it('charge le currentDocument avec ses sections et pistes', async () => {
      const detail = makeDetail({ sections: [makeSection()] });
      vi.mocked(getDocument).mockResolvedValueOnce(detail);
      await useDocumentStore.getState().openDocument('d1');
      expect(getDocument).toHaveBeenCalledWith('d1');
      expect(useDocumentStore.getState().currentDocument?.sections).toHaveLength(1);
    });

    // Résidu de revue lot D : deux openDocument entrelacés - la réponse
    // TARDIVE du premier ne doit pas écraser le document du second (jeton
    // d'ordonnancement module-scope, seule la réponse du dernier appel écrit).
    it('deux openDocument entrelacés : la réponse tardive du premier n\'écrase pas le second', async () => {
      let resolveA!: (v: DocumentDetail) => void;
      let resolveB!: (v: DocumentDetail) => void;
      vi.mocked(getDocument)
        .mockImplementationOnce(() => new Promise<DocumentDetail>((r) => { resolveA = r; }))
        .mockImplementationOnce(() => new Promise<DocumentDetail>((r) => { resolveB = r; }));

      const pA = useDocumentStore.getState().openDocument('dA');
      const pB = useDocumentStore.getState().openDocument('dB');

      // B (le plus récent) résout EN PREMIER : il écrit currentDocument.
      resolveB(makeDetail({ id: 'dB', title: 'Document B' }));
      await pB;
      expect(useDocumentStore.getState().currentDocument?.id).toBe('dB');
      expect(useDocumentStore.getState().isLoading).toBe(false);

      // A (périmé) résout APRÈS : il ne doit RIEN écrire.
      resolveA(makeDetail({ id: 'dA', title: 'Document A' }));
      await pA;
      expect(useDocumentStore.getState().currentDocument?.id).toBe('dB');
      expect(useDocumentStore.getState().isLoading).toBe(false);
    });

    it('un openDocument périmé qui ÉCHOUE ne pose pas non plus d\'erreur (le plus récent gère l\'état)', async () => {
      let rejectA!: (e: Error) => void;
      let resolveB!: (v: DocumentDetail) => void;
      vi.mocked(getDocument)
        .mockImplementationOnce(() => new Promise<DocumentDetail>((_r, rej) => { rejectA = rej; }))
        .mockImplementationOnce(() => new Promise<DocumentDetail>((r) => { resolveB = r; }));

      const pA = useDocumentStore.getState().openDocument('dA');
      const pB = useDocumentStore.getState().openDocument('dB');

      resolveB(makeDetail({ id: 'dB' }));
      await pB;

      rejectA(new Error('Impossible de contacter le serveur'));
      await pA;

      expect(useDocumentStore.getState().currentDocument?.id).toBe('dB');
      expect(useDocumentStore.getState().error).toBeNull();
    });
  });

  describe('createDocument', () => {
    it("n'ajoute qu'APRÈS confirmation de l'API (anti-faux-succès)", async () => {
      let resolveCreate!: (v: DocumentResponse) => void;
      vi.mocked(createDocument).mockReturnValueOnce(
        new Promise<DocumentResponse>((r) => {
          resolveCreate = r;
        })
      );
      const p = useDocumentStore.getState().createDocument({ title: 'Devis', brief: 'Un devis' });
      expect(useDocumentStore.getState().documents).toHaveLength(0);
      resolveCreate(makeDocument({ id: 'd2', title: 'Devis' }));
      await p;
      expect(useDocumentStore.getState().documents).toHaveLength(1);
      expect(useDocumentStore.getState().documents[0].id).toBe('d2');
    });
  });

  describe('generateOutline', () => {
    it('remplace les sections du currentDocument par la trame générée', async () => {
      useDocumentStore.setState({ currentDocument: makeDetail({ id: 'd1', sections: [] }) });
      const sections = [makeSection({ id: 's1', order: 10 }), makeSection({ id: 's2', order: 20 })];
      vi.mocked(generateOutline).mockResolvedValueOnce(sections);
      await useDocumentStore.getState().generateOutline('d1');
      const state = useDocumentStore.getState();
      expect(state.currentDocument?.sections).toHaveLength(2);
      expect(state.currentDocument?.sections_total).toBe(2);
    });
  });

  describe('updateSection', () => {
    it('met à jour la bonne section dans currentDocument', async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ sections: [makeSection({ id: 's1', title: 'Ancien' })] }),
      });
      vi.mocked(updateSection).mockResolvedValueOnce(makeSection({ id: 's1', title: 'Nouveau' }));
      await useDocumentStore.getState().updateSection('s1', { title: 'Nouveau' });
      expect(useDocumentStore.getState().currentDocument?.sections[0].title).toBe('Nouveau');
    });
  });

  describe('createSection', () => {
    it('insère la section à sa place (tri par order) et recalcule sections_total', async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({
          id: 'd1',
          sections: [makeSection({ id: 's1', order: 10 }), makeSection({ id: 's3', order: 30 })],
          sections_total: 2,
        }),
      });
      // Section intercalée entre s1 et s3 (order 20) : doit finir au MILIEU, pas en fin.
      vi.mocked(createSection).mockResolvedValueOnce(makeSection({ id: 's2', order: 20, title: 'Intercalée' }));
      await useDocumentStore.getState().createSection('d1', { title: 'Intercalée', order: 20 });
      const state = useDocumentStore.getState();
      expect(state.currentDocument?.sections.map((s) => s.id)).toEqual(['s1', 's2', 's3']);
      expect(state.currentDocument?.sections_total).toBe(3);
    });

    it("ne touche pas au currentDocument d'un AUTRE document", async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ id: 'd-autre', sections: [], sections_total: 0 }),
      });
      vi.mocked(createSection).mockResolvedValueOnce(makeSection({ id: 's1', document_id: 'd1' }));
      await useDocumentStore.getState().createSection('d1', { title: 'Ailleurs', order: 10 });
      expect(useDocumentStore.getState().currentDocument?.sections).toHaveLength(0);
    });

    it("pose une erreur affichable en cas d'échec, sans modifier la trame", async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1' })], sections_total: 1 }),
      });
      vi.mocked(createSection).mockRejectedValueOnce(new Error('Document introuvable'));
      await useDocumentStore.getState().createSection('d1', { title: 'X', order: 20 });
      const state = useDocumentStore.getState();
      expect(state.error).toBe('Document introuvable');
      expect(state.currentDocument?.sections).toHaveLength(1);
    });
  });

  describe('reorderSections', () => {
    it('applique la nouvelle trame renvoyée par le backend en cas de succès', async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({
          id: 'd1',
          sections: [makeSection({ id: 's1', order: 10 }), makeSection({ id: 's2', order: 20 })],
        }),
      });
      const reordered = [makeSection({ id: 's2', order: 5 }), makeSection({ id: 's1', order: 15 })];
      vi.mocked(reorderSections).mockResolvedValueOnce(reordered);
      await useDocumentStore.getState().reorderSections('d1', [
        { id: 's2', order: 5, depth: 0 },
        { id: 's1', order: 15, depth: 0 },
      ]);
      expect(useDocumentStore.getState().currentDocument?.sections[0].id).toBe('s2');
    });

    // Contrat backend (documents.py reorder_sections) : 409 structuré
    // {code, message, missing_ids, unknown_ids} - pas l'enveloppe générique.
    it("en cas de conflit 409 (REORDER incomplet), recharge le document et pose une erreur affichable", async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({
          id: 'd1',
          sections: [makeSection({ id: 's1', order: 10 })],
        }),
      });
      vi.mocked(reorderSections).mockRejectedValueOnce(
        new ReorderConflictError({
          code: 'SECTIONS_INCOMPLETE',
          message: "La réorganisation ne couvre pas exactement les sections existantes du document - aucune écriture effectuée.",
          missing_ids: ['s2'],
          unknown_ids: [],
        })
      );
      // Le rechargement (openDocument) doit refléter la trame RÉELLE côté serveur (inchangée).
      vi.mocked(getDocument).mockResolvedValueOnce(
        makeDetail({
          id: 'd1',
          sections: [makeSection({ id: 's1', order: 10 }), makeSection({ id: 's2', order: 20 })],
        })
      );

      await useDocumentStore.getState().reorderSections('d1', [{ id: 's1', order: 10, depth: 0 }]);

      expect(getDocument).toHaveBeenCalledWith('d1');
      const state = useDocumentStore.getState();
      expect(state.currentDocument?.sections).toHaveLength(2); // rechargé depuis le serveur
      expect(state.error).toContain('réorganisation');
    });
  });

  describe('validateSection', () => {
    it('met à jour le statut de la section et le décompte sections_validees', async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({
          sections: [makeSection({ id: 's1', status: 'brouillon' })],
          sections_validees: 0,
        }),
      });
      vi.mocked(validateSection).mockResolvedValueOnce(
        makeSection({ id: 's1', status: 'validee', summary: 'Résumé.' })
      );
      await useDocumentStore.getState().validateSection('s1');
      const state = useDocumentStore.getState();
      expect(state.currentDocument?.sections[0].status).toBe('validee');
      expect(state.currentDocument?.sections_validees).toBe(1);
    });
  });

  describe('exportDocument', () => {
    it("retourne les métadonnées d'export en cas de succès et nettoie l'erreur", async () => {
      useDocumentStore.setState({ error: 'Erreur périmée' });
      vi.mocked(exportDocument).mockResolvedValueOnce({
        success: true,
        format: 'docx',
        file_name: 'Proposition_abc12345.docx',
        download_url: '/api/skills/download/abc12345',
      });
      const result = await useDocumentStore.getState().exportDocument('d1', 'docx');
      expect(exportDocument).toHaveBeenCalledWith('d1', 'docx');
      expect(result?.file_name).toBe('Proposition_abc12345.docx');
      expect(result?.download_url).toBe('/api/skills/download/abc12345');
      expect(useDocumentStore.getState().error).toBeNull();
    });

    it("retourne null et pose l'erreur en cas d'échec (ex. document vide)", async () => {
      vi.mocked(exportDocument).mockRejectedValueOnce(new Error('Document vide : rien à exporter.'));
      const result = await useDocumentStore.getState().exportDocument('d1');
      expect(result).toBeNull();
      expect(useDocumentStore.getState().error).toBe('Document vide : rien à exporter.');
    });
  });

  describe('loadPistes / createPiste / updatePiste', () => {
    it('loadPistes peuple les pistes du currentDocument', async () => {
      useDocumentStore.setState({ currentDocument: makeDetail({ id: 'd1', pistes: [] }) });
      vi.mocked(listPistes).mockResolvedValueOnce([
        { id: 'p1', document_id: 'd1', section_origine_id: null, texte: 'Une piste', status: 'nouvelle', created_at: '2026-07-01T00:00:00Z' },
      ]);
      await useDocumentStore.getState().loadPistes('d1');
      expect(useDocumentStore.getState().currentDocument?.pistes).toHaveLength(1);
    });

    it('createPiste ajoute la piste au currentDocument après confirmation API', async () => {
      useDocumentStore.setState({ currentDocument: makeDetail({ id: 'd1', pistes: [] }) });
      vi.mocked(createPiste).mockResolvedValueOnce({
        id: 'p1',
        document_id: 'd1',
        section_origine_id: 's1',
        texte: 'Idée capturée à la main',
        status: 'nouvelle',
        created_at: '2026-07-01T00:00:00Z',
      });
      await useDocumentStore.getState().createPiste('d1', { texte: 'Idée capturée à la main', section_origine_id: 's1' });
      expect(createPiste).toHaveBeenCalledWith('d1', { texte: 'Idée capturée à la main', section_origine_id: 's1' });
      const pistes = useDocumentStore.getState().currentDocument?.pistes;
      expect(pistes).toHaveLength(1);
      expect(pistes?.[0].texte).toBe('Idée capturée à la main');
    });

    it("createPiste pose une erreur affichable en cas d'échec, sans ajouter de piste", async () => {
      useDocumentStore.setState({ currentDocument: makeDetail({ id: 'd1', pistes: [] }) });
      vi.mocked(createPiste).mockRejectedValueOnce(new Error('Document introuvable'));
      await useDocumentStore.getState().createPiste('d1', { texte: 'X' });
      expect(useDocumentStore.getState().error).toBe('Document introuvable');
      expect(useDocumentStore.getState().currentDocument?.pistes).toHaveLength(0);
    });

    // Régression revue D1 : une erreur périmée d'une action précédente ne doit
    // PAS survivre à un appel piste réussi (bannière d'erreur fantôme en UI).
    it("les actions pistes nettoient l'erreur périmée en cas de succès", async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ id: 'd1', pistes: [] }),
        error: 'Erreur périmée d\'une action précédente',
      });
      vi.mocked(listPistes).mockResolvedValueOnce([]);
      await useDocumentStore.getState().loadPistes('d1');
      expect(useDocumentStore.getState().error).toBeNull();

      useDocumentStore.setState({ error: 'Erreur périmée' });
      vi.mocked(createPiste).mockResolvedValueOnce({
        id: 'p1', document_id: 'd1', section_origine_id: null, texte: 'Piste', status: 'nouvelle', created_at: '2026-07-01T00:00:00Z',
      });
      await useDocumentStore.getState().createPiste('d1', { texte: 'Piste' });
      expect(useDocumentStore.getState().error).toBeNull();

      useDocumentStore.setState({ error: 'Erreur périmée' });
      vi.mocked(updatePiste).mockResolvedValueOnce({
        id: 'p1', document_id: 'd1', section_origine_id: null, texte: 'Piste', status: 'exploree', created_at: '2026-07-01T00:00:00Z',
      });
      await useDocumentStore.getState().updatePiste('p1', 'exploree');
      expect(useDocumentStore.getState().error).toBeNull();
    });

    it('updatePiste met à jour le statut de la bonne piste', async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({
          id: 'd1',
          pistes: [{ id: 'p1', document_id: 'd1', section_origine_id: null, texte: 'Une piste', status: 'nouvelle', created_at: '2026-07-01T00:00:00Z' }],
        }),
      });
      vi.mocked(updatePiste).mockResolvedValueOnce({
        id: 'p1',
        document_id: 'd1',
        section_origine_id: null,
        texte: 'Une piste',
        status: 'exploree',
        created_at: '2026-07-01T00:00:00Z',
      });
      await useDocumentStore.getState().updatePiste('p1', 'exploree');
      expect(useDocumentStore.getState().currentDocument?.pistes[0].status).toBe('exploree');
    });
  });

  describe('deleteDocument', () => {
    it('retire le document de la liste et vide currentDocument si concerné', async () => {
      useDocumentStore.setState({
        documents: [makeDocument({ id: 'd1' })],
        currentDocument: makeDetail({ id: 'd1' }),
      });
      vi.mocked(deleteDocument).mockResolvedValueOnce({ success: true, message: 'Document supprimé' });
      await useDocumentStore.getState().deleteDocument('d1');
      expect(useDocumentStore.getState().documents).toHaveLength(0);
      expect(useDocumentStore.getState().currentDocument).toBeNull();
    });
  });

  describe('draftSection - streaming au fil de l\'eau', () => {
    it('concatène 3 chunks texte progressivement et passe la section en brouillon', async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1', content: '', status: 'vide' })] }),
      });

      let releaseChunk2: () => void = () => {};
      let releaseChunk3: () => void = () => {};

      vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
        yield { type: 'text', content: 'Bon' };
        await new Promise<void>((resolve) => {
          releaseChunk2 = resolve;
        });
        yield { type: 'text', content: 'jour' };
        await new Promise<void>((resolve) => {
          releaseChunk3 = resolve;
        });
        yield { type: 'text', content: ' monde' };
        // Pas de chunk terminal explicite : le générateur s'épuise seul.
      });

      const streaming = useDocumentStore.getState().draftSection('s1');

      await waitFor(() => {
        expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Bon');
      });
      expect(useDocumentStore.getState().currentDocument?.sections[0].status).toBe('brouillon');
      expect(useDocumentStore.getState().isStreaming).toBe(true);

      releaseChunk2();
      await waitFor(() => {
        expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Bonjour');
      });

      releaseChunk3();
      await waitFor(() => {
        expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Bonjour monde');
      });

      await streaming;
      expect(useDocumentStore.getState().isStreaming).toBe(false);
    });

    it("le chunk 'done' recharge le document (contenu canonique + pistes) et arrête le streaming", async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1', content: '', status: 'vide' })], pistes: [] }),
      });

      vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
        yield { type: 'text', content: 'Brouillon partiel' };
        yield { type: 'done', section_id: 's1' };
      });

      vi.mocked(getDocument).mockResolvedValueOnce(
        makeDetail({
          id: 'd1',
          sections: [makeSection({ id: 's1', content: 'Contenu final canonique (sans bloc PISTES)', status: 'brouillon' })],
          pistes: [{ id: 'p1', document_id: 'd1', section_origine_id: 's1', texte: 'Une piste détectée', status: 'nouvelle', created_at: '2026-07-01T00:00:00Z' }],
        })
      );

      await useDocumentStore.getState().draftSection('s1');

      expect(getDocument).toHaveBeenCalledWith('d1');
      const state = useDocumentStore.getState();
      expect(state.currentDocument?.sections[0].content).toBe('Contenu final canonique (sans bloc PISTES)');
      expect(state.currentDocument?.pistes).toHaveLength(1);
      expect(state.isStreaming).toBe(false);
      expect(state.error).toBeNull();
    });

    it("le chunk 'error' conserve le contenu partiel déjà streamé et pose l'erreur, sans recharger le document", async () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1', content: '', status: 'vide' })] }),
      });

      vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
        yield { type: 'text', content: 'Début de rédaction' };
        yield { type: 'error', content: 'Erreur du fournisseur IA pendant la rédaction : timeout' };
      });

      await useDocumentStore.getState().draftSection('s1');

      const state = useDocumentStore.getState();
      expect(state.currentDocument?.sections[0].content).toBe('Début de rédaction');
      expect(state.currentDocument?.sections[0].status).toBe('brouillon');
      expect(state.error).toBe('Erreur du fournisseur IA pendant la rédaction : timeout');
      expect(state.isStreaming).toBe(false);
      expect(getDocument).not.toHaveBeenCalled();
    });

    it('un échec réseau avant tout chunk pose une erreur affichable sans planter', async () => {
      // eslint-disable-next-line require-yield -- la fonction ne doit justement JAMAIS yield ici (échec avant tout chunk)
      vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
        throw new Error('Impossible de contacter le serveur');
      });

      await useDocumentStore.getState().draftSection('s1');

      expect(useDocumentStore.getState().error).toBe('Impossible de contacter le serveur');
      expect(useDocumentStore.getState().isStreaming).toBe(false);
    });

    // Revue adversariale lot D (finding A) : le backend émet des DELTAS et
    // REMPLACE le contenu accumulé côté base - sans reset au démarrage du
    // draft, une retouche sur une section déjà rédigée afficherait
    // ancien+nouveau pendant tout le stream (divergence avec le backend).
    describe('reset du contenu au démarrage (finding A)', () => {
      it('retouche sur une section AVEC contenu existant : pendant le stream, le contenu est SEULEMENT la concat des chunks (jamais ancien+nouveau)', async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({
            id: 'd1',
            sections: [makeSection({ id: 's1', content: 'Ancien contenu déjà rédigé.', status: 'brouillon' })],
          }),
        });

        let releaseChunk: () => void = () => {};
        vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
          yield { type: 'text', content: 'Nouveau' };
          await new Promise<void>((resolve) => {
            releaseChunk = resolve;
          });
          yield { type: 'text', content: ' contenu' };
        });

        const streaming = useDocumentStore.getState().draftSection('s1', 'Reprends tout');

        await waitFor(() => {
          expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Nouveau');
        });
        // L'ancien contenu ne doit JAMAIS réapparaître pendant le stream.
        expect(useDocumentStore.getState().currentDocument?.sections[0].content).not.toContain('Ancien contenu');

        releaseChunk();
        await waitFor(() => {
          expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Nouveau contenu');
        });

        await streaming;
      });

      it('erreur mi-stream sur une retouche : le contenu reste le PARTIEL streamé depuis ce démarrage (pas ancien+partiel)', async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({
            id: 'd1',
            sections: [makeSection({ id: 's1', content: 'Ancien paragraphe complet.', status: 'brouillon' })],
          }),
        });

        vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
          yield { type: 'text', content: 'Début du nouveau texte' };
          yield { type: 'error', content: 'Erreur du fournisseur IA pendant la rédaction : timeout' };
        });

        await useDocumentStore.getState().draftSection('s1', 'Reprends tout');

        const state = useDocumentStore.getState();
        expect(state.currentDocument?.sections[0].content).toBe('Début du nouveau texte');
        expect(state.error).toBe('Erreur du fournisseur IA pendant la rédaction : timeout');
        expect(state.isStreaming).toBe(false);
      });

      it('première rédaction (section vide) : le reset au démarrage est un no-op, comportement inchangé', async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1', content: '', status: 'vide' })] }),
        });
        vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
          yield { type: 'text', content: 'Bonjour' };
        });

        await useDocumentStore.getState().draftSection('s1');

        expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Bonjour');
      });

      // Résidu de revue lot D : erreur AVANT le premier chunk texte - le
      // backend n'a rien flushé (la base garde l'ancien contenu), le store
      // doit RESTAURER le contenu pré-reset au lieu de laisser '' (sinon
      // l'utilisateur voit son paragraphe disparaître jusqu'au rechargement).
      it("chunk 'error' en tête de flux (0 chunk texte) sur une section rédigée : le contenu d'origine est restauré et l'erreur posée", async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({
            id: 'd1',
            sections: [makeSection({ id: 's1', content: 'Paragraphe déjà rédigé.', status: 'brouillon' })],
          }),
        });

        vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
          yield { type: 'error', content: 'Erreur du fournisseur IA pendant la rédaction : surcharge' };
        });

        await useDocumentStore.getState().draftSection('s1', 'Reprends tout');

        const state = useDocumentStore.getState();
        expect(state.currentDocument?.sections[0].content).toBe('Paragraphe déjà rédigé.');
        expect(state.error).toBe('Erreur du fournisseur IA pendant la rédaction : surcharge');
        expect(state.isStreaming).toBe(false);
      });

      it("exception réseau immédiate (0 chunk) sur une section rédigée : le contenu d'origine est restauré et l'erreur posée", async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({
            id: 'd1',
            sections: [makeSection({ id: 's1', content: 'Paragraphe déjà rédigé.', status: 'brouillon' })],
          }),
        });

        // eslint-disable-next-line require-yield -- la fonction ne doit justement JAMAIS yield ici (échec avant tout chunk)
        vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
          throw new Error('Impossible de contacter le serveur');
        });

        await useDocumentStore.getState().draftSection('s1', 'Reprends tout');

        const state = useDocumentStore.getState();
        expect(state.currentDocument?.sections[0].content).toBe('Paragraphe déjà rédigé.');
        expect(state.error).toBe('Impossible de contacter le serveur');
        expect(state.isStreaming).toBe(false);
      });
    });

    // Revue adversariale lot D (finding B) : stream abandonné (fermeture du
    // document, ou bascule pendant le stream) - isStreaming ne doit pas
    // rester bloqué, le flux transmis doit être annulable, et un `done`
    // tardif ne doit pas recharger le mauvais document.
    describe('annulation du stream (finding B)', () => {
      it('closeDocument pendant un stream : isStreaming repasse à false ET le signal transmis à l\'API est annulé', async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1', content: '', status: 'vide' })] }),
        });

        let capturedSignal: AbortSignal | undefined;
        let releaseChunk: () => void = () => {};
        vi.mocked(draftSection).mockImplementation(async function* (
          _sectionId: string,
          _instruction?: string,
          signal?: AbortSignal
        ): AsyncGenerator<DraftStreamChunk> {
          capturedSignal = signal;
          yield { type: 'text', content: 'Début' };
          await new Promise<void>((resolve) => {
            releaseChunk = resolve;
          });
          if (signal?.aborted) {
            const abortError = new Error('The operation was aborted.');
            abortError.name = 'AbortError';
            throw abortError;
          }
          yield { type: 'text', content: ' suite' };
        });

        const streaming = useDocumentStore.getState().draftSection('s1');

        await waitFor(() => {
          expect(useDocumentStore.getState().isStreaming).toBe(true);
          expect(capturedSignal).toBeDefined();
        });

        useDocumentStore.getState().closeDocument();

        expect(useDocumentStore.getState().isStreaming).toBe(false);
        expect(capturedSignal?.aborted).toBe(true);

        releaseChunk();
        await streaming; // ne doit pas planter (sortie silencieuse sur AbortError)

        expect(useDocumentStore.getState().error).toBeNull();
      });

      it("un nouveau draftSection annule silencieusement le stream précédent encore actif", async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({
            id: 'd1',
            sections: [makeSection({ id: 's1', content: '', status: 'vide' }), makeSection({ id: 's2', content: '', status: 'vide' })],
          }),
        });

        let firstSignal: AbortSignal | undefined;
        let releaseFirst: () => void = () => {};
        vi.mocked(draftSection).mockImplementationOnce(async function* (
          _sectionId: string,
          _instruction?: string,
          signal?: AbortSignal
        ): AsyncGenerator<DraftStreamChunk> {
          firstSignal = signal;
          yield { type: 'text', content: 'Premier flux' };
          await new Promise<void>((resolve) => {
            releaseFirst = resolve;
          });
          if (signal?.aborted) {
            const abortError = new Error('The operation was aborted.');
            abortError.name = 'AbortError';
            throw abortError;
          }
          yield { type: 'text', content: ' jamais vu' };
        });
        vi.mocked(draftSection).mockImplementationOnce(async function* (): AsyncGenerator<DraftStreamChunk> {
          yield { type: 'text', content: 'Second flux' };
        });

        const firstStreaming = useDocumentStore.getState().draftSection('s1');
        await waitFor(() => expect(firstSignal).toBeDefined());

        const secondStreaming = useDocumentStore.getState().draftSection('s2');

        expect(firstSignal?.aborted).toBe(true);
        releaseFirst();

        await Promise.all([firstStreaming, secondStreaming]);

        expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Premier flux');
        expect(useDocumentStore.getState().currentDocument?.sections[1].content).toBe('Second flux');
        expect(useDocumentStore.getState().error).toBeNull();
      });

      it("le chunk 'done' ne recharge PAS un document différent de celui actif au démarrage du draft (bascule pendant le stream)", async () => {
        useDocumentStore.setState({
          currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1', content: '', status: 'vide' })] }),
        });

        let releaseDone: () => void = () => {};
        vi.mocked(draftSection).mockImplementation(async function* (): AsyncGenerator<DraftStreamChunk> {
          yield { type: 'text', content: 'Partiel' };
          // Gate : le chunk 'done' n'arrive qu'APRÈS que le test ait basculé
          // le document actif (sinon les deux chunks s'enchaînent dans le
          // même tick et le test ne peut jamais observer l'état intermédiaire).
          await new Promise<void>((resolve) => {
            releaseDone = resolve;
          });
          yield { type: 'done', section_id: 's1' };
        });

        const streaming = useDocumentStore.getState().draftSection('s1');

        await waitFor(() => {
          expect(useDocumentStore.getState().currentDocument?.sections[0].content).toBe('Partiel');
        });

        // Bascule vers un AUTRE document PENDANT le stream (chemin réel :
        // finding E, un nouveau document est ouvert sans que le précédent
        // ait été proprement fermé).
        useDocumentStore.setState({ currentDocument: makeDetail({ id: 'd2', sections: [] }) });

        releaseDone();
        await streaming;

        expect(getDocument).not.toHaveBeenCalled();
        expect(useDocumentStore.getState().currentDocument?.id).toBe('d2');
        expect(useDocumentStore.getState().isStreaming).toBe(false);
      });
    });
  });

  describe('closeDocument', () => {
    it('réinitialise currentDocument, sectionActive et error (anti-flash D2/D3)', () => {
      useDocumentStore.setState({
        currentDocument: makeDetail({ id: 'd1', sections: [makeSection({ id: 's1' })] }),
        sectionActive: 's1',
        error: 'Une erreur périmée',
      });
      useDocumentStore.getState().closeDocument();
      const state = useDocumentStore.getState();
      expect(state.currentDocument).toBeNull();
      expect(state.sectionActive).toBeNull();
      expect(state.error).toBeNull();
    });
  });

  describe('clearError', () => {
    it('remet error à null', () => {
      useDocumentStore.setState({ error: 'Un souci' });
      useDocumentStore.getState().clearError();
      expect(useDocumentStore.getState().error).toBeNull();
    });
  });

  describe('requestCreateModal / clearCreateModalRequest (D4, documents.new)', () => {
    it('requestCreateModal pose le drapeau, clearCreateModalRequest l\'efface', () => {
      expect(useDocumentStore.getState().createModalRequested).toBe(false);
      useDocumentStore.getState().requestCreateModal();
      expect(useDocumentStore.getState().createModalRequested).toBe(true);
      useDocumentStore.getState().clearCreateModalRequest();
      expect(useDocumentStore.getState().createModalRequested).toBe(false);
    });
  });
});
