/**
 * THÉRÈSE v2 - Pipeline View (CRM Phase 5)
 *
 * Vue Kanban du pipeline commercial avec 7 stages.
 * Drag & Drop via @dnd-kit.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle } from 'lucide-react';
import { Etiquette } from '../ui/Etiquette';
import { cn } from '../../lib/utils';
import { PIPELINE_ETAPES, etiquetteDEtape } from './pipelineEtapes';
import {
  DndContext,
  DragOverlay,
  rectIntersection,
  useSensor,
  useSensors,
  PointerSensor,
  KeyboardSensor,
  useDroppable,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { accessibiliteGlisserDeposer } from '../../lib/accessibiliteGlisserDeposer';
import { useDemoMask } from '../../hooks';
import type { ContactResponse } from '../../services/api';

const PIPELINE_STAGES = PIPELINE_ETAPES;

interface PipelineViewProps {
  contacts: ContactResponse[];
  onContactClick: (contact: ContactResponse) => void;
  onStageChange: (contactId: string, newStage: string) => void;
}

export function PipelineView({ contacts, onContactClick, onStageChange }: PipelineViewProps) {
  const { maskText } = useDemoMask();
  const [contactsByStage, setContactsByStage] = useState<Record<string, ContactResponse[]>>({});
  const [activeContact, setActiveContact] = useState<ContactResponse | null>(null);

  // B-237 : sans `coordinateGetter`, dnd-kit avance son pointeur virtuel de
  // 25 px par flèche — dans des colonnes minmax(15rem, 1fr), la carte
  // reste au-dessus d'elle-même et aucune cible n'est jamais annoncée.
  // `sortableKeyboardCoordinates` saute de conteneur en conteneur.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  useEffect(() => {
    const grouped = PIPELINE_STAGES.reduce((acc, stage) => {
      acc[stage.id] = contacts.filter(c => c.stage === stage.id);
      return acc;
    }, {} as Record<string, ContactResponse[]>);

    setContactsByStage(grouped);
  }, [contacts]);

  // B-237 : Échap pendant un glissé descendait toute la cascade de la coque
  // jusqu'à `collapseEmbeddedView()` — la vue CRM entière se fermait au geste
  // qui devait seulement annuler le déplacement. dnd-kit écoute sur `document`
  // et a déjà annulé quand la coque, qui écoute sur `window`, prend la main :
  // il ne reste qu'à absorber la touche. Le handler se retire à l'annulation
  // (`onDragCancel`), faute de quoi il avalerait TOUS les Échap suivants.
  useEffect(() => {
    if (!activeContact) return;
    return pushEscapeHandler(() => {});
  }, [activeContact]);

  /** Colonne visée par une cible de dépôt : une colonne, ou la carte survolée. */
  function stageDepuisCible(overId: string): string | null {
    const stageIds: string[] = PIPELINE_STAGES.map((s) => s.id);
    if (stageIds.includes(overId)) return overId;
    for (const stage of stageIds) {
      if (contactsByStage[stage]?.some((c) => c.id === overId)) return stage;
    }
    return null;
  }

  function nomDuContact(contactId: string): string {
    const contact = contacts.find((c) => c.id === contactId);
    if (!contact) return 'Contact';
    const nom = [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Contact';
    return maskText(nom);
  }

  function libelleDuStage(stageId: string | null): string | null {
    return PIPELINE_STAGES.find((s) => s.id === stageId)?.label ?? null;
  }

  function handleDragStart(event: DragStartEvent) {
    const contactId = event.active.id as string;
    const contact = contacts.find((c) => c.id === contactId);
    if (contact) setActiveContact(contact);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveContact(null);

    const { active, over } = event;
    if (!over) return;

    const contactId = active.id as string;

    const targetStage = stageDepuisCible(over.id as string);

    if (!targetStage) return;

    const currentContact = contacts.find((c) => c.id === contactId);
    if (!currentContact || currentContact.stage === targetStage) return;

    onStageChange(contactId, targetStage);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={rectIntersection}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setActiveContact(null)}
      // B-237 puis B-441 : consignes et annonces en français, par les noms,
      // depuis le jeu PARTAGÉ des trois autres tableaux (un seul lexique).
      accessibility={accessibiliteGlisserDeposer((id) => {
        const identifiant = String(id);
        const stage = libelleDuStage(identifiant);
        if (stage) return `la colonne ${stage}`;
        return contacts.some((c) => c.id === identifiant)
          ? `la carte de ${nomDuContact(identifiant)}`
          : null;
      })}
    >
      <div className="grid grid-flow-col auto-cols-[minmax(15rem,1fr)] gap-3 overflow-x-auto pb-2 snap-x snap-proximity">
        {PIPELINE_STAGES.map((stage) => (
          <DroppableStage key={stage.id} stage={stage} count={contactsByStage[stage.id]?.length || 0}>
            <SortableContext
              items={(contactsByStage[stage.id] || []).map((c) => c.id)}
              strategy={verticalListSortingStrategy}
            >
              <AnimatePresence>
                {contactsByStage[stage.id]?.map((contact) => (
                  <SortableContactCard
                    key={contact.id}
                    contact={contact}
                    onClick={() => onContactClick(contact)}
                  />
                ))}
              </AnimatePresence>
            </SortableContext>
          </DroppableStage>
        ))}
      </div>

      <DragOverlay>
        {activeContact && (
          <ContactCard contact={activeContact} onClick={() => {}} isOverlay />
        )}
      </DragOverlay>
    </DndContext>
  );
}

// =============================================================================
// DROPPABLE STAGE COLUMN
// =============================================================================

interface DroppableStageProps {
  stage: (typeof PIPELINE_STAGES)[number];
  count: number;
  children: React.ReactNode;
}

function DroppableStage({ stage, count, children }: DroppableStageProps) {
  const { isOver, setNodeRef } = useDroppable({ id: stage.id });
  const etiquette = etiquetteDEtape(stage.id);

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'snap-start min-h-[22rem] bg-surface-2 rounded-md p-2 grid gap-2 content-start',
        isOver && 'ring-2 ring-ring bg-accent-tint',
      )}
    >
      <div className="flex items-center gap-2 px-2 py-1">
        <h3>
          <Etiquette domaine={etiquette.domaine} ton={etiquette.ton}>
            {stage.label}
          </Etiquette>
        </h3>
        <span className="ml-auto text-sm font-medium text-text-muted tabular-nums">{count}</span>
      </div>
      {children}
    </div>
  );
}

// =============================================================================
// SORTABLE CONTACT CARD
// =============================================================================

interface SortableContactCardProps {
  contact: ContactResponse;
  onClick: () => void;
}

function SortableContactCard({ contact, onClick }: SortableContactCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: contact.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div
      ref={(node) => { setNodeRef(node); setActivatorNodeRef(node); }}
      style={style}
      {...attributes}
      {...listeners}
    >
      <ContactCard
        contact={contact}
        onClick={onClick}
      />
    </div>
  );
}

// =============================================================================
// CONTACT CARD
// =============================================================================

interface ContactCardProps {
  contact: ContactResponse;
  onClick: () => void;
  isOverlay?: boolean;
}

const SCORE_AIDE =
  "Score de potentiel commercial, calculé depuis les informations du contact et son étape dans le pipeline. Plus il est haut, plus le prospect est chaud. L'échelle n'est pas plafonnée.";

function ContactCard({ contact, onClick, isOverlay }: ContactCardProps) {
  return (
    <motion.div
      /* B-151 : repère par élément pour les protocoles (`qsa`). Pas sur la
         carte de survol du drag, qui doublerait le comptage. */
      data-testid={isOverlay ? undefined : 'crm-contact-item'}
      aria-grabbed={isOverlay ? true : undefined}
      layout={!isOverlay}
      initial={isOverlay ? undefined : { opacity: 0, y: 10 }}
      animate={isOverlay ? undefined : { opacity: 1, y: 0 }}
      exit={isOverlay ? undefined : { opacity: 0, y: -10 }}
      onClick={onClick}
      className={cn(
        'bg-surface border border-border rounded-sm p-3 cursor-grab text-sm',
        isOverlay && 'outline outline-2 outline-dashed outline-accent outline-offset-2 bg-accent-tint',
      )}
    >
      <div className="font-semibold">
        {contact.first_name} {contact.last_name}
      </div>

      {contact.company && (
        <p className="text-sm text-text-muted truncate">{contact.company}</p>
      )}

      {contact.email && (
        <p className="text-sm text-text-muted truncate">{contact.email}</p>
      )}

      <div className="flex flex-wrap gap-2 items-center text-sm text-text-muted mt-2">
        <div className="flex items-center gap-1" title={SCORE_AIDE}>
          <span>Score</span>
          <span className="tabular-nums font-semibold text-text">{contact.score}</span>
          <HelpCircle size={18} className="text-text-muted" aria-label={SCORE_AIDE} />
        </div>

        {contact.source ? <Etiquette ton="neutre">{contact.source}</Etiquette> : null}
      </div>
    </motion.div>
  );
}
