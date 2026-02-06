// Onglet Performance - Paramètres THÉRÈSE
// Métriques streaming, gestion mémoire, économie d'énergie (US-PERF-01 à US-PERF-05)

import { useState, useEffect } from 'react';
import { Check, AlertCircle, Loader2, Gauge } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

export function PerformanceTab() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<api.PerformanceStatus | null>(null);
  const [cleaningUp, setCleaningUp] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setLoading(true);
    try {
      const data = await api.getPerformanceStatus();
      setStatus(data);
    } catch (err) {
      console.error('Échec du chargement du statut performance:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCleanup() {
    setCleaningUp(true);
    try {
      await api.triggerMemoryCleanup();
      await loadStatus();
    } catch (err) {
      console.error('Échec du nettoyage:', err);
    } finally {
      setCleaningUp(false);
    }
  }

  async function handleToggleBatterySaver() {
    if (!status) return;
    try {
      const newEnabled = !status.power.battery_saver_mode;
      await api.setBatterySaver(newEnabled);
      await loadStatus();
    } catch (err) {
      console.error('Échec du changement mode économie:', err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <Gauge className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h3 className="font-medium text-text">Performances</h3>
          <p className="text-xs text-text-muted">
            Monitoring et optimisation
          </p>
        </div>
      </div>

      {/* Métriques streaming (US-PERF-01) */}
      {status?.streaming && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-text">Temps de réponse</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.streaming.avg_first_token_ms?.toFixed(0) || '-'} ms
              </p>
              <p className="text-xs text-text-muted">Premier token (moyenne)</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.streaming.p95_first_token_ms?.toFixed(0) || '-'} ms
              </p>
              <p className="text-xs text-text-muted">Premier token (P95)</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">{status.streaming.total_requests}</p>
              <p className="text-xs text-text-muted">Requêtes totales</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">{status.streaming.total_tokens?.toLocaleString('fr-FR') || 0}</p>
              <p className="text-xs text-text-muted">Tokens générés</p>
            </div>
          </div>
          {/* Statut SLA */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
            status.streaming.meets_sla
              ? 'bg-green-500/10 border border-green-500/20'
              : 'bg-yellow-500/10 border border-yellow-500/20'
          }`}>
            {status.streaming.meets_sla ? (
              <>
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">SLA respecté ({"<"} 2s)</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 text-yellow-400" />
                <span className="text-sm text-yellow-400">SLA non respecté ({">"} 2s)</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Gestion mémoire (US-PERF-03) */}
      {status?.memory && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-text">Mémoire</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCleanup}
              disabled={cleaningUp}
            >
              {cleaningUp ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Nettoyer'
              )}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.memory.uptime_hours.toFixed(1)}h
              </p>
              <p className="text-xs text-text-muted">Uptime</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.memory.last_cleanup_ago_minutes.toFixed(0)} min
              </p>
              <p className="text-xs text-text-muted">Dernier nettoyage</p>
            </div>
          </div>
        </div>
      )}

      {/* Économie d'énergie (US-PERF-05) */}
      {status?.power && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-text">Mode économie d'énergie</h4>
              <p className="text-xs text-text-muted">
                Réduit les vérifications et animations pour économiser la batterie
              </p>
            </div>
            <button
              onClick={handleToggleBatterySaver}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                status.power.battery_saver_mode ? 'bg-accent-cyan' : 'bg-border'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                  status.power.battery_saver_mode ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2 bg-background/40 rounded border border-border/30">
              <span className="text-text-muted">Health check : </span>
              <span className="text-text">{status.power.health_check_interval}s</span>
            </div>
            <div className="p-2 bg-background/40 rounded border border-border/30">
              <span className="text-text-muted">Animations : </span>
              <span className="text-text">{status.power.reduce_animations ? 'Réduites' : 'Normales'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Nombre de conversations indexées */}
      {status?.conversations_total !== undefined && (
        <div className="pt-4 border-t border-border/30">
          <div className="p-3 bg-background/40 rounded-lg border border-border/30">
            <p className="text-2xl font-bold text-text">{status.conversations_total}</p>
            <p className="text-xs text-text-muted">Conversations indexées</p>
          </div>
        </div>
      )}
    </div>
  );
}
