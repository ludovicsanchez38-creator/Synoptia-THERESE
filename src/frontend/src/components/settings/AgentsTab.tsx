/**
 * THÉRÈSE v2 - Agents Settings Tab
 *
 * Configuration des agents IA embarqués (Atelier).
 * Choix du modèle par agent, chemin source, statut.
 */

import { useState, useEffect } from 'react';
import { Zap, RefreshCw, CheckCircle, XCircle, AlertCircle, Headphones, Wrench } from 'lucide-react';
import { getAgentStatus, getAgentConfig, updateAgentConfig } from '../../services/api/agents';
import type { AgentStatusResponse, AgentConfigResponse } from '../../services/api/agents';
import { useAtelierStore } from '../../stores/atelierStore';

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  recommended?: boolean;
}

export function AgentsTab() {
  const [status, setStatus] = useState<AgentStatusResponse | null>(null);
  const [, setConfig] = useState<AgentConfigResponse | null>(null);
  const [sourcePath, setSourcePathInput] = useState('');
  const [katiaModel, setThereseModel] = useState('claude-sonnet-4-6');
  const [zezetteModel, setZezetteModel] = useState('claude-sonnet-4-6');
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const setSourcePath = useAtelierStore((s) => s.setSourcePath);

  useEffect(() => {
    Promise.all([
      getAgentStatus().catch(() => null),
      getAgentConfig().catch(() => null),
    ]).then(([s, c]) => {
      setStatus(s);
      setConfig(c);
      if (c?.source_path) setSourcePathInput(c.source_path);
      if (c?.katia_model) setThereseModel(c.katia_model);
      if (c?.zezette_model) setZezetteModel(c.zezette_model);
      if (c?.available_models) setModels(c.available_models);
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateAgentConfig({
        source_path: sourcePath.trim() || undefined,
        katia_model: katiaModel,
        zezette_model: zezetteModel,
      });
      setConfig(updated);
      if (sourcePath.trim()) setSourcePath(sourcePath.trim());
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      const s = await getAgentStatus().catch(() => null);
      setStatus(s);
    } catch {
      // silent
    } finally {
      setSaving(false);
    }
  };

  const handleRefreshStatus = async () => {
    setLoading(true);
    const s = await getAgentStatus().catch(() => null);
    setStatus(s);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-text-muted">
        Chargement...
      </div>
    );
  }

  // Grouper les modèles par provider
  const providerLabels: Record<string, string> = {
    anthropic: 'Anthropic',
    openai: 'OpenAI',
    gemini: 'Google',
    grok: 'xAI',
    mistral: 'Mistral',
    openrouter: 'OpenRouter',
    deepseek: 'DeepSeek',
    ollama: 'Local (Ollama)',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-base font-semibold text-text flex items-center gap-2">
          <Zap size={18} className="text-purple-400" />
          Agents IA Embarqués
        </h3>
        <p className="mt-1 text-sm text-text-muted">
          Katia (PM/Guide) et Zézette (Dev) peuvent améliorer l'app directement.
        </p>
      </div>

      {/* Statut */}
      <div className="rounded-lg border border-border/50 bg-surface-elevated/30 p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-text">Statut</h4>
          <button
            onClick={handleRefreshStatus}
            className="text-xs text-text-muted hover:text-text transition"
          >
            <RefreshCw size={14} />
          </button>
        </div>
        <div className="space-y-2 text-sm">
          <StatusRow label="Git" ok={status?.git_available} />
          <StatusRow label="Dépôt détecté" ok={status?.repo_detected} />
          <StatusRow label="Katia" ok={status?.katia_ready} />
          <StatusRow label="Zézette" ok={status?.zezette_ready} />
          {status?.current_branch && (
            <div className="flex items-center justify-between text-text-muted">
              <span>Branche</span>
              <span className="font-mono text-xs">{status.current_branch}</span>
            </div>
          )}
        </div>
      </div>

      {/* Choix du modèle par agent */}
      <div className="rounded-lg border border-border/50 bg-surface-elevated/30 p-4">
        <h4 className="text-sm font-medium text-text mb-3">Modèle IA par agent</h4>

        {/* Katia */}
        <div className="mb-3">
          <label className="flex items-center gap-2 text-xs font-medium text-purple-400 mb-1.5">
            <Headphones size={12} />
            Katia (PM/Guide)
          </label>
          <select
            value={katiaModel}
            onChange={(e) => setThereseModel(e.target.value)}
            className="w-full rounded-lg border border-border/50 bg-bg px-3 py-2 text-sm text-text outline-none focus:border-purple-500/50"
          >
            {Object.entries(providerLabels).map(([provider, label]) => {
              const providerModels = models.filter((m) => m.provider === provider);
              if (providerModels.length === 0) return null;
              return (
                <optgroup key={provider} label={label}>
                  {providerModels.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}{m.recommended ? ' (recommandé)' : ''}
                    </option>
                  ))}
                </optgroup>
              );
            })}
          </select>
        </div>

        {/* Zézette */}
        <div>
          <label className="flex items-center gap-2 text-xs font-medium text-amber-400 mb-1.5">
            <Wrench size={12} />
            Zézette (Dev)
          </label>
          <select
            value={zezetteModel}
            onChange={(e) => setZezetteModel(e.target.value)}
            className="w-full rounded-lg border border-border/50 bg-bg px-3 py-2 text-sm text-text outline-none focus:border-purple-500/50"
          >
            {Object.entries(providerLabels).map(([provider, label]) => {
              const providerModels = models.filter((m) => m.provider === provider);
              if (providerModels.length === 0) return null;
              return (
                <optgroup key={provider} label={label}>
                  {providerModels.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}{m.recommended ? ' (recommandé)' : ''}
                    </option>
                  ))}
                </optgroup>
              );
            })}
          </select>
        </div>
      </div>

      {/* Chemin du source */}
      <div className="rounded-lg border border-border/50 bg-surface-elevated/30 p-4">
        <h4 className="text-sm font-medium text-text mb-2">
          Chemin du code source
        </h4>
        <p className="text-xs text-text-muted mb-3">
          Chemin local vers ton clone/fork du repo THÉRÈSE.
        </p>
        <input
          type="text"
          value={sourcePath}
          onChange={(e) => setSourcePathInput(e.target.value)}
          placeholder="/chemin/vers/Synoptia-THERESE"
          className="w-full rounded-lg border border-border/50 bg-bg px-3 py-2 text-sm text-text placeholder-text-muted/50 outline-none focus:border-purple-500/50"
        />
      </div>

      {/* Bouton sauver global */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full rounded-lg bg-purple-500/20 px-4 py-2.5 text-sm font-medium text-purple-400 transition hover:bg-purple-500/30 disabled:opacity-50"
      >
        {saving ? 'Sauvegarde...' : saved ? 'Sauvegardé' : 'Sauvegarder la configuration'}
      </button>
    </div>
  );
}

function StatusRow({ label, ok }: { label: string; ok?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-text-muted">{label}</span>
      {ok === undefined ? (
        <AlertCircle size={14} className="text-text-muted/50" />
      ) : ok ? (
        <CheckCircle size={14} className="text-green-400" />
      ) : (
        <XCircle size={14} className="text-red-400" />
      )}
    </div>
  );
}
