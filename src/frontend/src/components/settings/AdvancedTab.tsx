// Onglet Avancé - Paramètres THÉRÈSE
// Regroupe : Stockage, Accessibilité, Performance, Limites, CRM Sync

import { useState } from 'react';
import { Database, FolderOpen, Check, ChevronDown } from 'lucide-react';
import { Button } from '../ui/Button';
import { AccessibilityTab } from './AccessibilityTab';
import { PerformanceTab } from './PerformanceTab';
import { LimitsTab } from './LimitsTab';
import { CRMSyncPanel } from './CRMSyncPanel';
import * as api from '../../services/api';

export interface AdvancedTabProps {
  stats: api.Stats | null;
  workingDir: string | null;
  onSelectWorkingDir: () => void;
  onRefreshStats?: () => void;
}

// Section dépliable
function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-border/30 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 bg-surface-elevated/30 hover:bg-surface-elevated/50 transition-colors text-left"
      >
        <span className="text-sm font-medium text-text">{title}</span>
        <ChevronDown className={`w-4 h-4 text-text-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="px-4 py-4 border-t border-border/20">
          {children}
        </div>
      )}
    </div>
  );
}

export function AdvancedTab({
  stats,
  workingDir,
  onSelectWorkingDir,
  onRefreshStats,
}: AdvancedTabProps) {
  return (
    <div className="space-y-3">
      {/* Comportement au lancement (US-005) */}
      <CollapsibleSection title="Comportement au lancement">
        <StartupBehavior />
      </CollapsibleSection>

      {/* Stockage */}
      <CollapsibleSection title="Stockage des données" defaultOpen>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
              <Database className="w-5 h-5 text-accent-cyan" />
            </div>
            <div>
              <p className="text-xs text-text-muted">
                Tes données sont stockées localement sur ta machine
              </p>
            </div>
          </div>

          {/* Dossier de travail */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm text-text-muted">Dossier de travail</label>
              <Button variant="ghost" size="sm" onClick={onSelectWorkingDir}>
                <FolderOpen className="w-4 h-4 mr-2" />
                Parcourir
              </Button>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xs text-text font-mono truncate">
                {workingDir || 'Non configuré'}
              </p>
            </div>
          </div>

          {stats && (
            <>
              <div className="grid grid-cols-4 gap-2">
                <StatCard label="Conversations" value={stats.entities.conversations} />
                <StatCard label="Messages" value={stats.entities.messages} />
                <StatCard label="Contacts" value={stats.entities.contacts} />
                <StatCard label="Projets" value={stats.entities.projects} />
              </div>
              <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Données 100% locales</span>
              </div>
            </>
          )}
        </div>
      </CollapsibleSection>

      {/* Accessibilité */}
      <CollapsibleSection title="Accessibilité">
        <AccessibilityTab />
      </CollapsibleSection>

      {/* Performance */}
      <CollapsibleSection title="Performance">
        <PerformanceTab />
      </CollapsibleSection>

      {/* Limites & Consommation */}
      <CollapsibleSection title="Limites & Consommation">
        <LimitsTab />
      </CollapsibleSection>

      {/* CRM Google Sheets */}
      <CollapsibleSection title="Synchronisation CRM">
        <CRMSyncPanel onSyncComplete={onRefreshStats} />
      </CollapsibleSection>
    </div>
  );
}

function StartupBehavior() {
  const [skipDashboard, setSkipDashboard] = useState(() => {
    return localStorage.getItem('therese-skip-dashboard') === 'true';
  });

  const handleToggle = () => {
    const newValue = !skipDashboard;
    setSkipDashboard(newValue);
    localStorage.setItem('therese-skip-dashboard', newValue ? 'true' : 'false');
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-text">Ouvrir sur le chat directement</p>
          <p className="text-xs text-text-muted mt-0.5">
            Masquer le tableau de bord "Ma journée" au lancement
          </p>
        </div>
        <button
          onClick={handleToggle}
          className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
            skipDashboard ? 'bg-accent-cyan' : 'bg-border'
          }`}
          role="switch"
          aria-checked={skipDashboard}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              skipDashboard ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="p-2 bg-background/40 rounded-lg border border-border/30 text-center">
      <p className="text-lg font-bold text-text">{value.toLocaleString('fr-FR')}</p>
      <p className="text-xs text-text-muted">{label}</p>
    </div>
  );
}
