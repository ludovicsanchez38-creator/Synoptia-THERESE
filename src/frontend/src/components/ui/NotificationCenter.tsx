/**
 * THERESE v2 - NotificationCenter (US-004)
 *
 * Centre de notifications push in-app.
 * Icone cloche dans le header avec badge compteur + dropdown panel.
 */

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bell,
  CheckCheck,
  Info,
  AlertTriangle,
  Zap,
  Clock,
  ExternalLink,
  X,
} from "lucide-react";
import { useNotificationStore } from "../../stores/notificationStore";
import { useAccessibilityStore } from "../../stores/accessibilityStore";
import { announceToScreenReader } from "../../lib/accessibility";
import { cn } from "../../lib/utils";
import type { AppNotification } from "../../services/api/notifications";

// Icone par type de notification
function NotificationIcon({ type }: { type: AppNotification["type"] }) {
  switch (type) {
    case "warning":
      return <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0" />;
    case "action":
      return <Zap className="w-4 h-4 text-accent-magenta flex-shrink-0" />;
    case "reminder":
      return <Clock className="w-4 h-4 text-accent-cyan flex-shrink-0" />;
    default:
      return <Info className="w-4 h-4 text-info flex-shrink-0" />;
  }
}

// Temps relatif en francais
function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffH = Math.floor(diffMin / 60);
  const diffD = Math.floor(diffH / 24);

  if (diffMin < 1) return "a l'instant";
  if (diffMin < 60) return `il y a ${diffMin} min`;
  if (diffH < 24) return `il y a ${diffH}h`;
  if (diffD < 7) return `il y a ${diffD}j`;
  return date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

// Badge source
function SourceBadge({ source }: { source: string }) {
  const colors: Record<string, string> = {
    crm: "bg-purple-500/20 text-purple-400",
    invoice: "bg-amber-500/20 text-amber-400",
    calendar: "bg-cyan-500/20 text-cyan-400",
    task: "bg-blue-500/20 text-blue-400",
    agent: "bg-green-500/20 text-green-400",
    system: "bg-gray-500/20 text-gray-400",
  };
  const labels: Record<string, string> = {
    crm: "CRM",
    invoice: "Facture",
    calendar: "Agenda",
    task: "Tache",
    agent: "Agent",
    system: "Systeme",
  };
  return (
    <span
      className={cn(
        "text-[10px] font-medium px-1.5 py-0.5 rounded-full",
        colors[source] || colors.system
      )}
    >
      {labels[source] || source}
    </span>
  );
}

// Element de notification individuel
function NotificationItem({ notification }: { notification: AppNotification }) {
  const markAsRead = useNotificationStore((s) => s.markAsRead);
  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);

  const handleClick = () => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    // Annoncer le contenu au lecteur d'ecran
    announceToScreenReader(`${notification.title} : ${notification.message || ''}`);
  };

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
      transition={{ duration: reduceMotion ? 0 : 0.15 }}
      onClick={handleClick}
      className={cn(
        "flex gap-3 p-3 rounded-lg cursor-pointer transition-colors border",
        notification.is_read
          ? "bg-surface/30 border-transparent hover:bg-surface/50"
          : "bg-surface-elevated/60 border-border/40 hover:bg-surface-elevated/80"
      )}
    >
      {/* Icone */}
      <div className="mt-0.5">
        <NotificationIcon type={notification.type} />
      </div>

      {/* Contenu */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "text-sm font-medium truncate",
              notification.is_read ? "text-text-muted" : "text-text"
            )}
          >
            {notification.title}
          </span>
          <SourceBadge source={notification.source} />
        </div>
        <p className="text-xs text-text-muted mt-0.5 line-clamp-2">
          {notification.message}
        </p>
        <div className="flex items-center gap-2 mt-1.5">
          <span className="text-[10px] text-text-muted/60">
            {timeAgo(notification.created_at)}
          </span>
          {notification.action_url && notification.action_label && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                // Navigation via action_url possible ici
                if (!notification.is_read) markAsRead(notification.id);
              }}
              className="flex items-center gap-1 text-[10px] font-medium text-accent-cyan hover:text-accent-cyan/80 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              {notification.action_label}
            </button>
          )}
        </div>
      </div>

      {/* Indicateur non lu */}
      {!notification.is_read && (
        <div className="mt-1.5">
          <div className="w-2 h-2 rounded-full bg-accent-cyan shadow-[0_0_6px_rgba(34,211,238,0.5)]" />
        </div>
      )}
    </motion.div>
  );
}

// Composant principal
export function NotificationCenter() {
  const {
    notifications,
    unreadCount,
    isOpen,
    isLoading,
    toggle,
    close,
    markAllRead,
    startPolling,
    stopPolling,
  } = useNotificationStore();

  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);
  const panelRef = useRef<HTMLDivElement>(null);

  // Demarrer le polling au montage
  useEffect(() => {
    startPolling();
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  // Fermer au clic exterieur
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        close();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen, close]);

  return (
    <div className="relative" ref={panelRef}>
      {/* Bouton cloche */}
      <button
        onClick={toggle}
        className="relative w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-elevated/80 transition-colors"
        title="Notifications"
      >
        <Bell className="w-4.5 h-4.5 text-text-muted" />
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center text-[10px] font-bold text-white bg-red-500 rounded-full px-1 shadow-[0_0_8px_rgba(239,68,68,0.4)]"
            aria-live="polite"
            aria-label={`${unreadCount} notification${unreadCount > 1 ? 's' : ''} non lue${unreadCount > 1 ? 's' : ''}`}
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: reduceMotion ? 0 : 0.15 }}
            className="absolute right-0 top-full mt-2 w-[380px] max-h-[480px] bg-bg/95 backdrop-blur-xl border border-border/60 rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col"
            aria-live="polite"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border/40">
              <h3 className="text-sm font-semibold text-text">Notifications</h3>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="flex items-center gap-1 text-xs text-accent-cyan hover:text-accent-cyan/80 transition-colors"
                    title="Tout marquer comme lu"
                  >
                    <CheckCheck className="w-3.5 h-3.5" />
                    Tout lu
                  </button>
                )}
                <button
                  onClick={close}
                  className="p-1 hover:bg-surface-elevated rounded transition-colors"
                >
                  <X className="w-3.5 h-3.5 text-text-muted" />
                </button>
              </div>
            </div>

            {/* Liste */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {isLoading && notifications.length === 0 ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-5 h-5 border-2 border-accent-cyan/30 border-t-accent-cyan rounded-full animate-spin" />
                </div>
              ) : notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-text-muted">
                  <Bell className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">Aucune notification</p>
                  <p className="text-xs mt-1 opacity-60">
                    Tout est sous controle !
                  </p>
                </div>
              ) : (
                <AnimatePresence>
                  {notifications.map((notif) => (
                    <NotificationItem key={notif.id} notification={notif} />
                  ))}
                </AnimatePresence>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
