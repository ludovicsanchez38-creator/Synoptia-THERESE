import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  ChevronRight,
  ListTodo,
  Loader2,
  Mail,
  Receipt,
  RefreshCw,
  Sparkles,
  Users,
} from 'lucide-react';
import type { TodayDashboard } from '../../services/api/dashboard';
import type { AppView } from '../../stores/navigationStore';
import { buildTodayAttentionItems, todayBriefTitle, type AttentionKind } from './prototypeReadModels';
import type { ReadResource } from './usePrototypeReadData';

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
}: {
  resource: ReadResource<TodayDashboard>;
  onRetry: () => void;
  onOpenView: (view: AppView) => void;
}) {
  const items = resource.status === 'ready' ? buildTodayAttentionItems(resource.data) : [];
  const visibleItems = items.slice(0, 6);

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
            <h2 id="today-dashboard-title" className="text-sm font-semibold text-text">{todayBriefTitle(items.length)}</h2>
            <div className="text-xs text-text-muted">
              {resource.status === 'ready'
                ? `${items.length} élément${items.length > 1 ? 's' : ''} issu${items.length > 1 ? 's' : ''} de tes données`
                : 'Lecture des sources locales'}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onOpenView('calendar')}
          className="rounded-[8px] border border-border px-2.5 py-1.5 text-xs font-semibold text-text hover:bg-surface-2"
        >
          Vue complète
        </button>
      </div>

      {resource.status === 'loading' ? (
        <StateShell>
          <div className="flex items-center gap-2 text-sm text-text-muted" role="status">
            <Loader2 className="h-4 w-4 animate-spin text-accent" />
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
                className="inline-flex items-center gap-1.5 rounded-[9px] border border-text bg-text px-3 py-2 text-xs font-semibold text-white"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Réessayer
              </button>
              <button
                type="button"
                onClick={() => onOpenView('home')}
                className="rounded-[9px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text"
              >
                Ouvrir l’accueil
              </button>
            </div>
          </div>
        </StateShell>
      ) : items.length === 0 ? (
        <StateShell>
          <div className="text-center" data-testid="today-dashboard-empty">
            <CheckCircle2 className="mx-auto h-6 w-6 text-success" />
            <p className="mt-2 text-sm font-semibold text-text">Rien d’urgent pour le moment</p>
            <p className="mt-1 text-xs text-text-muted">Aucune relance, échéance ou rencontre à enjeu n’est remontée.</p>
          </div>
        </StateShell>
      ) : (
        <div className="divide-y divide-border">
          {visibleItems.map((item) => {
            const Icon = attentionIcons[item.kind];
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onOpenView(item.targetView)}
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
              onClick={() => onOpenView('home')}
              className="w-full px-4 py-3 text-center text-xs font-semibold text-accent hover:bg-surface-2"
            >
              Voir les {items.length - visibleItems.length} autres éléments
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
