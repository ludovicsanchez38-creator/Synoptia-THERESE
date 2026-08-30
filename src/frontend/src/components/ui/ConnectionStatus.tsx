import { Cpu, PowerOff, Loader } from 'lucide-react';
import { useStatusStore } from '../../stores/statusStore';
import { cn } from '../../lib/utils';

/**
 * État du MOTEUR LOCAL (le sidecar backend), pas du réseau.
 *
 * Campagne dix personas (28/08) : ce bandeau affichait « Connecté » avec une
 * icône Wifi. Une magistrate qui préparait ses interventions dans le train y a
 * lu, logiquement, qu'elle était en ligne. Le libellé et l'icône désignent
 * désormais ce qu'ils mesurent réellement.
 *
 * La détection réseau (`hooks/useOnlineStatus.ts`) existe et n'est branchée
 * nulle part : c'est un autre chantier. Ici, on se contente d'arrêter de faire
 * une promesse qu'on ne tient pas.
 */
export function ConnectionStatus() {
  const { connectionState, latency } = useStatusStore();

  const stateConfig = {
    connected: {
      icon: Cpu,
      color: 'text-success',
      bgColor: 'bg-success/10',
      label: 'Moteur actif',
    },
    connecting: {
      icon: Loader,
      color: 'text-warning',
      bgColor: 'bg-warning/10',
      label: 'Démarrage du moteur...',
    },
    disconnected: {
      icon: PowerOff,
      color: 'text-text-muted',
      bgColor: 'bg-surface-elevated',
      label: 'Moteur arrêté',
    },
    error: {
      icon: PowerOff,
      color: 'text-error',
      bgColor: 'bg-error/10',
      label: 'Erreur du moteur',
    },
  };

  const config = stateConfig[connectionState];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-sm text-xs',
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
