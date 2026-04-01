/**
 * THERESE v2 - Agent Catalog
 *
 * Grille 2x3 des agents metier preconfigures.
 * Charge les profils depuis GET /api/agents/profiles.
 * Clic sur un agent → callback onSelectAgent(profileId).
 */

import { useEffect, useState } from "react";
import { Bot, Loader2, AlertCircle, Brain } from "lucide-react";
import { motion } from "framer-motion";
import { getAgentProfiles, getAgentConfig } from "../../services/api/agents";
import type { AgentProfile, AgentModelInfo } from "../../services/api/agents";

/** Couleurs par ID agent (fallback si le backend ne les fournit pas) */
const COLOR_MAP: Record<string, { border: string; bg: string; text: string }> = {
  cyan: {
    border: "border-cyan-500/30",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
  },
  magenta: {
    border: "border-pink-500/30",
    bg: "bg-pink-500/10",
    text: "text-pink-400",
  },
  blue: {
    border: "border-blue-500/30",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
  },
  green: {
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
  },
  purple: {
    border: "border-purple-500/30",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
  },
  amber: {
    border: "border-amber-500/30",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
  },
};

const DEFAULT_COLOR = {
  border: "border-white/10",
  bg: "bg-white/5",
  text: "text-[#B6C7DA]",
};

/** Profils par defaut si le backend ne repond pas */
const FALLBACK_PROFILES: AgentProfile[] = [
  {
    id: "researcher",
    name: "Chercheur Web",
    description: "Recherche, synthese et veille sur le web",
    icon: "\uD83D\uDD0D",
    color: "cyan",
    tools: ["web_search", "read_file", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
  {
    id: "writer",
    name: "Redacteur",
    description: "Redaction, reformulation et correction de textes",
    icon: "\u270D\uFE0F",
    color: "magenta",
    tools: ["read_file", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
  {
    id: "analyst",
    name: "Analyste",
    description: "Analyse de donnees, code et documents",
    icon: "\uD83D\uDCCA",
    color: "blue",
    tools: ["read_file", "search_codebase", "run_command"],
    default_model: "claude-sonnet-4-6",
  },
  {
    id: "planner",
    name: "Planificateur",
    description: "Organisation, planning et suivi de projets",
    icon: "\uD83D\uDCC5",
    color: "green",
    tools: ["read_file", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
  {
    id: "coder",
    name: "Codeur",
    description: "Developpement, debug et refactoring",
    icon: "\uD83D\uDCBB",
    color: "purple",
    tools: ["read_file", "write_file", "search_codebase", "run_command", "git_status"],
    default_model: "claude-sonnet-4-6",
  },
  {
    id: "creative",
    name: "Creatif",
    description: "Brainstorming, ideation et contenus visuels",
    icon: "\uD83C\uDFA8",
    color: "amber",
    tools: ["web_search", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
];

const STORAGE_KEY = "therese-agent-model";

interface Props {
  onSelectAgent: (profileId: string, model?: string) => void;
}

export function AgentCatalog({ onSelectAgent }: Props) {
  const [profiles, setProfiles] = useState<AgentProfile[]>([]);
  const [availableModels, setAvailableModels] = useState<AgentModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>(() =>
    localStorage.getItem(STORAGE_KEY) || "",
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProfiles() {
      try {
        const [profilesData, configResp] = await Promise.all([
          getAgentProfiles(),
          getAgentConfig().catch(() => null),
        ]);
        if (!cancelled) {
          setProfiles(profilesData);
          if (configResp?.available_models) {
            setAvailableModels(configResp.available_models);
          }
          // Si pas de modele selectionne, utiliser le defaut du profil
          if (!selectedModel && profilesData[0]?.default_model) {
            const defaultModel = profilesData[0].default_model;
            setSelectedModel(defaultModel);
            localStorage.setItem(STORAGE_KEY, defaultModel);
          }
          setError(null);
        }
      } catch {
        if (!cancelled) {
          setProfiles(FALLBACK_PROFILES);
          setError(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadProfiles();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3">
        <Loader2 size={24} className="animate-spin text-[#6B7280]" />
        <p className="text-xs text-[#6B7280]">Chargement des agents...</p>
      </div>
    );
  }

  if (error && profiles.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <AlertCircle size={24} className="text-red-400/60" />
        <p className="text-xs text-red-400/80">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto px-4 py-6">
      {/* Header */}
      <div className="mb-5 text-center">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10">
          <Bot size={20} className="text-cyan-400" />
        </div>
        <h3 className="mb-1 text-sm font-semibold text-[#E6EDF7]">
          Choisis un agent
        </h3>
        <p className="text-xs text-[#6B7280]">
          Chaque agent est specialise dans un domaine. Selectionne celui qui correspond a ta tache.
        </p>
      </div>

      {/* Selecteur de modele LLM */}
      {availableModels.length > 0 && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-white/5 bg-[#131B35] px-3 py-2">
          <Brain size={14} className="shrink-0 text-cyan-400" />
          <select
            value={selectedModel}
            onChange={(e) => {
              setSelectedModel(e.target.value);
              localStorage.setItem(STORAGE_KEY, e.target.value);
            }}
            className="flex-1 bg-transparent text-xs text-[#E6EDF7] outline-none [&>optgroup]:bg-[#131B35] [&>option]:bg-[#131B35]"
          >
            {Object.entries(
              availableModels.reduce<Record<string, AgentModelInfo[]>>((acc, m) => {
                (acc[m.provider] ??= []).push(m);
                return acc;
              }, {}),
            ).map(([provider, models]) => (
              <optgroup key={provider} label={provider}>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
      )}

      {/* Grille 2x3 */}
      <div className="grid grid-cols-2 gap-3">
        {profiles.map((profile, index) => {
          const colors = COLOR_MAP[profile.color] || DEFAULT_COLOR;

          return (
            <motion.button
              key={profile.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: index * 0.06 }}
              onClick={() => onSelectAgent(profile.id, selectedModel || undefined)}
              className={`group flex flex-col items-center gap-2 rounded-xl border ${colors.border} bg-[#131B35] p-4 text-center transition-all hover:border-cyan-400/50 hover:bg-[#1a2340]`}
            >
              {/* Icone */}
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-lg ${colors.bg} text-lg transition-transform group-hover:scale-110`}
              >
                {profile.icon}
              </div>

              {/* Nom */}
              <span className={`text-xs font-semibold ${colors.text}`}>
                {profile.name}
              </span>

              {/* Description */}
              <span className="text-[10px] leading-snug text-[#6B7280]">
                {profile.description}
              </span>

              {/* Nombre d'outils */}
              <span className="mt-auto text-[9px] text-[#6B7280]/60">
                {profile.tools.length} outil{profile.tools.length > 1 ? "s" : ""}
              </span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
