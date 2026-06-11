/**
 * THERESE v2 - SetupChecklist : mise en route guidee qui se retire.
 * N'affiche que les etapes NON faites ; se masque entierement quand tout est branche.
 */
import { Calendar, Mail, FileSignature, KeyRound, ArrowRight } from 'lucide-react';
import type { SetupStatus } from '../../services/api/dashboard';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';

export function SetupChecklist({ status }: { status: SetupStatus }) {
  const steps = [
    {
      // US-012 : sans clé LLM, le premier message du chat échoue - cette
      // étape passe en tête (Ollama local reste l'alternative sans clé).
      done: status.has_llm_key,
      label: 'Configurer une clé IA (ou Ollama)',
      icon: KeyRound,
      action: () => usePanelStore.getState().openSettings(),
    },
    {
      done: status.has_calendar,
      label: 'Connecter ton agenda',
      icon: Calendar,
      action: () => useNavigationStore.getState().setView('calendar'),
    },
    {
      done: status.has_email,
      label: 'Connecter ta messagerie',
      icon: Mail,
      action: () => useNavigationStore.getState().setView('email'),
    },
    {
      done: status.billing_complete,
      label: 'Compléter le profil de facturation',
      icon: FileSignature,
      action: () => usePanelStore.getState().openSettings(),
    },
  ].filter((s) => !s.done);

  if (steps.length === 0) return null;

  return (
    <section className="rounded-xl border border-border bg-surface-2 p-4">
      <h2 className="text-sm font-semibold text-text mb-3">Mise en route</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {steps.map(({ label, icon: Icon, action }) => (
          <button
            key={label}
            type="button"
            onClick={action}
            className="flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] transition-colors text-left"
          >
            <Icon className="w-4 h-4 text-accent shrink-0" />
            <span className="text-[13px] text-text leading-tight flex-1">{label}</span>
            <ArrowRight className="w-3.5 h-3.5 text-text-muted shrink-0" />
          </button>
        ))}
      </div>
    </section>
  );
}
