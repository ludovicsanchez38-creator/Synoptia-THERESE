import { Wifi, WifiOff, Loader } from 'lucide-react';
import { useStatusStore } from '../../stores/statusStore';
import { cn } from '../../lib/utils';

export function ConnectionStatus() {
  const { connectionState, latency } = useStatusStore();

  const stateConfig = {
    connected: {
      icon: Wifi,
      color: 'text-success',
      bgColor: 'bg-success/10',
      label: 'Connecté',
    },
    connecting: {
      icon: Loader,
      color: 'text-warning',
      bgColor: 'bg-warning/10',
      label: 'Connexion...',
    },
    disconnected: {
      icon: WifiOff,
      color: 'text-text-muted',
      bgColor: 'bg-surface-elevated',
      label: 'Déconnecté',
    },
    error: {
      icon: WifiOff,
      color: 'text-error',
      bgColor: 'bg-error/10',
      label: 'Erreur',
    },
  };

  const config = stateConfig[connectionState];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs',
        config.bgColor
      )}
    >
      <Icon
        className={cn(
          'w-3.5 h-3.5',
          config.color,
          connectionState === 'connecting' && 'animate-spin'
        )}
      />
      <span className={config.color}>{config.label}</span>
      {connectionState === 'connected' && latency && (
        <span className="text-text-muted">{latency}ms</span>
      )}
    </div>
  );
}
