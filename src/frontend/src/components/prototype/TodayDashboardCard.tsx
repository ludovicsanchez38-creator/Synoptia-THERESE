import { useEffect, useState } from 'react';
import {
  libelleDuRepli,
  lireLeReglage,
  motActif,
  motsUtiles,
  oublierLesAutresJours,
  REGLAGE_PAR_DEFAUT,
  ecrireLeReglage,
  seuilDuReglage,
  type ReglageDuBrief,
} from '../../lib/variateurDuBrief';
import { BoutonOuvrirLaVue } from './BoutonOuvrirLaVue';
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  ChevronRight,
  ListTodo,
  Mail,
  Receipt,
  RefreshCw,
  Sparkles,
  Users,
} from 'lucide-react';
import type { SetupStatus, TodayDashboard } from '../../services/api/dashboard';
import type { AppView } from '../../stores/navigationStore';
import { buildTodayAttentionItems, todayBriefTitle, type AttentionKind, type TodayAttentionItem } from './prototypeReadModels';
import type { ReadResource } from './usePrototypeReadData';
import { Spinner } from '../ui/Spinner';
import { SetupChecklist } from '../home/SetupChecklist';

const attentionIcons = {
  event: Calendar,
  task: ListTodo,
  follow_up: Mail,
  invoice: Receipt,
  prospect: Users,
} satisfies Record<AttentionKind, typeof Calendar>;

const attentionColors: Record<AttentionKind, string> = {
  event: 'bg-accent-tint text-accent',
  task: 'bg-[var(--color-warning-tint)] text-warning',
  follow_up: 'bg-[var(--k4bg)] text-[var(--k4)]',
  invoice: 'bg-[var(--k3bg)] text-[var(--k3)]',
  prospect: 'bg-[var(--k4bg)] text-[var(--k4)]',
};

function StateShell({ children }: { children: React.ReactNode }) {
  return <div className="flex min-h-44 items-center justify-center px-5 py-8">{children}</div>;
}

function SourcePill({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs font-semibold text-text-muted">
      {label}
    </span>
  );
}

export function TodayDashboardCard({
  resource,
  onRetry,
  onOpenView,
  onOpenItem,
  setup = null,
  onSetupEmail,
}: {
  resource: ReadResource<TodayDashboard>;
  onRetry: () => void;
  onOpenView: (view: AppView) => void;
  /**
   * Ouvrir l'objet que l'item désigne (entrée 8 du plan du 28/08).
   *
   * « Tu peux agir ici, sans chercher le bon module » s'affiche trois lignes
   * plus haut, et le clic ouvrait le module. Sur « Relancer Dupont », il
   * fallait retrouver Dupont dans la boîte entière.
   *
   * Facultatif, et personne ne le fournit encore : la première tentative
   * ouvrait bien une surface pour chaque type, mais l'OBJET n'y arrivait que
   * pour la facture. Un brief à moitié précis serait pire que l'actuel,
   * uniformément grossier. Le point d'accroche reste, la reprise le remplira.
   */
  onOpenItem?: (item: TodayAttentionItem) => void;
  /** B1 (0.48) : l'état vide dit la vérité - sans compte email, le brief
      ne peut rien préparer. La coque charge le SetupStatus et le passe. */
  setup?: SetupStatus | null;
  onSetupEmail?: () => void;
}) {
  const items = resource.status === 'ready' ? buildTodayAttentionItems(resource.data) : [];
  // Entrée 11b : le brief montre six éléments, le reste se déroule ici plutôt
  // que sur un autre écran. Depuis le 29/08, le seuil est réglable.
  const [toutAfficher, setToutAfficher] = useState(false);
  const jour = resource.status === 'ready' ? resource.data.date : null;
  const [reglage, setReglage] = useState<ReglageDuBrief>(REGLAGE_PAR_DEFAUT);
  const [jourConnu, setJourConnu] = useState<string | null>(null);
  // Le réglage vit et meurt avec la journée civile du backend : dès qu'elle
  // change, on repart du défaut sans attendre un remontage.
  if (jour !== null && jour !== jourConnu) {
    setJourConnu(jour);
    setReglage(lireLeReglage(jour));
    setToutAfficher(false);
  }

  // La purge est un effet de bord : elle n'a rien à faire dans le corps du
  // rendu, que StrictMode rejoue et que React peut abandonner.
  useEffect(() => {
    if (jour !== null) oublierLesAutresJours(jour);
  }, [jour]);

  const motsOfferts = motsUtiles(items.length);
  const motCoche = motActif(reglage, items.length);
  const seuil = seuilDuReglage(reglage);
  const visibleItems = toutAfficher || seuil === null ? items : items.slice(0, seuil);
  const replies = items.slice(visibleItems.length);
  const retardsReplies = replies.filter((item) => item.urgent).length;

  function choisirLeReglage(valeur: ReglageDuBrief) {
    setReglage(valeur);
    // Le réglage l'emporte sur une expansion ponctuelle déjà faite.
    setToutAfficher(false);
    if (jour !== null) ecrireLeReglage(jour, valeur);
  }

  return (
    <section
      aria-labelledby="today-dashboard-title"
      className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]"
      data-testid="today-dashboard-card"
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-[9px] border border-text bg-accent-tint text-accent">
            <Sparkles className="h-4 w-4" />
          </span>
          <div>
            <h2 id="today-dashboard-title" className="text-base font-semibold text-text">
              {resource.status === 'ready' ? todayBriefTitle(items.length) : 'Ta journée'}
            </h2>
            <div className="text-xs text-text-muted">
              {resource.status === 'ready'
                ? `${items.length} élément${items.length > 1 ? 's' : ''} issu${items.length > 1 ? 's' : ''} de tes données`
                : 'Lecture des sources locales'}
            </div>
          </div>
        </div>
        <BoutonOuvrirLaVue vue="calendar" onOuvrir={() => onOpenView('calendar')} />
      </div>

      {/* Le variateur (plan du 29/08). Les trois mots sont écrits : une pastille
          muette, c'est « des petits dessins sans nom, je n'ose pas ». Il
          n'apparaît que lorsqu'il a de quoi replier, pour ne pas offrir une
          commande sans effet. */}
      {resource.status === 'ready' && motsOfferts.length > 1 && (
        <div className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-2">
          <span id="variateur-brief-libelle" className="text-xs text-text-muted">
            Aujourd’hui, montre-moi
          </span>
          <div
            role="radiogroup"
            aria-labelledby="variateur-brief-libelle"
            className="flex items-center gap-1 rounded-[9px] border border-border bg-surface-2 p-0.5"
          >
            {motsOfferts.map(({ valeur, mot }) => (
              <label
                key={valeur}
                /* La radio elle-même est hors écran (`sr-only`) : sans cette
                   règle, le contour de focus se dessinerait sur un pixel
                   invisible et personne ne saurait, au clavier, sur quel mot
                   il se trouve. */
                className={`cursor-pointer rounded-[7px] px-2.5 py-1 text-xs font-medium transition-colors focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent-cyan ${
                  motCoche?.valeur === valeur
                    ? 'bg-surface text-text shadow-[0_1px_2px_rgba(16,28,54,0.12)]'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <input
                  type="radio"
                  name="variateur-brief"
                  className="sr-only"
                  checked={motCoche?.valeur === valeur}
                  onChange={() => choisirLeReglage(valeur)}
                  /* Une radio déjà cochée n'émet pas `change` : sans ce clic,
                     revenir à « l'essentiel » depuis une liste dépliée ne
                     ferait rien, et le mot mentirait. */
                  onClick={() => {
                    if (motCoche?.valeur === valeur) choisirLeReglage(valeur);
                  }}
                />
                {mot}
              </label>
            ))}
          </div>
        </div>
      )}

      {resource.status === 'loading' ? (
        <StateShell>
          <div className="flex items-center gap-2 text-sm text-text-muted" role="status">
            <Spinner taille="bouton" className="text-accent" />
            Je rassemble ta journée…
          </div>
        </StateShell>
      ) : resource.status === 'error' ? (
        <StateShell>
          <div className="max-w-sm text-center" data-testid="today-dashboard-error">
            <AlertCircle className="mx-auto h-5 w-5 text-warning" />
            <p className="mt-2 text-sm font-semibold text-text">Brief indisponible</p>
            <p className="mt-1 text-xs leading-5 text-text-muted">{resource.error}</p>
            <div className="mt-4 flex justify-center gap-2">
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 rounded-[9px] border border-accent-fill bg-accent-fill px-3 py-2 text-xs font-semibold text-accent-ink"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Réessayer
              </button>
            </div>
          </div>
        </StateShell>
      ) : items.length === 0 ? (
        <StateShell>
          {setup !== null && setup.has_email === false ? (
            <div className="text-center" data-testid="today-dashboard-setup-email">
              <Mail className="mx-auto h-6 w-6 text-accent" />
              <p className="mt-2 text-sm font-semibold text-text">Branche tes mails pour que je te prépare la journée</p>
              <p className="mt-1 text-xs text-text-muted">Sans boîte connectée, le brief ne voit ni messages à traiter ni relances.</p>
              <button
                type="button"
                onClick={onSetupEmail}
                /* L'action qui sort de l'état vide : elle mérite mieux que
                   la taille des métadonnées qui l'entourent. */
                className="mt-4 rounded-[9px] bg-accent-fill px-3 py-2 text-sm font-semibold text-accent-ink"
              >
                Brancher mes mails
              </button>
            </div>
          ) : (
            <div className="text-center" data-testid="today-dashboard-empty">
              <CheckCircle2 className="mx-auto h-6 w-6 text-success" />
              <p className="mt-2 text-sm font-semibold text-text">Rien d’urgent pour le moment</p>
              <p className="mt-1 text-xs text-text-muted">Aucune relance, échéance ou rencontre à enjeu n’est remontée.</p>
            </div>
          )}
          {/* Entrée 11 : ce qui reste à brancher se voyait uniquement sur un
              second accueil, joignable par « Voir les autres ». La liste vient
              ici, à l'endroit qui constate le vide qu'elle explique.
              L'étape messagerie est masquée quand le message dédié ci-dessus
              la porte déjà : deux invitations pour le même geste en valent
              zéro. La liste se cache d'elle-même quand tout est branché. */}
          {setup !== null && (
            <div className="mt-4">
              <SetupChecklist
                status={
                  setup.has_email === false ? { ...setup, has_email: true } : setup
                }
              />
            </div>
          )}
        </StateShell>
      ) : (
        <div className="divide-y divide-border">
          {visibleItems.map((item) => {
            const Icon = attentionIcons[item.kind];
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => (onOpenItem ? onOpenItem(item) : onOpenView(item.targetView))}
                className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-surface-2"
              >
                <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-[10px] ${attentionColors[item.kind]}`}>
                  <Icon className="h-[18px] w-[18px]" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-text">{item.title}</span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                      item.urgent ? 'bg-[var(--color-error-tint)] text-error' : 'bg-surface-2 text-text-muted'
                    }`}>
                      {item.badge}
                    </span>
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-text-muted">{item.detail}</span>
                </span>
                <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" />
              </button>
            );
          })}
          {items.length > visibleItems.length && (
            <button
              type="button"
              /* Entrée 11b : ce bouton menait à un second accueil pour lire la
                 suite d'une liste qu'on a déjà sous les yeux. Elle se déroule
                 ici. */
              onClick={() => setToutAfficher(true)}
              className="w-full px-4 py-3 text-center text-xs font-semibold text-accent hover:bg-surface-2"
            >
              {libelleDuRepli(replies.length, retardsReplies)}
            </button>
          )}
        </div>
      )}

      {resource.status === 'ready' && (
        <div className="flex flex-wrap items-center gap-1.5 border-t border-border bg-surface-2 px-4 py-2.5">
          <span className="mr-1 text-xs font-medium text-text-muted">Sources réelles</span>
          {resource.data.events.length > 0 && <SourcePill label="Agenda" />}
          {resource.data.urgent_tasks.length > 0 && <SourcePill label="Tâches" />}
          {resource.data.due_follow_ups.length > 0 && <SourcePill label="Relances" />}
          {resource.data.overdue_invoices.length > 0 && <SourcePill label="Factures" />}
          {resource.data.stale_prospects.length > 0 && <SourcePill label="CRM" />}
        </div>
      )}
    </section>
  );
}
