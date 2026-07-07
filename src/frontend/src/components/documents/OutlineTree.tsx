/**
 * THÉRÈSE v2 - OutlineTree (Atelier documentaire, D3)
 *
 * Trame draggable du document actif : liste triée par `order`, indentation
 * par `depth`, statuts en tags carrés theme-aware. Composant purement
 * présentationnel (props uniquement, aucun accès direct au store) - même
 * découplage que `ProjectsKanban.tsx` (le parent, ici `DocumentWorkspace`,
 * fait le pont avec `documentStore`).
 *
 * Drag & drop @dnd-kit - pattern BUG-041 (PR #92, `ProjectsKanban.tsx`) :
 * les listeners couvrent TOUTE la ligne (pas une poignée), `onDragCancel`
 * est géré, `activationConstraint` (distance 8px) laisse le clic simple
 * (sélection de section) fonctionner sans déclencher de drag parasite. NE
 * PAS revenir au pattern poignée-seule (dette historique documentée dans
 * CLAUDE.md pour TaskKanban.tsx).
 */
import { useMemo, useState } from 'react';
import { GripVertical, Loader2, Plus, Sparkles } from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  useSensor,
  useSensors,
  PointerSensor,
  KeyboardSensor,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Button } from '../ui/Button';
import type { DocumentSection, SectionCreateRequest, SectionsReorderItem } from '../../services/api/documents';
import { computeReorderPayload } from './reorderPayload';

// =============================================================================
// STATUTS (tags carrés theme-aware)
// =============================================================================

const STATUS_META: Record<DocumentSection['status'], { label: string; className: string }> = {
  vide: { label: 'Vide', className: 'text-text-muted border-border/40 bg-surface' },
  brouillon: { label: 'Brouillon', className: 'text-warning border-warning/30 bg-warning/10' },
  validee: { label: 'Validée', className: 'text-success border-success/30 bg-success/10' },
};

function StatusTag({ status }: { status: DocumentSection['status'] }) {
  const meta = STATUS_META[status];
  return (
    <span
      className={`shrink-0 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide rounded-[6px] border ${meta.className}`}
    >
      {meta.label}
    </span>
  );
}

// =============================================================================
// PROPS
// =============================================================================

export interface OutlineTreeProps {
  sections: DocumentSection[];
  activeSectionId: string | null;
  isLoading: boolean;
  error: string | null;
  onSelect: (sectionId: string) => void;
  onReorder: (items: SectionsReorderItem[]) => void;
  onCreateSection: (payload: SectionCreateRequest) => void;
  onGenerateOutline: () => void;
}

// =============================================================================
// COMPOSANT PRINCIPAL
// =============================================================================

export function OutlineTree({
  sections,
  activeSectionId,
  isLoading,
  error,
  onSelect,
  onReorder,
  onCreateSection,
  onGenerateOutline,
}: OutlineTreeProps) {
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [addingSection, setAddingSection] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newBrief, setNewBrief] = useState('');
  const [newDepth, setNewDepth] = useState<0 | 1>(0);

  const sortedSections = useMemo(() => [...sections].sort((a, b) => a.order - b.order), [sections]);
  const draggingSection = useMemo(
    () => sortedSections.find((s) => s.id === draggingId) ?? null,
    [sortedSections, draggingId]
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor)
  );

  function handleDragStart(event: DragStartEvent) {
    setDraggingId(event.active.id as string);
  }

  function handleDragEnd(event: DragEndEvent) {
    setDraggingId(null);
    const { active, over } = event;
    if (!over) return;
    const items = computeReorderPayload(sortedSections, active.id as string, over.id as string);
    if (items) onReorder(items);
  }

  function resetForm() {
    setNewTitle('');
    setNewBrief('');
    setNewDepth(0);
    setAddingSection(false);
  }

  function handleCreateSection() {
    const title = newTitle.trim();
    if (!title) return;
    const maxOrder = sortedSections.length > 0 ? sortedSections[sortedSections.length - 1].order : 0;
    onCreateSection({ title, brief: newBrief.trim(), order: maxOrder + 10, depth: newDepth });
    resetForm();
  }

  return (
    <div className="flex flex-col h-full" data-testid="outline-tree">
      <div className="flex items-center justify-between gap-2 px-3 py-2.5 border-b border-border/40 shrink-0">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Trame</h2>
        <Button variant="ghost" size="sm" onClick={() => setAddingSection((v) => !v)}>
          <Plus className="w-4 h-4 mr-1" />
          Ajouter une section
        </Button>
      </div>

      {error && (
        <div className="mx-3 mt-2 px-3 py-2 rounded-[6px] border border-error/30 bg-error/10 text-xs text-error">
          {error}
        </div>
      )}

      {addingSection && (
        <div className="mx-3 mt-2 p-3 rounded-lg border border-border/40 bg-surface/60 space-y-2">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Titre de la section"
            aria-label="Titre de la nouvelle section"
            className="w-full px-2.5 py-1.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
            autoFocus
          />
          <textarea
            value={newBrief}
            onChange={(e) => setNewBrief(e.target.value)}
            placeholder="Consigne (optionnel)"
            aria-label="Consigne de la nouvelle section"
            rows={2}
            className="w-full px-2.5 py-1.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
          />
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">Niveau</span>
            <button
              type="button"
              onClick={() => setNewDepth(0)}
              className={`px-2 py-1 text-xs rounded-[6px] border transition-colors ${
                newDepth === 0
                  ? 'border-accent-cyan text-accent-cyan bg-accent-cyan/10'
                  : 'border-border/40 text-text-muted'
              }`}
            >
              Niveau 1
            </button>
            <button
              type="button"
              onClick={() => setNewDepth(1)}
              className={`px-2 py-1 text-xs rounded-[6px] border transition-colors ${
                newDepth === 1
                  ? 'border-accent-cyan text-accent-cyan bg-accent-cyan/10'
                  : 'border-border/40 text-text-muted'
              }`}
            >
              Niveau 2
            </button>
          </div>
          <div className="flex items-center justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" onClick={resetForm}>
              Annuler
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreateSection} disabled={!newTitle.trim()}>
              Créer
            </Button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto py-1">
        {sortedSections.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-10 px-4 text-center">
            <p className="text-xs text-text-muted">Aucune section pour l&apos;instant.</p>
            <Button variant="secondary" size="sm" onClick={onGenerateOutline} disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4 mr-1.5" />
              )}
              Générer la trame
            </Button>
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDragCancel={() => setDraggingId(null)}
          >
            <SortableContext items={sortedSections.map((s) => s.id)} strategy={verticalListSortingStrategy}>
              {sortedSections.map((section) => (
                <SortableSectionRow
                  key={section.id}
                  section={section}
                  isActive={section.id === activeSectionId}
                  onSelect={onSelect}
                />
              ))}
            </SortableContext>
            <DragOverlay>{draggingSection && <SectionRow section={draggingSection} isActive={false} isOverlay />}</DragOverlay>
          </DndContext>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// LIGNE SORTABLE (wrapper avec listeners sur TOUT le corps - BUG-041)
// =============================================================================

interface SortableSectionRowProps {
  section: DocumentSection;
  isActive: boolean;
  onSelect: (sectionId: string) => void;
}

function SortableSectionRow({ section, isActive, onSelect }: SortableSectionRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: section.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  // BUG-041 : les listeners couvrent TOUT le wrapper (pas une poignée
  // isolée) - attraper la ligne par son corps démarre le drag. Le clic
  // simple (sélection) reste distingué du drag par l'activationConstraint
  // (distance 8px) du PointerSensor, pas par une zone de listener réduite.
  return (
    <div ref={setNodeRef} style={style} className="cursor-grab active:cursor-grabbing" {...attributes} {...listeners}>
      <SectionRow section={section} isActive={isActive} onSelect={onSelect} />
    </div>
  );
}

// =============================================================================
// LIGNE (visuel)
// =============================================================================

interface SectionRowProps {
  section: DocumentSection;
  isActive: boolean;
  isOverlay?: boolean;
  onSelect?: (sectionId: string) => void;
}

function SectionRow({ section, isActive, isOverlay, onSelect }: SectionRowProps) {
  return (
    <div
      className={`mx-2 my-0.5 rounded-lg border transition-colors ${
        isOverlay
          ? 'shadow-xl ring-2 ring-accent-cyan/30 bg-surface border-border'
          : isActive
          ? 'border-accent-cyan/50 bg-accent-cyan/10'
          : 'border-transparent hover:bg-surface/60 hover:border-border/40'
      }`}
      style={{ paddingLeft: section.depth * 16 }}
    >
      <button type="button" onClick={() => onSelect?.(section.id)} className="w-full flex items-center gap-2 px-2.5 py-2 text-left">
        <GripVertical className="w-3.5 h-3.5 text-text-muted/30 shrink-0" />
        <span className="text-sm text-text truncate flex-1 min-w-0">{section.title}</span>
        <StatusTag status={section.status} />
      </button>
    </div>
  );
}
