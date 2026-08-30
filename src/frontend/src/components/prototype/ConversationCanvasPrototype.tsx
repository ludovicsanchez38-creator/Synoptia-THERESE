import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { BoutonFermerLePanneau } from './BoutonFermerLePanneau';
import { AnimatePresence, motion, useIsPresent } from 'framer-motion';
import {
  AlertCircle,
  ArrowUp,
  Bot,
  Briefcase,
  Calendar,
  ChevronRight,
  Folder,
  HardDrive,
  History,
  Mail,
  HelpCircle,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  User,
  Users,
  X,
  Home,
} from 'lucide-react';
import {
  CapabilityCenter,
  TrustCenter,
  capabilities,
  featuredCapabilities,
  type CapabilityItem,
} from './CapabilityCenter';
import { CharacterPortrait } from './DecisionMissionPrototype';
import { ConnectionStatus } from '../ui/ConnectionStatus';
import { WindowControls } from '../window/WindowControls';
import { isMacPlatform } from '../../lib/platform';
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
import { Spinner } from '../ui/Spinner';
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
import { CLIENT_ACTION_EVENT } from '../../lib/clientActions';
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
import { TraitementsIndicator } from '../traitements/TraitementsIndicator';
import { useConversationSync } from '../../hooks/useConversationSync';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { usePanelStore } from '../../stores/panelStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { useAtelierStore } from '../../stores/atelierStore';
import { useDemoStore } from '../../stores/demoStore';
import { useNavigationStore, type AppView } from '../../stores/navigationStore';
import { consumeHandoffPrompt, resolveDeepLinkAction, resolveDeepLinkPanel, resolveDeepLinkView, resolveSettingsTab, nettoyerLiensProfondsConsommes } from '../../lib/deepLinks';
import { usePanelStore as usePanelStoreDirect } from '../../stores/panelStore';
import { useAtelierStore as useAtelierStoreDirect } from '../../stores/atelierStore';
import { useActionsStore as useActionsStoreDirect } from '../../stores/actionsStore';
import { runTopEscapeHandler } from '../../lib/escapeStack';
import { useContactsStore as useContactsStoreDirect } from '../../stores/contactsStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { PanelContainer } from '../chat/PanelContainer';
import { listUserCommands, type UserCommand } from '../../services/api/commands';
import type { SlashCommand } from '../chat/SlashCommandsMenu';
import { ShortcutsModal } from '../chat/ShortcutsModal';
import { VoiceDictationButton } from '../chat/VoiceDictationButton';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { estCoteACote, usePanneauCouvrant } from '../../hooks/usePanneauCouvrant';
import { VoilePanneau } from './VoilePanneau';
import { ACTIONS_ETABLI, ICONES_ETABLI, PLACEHOLDER_COMPOSEUR, TITRES_ETABLI } from '../../lib/etabli';
import { actionsDeLEtabli } from '../../lib/etabliDePremierLancement';
import { actionsAuRepos } from '../../lib/paletteAuRepos';
import { fetchSetupStatus, type SetupStatus } from '../../services/api/dashboard';

type Scenario = 'today' | 'memory' | 'email' | 'meeting' | 'invoice' | 'board' | 'atelier';
type RightPanelTool = 'calculator' | 'deliverables' | 'images' | 'follow-ups' | 'voice';
// E3 : les titres des CINQ verbes de l'établi viennent de `lib/etabli`, à côté
// des verbes eux-mêmes. Leur éloignement est ce qui a permis la dérive de la
// v0.53.0 : l'entrée 10 a changé ce que « Écrire » fait, cette table est restée
// sur « Consulter mes emails », et le canevas l'annonçait aux lecteurs d'écran.
// `today` et `atelier` ne sont pas des verbes de l'établi : ils restent ici.
const scenarioLabels: Record<Scenario, string> = {
  ...TITRES_ETABLI,
  today: 'Mes priorités du jour',
  atelier: 'Confier une mission',
};

const scenarioPrompts: Record<Scenario, string> = {
  today: "Qu'est-ce qui demande mon attention aujourd'hui ?",
  memory: 'Retrouve mes contacts récents et leur contexte mémorisé.',
  email: 'Aide-moi à écrire un message : propose un objet et un corps que je pourrai relire.',
  meeting: 'Prépare mon prochain rendez-vous et montre-moi uniquement le contexte vérifiable.',
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
      className={`grid h-11 w-11 place-items-center rounded-[10px] border transition-colors ${
        active
          ? 'border-accent-fill bg-accent-fill text-accent-ink'
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
  redactionLibre,
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
  onEnsureMeetingCalendar,
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
  /** Entrée 10 : « Écrire » ouvre une rédaction, pas une liste. */
  redactionLibre: boolean;
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
  onEnsureMeetingCalendar: () => Promise<void>;
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
  // Hotfix 0.48.1 : isolation seulement quand le panneau RECOUVRE la zone.
  // Revue passe 2 : le clavier reste À LA PAGE en toutes circonstances -
  // le rail et l'en-tête sont actifs, un piège les rendrait inatteignables,
  // et un réarmement au redimensionnement volerait Escape à une modale.
  const estCouvrant = usePanneauCouvrant();
  useDialogFocusTrap(dialogRef, {
    active: isPresent,
    onEscape: onClose,
    isolateBackground: estCouvrant,
    piegeClavier: false,
  });

  return (
    <motion.aside
      ref={dialogRef}
      // E5 : `role="dialog"` promettait un focus contenu, une page neutralisée
      // et un Échap qui rend la main. Avec `piegeClavier: false` — délibéré,
      // le panneau vit côte à côte avec la conversation au-dessus du seuil xl —
      // rien de tout cela n'est vrai, et un lecteur d'écran annonçait
      // « dialogue ». La revue 0.49 avait corrigé les six panneaux frères ;
      // celui-ci y avait échappé, étant une fonction interne de la coque et
      // non un fichier `*Canvas.tsx`. C'est pourtant la surface que les cinq
      // verbes ouvrent.
      role="region"
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
      <BoutonFermerLePanneau onClose={onClose} />
      {scenario === 'email' ? (
        <EmailMessageCanvas
          resource={emailMessageResource}
          nouvelleRedaction={redactionLibre}
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
          onEnsureCalendar={onEnsureMeetingCalendar}
          onAbandon={onClose}
          onOpenClassic={() => onOpenView('calendar')}
        />
      ) : scenario === 'invoice' ? (
        <InvoiceWorkspaceCanvas
          resource={invoiceResource}
          invoiceResource={invoiceDetailResource}
          selection={selectedInvoiceId}
          /* Entrée 2 : le client déjà à l'écran arme le nouveau devis. La
             valeur reste modifiable dans le formulaire. */
          contactInitial={selectedContactId ?? undefined}
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
      // Les parcours sont listés juste au-dessus : une capacité qui mène au
      // même scénario ferait doublon dans la même palette, et deux entrées
      // pour une seule destination font douter qu'elles soient identiques.
      // Le cas préexistait pour Email, Contacts et Devis et factures ; la
      // puce « Décider » en aurait ajouté un quatrième.
      const dejaEnParcours = new Set<string>(ACTIONS_ETABLI.map((a) => a.id));
      return featuredCapabilities
        .map((id) => capabilities.find((item) => item.id === id))
        .filter((item): item is CapabilityItem => Boolean(item))
        .filter((item) => !item.scenario || !dejaEnParcours.has(item.scenario));
    }
    return capabilities
      .filter((item) =>
        [item.title, item.description, ...item.features, ...item.keywords].join(' ').toLowerCase().includes(normalized),
      )
      .slice(0, 8);
  }, [query]);
  const visibleActions = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      // Entrée 1 : la palette rendait une liste vide tant qu'on n'avait rien
      // tapé, alors que des destinations câblées attendaient. Elle suggère
      // maintenant celles qu'aucune autre section n'annonce déjà — les
      // parcours et les capacités sont listés juste au-dessus.
      return actionsAuRepos(
        getActions(),
        ACTIONS_ETABLI.map((a) => a.id),
        visibleCapabilities.map((c) => c.id),
      );
    }
    return getActions().filter((action) =>
      [action.label, action.description || '', ...(action.keywords || [])]
        .join(' ')
        .toLowerCase()
        .includes(normalized),
    ).slice(0, 6);
  }, [query, visibleCapabilities]);
  const scenarioCount = query ? 0 : ACTIONS_ETABLI.length;
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
              {ACTIONS_ETABLI.map((action, optionIndex) => (
                <button
                  key={action.id}
                  id={`prototype-command-option-${optionIndex}`}
                  role="option"
                  aria-selected={activeOption === optionIndex}
                  tabIndex={-1}
                  type="button"
                  onMouseEnter={() => setActiveOption(optionIndex)}
                  onClick={() => {
                    onSelect(action.id);
                    onClose();
                  }}
                  className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2.5 text-left hover:bg-bg"
                >
                  <span className="grid h-8 w-8 place-items-center overflow-hidden rounded-[8px] bg-accent-tint text-accent">
                    {(() => {
                      // Table exhaustive plutôt qu'une cascade : la branche
                      // fourre-tout d'avant donnait l'icône de la facture à
                      // toute action nouvelle, sans rien casser.
                      const Icone = ICONES_ETABLI[action.id];
                      return <Icone className="h-4 w-4" />;
                    })()}
                  </span>
                  <span className="flex-1">
                    <span className="block text-sm font-semibold text-text">{action.label}</span>
                    <span className="block text-xs text-text-muted">{scenarioPrompts[action.id]}</span>
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


/**
 * Overlays de la pile unifiée, dans l'ordre de `cascade Échap de la coque` mais SANS son
 * retour de vue final : la coque enchaîne ensuite sur ses propres surfaces.
 * Retourne vrai si Échap a été consommé ici.
 */
/**
 * L'AUTORITÉ d'Échap pour toute l'application, avec la cascade de l'effet
 * clavier plus bas dans ce fichier.
 *
 * Il exista un `lib/cascade Échap de la coque.ts` qui se déclarait « UNE seule autorité
 * pour la touche Échap ». Il n'avait plus AUCUN appelant, alors que quatorze
 * composants lui déléguaient par commentaire : Échap ne marchait plus que par
 * l'ordre de cette cascade, que personne ne pouvait vérifier depuis les
 * composants qui le subissaient. Ses onze branches étant toutes couvertes ici
 * — et sept d'entre elles ne pouvant PAS l'être ailleurs, puisqu'elles portent
 * sur des états locaux de la coque que les stores ne voient pas —, il a été
 * retiré le 27/08/2026 plutôt que rebranché.
 *
 * Deux moitiés, dans cet ordre : ici les overlays portés par les STORES, puis
 * dans l'effet clavier les surfaces LOCALES (palette, tiroir, centre de
 * confiance, chat, vue embarquée, panneaux). Une surface nouvelle doit
 * s'inscrire dans l'une des deux — il n'y a pas de troisième endroit.
 */
function consommeEchapUnifie(): boolean {
  if (runTopEscapeHandler()) return true;
  const ps = usePanelStoreDirect.getState();
  if (ps.showSaveCommand) { ps.closeSaveCommand(); return true; }
  if (ps.showContactModal) { ps.closeContactModal(); return true; }
  if (ps.showProjectModal) { ps.closeProjectModal(); return true; }
  if (ps.showBoardPanel) { ps.closeBoardPanel(); return true; }
  if (ps.showShortcuts) { ps.closeShortcuts(); return true; }
  if (ps.showSettings) { ps.closeSettings(); return true; }
  if (ps.showPromptLibrary) { ps.closePromptLibrary(); return true; }
  if (useAtelierStoreDirect.getState().isOpen) { useAtelierStoreDirect.getState().closePanel(); return true; }
  if (useActionsStoreDirect.getState().isPanelOpen) { useActionsStoreDirect.getState().closePanel(); return true; }
  return false;
}

export function ConversationCanvasPrototype() {
  const theme = useAccessibilityStore((state) => state.theme);
  const highContrast = useAccessibilityStore((state) => state.highContrast);
  const initialScenario = useMemo<Scenario>(() => {
    const value = new URLSearchParams(window.location.search).get('scenario');
    return value === 'memory' || value === 'email' || value === 'meeting' || value === 'invoice' || value === 'board' || value === 'atelier' ? value : 'today';
  }, []);
  const { resource: todayResource, refresh: refreshToday } = useTodayDashboardResource();
  // B1 (0.48) : la coque charge le SetupStatus (l'état vide honnête du brief).
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  /**
   * Tant que `setupStatus` n'est pas lu, on ne masque RIEN : un accueil qui
   * retire un verbe le temps d'une requête clignote, et un verbe qui clignote
   * est plus déroutant qu'un verbe de trop.
   */
  const actionsVisibles = useMemo(
    () =>
      setupStatus === null
        ? ACTIONS_ETABLI
        : actionsDeLEtabli({
            auMoinsUneFacture: setupStatus.has_invoices,
            infosSocieteCompletes: setupStatus.billing_complete,
          }),
    [setupStatus],
  );
  useEffect(() => {
    let annule = false;
    fetchSetupStatus()
      .then((statut) => { if (!annule) setSetupStatus(statut); })
      .catch(() => { /* indisponible : l'état vide standard s'affiche */ });
    return () => { annule = true; };
  }, []);
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
    ensureDefaultCalendar: ensureMeetingCalendar,
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
  /* L'heure du contenu affiché, figée à son apparition : une horloge qui
     défile attirerait l'œil sans rien apprendre de plus. */
  const [heureDAffichage] = useState(() =>
    new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
  );
  const [drawerSurface, setDrawerSurface] = useState<PrototypeConversationDrawerSurface>('history');
  const [commandOpen, setCommandOpen] = useState(false);
  const [capabilityCenterOpen, setCapabilityCenterOpen] = useState(false);
  const [trustCenterOpen, setTrustCenterOpen] = useState(false);
  const [selectedCapability, setSelectedCapability] = useState<CapabilityItem | null>(null);
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [selectedMeetingTarget, setSelectedMeetingTarget] = useState<MeetingTarget>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | 'new-devis' | null>(null);
  // Entrée 10 : pendant exact de 'new-devis'. « Écrire » ouvre une rédaction,
  // là où il menait à « Messages à consulter ».
  const [redactionLibre, setRedactionLibre] = useState(false);
  const [selectedBoardTarget, setSelectedBoardTarget] = useState<BoardTarget>(null);
  const [selectedAtelierTarget, setSelectedAtelierTarget] = useState<AtelierTarget>(
    initialScenario === 'atelier' ? 'new-mission' : null,
  );
  const [composerValue, setComposerValue] = useState('');
  const [composerVoiceError, setComposerVoiceError] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  // BUG-157 : `profile` seul ne distingue pas « chargement », « échec » et
  // « profil sans nom ». L'interface affichait donc un faux état normal (et
  // l'icône des Paramètres en repli du bouton Profil).
  const [profileState, setProfileState] = useState<'loading' | 'loaded' | 'error'>('loading');
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInitialPrompt, setChatInitialPrompt] = useState<string | null>(null);
  const [embeddedView, setEmbeddedView] = useState<Exclude<AppView, 'chat'> | null>(null);
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
    // BUG-139 : lire l'état VIVANT du store, pas la valeur capturée au dernier
    // rendu - la navigation déterministe s'exécute juste après la fin du flux,
    // avant le re-rendu, et se faisait refuser par une fermeture périmée.
    if (!useChatStore.getState().isStreaming) return false;
    useStatusStore.getState().addNotification({
      type: 'warning',
      title: 'Réponse en cours',
      message: 'Arrête la réponse avant de changer de vue ou de conversation.',
    });
    return true;
  }, []);

  const closeConversationDrawer = useCallback(() => {
    setDrawerOpen(false);
    // Le store reste la définition de l'action « Conversations » : le tenir
    // d'accord avec l'écran évite qu'un geste local et la commande divergent.
    if (usePanelStoreDirect.getState().showConversationSidebar) {
      usePanelStoreDirect.getState().closeConversationSidebar();
    }
  }, []);
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

  // Même patron que le pont J0a des vues, pour la même raison. L'action
  // « Conversations » (raccourci B, palette ⌘K) bascule
  // `showConversationSidebar` dans le panelStore ; la coque, elle, a son
  // propre tiroir en état local. La commande basculait donc un booléen que
  // personne n'affichait : un geste annoncé, exécuté sans erreur, et sans le
  // moindre effet visible.
  const tiroirDemande = usePanelStore((state) => state.showConversationSidebar);
  const dernierTiroirRef = useRef<boolean | null>(null);
  useEffect(() => {
    if (dernierTiroirRef.current === null) {
      dernierTiroirRef.current = tiroirDemande;
      return;
    }
    if (dernierTiroirRef.current === tiroirDemande) return;
    dernierTiroirRef.current = tiroirDemande;
    if (tiroirDemande) openConversationDrawer('history');
    else closeConversationDrawer();
    // openConversationDrawer est recréé à chaque rendu : l'inclure bouclerait.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tiroirDemande]);

  useEffect(() => {
    let active = true;
    // Contre-vérification N4 : plusieurs chargements peuvent se chevaucher
    // (montage + enregistrements successifs). Sans jeton, une réponse ancienne
    // écrase une plus récente et réaffiche l'ancien profil.
    let jeton = 0;
    const charger = () => {
      const courant = ++jeton;
      getProfile()
        .then((value) => {
          if (active && courant === jeton) { setProfile(value); setProfileState('loaded'); }
        })
        .catch(() => {
          if (active && courant === jeton) { setProfile(null); setProfileState('error'); }
        });
    };
    charger();
    // Revue Soso 27/07 (F6) : le profil n'était lu qu'au montage. Après un
    // enregistrement dans les Paramètres, les initiales, le nom d'espace et la
    // salutation restaient sur l'ancienne valeur jusqu'au redémarrage.
    window.addEventListener('therese:profile-updated', charger);
    return () => {
      active = false;
      window.removeEventListener('therese:profile-updated', charger);
    };
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

  // J0 (31/07) : l'écouteur `therese:insert-prompt` qui vivait ici a été
  // supprimé — il faisait doublon avec celui déclaré plus bas. Les deux
  // consultaient la garde de streaming, qui NOTIFIE quand elle refuse : un
  // seul geste produisait deux bandeaux « Réponse en cours ». Celui qui reste
  // délègue à `openChat`, qui pose en plus la vue canonique et remet à zéro le
  // composeur — ce que cette version ne faisait pas.

  const openChat = (prompt?: string) => {
    if (blockStreamingNavigation()) return;
    setChatInitialPrompt(prompt?.trim() || null);
    if (useNavigationStore.getState().activeView !== 'chat') {
      useNavigationStore.getState().setView('chat');
    }
    setEmbeddedView(null);
    // Entrée 9 : ouvrir le chat fermait l'objet qu'on venait de lire. Poser
    // une question sur un message coûtait de le perdre, puis de le rouvrir.
    // Sous le seuil, en revanche, le canevas recouvre la colonne et l'isole
    // (voile 0.48.1) : l'y laisser poserait `inert` sur la conversation qu'on
    // vient d'ouvrir — un chat à l'écran, et mort.
    if (!estCoteACote()) setCanvasOpen(false);
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
    // J0a : `navigationStore` est la source de navigation canonique. La coque
    // pilotait ses vues par un état local que le store ignorait, si bien que
    // les composants communs (accueil, registre d'actions, commandes) posaient
    // une vue que personne n'affichait.
    if (useNavigationStore.getState().activeView !== view) {
      useNavigationStore.getState().setView(view);
    }
  };
  // J0a : l'autre sens. Toute navigation posée dans le store - accueil
  // (QuickActions, TodayPanels, RecentConversations), registre d'actions,
  // commandes déterministes - doit devenir visible ici. Sans cet abonnement,
  // ces gestes changeaient un état que la coque n'observait pas.
  const viewDemandee = useNavigationStore((state) => state.activeView);
  // La référence part de la vue COURANTE, pas de `null`.
  //
  // `null` servait ici de sentinelle « effet pas encore initialisé ». Depuis
  // que `null` est aussi une valeur métier légitime — « aucune vue, la coque
  // montre son accueil » —, les deux sens sont entrés en collision : la
  // PREMIÈRE navigation depuis l'accueil était prise pour l'initialisation et
  // avalée. L'écran restait sur l'accueil pendant que le store disait autre
  // chose, pour tout geste qui appelle seulement `setView` (actions rapides de
  // l'accueil, « Tout voir » de l'agenda, raccourcis de mise en route).
  //
  // Partir de la valeur courante donne le même « ne rien forcer au montage »
  // sans avoir besoin d'une valeur réservée.
  const derniereVueRef = useRef<AppView | null>(viewDemandee);
  useEffect(() => {
    // Seuls les CHANGEMENTS de vue comptent : au montage, la référence vaut
    // déjà la vue courante, donc rien ne se déclenche.
    if (derniereVueRef.current === viewDemandee) return;
    // La référence n'avance QUE si la navigation aboutit. Refusée pendant un
    // flux, la demande resterait sinon perdue : `activeView` n'ayant pas
    // changé, aucun rattrapage n'aurait lieu à la fin du flux. D'où `isStreaming`
    // en dépendance : la demande en attente est rejouée dès que le flux finit.
    if (isStreaming) return;
    derniereVueRef.current = viewDemandee;
    if (viewDemandee === null) {
      // Retour à l'accueil : le store ne désigne plus aucune vue, l'écran
      // doit suivre. Sans cette branche, fermer par le store laissait la
      // dernière vue affichée - l'écran et la pile divergeaient à nouveau.
      // 28/08 : le chat aussi. « Revenir à l'accueil » depuis une
      // conversation ne ramenait rien, puisque le chat n'est pas une vue
      // embarquée — il occupe la colonne par un autre chemin.
      setEmbeddedView(null);
      setChatOpen(false);
      setCanvasOpen(false);
      return;
    }
    if (viewDemandee === 'chat') {
      if (!chatOpen) openChat();
      return;
    }
    if (embeddedView === viewDemandee) return;
    openEmbeddedView(viewDemandee);
    // openEmbeddedView et openChat sont recréés à chaque rendu : les inclure
    // relancerait l'effet en boucle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewDemandee, isStreaming]);

  // J0b : reprises de l'ancienne coque, qui les portait seule.
  //
  // 1. Le pont de recette `window.__therese` (appel bas niveau des actions et
  //    lecture des stores) : c'est l'outil de diagnostic des testeurs.
  // 2. L'insertion d'un prompt venu d'ailleurs (⌘K « Produire un document »,
  //    bibliothèque de prompts).
  // 3. Les liens profonds `?view=` / `?settings_tab=` et le prompt transmis.
  useEffect(() => {
    const surPromptInsere = (evenement: Event) => {
      const texte = (evenement as CustomEvent<string>).detail;
      // Garde reprise de l'écouteur fusionné : un prompt vide ne doit pas
      // ouvrir le chat (`openChat` accepte `null` et l'ouvrirait quand même).
      if (typeof texte !== 'string' || !texte.trim()) return;
      openChat(texte);
    };
    window.addEventListener('therese:insert-prompt', surPromptInsere as EventListener);
    (window as unknown as { __therese?: unknown }).__therese = {
      runAction,
      getActions,
      stores: {
        navigation: useNavigationStore,
        panel: usePanelStore,
        chat: useChatStore,
        atelier: useAtelierStore,
        actions: useActionsStoreDirect,
        contacts: useContactsStoreDirect,
      },
    };
    return () => window.removeEventListener('therese:insert-prompt', surPromptInsere as EventListener);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // F3 : la préférence « ignorer l'accueil » n'avait plus aucun effet depuis
    // le retrait du classic. On l'honore ici sans appeler `initializeView`, qui
    // poserait la vue 'home' et écraserait l'accueil conversationnel natif de
    // la coque (ce dernier REMPLACE l'ancien tableau de bord).
    const ignorerAccueil = usePersonalisationStore.getState().skipDashboard ?? false;
    const recherche = window.location.search;
    const vueDemandee = resolveDeepLinkView(recherche);
    const ongletReglages = resolveSettingsTab(recherche);
    const promptTransmis = consumeHandoffPrompt(recherche);
    if (promptTransmis) {
      openChat(promptTransmis);
    } else if (vueDemandee === 'chat') {
      openChat();
    } else if (vueDemandee) {
      openEmbeddedView(vueDemandee);
    }
    // F5 : ces deux paramètres étaient lus mais jamais appliqués - un lien
    // profond vers le Board ou les Actions n'ouvrait rien.
    const panneau = resolveDeepLinkPanel(recherche);
    if (panneau === 'board') toggleBoardPanel();
    else if (panneau === 'atelier') openAtelierPanel();
    const actionDemandee = resolveDeepLinkAction(recherche);
    if (actionDemandee) runAction(actionDemandee);
    if (ongletReglages) openSettings(ongletReglages);
    if (ignorerAccueil && !promptTransmis && !vueDemandee && !panneau && !actionDemandee) {
      openChat();
    }
    // Finding 9 : sans ce nettoyage, les paramètres restent dans l'URL et sont
    // rejoués à chaque rechargement — un lien vers les Réglages devenait
    // collant.
    nettoyerLiensProfondsConsommes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const collapseEmbeddedView = useCallback(() => {
    if (!embeddedView) return;
    setEmbeddedView(null);
    // Remédiation NO-GO J0 : sans retour dans le store, `activeView` restait
    // sur la vue fermée. Rejouer la même action devenait un no-op
    // (`setView` ignore une valeur identique) et la vue ne se rouvrait plus.
    if (useNavigationStore.getState().activeView === embeddedView) {
      useNavigationStore.getState().goBack();
    }
  }, [embeddedView]);
  const fermerLeChat = useCallback(() => {
    setChatOpen(false);
    setChatInitialPrompt(null);
    // Finding 7 : fermer le chat ne touchait que l'état local. Le store restait
    // sur `chat`, si bien qu'un `setView('chat')` ultérieur — celui qu'émet
    // `actionsStore` à la fin d'une Action — devenait un no-op. Le résultat
    // était ajouté à la conversation sans jamais la rouvrir : du travail qui
    // paraît perdu. Même patron que `collapseEmbeddedView`.
    if (useNavigationStore.getState().activeView === 'chat') {
      useNavigationStore.getState().goBack();
    }
  }, []);
  const collapseToolPanel = useCallback((tool: RightPanelTool) => {
    if (tool === 'calculator') setCalculatorOpen(false);
    else if (tool === 'deliverables') setDeliverablesOpen(false);
    else if (tool === 'images') setImagesOpen(false);
    else if (tool === 'follow-ups') setFollowUpsOpen(false);
    else setVoiceOpen(false);
    setCanvasOpen(false);
  }, []);
  const collapseScenarioPanel = useCallback(() => {
    if (scenario === 'today') return;
    setCanvasOpen(false);
  }, [scenario]);
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
    // Entrée 6 : le gestionnaire avait sa branche, la coque ne la remplissait
    // jamais. La fiche des raccourcis annonçait un groupe Fichiers vide.
    onOpenFile: () => openEmbeddedView('files'),
    onNewContact: () => usePanelStore.getState().openNewContact(),
    onNewProject: () => usePanelStore.getState().openNewProject(),
    onOpenSettings: () => openSettings('profile'),
    onSearch: () => openEmbeddedView('memory'),
    onToggleDemoMode: toggleDemoMode,
    onToggleAtelierPanel: toggleAtelierPanel,
    onOpenKatiaNewTask: openAtelierPanel,
  });

  // Hotfix 0.48.1 : un panneau latéral est ouvert ET recouvre la zone ?
  const panneauCouvrant = usePanneauCouvrant();
  const panneauLateralOuvert =
    calculatorOpen || deliverablesOpen || imagesOpen || followUpsOpen || voiceOpen
    || (canvasOpen && scenario !== 'today');

  // Relecture Grok, objection 2 : `openChat` lit la largeur UNE FOIS, alors que
  // l'isolation, elle, la suit (`usePanneauCouvrant` écoute `matchMedia`, le
  // piège de focus se réarme). Ouvrir large puis rétrécir posait donc `inert`
  // sur la conversation restée à côté — l'échec que l'entrée 9 refuse, avec un
  // geste de retard. Sous le seuil, le canevas cède la place, exactement comme
  // s'il avait été ouvert à cette largeur.
  useEffect(() => {
    if (chatOpen && canvasOpen && panneauCouvrant) setCanvasOpen(false);
  }, [chatOpen, canvasOpen, panneauCouvrant]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Remédiation NO-GO J0 : la cascade locale ignorait les modales gérées
        // par la pile unifiée (Réglages, contact, projet, bibliothèque, Actions,
        // Atelier). Échap fermait alors le chat DERRIÈRE la modale, ou ne
        // faisait rien. Ces overlays passent en premier.
        if (consommeEchapUnifie()) return;
        if (commandOpen) closeCommandPalette();
        else if (capabilityCenterOpen) closeCapabilityCenter();
        else if (trustCenterOpen) closeTrustCenter();
        else if (drawerOpen) closeConversationDrawer();
        else if (chatOpen) {
          if (blockStreamingNavigation()) return;
          fermerLeChat();
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
  }, [blockStreamingNavigation, calculatorOpen, canvasOpen, capabilityCenterOpen, chatOpen, closeCapabilityCenter, closeCommandPalette, closeConversationDrawer, closeTrustCenter, collapseEmbeddedView, collapseScenarioPanel, collapseToolPanel, commandOpen, deliverablesOpen, drawerOpen, embeddedView, fermerLeChat, followUpsOpen, imagesOpen, trustCenterOpen, voiceOpen]);

  /**
   * Ramener l'écran à l'accueil : l'établi sur le brief, aucun panneau, aucune
   * conversation. Distincte du retour PAR LE STORE (`viewDemandee === null`),
   * qui ferme les surfaces sans toucher au parcours : revenir d'une vue vers
   * l'établi ne doit pas effacer le parcours qu'on y avait choisi.
   */
  function rangerPourLAccueil() {
    setEmbeddedView(null);
    setChatOpen(false);
    setCanvasOpen(false);
    setCalculatorOpen(false);
    setDeliverablesOpen(false);
    setImagesOpen(false);
    setFollowUpsOpen(false);
    setVoiceOpen(false);
    setSelectedCapability(null);
    setRedactionLibre(false);
    setScenario('today');
    setComposerValue('');
  }

  function chooseScenario(next: Scenario) {
    if (blockStreamingNavigation()) return;
    setScenario(next);
    fermerLeChat();
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
    // Entrée 10 : le verbe le plus simple de l'établi demandait trois clics.
    // Il ouvre maintenant une rédaction, comme « Facturer » ouvre un devis.
    setRedactionLibre(next === 'email');
    setCanvasOpen(next !== 'today' && next !== 'invoice' && next !== 'board');
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
    fermerLeChat();
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
    // La destination est DÉCLARÉE dans la carte : l'ouvrir au clic, plutôt
    // que d'attendre une validation du composeur que rien n'annonce. Le
    // premier geste suffit là où il en fallait deux.
    //
    // Frontière : seules les destinations de NAVIGATION s'ouvrent ainsi. Une
    // carte de type `prompt` propose un texte à relire et à corriger avant
    // envoi — cette étape est une fonctionnalité, pas un frottement, et la
    // supprimer enverrait un message que personne n'a validé.
    if (capability.destination && capability.destination.kind !== 'prompt') {
      ouvrirDestination(capability.destination);
      setSelectedCapability(null);
      setComposerValue('');
      return;
    }
    setComposerValue(capability.prompt);
  }

  /**
   * Ouvre ce qu'une carte désigne. Partagé par le clic sur la carte et par la
   * validation du composeur : deux portes, une seule définition de ce que
   * « ouvrir » veut dire.
   */
  function ouvrirDestination(destination: NonNullable<CapabilityItem['destination']>) {
    if (destination.kind === 'pending') return;
    if (destination.kind === 'calculator') { setCalculatorOpen(true); setCanvasOpen(true); return; }
    if (destination.kind === 'deliverables') { setDeliverablesOpen(true); setCanvasOpen(true); return; }
    if (destination.kind === 'images') { setImagesOpen(true); setCanvasOpen(true); return; }
    if (destination.kind === 'follow-ups') { setFollowUpsOpen(true); setCanvasOpen(true); return; }
    if (destination.kind === 'voice') { setVoiceOpen(true); setCanvasOpen(true); return; }
    if (destination.kind === 'view') {
      if (destination.view === 'chat') openChat();
      else openEmbeddedView(destination.view);
      return;
    }
    if (destination.kind === 'action') {
      if (destination.action === 'settings.open') openSettings(destination.settingsTab);
      else runAction(destination.action);
    }
  }

  function submitComposer() {
    const destination = selectedCapability?.destination;
    // Les destinations de navigation s'ouvrent maintenant dès le clic sur la
    // carte ; ce chemin reste pour les cartes atteintes autrement (palette,
    // lien profond) et pour ne pas perdre une capacité déjà sélectionnée.
    if (destination && destination.kind !== 'prompt') {
      ouvrirDestination(destination);
      setSelectedCapability(null);
      setComposerValue('');
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

  // BUG-139 : les navigations déterministes du chat ({action: ouvrir crm})
  // arrivent par cet événement - la coque le revendique et ouvre la vue
  // EMBARQUÉE (le registre classique ne pilote pas cette interface).
  const runUnifiedActionRef = useRef<(actionId: string) => void>(() => {});
  useEffect(() => {
    const onClientAction = (event: Event) => {
      const detail = (event as CustomEvent<{ actionId?: string }>).detail;
      if (!detail?.actionId) return;
      event.preventDefault();
      runUnifiedActionRef.current(detail.actionId);
    };
    window.addEventListener(CLIENT_ACTION_EVENT, onClientAction);
    return () => window.removeEventListener(CLIENT_ACTION_EVENT, onClientAction);
  }, []);

  function runUnifiedAction(actionId: string) {
    const viewByAction: Partial<Record<string, Exclude<AppView, 'chat'>>> = {
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
    // 28/08 : « Accueil » ne désigne plus une vue embarquée mais l'accueil de
    // la coque — celui qu'on voit en ouvrant l'application.
    if (actionId === 'home.open') {
      if (blockStreamingNavigation()) return;
      useNavigationStore.getState().retourAccueil();
      // Relecture Grok, objection 1 : `retourAccueil()` remet `activeView` à
      // `null`. Depuis l'établi il y est DÉJÀ — « Écrire » passe par
      // `chooseScenario`, qui ne touche pas au store — et l'effet qui range
      // l'écran n'écoute que les CHANGEMENTS de vue. Le bouton ne faisait donc
      // rien sur le parcours le plus fréquent. Le ménage se fait ici.
      rangerPourLAccueil();
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
  runUnifiedActionRef.current = runUnifiedAction;

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
      /* J0a : la vue courante de la coque, lisible sans monter les panneaux
         embarqués (chargés en lazy). Sert aux tests et à la recette. */
      data-embedded-view={embeddedView ?? (chatOpen ? 'chat' : 'accueil')}
    >
      <div className="flex h-full flex-col">
        <header data-dialog-allow onMouseDown={startWindowDrag} className="flex min-h-14 shrink-0 items-center gap-3 border-b border-border bg-surface px-3 select-none sm:px-4">
          <WindowControls side="left" />
          <div className="flex min-w-0 flex-1 items-center gap-4">
            <div className="flex min-w-0 items-center gap-2.5">
              <span className="relative h-2.5 w-2.5 rounded-full bg-accent-fill" aria-hidden="true">
                <span className="absolute inset-0 rounded-full bg-accent-fill opacity-40 blur-[4px]" />
              </span>
              <span className="text-sm font-bold tracking-[0.02em] text-text">THÉRÈSE</span>
              <span className="hidden rounded-full border border-border bg-surface-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-text-muted lg:inline-flex">Interface unifiée</span>
            </div>
            {/* Finding 10 : l'état de connexion ne vivait que dans la surface
                de chat. Un utilisateur dans CRM, Fichiers ou Factures ne voyait
                plus rien quand le backend tombait — ses actions échouaient sans
                explication. Ici, il couvre toutes les vues. */}
            <div data-testid="etat-connexion-coque" className="shrink-0">
              <ConnectionStatus />
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
              <kbd className="rounded-[5px] bg-bg px-1.5 py-0.5 text-xs text-text-muted">{isMacPlatform() ? '⌘K' : 'Ctrl+K'}</kbd>
            </button>
            <TraitementsIndicator />
            <WindowControls side="right" />
          </div>
        </header>

        <div className="relative flex min-h-0 flex-1">
          <nav data-dialog-allow aria-label="Navigation principale" className="flex w-16 shrink-0 flex-col items-center border-r border-border bg-surface-2 py-3">
            {/* Signalé par Ludo le 28/08 : aucun bouton ne ramenait à l'accueil.
                On ne pouvait que fermer ce qu'on avait ouvert, ce qui suppose
                de savoir ce qu'on a ouvert. Il vient en tête du rail : c'est
                la destination la plus fondamentale de l'application. */}
            <IconButton label="Accueil" onClick={() => runUnifiedAction('home.open')}><Home className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Nouvelle conversation" onClick={startConversation}><Plus className="h-[18px] w-[18px]" /></IconButton>
            {/* Entrée 4 : deux boutons ouvraient le même tiroir, où `surface` ne
                change que le focus initial. Et « Rechercher » ici ne cherchait
                que dans les titres de conversation, jamais dans les mails, les
                fichiers ou les contacts, contrairement à ce que la loupe
                laissait croire. Le mot reste à la palette, qui indexe tout. */}
            <IconButton label="Conversations" onClick={() => openConversationDrawer('search')}><History className="h-[18px] w-[18px]" /></IconButton>
            <IconButton label="Projets" onClick={() => openEmbeddedView('projects')}><Folder className="h-[18px] w-[18px]" /></IconButton>
            {/* BUG-159 : accès permanent aux Paramètres, au-dessus de l'aide
                (demande Dr_logic) - ils n'étaient joignables que par la palette
                ou par le bouton Profil, dont la fonction n'était pas lisible. */}
            <div className="mt-auto flex flex-col items-center gap-1.5">
              <IconButton label="Paramètres" onClick={() => openSettings()}><Settings className="h-[18px] w-[18px]" /></IconButton>
              {/* Inventaire des capacités du 13/08/2026, deux défauts corrigés
                  d'un même geste.

                  Ce bouton écrivait « /aide » dans le composeur SANS l'envoyer.
                  L'utilisateur voyait du texte apparaître dans une zone de
                  saisie, et « /aide » déclenche par ailleurs le menu de
                  complétion : il fallait deviner qu'il restait à presser Entrée.

                  Et le centre des Capacités — le seul catalogue de ce que
                  THÉRÈSE sait faire — n'était atteignable que depuis le
                  composeur de l'accueil, donc invisible dès qu'une conversation
                  était ouverte. Un testeur qui commence par « Nouvelle
                  conversation » ne le voyait jamais.

                  Le bouton d'aide ouvre donc ce catalogue, depuis n'importe où. */}
              <IconButton label="Plus d’outils" onClick={() => setCapabilityCenterOpen(true)}><HelpCircle className="h-[18px] w-[18px]" /></IconButton>
              <button
                type="button"
                data-testid="shell-profile-button"
                onClick={() => openSettings('profile')}
                disabled={profileState === 'loading'}
                aria-label={
                  profileState === 'loading'
                    ? 'Chargement du profil…'
                    : profileState === 'error'
                      ? 'Profil indisponible - ouvrir le profil'
                      : 'Ouvrir le profil'
                }
                title={profileState === 'loading' ? 'Chargement du profil…' : 'Ouvrir le profil'}
                className="grid h-11 w-11 place-items-center rounded-full border border-accent-fill bg-accent-fill text-xs font-bold text-accent-ink shadow-[var(--shadow-card)] disabled:opacity-70"
              >
                {profileState === 'loading' ? (
                  <Spinner taille="bouton" />
                ) : profileState === 'error' ? (
                  <AlertCircle className="h-4 w-4" aria-hidden="true" />
                ) : displayName ? (
                  displayName.slice(0, 2).toLocaleUpperCase('fr-FR')
                ) : (
                  <User className="h-4 w-4" aria-hidden="true" />
                )}
              </button>
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
                  fermerLeChat();
                }}
              />
            ) : embeddedView ? (
              <PrototypeUnifiedViewCanvas view={embeddedView} onClose={collapseEmbeddedView} />
            ) : (
            <section data-testid="coque-colonne-principale" className="relative flex min-w-0 flex-1 flex-col bg-bg">
              <div ref={conversationScrollRef} className="flex-1 overflow-y-auto px-5 pb-44 pt-7 sm:px-8">
                <div className={`mx-auto transition-[max-width] duration-200 ${canvasOpen ? 'max-w-[760px]' : 'max-w-[860px]'}`}>
                  {(boardRun.status === 'running' || atelierRun.status === 'running') && (
                    <div className="mb-4 flex flex-wrap gap-2" data-testid="shell-background-activities" role="status">
                      {boardRun.status === 'running' && <button type="button" onClick={() => { setScenario('board'); setSelectedBoardTarget('current'); setCanvasOpen(true); }} className="inline-flex items-center gap-2 rounded-[10px] border border-[var(--k4)]/30 bg-[var(--k4bg)] px-3 py-2 text-xs font-semibold text-[var(--k4)]"><Spinner taille="ligne" />Board en arrière-plan · {boardRun.phase || 'délibération en cours'}</button>}
                      {atelierRun.status === 'running' && <button type="button" onClick={() => { setScenario('atelier'); setSelectedAtelierTarget('current'); setCanvasOpen(true); }} className="inline-flex items-center gap-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint px-3 py-2 text-xs font-semibold text-accent"><Spinner taille="ligne" />Atelier en arrière-plan · {atelierRun.phase || 'mission en cours'}</button>}
                    </div>
                  )}
                  <div className="mb-7 flex items-start gap-3">
                    <CharacterPortrait index={0} className="mt-0.5 h-8 w-8 rounded-[10px] border border-text shadow-[var(--shadow-card)]" />
                    <div>
                      <h1 className="text-[24px] font-bold tracking-[-0.035em] text-text">Bonjour{displayName ? ` ${displayName}` : ''}.</h1>
                      <p className="mt-1 text-sm leading-6 text-text-muted">
                        {scenario === 'today'
                          ? "J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module."
                          : scenario === 'memory'
                            ? 'Je consulte les contacts réellement enregistrés et leur contexte local, sans rien modifier.'
                          : scenario === 'email'
                            ? 'Je prépare un message. Tu peux le relire et le corriger : rien ne part d’ici.'
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
                    {/* « maintenant » était écrit en dur : il ne changeait
                        jamais et n'apprenait donc rien, tout en occupant une
                        place permanente. Une heure réelle dit de quand date
                        ce qu'on lit. */}
                    <span className="font-normal">· {heureDAffichage}</span>
                  </div>

                  {scenario === 'today' ? (
                    <TodayDashboardCard
                      resource={todayResource}
                      onRetry={() => void refreshToday()}
                      onOpenView={(view) => {
                        if (view === 'chat') openChat();
                        else openEmbeddedView(view);
                      }}
                      setup={setupStatus}
                      onSetupEmail={() => openEmbeddedView('email')}
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
                    {/* Entrée 3 : sur le brief, la carte affiche déjà ses
                        « Sources réelles », conditionnées aux données
                        chargées. Cette rangée-ci, écrite en dur, disait la
                        même chose deux centimètres plus bas. Les autres
                        parcours gardent la leur : elles ne se répètent pas,
                        elles disent ce que CE parcours peut faire. */}
                    {scenario !== 'today' && (
                      <span className="mr-1 text-xs font-medium text-text-muted">Sources</span>
                    )}
                    {scenario === 'today' ? null : scenario === 'memory' ? (
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
                        <SourceChip icon={<HardDrive className="h-3 w-3" />} label="Devis et factures" />
                        <SourceChip icon={<Users className="h-3 w-3" />} label="Tes clients" />
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
                      {actionsVisibles.map((action) => (
                        <button
                          key={action.id}
                          type="button"
                          onClick={() => chooseScenario(action.id)}
                          aria-pressed={scenario === action.id}
                          /* text-sm et non text-xs : ce sont les cinq gestes
                             principaux de l'accueil, ils avaient la taille de
                             « Connecté » et des mentions du bas de page. Une
                             action ne se lit pas comme une métadonnée. */
                          className={`rounded-full border px-3 py-2 text-sm font-semibold ${
                            scenario === action.id
                              ? 'border-accent-fill bg-accent-fill text-accent-ink'
                              : 'border-border bg-surface text-text-muted hover:border-border hover:text-text'
                          }`}
                        >
                          {action.label}
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
                        placeholder={PLACEHOLDER_COMPOSEUR}
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
                      {/* B1 (0.48) : le bouton « Capacités » du composeur est
                          retiré - le tiroir s'ouvre par sa porte unique du
                          rail (« Plus d'outils »). */}
                      <div className="flex items-center gap-1" />
                      <div className="flex items-center gap-2">
                        <span className="hidden text-xs font-medium text-text-muted sm:inline">Parcours réel · envoi et rendez-vous confirmés</span>
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
                          className="grid h-11 w-11 place-items-center rounded-[10px] border border-text bg-accent-fill text-accent-ink shadow-[var(--shadow-card)] hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:border-border disabled:bg-surface-2 disabled:text-text-muted disabled:shadow-none disabled:hover:translate-y-0"
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

            {/* Hotfix 0.48.1 : quand un panneau devient modal (petit écran),
                le fond isolé doit se VOIR - sinon l'app paraît figée. */}
            {panneauCouvrant && panneauLateralOuvert && <VoilePanneau />}

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
                  redactionLibre={redactionLibre}
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
                  onEnsureMeetingCalendar={ensureMeetingCalendar}
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
