/**
 * THÉRÈSE v2 - DashboardToday (US-005)
 *
 * Tableau de bord "Ma journée" affiché à l'ouverture de l'application.
 * 4 sections en cards glass : RDV, Tâches urgentes, Factures impayées, Prospects.
 * Design : fond sombre, cards glass, accent couleurs par type.
 */

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar,
  CheckSquare,
  FileText,
  Users,
  ArrowRight,
  MessageSquare,
  Sparkles,
  Clock,
  AlertTriangle,
  MapPin,
} from 'lucide-react';
import {
  fetchTodayDashboard,
  type TodayDashboard,
  type DashboardEvent,
  type DashboardTask,
  type DashboardInvoice,
  type DashboardProspect,
} from '../../services/api/dashboard';
import { openPanelWindow } from '../../services/windowManager';

// ============================================================
// Types
// ============================================================

interface DashboardTodayProps {
  onDismiss: () => void;
}

// ============================================================
// Sub-components
// ============================================================

function DashboardCard({
  title,
  icon: Icon,
  count,
  accentColor,
  items,
  renderItem,
  onViewAll,
  emptyMessage,
}: {
  title: string;
  icon: React.ElementType;
  count: number;
  accentColor: string;
  items: unknown[];
  renderItem: (item: unknown, index: number) => React.ReactNode;
  onViewAll: () => void;
  emptyMessage: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-surface/60 backdrop-blur-xl border border-border/50 rounded-2xl p-5 hover:border-border transition-colors"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${accentColor}15` }}
          >
            <Icon className="w-4.5 h-4.5" style={{ color: accentColor }} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text">{title}</h3>
            <span className="text-xs text-text-muted">
              {count === 0 ? 'Aucun' : count} {count > 1 ? 'éléments' : 'élément'}
            </span>
          </div>
        </div>
        {count > 0 && (
          <span
            className="text-xs font-bold px-2 py-1 rounded-full"
            style={{ backgroundColor: `${accentColor}20`, color: accentColor }}
          >
            {count}
          </span>
        )}
      </div>

      {/* Items */}
      {items.length === 0 ? (
        <p className="text-sm text-text-muted italic py-2">{emptyMessage}</p>
      ) : (
        <div className="space-y-2">
          {items.slice(0, 3).map((item, idx) => (
            <div key={idx} onClick={onViewAll} className="cursor-pointer">
              {renderItem(item, idx)}
            </div>
          ))}
          {items.length > 3 && (
            <button
              onClick={onViewAll}
              className="flex items-center gap-1.5 text-xs text-accent-cyan hover:text-accent-cyan/80 transition-colors mt-2 group"
            >
              <span>Voir les {items.length} éléments</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}

function EventItem({ event }: { event: DashboardEvent }) {
  const time = event.all_day
    ? 'Journée entière'
    : event.start_datetime
      ? new Date(event.start_datetime).toLocaleTimeString('fr-FR', {
          hour: '2-digit',
          minute: '2-digit',
        })
      : '';

  return (
    <div className="flex items-start gap-3 p-2.5 rounded-xl bg-surface-elevated/50 hover:bg-surface-elevated transition-colors">
      <Clock className="w-4 h-4 text-accent-cyan mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-text truncate">{event.summary}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-text-muted">{time}</span>
          {event.location && (
            <span className="text-xs text-text-muted flex items-center gap-0.5">
              <MapPin className="w-3 h-3" />
              {event.location}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function TaskItem({ task }: { task: DashboardTask }) {
  const isOverdue = task.due_date && new Date(task.due_date) < new Date();
  const priorityColors: Record<string, string> = {
    urgent: '#EF4444',
    high: '#F97316',
    medium: '#EAB308',
    low: '#6B7280',
  };

  return (
    <div className="flex items-start gap-3 p-2.5 rounded-xl bg-surface-elevated/50 hover:bg-surface-elevated transition-colors">
      <CheckSquare className="w-4 h-4 mt-0.5 shrink-0" style={{ color: priorityColors[task.priority] || '#6B7280' }} />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-text truncate">{task.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs capitalize" style={{ color: priorityColors[task.priority] || '#6B7280' }}>
            {task.priority}
          </span>
          {isOverdue && (
            <span className="text-xs text-red-400 flex items-center gap-0.5">
              <AlertTriangle className="w-3 h-3" />
              En retard
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function InvoiceItem({ invoice }: { invoice: DashboardInvoice }) {
  return (
    <div className="flex items-start gap-3 p-2.5 rounded-xl bg-surface-elevated/50 hover:bg-surface-elevated transition-colors">
      <FileText className="w-4 h-4 text-accent-magenta mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-text truncate">{invoice.invoice_number}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs font-semibold text-accent-magenta">
            {invoice.total_ttc.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} {invoice.currency === 'EUR' ? '\u20AC' : invoice.currency}
          </span>
          {invoice.due_date && (
            <span className="text-xs text-text-muted">
              échue le {new Date(invoice.due_date).toLocaleDateString('fr-FR')}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function ProspectItem({ prospect }: { prospect: DashboardProspect }) {
  const daysSince = prospect.last_interaction
    ? Math.floor((Date.now() - new Date(prospect.last_interaction).getTime()) / (1000 * 60 * 60 * 24))
    : null;

  return (
    <div className="flex items-start gap-3 p-2.5 rounded-xl bg-surface-elevated/50 hover:bg-surface-elevated transition-colors">
      <Users className="w-4 h-4 text-purple-400 mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-text truncate">{prospect.name}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {prospect.company && <span className="text-xs text-text-muted">{prospect.company}</span>}
          {daysSince !== null && (
            <span className="text-xs text-purple-400">{daysSince}j sans contact</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Main Component
// ============================================================

export function DashboardToday({ onDismiss }: DashboardTodayProps) {
  const [data, setData] = useState<TodayDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const start = performance.now();
    fetchTodayDashboard()
      .then((d) => {
        setData(d);
        const elapsed = Math.round(performance.now() - start);
        console.log(`[Dashboard] Chargé en ${elapsed}ms`);
      })
      .catch((err) => {
        console.warn('[Dashboard] Erreur chargement:', err);
        setError('Impossible de charger le tableau de bord');
      })
      .finally(() => setLoading(false));
  }, []);

  const totalItems = data
    ? data.summary.events_count + data.summary.tasks_count + data.summary.invoices_count + data.summary.prospects_count
    : 0;

  const allClear = data !== null && totalItems === 0;

  const handleOpenCalendar = useCallback(() => openPanelWindow('calendar'), []);
  const handleOpenTasks = useCallback(() => openPanelWindow('tasks'), []);
  const handleOpenInvoices = useCallback(() => openPanelWindow('invoices'), []);
  const handleOpenCRM = useCallback(() => openPanelWindow('crm'), []);

  // Loading
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent-cyan/30 border-t-accent-cyan rounded-full animate-spin mx-auto" />
          <p className="text-text-muted text-sm mt-3">Chargement de votre journée...</p>
        </div>
      </div>
    );
  }

  // Error fallback
  if (error || !data) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-sm">
          <p className="text-text-muted text-sm">{error || 'Erreur inconnue'}</p>
          <button
            onClick={onDismiss}
            className="mt-4 px-4 py-2 bg-accent-cyan/10 text-accent-cyan rounded-xl hover:bg-accent-cyan/20 transition-colors text-sm"
          >
            Passer au chat
          </button>
        </div>
      </div>
    );
  }

  const today = new Date();
  const greeting =
    today.getHours() < 12
      ? 'Bonjour'
      : today.getHours() < 18
        ? 'Bon après-midi'
        : 'Bonsoir';

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-bold text-text">
            {greeting} !
          </h1>
          <p className="text-text-muted mt-1">
            {today.toLocaleDateString('fr-FR', {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </p>
        </motion.div>

        {/* All clear message */}
        {allClear && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-8 text-center mb-8"
          >
            <Sparkles className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
            <h2 className="text-lg font-semibold text-emerald-300">
              Tout est sous contrôle !
            </h2>
            <p className="text-emerald-400/70 text-sm mt-1">
              Aucun RDV, aucune tâche urgente, aucune facture en retard. Belle journée.
            </p>
          </motion.div>
        )}

        {/* Cards grid */}
        {!allClear && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <DashboardCard
              title="Rendez-vous"
              icon={Calendar}
              count={data.summary.events_count}
              accentColor="#22D3EE"
              items={data.events}
              renderItem={(item, idx) => <EventItem key={idx} event={item as DashboardEvent} />}
              onViewAll={handleOpenCalendar}
              emptyMessage="Aucun rendez-vous aujourd'hui"
            />
            <DashboardCard
              title="Tâches urgentes"
              icon={CheckSquare}
              count={data.summary.tasks_count}
              accentColor="#F97316"
              items={data.urgent_tasks}
              renderItem={(item, idx) => <TaskItem key={idx} task={item as DashboardTask} />}
              onViewAll={handleOpenTasks}
              emptyMessage="Aucune tâche urgente"
            />
            <DashboardCard
              title="Factures impayées"
              icon={FileText}
              count={data.summary.invoices_count}
              accentColor="#E11D8D"
              items={data.overdue_invoices}
              renderItem={(item, idx) => <InvoiceItem key={idx} invoice={item as DashboardInvoice} />}
              onViewAll={handleOpenInvoices}
              emptyMessage="Aucune facture en retard"
            />
            <DashboardCard
              title="Prospects à relancer"
              icon={Users}
              count={data.summary.prospects_count}
              accentColor="#8B5CF6"
              items={data.stale_prospects}
              renderItem={(item, idx) => <ProspectItem key={idx} prospect={item as DashboardProspect} />}
              onViewAll={handleOpenCRM}
              emptyMessage="Aucun prospect à relancer"
            />
          </div>
        )}

        {/* CTA passer au chat */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center"
        >
          <button
            onClick={onDismiss}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-accent-cyan/10 to-accent-magenta/10 border border-border/50 rounded-2xl text-text hover:border-accent-cyan/30 transition-all group"
          >
            <MessageSquare className="w-4 h-4 text-accent-cyan" />
            <span className="text-sm font-medium">Passer au chat</span>
            <ArrowRight className="w-4 h-4 text-text-muted group-hover:translate-x-0.5 transition-transform" />
          </button>
        </motion.div>
      </div>
    </div>
  );
}
