import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { useStatusStore } from '../../stores/statusStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { announceToScreenReader } from '../../lib/accessibility';
import { cn } from '../../lib/utils';
import { Z_LAYER } from '../../styles/z-layers';

export function Notifications() {
  const { notifications, dismissNotification } = useStatusStore();
  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);
  const prevCountRef = useRef(notifications.length);

  // Annoncer les nouvelles notifications aux lecteurs d'ecran
  useEffect(() => {
    if (notifications.length > prevCountRef.current) {
      const latest = notifications[notifications.length - 1];
      if (latest) {
        const text = latest.message
          ? `${latest.title} : ${latest.message}`
          : latest.title;
        announceToScreenReader(text, { assertive: latest.type === 'error' });
      }
    }
    prevCountRef.current = notifications.length;
  }, [notifications]);

  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const colors = {
    success: 'border-success bg-success/10',
    error: 'border-error bg-error/10',
    warning: 'border-warning bg-warning/10',
    info: 'border-info bg-info/10',
  };

  const iconColors = {
    success: 'text-success',
    error: 'text-error',
    warning: 'text-warning',
    info: 'text-info',
  };

  return (
    <div
      className={`fixed bottom-4 right-4 ${Z_LAYER.TOAST} flex flex-col gap-2 max-w-sm`}
      // B-308 : une modale isole ses frères DOM avec `inert`. Les toasts sont
      // rendus au niveau de la coque et doivent rester fermables au-dessus de
      // cette modale ; le focus trap reconnaît explicitement cet attribut.
      data-dialog-allow
      // B-280 : ce conteneur n'est PAS une région live. Il l'était (role=status
      // + aria-live=polite) en plus de l'annonce explicite de l'effet ci-dessus,
      // et chaque notification partait donc deux fois au lecteur d'écran. Des
      // deux mécanismes, `announceToScreenReader` est le seul qui sait passer en
      // `assertive` sur une erreur : c'est celui qu'on garde. Le rôle `region`
      // conserve le repère de navigation et le nom du groupe.
      role="region"
      aria-label="Notifications"
    >
      <AnimatePresence>
        {notifications.map((notification) => {
          const Icon = icons[notification.type];

          return (
            <motion.div
              key={notification.id}
              initial={reduceMotion ? false : { opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={reduceMotion ? { opacity: 0 } : { opacity: 0, x: 50, scale: 0.9 }}
              transition={{ duration: reduceMotion ? 0 : 0.2 }}
              className={cn(
                'flex items-start gap-3 p-4 rounded-md border shadow-lg backdrop-blur-sm',
                colors[notification.type]
              )}
            >
              <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', iconColors[notification.type])} />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-text break-words">{notification.title}</p>
                {notification.message && (
                  // BUG-134 : token primaire (le muted rendait le message
                  // explicatif à peine lisible sur le fond translucide) +
                  // break-words pour les chemins/URLs sans espace.
                  <p className="text-sm text-text mt-1 break-words">{notification.message}</p>
                )}
              </div>
              <button
                onClick={() => dismissNotification(notification.id)}
                className="p-1 hover:bg-surface rounded-sm transition-colors"
                // B-285 : sans ce nom, le bouton n'avait que le <svg> de lucide
                // pour contenu et s'annonçait « bouton », rien de plus.
                aria-label={`Fermer la notification : ${notification.title}`}
              >
                <X className="w-4 h-4 text-text-muted" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
