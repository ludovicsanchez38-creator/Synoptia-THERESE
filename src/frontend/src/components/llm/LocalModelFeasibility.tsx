import { AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';
import type { OllamaModel, SystemResources } from '../../services/api';
import { assessLocalModelFeasibility } from './modelFeasibility';

const GIB = 1024 ** 3;

function formatGib(bytes: number): string {
  return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(bytes / GIB);
}

export function LocalModelFeasibility({
  model,
  resources,
}: {
  model: OllamaModel | undefined;
  resources: SystemResources | null;
}) {
  const result = assessLocalModelFeasibility(model, resources);

  if (result.status === 'unknown') {
    return (
      <div className="flex items-start gap-2 rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted" data-testid="local-model-feasibility" data-status="unknown">
        <HelpCircle className="mt-0.5 h-4 w-4 shrink-0" />
        <span>Faisabilité RAM inconnue. Le choix reste possible.</span>
      </div>
    );
  }

  const estimated = formatGib(result.estimatedRamBytes!);
  const prudentLimit = formatGib(resources!.safe_local_model_ram_bytes!);
  const totalRam = resources!.total_ram_bytes == null
    ? null
    : formatGib(resources!.total_ram_bytes);

  if (result.status === 'too-large') {
    return (
      <div className="flex items-start gap-2 rounded-lg border border-error/50 bg-[var(--color-error-tint)] px-3 py-2 text-xs leading-5 text-error" role="alert" data-testid="local-model-feasibility" data-status="too-large">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <span>
          <strong className="mr-1 inline-flex rounded-full bg-error/15 px-2 py-0.5">RAM déconseillée</strong>
          Environ {estimated} Gio requis, pour un plafond de {prudentLimit} Gio
          {totalRam ? ` (la moitié des ${totalRam} Gio de RAM)` : ''}. Le choix reste possible, mais la machine peut fortement ralentir.
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-xs leading-5 text-green-400" data-testid="local-model-feasibility" data-status="feasible">
      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
      <span>
        <strong className="mr-1 inline-flex rounded-full bg-green-500/15 px-2 py-0.5">RAM compatible</strong>
        Environ {estimated} Gio requis, sous le plafond de {prudentLimit} Gio.
      </span>
    </div>
  );
}
