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
 * Revue adversariale lot D (finding E) : le bouton interne « Retour » n'est
 * PAS le seul chemin de sortie de l'atelier - la back-bar « ← Chat » de
 * ChatLayout, Échap (cascade Échap de la coque -> goBack) et les boutons header/⌘K
 * (setView) démontent ce composant SANS passer par `handleBack`. Un effet de
 * nettoyage au DÉMONTAGE appelle donc `closeDocument()` inconditionnellement
 * (idempotent - déjà appelé ou non par `handleBack`), et le rendu est gardé
 * par `doc` (currentDocument SEULEMENT s'il correspond à `documentId`) pour
 * qu'un document précédent encore en mémoire au moment du montage (fenêtre
 * where le nettoyage précédent n'a pas encore été traité) ne flashe jamais.
 *
 * Export : `exportDocument` du store renvoie les métadonnées
 * ({download_url, file_name}) SANS déclencher le téléchargement (décision
 * D1) - le déclenchement navigateur suit la même mécanique que
 * `exportConversation` (chat.ts:282) via `downloadExportedDocument`.
 */
import { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Download } from 'lucide-react';
import { Button } from '../ui/Button';
import { useDocumentStore } from '../../stores/documentStore';
import { downloadExportedDocument, type DocumentPiste } from '../../services/api/documents';
import { OutlineTree } from './OutlineTree';
import { SectionEditor } from './SectionEditor';
import { PistesPanel } from './PistesPanel';
import { Spinner } from '../ui/Spinner';

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

  // Finding E : filet de sécurité au démontage, pour les 3 chemins de sortie
  // qui ne passent PAS par handleBack (back-bar ChatLayout, Échap, boutons
  // header/⌘K). Idempotent avec l'appel déjà fait par handleBack (« Retour »).
  useEffect(() => {
    return () => {
      closeDocument();
    };
  }, [closeDocument]);

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

  // Finding E : currentDocument peut encore porter un AUTRE document au
  // moment du montage (nettoyage précédent pas encore traité, ou store
  // partagé entre deux instances successives) - `doc` ne vaut le document du
  // store QUE s'il correspond à `documentId`, sinon on reste en chargement
  // (aucun contenu d'un document précédent ne doit apparaître, même
  // brièvement).
  const doc = currentDocument && currentDocument.id === documentId ? currentDocument : null;
  const activeSection = doc?.sections.find((s) => s.id === sectionActive) ?? null;

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-bg" data-testid="document-workspace">
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-border/40 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            Retour aux documents
          </Button>
          {doc && <p className="text-sm font-medium text-text truncate">{doc.title}</p>}
        </div>
        {doc && (
          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="sm" onClick={() => handleExport('md')} disabled={exportingFormat !== null}>
              {exportingFormat === 'md' ? (
                <Spinner taille="bouton" className="mr-1.5" />
              ) : (
                <Download className="w-4 h-4 mr-1.5" />
              )}
              Exporter .md
            </Button>
            <Button variant="secondary" size="sm" onClick={() => handleExport('docx')} disabled={exportingFormat !== null}>
              {exportingFormat === 'docx' ? (
                <Spinner taille="bouton" className="mr-1.5" />
              ) : (
                <Download className="w-4 h-4 mr-1.5" />
              )}
              Exporter .docx
            </Button>
          </div>
        )}
      </div>

      {!doc ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Spinner taille="bouton" />
            Chargement du document...
          </div>
        </div>
      ) : (
        <div className="flex-1 min-h-0 flex overflow-hidden">
          <div className="w-72 shrink-0 border-r border-border/40 overflow-y-auto">
            <OutlineTree
              sections={doc.sections}
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

          <PistesPanel pistes={doc.pistes} onExplore={handleExplorePiste} onIgnore={handleIgnorePiste} />
        </div>
      )}
    </div>
  );
}
