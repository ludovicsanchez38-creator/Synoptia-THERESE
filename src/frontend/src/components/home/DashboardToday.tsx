/**
 * THÉRÈSE v2 - DashboardToday (US-005) — Refonte DA « Équilibre / Signature »
 *
 * Tableau de bord "Ma journée" : topbar (salutation + statut), rangée de 4 KPIs,
 * panneaux Agenda du jour + « Thérèse vous suggère », barre de saisie.
 * Theme-aware (clair Équilibre par défaut, sombre Signature). Données réelles.
 */

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar,
  AlarmClock,
  Receipt,
  Users,
  ArrowRight,
  MessageSquare,
  Sparkles,
  ShieldCheck,
  Search,
  Send,
  Cpu,
  AlertCircle,
  FileText,
} from 'lucide-react';
import {
  fetchTodayDashboard,
  type TodayDashboard,
  type DashboardEvent,
  type DashboardInvoice,
  type DashboardProspect,
} from '../../services/api/dashboard';
import { openPanelWindow } from '../../services/windowManager';
import { useReducedMotion } from '../../stores/accessibilityStore';

interface DashboardTodayProps {
  onDismiss: () => void;
}

// ============================================================
// Sous-composants
// ============================================================

function Kpi({
  k,
  icon: Icon,
  num,
  label,
  sub,
  onClick,
}: {
  k: 1 | 2 | 3 | 4;
  icon: React.ElementType;
  num: string | number;
  label: string;
  sub: string;
  onClick: () => void;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.button
      type="button"
      onClick={onClick}
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={reduced ? { duration: 0 } : { duration: 0.3, delay: k * 0.04 }}
      className="text-left bg-surface border border-border rounded-xl p-[18px] shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)] transition-shadow"
    >
      <div
        className="w-[42px] h-[42px] rounded-[10px] grid place-items-center mb-4"
        style={{ background: `var(--k${k}bg)`, color: `var(--k${k})` }}
      >
        <Icon className="w-[21px] h-[21px]" />
      </div>
      <div className="text-[30px] font-extrabold tracking-tight leading-none text-text">{num}</div>
      <div className="text-[13.5px] text-text-muted mt-1.5 font-medium">{label}</div>
      <div className="text-xs mt-2 font-semibold" style={{ color: `var(--k${k})` }}>{sub}</div>
    </motion.button>
  );
}

function AgendaRow({ event, k }: { event: DashboardEvent; k: 1 | 2 | 3 | 4 }) {
  const time = event.all_day
    ? 'Jour.'
    : event.start_datetime
      ? new Date(event.start_datetime).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      : '--:--';
  return (
    <div className="flex items-center gap-3.5 p-3 rounded-[10px] bg-surface-2 border border-border">
      <span className="text-[13px] font-bold tabular-nums min-w-[46px] text-text">{time}</span>
      <span className="w-[3px] self-stretch rounded-[3px]" style={{ background: `var(--k${k})` }} />
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-text truncate">{event.summary}</span>
        {event.location && <span className="block text-xs text-text-muted truncate">{event.location}</span>}
      </span>
    </div>
  );
}

function Suggestion({
  icon: Icon,
  title,
  meta,
  warn,
  onClick,
}: {
  icon: React.ElementType;
  title: string;
  meta: string;
  warn?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left flex items-start gap-3 p-3 rounded-[10px] border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] transition-colors"
    >
      <span
        className="w-[30px] h-[30px] rounded-lg grid place-items-center shrink-0"
        style={warn ? { background: 'var(--k3bg)', color: 'var(--k3)' } : { background: 'var(--color-accent-tint)', color: 'var(--color-accent)' }}
      >
        <Icon className="w-4 h-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[13px] font-semibold text-text leading-snug">{title}</span>
        <span className="block text-[11.5px] text-text-muted mt-0.5">{meta}</span>
      </span>
      <ArrowRight className="w-4 h-4 text-text-muted self-center shrink-0" />
    </button>
  );
}

// ============================================================
// Composant principal
// ============================================================

export function DashboardToday({ onDismiss }: DashboardTodayProps) {
  const [data, setData] = useState<TodayDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTodayDashboard()
      .then(setData)
      .catch((err) => {
        console.warn('[Dashboard] Erreur chargement:', err);
        setError('Impossible de charger le tableau de bord');
      })
      .finally(() => setLoading(false));
  }, []);

  const handleOpenCalendar = useCallback(() => openPanelWindow('calendar'), []);
  const handleOpenTasks = useCallback(() => openPanelWindow('tasks'), []);
  const handleOpenInvoices = useCallback(() => openPanelWindow('invoices'), []);
  const handleOpenCRM = useCallback(() => openPanelWindow('crm'), []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent/30 border-t-accent rounded-full animate-spin mx-auto" />
          <p className="text-text-muted text-sm mt-3">Chargement de votre journée...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-sm">
          <p className="text-text-muted text-sm">{error || 'Erreur inconnue'}</p>
          <button
            onClick={onDismiss}
            className="mt-4 px-4 py-2 bg-accent-tint text-accent rounded-xl hover:brightness-105 transition text-sm"
          >
            Passer au chat
          </button>
        </div>
      </div>
    );
  }

  const today = new Date();
  const greeting = today.getHours() < 12 ? 'Bonjour' : today.getHours() < 18 ? 'Bon après-midi' : 'Bonsoir';
  const dateStr = today.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

  const overdueTotal = data.overdue_invoices.reduce((s, i) => s + (i.total_ttc || 0), 0);

  // « Thérèse vous suggère » : dérivé des données réelles (max 3)
  const suggestions: { icon: React.ElementType; title: string; meta: string; warn?: boolean; onClick: () => void }[] = [];
  const od = data.overdue_invoices[0] as DashboardInvoice | undefined;
  if (od) {
    suggestions.push({
      icon: AlertCircle,
      warn: true,
      title: `Relancer la facture ${od.invoice_number}`,
      meta: `${(od.total_ttc || 0).toLocaleString('fr-FR')} € en attente`,
      onClick: handleOpenInvoices,
    });
  }
  const ev = data.events[0] as DashboardEvent | undefined;
  if (ev) {
    suggestions.push({
      icon: FileText,
      title: `Préparer : ${ev.summary}`,
      meta: ev.location || 'Rendez-vous du jour',
      onClick: handleOpenCalendar,
    });
  }
  const pr = data.stale_prospects[0] as DashboardProspect | undefined;
  if (pr) {
    suggestions.push({
      icon: Sparkles,
      title: `Relancer ${pr.name}`,
      meta: pr.company || 'Prospect à recontacter',
      onClick: handleOpenCRM,
    });
  }

  return (
    <div className="flex-1 min-w-0 overflow-y-auto px-7 py-6">
      <div className="flex flex-col gap-[22px] max-w-[1180px] mx-auto">
        {/* Topbar */}
        <div className="flex items-start gap-4">
          <div>
            <h1 className="text-[26px] font-extrabold tracking-tight leading-tight text-text">
              {greeting} <span className="text-accent">!</span>
            </h1>
            <p className="text-sm text-text-muted mt-1.5 first-letter:capitalize">
              Voici votre journée — {dateStr}.
            </p>
          </div>
          <div className="ml-auto flex flex-col items-end gap-3">
            <div className="hidden md:flex items-center gap-2.5 w-[270px] h-10 px-3.5 rounded-full bg-surface border border-border text-text-muted text-[13px]">
              <Search className="w-4 h-4" />
              <span className="truncate">Rechercher une conversation, un contact…</span>
            </div>
            <div className="flex gap-2">
              <span className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-full text-[12.5px] font-medium bg-surface border border-border text-text">
                <span className="w-[7px] h-[7px] rounded-full" style={{ background: 'var(--color-success)' }} />
                En ligne
              </span>
              <span className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-full text-[12.5px] font-medium bg-surface border text-accent" style={{ borderColor: 'color-mix(in srgb, var(--color-accent) 45%, transparent)' }}>
                <ShieldCheck className="w-3.5 h-3.5" />
                Données locales
              </span>
            </div>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Kpi k={1} icon={Calendar} num={data.summary.events_count} label="Rendez-vous" sub="Aujourd'hui" onClick={handleOpenCalendar} />
          <Kpi k={2} icon={AlarmClock} num={data.summary.tasks_count} label="Tâches urgentes" sub="À traiter" onClick={handleOpenTasks} />
          <Kpi k={3} icon={Receipt} num={overdueTotal > 0 ? `${overdueTotal.toLocaleString('fr-FR')} €` : '0 €'} label="Factures impayées" sub={`${data.summary.invoices_count} en attente`} onClick={handleOpenInvoices} />
          <Kpi k={4} icon={Users} num={data.summary.prospects_count} label="Prospects actifs" sub="Pipeline" onClick={handleOpenCRM} />
        </div>

        {/* Panneaux */}
        <div className="grid grid-cols-1 lg:grid-cols-[1.25fr_1fr] gap-4">
          {/* Agenda */}
          <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)] flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-text">Agenda du jour</h2>
              <button onClick={handleOpenCalendar} className="text-[12.5px] text-accent font-semibold hover:underline">Tout voir</button>
            </div>
            {data.events.length === 0 ? (
              <p className="text-sm text-text-muted py-2">Aucun rendez-vous aujourd'hui.</p>
            ) : (
              <div className="flex flex-col gap-3">
                {data.events.slice(0, 4).map((e, i) => (
                  <AgendaRow key={i} event={e} k={((i % 4) + 1) as 1 | 2 | 3 | 4} />
                ))}
              </div>
            )}
          </section>

          {/* Suggestions */}
          <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)] flex flex-col">
            <h2 className="text-base font-bold text-text mb-4">Thérèse vous suggère</h2>
            {suggestions.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center flex-1 py-6">
                <Sparkles className="w-8 h-8 mb-2" style={{ color: 'var(--color-success)' }} />
                <p className="text-sm font-semibold text-text">Tout est sous contrôle.</p>
                <p className="text-xs text-text-muted mt-1">Aucune relance ni urgence en attente.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-2.5">
                {suggestions.map((s, i) => (
                  <Suggestion key={i} {...s} />
                ))}
              </div>
            )}
          </section>
        </div>

        {/* Barre de saisie */}
        <button
          onClick={onDismiss}
          className="flex items-center gap-3 py-3 px-[18px] rounded-full bg-surface border border-border shadow-[var(--shadow-sm)] text-left hover:border-[color-mix(in_srgb,var(--color-ring)_40%,var(--color-border))] transition-colors"
        >
          <MessageSquare className="w-4 h-4 text-accent" />
          <span className="flex-1 text-sm text-text-muted">Demandez à Thérèse…</span>
          <span className="text-xs text-text-muted hidden sm:flex items-center gap-1.5"><Cpu className="w-3.5 h-3.5" /> Claude Opus</span>
          <span className="w-9 h-9 rounded-full grid place-items-center bg-accent-fill text-accent-ink shadow-[var(--glow)]">
            <Send className="w-4 h-4" />
          </span>
        </button>
      </div>
    </div>
  );
}
