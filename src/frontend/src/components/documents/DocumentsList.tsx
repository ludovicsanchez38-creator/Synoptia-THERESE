/**
 * THÉRÈSE v2 - DocumentsList (Atelier documentaire, D2)
 *
 * Vue « Documents » du routeur content-swap : liste des documents avec
 * progression (sections validées / total), création via une modale légère
 * (titre + brief + projet lié optionnel), vide guidé.
 *
 * Le clic sur un document appelle `openDocument` du documentStore (D1) ;
 * la bascule liste <-> atelier est un état LOCAL (workspaceOpenId).
 * L'atelier lui-même (trame draggable + éditeur de section, D3) vit dans
 * `DocumentWorkspace` - il gère son propre cycle de vie de fermeture
 * (`closeDocument()` du store, appelé avant `onBack`).
 *
 * Échap : NE PAS ajouter d'écouteur clavier local - `resolveEscape` gère
 * déjà le retour de vue (content-swap) et la pile pushEscapeHandler gère
 * la modale de création (comme ProjectsPanel pour ProjectModal).
 *
 * Ouverture de la modale depuis ⌘K/Accueil (D4, action `documents.new`) :
 * `modalOpen` reste un état LOCAL (comme avant D4) pour tous les chemins
 * d'ouverture existants (clic sur les boutons « Nouveau document » de cette
 * vue) - seul un nouveau chemin s'y ajoute, `documentStore.createModalRequested`,
 * un drapeau ponctuel consommé une fois au montage (et à chaque fois qu'il
 * passe à `true` pendant que la vue est déjà montée). Ce drapeau vit dans le
 * store plutôt qu'un CustomEvent car l'action peut se déclencher AVANT que
 * cette vue ne soit montée (⌘K depuis une autre vue) - un event DOM dispatché
 * avant l'attache du listener serait perdu, un state Zustand déjà posé est lu
 * correctement au premier rendu.
 */
import { useCallback, useEffect, useState } from 'react';
import { FileText, Loader2, Plus } from 'lucide-react';
import { useDocumentStore } from '../../stores/documentStore';
import type { DocumentResponse } from '../../services/api/documents';
import { Button } from '../ui/Button';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { DocumentCreateModal } from './DocumentCreateModal';
import { DocumentWorkspace } from './DocumentWorkspace';

// =============================================================================
// PROGRESSION
// =============================================================================

interface DocumentProgressProps {
  total: number;
  validated: number;
}

function DocumentProgress({ total, validated }: DocumentProgressProps) {
  const pct = total > 0 ? Math.round((validated / total) * 100) : 0;
  const label = total > 0 ? `${validated}/${total} sections validées` : 'Trame non générée';

  return (
    <div className="flex items-center gap-2">
      <div
        className="flex-1 h-1.5 rounded-full bg-border/40 overflow-hidden"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div className="h-full bg-success transition-[width] duration-300" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-text-muted whitespace-nowrap">{label}</span>
    </div>
  );
}

// =============================================================================
// CARTE DOCUMENT
// =============================================================================

interface DocumentCardProps {
  document: DocumentResponse;
  onOpen: (id: string) => void;
}

function DocumentCard({ document, onOpen }: DocumentCardProps) {
  const isTermine = document.status === 'termine';

  return (
    <button
      type="button"
      onClick={() => onOpen(document.id)}
      className="w-full text-left px-4 py-3 rounded-xl border border-border/40 bg-surface/60 hover:bg-surface hover:border-border transition-colors"
      data-testid="document-card"
    >
      <div className="flex items-center gap-2 min-w-0">
        <p className="text-sm font-medium text-text truncate">{document.title}</p>
        <span
          className={`shrink-0 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide rounded-[6px] border ${
            isTermine
              ? 'text-success border-success/30 bg-success/10'
              : 'text-warning border-warning/30 bg-warning/10'
          }`}
        >
          {isTermine ? 'Terminé' : 'En cours'}
        </span>
      </div>
      {document.brief && <p className="text-xs text-text-muted truncate mt-1">{document.brief}</p>}
      <div className="mt-3">
        <DocumentProgress total={document.sections_total} validated={document.sections_validees} />
      </div>
    </button>
  );
}

// =============================================================================
// VUE PRINCIPALE
// =============================================================================

export function DocumentsList() {
  const documents = useDocumentStore((s) => s.documents);
  const isLoading = useDocumentStore((s) => s.isLoading);
  const error = useDocumentStore((s) => s.error);
  const loadDocuments = useDocumentStore((s) => s.loadDocuments);
  const openDocument = useDocumentStore((s) => s.openDocument);
  const createModalRequested = useDocumentStore((s) => s.createModalRequested);
  const clearCreateModalRequest = useDocumentStore((s) => s.clearCreateModalRequest);

  const [modalOpen, setModalOpen] = useState(false);
  // Bascule liste <-> atelier (DocumentWorkspace, D3). État local
  // volontairement : le store ne porte pas de notion de "vue courante",
  // seulement les données du document ouvert.
  const [workspaceOpenId, setWorkspaceOpenId] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // D4 : ouverture de la modale demandée depuis ⌘K/Accueil (documents.new).
  // Dépend de createModalRequested (pas juste [] au montage) pour couvrir
  // aussi le cas où la vue est DÉJÀ montée quand l'action se déclenche.
  //
  // Revue finale (finding minor 4) : si l'atelier (DocumentWorkspace) est
  // ouvert, cette vue rend la branche `workspaceOpenId` plus bas - le bloc
  // qui contient la modale n'est PAS monté. Consommer quand même le drapeau
  // (poser modalOpen=true + le clear) ne produisait aucun effet visible
  // immédiat, mais laissait modalOpen=true en mémoire : au retour à la liste
  // (fermeture de l'atelier), la modale surgissait sans geste explicite de
  // l'utilisateur. Fix : le drapeau est TOUJOURS effacé (la demande est
  // consommée, jamais mise en file d'attente), mais l'ouverture de la
  // modale elle-même n'a lieu que si l'atelier n'est pas ouvert.
  useEffect(() => {
    if (!createModalRequested) return;
    if (workspaceOpenId === null) {
      setModalOpen(true);
    }
    clearCreateModalRequest();
  }, [createModalRequested, clearCreateModalRequest, workspaceOpenId]);

  // La modale de création s'inscrit sur la pile Échap unifiée (comme
  // ProjectsPanel pour ProjectModal) - PAS d'écouteur clavier local ici.
  useEffect(() => {
    if (!modalOpen) return;
    return pushEscapeHandler(() => setModalOpen(false));
  }, [modalOpen]);

  const handleOpen = useCallback(
    (id: string) => {
      setWorkspaceOpenId(id);
      openDocument(id);
    },
    [openDocument]
  );

  const handleBackToList = useCallback(() => {
    setWorkspaceOpenId(null);
  }, []);

  if (workspaceOpenId) {
    return <DocumentWorkspace documentId={workspaceOpenId} onBack={handleBackToList} />;
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-bg overflow-y-auto" data-testid="documents-list">
      <div className="max-w-[760px] w-full mx-auto px-5 py-6">
        {/* En-tête */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-[6px] grid place-items-center bg-accent-tint text-accent-cyan border-[1.5px] border-[var(--btn-ink)]">
              <FileText className="w-5 h-5" />
            </span>
            <div>
              <h1 className="text-lg font-bold text-text leading-tight">Documents</h1>
              <p className="text-xs text-text-muted">
                {documents.length} document{documents.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <Button variant="primary" size="sm" onClick={() => setModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            Nouveau document
          </Button>
        </div>

        {error && (
          <div className="mb-4 px-3 py-2 rounded-[6px] border border-error/30 bg-error/10 text-sm text-error">
            {error}
          </div>
        )}

        {/* Contenu */}
        {isLoading && documents.length === 0 ? (
          <div className="flex items-center justify-center gap-2 py-16 text-sm text-text-muted">
            <Loader2 className="w-5 h-5 animate-spin text-accent-cyan" />
            Chargement des documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <FileText className="w-8 h-8 text-text-muted/50" />
            <p className="text-sm text-text-muted max-w-xs">
              Crée ton premier document pour démarrer une proposition, un dossier ou un rapport structuré.
            </p>
            <Button variant="primary" size="sm" onClick={() => setModalOpen(true)}>
              <Plus className="w-4 h-4 mr-1.5" />
              Nouveau document
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <DocumentCard key={doc.id} document={doc} onOpen={handleOpen} />
            ))}
          </div>
        )}
      </div>

      {/* Après création, le document créé apparaît en tête de liste
          (documentStore.createDocument le préfixe déjà) - pas de rechargement
          nécessaire. L'ouverture de l'atelier reste un geste explicite (clic
          sur la carte). */}
      <DocumentCreateModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
