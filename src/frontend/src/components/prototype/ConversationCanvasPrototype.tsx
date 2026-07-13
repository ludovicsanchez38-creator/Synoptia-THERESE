import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowUp,
  Bell,
  Bot,
  Briefcase,
  Calendar,
  ChevronDown,
  ChevronRight,
  FileText,
  Folder,
  Globe,
  HardDrive,
  History,
  Mail,
  Menu,
  MessageSquare,
  Mic,
  Paperclip,
  PanelRightClose,
  Plus,
  Receipt,
  Search,
  Settings,
  ShieldCheck,
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
import { usePrototypeEmailData, type EmailLength, type EmailTone } from './usePrototypeEmailData';
import { usePrototypeInvoiceData, type InvoiceWorkspaceData } from './usePrototypeInvoiceData';
import { usePrototypeMeetingData, type MeetingWorkspaceData } from './usePrototypeMeetingData';
import { usePrototypeBoardData, type BoardWorkspaceData } from './usePrototypeBoardData';
import { usePrototypeAtelierData, type AtelierWorkspaceData } from './usePrototypeAtelierData';
import { useContactsResource, useTodayDashboardResource, type ReadResource } from './usePrototypeReadData';
import { openClassicPanel, openClassicView } from '../../lib/classicNavigation';
import type { CreateInvoiceRequest, Invoice } from '../../services/api/invoices';
import type { EmailMessage, SendEmailRequest } from '../../services/api/email';
import type { Contact } from '../../services/api/memory';
import type { BoardDecisionDetail, BoardRequest } from '../../services/api/board';
import type { AgentTaskResponse, DiffResponse } from '../../services/api/agents';
import type { CalendarEvent, CreateEventRequest } from '../../services/api/calendar';
import type { ActivityResponse } from '../../services/api/crm-extended';

type Scenario = 'today' | 'memory' | 'email' | 'meeting' | 'invoice' | 'board' | 'atelier';

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
  meeting: 'Prépare mon rendez-vous avec Claire Fontaine.',
  invoice: 'Retrouve mes derniers devis et factures, ou aide-moi à préparer un devis brouillon.',
  board: 'Retrouve mes dernières décisions ou aide-moi à cadrer une nouvelle question stratégique.',
  atelier: 'Demande à l’Atelier de simplifier l’onboarding sans toucher aux données existantes.',
};

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
      className={`grid h-9 w-9 place-items-center rounded-[10px] border transition-colors ${
        active
          ? 'border-[#101C36] bg-[#101C36] text-white'
          : 'border-transparent text-[#5B6A82] hover:border-[#DCE4F1] hover:bg-white hover:text-[#101C36]'
      } ${className}`}
    >
      {children}
    </button>
  );
}

function SourceChip({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[#DCE4F1] bg-white px-2.5 py-1 text-[11px] font-medium text-[#5B6A82]">
      {icon}
      {label}
    </span>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7B8AA3]">
      {children}
    </div>
  );
}

function ConversationDrawer({ onClose }: { onClose: () => void }) {
  return (
    <motion.aside
      initial={{ x: -24, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -24, opacity: 0 }}
      transition={{ duration: 0.18 }}
      className="absolute inset-y-0 left-16 z-30 w-[286px] border-r border-[#DCE4F1] bg-white shadow-[12px_0_40px_rgba(16,28,54,0.10)]"
    >
      <div className="flex h-14 items-center justify-between border-b border-[#E7ECF4] px-4">
        <span className="text-sm font-semibold text-[#101C36]">Conversations</span>
        <IconButton label="Fermer les conversations" onClick={onClose}>
          <X className="h-4 w-4" />
        </IconButton>
      </div>

      <div className="p-3">
        <button
          type="button"
          className="mb-3 flex w-full items-center justify-center gap-2 rounded-[10px] border border-[#101C36] bg-[#101C36] px-3 py-2.5 text-sm font-semibold text-white shadow-[2px_2px_0_#22D3EE]"
        >
          <Plus className="h-4 w-4" />
          Nouvelle conversation
        </button>
        <div className="relative mb-5">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#7B8AA3]" />
          <input
            aria-label="Rechercher une conversation"
            placeholder="Rechercher…"
            className="w-full rounded-[10px] border border-[#DCE4F1] bg-[#F7F9FD] py-2 pl-9 pr-3 text-sm text-[#101C36] outline-none focus:border-[#22D3EE]"
          />
        </div>

        <SectionLabel>Aujourd’hui</SectionLabel>
        <button type="button" className="mb-1 w-full rounded-[9px] bg-[#E8F8FB] px-3 py-2.5 text-left">
          <div className="truncate text-sm font-semibold text-[#101C36]">Priorités et rendez-vous</div>
          <div className="mt-0.5 text-[11px] text-[#5B6A82]">Il y a 8 min</div>
        </button>
        <button type="button" className="mb-1 w-full rounded-[9px] px-3 py-2.5 text-left hover:bg-[#F3F6FC]">
          <div className="truncate text-sm font-medium text-[#101C36]">Refonte de l’offre PROPULSER</div>
          <div className="mt-0.5 text-[11px] text-[#5B6A82]">Il y a 2 h</div>
        </button>

        <SectionLabel>Hier</SectionLabel>
        <button type="button" className="mb-5 w-full rounded-[9px] px-3 py-2.5 text-left hover:bg-[#F3F6FC]">
          <div className="truncate text-sm font-medium text-[#101C36]">Programme parrainage</div>
          <div className="mt-0.5 text-[11px] text-[#5B6A82]">Hier, 18:42</div>
        </button>

        <SectionLabel>Espaces de travail</SectionLabel>
        {[
          ['Synoptïa', '12 conversations', '#22D3EE'],
          ['THÉRÈSE', '8 conversations', '#E11D8D'],
          ['Formations', '5 conversations', '#A855F7'],
        ].map(([name, count, color]) => (
          <button key={name} type="button" className="flex w-full items-center gap-3 rounded-[9px] px-3 py-2.5 text-left hover:bg-[#F3F6FC]">
            <span className="h-2.5 w-2.5 rounded-[3px]" style={{ backgroundColor: color }} />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-[#101C36]">{name}</span>
              <span className="block text-[11px] text-[#7B8AA3]">{count}</span>
            </span>
            <ChevronRight className="h-4 w-4 text-[#9AA7BB]" />
          </button>
        ))}
      </div>
    </motion.aside>
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
}) {
  return (
    <motion.aside
      initial={{ x: 32, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 32, opacity: 0 }}
      transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
      className="absolute inset-y-0 right-0 z-20 h-full w-full max-w-[620px] border-l border-[#DCE4F1] bg-[#F7F9FD] shadow-[-18px_0_45px_rgba(16,28,54,0.12)] sm:w-[calc(100%-48px)] xl:relative xl:w-[43%] xl:min-w-[440px] xl:shadow-none"
    >
      <button
        type="button"
        onClick={onClose}
        aria-label="Fermer le canevas"
        title="Fermer le canevas"
        className="absolute right-4 top-3.5 z-30 grid h-9 w-9 place-items-center rounded-[9px] border border-[#DCE4F1] bg-white text-[#5B6A82] shadow-sm hover:text-[#101C36]"
      >
        <PanelRightClose className="h-4 w-4" />
      </button>
      {scenario === 'email' ? (
        <EmailMessageCanvas
          resource={emailMessageResource}
          onRetry={onRetryEmailMessage}
          onGenerateDraft={onGenerateEmailDraft}
          onSaveDraft={onSaveEmailDraft}
          onOpenClassic={() => openClassicView('email')}
        />
      ) : scenario === 'memory' ? (
        <ContactsMemoryCanvas
          resource={contactsResource}
          selectedContactId={selectedContactId}
          onSelectContact={onSelectContact}
          onRetry={onRetryContacts}
          onOpenClassic={() => openClassicView('memory')}
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
          onOpenClassic={() => openClassicView('calendar')}
        />
      ) : scenario === 'invoice' ? (
        <InvoiceWorkspaceCanvas
          resource={invoiceResource}
          invoiceResource={invoiceDetailResource}
          selection={selectedInvoiceId}
          onRetry={onRetryInvoices}
          onRetryInvoice={onRetryInvoice}
          onCreateDraft={onCreateDevisDraft}
          onOpenClassic={() => openClassicView('invoices')}
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
          onOpenClassic={() => openClassicPanel('board')}
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
          onOpenClassic={() => openClassicPanel('atelier')}
        />
      )}
    </motion.aside>
  );
}

function CommandPalette({
  onClose,
  onSelect,
  onCapability,
}: {
  onClose: () => void;
  onSelect: (scenario: Scenario) => void;
  onCapability: (capability: CapabilityItem) => void;
}) {
  const [query, setQuery] = useState('');
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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 flex items-start justify-center bg-[#101C36]/35 px-4 pt-[13vh] backdrop-blur-[3px]"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: -12, scale: 0.98 }}
        animate={{ y: 0, scale: 1 }}
        exit={{ y: -12, scale: 0.98 }}
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-[570px] overflow-hidden rounded-[16px] border border-[#DCE4F1] bg-white shadow-[0_26px_70px_rgba(16,28,54,0.25)]"
      >
        <div className="flex items-center gap-3 border-b border-[#E7ECF4] px-4 py-3.5">
          <Search className="h-5 w-5 text-[#7B8AA3]" />
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Chercher ou demander à Thérèse…"
            className="flex-1 bg-transparent text-sm text-[#101C36] outline-none placeholder:text-[#9AA7BB]"
          />
          <kbd className="rounded-[6px] border border-[#DCE4F1] bg-[#F7F9FD] px-1.5 py-0.5 text-[10px] text-[#7B8AA3]">esc</kbd>
        </div>
        <div className="max-h-[440px] overflow-y-auto p-2">
          {!query && (
            <>
              <SectionLabel>Parcours</SectionLabel>
              {(['today', 'memory', 'email', 'meeting', 'invoice', 'board', 'atelier'] as Scenario[]).map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => {
                    onSelect(item);
                    onClose();
                  }}
                  className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2.5 text-left hover:bg-[#F3F6FC]"
                >
                  <span className="grid h-8 w-8 place-items-center overflow-hidden rounded-[8px] bg-[#DEF4F9] text-[#0F8FB3]">
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
                    <span className="block text-sm font-semibold text-[#101C36]">{scenarioLabels[item]}</span>
                    <span className="block text-xs text-[#7B8AA3]">{scenarioPrompts[item]}</span>
                  </span>
                  <ChevronRight className="h-4 w-4 text-[#9AA7BB]" />
                </button>
              ))}
              <div className="my-2 h-px bg-[#E7ECF4]" />
            </>
          )}

          <SectionLabel>{query ? `${visibleCapabilities.length} résultat${visibleCapabilities.length > 1 ? 's' : ''}` : 'Capacités fréquentes'}</SectionLabel>
          {visibleCapabilities.map((capability) => {
            const Icon = capability.icon;
            return (
              <button
                key={capability.id}
                type="button"
                onClick={() => {
                  onCapability(capability);
                  onClose();
                }}
                className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2.5 text-left hover:bg-[#F3F6FC]"
              >
                {capability.id === 'decision-board' ? (
                  <CharacterPortrait index={1} className="h-8 w-8 rounded-[8px]" />
                ) : capability.id === 'agents' ? (
                  <CharacterPortrait index={6} className="h-8 w-8 rounded-[8px]" />
                ) : (
                  <span className="grid h-8 w-8 place-items-center rounded-[8px] bg-[#F0E9FC] text-[#7C3AED]">
                    <Icon className="h-4 w-4" />
                  </span>
                )}
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-[#101C36]">{capability.title}</span>
                  <span className="block truncate text-xs text-[#7B8AA3]">{capability.description}</span>
                </span>
                <ChevronRight className="h-4 w-4 text-[#9AA7BB]" />
              </button>
            );
          })}
          {visibleCapabilities.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-[#7B8AA3]">Aucune capacité trouvée.</div>
          )}
        </div>
        <div className="flex items-center justify-between border-t border-[#E7ECF4] bg-[#F8FAFD] px-4 py-2 text-[10px] text-[#8190A5]">
          <span>{capabilities.length} capacités indexées</span>
          <span>Recherche par résultat, fonction ou outil</span>
        </div>
      </motion.div>
    </motion.div>
  );
}

export function ConversationCanvasPrototype() {
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
  const conversationScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setCapabilityCenterOpen(false);
        setTrustCenterOpen(false);
        setCommandOpen(true);
      }
      if (event.key === 'Escape') {
        if (commandOpen) setCommandOpen(false);
        else if (capabilityCenterOpen) setCapabilityCenterOpen(false);
        else if (trustCenterOpen) setTrustCenterOpen(false);
        else if (drawerOpen) setDrawerOpen(false);
        else if (canvasOpen) {
          if (scenario === 'board') cancelBoardDeliberation();
          if (scenario === 'atelier') void cancelAtelierMission();
          setCanvasOpen(false);
        }
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [canvasOpen, cancelAtelierMission, cancelBoardDeliberation, capabilityCenterOpen, commandOpen, drawerOpen, scenario, trustCenterOpen]);

  function chooseScenario(next: Scenario) {
    if (scenario === 'board') cancelBoardDeliberation();
    if (scenario === 'atelier') void cancelAtelierMission();
    setScenario(next);
    if (next === 'atelier') {
      setSelectedAtelierTarget(atelierRun.status === 'idle' ? 'new-mission' : 'current');
    }
    if (next === 'meeting') setSelectedMeetingTarget(null);
    setCanvasOpen(next !== 'today' && next !== 'email' && next !== 'invoice' && next !== 'board');
    setComposerValue('');
    setSelectedCapability(null);
    conversationScrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function chooseCapability(capability: CapabilityItem) {
    setCapabilityCenterOpen(false);
    setCommandOpen(false);
    setSelectedCapability(capability);
    if (capability.scenario) {
      chooseScenario(capability.scenario);
      return;
    }
    setCanvasOpen(false);
    setComposerValue(capability.prompt);
  }

  function submitComposer() {
    const normalized = composerValue.toLowerCase();
    if (normalized.includes('board') || normalized.includes('décision') || normalized.includes('arbitr')) chooseScenario('board');
    else if (normalized.includes('atelier') || normalized.includes('mission') || normalized.includes('implément')) chooseScenario('atelier');
    else if (normalized.includes('devis') || normalized.includes('facture')) chooseScenario('invoice');
    else if (normalized.includes('email') || normalized.includes('mail') || normalized.includes('message')) chooseScenario('email');
    else if (normalized.includes('contact') || normalized.includes('mémoire') || normalized.includes('personne')) chooseScenario('memory');
    else if (normalized.includes('rendez') || normalized.includes('claire')) chooseScenario('meeting');
    else chooseScenario('today');
    setSelectedCapability(null);
  }

  const SelectedCapabilityIcon = selectedCapability?.icon;

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#F3F6FC] text-[#101C36]" data-testid="conversation-canvas-prototype">
      <div className="flex h-full flex-col">
        <header className="flex h-14 shrink-0 items-center border-b border-[#DCE4F1] bg-white px-4">
          <div className="flex flex-1 items-center gap-4">
            <div className="flex items-center gap-2" aria-hidden="true">
              <span className="h-3 w-3 rounded-full bg-[#FF605C]" />
              <span className="h-3 w-3 rounded-full bg-[#FFBD44]" />
              <span className="h-3 w-3 rounded-full bg-[#00CA4E]" />
            </div>
            <div className="h-5 w-px bg-[#DCE4F1]" />
            <div className="flex items-center gap-2.5">
              <span className="relative h-2.5 w-2.5 rounded-full bg-[#22D3EE]">
                <span className="absolute inset-0 rounded-full bg-[#22D3EE] opacity-40 blur-[4px]" />
              </span>
              <span className="text-sm font-bold tracking-[0.02em] text-[#101C36]">THÉRÈSE</span>
              <span className="rounded-full border border-[#DCE4F1] bg-[#F7F9FD] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-[#7B8AA3]">Prototype</span>
            </div>
          </div>

          <button type="button" className="flex items-center gap-2 rounded-[10px] border border-[#DCE4F1] bg-[#F7F9FD] px-3 py-2 text-xs font-semibold text-[#33415C] hover:bg-white">
            <Briefcase className="h-3.5 w-3.5 text-[#0F8FB3]" />
            Synoptïa
            <ChevronDown className="h-3.5 w-3.5 text-[#7B8AA3]" />
          </button>

          <div className="flex flex-1 items-center justify-end gap-1.5">
            <button
              type="button"
              onClick={() => {
                setTrustCenterOpen((open) => !open);
                setCapabilityCenterOpen(false);
                setCommandOpen(false);
              }}
              className="mr-1 hidden items-center gap-1.5 rounded-full border border-[#CDEAF0] bg-[#F1FBFC] px-2.5 py-1.5 text-[11px] font-semibold text-[#315D69] hover:border-[#9ED7E1] sm:flex"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-[#0F8FB3]" />
              Contrôle des données
            </button>
            <button
              type="button"
              onClick={() => {
                setCommandOpen(true);
                setCapabilityCenterOpen(false);
                setTrustCenterOpen(false);
              }}
              className="hidden items-center gap-2 rounded-[9px] border border-[#DCE4F1] bg-white px-2.5 py-1.5 text-xs text-[#5B6A82] hover:bg-[#F7F9FD] md:flex"
            >
              <Search className="h-3.5 w-3.5" />
              Rechercher
              <kbd className="rounded-[5px] bg-[#F3F6FC] px-1.5 py-0.5 text-[9px] text-[#7B8AA3]">⌘K</kbd>
            </button>
            <IconButton label="Notifications"><Bell className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Paramètres"><Settings className="h-[18px] w-[18px]" /></IconButton>
          </div>
        </header>

        <div className="relative flex min-h-0 flex-1">
          <nav aria-label="Navigation principale" className="flex w-16 shrink-0 flex-col items-center border-r border-[#DCE4F1] bg-[#F8FAFD] py-3">
            <IconButton label="Conversations" onClick={() => setDrawerOpen((open) => !open)} active={drawerOpen}>
              <Menu className="h-[18px] w-[18px]" />
            </IconButton>
            <div className="my-2 h-px w-7 bg-[#DCE4F1]" />
            <IconButton label="Nouvelle conversation"><Plus className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Rechercher" onClick={() => { setCommandOpen(true); setCapabilityCenterOpen(false); setTrustCenterOpen(false); }}><Search className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Historique"><History className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Espaces de travail"><Folder className="h-[18px] w-[18px]" /></IconButton>
            <div className="mt-auto flex flex-col items-center gap-1.5">
              <IconButton label="Aide"><MessageSquare className="h-[18px] w-[18px]" /></IconButton>
              <button type="button" className="grid h-9 w-9 place-items-center rounded-full border border-[#101C36] bg-[#101C36] text-[11px] font-bold text-white shadow-[2px_2px_0_#22D3EE]" title="Profil Ludo">LS</button>
            </div>
          </nav>

          <AnimatePresence>{drawerOpen && <ConversationDrawer onClose={() => setDrawerOpen(false)} />}</AnimatePresence>

          <main id="main-content" className="relative flex min-w-0 flex-1 overflow-hidden">
            <section className="relative flex min-w-0 flex-1 flex-col bg-[#F3F6FC]">
              <div ref={conversationScrollRef} className="flex-1 overflow-y-auto px-5 pb-44 pt-7 sm:px-8">
                <div className={`mx-auto transition-[max-width] duration-200 ${canvasOpen ? 'max-w-[760px]' : 'max-w-[860px]'}`}>
                  <div className="mb-7 flex items-start gap-3">
                    <CharacterPortrait index={0} className="mt-0.5 h-8 w-8 rounded-[10px] border border-[#101C36] shadow-[2px_2px_0_#101C36]" />
                    <div>
                      <h1 className="text-[24px] font-bold tracking-[-0.035em] text-[#101C36]">Bonjour Ludo.</h1>
                      <p className="mt-1 text-sm leading-6 text-[#5B6A82]">
                        {scenario === 'today'
                          ? "J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module."
                          : scenario === 'memory'
                            ? 'Je consulte les contacts réellement enregistrés et leur contexte local, sans rien modifier.'
                          : scenario === 'email'
                            ? 'Je consulte la boîte connectée. Tu peux lire un message et préparer un brouillon sans l’envoyer.'
                          : scenario === 'meeting'
                            ? 'J’ai rassemblé le contexte utile pour ton rendez-vous, sans modifier tes données.'
                            : scenario === 'invoice'
                              ? 'Je consulte les documents réellement enregistrés. Tu peux aussi préparer un devis brouillon avant toute génération ou envoi.'
                              : scenario === 'board'
                                ? 'Je consulte les décisions enregistrées. Tu peux relire un historique ou préparer une nouvelle question avant de lancer quoi que ce soit.'
                                : 'Je consulte les missions réellement enregistrées. Tu peux cadrer un changement, suivre son exécution isolée et relire le diff avant toute application.'}
                      </p>
                    </div>
                  </div>

                  <div className="mb-5 flex justify-end">
                    <div className="max-w-[78%] rounded-[15px_15px_4px_15px] border border-[#CFE9EE] bg-[#E8F8FB] px-4 py-2.5 text-sm text-[#284C56]">
                      {scenarioPrompts[scenario]}
                    </div>
                  </div>

                  <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold text-[#7B8AA3]">
                    <CharacterPortrait index={0} className="h-5 w-5 rounded-[6px] border border-[#101C36]" />
                    THÉRÈSE
                    <span className="font-normal">· maintenant</span>
                  </div>

                  {scenario === 'today' ? (
                    <TodayDashboardCard
                      resource={todayResource}
                      onRetry={() => void refreshToday()}
                      onOpenView={openClassicView}
                    />
                  ) : scenario === 'memory' ? (
                    <ContactsMemoryCard
                      resource={contactsResource}
                      onRetry={() => void refreshContacts()}
                      onOpenContact={(contactId) => {
                        setSelectedContactId(contactId);
                        setCanvasOpen(true);
                      }}
                      onOpenClassic={() => openClassicView('memory')}
                    />
                  ) : scenario === 'email' ? (
                    <EmailInboxCard
                      resource={emailInboxResource}
                      onRetry={() => void refreshEmailInbox()}
                      onOpenMessage={(messageId) => {
                        setCanvasOpen(true);
                        void openEmailMessage(messageId);
                      }}
                      onOpenClassic={() => openClassicView('email')}
                    />
                  ) : scenario === 'meeting' ? (
                    <MeetingCard onOpen={() => setCanvasOpen(true)} />
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
                      onOpenClassic={() => openClassicView('invoices')}
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
                      onOpenClassic={() => openClassicPanel('board')}
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
                      onOpenClassic={() => openClassicPanel('atelier')}
                    />
                  )}

                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <span className="mr-1 text-[11px] font-medium text-[#7B8AA3]">Sources</span>
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
                        <SourceChip icon={<HardDrive className="h-3 w-3" />} label="Mémoire locale" />
                        <SourceChip icon={<Mail className="h-3 w-3" />} label="Email" />
                        <SourceChip icon={<Calendar className="h-3 w-3" />} label="Agenda" />
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

                  <div className="mt-9 border-t border-[#DCE4F1] pt-5">
                    <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#7B8AA3]">Essayer un autre parcours</div>
                    <div className="flex flex-wrap gap-2">
                      {(['today', 'memory', 'email', 'meeting', 'invoice', 'board', 'atelier'] as Scenario[]).map((item) => (
                        <button
                          key={item}
                          type="button"
                          onClick={() => chooseScenario(item)}
                          className={`rounded-full border px-3 py-2 text-xs font-semibold ${
                            scenario === item
                              ? 'border-[#101C36] bg-[#101C36] text-white'
                              : 'border-[#DCE4F1] bg-white text-[#5B6A82] hover:border-[#AEBACD] hover:text-[#101C36]'
                          }`}
                        >
                          {scenarioLabels[item]}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-[linear-gradient(to_top,#F3F6FC_70%,transparent)] px-5 pb-5 pt-12 sm:px-8">
                <div className={`pointer-events-auto mx-auto transition-[max-width] duration-200 ${canvasOpen ? 'max-w-[760px]' : 'max-w-[860px]'}`}>
                  <div className="rounded-[18px] border border-[#CBD6E6] bg-white p-2 shadow-[0_18px_45px_-24px_rgba(16,28,54,0.45)] focus-within:border-[#22D3EE] focus-within:shadow-[0_0_0_3px_rgba(34,211,238,0.12),0_18px_45px_-24px_rgba(16,28,54,0.45)]">
                    {selectedCapability && SelectedCapabilityIcon && (
                      <div className="mx-1 mt-1 flex items-center gap-2 rounded-[10px] border border-[#E1D9F5] bg-[#F7F3FE] px-2.5 py-2 text-xs text-[#5B477E]">
                        <span className="grid h-6 w-6 place-items-center rounded-[7px] bg-[#EAE1FB] text-[#7C3AED]">
                          <SelectedCapabilityIcon className="h-3.5 w-3.5" />
                        </span>
                        <span className="min-w-0 flex-1 truncate"><span className="font-semibold">Capacité :</span> {selectedCapability.title}</span>
                        <button type="button" onClick={() => setSelectedCapability(null)} aria-label="Retirer la capacité" className="grid h-6 w-6 place-items-center rounded-[7px] hover:bg-white">
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}
                    <textarea
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
                      className="max-h-28 min-h-12 w-full resize-none bg-transparent px-2.5 py-2 text-sm leading-6 text-[#101C36] outline-none placeholder:text-[#9AA7BB]"
                    />
                    <div className="flex items-center justify-between gap-3 px-1 pb-1">
                      <div className="flex items-center gap-1">
                        <IconButton label="Joindre un fichier"><Paperclip className="h-[17px] w-[17px]" /></IconButton>
                        <IconButton label="Dicter"><Mic className="h-[17px] w-[17px]" /></IconButton>
                        <button
                          type="button"
                          onClick={() => {
                            setCapabilityCenterOpen(true);
                            setCommandOpen(false);
                            setTrustCenterOpen(false);
                          }}
                          className="flex h-9 items-center gap-1.5 rounded-[10px] px-2.5 text-xs font-medium text-[#5B6A82] hover:bg-[#F3F6FC] hover:text-[#101C36]"
                        >
                          <Plus className="h-4 w-4" />
                          Capacités
                        </button>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="hidden items-center gap-1 text-[10px] font-medium text-[#7B8AA3] sm:flex">
                          <Globe className="h-3 w-3" />
                          Auto · Local prioritaire
                        </span>
                        <button
                          type="button"
                          onClick={submitComposer}
                          aria-label="Envoyer"
                          className="grid h-9 w-9 place-items-center rounded-[10px] border border-[#101C36] bg-[#22D3EE] text-[#06121F] shadow-[2px_2px_0_#101C36] hover:-translate-y-0.5"
                        >
                          <ArrowUp className="h-[18px] w-[18px]" />
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 text-center text-[10px] text-[#8A97AB]">Thérèse montre ses sources et demande confirmation avant toute action externe.</div>
                </div>
              </div>
            </section>

            <AnimatePresence>
              {canvasOpen && scenario !== 'today' && (
                <ContextCanvas
                  scenario={scenario}
                  onClose={() => {
                    if (scenario === 'board') cancelBoardDeliberation();
                    if (scenario === 'atelier') void cancelAtelierMission();
                    setCanvasOpen(false);
                  }}
                  contactsResource={contactsResource}
                  emailMessageResource={emailMessageResource}
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
                  onRetryInvoices={() => void refreshInvoices()}
                  onRetryInvoice={() => void retryInvoice()}
                  onCreateDevisDraft={createDevisDraft}
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
                />
              )}
            </AnimatePresence>
          </main>
        </div>
      </div>

      <AnimatePresence>
        {commandOpen && (
          <CommandPalette
            onClose={() => setCommandOpen(false)}
            onSelect={chooseScenario}
            onCapability={chooseCapability}
          />
        )}
        {capabilityCenterOpen && (
          <CapabilityCenter onClose={() => setCapabilityCenterOpen(false)} onChoose={chooseCapability} />
        )}
        {trustCenterOpen && <TrustCenter onClose={() => setTrustCenterOpen(false)} />}
      </AnimatePresence>
    </div>
  );
}
