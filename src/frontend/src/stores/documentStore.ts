/**
 * THÉRÈSE v2 - Document Store
 *
 * State management pour l'atelier documentaire (documents longs à sections
 * multiples : propositions, dossiers, rapports). Consomme `services/api/documents.ts`.
 * Pattern Zustand identique à `openclawStore.ts` / `contactsStore.ts` : aucune
 * mutation locale avant confirmation de l'API (anti-faux-succès), erreur
 * affichable dans `error` plutôt que des exceptions non gérées.
 *
 * Streaming de rédaction (`draftSection`) : le contenu de la section ciblée
 * est RÉINITIALISÉ à `''` AU DÉMARRAGE du draft (retouche ET première
 * rédaction) - le backend émet des DELTAS et REMPLACE `target.content` par
 * l'accumulé côté base, donc le store doit reconstruire le contenu de zéro
 * pour rester en miroir exact (sinon une retouche affiche ancien+nouveau
 * pendant tout le stream, cf revue adversariale lot D, finding A). Le
 * contenu est ensuite mis à jour AU FIL DE L'EAU (chunk par chunk, immuable
 * - nouveaux tableaux/objets, jamais de mutation en place) pendant que
 * `isStreaming` reste vrai. Sur chunk `error`, le contenu déjà streamé
 * depuis CE démarrage est conservé tel quel (le backend a lui-même persisté
 * le partiel, zéro perte) et `error` est posé. Sur chunk `done`, le document
 * est rechargé pour récupérer le contenu canonique (sans bloc PISTES) et les
 * nouvelles pistes détectées - SAUF si le document actif a changé depuis le
 * démarrage du draft (id capturé au départ, comparé à `get().currentDocument
 * ?.id` : sinon on rechargerait le mauvais document, finding B).
 *
 * Annulation (finding B) : un `AbortController` module-scope (`draftAbort
 * Controller`, un seul flux de rédaction actif à la fois puisque
 * `isStreaming` est global) est créé à chaque `draftSection` et transmis en
 * `signal` à `services/api/documents.draftSection`. Un nouveau draft annule
 * silencieusement un stream encore actif ; `closeDocument` fait de même. Sur
 * `AbortError`, sortie silencieuse - ni `error` ni `isStreaming` ne sont
 * posés ici (déjà gérés par le déclencheur de l'abort), le contenu partiel
 * reste tel quel (le backend l'a déjà persisté via son propre `finally`).
 */

import { create } from 'zustand';
import type {
  DocumentResponse,
  DocumentDetail,
  DocumentSection,
  DocumentCreateRequest,
  SectionCreateRequest,
  SectionUpdateRequest,
  SectionsReorderItem,
  PisteCreateRequest,
  PisteStatus,
  DocumentExportResponse,
} from '../services/api/documents';
import {
  listDocuments as apiListDocuments,
  getDocument as apiGetDocument,
  createDocument as apiCreateDocument,
  deleteDocument as apiDeleteDocument,
  generateOutline as apiGenerateOutline,
  createSection as apiCreateSection,
  updateSection as apiUpdateSection,
  reorderSections as apiReorderSections,
  draftSection as apiDraftSection,
  validateSection as apiValidateSection,
  exportDocument as apiExportDocument,
  listPistes as apiListPistes,
  createPiste as apiCreatePiste,
  updatePiste as apiUpdatePiste,
  ReorderConflictError,
} from '../services/api/documents';

interface DocumentStore {
  // État
  documents: DocumentResponse[];
  currentDocument: DocumentDetail | null;
  sectionActive: string | null;
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;
  /** Drapeau UI ponctuel (D4) : posé par l'action ⌘K/Accueil `documents.new`
   * AVANT que la vue Documents ne soit montée (ou pendant qu'elle l'est
   * déjà) - `DocumentsList` le consomme (ouvre sa modale de création locale)
   * puis l'efface via `clearCreateModalRequest`. Vit dans le store (pas un
   * CustomEvent) précisément parce que la vue peut ne pas encore être
   * montée au moment où l'action se déclenche (⌘K depuis une autre vue) :
   * un event DOM dispatché avant le montage du listener serait perdu, alors
   * qu'un state Zustand déjà posé est lu correctement au premier rendu. */
  createModalRequested: boolean;

  // Documents
  loadDocuments: () => Promise<void>;
  openDocument: (id: string) => Promise<void>;
  createDocument: (payload: DocumentCreateRequest) => Promise<DocumentResponse | null>;
  deleteDocument: (id: string) => Promise<void>;
  /** Referme l'atelier (D3) : reset currentDocument/sectionActive/error - évite
   * qu'un document précédent flashe au prochain montage de l'atelier. */
  closeDocument: () => void;
  /** Pose le drapeau `createModalRequested` (D4, action `documents.new`). */
  requestCreateModal: () => void;
  /** Efface le drapeau `createModalRequested` (D4, consommé par `DocumentsList`). */
  clearCreateModalRequest: () => void;

  // Trame / sections
  generateOutline: (documentId: string) => Promise<void>;
  createSection: (documentId: string, payload: SectionCreateRequest) => Promise<void>;
  updateSection: (sectionId: string, payload: SectionUpdateRequest) => Promise<void>;
  reorderSections: (documentId: string, items: SectionsReorderItem[]) => Promise<void>;
  setSectionActive: (sectionId: string | null) => void;

  // Rédaction
  draftSection: (sectionId: string, instruction?: string) => Promise<void>;
  validateSection: (sectionId: string) => Promise<void>;

  // Export
  exportDocument: (documentId: string, format?: 'md' | 'docx') => Promise<DocumentExportResponse | null>;

  // Pistes
  loadPistes: (documentId: string) => Promise<void>;
  createPiste: (documentId: string, payload: PisteCreateRequest) => Promise<void>;
  updatePiste: (pisteId: string, status: PisteStatus) => Promise<void>;

  // UI
  clearError: () => void;
}

/**
 * AbortController du flux de rédaction en cours (D4, finding B) - module-
 * scope plutôt que dans le state Zustand : ce n'est pas une donnée
 * affichable, et un seul flux de rédaction est actif à la fois (`isStreaming`
 * est global, pas par section).
 */
let draftAbortController: AbortController | null = null;

/** Applique une mise à jour à une section précise de currentDocument (immuable). */
function patchSection(
  document: DocumentDetail,
  sectionId: string,
  patch: (section: DocumentSection) => DocumentSection
): DocumentDetail {
  return {
    ...document,
    sections: document.sections.map((section) => (section.id === sectionId ? patch(section) : section)),
  };
}

export const useDocumentStore = create<DocumentStore>((set, get) => ({
  documents: [],
  currentDocument: null,
  sectionActive: null,
  isStreaming: false,
  isLoading: false,
  error: null,
  createModalRequested: false,

  // ============================================================
  // Documents
  // ============================================================

  loadDocuments: async () => {
    set({ isLoading: true, error: null });
    try {
      const documents = await apiListDocuments();
      set({ documents, isLoading: false });
    } catch (e: any) {
      set({ isLoading: false, error: e?.message || 'Impossible de charger les documents.' });
    }
  },

  openDocument: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const document = await apiGetDocument(id);
      set({ currentDocument: document, isLoading: false });
    } catch (e: any) {
      set({ isLoading: false, error: e?.message || 'Impossible de charger le document.' });
    }
  },

  createDocument: async (payload) => {
    set({ error: null });
    try {
      // Confirmation API AVANT toute mutation locale (pas de faux succès).
      const created = await apiCreateDocument(payload);
      set((s) => ({ documents: [created, ...s.documents] }));
      return created;
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de créer le document.' });
      return null;
    }
  },

  deleteDocument: async (id) => {
    set({ error: null });
    try {
      await apiDeleteDocument(id);
      set((s) => ({
        documents: s.documents.filter((d) => d.id !== id),
        currentDocument: s.currentDocument?.id === id ? null : s.currentDocument,
      }));
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de supprimer le document.' });
    }
  },

  closeDocument: () => {
    // Finding B : abandonner un stream en cours plutôt que le laisser tourner
    // dans le vide (isStreaming resterait bloqué à `true`, et un `done`
    // tardif rechargerait un document qu'on vient de quitter).
    draftAbortController?.abort();
    draftAbortController = null;
    set({ currentDocument: null, sectionActive: null, error: null, isStreaming: false });
  },

  requestCreateModal: () => set({ createModalRequested: true }),
  clearCreateModalRequest: () => set({ createModalRequested: false }),

  // ============================================================
  // Trame / sections
  // ============================================================

  generateOutline: async (documentId) => {
    set({ isLoading: true, error: null });
    try {
      const sections = await apiGenerateOutline(documentId);
      set((s) => ({
        isLoading: false,
        currentDocument:
          s.currentDocument && s.currentDocument.id === documentId
            ? { ...s.currentDocument, sections, sections_total: sections.length }
            : s.currentDocument,
      }));
    } catch (e: any) {
      set({ isLoading: false, error: e?.message || 'Impossible de générer la trame.' });
    }
  },

  createSection: async (documentId, payload) => {
    set({ error: null });
    try {
      const section = await apiCreateSection(documentId, payload);
      set((s) => {
        if (!s.currentDocument || s.currentDocument.id !== documentId) return s;
        const sections = [...s.currentDocument.sections, section].sort((a, b) => a.order - b.order);
        return {
          currentDocument: { ...s.currentDocument, sections, sections_total: sections.length },
        };
      });
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de créer la section.' });
    }
  },

  updateSection: async (sectionId, payload) => {
    set({ error: null });
    try {
      const updated = await apiUpdateSection(sectionId, payload);
      set((s) => {
        if (!s.currentDocument) return s;
        return { currentDocument: patchSection(s.currentDocument, sectionId, () => updated) };
      });
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de mettre à jour la section.' });
    }
  },

  reorderSections: async (documentId, items) => {
    set({ error: null });
    try {
      const sections = await apiReorderSections(documentId, items);
      set((s) => {
        if (!s.currentDocument || s.currentDocument.id !== documentId) return s;
        return { currentDocument: { ...s.currentDocument, sections } };
      });
    } catch (e) {
      if (e instanceof ReorderConflictError) {
        // Invariant anti-perte : le backend n'a RIEN écrit. On recharge la
        // trame réelle (resynchronisation) puis on affiche l'erreur causale.
        await get().openDocument(documentId);
        set({ error: e.message || 'Réorganisation incomplète - la trame a été rechargée.' });
      } else {
        const message = e instanceof Error ? e.message : 'Impossible de réorganiser la trame.';
        set({ error: message });
      }
    }
  },

  setSectionActive: (sectionId) => set({ sectionActive: sectionId }),

  // ============================================================
  // Rédaction (streaming SSE)
  // ============================================================

  draftSection: async (sectionId, instruction) => {
    // Un nouveau draft annule silencieusement un stream précédent encore actif.
    draftAbortController?.abort();
    const controller = new AbortController();
    draftAbortController = controller;

    // Id du document actif capturé AU DÉMARRAGE (finding B) : le chunk `done`
    // ne doit recharger que si ce document est TOUJOURS l'actif à la fin du
    // stream (sinon on rechargerait le mauvais document après une bascule).
    const documentId = get().currentDocument?.id;

    // Finding A : reset du contenu de la section ciblée AVANT toute
    // consommation du stream (retouche ET première rédaction) - le backend
    // émet des deltas et remplace `content` par l'accumulé côté base, le
    // store doit repartir de zéro pour rester en miroir exact.
    set((s) => ({
      isStreaming: true,
      error: null,
      sectionActive: sectionId,
      currentDocument: s.currentDocument
        ? patchSection(s.currentDocument, sectionId, (section) => ({ ...section, content: '' }))
        : s.currentDocument,
    }));

    try {
      for await (const chunk of apiDraftSection(sectionId, instruction, controller.signal)) {
        if (chunk.type === 'text') {
          const delta = chunk.content ?? '';
          set((s) => {
            if (!s.currentDocument) return s;
            return {
              currentDocument: patchSection(s.currentDocument, sectionId, (section) => ({
                ...section,
                content: section.content + delta,
                status: 'brouillon',
              })),
            };
          });
        } else if (chunk.type === 'error') {
          // Le contenu déjà streamé depuis CE démarrage (chunks 'text'
          // précédents) reste en l'état - le backend l'a lui-même persisté,
          // zéro perte.
          set({ isStreaming: false, error: chunk.content || 'Erreur pendant la rédaction.' });
          return;
        } else if (chunk.type === 'done') {
          // Contenu canonique (sans bloc PISTES) + nouvelles pistes : on
          // recharge le document plutôt que de faire confiance au flux -
          // MAIS seulement si le document actif n'a pas changé entretemps.
          if (documentId && get().currentDocument?.id === documentId) {
            await get().openDocument(documentId);
          }
          set({ isStreaming: false });
          return;
        }
      }
      // Générateur épuisé sans chunk terminal explicite : on arrête proprement.
      set({ isStreaming: false });
    } catch (e: any) {
      if (e?.name === 'AbortError') {
        // Annulation volontaire (nouveau draft ou fermeture/changement de
        // document) : sortie silencieuse - le déclencheur de l'abort a déjà
        // géré `isStreaming`, et le backend a persisté le partiel de son
        // côté (son propre `finally`). Rien à afficher, rien à écraser.
        return;
      }
      set({ isStreaming: false, error: e?.message || 'Erreur réseau pendant la rédaction.' });
    } finally {
      if (draftAbortController === controller) {
        draftAbortController = null;
      }
    }
  },

  validateSection: async (sectionId) => {
    set({ error: null });
    try {
      const updated = await apiValidateSection(sectionId);
      set((s) => {
        if (!s.currentDocument) return s;
        const document = patchSection(s.currentDocument, sectionId, () => updated);
        const sections_validees = document.sections.filter((sec) => sec.status === 'validee').length;
        return { currentDocument: { ...document, sections_validees } };
      });
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de valider la section.' });
    }
  },

  // ============================================================
  // Export
  // ============================================================

  exportDocument: async (documentId, format = 'md') => {
    set({ error: null });
    try {
      return await apiExportDocument(documentId, format);
    } catch (e: any) {
      set({ error: e?.message || "Impossible d'exporter le document." });
      return null;
    }
  },

  // ============================================================
  // Pistes
  // ============================================================

  loadPistes: async (documentId) => {
    set({ error: null });
    try {
      const pistes = await apiListPistes(documentId);
      set((s) => {
        if (!s.currentDocument || s.currentDocument.id !== documentId) return s;
        return { currentDocument: { ...s.currentDocument, pistes } };
      });
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de charger les pistes.' });
    }
  },

  createPiste: async (documentId, payload) => {
    set({ error: null });
    try {
      const piste = await apiCreatePiste(documentId, payload);
      set((s) => {
        if (!s.currentDocument || s.currentDocument.id !== documentId) return s;
        return { currentDocument: { ...s.currentDocument, pistes: [...s.currentDocument.pistes, piste] } };
      });
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de capturer la piste.' });
    }
  },

  updatePiste: async (pisteId, status) => {
    set({ error: null });
    try {
      const updated = await apiUpdatePiste(pisteId, status);
      set((s) => {
        if (!s.currentDocument) return s;
        return {
          currentDocument: {
            ...s.currentDocument,
            pistes: s.currentDocument.pistes.map((p) => (p.id === pisteId ? updated : p)),
          },
        };
      });
    } catch (e: any) {
      set({ error: e?.message || 'Impossible de mettre à jour la piste.' });
    }
  },

  // ============================================================
  // UI
  // ============================================================

  clearError: () => set({ error: null }),
}));
