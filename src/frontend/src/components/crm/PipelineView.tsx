/**
 * THÉRÈSE v2 - Pipeline View (CRM Phase 5)
 *
 * Vue Kanban du pipeline commercial avec 7 stages.
 * Drag & Drop via @dnd-kit.
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle } from 'lucide-react';
import { Etiquette } from '../ui/Etiquette';
import { cn } from '../../lib/utils';
import { PIPELINE_ETAPES, SCORE_AIDE, etiquetteDEtape } from './pipelineEtapes';
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
import { accessibiliteGlisserDeposer, laCarteDe } from '../../lib/accessibiliteGlisserDeposer';
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
  // B-1383 : la carte déposée dans une autre colonne n'y apparaît qu'après la
  // réponse du moteur, sous un autre parent : l'ancien nœud part avec le
  // focus. On retient la carte pour lui rendre le focus dans sa colonne.
  const carteDeposee = useRef<{ id: string; stage: string } | null>(null);
  const grilleRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    const deposee = carteDeposee.current;
    if (!deposee || !contactsByStage[deposee.stage]?.some((c) => c.id === deposee.id)) return;
    carteDeposee.current = null;
    const selecteur = `[data-colonne="${echapperPourCss(deposee.stage)}"] [data-carte="${echapperPourCss(deposee.id)}"]`;
    const nouvelle = grilleRef.current?.querySelector<HTMLElement>(selecteur);
    const actif = document.activeElement as HTMLElement | null;
    // Seulement si le focus est perdu (page) ou resté sur l'ancienne carte :
    // un focus posé ailleurs entre-temps n'est pas volé.
    const focusPerdu = !actif || actif === document.body || actif.dataset.carte === deposee.id;
    if (nouvelle && focusPerdu && actif !== nouvelle) nouvelle.focus();
  }, [contactsByStage]);

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

    carteDeposee.current = { id: contactId, stage: targetStage };
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
          ? laCarteDe(nomDuContact(identifiant))
          : null;
      })}
    >
      <div ref={grilleRef} className="grid grid-flow-col auto-cols-[minmax(15rem,1fr)] gap-3 overflow-x-auto pb-2 snap-x snap-proximity">
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

/** `CSS.escape` n'existe pas partout (jsdom ancien) : repli sur les guillemets. */
function echapperPourCss(valeur: string): string {
  return typeof globalThis.CSS?.escape === 'function' ? globalThis.CSS.escape(valeur) : valeur.replace(/["\\]/g, '\\$&');
}

function DroppableStage({ stage, count, children }: DroppableStageProps) {
  const { isOver, setNodeRef } = useDroppable({ id: stage.id });
  const etiquette = etiquetteDEtape(stage.id);

  return (
    <div
      ref={setNodeRef}
      data-colonne={stage.id}
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
  const { maskText: masquer } = useDemoMask();
  // B-877 : le conteneur triable garde pour nom le seul nom du contact ; sans
  // cela, le bouton « Ouvrir la fiche » entrerait dans son nom calculé.
  const nomAccessible = masquer([contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Contact');
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
      aria-label={nomAccessible}
      data-carte={contact.id}
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


function ContactCard({ contact, onClick, isOverlay }: ContactCardProps) {
  const { maskText: masquer } = useDemoMask();
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
      {/* B-845 : en démonstration, la carte passe par le même masque que
          l'annonce de déplacement ; sinon le vrai client restait à l'écran. */}
      <div className="font-semibold">
        {masquer([contact.first_name, contact.last_name].filter(Boolean).join(' '))}
      </div>

      {contact.company && (
        <p className="text-sm text-text-muted truncate">{masquer(contact.company)}</p>
      )}

      {contact.email && (
        <p className="text-sm text-text-muted truncate">{masquer(contact.email)}</p>
      )}

      {/* B-877 : un vrai bouton pour ouvrir la fiche au clavier ; le conteneur
          dnd-kit réserve Entrée et Espace au glisser, d'où l'arrêt de la
          propagation. Pas sur la carte de survol du drag. */}
      {!isOverlay && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onClick(); }}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') e.stopPropagation(); }}
          onPointerDown={(e) => e.stopPropagation()}
          className="mt-2 inline-flex min-h-6 items-center rounded-sm border border-border px-2 text-sm text-text-muted hover:text-text focus-visible:outline-2 focus-visible:outline-accent"
        >
          Ouvrir la fiche
        </button>
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
