/**
 * THÉRÈSE v2 - TodayPanels : Agenda du jour | À traiter (factures/prospects/tâches).
 * Reçoit les données ; ne fetch pas (séparation des responsabilités).
 */
import { Calendar, AlertCircle, Users, AlarmClock } from 'lucide-react';
import type { TodayDashboard } from '../../services/api/dashboard';
import { useNavigationStore } from '../../stores/navigationStore';

function go(view: 'calendar' | 'invoices' | 'crm' | 'tasks') {
  useNavigationStore.getState().setView(view);
}

export function TodayPanels({ data }: { data: TodayDashboard }) {
  const events = data.events.slice(0, 4);
  const overdue = data.overdue_invoices.slice(0, 3);
  const stale = data.stale_prospects.slice(0, 3);
  const tasks = data.urgent_tasks.slice(0, 3);
  const hasActionables = overdue.length + stale.length + tasks.length > 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Agenda */}
      <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-text">Agenda du jour</h2>
          <button onClick={() => go('calendar')} className="text-[12.5px] text-accent font-semibold hover:underline">Tout voir</button>
        </div>
        {events.length === 0 ? (
          <p className="text-sm text-text-muted py-2">Rien de prévu aujourd'hui.</p>
        ) : (
          <ul className="flex flex-col gap-2.5">
            {events.map((e, i) => (
              <li key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-surface-2 border border-border">
                <Calendar className="w-4 h-4 text-accent shrink-0" />
                <span className="text-sm text-text truncate flex-1">{e.summary}</span>
                <span className="text-xs text-text-muted tabular-nums">
                  {e.all_day ? 'Jour.' : e.start_datetime ? new Date(e.start_datetime).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* À traiter */}
      <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)]">
        <h2 className="text-base font-bold text-text mb-4">À traiter</h2>
        {!hasActionables ? (
          <p className="text-sm text-text-muted py-2">Aucune relance en attente.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {overdue.map((inv) => (
              <li key={inv.id}>
                <button onClick={() => go('invoices')} className="w-full flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] text-left">
                  <AlertCircle className="w-4 h-4 text-warning shrink-0" />
                  <span className="text-[13px] text-text truncate flex-1">Relancer {inv.invoice_number}</span>
                  <span className="text-xs text-text-muted">{(inv.total_ttc || 0).toLocaleString('fr-FR')} €</span>
                </button>
              </li>
            ))}
            {stale.map((p) => (
              <li key={p.id}>
                <button onClick={() => go('crm')} className="w-full flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] text-left">
                  <Users className="w-4 h-4 text-accent shrink-0" />
                  <span className="text-[13px] text-text truncate flex-1">Relancer {p.name}</span>
                  <span className="text-xs text-text-muted truncate">{p.company || ''}</span>
                </button>
              </li>
            ))}
            {tasks.map((t) => (
              <li key={t.id}>
                <button onClick={() => go('tasks')} className="w-full flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] text-left">
                  <AlarmClock className="w-4 h-4 text-accent shrink-0" />
                  <span className="text-[13px] text-text truncate flex-1">{t.title}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
