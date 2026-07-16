/* eslint-disable react-refresh/only-export-components -- prototype catalogue and its visual browser intentionally share one module */
import { useMemo, useRef, useState, type ReactNode } from 'react';
import { motion, useIsPresent } from 'framer-motion';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { handleRovingFocus } from '../../lib/rovingFocus';
import {
  Bell,
  Bot,
  Briefcase,
  Calculator,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Database,
  FileText,
  Gauge,
  Gavel,
  Globe,
  HardDrive,
  Image,
  Key,
  ListTodo,
  Mail,
  Mic,
  Plug,
  Receipt,
  Scale,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Terminal,
  UserCheck,
  Users,
  Variable,
  Workflow,
  X,
  type LucideIcon,
} from 'lucide-react';
import { CharacterPortrait } from './DecisionMissionPrototype';
import type { AppView } from '../../stores/navigationStore';
import type { ClassicAction, ClassicSettingsTab } from '../../lib/classicNavigation';

export type CapabilityGroupId = 'organize' | 'business' | 'create' | 'decide' | 'automate' | 'control';
export type PrototypeScenario = 'today' | 'memory' | 'email' | 'meeting' | 'invoice' | 'board' | 'atelier';
export type CapabilityDestination =
  | { kind: 'view'; view: AppView }
  | { kind: 'action'; action: ClassicAction; settingsTab?: ClassicSettingsTab }
  | { kind: 'prompt' }
  | { kind: 'calculator' }
  | { kind: 'deliverables' }
  | { kind: 'images' }
  | { kind: 'follow-ups' }
  | { kind: 'voice' }
  | { kind: 'pending'; reason: string };

export interface CapabilityItem {
  id: string;
  group: CapabilityGroupId;
  title: string;
  description: string;
  features: string[];
  keywords: string[];
  prompt: string;
  icon: LucideIcon;
  scenario?: PrototypeScenario;
  destination?: CapabilityDestination;
}

interface CapabilityGroup {
  id: CapabilityGroupId;
  title: string;
  shortTitle: string;
  description: string;
  icon: LucideIcon;
  color: string;
  tint: string;
}

export const capabilityGroups: CapabilityGroup[] = [
  {
    id: 'organize',
    title: 'Organiser mon quotidien',
    shortTitle: 'Quotidien',
    description: 'Voir l’essentiel et transformer les informations entrantes en actions.',
    icon: Calendar,
    color: 'var(--k1)',
    tint: 'var(--k1bg)',
  },
  {
    id: 'business',
    title: 'Développer mon activité',
    shortTitle: 'Activité',
    description: 'Suivre les personnes, les projets et le cycle commercial de bout en bout.',
    icon: Briefcase,
    color: 'var(--k3)',
    tint: 'var(--k3bg)',
  },
  {
    id: 'create',
    title: 'Créer et produire',
    shortTitle: 'Création',
    description: 'Passer d’une idée à un livrable utilisable, dans le bon format.',
    icon: FileText,
    color: 'var(--k2)',
    tint: 'var(--k2bg)',
  },
  {
    id: 'decide',
    title: 'Comprendre et décider',
    shortTitle: 'Décision',
    description: 'Chercher, vérifier, comparer et éclairer une décision importante.',
    icon: Gavel,
    color: 'var(--k4)',
    tint: 'var(--k4bg)',
  },
  {
    id: 'automate',
    title: 'Automatiser et déléguer',
    shortTitle: 'Automatisation',
    description: 'Faire exécuter des tâches répétitives par des actions, outils et agents.',
    icon: Workflow,
    color: 'var(--color-success)',
    tint: 'var(--color-success-tint)',
  },
  {
    id: 'control',
    title: 'Maîtriser Thérèse',
    shortTitle: 'Contrôle',
    description: 'Garder la main sur les données, les modèles, les coûts et le comportement.',
    icon: ShieldCheck,
    color: 'var(--color-text-muted)',
    tint: 'var(--color-surface-2)',
  },
];

export const capabilities: CapabilityItem[] = [
  {
    id: 'daily-brief', group: 'organize', title: 'Brief du jour', icon: Sparkles, scenario: 'today',
    description: 'Regrouper rendez-vous, urgences, relances et notifications dans une seule vue.',
    features: ['Dashboard', 'Notifications', 'Relances'], keywords: ['aujourd’hui', 'priorités', 'alertes'],
    prompt: "Qu’est-ce qui demande mon attention aujourd’hui ?",
  },
  {
    id: 'email', group: 'organize', title: 'Email', icon: Mail, scenario: 'email',
    description: 'Lire les messages et préparer des réponses avec le contexte de la relation.',
    features: ['IMAP/Gmail', 'Brouillons', 'Signatures'], keywords: ['mail', 'message', 'réponse'],
    prompt: 'Résume mes messages prioritaires et prépare les réponses nécessaires.',
  },
  {
    id: 'calendar', group: 'organize', title: 'Agenda', icon: Calendar, scenario: 'meeting',
    description: 'Préparer les rendez-vous et créer des événements sans changer d’écran.',
    features: ['CalDAV/Google', 'Ajout rapide', 'Import/Export ICS'], keywords: ['calendrier', 'rendez-vous', 'événement'],
    prompt: 'Prépare mon prochain rendez-vous et rassemble le contexte utile.',
  },
  {
    id: 'tasks', group: 'organize', title: 'Tâches', icon: ListTodo,
    description: 'Créer, prioriser et terminer les actions issues des conversations.',
    features: ['Création', 'Priorités', 'Complétion'], keywords: ['todo', 'action', 'liste'],
    prompt: 'Transforme cette conversation en liste de tâches priorisée.', destination: { kind: 'view', view: 'tasks' },
  },
  {
    id: 'attention', group: 'organize', title: 'Relances et alertes', icon: Bell,
    description: 'Faire remonter ce qui risque d’être oublié avant que cela devienne urgent.',
    features: ['Création depuis un email', 'Échéances', 'Suivi et complétion'], keywords: ['relance', 'retard', 'échéance'],
    prompt: 'Montre-moi les relances et échéances à traiter cette semaine.', destination: { kind: 'follow-ups' },
  },

  {
    id: 'contacts-memory', group: 'business', title: 'Contacts et mémoire', icon: Users, scenario: 'memory',
    description: 'Retrouver les personnes, notes et éléments de contexte sans chercher dans plusieurs modules.',
    features: ['Recherche hybride', 'Scopes', 'Extraction d’entités'], keywords: ['contact', 'mémoire', 'notes'],
    prompt: 'Retrouve tout ce que je sais sur cette personne et résume la relation.',
  },
  {
    id: 'crm', group: 'business', title: 'Pipeline commercial', icon: UserCheck,
    description: 'Suivre prospects, activités et étapes commerciales depuis la conversation.',
    features: ['Scoring', 'Pipeline', 'Activités'], keywords: ['crm', 'prospect', 'opportunité'],
    prompt: 'Analyse mon pipeline et indique les opportunités à faire avancer.', destination: { kind: 'view', view: 'crm' },
  },
  {
    id: 'projects', group: 'business', title: 'Projets', icon: Briefcase,
    description: 'Relier objectifs, contacts, budget, documents et tâches dans un même contexte.',
    features: ['Kanban', 'Budgets', 'Contacts liés'], keywords: ['projet', 'kanban', 'avancement'],
    prompt: 'Fais le point sur mes projets et signale les prochains blocages.', destination: { kind: 'view', view: 'projects' },
  },
  {
    id: 'billing', group: 'business', title: 'Devis et factures', icon: Receipt, scenario: 'invoice',
    description: 'Créer, vérifier et suivre les documents commerciaux avec validation avant envoi.',
    features: ['Devis/Factures/Avoirs', 'PDF conforme', 'Multi-devises'], keywords: ['devis', 'facture', 'paiement'],
    prompt: 'Crée un devis à partir de cette relation et montre-le-moi avant validation.',
  },
  {
    id: 'deliverables', group: 'business', title: 'Livrables et suivi client', icon: CheckCircle2,
    description: 'Relier ce qui a été promis, livré, facturé et reste à faire.',
    features: ['Livrables', 'Tâches restantes', 'Facturation du contact'], keywords: ['livraison', 'client', 'suivi'],
    prompt: 'Résume les livrables, factures et prochaines actions de ce client.', destination: { kind: 'deliverables' },
  },

  {
    id: 'document-workshop', group: 'create', title: 'Atelier documentaire', icon: FileText,
    description: 'Construire propositions, dossiers et rapports structurés avec un canevas éditable.',
    features: ['Trame', 'Sections', 'Réécriture'], keywords: ['document', 'rapport', 'proposition'],
    prompt: 'Aide-moi à construire un document structuré à partir de mes sources.', destination: { kind: 'view', view: 'documents' },
  },
  {
    id: 'office', group: 'create', title: 'Word, PowerPoint et Excel', icon: Database,
    description: 'Produire directement un fichier Office exploitable dans le format adapté.',
    features: ['DOCX', 'PPTX', 'XLSX'], keywords: ['word', 'powerpoint', 'excel', 'office'],
    prompt: 'Produis le livrable Office adapté à mon besoin et montre-moi un aperçu.', destination: { kind: 'action', action: 'guided.open' },
  },
  {
    id: 'images', group: 'create', title: 'Images', icon: Image,
    description: 'Générer un visuel, choisir le moteur et retrouver l’historique des créations.',
    features: ['Génération confirmée', 'Choix du provider', 'Historique réel'], keywords: ['visuel', 'photo', 'illustration'],
    prompt: 'Crée un visuel à partir de cette idée et respecte mon contexte de marque.', destination: { kind: 'images' },
  },
  {
    id: 'voice', group: 'create', title: 'Voix et transcription', icon: Mic,
    description: 'Dicter une demande ou transformer un enregistrement en texte exploitable.',
    features: ['Dictée', 'Import audio', 'Whisper et Piper'], keywords: ['audio', 'micro', 'transcription'],
    prompt: 'Transcris cet enregistrement puis extrais les décisions et actions.', destination: { kind: 'voice' },
  },
  {
    id: 'prompts-variables', group: 'create', title: 'Modèles et variables', icon: Variable,
    description: 'Réutiliser les meilleures formulations sans recopier les informations métier.',
    features: ['Bibliothèque de prompts', 'Variables', 'Commandes personnalisées'], keywords: ['template', 'modèle', 'commande'],
    prompt: 'Aide-moi à créer un modèle réutilisable avec les bonnes variables.', destination: { kind: 'action', action: 'prompt-library.open' },
  },

  {
    id: 'web-research', group: 'decide', title: 'Recherche web', icon: Globe,
    description: 'Chercher l’information actuelle et conserver des sources vérifiables.',
    features: ['Brave/SearXNG/DDG', 'Recherche approfondie', 'Citations'], keywords: ['web', 'internet', 'actualité'],
    prompt: 'Fais une recherche actuelle et cite précisément les sources utilisées.', destination: { kind: 'prompt' },
  },
  {
    id: 'files-rag', group: 'decide', title: 'Fichiers et connaissances', icon: HardDrive,
    description: 'Indexer et interroger les documents locaux avec recherche sémantique.',
    features: ['Indexation', 'RAG', 'PDF/DOCX/Texte'], keywords: ['fichier', 'pdf', 'indexation'],
    prompt: 'Analyse mes fichiers locaux sur ce sujet et relie les informations utiles.', destination: { kind: 'view', view: 'files' },
  },
  {
    id: 'decision-board', group: 'decide', title: 'Board de décision', icon: Gavel, scenario: 'board',
    description: 'Faire confronter cinq regards avant de prendre une décision importante.',
    features: ['5 conseillers', 'Consensus', 'Divergences'], keywords: ['board', 'décision', 'conseillers'],
    prompt: 'Convoque le Board pour analyser cette décision et expliciter les divergences.',
  },
  {
    id: 'calculators', group: 'decide', title: 'Calculateurs', icon: Calculator,
    description: 'Tester rapidement la viabilité ou la priorité d’une option.',
    features: ['ROI', 'ICE/RICE', 'VAN/Seuil de rentabilité'], keywords: ['calcul', 'rentabilité', 'priorité'],
    prompt: 'Calcule la rentabilité de cette option et explique les hypothèses.', destination: { kind: 'calculator' },
  },
  {
    id: 'legal', group: 'decide', title: 'Références juridiques', icon: Scale,
    description: 'Mobiliser le corpus vérifié et signaler clairement les points à confirmer.',
    features: ['Corpus juridique', 'Références vérifiées', 'Relecture humaine'], keywords: ['juridique', 'loi', 'clause'],
    prompt: 'Analyse ce point juridique avec des références vérifiables et signale les incertitudes.', destination: { kind: 'prompt' },
  },

  {
    id: 'actions', group: 'automate', title: 'Actions et relances', icon: Workflow,
    description: 'Lancer un rapport, une relance ou un audit et suivre son exécution.',
    features: ['Actions guidées', 'Suivi d’exécution', 'Résultat vérifiable'], keywords: ['action', 'rapport', 'audit'],
    prompt: 'Prépare une action automatisée pour ce besoin et demande ma validation avant exécution.', destination: { kind: 'action', action: 'actions.open' },
  },
  {
    id: 'agents', group: 'automate', title: 'Atelier d’agents', icon: Bot, scenario: 'atelier',
    description: 'Confier une mission cadrée à Katia et Zézette avec revue avant application.',
    features: ['Missions', 'Plan', 'Revue de code'], keywords: ['katia', 'zézette', 'agent'],
    prompt: 'Transforme ce besoin en mission cadrée pour l’Atelier et montre-moi le plan.',
  },
  {
    id: 'mcp', group: 'automate', title: 'Connecteurs MCP', icon: Plug,
    description: 'Accéder à des outils et services externes sans multiplier les interfaces.',
    features: ['Serveurs', 'Presets', 'Outils'], keywords: ['mcp', 'connecteur', 'notion', 'slack'],
    prompt: 'Trouve le connecteur adapté à ce besoin et explique les permissions nécessaires.', destination: { kind: 'action', action: 'settings.open', settingsTab: 'tools' },
  },
  {
    id: 'skills-commands', group: 'automate', title: 'Skills et commandes', icon: Terminal,
    description: 'Enregistrer les processus récurrents pour les relancer en langage naturel.',
    features: ['Skills', 'Commandes V3', 'Outils dynamiques'], keywords: ['skill', 'slash', 'workflow'],
    prompt: 'Transforme ce processus récurrent en commande réutilisable.', destination: { kind: 'prompt' },
  },

  {
    id: 'providers', group: 'control', title: 'Modèles et providers', icon: SlidersHorizontal,
    description: 'Laisser Thérèse choisir le bon modèle ou imposer un provider pour un usage.',
    features: ['Multi-LLM', 'Ollama local', 'Fallback'], keywords: ['claude', 'gpt', 'gemini', 'mistral'],
    prompt: 'Montre-moi quel modèle est utilisé pour chaque usage et pourquoi.', destination: { kind: 'action', action: 'settings.open', settingsTab: 'ai' },
  },
  {
    id: 'privacy', group: 'control', title: 'Données et RGPD', icon: ShieldCheck,
    description: 'Exporter, anonymiser et maîtriser ce qui est conservé ou transmis.',
    features: ['Export Art. 20', 'Anonymisation Art. 17', 'Consentement'], keywords: ['rgpd', 'export', 'anonymiser'],
    prompt: 'Montre-moi les données concernées et les options RGPD disponibles.', destination: { kind: 'action', action: 'settings.open', settingsTab: 'privacy' },
  },
  {
    id: 'security', group: 'control', title: 'Sécurité locale', icon: Key,
    description: 'Voir où résident les données, les clés et ce qui quitte la machine.',
    features: ['Secrets chiffrés', 'Trousseau système', 'Local/Cloud visible'], keywords: ['chiffrement', 'clé', 'local'],
    prompt: 'Explique précisément où sont stockées mes données et ce qui est transmis.', destination: { kind: 'action', action: 'settings.open', settingsTab: 'privacy' },
  },
  {
    id: 'usage', group: 'control', title: 'Coûts, limites et performance', icon: Gauge,
    description: 'Estimer le coût, contrôler les limites et suivre la consommation.',
    features: ['Estimation', 'Limites', 'Statistiques'], keywords: ['coût', 'token', 'usage', 'performance'],
    prompt: 'Résume ma consommation, mes limites et les optimisations possibles.', destination: { kind: 'action', action: 'settings.open', settingsTab: 'advanced' },
  },
  {
    id: 'profile', group: 'control', title: 'Profil et espace de travail', icon: Settings,
    description: 'Centraliser le profil émetteur, le dossier local et le contexte personnel.',
    features: ['Profil/SIRET/NDA', 'Dossier de travail', 'THERESE.md'], keywords: ['profil', 'siret', 'contexte'],
    prompt: 'Vérifie que mon profil et mon espace de travail sont correctement configurés.', destination: { kind: 'action', action: 'settings.open', settingsTab: 'profile' },
  },
  {
    id: 'personalization', group: 'control', title: 'Personnalisation', icon: UserCheck,
    description: 'Adapter l’interface, son démarrage et le niveau de fonctions visibles.',
    features: ['Mode standard/contributeur', 'Accessibilité', 'Démarrage'], keywords: ['personnaliser', 'préférences', 'mode'],
    prompt: 'Aide-moi à ajuster l’interface de Thérèse à ma façon de travailler.',
    destination: { kind: 'action', action: 'settings.open', settingsTab: 'advanced' },
  },
];

export const featuredCapabilities = ['daily-brief', 'email', 'contacts-memory', 'billing', 'decision-board', 'agents', 'document-workshop', 'web-research'];

function countForGroup(groupId: CapabilityGroupId) {
  return capabilities.filter((item) => item.group === groupId).length;
}

function FeaturePills({ features }: { features: string[] }) {
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {features.map((feature) => (
        <span key={feature} className="rounded-full border border-border bg-surface-2 px-2 py-0.5 text-xs font-semibold text-text-muted">
          {feature}
        </span>
      ))}
    </div>
  );
}

export function CapabilityCenter({
  onClose,
  onChoose,
}: {
  onClose: () => void;
  onChoose: (capability: CapabilityItem) => void;
}) {
  const [selectedGroup, setSelectedGroup] = useState<CapabilityGroupId>('organize');
  const [query, setQuery] = useState('');
  const dialogRef = useRef<HTMLElement>(null);
  const isPresent = useIsPresent();
  useDialogFocusTrap(dialogRef, { active: isPresent, onEscape: onClose, isolateBackground: true });

  const visibleCapabilities = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return capabilities.filter((item) => item.group === selectedGroup);
    return capabilities.filter((item) =>
      [item.title, item.description, ...item.features, ...item.keywords].join(' ').toLowerCase().includes(normalized),
    );
  }, [query, selectedGroup]);

  const activeGroup = capabilityGroups.find((group) => group.id === selectedGroup) ?? capabilityGroups[0];
  const ActiveGroupIcon = activeGroup.icon;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[70] flex items-center justify-center bg-text/35 p-2 backdrop-blur-[4px] sm:p-5"
      onClick={onClose}
    >
      <motion.section
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="capability-center-title"
        tabIndex={-1}
        initial={{ y: 18, scale: 0.985 }}
        animate={{ y: 0, scale: 1 }}
        exit={{ y: 18, scale: 0.985 }}
        transition={{ duration: 0.2 }}
        onClick={(event) => event.stopPropagation()}
        className="flex h-[calc(100vh-1rem)] w-full max-w-[1120px] flex-col overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_34px_90px_rgba(16,28,54,0.28)] sm:h-[min(760px,88vh)] sm:rounded-[20px]"
      >
        <header className="flex items-start gap-3 border-b border-border px-4 py-4 sm:gap-5 sm:px-6 sm:py-5">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[13px] border border-text bg-accent-tint text-accent shadow-[2px_2px_0_var(--btn-shadow-color)]">
            <Sparkles className="h-5 w-5" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 id="capability-center-title" data-dialog-autofocus tabIndex={-1} className="text-xl font-bold tracking-[-0.025em] text-text outline-none">Ce que Thérèse sait mobiliser</h2>
              <span className="rounded-full bg-bg px-2 py-1 text-xs font-semibold text-text-muted">{capabilities.length} capacités</span>
            </div>
            <p className="mt-1 text-sm text-text-muted">Tu demandes un résultat. Thérèse combine les fonctions utiles et garde les détails techniques en retrait.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Fermer les capacités" className="grid h-11 w-11 shrink-0 place-items-center rounded-[10px] border border-border text-text-muted hover:bg-bg hover:text-text">
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="flex min-h-0 flex-1 flex-col md:flex-row">
          <nav role="tablist" className="flex w-full shrink-0 gap-1 overflow-x-auto border-b border-border bg-surface-2 p-2 md:block md:w-[250px] md:overflow-y-auto md:border-b-0 md:border-r md:p-3" aria-label="Intentions">
            <div className="hidden px-2 pt-1 text-xs font-semibold uppercase tracking-[0.14em] text-text-muted md:mb-3 md:block">Je veux…</div>
            {capabilityGroups.map((group) => {
              const Icon = group.icon;
              const selected = selectedGroup === group.id && !query;
              return (
                <button
                  key={group.id}
                  id={`capability-group-${group.id}`}
                  type="button"
                  role="tab"
                  aria-selected={selectedGroup === group.id}
                  aria-controls="capability-results-panel"
                  tabIndex={selectedGroup === group.id ? 0 : -1}
                  onKeyDown={(event) => handleRovingFocus(
                    event,
                    '[role="tab"]',
                    event.key === 'ArrowUp' || event.key === 'ArrowDown' ? 'vertical' : 'horizontal',
                  )}
                  onClick={() => {
                    setSelectedGroup(group.id);
                    setQuery('');
                  }}
                  className={`flex min-h-11 shrink-0 items-center gap-2 rounded-[11px] px-3 py-2 text-left md:mb-1 md:w-full md:gap-3 md:py-3 ${selected ? 'bg-surface shadow-sm ring-1 ring-border' : 'hover:bg-surface/75'}`}
                >
                  <span className="grid h-8 w-8 place-items-center rounded-[9px]" style={{ backgroundColor: group.tint, color: group.color }}>
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-xs font-semibold text-text">{group.shortTitle}</span>
                    <span className="mt-0.5 hidden text-xs text-text-muted md:block">{countForGroup(group.id)} capacités</span>
                  </span>
                  <ChevronRight className={`hidden h-4 w-4 md:block ${selected ? 'text-text' : 'text-text-muted'}`} />
                </button>
              );
            })}
            <div className="mt-5 hidden rounded-[12px] border border-accent-cyan/30 bg-accent-tint p-3 md:block">
              <div className="flex items-center gap-2 text-xs font-semibold text-accent">
                <ShieldCheck className="h-4 w-4 text-accent" />
                Toujours sous contrôle
              </div>
              <p className="mt-1.5 text-xs leading-4 text-text-muted">Sources et coûts affichés lorsqu’ils sont disponibles ; confirmation sur les actions externes raccordées.</p>
            </div>
          </nav>

          <div id="capability-results-panel" role="tabpanel" aria-labelledby={`capability-group-${selectedGroup}`} className="flex min-w-0 flex-1 flex-col">
            <div className="border-b border-border px-4 py-3 sm:px-5 sm:py-4">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
                <input
                  data-dialog-autofocus
                  type="search"
                  aria-label="Rechercher une capacité"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Chercher une capacité, un résultat ou un outil…"
                  className="w-full rounded-[11px] border border-border bg-surface-2 py-2.5 pl-9 pr-3 text-sm text-text outline-none focus:border-[#22D3EE] focus:bg-surface"
                />
              </div>
              {!query && (
                <div className="mt-3 flex items-start gap-3">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[9px]" style={{ backgroundColor: activeGroup.tint, color: activeGroup.color }}>
                    <ActiveGroupIcon className="h-4 w-4" />
                  </span>
                  <div>
                    <div className="text-sm font-semibold text-text">{activeGroup.title}</div>
                    <div className="mt-0.5 text-xs text-text-muted">{activeGroup.description}</div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto bg-bg p-3 sm:p-5">
              <div className="sr-only" role="status" aria-live="polite">{visibleCapabilities.length} capacité{visibleCapabilities.length > 1 ? 's' : ''} affichée{visibleCapabilities.length > 1 ? 's' : ''}</div>
              {visibleCapabilities.length === 0 ? (
                <div className="grid h-full place-items-center text-center">
                  <div>
                    <Search className="mx-auto h-7 w-7 text-text-muted" />
                    <div className="mt-3 text-sm font-semibold text-text">Aucune capacité trouvée</div>
                    <div className="mt-1 text-xs text-text-muted">Essaie avec le résultat souhaité, par exemple « devis » ou « analyser ».</div>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                  {visibleCapabilities.map((capability) => {
                    const Icon = capability.icon;
                    const group = capabilityGroups.find((item) => item.id === capability.group) ?? activeGroup;
                    return (
                      <button
                        key={capability.id}
                        type="button"
                        onClick={() => onChoose(capability)}
                        className="group rounded-[14px] border border-border bg-surface p-4 text-left shadow-[0_8px_24px_-22px_rgba(16,28,54,0.55)] hover:-translate-y-0.5 hover:border-[#B8C5D8] hover:shadow-[0_14px_30px_-20px_rgba(16,28,54,0.35)]"
                      >
                        <div className="flex items-start gap-3">
                          {capability.id === 'decision-board' ? (
                            <CharacterPortrait index={1} className="h-9 w-9 rounded-[10px] border border-white shadow-sm" />
                          ) : capability.id === 'agents' ? (
                            <CharacterPortrait index={6} className="h-9 w-9 rounded-[10px] border border-white shadow-sm" />
                          ) : (
                            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px]" style={{ backgroundColor: group.tint, color: group.color }}>
                              <Icon className="h-[18px] w-[18px]" />
                            </span>
                          )}
                          <span className="min-w-0 flex-1">
                            <span className="flex items-center justify-between gap-3">
                              <span className="text-sm font-semibold text-text">{capability.title}</span>
                              <ChevronRight className="h-4 w-4 shrink-0 text-text-muted group-hover:text-text" />
                            </span>
                            <span className="mt-1 block text-xs leading-5 text-text-muted">{capability.description}</span>
                          </span>
                        </div>
                        <FeaturePills features={capability.features} />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <footer className="flex flex-wrap items-center justify-between gap-1 border-t border-border bg-surface px-4 py-2 text-xs text-text-muted sm:px-5 sm:py-3">
              <span>Une capacité ouvre le parcours réel correspondant ou prépare une demande à poursuivre dans le chat.</span>
              <span className="font-semibold text-text-muted">Langage naturel · {/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘K' : 'Ctrl+K'} · Capacités</span>
            </footer>
          </div>
        </div>
      </motion.section>
    </motion.div>
  );
}

function TrustRow({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
  return (
    <div className="flex items-start gap-3 rounded-[10px] px-2 py-2.5 hover:bg-surface-2">
      <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-[8px] bg-accent-tint text-accent">{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="block text-xs font-semibold text-text">{title}</span>
        <span className="mt-0.5 block text-xs leading-4 text-text-muted">{value}</span>
      </span>
    </div>
  );
}

export function TrustCenter({
  onClose,
  onOpenPrivacy,
  onOpenAdvanced,
}: {
  onClose: () => void;
  onOpenPrivacy: () => void;
  onOpenAdvanced: () => void;
}) {
  const dialogRef = useRef<HTMLElement>(null);
  const isPresent = useIsPresent();
  useDialogFocusTrap(dialogRef, { active: isPresent, onEscape: onClose, isolateBackground: true });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[65]"
      onClick={onClose}
    >
      <motion.section
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Centre de confiance"
        tabIndex={-1}
        initial={{ y: -8, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -8, opacity: 0 }}
        onClick={(event) => event.stopPropagation()}
        className="absolute right-4 top-[62px] w-[360px] overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_24px_70px_rgba(16,28,54,0.22)]"
      >
        <div className="flex items-start gap-3 border-b border-border bg-accent-tint px-4 py-4">
          <span className="grid h-9 w-9 place-items-center rounded-[10px] border border-accent-cyan/30 bg-surface text-accent">
            <ShieldCheck className="h-[18px] w-[18px]" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-semibold text-text">Centre de confiance</div>
            <div className="mt-0.5 text-xs leading-4 text-text-muted">Thérèse explique ce qu’elle utilise avant d’agir.</div>
          </div>
          <button type="button" data-dialog-autofocus onClick={onClose} aria-label="Fermer le centre de confiance" className="grid h-7 w-7 place-items-center rounded-[8px] text-text-muted hover:bg-surface">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="p-2">
          <TrustRow icon={<Database className="h-3.5 w-3.5" />} title="Données" value="Données métier conservées localement ; secrets protégés par le trousseau système." />
          <TrustRow icon={<SlidersHorizontal className="h-3.5 w-3.5" />} title="Modèles" value="Provider et modèle configurés dans les réglages, avec option locale via Ollama." />
          <TrustRow icon={<Globe className="h-3.5 w-3.5" />} title="Traitement externe" value="Les parcours raccordés indiquent leur destination et demandent une confirmation avant l’effet externe." />
          <TrustRow icon={<Gauge className="h-3.5 w-3.5" />} title="Coûts et limites" value="Seules les consommations réellement mesurées sont présentées comme telles." />
          <TrustRow icon={<ShieldCheck className="h-3.5 w-3.5" />} title="RGPD" value="Export global et droits par contact accessibles depuis Confidentialité et le CRM." />
        </div>
        <div className="grid grid-cols-2 gap-2 border-t border-border bg-surface-2 p-3">
          <button type="button" onClick={onOpenPrivacy} className="rounded-[9px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text hover:border-border">Confidentialité</button>
          <button type="button" onClick={onOpenAdvanced} className="rounded-[9px] border border-text bg-text px-3 py-2 text-xs font-semibold text-white">Réglages avancés</button>
        </div>
      </motion.section>
    </motion.div>
  );
}
