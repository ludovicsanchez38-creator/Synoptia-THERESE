// Onglet Limites & Consommation - Paramètres THÉRÈSE
// Usage quotidien/mensuel, limites configurables, budget (US-ESC-01 à US-ESC-05)

import { useState, useEffect } from 'react';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

export function LimitsTab() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<api.EscalationStatus | null>(null);
  const [limits, setLimits] = useState<api.TokenLimits | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [statusData, limitsData] = await Promise.all([
        api.getEscalationStatus(),
        api.getTokenLimits(),
      ]);
      setStatus(statusData);
      setLimits(limitsData);
    } catch (err) {
      console.error('Échec du chargement des données de limites:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveLimits() {
    if (!limits) return;
    setSaving(true);
    try {
      await api.setTokenLimits(limits);
      await loadData();
    } catch (err) {
      console.error('Échec de la sauvegarde des limites:', err);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
      </div>
    );
  }

  // Calcul des pourcentages d'utilisation
  const dailyInputPercent = limits && status?.daily_usage
    ? Math.min(100, (status.daily_usage.input_tokens / limits.daily_input_limit) * 100)
    : 0;
  const monthlyBudgetPercent = limits && status?.monthly_usage
    ? Math.min(100, (status.monthly_usage.cost_eur / limits.monthly_budget_eur) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h3 className="font-medium text-text">Limites & Consommation</h3>
          <p className="text-xs text-text-muted">
            Contrôle des coûts et de l'utilisation des tokens
          </p>
        </div>
      </div>

      {/* Usage quotidien (US-ESC-04) */}
      {status?.daily_usage && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-text">Usage aujourd'hui</h4>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {(status.daily_usage.input_tokens / 1000).toFixed(1)}K
              </p>
              <p className="text-xs text-text-muted">Tokens entrée</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {(status.daily_usage.output_tokens / 1000).toFixed(1)}K
              </p>
              <p className="text-xs text-text-muted">Tokens sortie</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {status.daily_usage.cost_eur.toFixed(2)} €
              </p>
              <p className="text-xs text-text-muted">Coût</p>
            </div>
          </div>
          {/* Barre de progression */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-text-muted">
              <span>Limite quotidienne</span>
              <span>{dailyInputPercent.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-background rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  dailyInputPercent > 90 ? 'bg-red-500' : dailyInputPercent > 75 ? 'bg-yellow-500' : 'bg-accent-cyan'
                }`}
                style={{ width: `${dailyInputPercent}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Usage mensuel */}
      {status?.monthly_usage && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <h4 className="text-sm font-medium text-text">Usage ce mois</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {(status.monthly_usage.input_tokens / 1000).toFixed(1)}K
              </p>
              <p className="text-xs text-text-muted">Tokens totaux</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {status.monthly_usage.cost_eur.toFixed(2)} €
              </p>
              <p className="text-xs text-text-muted">Coût total</p>
            </div>
          </div>
          {/* Progression du budget */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-text-muted">
              <span>Budget mensuel ({limits?.monthly_budget_eur || 50} €)</span>
              <span>{monthlyBudgetPercent.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-background rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  monthlyBudgetPercent > 90 ? 'bg-red-500' : monthlyBudgetPercent > 75 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${monthlyBudgetPercent}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Configuration des limites (US-ESC-03) */}
      {limits && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-text">Limites configurables</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSaveLimits}
              disabled={saving}
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="settings-limit-max-input" className="text-xs text-text-muted mb-1 block">Max tokens/requête (entrée)</label>
              <input
                id="settings-limit-max-input"
                type="number"
                value={limits.max_input_tokens}
                onChange={(e) => setLimits({ ...limits, max_input_tokens: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan"
              />
            </div>
            <div>
              <label htmlFor="settings-limit-max-output" className="text-xs text-text-muted mb-1 block">Max tokens/requête (sortie)</label>
              <input
                id="settings-limit-max-output"
                type="number"
                value={limits.max_output_tokens}
                onChange={(e) => setLimits({ ...limits, max_output_tokens: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan"
              />
            </div>
            <div>
              <label htmlFor="settings-limit-daily" className="text-xs text-text-muted mb-1 block">Limite quotidienne (tokens)</label>
              <input
                id="settings-limit-daily"
                type="number"
                value={limits.daily_input_limit}
                onChange={(e) => setLimits({ ...limits, daily_input_limit: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan"
              />
            </div>
            <div>
              <label htmlFor="settings-limit-budget" className="text-xs text-text-muted mb-1 block">Budget mensuel (€)</label>
              <input
                id="settings-limit-budget"
                type="number"
                step="0.01"
                value={limits.monthly_budget_eur}
                onChange={(e) => setLimits({ ...limits, monthly_budget_eur: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan"
              />
            </div>
          </div>
          <div>
            <label htmlFor="settings-limit-warn" className="text-xs text-text-muted mb-1 block">Alerter à (% du budget)</label>
            <input
              id="settings-limit-warn"
              type="number"
              min="0"
              max="100"
              value={limits.warn_at_percentage}
              onChange={(e) => setLimits({ ...limits, warn_at_percentage: parseInt(e.target.value) || 80 })}
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
        </div>
      )}

      {/* Information */}
      <div className="p-3 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-accent-cyan mt-0.5" />
          <div className="text-sm text-accent-cyan">
            <p className="font-medium">Indicateurs IA (US-ESC-01)</p>
            <p className="text-xs text-accent-cyan/80 mt-1">
              THÉRÈSE détecte automatiquement quand l'IA n'est pas sûre de sa réponse et l'indique dans la conversation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
