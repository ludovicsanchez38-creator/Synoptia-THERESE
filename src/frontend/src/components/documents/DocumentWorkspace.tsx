/**
 * THÉRÈSE v2 - DocumentWorkspace (Atelier documentaire, D3)
 *
 * Remplace le placeholder posé par `DocumentsList` en D2. Layout : trame
 * (`OutlineTree`) à gauche, éditeur de la section active (`SectionEditor`)
 * au centre, volet Pistes (`PistesPanel`, D4) à droite.
 *
 * Seul composant connecté au store de l'atelier - `OutlineTree`,
 * `SectionEditor` et `PistesPanel` restent des composants présentationnels
 * (props), pattern identique à `ProjectsPanel` -> `ProjectsKanban`.
 *
 * « Explorer » une piste (D4) : passe son statut à `exploree` (updatePiste),
 * sélectionne sa section d'origine (`section_origine_id`) comme section
 * active ET préremplit le champ instruction de `SectionEditor` avec le texte
 * de la piste. Le préremplissage est un état LOCAL à ce composant
 * (`instructionPrefill`, pas dans le store) : c'est une intention UI
 * ponctuelle (« pose ce texte dans ce champ maintenant »), pas une donnée du
 * document - `SectionEditor` la consomme puis appelle
 * `onInstructionPrefillApplied` pour l'effacer ici (anti-réemploi si
 * l'utilisateur revient plus tard sur la même section sans re-explorer).
 *
 * « Retour aux documents » appelle `closeDocument()` du store (reset
 * currentDocument/sectionActive/error, D3) AVANT de rendre la main au
 * parent (`onBack`, bascule locale D2) - sinon le document actuel pourrait
 * flasher au prochain montage de l'atelier (lifecycle laissé ouvert par D2).
 *
 * Export : `exportDocument` du store renvoie les métadonnées
 * ({download_url, file_name}) SANS déclencher le téléchargement (décision
 * D1) - le déclenchement navigateur suit la même mécanique que
 * `exportConversation` (chat.ts:282) via `downloadExportedDocument`.
 */
import { useCallback, useState } from 'react';
import { ArrowLeft, Download, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { useDocumentStore } from '../../stores/documentStore';
import { downloadExportedDocument, type DocumentPiste } from '../../services/api/documents';
import { OutlineTree } from './OutlineTree';
import { SectionEditor } from './SectionEditor';
import { PistesPanel } from './PistesPanel';

export interface DocumentWorkspaceProps {
  documentId: string;
  onBack: () => void;
}

export function DocumentWorkspace({ documentId, onBack }: DocumentWorkspaceProps) {
  const currentDocument = useDocumentStore((s) => s.currentDocument);
  const sectionActive = useDocumentStore((s) => s.sectionActive);
  const isStreaming = useDocumentStore((s) => s.isStreaming);
  const isLoading = useDocumentStore((s) => s.isLoading);
  const error = useDocumentStore((s) => s.error);
  const setSectionActive = useDocumentStore((s) => s.setSectionActive);
  const reorderSections = useDocumentStore((s) => s.reorderSections);
  const createSection = useDocumentStore((s) => s.createSection);
  const generateOutline = useDocumentStore((s) => s.generateOutline);
  const updateSection = useDocumentStore((s) => s.updateSection);
  const draftSection = useDocumentStore((s) => s.draftSection);
  const validateSection = useDocumentStore((s) => s.validateSection);
  const exportDocument = useDocumentStore((s) => s.exportDocument);
  const closeDocument = useDocumentStore((s) => s.closeDocument);
  const updatePiste = useDocumentStore((s) => s.updatePiste);

  const [exportingFormat, setExportingFormat] = useState<'md' | 'docx' | null>(null);
  // Préremplissage ponctuel de l'instruction de SectionEditor (D4, cf.
  // commentaire d'en-tête) - PAS une donnée du document, un état UI local.
  const [instructionPrefill, setInstructionPrefill] = useState<string | null>(null);

  const handleBack = useCallback(() => {
    closeDocument();
    onBack();
  }, [closeDocument, onBack]);

  const handleExport = useCallback(
    async (format: 'md' | 'docx') => {
      setExportingFormat(format);
      try {
        const exported = await exportDocument(documentId, format);
        if (exported) {
          await downloadExportedDocument(exported);
        }
      } catch (e) {
        // exportDocument pose déjà `error` dans le store en cas d'échec API ;
        // seul un échec du DÉCLENCHEMENT du téléchargement (fetch du blob)
        // atterrit ici, sans point d'affichage dédié dans l'atelier.
        console.error('Téléchargement du document impossible :', e);
      } finally {
        setExportingFormat(null);
      }
    },
    [documentId, exportDocument]
  );

  // « Explorer » (D4) : la piste peut ne pas avoir de section d'origine
  // (section_origine_id null) - dans ce cas, on marque juste la piste
  // explorée sans toucher à la sélection ni à l'instruction.
  const handleExplorePiste = useCallback(
    (piste: DocumentPiste) => {
      updatePiste(piste.id, 'exploree');
      if (piste.section_origine_id) {
        setSectionActive(piste.section_origine_id);
        setInstructionPrefill(piste.texte);
      }
    },
    [updatePiste, setSectionActive]
  );

  const handleIgnorePiste = useCallback(
    (piste: DocumentPiste) => {
      updatePiste(piste.id, 'ignoree');
    },
    [updatePiste]
  );

  const activeSection = currentDocument?.sections.find((s) => s.id === sectionActive) ?? null;

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-bg" data-testid="document-workspace">
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-border/40 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            Retour aux documents
          </Button>
          {currentDocument && <p className="text-sm font-medium text-text truncate">{currentDocument.title}</p>}
        </div>
        {currentDocument && (
          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="sm" onClick={() => handleExport('md')} disabled={exportingFormat !== null}>
              {exportingFormat === 'md' ? (
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-1.5" />
              )}
              Exporter .md
            </Button>
            <Button variant="secondary" size="sm" onClick={() => handleExport('docx')} disabled={exportingFormat !== null}>
              {exportingFormat === 'docx' ? (
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-1.5" />
              )}
              Exporter .docx
            </Button>
          </div>
        )}
      </div>

      {!currentDocument ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Loader2 className="w-4 h-4 animate-spin" />
            Chargement du document...
          </div>
        </div>
      ) : (
        <div className="flex-1 min-h-0 flex overflow-hidden">
          <div className="w-72 shrink-0 border-r border-border/40 overflow-y-auto">
            <OutlineTree
              sections={currentDocument.sections}
              activeSectionId={sectionActive}
              isLoading={isLoading}
              error={error}
              onSelect={setSectionActive}
              onReorder={(items) => reorderSections(documentId, items)}
              onCreateSection={(payload) => createSection(documentId, payload)}
              onGenerateOutline={() => generateOutline(documentId)}
            />
          </div>

          <SectionEditor
            section={activeSection}
            isStreaming={isStreaming}
            error={error}
            onUpdateSection={updateSection}
            onDraft={draftSection}
            onValidate={validateSection}
            instructionPrefill={instructionPrefill}
            onInstructionPrefillApplied={() => setInstructionPrefill(null)}
          />

          <PistesPanel pistes={currentDocument.pistes} onExplore={handleExplorePiste} onIgnore={handleIgnorePiste} />
        </div>
      )}
    </div>
  );
}
