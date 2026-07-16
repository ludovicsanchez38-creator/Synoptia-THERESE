import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { AnimatePresence, motion, useIsPresent } from 'framer-motion';
import {
  ArrowUp,
  Bot,
  Briefcase,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Folder,
  HardDrive,
  History,
  Loader2,
  Mail,
  Menu,
  MessageSquare,
  PanelRightClose,
  Plus,
  Receipt,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import {
  CapabilityCenter,
  TrustCenter,
  capabilities,
  featuredCapabilities,
  type CapabilityItem,
} from './CapabilityCenter';
import { CharacterPortrait } from './DecisionMissionPrototype';
import { WindowControls } from '../window/WindowControls';
import { startWindowDrag } from '../../lib/windowChrome';
import {
  AtelierHistoryCard,
  AtelierWorkspaceCanvas,
  type AtelierReviewAction,
  type AtelierTarget,
} from './AtelierConversationCard';
import { BoardHistoryCard, BoardWorkspaceCanvas, type BoardTarget } from './BoardConversationCard';
import { ContactsMemoryCanvas, ContactsMemoryCard } from './ContactsMemoryCard';
import { EmailInboxCard, EmailMessageCanvas } from './EmailConversationCard';
import { InvoiceWorkspaceCanvas, InvoiceWorkspaceCard } from './InvoiceConversationCard';
import {
  MeetingAgendaCard,
  MeetingWorkspaceCanvas,
  type MeetingTarget,
} from './MeetingConversationCard';
import { TodayDashboardCard } from './TodayDashboardCard';
import { CalculatorWorkspaceCanvas } from './CalculatorWorkspaceCanvas';
import { DeliverablesWorkspaceCanvas } from './DeliverablesWorkspaceCanvas';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';
import { FollowUpsWorkspaceCanvas } from './FollowUpsWorkspaceCanvas';
import { VoiceWorkspaceCanvas } from './VoiceWorkspaceCanvas';
import {
  PrototypeConversationDrawer,
  type PrototypeConversationDrawerSurface,
} from './PrototypeConversationDrawer';
import { PrototypeChatSurface } from './PrototypeChatSurface';
import { PrototypeUnifiedViewCanvas } from './PrototypeUnifiedViewCanvas';
import { usePrototypeEmailData, type EmailLength, type EmailTone } from './usePrototypeEmailData';
import { usePrototypeInvoiceData, type InvoiceWorkspaceData } from './usePrototypeInvoiceData';
import {
  meetingEventKey,
  usePrototypeMeetingData,
  type MeetingWorkspaceData,
} from './usePrototypeMeetingData';
import { usePrototypeBoardData, type BoardWorkspaceData } from './usePrototypeBoardData';
import { usePrototypeAtelierData, type AtelierWorkspaceData } from './usePrototypeAtelierData';
import { useContactsResource, useTodayDashboardResource, type ReadResource } from './usePrototypeReadData';
import { getActions, runAction } from '../../lib/actionRegistry';
import type { CreateInvoiceRequest, Invoice } from '../../services/api/invoices';
import type { EmailMessage, SendEmailRequest } from '../../services/api/email';
import type { Contact } from '../../services/api/memory';
import type { BoardDecisionDetail, BoardRequest } from '../../services/api/board';
import type { AgentTaskResponse, DiffResponse } from '../../services/api/agents';
import type { CalendarEvent, CreateEventRequest } from '../../services/api/calendar';
import type { ActivityResponse } from '../../services/api/crm-extended';
import { getProfile, type UserProfile } from '../../services/api/config';
import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { useConversationSync } from '../../hooks/useConversationSync';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { usePanelStore } from '../../stores/panelStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { useAtelierStore } from '../../stores/atelierStore';
import { useDemoStore } from '../../stores/demoStore';
import type { AppView } from '../../stores/navigationStore';
import { PanelContainer } from '../chat/PanelContainer';
import { listUserCommands, type UserCommand } from '../../services/api/commands';
import type { SlashCommand } from '../chat/SlashCommandsMenu';
import { ShortcutsModal } from '../chat/ShortcutsModal';
import { VoiceDictationButton } from '../chat/VoiceDictationButton';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

type Scenario = 'today' | 'memory' | 'email' | 'meeting' | 'invoice' | 'board' | 'atelier';
type RightPanelTool = 'calculator' | 'deliverables' | 'images' | 'follow-ups' | 'voice';
type CollapsedRightPanel =
  | { kind: 'embedded'; view: Exclude<AppView, 'chat'> }
  | { kind: 'scenario'; scenario: Exclude<Scenario, 'today'> }
  | { kind: 'tool'; tool: RightPanelTool };

const scenarioLabels: Record<Scenario, string> = {
  today: 'Mes priorités du jour',
  memory: 'Retrouver un contact',
  email: 'Consulter mes emails',
  meeting: 'Préparer un rendez-vous',
  invoice: 'Créer un devis',
  board: 'Éclairer une décision',
  atelier: 'Confier une mission',
};

const scenarioPrompts: Record<Scenario, string> = {
  today: "Qu'est-ce qui demande mon attention aujourd'hui ?",
  memory: 'Retrouve mes contacts récents et leur contexte mémorisé.',
  email: 'Montre-moi les messages à traiter et aide-moi à préparer une réponse.',
  meeting: 'Prépare mon prochain rendez-vous et montre-moi uniquement le contexte vérifiable.',
  invoice: 'Retrouve mes derniers devis et factures, ou aide-moi à préparer un devis brouillon.',
  board: 'Retrouve mes dernières décisions ou aide-moi à cadrer une nouvelle question stratégique.',
  atelier: 'Demande à l’Atelier de simplifier l’onboarding sans toucher aux données existantes.',
};

const rightPanelToolLabels: Record<RightPanelTool, string> = {
  calculator: 'Calculateurs',
  deliverables: 'Suivi client',
  images: 'Images',
  'follow-ups': 'Relances',
  voice: 'Voix',
};

function collapsedRightPanelLabel(panel: CollapsedRightPanel): string {
  if (panel.kind === 'embedded') return panel.view;
  if (panel.kind === 'scenario') return scenarioLabels[panel.scenario];
  return rightPanelToolLabels[panel.tool];
}

function IconButton({
  label,
  children,
  onClick,
  active = false,
  className = '',
}: {
  label: string;
  children: ReactNode;
  onClick?: () => void;
  active?: boolean;
  className?: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className={`grid h-11 w-11 place-items-center rounded-[10px] border transition-colors ${
        active
          ? 'border-text bg-text text-white'
          : 'border-transparent text-text-muted hover:border-border hover:bg-surface hover:text-text'
      } ${className}`}
    >
      {children}
    </button>
  );
}

function SourceChip({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 text-xs font-medium text-text-muted">
      {icon}
      {label}
    </span>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div role="presentation" className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-text-muted">
      {children}
    </div>
  );
}

function ContextCanvas({
  scenario,
  onClose,
  contactsResource,
  emailMessageResource,
  meetingResource,
  meetingEventResource,
  meetingTarget,
  invoiceResource,
  invoiceDetailResource,
  boardResource,
  boardDecisionResource,
  boardRun,
  boardTarget,
  atelierResource,
  atelierTaskResource,
  atelierDiffResource,
  atelierRun,
  atelierTarget,
  atelierActionPending,
  selectedInvoiceId,
  selectedContactId,
  onSelectContact,
  onRetryContacts,
  onRetryEmailMessage,
  onGenerateEmailDraft,
  onSaveEmailDraft,
  onRetryMeeting,
  onRetryMeetingEvent,
  onCreateMeetingEvent,
  onCreateMeetingNote,
  onRetryInvoices,
  onRetryInvoice,
  onCreateDevisDraft,
  onCreateInvoiceContact,
  onRetryBoard,
  onRetryBoardDecision,
  onStartBoard,
  onCancelBoard,
  onResetBoard,
  onRetryAtelier,
  onRetryAtelierTask,
  onStartAtelier,
  onCancelAtelier,
  onResetAtelier,
  onMutateAtelierTask,
  onOpenView,
  onOpenBoardPanel,
  onOpenAtelierPanel,
}: {
  scenario: Exclude<Scenario, 'today'>;
  onClose: () => void;
  contactsResource: ReadResource<Contact[]>;
  emailMessageResource: ReadResource<EmailMessage> | null;
  meetingResource: ReadResource<MeetingWorkspaceData>;
  meetingEventResource: ReturnType<typeof usePrototypeMeetingData>['eventResource'];
  meetingTarget: MeetingTarget;
  invoiceResource: ReadResource<InvoiceWorkspaceData>;
  invoiceDetailResource: ReadResource<Invoice> | null;
  boardResource: ReadResource<BoardWorkspaceData>;
  boardDecisionResource: ReadResource<BoardDecisionDetail> | null;
  boardRun: ReturnType<typeof usePrototypeBoardData>['run'];
  boardTarget: BoardTarget;
  atelierResource: ReadResource<AtelierWorkspaceData>;
  atelierTaskResource: ReadResource<AgentTaskResponse> | null;
  atelierDiffResource: ReadResource<DiffResponse> | null;
  atelierRun: ReturnType<typeof usePrototypeAtelierData>['run'];
  atelierTarget: AtelierTarget;
  atelierActionPending: AtelierReviewAction | null;
  selectedInvoiceId: string | 'new-devis' | null;
  selectedContactId: string | null;
  onSelectContact: (contactId: string) => void;
  onRetryContacts: () => void;
  onRetryEmailMessage: () => void;
  onGenerateEmailDraft: (messageId: string, tone: EmailTone, length: EmailLength) => Promise<string>;
  onSaveEmailDraft: (request: SendEmailRequest) => Promise<{ id: string }>;
  onRetryMeeting: () => void;
  onRetryMeetingEvent: () => void;
  onCreateMeetingEvent: (request: CreateEventRequest) => Promise<CalendarEvent>;
  onCreateMeetingNote: (eventId: string, contactId: string, description: string) => Promise<ActivityResponse>;
  onRetryInvoices: () => void;
  onRetryInvoice: () => void;
  onCreateDevisDraft: (request: CreateInvoiceRequest) => Promise<Invoice>;
  onCreateInvoiceContact: (data: Partial<Contact>) => Promise<Contact>;
  onRetryBoard: () => void;
  onRetryBoardDecision: () => void;
  onStartBoard: (request: BoardRequest) => Promise<void>;
  onCancelBoard: () => void;
  onResetBoard: () => void;
  onRetryAtelier: () => void;
  onRetryAtelierTask: () => void;
  onStartAtelier: (instruction: string) => Promise<void>;
  onCancelAtelier: () => Promise<void>;
  onResetAtelier: () => void;
  onMutateAtelierTask: (
    taskId: string,
    action: AtelierReviewAction,
  ) => Promise<AgentTaskResponse | undefined>;
  onOpenView: (view: Exclude<AppView, 'chat'>) => void;
  onOpenBoardPanel: () => void;
  onOpenAtelierPanel: () => void;
}) {
  const dialogRef = useRef<HTMLElement>(null);
  const isPresent = useIsPresent();
  useDialogFocusTrap(dialogRef, { active: isPresent, onEscape: onClose, isolateBackground: true });

  return (
    <motion.aside
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="prototype-context-canvas-title"
      tabIndex={-1}
      initial={{ x: 32, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 32, opacity: 0 }}
      transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
      className="absolute inset-y-0 right-0 z-20 h-full w-full max-w-[620px] border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] sm:w-[calc(100%-48px)] xl:relative xl:w-[43%] xl:min-w-[440px] xl:shadow-none"
    >
      <h2 id="prototype-context-canvas-title" data-dialog-autofocus tabIndex={-1} className="sr-only">
        {scenarioLabels[scenario]}
      </h2>
      <button
        type="button"
        onClick={onClose}
        aria-label="Fermer le canevas"
        title="Fermer le canevas"
        className="absolute right-4 top-3.5 z-30 grid h-9 w-9 place-items-center rounded-[9px] border border-border bg-surface text-text-muted shadow-sm hover:text-text"
      >
        <PanelRightClose className="h-4 w-4" />
      </button>
      {scenario === 'email' ? (
        <EmailMessageCanvas
          resource={emailMessageResource}
          onRetry={onRetryEmailMessage}
          onGenerateDraft={onGenerateEmailDraft}
          onSaveDraft={onSaveEmailDraft}
          onOpenClassic={() => onOpenView('email')}
        />
      ) : scenario === 'memory' ? (
        <ContactsMemoryCanvas
          resource={contactsResource}
          selectedContactId={selectedContactId}
          onSelectContact={onSelectContact}
          onRetry={onRetryContacts}
          onOpenClassic={() => onOpenView('memory')}
        />
      ) : scenario === 'meeting' ? (
        <MeetingWorkspaceCanvas
          resource={meetingResource}
          eventResource={meetingEventResource}
          target={meetingTarget}
          onRetry={onRetryMeeting}
          onRetryEvent={onRetryMeetingEvent}
          onCreateEvent={onCreateMeetingEvent}
          onCreateNote={onCreateMeetingNote}
          onAbandon={onClose}
          onOpenClassic={() => onOpenView('calendar')}
        />
      ) : scenario === 'invoice' ? (
        <InvoiceWorkspaceCanvas
          resource={invoiceResource}
          invoiceResource={invoiceDetailResource}
          selection={selectedInvoiceId}
          onRetry={onRetryInvoices}
          onRetryInvoice={onRetryInvoice}
          onCreateDraft={onCreateDevisDraft}
          onCreateContact={onCreateInvoiceContact}
          onOpenClassic={() => onOpenView('invoices')}
        />
      ) : scenario === 'board' ? (
        <BoardWorkspaceCanvas
          resource={boardResource}
          decisionResource={boardDecisionResource}
          run={boardRun}
          target={boardTarget}
          onRetry={onRetryBoard}
          onRetryDecision={onRetryBoardDecision}
          onStart={onStartBoard}
          onCancel={onCancelBoard}
          onReset={onResetBoard}
          onOpenClassic={onOpenBoardPanel}
        />
      ) : (
        <AtelierWorkspaceCanvas
          resource={atelierResource}
          taskResource={atelierTaskResource}
          diffResource={atelierDiffResource}
          run={atelierRun}
          target={atelierTarget}
          actionPending={atelierActionPending}
          onRetry={onRetryAtelier}
          onRetryTask={onRetryAtelierTask}
          onStart={onStartAtelier}
          onCancel={onCancelAtelier}
          onReset={onResetAtelier}
          onMutate={onMutateAtelierTask}
          onOpenClassic={onOpenAtelierPanel}
        />
      )}
    </motion.aside>
  );
}

function CommandPalette({
  onClose,
  onSelect,
  onCapability,
  onAction,
}: {
  onClose: () => void;
  onSelect: (scenario: Scenario) => void;
  onCapability: (capability: CapabilityItem) => void;
  onAction: (actionId: string) => void;
}) {
  const [query, setQuery] = useState('');
  const [activeOption, setActiveOption] = useState(0);
  const dialogRef = useRef<HTMLDivElement>(null);
  const isPresent = useIsPresent();
  useDialogFocusTrap(dialogRef, { active: isPresent, onEscape: onClose, isolateBackground: true });
  const visibleCapabilities = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return featuredCapabilities
        .map((id) => capabilities.find((item) => item.id === id))
        .filter((item): item is CapabilityItem => Boolean(item));
    }
    return capabilities
      .filter((item) =>
        [item.title, item.description, ...item.features, ...item.keywords].join(' ').toLowerCase().includes(normalized),
      )
      .slice(0, 8);
  }, [query]);
  const visibleActions = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return [];
    return getActions().filter((action) =>
      [action.label, action.description || '', ...(action.keywords || [])]
        .join(' ')
        .toLowerCase()
        .includes(normalized),
    ).slice(0, 6);
  }, [query]);
  const scenarioCount = query ? 0 : 7;
  const optionCount = scenarioCount + visibleCapabilities.length + visibleActions.length;
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);

  useEffect(() => {
    setActiveOption(0);
  }, [query]);

  const handleSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp' || event.key === 'Home' || event.key === 'End') {
      event.preventDefault();
      setActiveOption((current) => {
        if (optionCount === 0) return 0;
        if (event.key === 'Home') return 0;
        if (event.key === 'End') return optionCount - 1;
        return event.key === 'ArrowDown'
          ? (current + 1) % optionCount
          : (current - 1 + optionCount) % optionCount;
      });
    } else if (event.key === 'Enter' && optionCount > 0) {
      event.preventDefault();
      dialogRef.current?.querySelectorAll<HTMLElement>('[role="option"]')[activeOption]?.click();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 flex items-start justify-center bg-text/35 px-4 pt-[13vh] backdrop-blur-[3px]"
      onClick={onClose}
    >
      <motion.div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Rechercher dans Thérèse"
        tabIndex={-1}
        initial={{ y: -12, scale: 0.98 }}
        animate={{ y: 0, scale: 1 }}
        exit={{ y: -12, scale: 0.98 }}
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-[570px] overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_26px_70px_rgba(16,28,54,0.25)]"
      >
        <div className="flex items-center gap-3 border-b border-border px-4 py-3.5">
          <Search className="h-5 w-5 text-text-muted" />
          <input
            autoFocus
            data-dialog-autofocus
            role="combobox"
            aria-label="Rechercher une commande, un parcours ou une capacité"
            aria-expanded="true"
            aria-autocomplete="list"
            aria-controls="prototype-command-results"
            aria-activedescendant={optionCount > 0 ? `prototype-command-option-${activeOption}` : undefined}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Chercher ou demander à Thérèse…"
            className="flex-1 bg-transparent text-sm text-text outline-none placeholder:text-text-muted"
          />
          <kbd className="rounded-[6px] border border-border bg-surface-2 px-1.5 py-0.5 text-xs text-text-muted">Échap</kbd>
          <button type="button" onClick={onClose} className="rounded-[7px] border border-border px-2 py-1 text-xs font-semibold text-text-muted hover:text-text">Fermer</button>
        </div>
        <div id="prototype-command-results" role="listbox" aria-label="Résultats" className="max-h-[440px] overflow-y-auto p-2">
          <div className="sr-only" role="status" aria-live="polite">{optionCount} résultat{optionCount > 1 ? 's' : ''}</div>
          {!query && (
            <>
              <SectionLabel>Parcours</SectionLabel>
              {(['today', 'memory', 'email', 'meeting', 'invoice', 'board', 'atelier'] as Scenario[]).map((item, optionIndex) => (
                <button
                  key={item}
                  id={`prototype-command-option-${optionIndex}`}
                  role="option"
                  aria-selected={activeOption === optionIndex}
                  tabIndex={-1}
                  type="button"
                  onMouseEnter={() => setActiveOption(optionIndex)}
                  onClick={() => {
                    onSelect(item);
                    onClose();
                  }}
                  className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2.5 text-left hover:bg-bg"
                >
                  <span className="grid h-8 w-8 place-items-center overflow-hidden rounded-[8px] bg-accent-tint text-accent">
                    {item === 'today' ? (
                      <CharacterPortrait index={0} className="h-8 w-8 rounded-[8px]" />
                    ) : item === 'memory' ? (
                      <Users className="h-4 w-4" />
                    ) : item === 'email' ? (
                      <Mail className="h-4 w-4" />
                    ) : item === 'meeting' ? (
                      <Calendar className="h-4 w-4" />
                    ) : item === 'invoice' ? (
                      <Receipt className="h-4 w-4" />
                    ) : item === 'board' ? (
                      <CharacterPortrait index={1} className="h-8 w-8 rounded-[8px]" />
                    ) : (
                      <CharacterPortrait index={6} className="h-8 w-8 rounded-[8px]" />
                    )}
                  </span>
                  <span className="flex-1">
                    <span className="block text-sm font-semibold text-text">{scenarioLabels[item]}</span>
                    <span className="block text-xs text-text-muted">{scenarioPrompts[item]}</span>
                  </span>
                  <ChevronRight className="h-4 w-4 text-text-muted" />
                </button>
              ))}
              <div className="my-2 h-px bg-border" />
            </>
          )}

          <SectionLabel>{query ? `${visibleCapabilities.length} résultat${visibleCapabilities.length > 1 ? 's' : ''}` : 'Capacités fréquentes'}</SectionLabel>
          {visibleCapabilities.map((capability, capabilityIndex) => {
            const Icon = capability.icon;
            const optionIndex = scenarioCount + capabilityIndex;
            return (
              <button
                key={capability.id}
                id={`prototype-command-option-${optionIndex}`}
                role="option"
                aria-selected={activeOption === optionIndex}
                tabIndex={-1}
                type="button"
                onMouseEnter={() => setActiveOption(optionIndex)}
                onClick={() => {
                  onCapability(capability);
                  onClose();
                }}
                className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2.5 text-left hover:bg-bg"
              >
                {capability.id === 'decision-board' ? (
                  <CharacterPortrait index={1} className="h-8 w-8 rounded-[8px]" />
                ) : capability.id === 'agents' ? (
                  <CharacterPortrait index={6} className="h-8 w-8 rounded-[8px]" />
                ) : (
                  <span className="grid h-8 w-8 place-items-center rounded-[8px] bg-[var(--k4bg)] text-[var(--k4)]">
                    <Icon className="h-4 w-4" />
                  </span>
                )}
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-text">{capability.title}</span>
                  <span className="block truncate text-xs text-text-muted">{capability.description}</span>
                </span>
                <ChevronRight className="h-4 w-4 text-text-muted" />
              </button>
            );
          })}
          {visibleCapabilities.length === 0 && visibleActions.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-text-muted">Aucune capacité trouvée.</div>
          )}
          {visibleActions.length > 0 && (
            <>
              <div className="my-2 h-px bg-border" />
              <SectionLabel>Commandes de l’application</SectionLabel>
              {visibleActions.map((action, actionIndex) => {
                const optionIndex = scenarioCount + visibleCapabilities.length + actionIndex;
                return <button key={action.id} id={`prototype-command-option-${optionIndex}`} role="option" aria-selected={activeOption === optionIndex} tabIndex={-1} type="button" onMouseEnter={() => setActiveOption(optionIndex)} onClick={() => { onAction(action.id); onClose(); }} className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2.5 text-left hover:bg-bg">
                  <span className="grid h-8 w-8 place-items-center rounded-[8px] bg-accent-tint text-accent"><Sparkles className="h-4 w-4" /></span>
                  <span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-text">{action.label}</span><span className="block truncate text-xs text-text-muted">{action.description}</span></span>
                  {action.shortcut && <kbd className="rounded-[5px] bg-bg px-1.5 py-0.5 text-xs text-text-muted">{action.shortcut}</kbd>}
                </button>;
              })}
            </>
          )}
        </div>
        <div className="flex items-center justify-between border-t border-border bg-surface-2 px-4 py-2 text-xs text-text-muted">
          <span>{capabilities.length} capacités indexées</span>
          <span>Recherche par résultat, fonction ou outil · {isMac ? '⌘K' : 'Ctrl+K'}</span>
        </div>
      </motion.div>
    </motion.div>
  );
}

export function ConversationCanvasPrototype() {
  const theme = useAccessibilityStore((state) => state.theme);
  const highContrast = useAccessibilityStore((state) => state.highContrast);
  const initialScenario = useMemo<Scenario>(() => {
    const value = new URLSearchParams(window.location.search).get('scenario');
    return value === 'memory' || value === 'email' || value === 'meeting' || value === 'invoice' || value === 'board' || value === 'atelier' ? value : 'today';
  }, []);
  const { resource: todayResource, refresh: refreshToday } = useTodayDashboardResource();
  const { resource: contactsResource, refresh: refreshContacts } = useContactsResource();
  const [scenario, setScenario] = useState<Scenario>(initialScenario);
  const [canvasOpen, setCanvasOpen] = useState(
    initialScenario !== 'today' && initialScenario !== 'email' && initialScenario !== 'invoice' && initialScenario !== 'board',
  );
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [deliverablesOpen, setDeliverablesOpen] = useState(false);
  const [imagesOpen, setImagesOpen] = useState(false);
  const [followUpsOpen, setFollowUpsOpen] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const {
    inboxResource: emailInboxResource,
    messageResource: emailMessageResource,
    refreshInbox: refreshEmailInbox,
    openMessage: openEmailMessage,
    retryMessage: retryEmailMessage,
    generateDraft: generateEmailDraft,
    saveDraft: saveEmailDraft,
  } = usePrototypeEmailData(scenario === 'email');
  const {
    resource: meetingResource,
    eventResource: meetingEventResource,
    refresh: refreshMeeting,
    openEvent: openMeetingEvent,
    retryEvent: retryMeetingEvent,
    createCalendarEvent: createMeetingEvent,
    createMeetingNote,
  } = usePrototypeMeetingData(scenario === 'meeting');
  const {
    resource: invoiceResource,
    invoiceResource: invoiceDetailResource,
    refresh: refreshInvoices,
    openInvoice,
    retryInvoice,
    createDevisDraft,
    createInvoiceContact,
  } = usePrototypeInvoiceData(scenario === 'invoice');
  const {
    resource: boardResource,
    decisionResource: boardDecisionResource,
    run: boardRun,
    refresh: refreshBoard,
    openDecision: openBoardDecision,
    retryDecision: retryBoardDecision,
    startDeliberation: startBoardDeliberation,
    cancelDeliberation: cancelBoardDeliberation,
    resetRun: resetBoardRun,
  } = usePrototypeBoardData(scenario === 'board');
  const {
    resource: atelierResource,
    taskResource: atelierTaskResource,
    diffResource: atelierDiffResource,
    run: atelierRun,
    actionPending: atelierActionPending,
    refresh: refreshAtelier,
    openTask: openAtelierTask,
    retryTask: retryAtelierTask,
    startMission: startAtelierMission,
    cancelMission: cancelAtelierMission,
    mutateTask: mutateAtelierTask,
    resetRun: resetAtelierRun,
  } = usePrototypeAtelierData(scenario === 'atelier');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerSurface, setDrawerSurface] = useState<PrototypeConversationDrawerSurface>('history');
  const [commandOpen, setCommandOpen] = useState(false);
  const [capabilityCenterOpen, setCapabilityCenterOpen] = useState(false);
  const [trustCenterOpen, setTrustCenterOpen] = useState(false);
  const [selectedCapability, setSelectedCapability] = useState<CapabilityItem | null>(null);
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [selectedMeetingTarget, setSelectedMeetingTarget] = useState<MeetingTarget>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | 'new-devis' | null>(null);
  const [selectedBoardTarget, setSelectedBoardTarget] = useState<BoardTarget>(null);
  const [selectedAtelierTarget, setSelectedAtelierTarget] = useState<AtelierTarget>(
    initialScenario === 'atelier' ? 'new-mission' : null,
  );
  const [composerValue, setComposerValue] = useState('');
  const [composerVoiceError, setComposerVoiceError] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInitialPrompt, setChatInitialPrompt] = useState<string | null>(null);
  const [embeddedView, setEmbeddedView] = useState<Exclude<AppView, 'chat'> | null>(null);
  const [lastCollapsedRightPanel, setLastCollapsedRightPanel] = useState<CollapsedRightPanel | null>(null);
  const [userSlashCommands, setUserSlashCommands] = useState<SlashCommand[]>([]);
  const conversationScrollRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const createConversation = useChatStore((state) => state.createConversation);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const openSettings = usePanelStore((state) => state.openSettings);
  const showShortcuts = usePanelStore((state) => state.showShortcuts);
  const openShortcuts = usePanelStore((state) => state.openShortcuts);
  const closeShortcuts = usePanelStore((state) => state.closeShortcuts);
  const toggleBoardPanel = usePanelStore((state) => state.toggleBoardPanel);
  const openAtelierPanel = useAtelierStore((state) => state.openPanel);
  const toggleAtelierPanel = useAtelierStore((state) => state.togglePanel);
  const toggleDemoMode = useDemoStore((state) => state.toggle);
  useConversationSync();

  const blockStreamingNavigation = useCallback(() => {
    if (!isStreaming) return false;
    useStatusStore.getState().addNotification({
      type: 'warning',
      title: 'Réponse en cours',
      message: 'Arrête la réponse avant de changer de vue ou de conversation.',
    });
    return true;
  }, [isStreaming]);

  const closeConversationDrawer = useCallback(() => setDrawerOpen(false), []);
  const closeCommandPalette = useCallback(() => setCommandOpen(false), []);
  const closeCapabilityCenter = useCallback(() => setCapabilityCenterOpen(false), []);
  const closeTrustCenter = useCallback(() => setTrustCenterOpen(false), []);

  const openConversationDrawer = useCallback((surface: PrototypeConversationDrawerSurface) => {
    setDrawerSurface(surface);
    setDrawerOpen(true);
    setCommandOpen(false);
    setCapabilityCenterOpen(false);
    setTrustCenterOpen(false);
  }, []);

  const toggleConversationDrawer = useCallback(() => {
    if (drawerOpen) closeConversationDrawer();
    else openConversationDrawer('history');
  }, [closeConversationDrawer, drawerOpen, openConversationDrawer]);

  useEffect(() => {
    let active = true;
    getProfile()
      .then((value) => { if (active) setProfile(value); })
      .catch(() => { if (active) setProfile(null); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    listUserCommands()
      .then((commands: UserCommand[]) => {
        setUserSlashCommands(commands.map((command) => ({
          id: `user-${command.name}`,
          name: command.name,
          description: command.description || command.name,
          icon: <Sparkles className="h-4 w-4" />,
          prefix: command.content,
        })));
      })
      .catch(() => setUserSlashCommands([]));
  }, []);

  useEffect(() => {
    const onInsertPrompt = (event: Event) => {
      const prompt = (event as CustomEvent<string>).detail;
      if (typeof prompt !== 'string' || !prompt.trim()) return;
      if (blockStreamingNavigation()) return;
      setChatInitialPrompt(prompt.trim());
      setEmbeddedView(null);
      setCanvasOpen(false);
      setCalculatorOpen(false);
      setDeliverablesOpen(false);
      setImagesOpen(false);
      setFollowUpsOpen(false);
      setVoiceOpen(false);
      setChatOpen(true);
    };
    window.addEventListener('therese:insert-prompt', onInsertPrompt as EventListener);
    return () => window.removeEventListener('therese:insert-prompt', onInsertPrompt as EventListener);
  }, [blockStreamingNavigation]);

  const openChat = (prompt?: string) => {
    if (blockStreamingNavigation()) return;
    setChatInitialPrompt(prompt?.trim() || null);
    setEmbeddedView(null);
    setCanvasOpen(false);
    setCalculatorOpen(false);
    setDeliverablesOpen(false);
    setImagesOpen(false);
    setFollowUpsOpen(false);
    setVoiceOpen(false);
    setSelectedCapability(null);
    setComposerValue('');
    setChatOpen(true);
  };
  const startConversation = () => {
    if (blockStreamingNavigation()) return;
    createConversation();
    openChat();
  };
  const openEmbeddedView = (view: Exclude<AppView, 'chat'>) => {
    if (blockStreamingNavigation()) return;
    setChatOpen(false);
    setChatInitialPrompt(null);
    setCanvasOpen(false);
    setCalculatorOpen(false);
    setDeliverablesOpen(false);
    setImagesOpen(false);
    setFollowUpsOpen(false);
    setVoiceOpen(false);
    setSelectedCapability(null);
    setComposerValue('');
    setEmbeddedView(view);
  };
  const collapseEmbeddedView = useCallback(() => {
    if (!embeddedView) return;
    setLastCollapsedRightPanel({ kind: 'embedded', view: embeddedView });
    setEmbeddedView(null);
  }, [embeddedView]);
  const collapseToolPanel = useCallback((tool: RightPanelTool) => {
    setLastCollapsedRightPanel({ kind: 'tool', tool });
    if (tool === 'calculator') setCalculatorOpen(false);
    else if (tool === 'deliverables') setDeliverablesOpen(false);
    else if (tool === 'images') setImagesOpen(false);
    else if (tool === 'follow-ups') setFollowUpsOpen(false);
    else setVoiceOpen(false);
    setCanvasOpen(false);
  }, []);
  const collapseScenarioPanel = useCallback(() => {
    if (scenario === 'today') return;
    setLastCollapsedRightPanel({ kind: 'scenario', scenario });
    setCanvasOpen(false);
  }, [scenario]);
  const reopenLastRightPanel = () => {
    if (!lastCollapsedRightPanel || blockStreamingNavigation()) return;
    const panel = lastCollapsedRightPanel;
    setLastCollapsedRightPanel(null);
    if (panel.kind === 'embedded') {
      openEmbeddedView(panel.view);
      return;
    }

    setChatOpen(false);
    setChatInitialPrompt(null);
    setEmbeddedView(null);
    setCalculatorOpen(panel.kind === 'tool' && panel.tool === 'calculator');
    setDeliverablesOpen(panel.kind === 'tool' && panel.tool === 'deliverables');
    setImagesOpen(panel.kind === 'tool' && panel.tool === 'images');
    setFollowUpsOpen(panel.kind === 'tool' && panel.tool === 'follow-ups');
    setVoiceOpen(panel.kind === 'tool' && panel.tool === 'voice');
    if (panel.kind === 'scenario') setScenario(panel.scenario);
    setCanvasOpen(true);
  };
  const displayName = profile?.nickname?.trim() || profile?.display_name?.trim().split(/\s+/)[0] || null;
  const workspaceName = profile?.company?.trim() || 'Espace de travail';

  useKeyboardShortcuts({
    onCommandPalette: () => {
      setCapabilityCenterOpen(false);
      setTrustCenterOpen(false);
      setCommandOpen(true);
    },
    onNewConversation: startConversation,
    onShowShortcuts: openShortcuts,
    onToggleMemoryPanel: () => embeddedView === 'memory' ? setEmbeddedView(null) : openEmbeddedView('memory'),
    onToggleConversationSidebar: toggleConversationDrawer,
    onToggleBoardPanel: toggleBoardPanel,
    onToggleEmailPanel: () => openEmbeddedView('email'),
    onToggleCalendarPanel: () => openEmbeddedView('calendar'),
    onToggleTasksPanel: () => openEmbeddedView('tasks'),
    onToggleInvoicesPanel: () => openEmbeddedView('invoices'),
    onToggleCRMPanel: () => openEmbeddedView('crm'),
    onNewContact: () => usePanelStore.getState().openNewContact(),
    onNewProject: () => usePanelStore.getState().openNewProject(),
    onOpenSettings: () => openSettings('profile'),
    onSearch: () => openEmbeddedView('memory'),
    onToggleDemoMode: toggleDemoMode,
    onToggleAtelierPanel: toggleAtelierPanel,
    onOpenKatiaNewTask: openAtelierPanel,
  });

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (commandOpen) closeCommandPalette();
        else if (capabilityCenterOpen) closeCapabilityCenter();
        else if (trustCenterOpen) closeTrustCenter();
        else if (drawerOpen) closeConversationDrawer();
        else if (chatOpen) {
          if (blockStreamingNavigation()) return;
          setChatOpen(false);
          setChatInitialPrompt(null);
        } else if (embeddedView) collapseEmbeddedView();
        else if (calculatorOpen) collapseToolPanel('calculator');
        else if (deliverablesOpen) collapseToolPanel('deliverables');
        else if (imagesOpen) collapseToolPanel('images');
        else if (followUpsOpen) collapseToolPanel('follow-ups');
        else if (voiceOpen) collapseToolPanel('voice');
        else if (canvasOpen) collapseScenarioPanel();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [blockStreamingNavigation, calculatorOpen, canvasOpen, capabilityCenterOpen, chatOpen, closeCapabilityCenter, closeCommandPalette, closeConversationDrawer, closeTrustCenter, collapseEmbeddedView, collapseScenarioPanel, collapseToolPanel, commandOpen, deliverablesOpen, drawerOpen, embeddedView, followUpsOpen, imagesOpen, trustCenterOpen, voiceOpen]);

  function chooseScenario(next: Scenario) {
    if (blockStreamingNavigation()) return;
    setScenario(next);
    setChatOpen(false);
    setChatInitialPrompt(null);
    setEmbeddedView(null);
    setCalculatorOpen(false);
    setDeliverablesOpen(false);
    setImagesOpen(false);
    setFollowUpsOpen(false);
    setVoiceOpen(false);
    if (next === 'atelier') {
      setSelectedAtelierTarget(atelierRun.status === 'idle' ? 'new-mission' : 'current');
    }
    if (next === 'meeting') setSelectedMeetingTarget(null);
    setCanvasOpen(next !== 'today' && next !== 'email' && next !== 'invoice' && next !== 'board');
    setComposerValue('');
    setSelectedCapability(null);
    if (typeof conversationScrollRef.current?.scrollTo === 'function') {
      conversationScrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function chooseCapability(capability: CapabilityItem) {
    if (blockStreamingNavigation()) return;
    setCapabilityCenterOpen(false);
    setCommandOpen(false);
    setSelectedCapability(capability);
    setChatOpen(false);
    setChatInitialPrompt(null);
    setEmbeddedView(null);
    setCalculatorOpen(false);
    setDeliverablesOpen(false);
    setImagesOpen(false);
    setFollowUpsOpen(false);
    setVoiceOpen(false);
    if (capability.scenario) {
      chooseScenario(capability.scenario);
      return;
    }
    setCanvasOpen(false);
    setComposerValue(capability.prompt);
  }

  function submitComposer() {
    const destination = selectedCapability?.destination;
    if (destination?.kind === 'pending') return;
    if (destination?.kind === 'calculator') {
      setCalculatorOpen(true);
      setCanvasOpen(true);
      setSelectedCapability(null);
      setComposerValue('');
      return;
    }
    if (destination?.kind === 'deliverables') {
      setDeliverablesOpen(true);
      setCanvasOpen(true);
      setSelectedCapability(null);
      setComposerValue('');
      return;
    }
    if (destination?.kind === 'images') {
      setImagesOpen(true);
      setCanvasOpen(true);
      setSelectedCapability(null);
      setComposerValue('');
      return;
    }
    if (destination?.kind === 'follow-ups') {
      setFollowUpsOpen(true);
      setCanvasOpen(true);
      setSelectedCapability(null);
      setComposerValue('');
      return;
    }
    if (destination?.kind === 'voice') {
      setVoiceOpen(true);
      setCanvasOpen(true);
      setSelectedCapability(null);
      setComposerValue('');
      return;
    }
    if (destination?.kind === 'view') {
      if (destination.view === 'chat') openChat();
      else openEmbeddedView(destination.view);
      return;
    }
    if (destination?.kind === 'action') {
      if (destination.action === 'settings.open') {
        openSettings(destination.settingsTab);
      } else {
        runAction(destination.action);
      }
      return;
    }
    if (destination?.kind === 'prompt') {
      openChat(composerValue || selectedCapability?.prompt || '');
      return;
    }

    // Sans capacité choisie, le champ est une vraie entrée de conversation.
    // Les parcours déterministes restent accessibles par leurs cartes et leurs
    // raccourcis ; une demande libre ne doit jamais être remplacée par un
    // scénario approché ou perdre son texte.
    if (composerValue.trim()) openChat(composerValue);
  }

  const handleComposerTranscript = useCallback((text: string) => {
    setComposerValue((previous) => {
      const trimmed = previous.trim();
      return trimmed ? `${trimmed} ${text}` : text;
    });
    composerRef.current?.focus();
    setComposerVoiceError(null);
  }, []);

  const handleComposerVoiceError = useCallback((error: string) => {
    setComposerVoiceError(error);
  }, []);

  function runUnifiedAction(actionId: string) {
    const viewByAction: Partial<Record<string, Exclude<AppView, 'chat'>>> = {
      'home.open': 'home',
      'memory.open': 'memory',
      'memory.search': 'memory',
      'crm.open': 'crm',
      'email.open': 'email',
      'calendar.open': 'calendar',
      'tasks.open': 'tasks',
      'invoices.open': 'invoices',
      'projects.open': 'projects',
      'files.open': 'files',
      'documents.open': 'documents',
      'documents.new': 'documents',
    };
    const view = viewByAction[actionId];
    if (view) {
      runAction(actionId);
      openEmbeddedView(view);
      return;
    }
    if (actionId === 'chat.new') { startConversation(); return; }
    if (actionId === 'chat.clear') {
      if (blockStreamingNavigation()) return;
      useChatStore.getState().clearCurrentConversation();
      openChat();
      return;
    }
    if (actionId === 'conversations.toggle') { setDrawerOpen((open) => !open); return; }
    if (actionId === 'contact.new') { usePanelStore.getState().openNewContact(); return; }
    if (actionId === 'project.new') { usePanelStore.getState().openNewProject(); return; }
    if (actionId === 'board.open') { toggleBoardPanel(); return; }
    if (actionId === 'data.export') { openSettings('privacy'); return; }
    if (actionId === 'settings.open') { openSettings('profile'); return; }
    if (actionId === 'shortcuts.open') { openShortcuts(); return; }
    runAction(actionId);
  }

  const SelectedCapabilityIcon = selectedCapability?.icon;
  const selectedDestination = selectedCapability?.destination;
  const destinationIsPending = selectedDestination?.kind === 'pending';
  const destinationUsesChat = !selectedDestination || selectedDestination.kind === 'prompt';
  const composerActionLabel = destinationIsPending
    ? 'Parcours en cours de raccordement'
    : selectedDestination?.kind === 'calculator'
      ? 'Ouvrir les calculateurs'
      : selectedDestination?.kind === 'deliverables'
        ? 'Ouvrir le suivi client'
      : selectedDestination?.kind === 'images'
        ? 'Ouvrir le studio Images'
      : selectedDestination?.kind === 'follow-ups'
        ? 'Ouvrir les relances'
      : selectedDestination?.kind === 'voice'
        ? 'Ouvrir l’espace Voix'
      : selectedDestination?.kind === 'view' || selectedDestination?.kind === 'action'
      ? 'Ouvrir le parcours réel'
      : selectedDestination?.kind === 'prompt'
        ? 'Poursuivre dans le chat'
        : 'Poursuivre dans le chat';

  return (
    <div
      className="h-screen w-screen overflow-hidden bg-bg text-text"
      data-testid="conversation-canvas-prototype"
      data-theme={theme}
      data-high-contrast={highContrast ? 'true' : undefined}
    >
      <div className="flex h-full flex-col">
        <header data-dialog-allow onMouseDown={startWindowDrag} className="flex min-h-14 shrink-0 items-center gap-3 border-b border-border bg-surface px-3 select-none sm:px-4">
          <WindowControls />
          <div className="flex min-w-0 flex-1 items-center gap-4">
            <div className="flex min-w-0 items-center gap-2.5">
              <span className="relative h-2.5 w-2.5 rounded-full bg-accent-fill" aria-hidden="true">
                <span className="absolute inset-0 rounded-full bg-accent-fill opacity-40 blur-[4px]" />
              </span>
              <span className="text-sm font-bold tracking-[0.02em] text-text">THÉRÈSE</span>
              <span className="hidden rounded-full border border-border bg-surface-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-text-muted lg:inline-flex">Interface unifiée</span>
            </div>
          </div>

          <div className="hidden items-center gap-2 rounded-[10px] border border-border bg-surface-2 px-3 py-2 text-xs font-semibold text-text md:flex" data-testid="workspace-label" aria-label={`Espace de travail : ${workspaceName}`}>
            <Briefcase className="h-3.5 w-3.5 text-accent" />
            {workspaceName}
          </div>

          <div className="flex flex-1 items-center justify-end gap-1.5">
            <button
              type="button"
              onClick={() => {
                setTrustCenterOpen((open) => !open);
                setCapabilityCenterOpen(false);
                setCommandOpen(false);
              }}
              className="mr-1 hidden items-center gap-1.5 rounded-full border border-accent-cyan/30 bg-accent-tint px-2.5 py-1.5 text-xs font-semibold text-accent hover:border-[#9ED7E1] sm:flex"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-accent" />
              Contrôle des données
            </button>
            <button
              type="button"
              onClick={() => {
                setCommandOpen(true);
                setCapabilityCenterOpen(false);
                setTrustCenterOpen(false);
              }}
              className="hidden items-center gap-2 rounded-[9px] border border-border bg-surface px-2.5 py-1.5 text-xs text-text-muted hover:bg-surface-2 md:flex"
            >
              <Search className="h-3.5 w-3.5" />
              Rechercher
              <kbd className="rounded-[5px] bg-bg px-1.5 py-0.5 text-xs text-text-muted">{/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘K' : 'Ctrl+K'}</kbd>
            </button>
            <IconButton label="Agenda" onClick={() => openEmbeddedView('calendar')}><Calendar className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Paramètres" onClick={() => openSettings('profile')}><Settings className="h-[18px] w-[18px]" /></IconButton>
          </div>
        </header>

        <div className="relative flex min-h-0 flex-1">
          <nav data-dialog-allow aria-label="Navigation principale" className="flex w-16 shrink-0 flex-col items-center border-r border-border bg-surface-2 py-3">
            <IconButton label="Conversations" onClick={toggleConversationDrawer} active={drawerOpen}>
              <Menu className="h-[18px] w-[18px]" />
            </IconButton>
            <div className="my-2 h-px w-7 bg-border" />
            <IconButton label="Nouvelle conversation" onClick={startConversation}><Plus className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Rechercher" onClick={() => openConversationDrawer('search')}><Search className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Historique" onClick={() => openConversationDrawer('history')}><History className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Espaces de travail" onClick={() => openEmbeddedView('projects')}><Folder className="h-[18px] w-[18px]" /></IconButton>
            <div className="mt-auto flex flex-col items-center gap-1.5">
              <IconButton label="Aide" onClick={() => openChat('/aide')}><MessageSquare className="h-[18px] w-[18px]" /></IconButton>
              <button type="button" onClick={() => openSettings('profile')} aria-label="Ouvrir le profil" className="grid h-11 w-11 place-items-center rounded-full border border-text bg-text text-xs font-bold text-white shadow-[2px_2px_0_var(--color-accent-fill)]" title="Ouvrir le profil">{displayName ? displayName.slice(0, 2).toLocaleUpperCase('fr-FR') : <Settings className="h-4 w-4" />}</button>
            </div>
          </nav>

          <AnimatePresence>{drawerOpen && <PrototypeConversationDrawer surface={drawerSurface} navigationLocked={isStreaming} onClose={closeConversationDrawer} onOpenChat={() => openChat()} />}</AnimatePresence>

          <main id="main-content" className="relative flex min-w-0 flex-1 overflow-hidden">
            {chatOpen ? (
              <PrototypeChatSurface
                initialPrompt={chatInitialPrompt}
                userCommands={userSlashCommands}
                onInitialPromptConsumed={() => setChatInitialPrompt(null)}
                onOpenCommandPalette={() => {
                  setCommandOpen(true);
                  setCapabilityCenterOpen(false);
                  setTrustCenterOpen(false);
                }}
                onClose={() => {
                  if (blockStreamingNavigation()) return;
                  setChatOpen(false);
                  setChatInitialPrompt(null);
                }}
              />
            ) : embeddedView ? (
              <PrototypeUnifiedViewCanvas view={embeddedView} onClose={collapseEmbeddedView} />
            ) : (
            <section className="relative flex min-w-0 flex-1 flex-col bg-bg">
              <div ref={conversationScrollRef} className="flex-1 overflow-y-auto px-5 pb-44 pt-7 sm:px-8">
                <div className={`mx-auto transition-[max-width] duration-200 ${canvasOpen ? 'max-w-[760px]' : 'max-w-[860px]'}`}>
                  {(boardRun.status === 'running' || atelierRun.status === 'running') && (
                    <div className="mb-4 flex flex-wrap gap-2" data-testid="shell-background-activities" role="status">
                      {boardRun.status === 'running' && <button type="button" onClick={() => { setScenario('board'); setSelectedBoardTarget('current'); setCanvasOpen(true); }} className="inline-flex items-center gap-2 rounded-[10px] border border-[var(--k4)]/30 bg-[var(--k4bg)] px-3 py-2 text-xs font-semibold text-[var(--k4)]"><Loader2 className="h-3.5 w-3.5 animate-spin" />Board en arrière-plan · {boardRun.phase || 'délibération en cours'}</button>}
                      {atelierRun.status === 'running' && <button type="button" onClick={() => { setScenario('atelier'); setSelectedAtelierTarget('current'); setCanvasOpen(true); }} className="inline-flex items-center gap-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint px-3 py-2 text-xs font-semibold text-accent"><Loader2 className="h-3.5 w-3.5 animate-spin" />Atelier en arrière-plan · {atelierRun.phase || 'mission en cours'}</button>}
                    </div>
                  )}
                  <div className="mb-7 flex items-start gap-3">
                    <CharacterPortrait index={0} className="mt-0.5 h-8 w-8 rounded-[10px] border border-text shadow-[2px_2px_0_var(--btn-shadow-color)]" />
                    <div>
                      <h1 className="text-[24px] font-bold tracking-[-0.035em] text-text">Bonjour{displayName ? ` ${displayName}` : ''}.</h1>
                      <p className="mt-1 text-sm leading-6 text-text-muted">
                        {scenario === 'today'
                          ? "J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module."
                          : scenario === 'memory'
                            ? 'Je consulte les contacts réellement enregistrés et leur contexte local, sans rien modifier.'
                          : scenario === 'email'
                            ? 'Je consulte la boîte connectée. Tu peux lire un message et préparer un brouillon sans l’envoyer.'
                          : scenario === 'meeting'
                            ? 'Je consulte les événements, les participants et le contexte CRM réellement relié, sans rien inventer.'
                            : scenario === 'invoice'
                              ? 'Je consulte les documents réellement enregistrés. Tu peux aussi préparer un devis brouillon avant toute génération ou envoi.'
                              : scenario === 'board'
                                ? 'Je consulte les décisions enregistrées. Tu peux relire un historique ou préparer une nouvelle question avant de lancer quoi que ce soit.'
                                : 'Je consulte les missions réellement enregistrées. Tu peux cadrer un changement, suivre son exécution isolée et relire le diff avant toute application.'}
                      </p>
                    </div>
                  </div>

                  <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-text-muted">
                    <CharacterPortrait index={0} className="h-5 w-5 rounded-[6px] border border-text" />
                    THÉRÈSE
                    <span className="font-normal">· maintenant</span>
                  </div>

                  {scenario === 'today' ? (
                    <TodayDashboardCard
                      resource={todayResource}
                      onRetry={() => void refreshToday()}
                      onOpenView={(view) => {
                        if (view === 'chat') openChat();
                        else openEmbeddedView(view);
                      }}
                    />
                  ) : scenario === 'memory' ? (
                    <ContactsMemoryCard
                      resource={contactsResource}
                      onRetry={() => void refreshContacts()}
                      onOpenContact={(contactId) => {
                        setSelectedContactId(contactId);
                        setCanvasOpen(true);
                      }}
                      onOpenClassic={() => openEmbeddedView('memory')}
                    />
                  ) : scenario === 'email' ? (
                    <EmailInboxCard
                      resource={emailInboxResource}
                      onRetry={() => void refreshEmailInbox()}
                      onOpenMessage={(messageId) => {
                        setCanvasOpen(true);
                        void openEmailMessage(messageId);
                      }}
                      onOpenClassic={() => openEmbeddedView('email')}
                    />
                  ) : scenario === 'meeting' ? (
                    <MeetingAgendaCard
                      resource={meetingResource}
                      onRetry={() => void refreshMeeting()}
                      onOpenEvent={(eventId) => {
                        setSelectedMeetingTarget(eventId);
                        setCanvasOpen(true);
                        void openMeetingEvent(eventId);
                      }}
                      onNewEvent={() => {
                        setSelectedMeetingTarget('new-event');
                        setCanvasOpen(true);
                      }}
                      onOpenClassic={() => openEmbeddedView('calendar')}
                    />
                  ) : scenario === 'invoice' ? (
                    <InvoiceWorkspaceCard
                      resource={invoiceResource}
                      onRetry={() => void refreshInvoices()}
                      onOpenInvoice={(invoiceId) => {
                        setSelectedInvoiceId(invoiceId);
                        setCanvasOpen(true);
                        void openInvoice(invoiceId);
                      }}
                      onCreateDevis={() => {
                        setSelectedInvoiceId('new-devis');
                        setCanvasOpen(true);
                      }}
                      onOpenClassic={() => openEmbeddedView('invoices')}
                    />
                  ) : scenario === 'board' ? (
                    <BoardHistoryCard
                      resource={boardResource}
                      run={boardRun}
                      onRetry={() => void refreshBoard()}
                      onOpenDecision={(decisionId) => {
                        setSelectedBoardTarget(decisionId);
                        setCanvasOpen(true);
                        void openBoardDecision(decisionId);
                      }}
                      onNewBoard={() => {
                        resetBoardRun();
                        setSelectedBoardTarget('new-board');
                        setCanvasOpen(true);
                      }}
                      onOpenCurrent={() => {
                        setSelectedBoardTarget('current');
                        setCanvasOpen(true);
                      }}
                      onOpenClassic={toggleBoardPanel}
                    />
                  ) : (
                    <AtelierHistoryCard
                      resource={atelierResource}
                      run={atelierRun}
                      onRetry={() => void refreshAtelier()}
                      onOpenTask={(taskId) => {
                        setSelectedAtelierTarget(taskId);
                        setCanvasOpen(true);
                        void openAtelierTask(taskId);
                      }}
                      onNewMission={() => {
                        resetAtelierRun();
                        setSelectedAtelierTarget('new-mission');
                        setCanvasOpen(true);
                      }}
                      onOpenCurrent={() => {
                        setSelectedAtelierTarget('current');
                        setCanvasOpen(true);
                      }}
                      onOpenClassic={openAtelierPanel}
                    />
                  )}

                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <span className="mr-1 text-xs font-medium text-text-muted">Sources</span>
                    {scenario === 'today' ? (
                      <>
                        <SourceChip icon={<HardDrive className="h-3 w-3" />} label="Dashboard local" />
                        <SourceChip icon={<ShieldCheck className="h-3 w-3" />} label="Lecture seule" />
                      </>
                    ) : scenario === 'memory' ? (
                      <>
                        <SourceChip icon={<HardDrive className="h-3 w-3" />} label="Mémoire locale" />
                        <SourceChip icon={<Users className="h-3 w-3" />} label="Contacts réels" />
                        <SourceChip icon={<ShieldCheck className="h-3 w-3" />} label="Lecture seule" />
                      </>
                    ) : scenario === 'email' ? (
                      <>
                        <SourceChip
                          icon={<Mail className="h-3 w-3" />}
                          label={emailInboxResource.status === 'ready' && emailInboxResource.data.currentAccount
                            ? `${emailInboxResource.data.currentAccount.provider === 'gmail' ? 'Gmail' : 'IMAP'} connecté`
                            : 'Email'}
                        />
                        <SourceChip icon={<ShieldCheck className="h-3 w-3" />} label="Brouillon confirmé, aucun envoi" />
                      </>
                    ) : scenario === 'meeting' ? (
                      <>
                        <SourceChip
                          icon={<Calendar className="h-3 w-3" />}
                          label={meetingResource.status === 'ready'
                            ? `${meetingResource.data.calendars.length} calendrier${meetingResource.data.calendars.length > 1 ? 's' : ''}`
                            : 'Agenda'}
                        />
                        <SourceChip
                          icon={<Users className="h-3 w-3" />}
                          label={meetingResource.status === 'ready'
                            ? `${meetingResource.data.contacts.length} contacts consultables`
                            : 'CRM local'}
                        />
                        <SourceChip icon={<ShieldCheck className="h-3 w-3" />} label="Écriture confirmée" />
                      </>
                    ) : scenario === 'invoice' ? (
                      <>
                        <SourceChip icon={<HardDrive className="h-3 w-3" />} label="Facturation locale" />
                        <SourceChip icon={<Users className="h-3 w-3" />} label="Référentiel contacts" />
                        <SourceChip icon={<ShieldCheck className="h-3 w-3" />} label="Brouillon confirmé, aucun envoi" />
                      </>
                    ) : scenario === 'board' ? (
                      <>
                        <SourceChip icon={<HardDrive className="h-3 w-3" />} label="Historique local" />
                        <SourceChip icon={<Users className="h-3 w-3" />} label="5 conseillers" />
                        <SourceChip icon={<ShieldCheck className="h-3 w-3" />} label="Cloud ou Ollama confirmé" />
                      </>
                    ) : (
                      <>
                        <SourceChip icon={<Folder className="h-3 w-3" />} label="Dépôt Git autorisé" />
                        <SourceChip icon={<Bot className="h-3 w-3" />} label="Katia + Zézette réelles" />
                        <SourceChip icon={<ShieldCheck className="h-3 w-3" />} label="Worktree isolé · validation séparée" />
                      </>
                    )}
                  </div>

                  <div className="mt-9 border-t border-border pt-5">
                    <div className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">Essayer un autre parcours</div>
                    <div className="flex flex-wrap gap-2">
                      {(['today', 'memory', 'email', 'meeting', 'invoice', 'board', 'atelier'] as Scenario[]).map((item) => (
                        <button
                          key={item}
                          type="button"
                          onClick={() => chooseScenario(item)}
                          aria-pressed={scenario === item}
                          className={`rounded-full border px-3 py-2 text-xs font-semibold ${
                            scenario === item
                              ? 'border-text bg-text text-white'
                              : 'border-border bg-surface text-text-muted hover:border-border hover:text-text'
                          }`}
                        >
                          {scenarioLabels[item]}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div
                className="pointer-events-none absolute inset-x-0 bottom-0 bg-[linear-gradient(to_top,var(--color-bg)_70%,transparent)] px-5 pb-5 pt-12 sm:px-8"
                data-testid="prototype-composer-backdrop"
              >
                <div className={`pointer-events-auto mx-auto transition-[max-width] duration-200 ${canvasOpen ? 'max-w-[760px]' : 'max-w-[860px]'}`}>
                  <div className="rounded-[18px] border border-border bg-surface p-2 shadow-[0_18px_45px_-24px_rgba(16,28,54,0.45)] focus-within:border-[#22D3EE] focus-within:shadow-[0_0_0_3px_rgba(34,211,238,0.12),0_18px_45px_-24px_rgba(16,28,54,0.45)]">
                    {selectedCapability && SelectedCapabilityIcon && (
                      <div className="mx-1 mt-1 flex items-center gap-2 rounded-[10px] border border-[var(--k4)]/30 bg-[var(--k4bg)] px-2.5 py-2 text-xs text-[var(--k4)]">
                        <span className="grid h-6 w-6 place-items-center rounded-[7px] bg-[var(--k4bg)] text-[var(--k4)]">
                          <SelectedCapabilityIcon className="h-3.5 w-3.5" />
                        </span>
                        <span className="min-w-0 flex-1 truncate"><span className="font-semibold">Capacité :</span> {selectedCapability.title}</span>
                        <button type="button" onClick={() => setSelectedCapability(null)} aria-label="Retirer la capacité" className="grid h-6 w-6 place-items-center rounded-[7px] hover:bg-surface">
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}
                    {destinationUsesChat ? (
                      <textarea
                        ref={composerRef}
                        aria-label="Message à Thérèse"
                        value={composerValue}
                        onChange={(event) => setComposerValue(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' && !event.shiftKey) {
                            event.preventDefault();
                            submitComposer();
                          }
                        }}
                        rows={2}
                        placeholder="Demande à Thérèse d’organiser, créer ou agir…"
                        className="max-h-28 min-h-12 w-full resize-none bg-transparent px-2.5 py-2 text-sm leading-6 text-text outline-none placeholder:text-text-muted"
                      />
                    ) : (
                      <div
                        className={`mx-1 my-2 rounded-[10px] border px-3 py-2.5 text-xs leading-5 ${
                          destinationIsPending
                            ? 'border-warning/40 bg-[var(--color-warning-tint)] text-warning'
                            : 'border-accent-cyan/30 bg-accent-tint text-accent'
                        }`}
                        data-testid="capability-destination-message"
                      >
                        {selectedDestination?.kind === 'pending'
                          ? selectedDestination.reason
                          : 'Cette capacité ouvre sa surface fonctionnelle réelle. Aucun message ne sera envoyé et aucune donnée ne sera modifiée par ce passage.'}
                      </div>
                    )}
                    {composerVoiceError && (
                      <div role="alert" className="mx-1 mb-2 flex items-start gap-2 rounded-[8px] border border-error/20 bg-error/10 px-3 py-2 text-xs text-error">
                        <span className="flex-1">{composerVoiceError}</span>
                        <button type="button" onClick={() => setComposerVoiceError(null)} aria-label="Fermer l’erreur de dictée"><X className="h-3.5 w-3.5" /></button>
                      </div>
                    )}
                    <div className="flex items-center justify-between gap-3 px-1 pb-1">
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => {
                            setCapabilityCenterOpen(true);
                            setCommandOpen(false);
                            setTrustCenterOpen(false);
                          }}
                          className="flex h-9 items-center gap-1.5 rounded-[10px] px-2.5 text-xs font-medium text-text-muted hover:bg-bg hover:text-text"
                        >
                          <Plus className="h-4 w-4" />
                          Capacités
                        </button>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="hidden text-xs font-medium text-text-muted sm:inline">Parcours réel · confirmation avant effet</span>
                        {destinationUsesChat && (
                          <VoiceDictationButton
                            onTranscript={handleComposerTranscript}
                            onError={handleComposerVoiceError}
                            testId="prototype-chat-voice-btn"
                            className="rounded-[10px] border border-transparent text-text-muted hover:border-border hover:bg-bg hover:text-text"
                          />
                        )}
                        <button
                          type="button"
                          onClick={submitComposer}
                          disabled={destinationIsPending || (destinationUsesChat && !composerValue.trim())}
                          aria-label={composerActionLabel}
                          title={composerActionLabel}
                          className="grid h-11 w-11 place-items-center rounded-[10px] border border-text bg-accent-fill text-accent-ink shadow-[2px_2px_0_var(--btn-shadow-color)] hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:border-border disabled:bg-surface-2 disabled:text-text-muted disabled:shadow-none disabled:hover:translate-y-0"
                        >
                          {destinationUsesChat ? <ArrowUp className="h-[18px] w-[18px]" /> : <ChevronRight className="h-[18px] w-[18px]" />}
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 text-center text-xs text-text-muted">Thérèse affiche les sources reçues et confirme les effets externes effectivement raccordés.</div>
                </div>
              </div>
            </section>
            )}

            <AnimatePresence>
              {calculatorOpen ? (
                <CalculatorWorkspaceCanvas
                  onClose={() => {
                    collapseToolPanel('calculator');
                  }}
                />
              ) : deliverablesOpen ? (
                <DeliverablesWorkspaceCanvas
                  onClose={() => {
                    collapseToolPanel('deliverables');
                  }}
                  onOpenProjects={() => openEmbeddedView('projects')}
                  onOpenInvoices={() => openEmbeddedView('invoices')}
                />
              ) : imagesOpen ? (
                <ImagesWorkspaceCanvas
                  onClose={() => {
                    collapseToolPanel('images');
                  }}
                />
              ) : followUpsOpen ? (
                <FollowUpsWorkspaceCanvas
                  onClose={() => {
                    collapseToolPanel('follow-ups');
                  }}
                  onOpenEmail={() => openEmbeddedView('email')}
                />
              ) : voiceOpen ? (
                <VoiceWorkspaceCanvas
                  onClose={() => {
                    collapseToolPanel('voice');
                  }}
                  onContinueInChat={(prompt) => {
                    setVoiceOpen(false);
                    setCanvasOpen(false);
                    openChat(prompt);
                  }}
                />
              ) : canvasOpen && scenario !== 'today' && (
                <ContextCanvas
                  scenario={scenario}
                  onClose={() => {
                    collapseScenarioPanel();
                  }}
                  contactsResource={contactsResource}
                  emailMessageResource={emailMessageResource}
                  meetingResource={meetingResource}
                  meetingEventResource={meetingEventResource}
                  meetingTarget={selectedMeetingTarget}
                  invoiceResource={invoiceResource}
                  invoiceDetailResource={invoiceDetailResource}
                  boardResource={boardResource}
                  boardDecisionResource={boardDecisionResource}
                  boardRun={boardRun}
                  boardTarget={selectedBoardTarget}
                  atelierResource={atelierResource}
                  atelierTaskResource={atelierTaskResource}
                  atelierDiffResource={atelierDiffResource}
                  atelierRun={atelierRun}
                  atelierTarget={selectedAtelierTarget}
                  atelierActionPending={atelierActionPending}
                  selectedInvoiceId={selectedInvoiceId}
                  selectedContactId={selectedContactId}
                  onSelectContact={setSelectedContactId}
                  onRetryContacts={() => void refreshContacts()}
                  onRetryEmailMessage={() => void retryEmailMessage()}
                  onGenerateEmailDraft={generateEmailDraft}
                  onSaveEmailDraft={saveEmailDraft}
                  onRetryMeeting={() => void refreshMeeting()}
                  onRetryMeetingEvent={() => void retryMeetingEvent()}
                  onCreateMeetingEvent={async (request) => {
                    const created = await createMeetingEvent(request);
                    setSelectedMeetingTarget(meetingEventKey(created));
                    return created;
                  }}
                  onCreateMeetingNote={createMeetingNote}
                  onRetryInvoices={() => void refreshInvoices()}
                  onRetryInvoice={() => void retryInvoice()}
                  onCreateDevisDraft={createDevisDraft}
                  onCreateInvoiceContact={createInvoiceContact}
                  onRetryBoard={() => void refreshBoard()}
                  onRetryBoardDecision={() => void retryBoardDecision()}
                  onStartBoard={startBoardDeliberation}
                  onCancelBoard={cancelBoardDeliberation}
                  onResetBoard={() => {
                    resetBoardRun();
                    setSelectedBoardTarget('new-board');
                  }}
                  onRetryAtelier={() => void refreshAtelier()}
                  onRetryAtelierTask={() => void retryAtelierTask()}
                  onStartAtelier={startAtelierMission}
                  onCancelAtelier={cancelAtelierMission}
                  onResetAtelier={() => {
                    resetAtelierRun();
                    setSelectedAtelierTarget('new-mission');
                  }}
                  onMutateAtelierTask={mutateAtelierTask}
                  onOpenView={openEmbeddedView}
                  onOpenBoardPanel={toggleBoardPanel}
                  onOpenAtelierPanel={openAtelierPanel}
                />
              )}
            </AnimatePresence>
            {lastCollapsedRightPanel && !embeddedView && !canvasOpen && (
              <button
                type="button"
                onClick={reopenLastRightPanel}
                aria-label={`Rouvrir le panneau ${collapsedRightPanelLabel(lastCollapsedRightPanel)}`}
                title={`Rouvrir le panneau ${collapsedRightPanelLabel(lastCollapsedRightPanel)}`}
                data-testid="reopen-right-panel-tab"
                className="absolute right-0 top-1/2 z-30 grid h-12 w-7 -translate-y-1/2 place-items-center rounded-l-[10px] border border-r-0 border-border bg-surface text-text-muted shadow-[-4px_4px_14px_rgba(16,28,54,0.15)] hover:bg-surface-2 hover:text-text"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
            )}
          </main>
        </div>
      </div>

      <PanelContainer onUserCommandsRefresh={setUserSlashCommands} />
      <ShortcutsModal isOpen={showShortcuts} onClose={closeShortcuts} />

      <AnimatePresence>
        {commandOpen && (
          <CommandPalette
            onClose={closeCommandPalette}
            onSelect={chooseScenario}
            onCapability={chooseCapability}
            onAction={runUnifiedAction}
          />
        )}
        {capabilityCenterOpen && (
          <CapabilityCenter onClose={closeCapabilityCenter} onChoose={chooseCapability} />
        )}
        {trustCenterOpen && (
          <TrustCenter
            onClose={closeTrustCenter}
            onOpenPrivacy={() => openSettings('privacy')}
            onOpenAdvanced={() => openSettings('advanced')}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
