import { useState, useEffect } from 'react';
import {
  Wrench,
  Plus,
  Play,
  Square,
  RefreshCw,
  Trash2,
  Check,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Download,
  Server,
  Zap,
  Globe,
  Briefcase,
  BarChart3,
  CreditCard,
  Search,
  Megaphone,
  Settings2,
  MessageCircle,
  Star,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { EnvVarModal } from './EnvVarModal';
import * as api from '../../services/api';

// ============================================================
// PresetCategory - Groupe de presets avec header repliable
// ============================================================

interface PresetCategoryProps {
  category: string;
  label: string;
  icon: React.ReactNode;
  presets: api.MCPPreset[];
  servers: api.MCPServer[];
  installingPreset: string | null;
  onInstall: (presetId: string) => void;
  defaultCollapsed?: boolean;
}

function PresetCategory({
  label,
  icon,
  presets,
  servers,
  installingPreset,
  onInstall,
  defaultCollapsed = false,
}: PresetCategoryProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <div>
      {/* Category header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 w-full text-left mb-2 group"
      >
        <span className="text-accent-cyan/70 group-hover:text-accent-cyan transition-colors">
          {icon}
        </span>
        <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
          {label}
        </span>
        <div className="flex-1 h-px bg-border/30" />
        {collapsed ? (
          <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
        )}
      </button>

      {/* Preset cards */}
      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-2 gap-2">
              {presets.map((preset) => {
                const runningServer = servers.find(
                  (s) => s.name === preset.name && s.status === 'running'
                );
                const isInstalled = servers.some((s) => s.name === preset.name);
                const isInstalling = installingPreset === preset.id;

                return (
                  <button
                    key={preset.id}
                    onClick={() => !isInstalled && !isInstalling && onInstall(preset.id)}
                    disabled={isInstalled || isInstalling}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      runningServer
                        ? 'bg-green-500/10 border-green-500/30 cursor-default'
                        : isInstalled
                        ? 'bg-background/60 border-border/50 cursor-default opacity-60'
                        : isInstalling
                        ? 'bg-accent-cyan/10 border-accent-cyan/30 cursor-wait'
                        : 'bg-background/60 border-border/50 hover:border-accent-cyan/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-medium text-text">{preset.name}</span>
                        {preset.popular && (
                          <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                        )}
                        {preset.risk_level === 'high' && (
                          <span className="flex items-center gap-0.5 px-1 py-0.5 rounded text-[10px] font-medium bg-red-500/20 text-red-400" title={preset.risk_warning}>
                            <ShieldAlert className="w-2.5 h-2.5" />
                            Élevé
                          </span>
                        )}
                        {preset.risk_level === 'medium' && (
                          <span className="flex items-center gap-0.5 px-1 py-0.5 rounded text-[10px] font-medium bg-yellow-500/20 text-yellow-400" title={preset.risk_warning}>
                            <ShieldAlert className="w-2.5 h-2.5" />
                            Moyen
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        {preset.url && (
                          <a
                            href={preset.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="p-0.5 hover:bg-border/30 rounded transition-colors"
                            title={`Voir ${preset.name}`}
                          >
                            <ExternalLink className="w-3 h-3 text-text-muted hover:text-accent-cyan" />
                          </a>
                        )}
                        {isInstalling && <Loader2 className="w-4 h-4 text-accent-cyan animate-spin" />}
                        {!isInstalling && runningServer && <Check className="w-4 h-4 text-green-400" />}
                        {!isInstalling && isInstalled && !runningServer && (
                          <AlertCircle className="w-4 h-4 text-yellow-400" />
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-text-muted line-clamp-2">{preset.description}</p>
                    {preset.env_required && preset.env_required.length > 0 && (
                      <p className="text-xs text-yellow-400 mt-1">
                        Requiert: {preset.env_required.join(', ')}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// ToolsPanel - Main component
// ============================================================

interface ToolsPanelProps {
  onError: (error: string | null) => void;
}

export function ToolsPanel({ onError }: ToolsPanelProps) {
  const [loading, setLoading] = useState(true);
  const [servers, setServers] = useState<api.MCPServer[]>([]);
  const [presets, setPresets] = useState<api.MCPPreset[]>([]);
  const [status, setStatus] = useState<api.MCPStatus | null>(null);
  const [expandedServer, setExpandedServer] = useState<string | null>(null);
  const [showAddServer, setShowAddServer] = useState(false);
  const [showPresets, setShowPresets] = useState(false);
  const [serverToDelete, setServerToDelete] = useState<string | null>(null);
  const [installingPreset, setInstallingPreset] = useState<string | null>(null);
  const [presetToConfig, setPresetToConfig] = useState<api.MCPPreset | null>(null);
  const [presetFilter, setPresetFilter] = useState('');

  // New server form
  const [newServer, setNewServer] = useState({
    name: '',
    command: '',
    args: '',
    enabled: true,
  });
  const [addingServer, setAddingServer] = useState(false);

  // Load data
  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [serversData, presetsData, statusData] = await Promise.all([
        api.listMCPServers(),
        api.listMCPPresets(),
        api.getMCPStatus(),
      ]);
      setServers(serversData);
      setPresets(presetsData);
      setStatus(statusData);
    } catch (err) {
      console.error('Failed to load MCP data:', err);
      onError('Erreur lors du chargement des serveurs MCP');
    } finally {
      setLoading(false);
    }
  }

  async function handleStartServer(serverId: string) {
    try {
      const updated = await api.startMCPServer(serverId);
      setServers((prev) => prev.map((s) => (s.id === serverId ? updated : s)));
      await refreshStatus();
    } catch (err) {
      onError(`Erreur: ${err instanceof Error ? err.message : 'Impossible de démarrer le serveur'}`);
    }
  }

  async function handleStopServer(serverId: string) {
    try {
      const updated = await api.stopMCPServer(serverId);
      setServers((prev) => prev.map((s) => (s.id === serverId ? updated : s)));
      await refreshStatus();
    } catch (err) {
      onError(`Erreur: ${err instanceof Error ? err.message : 'Impossible d\'arrêter le serveur'}`);
    }
  }

  async function handleRestartServer(serverId: string) {
    try {
      const updated = await api.restartMCPServer(serverId);
      setServers((prev) => prev.map((s) => (s.id === serverId ? updated : s)));
      await refreshStatus();
    } catch (err) {
      onError(`Erreur: ${err instanceof Error ? err.message : 'Impossible de redémarrer le serveur'}`);
    }
  }

  async function handleDeleteServer(serverId: string) {
    setServerToDelete(serverId);
  }

  async function confirmDelete() {
    if (!serverToDelete) return;

    try {
      console.log('Deleting MCP server:', serverToDelete);
      await api.deleteMCPServer(serverToDelete);
      console.log('Server deleted successfully');

      // Reload all data from backend to ensure consistency
      await loadData();

      // Clear error if any
      onError(null);
    } catch (err) {
      console.error('Failed to delete MCP server:', err);
      const errorMsg = err instanceof Error ? err.message : 'Impossible de supprimer le serveur';
      onError(`Erreur suppression: ${errorMsg}`);
    } finally {
      setServerToDelete(null);
    }
  }

  async function handleAddServer() {
    if (!newServer.name.trim() || !newServer.command.trim()) {
      onError('Nom et commande requis');
      return;
    }

    setAddingServer(true);
    try {
      const created = await api.createMCPServer({
        name: newServer.name,
        command: newServer.command,
        args: newServer.args.split(' ').filter((a) => a.trim()),
        enabled: newServer.enabled,
      });
      setServers((prev) => [...prev, created]);
      setNewServer({ name: '', command: '', args: '', enabled: true });
      setShowAddServer(false);
      await refreshStatus();
    } catch (err) {
      onError(`Erreur: ${err instanceof Error ? err.message : 'Impossible d\'ajouter le serveur'}`);
    } finally {
      setAddingServer(false);
    }
  }

  async function handleInstallPreset(presetId: string) {
    const preset = presets.find((p) => p.id === presetId);
    if (!preset) return;

    // Check if already installed (éviter doublons)
    const alreadyInstalled = servers.some((s) => s.name === preset.name);
    if (alreadyInstalled) {
      onError(`${preset.name} est déjà installé`);
      return;
    }

    // Check for required env vars - ouvrir modal si nécessaire
    if (preset.env_required && preset.env_required.length > 0) {
      setPresetToConfig(preset);
      return;
    }

    // Pas de clés requises, installer directement
    await doInstallPreset(presetId, {});
  }

  async function handleEnvVarSubmit(envVars: Record<string, string>) {
    if (!presetToConfig) return;
    setPresetToConfig(null);
    await doInstallPreset(presetToConfig.id, envVars);
  }

  async function doInstallPreset(presetId: string, envVars: Record<string, string>) {
    setInstallingPreset(presetId);

    try {
      // Install preset
      const installed = await api.installMCPPreset(presetId, envVars);
      setServers((prev) => [...prev, installed]);
      setPresets((prev) =>
        prev.map((p) => (p.id === presetId ? { ...p, installed: true } : p))
      );

      // Auto-start after installation
      try {
        await handleStartServer(installed.id);
      } catch (startErr) {
        console.error('Failed to auto-start server:', startErr);
        // Don't show error, server is installed, user can start manually
      }

      await refreshStatus();
    } catch (err) {
      onError(`Erreur: ${err instanceof Error ? err.message : 'Impossible d\'installer le preset'}`);
    } finally {
      setInstallingPreset(null);
    }
  }

  async function refreshStatus() {
    try {
      const statusData = await api.getMCPStatus();
      setStatus(statusData);
    } catch {
      // Ignore
    }
  }

  // getStatusColor is available for future use
  function _getStatusColor(serverStatus: api.MCPServerStatus) {
    switch (serverStatus) {
      case 'running':
        return 'text-green-400';
      case 'starting':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-text-muted';
    }
  }
  void _getStatusColor; // suppress unused warning

  function getStatusBadge(serverStatus: api.MCPServerStatus) {
    switch (serverStatus) {
      case 'running':
        return (
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-500/20 text-green-400">
            Actif
          </span>
        );
      case 'starting':
        return (
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-500/20 text-yellow-400">
            Démarrage...
          </span>
        );
      case 'error':
        return (
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-500/20 text-red-400">
            Erreur
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-border/50 text-text-muted">
            Arrêté
          </span>
        );
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
      {/* Header + Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Wrench className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h3 className="font-medium text-text">Serveurs MCP</h3>
            <p className="text-xs text-text-muted">
              {status?.running_servers || 0} actif(s) sur {status?.total_servers || 0} •{' '}
              {status?.total_tools || 0} tools disponibles
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setShowPresets(!showPresets)}>
            <Download className="w-4 h-4 mr-2" />
            Presets
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setShowAddServer(!showAddServer)}>
            <Plus className="w-4 h-4 mr-2" />
            Ajouter
          </Button>
        </div>
      </div>

      {/* Presets Panel */}
      <AnimatePresence>
        {showPresets && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-background/40 rounded-lg border border-border/30 space-y-4">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-accent-cyan" />
                  <span className="text-sm font-medium text-text">
                    Presets disponibles
                    <span className="text-text-muted font-normal ml-1">({presets.length})</span>
                  </span>
                </div>
              </div>

              {/* Barre de recherche */}
              <input
                type="text"
                value={presetFilter}
                onChange={(e) => setPresetFilter(e.target.value)}
                placeholder="Rechercher un preset..."
                className="w-full px-3 py-1.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              />

              {(() => {
                // Filtrer par recherche
                const filter = presetFilter.toLowerCase().trim();
                const filteredPresets = filter
                  ? presets.filter((p) =>
                      p.name.toLowerCase().includes(filter) ||
                      p.description.toLowerCase().includes(filter) ||
                      (p.category || '').toLowerCase().includes(filter)
                    )
                  : presets;

                // Grouper les presets par categorie
                const CATEGORY_ORDER = ['essentiels', 'productivite', 'recherche', 'marketing', 'crm', 'finance', 'communication', 'avance'];
                const CATEGORY_LABELS: Record<string, string> = {
                  essentiels: 'Essentiels',
                  productivite: 'Productivite',
                  recherche: 'Recherche',
                  marketing: 'Marketing',
                  crm: 'CRM & Ventes',
                  finance: 'Finance',
                  communication: 'Communication',
                  avance: 'Avance',
                };
                const CATEGORY_ICONS: Record<string, React.ReactNode> = {
                  essentiels: <Globe className="w-3.5 h-3.5" />,
                  productivite: <Briefcase className="w-3.5 h-3.5" />,
                  recherche: <Search className="w-3.5 h-3.5" />,
                  marketing: <Megaphone className="w-3.5 h-3.5" />,
                  crm: <BarChart3 className="w-3.5 h-3.5" />,
                  finance: <CreditCard className="w-3.5 h-3.5" />,
                  communication: <MessageCircle className="w-3.5 h-3.5" />,
                  avance: <Settings2 className="w-3.5 h-3.5" />,
                };

                const grouped: Record<string, api.MCPPreset[]> = {};
                for (const preset of filteredPresets) {
                  const cat = preset.category || 'essentiels';
                  if (!grouped[cat]) grouped[cat] = [];
                  grouped[cat].push(preset);
                }

                const categories = CATEGORY_ORDER.filter((cat) => grouped[cat]?.length);

                if (categories.length === 0 && filter) {
                  return (
                    <p className="text-sm text-text-muted text-center py-4">
                      Aucun preset pour "{presetFilter}"
                    </p>
                  );
                }

                return categories.map((cat) => (
                  <PresetCategory
                    key={cat}
                    category={cat}
                    label={CATEGORY_LABELS[cat] || cat}
                    icon={CATEGORY_ICONS[cat]}
                    presets={grouped[cat]}
                    servers={servers}
                    installingPreset={installingPreset}
                    onInstall={handleInstallPreset}
                    defaultCollapsed={cat === 'avance' && !filter}
                  />
                ));
              })()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add Server Form */}
      <AnimatePresence>
        {showAddServer && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-background/40 rounded-lg border border-border/30 space-y-3">
              <div className="flex items-center gap-2 mb-3">
                <Server className="w-4 h-4 text-accent-cyan" />
                <span className="text-sm font-medium text-text">Nouveau serveur MCP</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Nom</label>
                  <input
                    type="text"
                    value={newServer.name}
                    onChange={(e) => setNewServer((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="Mon serveur"
                    className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Commande</label>
                  <input
                    type="text"
                    value={newServer.command}
                    onChange={(e) => setNewServer((prev) => ({ ...prev, command: e.target.value }))}
                    placeholder="npx"
                    className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-text-muted mb-1 block">Arguments (séparés par espaces)</label>
                <input
                  type="text"
                  value={newServer.args}
                  onChange={(e) => setNewServer((prev) => ({ ...prev, args: e.target.value }))}
                  placeholder="-y @anthropic/mcp-server-filesystem ~"
                  className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={newServer.enabled}
                    onChange={(e) => setNewServer((prev) => ({ ...prev, enabled: e.target.checked }))}
                    className="rounded border-border bg-background"
                  />
                  Démarrer automatiquement
                </label>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setShowAddServer(false)}>
                    Annuler
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleAddServer}
                    disabled={addingServer || !newServer.name.trim() || !newServer.command.trim()}
                  >
                    {addingServer ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Ajouter'}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Servers List */}
      {servers.length === 0 ? (
        <div className="p-8 text-center bg-background/40 rounded-lg border border-border/30">
          <Server className="w-8 h-8 text-text-muted mx-auto mb-3" />
          <p className="text-text-muted">Aucun serveur MCP configuré</p>
          <p className="text-xs text-text-muted mt-1">
            Cliquez sur "Presets" pour installer des serveurs prédéfinis
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {servers.map((server) => (
            <div
              key={server.id}
              className="bg-background/40 rounded-lg border border-border/30 overflow-hidden"
            >
              {/* Server Header */}
              <div className="flex items-center justify-between p-3">
                <div
                  className="flex items-center gap-3 flex-1 cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setExpandedServer(expandedServer === server.id ? null : server.id)}
                >
                  <div className={`w-2 h-2 rounded-full ${
                    server.status === 'running' ? 'bg-green-400 animate-pulse' :
                    server.status === 'starting' ? 'bg-yellow-400 animate-pulse' :
                    server.status === 'error' ? 'bg-red-400' : 'bg-border'
                  }`} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-text">{server.name}</span>
                      {getStatusBadge(server.status)}
                    </div>
                    <p className="text-xs text-text-muted">
                      {server.command} {server.args.join(' ')}
                    </p>
                    {/* Show error inline if present */}
                    {server.error && (
                      <p className="text-xs text-red-400 mt-1 line-clamp-1" title={server.error}>
                        {server.error}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-muted">
                    {server.tools.length} tool{server.tools.length !== 1 ? 's' : ''}
                  </span>
                  {/* Quick delete button for error servers */}
                  {server.status === 'error' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteServer(server.id);
                      }}
                      className="p-1 rounded hover:bg-red-500/10 transition-colors"
                      title="Supprimer"
                    >
                      <Trash2 className="w-3 h-3 text-red-400" />
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpandedServer(expandedServer === server.id ? null : server.id);
                    }}
                    className="p-1"
                  >
                    {expandedServer === server.id ? (
                      <ChevronDown className="w-4 h-4 text-text-muted" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-text-muted" />
                    )}
                  </button>
                </div>
              </div>

              {/* Server Details (Expanded) */}
              <AnimatePresence>
                {expandedServer === server.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden border-t border-border/30"
                  >
                    <div className="p-3 space-y-3">
                      {/* Error message */}
                      {server.error && (
                        <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                          <span className="text-xs text-red-400">{server.error}</span>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        {server.status === 'running' ? (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStopServer(server.id)}
                            >
                              <Square className="w-4 h-4 mr-2" />
                              Arrêter
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRestartServer(server.id)}
                            >
                              <RefreshCw className="w-4 h-4 mr-2" />
                              Redémarrer
                            </Button>
                          </>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStartServer(server.id)}
                          >
                            <Play className="w-4 h-4 mr-2" />
                            Démarrer
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteServer(server.id)}
                          className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Supprimer
                        </Button>
                      </div>

                      {/* Tools list */}
                      {server.tools.length > 0 && (
                        <div>
                          <p className="text-xs text-text-muted mb-2">Tools disponibles :</p>
                          <div className="space-y-1">
                            {server.tools.map((tool) => (
                              <div
                                key={tool.name}
                                className="flex items-start gap-2 p-2 bg-background/60 rounded-lg"
                              >
                                <Wrench className="w-3 h-3 text-accent-cyan mt-0.5 shrink-0" />
                                <div>
                                  <p className="text-xs font-medium text-text">{tool.name}</p>
                                  <p className="text-xs text-text-muted line-clamp-2">
                                    {tool.description}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      )}

      {/* Help text */}
      <p className="text-xs text-text-muted">
        Les serveurs MCP permettent d'ajouter des outils externes à THÉRÈSE (filesystem, web, APIs...).{' '}
        <a
          href="https://modelcontextprotocol.io"
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent-cyan hover:underline"
        >
          En savoir plus
        </a>
      </p>

      {/* EnvVar Configuration Modal */}
      <AnimatePresence>
        {presetToConfig && (
          <EnvVarModal
            preset={presetToConfig}
            onSubmit={handleEnvVarSubmit}
            onCancel={() => setPresetToConfig(null)}
          />
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {serverToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setServerToDelete(null)}
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative bg-surface border border-border rounded-xl p-6 max-w-md w-full shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                  <AlertCircle className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-text">Supprimer ce serveur MCP ?</h3>
                  <p className="text-sm text-text-muted">Cette action est irréversible.</p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 mt-6">
                <Button variant="ghost" size="sm" onClick={() => setServerToDelete(null)}>
                  Annuler
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={confirmDelete}
                  className="bg-red-500 hover:bg-red-600"
                >
                  Supprimer
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
