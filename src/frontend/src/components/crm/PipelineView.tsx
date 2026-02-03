/**
 * THÉRÈSE v2 - Pipeline View (CRM Phase 5)
 *
 * Vue Kanban du pipeline commercial avec 7 stages.
 * Drag & Drop via @dnd-kit.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Building2, Mail, TrendingUp, GripVertical } from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
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
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { ContactResponse } from '../../services/api';

// Les 7 stages du pipeline
const PIPELINE_STAGES = [
  { id: 'contact', label: 'Contact', color: 'bg-gray-500' },
  { id: 'discovery', label: 'Decouverte', color: 'bg-blue-500' },
  { id: 'proposition', label: 'Proposition', color: 'bg-purple-500' },
  { id: 'signature', label: 'Signature', color: 'bg-yellow-500' },
  { id: 'delivery', label: 'Livraison', color: 'bg-orange-500' },
  { id: 'active', label: 'Actif', color: 'bg-green-500' },
  { id: 'archive', label: 'Archive', color: 'bg-gray-400' },
];

interface PipelineViewProps {
  contacts: ContactResponse[];
  onContactClick: (contact: ContactResponse) => void;
  onStageChange: (contactId: string, newStage: string) => void;
}

export function PipelineView({ contacts, onContactClick, onStageChange }: PipelineViewProps) {
  const [contactsByStage, setContactsByStage] = useState<Record<string, ContactResponse[]>>({});
  const [activeContact, setActiveContact] = useState<ContactResponse | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor)
  );

  useEffect(() => {
    const grouped = PIPELINE_STAGES.reduce((acc, stage) => {
      acc[stage.id] = contacts.filter(c => c.stage === stage.id);
      return acc;
    }, {} as Record<string, ContactResponse[]>);

    setContactsByStage(grouped);
  }, [contacts]);

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

    // Determine the target stage
    let targetStage: string | null = null;

    const stageIds = PIPELINE_STAGES.map((s) => s.id);
    if (stageIds.includes(over.id as string)) {
      targetStage = over.id as string;
    } else {
      // Dropped on a contact card - find which stage it belongs to
      for (const stage of stageIds) {
        if (contactsByStage[stage]?.some((c) => c.id === over.id)) {
          targetStage = stage;
          break;
        }
      }
    }

    if (!targetStage) return;

    const currentContact = contacts.find((c) => c.id === contactId);
    if (!currentContact || currentContact.stage === targetStage) return;

    onStageChange(contactId, targetStage);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4">
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

  return (
    <div ref={setNodeRef} className="flex-shrink-0 w-72">
      {/* Header colonne */}
      <div className={`${stage.color} text-white rounded-t-lg px-4 py-3`}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{stage.label}</h3>
          <span className="text-sm opacity-80">{count}</span>
        </div>
      </div>

      {/* Cards contacts */}
      <div
        className={`bg-surface border border-surface rounded-b-lg p-2 min-h-[200px] space-y-2 transition-colors ${
          isOver ? 'ring-2 ring-accent-cyan/50 bg-accent-cyan/5' : ''
        }`}
      >
        {children}
      </div>
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
    <div ref={setNodeRef} style={style} {...attributes}>
      <ContactCard
        contact={contact}
        onClick={onClick}
        dragListeners={listeners}
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
  dragListeners?: Record<string, unknown>;
}

function ContactCard({ contact, onClick, isOverlay, dragListeners }: ContactCardProps) {
  return (
    <motion.div
      layout={!isOverlay}
      initial={isOverlay ? undefined : { opacity: 0, y: 10 }}
      animate={isOverlay ? undefined : { opacity: 1, y: 0 }}
      exit={isOverlay ? undefined : { opacity: 0, y: -10 }}
      onClick={onClick}
      className={`bg-background border border-surface hover:border-accent-cyan rounded-lg p-3 cursor-pointer transition-colors relative ${
        isOverlay ? 'shadow-xl ring-2 ring-accent-cyan/30' : ''
      }`}
    >
      {/* Drag Handle */}
      {dragListeners && (
        <div
          className="absolute top-3 left-1 cursor-grab active:cursor-grabbing text-text-muted/40 hover:text-text-muted"
          {...dragListeners}
          onClick={(e) => e.stopPropagation()}
        >
          <GripVertical className="w-4 h-4" />
        </div>
      )}

      <div className={dragListeners ? 'pl-5' : ''}>
        {/* Nom */}
        <div className="flex items-center gap-2 mb-2">
          <User className="w-4 h-4 text-text-muted" />
          <span className="font-medium text-sm text-text-primary">
            {contact.first_name} {contact.last_name}
          </span>
        </div>

        {/* Entreprise */}
        {contact.company && (
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <Building2 className="w-3 h-3" />
            <span className="truncate">{contact.company}</span>
          </div>
        )}

        {/* Email */}
        {contact.email && (
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <Mail className="w-3 h-3" />
            <span className="truncate">{contact.email}</span>
          </div>
        )}

        {/* Score */}
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-surface">
          <div className="flex items-center gap-1 text-xs">
            <TrendingUp className="w-3 h-3 text-accent-cyan" />
            <span className="text-text-muted">Score:</span>
            <span className="font-semibold text-accent-cyan">{contact.score}</span>
          </div>

          {contact.source && (
            <span className="text-xs bg-surface px-2 py-0.5 rounded text-text-muted">
              {contact.source}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
