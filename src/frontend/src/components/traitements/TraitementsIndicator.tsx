/**
 * Le badge des traitements dans la coque (0.46).
 */
import { useEffect } from 'react';
import { Activity } from 'lucide-react';

import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { TraitementsPanel } from './TraitementsPanel';

export function TraitementsIndicator() {
  const traitements = useProcessingTasksStore((s) => s.traitements);
  const panneauOuvert = useProcessingTasksStore((s) => s.panneauOuvert);
  const ouvrir = useProcessingTasksStore((s) => s.ouvrirPanneau);
  const fermer = useProcessingTasksStore((s) => s.fermerPanneau);
  const demarrerSondage = useProcessingTasksStore((s) => s.demarrerSondage);
  const arreterSondage = useProcessingTasksStore((s) => s.arreterSondage);

  useEffect(() => {
    demarrerSondage();
    return arreterSondage;
  }, [demarrerSondage, arreterSondage]);

  const actives = traitements.filter(
    (t) =>
      t.state === 'running' || t.state === 'queued' || t.state === 'cancel_requested',
  ).length;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => (panneauOuvert ? fermer() : ouvrir())}
        aria-label={`Travaux (${actives} en cours)`}
        className="relative flex items-center rounded-md border border-border bg-surface p-1.5 text-text-muted hover:bg-surface-2"
      >
        <Activity className="h-3.5 w-3.5" />
        {actives > 0 && (
          <span
            className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-xs font-semibold text-white"
            data-testid="traitements-actifs"
          >
            {actives}
          </span>
        )}
      </button>
      {panneauOuvert && <TraitementsPanel />}
    </div>
  );
}
