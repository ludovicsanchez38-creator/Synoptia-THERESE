// Onglet Données - Paramètres THÉRÈSE
// Stockage local, statistiques, dossier de travail, mode démo, sync CRM

import { Check, Database, FolderOpen, Eye } from 'lucide-react';
import { Button } from '../ui/Button';
import { CRMSyncPanel } from './CRMSyncPanel';
import { useDemoStore } from '../../stores/demoStore';
import * as api from '../../services/api';

export interface DataTabProps {
  stats: api.Stats | null;
  workingDir: string | null;
  onSelectWorkingDir: () => void;
  onRefreshStats?: () => void;
}

export function DataTab({
  stats,
  workingDir,
  onSelectWorkingDir,
  onRefreshStats,
}: DataTabProps) {
  return (
    <div className="space-y-6">
      {/* Section stockage local */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Database className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h3 className="font-medium text-text">Stockage des données</h3>
            <p className="text-xs text-text-muted">
              Vos données sont stockées localement sur votre machine
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

        {stats ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Conversations" value={stats.entities.conversations} />
              <StatCard label="Messages" value={stats.entities.messages} />
              <StatCard label="Contacts" value={stats.entities.contacts} />
              <StatCard label="Projets" value={stats.entities.projects} />
            </div>

            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xs text-text-muted mb-1">Emplacement de la base</p>
              <p className="text-xs text-text font-mono truncate">{stats.db_path}</p>
            </div>

            <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">
                  Données stockées localement - 100% privé
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-background/40 rounded-lg border border-border/30 text-center">
            <p className="text-sm text-text-muted">Statistiques non disponibles</p>
          </div>
        )}
      </div>

      {/* Séparateur */}
      <div className="border-t border-border/30" />

      {/* Section mode démo */}
      <DemoModeSection />

      {/* Séparateur */}
      <div className="border-t border-border/30" />

      {/* Section sync CRM */}
      <CRMSyncPanel onSyncComplete={onRefreshStats} />
    </div>
  );
}

// Section Mode Démo - masque les données réelles
function DemoModeSection() {
  const demoEnabled = useDemoStore((s) => s.enabled);
  const toggleDemo = useDemoStore((s) => s.toggle);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          demoEnabled
            ? 'bg-accent-cyan/20'
            : 'bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20'
        }`}>
          <Eye className="w-5 h-5 text-accent-cyan" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-text">Mode Démo</h3>
          <p className="text-xs text-text-muted">
            Masque les noms et données clients par des personas fictifs
          </p>
        </div>
        <button
          onClick={toggleDemo}
          className={`relative w-11 h-6 rounded-full transition-colors ${
            demoEnabled ? 'bg-accent-cyan' : 'bg-border'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
              demoEnabled ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {demoEnabled && (
        <div className="p-3 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-accent-cyan flex-shrink-0" />
            <span className="text-sm text-accent-cyan">
              Mode démo actif - les données réelles sont masquées
            </span>
          </div>
          <p className="text-xs text-text-muted mt-1.5">
            Raccourci : ⌘⇧D pour activer/désactiver
          </p>
        </div>
      )}

      <p className="text-xs text-text-muted/60">
        Idéal pour les vidéos de présentation et les démos en direct.
        Aucune donnée n'est modifiée en base.
      </p>
    </div>
  );
}

// Carte statistique réutilisable
function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="p-3 bg-background/40 rounded-lg border border-border/30">
      <p className="text-2xl font-bold text-text">{value.toLocaleString('fr-FR')}</p>
      <p className="text-xs text-text-muted">{label}</p>
    </div>
  );
}
