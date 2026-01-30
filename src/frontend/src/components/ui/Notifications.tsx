import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { useStatusStore } from '../../stores/statusStore';
import { cn } from '../../lib/utils';

export function Notifications() {
  const { notifications, dismissNotification } = useStatusStore();

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
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      <AnimatePresence>
        {notifications.map((notification) => {
          const Icon = icons[notification.type];

          return (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className={cn(
                'flex items-start gap-3 p-4 rounded-xl border shadow-lg backdrop-blur-sm',
                colors[notification.type]
              )}
            >
              <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', iconColors[notification.type])} />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-text">{notification.title}</p>
                {notification.message && (
                  <p className="text-sm text-text-muted mt-1">{notification.message}</p>
                )}
              </div>
              <button
                onClick={() => dismissNotification(notification.id)}
                className="p-1 hover:bg-surface rounded transition-colors"
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
