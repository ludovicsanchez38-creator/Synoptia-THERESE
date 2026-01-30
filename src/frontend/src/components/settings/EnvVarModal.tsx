import { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff, ExternalLink, AlertCircle, Check } from 'lucide-react';
import { Button } from '../ui/Button';

interface PresetMCP {
  id: string;
  name: string;
  description: string;
  env_required?: string[];
}

interface EnvVarModalProps {
  preset: PresetMCP;
  onSubmit: (envVars: Record<string, string>) => void;
  onCancel: () => void;
}

// Configuration de validation par variable d'environnement
const ENV_VAR_CONFIG: Record<string, {
  prefix?: string;
  consoleUrl: string;
  label: string;
}> = {
  GITHUB_TOKEN: {
    prefix: 'ghp_',
    consoleUrl: 'https://github.com/settings/tokens',
    label: 'GitHub Personal Access Token',
  },
  SLACK_BOT_TOKEN: {
    prefix: 'xoxb-',
    consoleUrl: 'https://api.slack.com/apps',
    label: 'Slack Bot Token',
  },
  NOTION_API_KEY: {
    prefix: 'secret_',
    consoleUrl: 'https://www.notion.so/my-integrations',
    label: 'Notion Integration Token',
  },
  AIRTABLE_API_KEY: {
    prefix: 'pat',
    consoleUrl: 'https://airtable.com/create/tokens',
    label: 'Airtable Personal Access Token',
  },
  ZAPIER_API_KEY: {
    consoleUrl: 'https://zapier.com/app/developer',
    label: 'Zapier API Key',
  },
  MAKE_API_KEY: {
    consoleUrl: 'https://www.make.com/en/api-documentation',
    label: 'Make API Key',
  },
  LINEAR_API_KEY: {
    consoleUrl: 'https://linear.app/settings/api',
    label: 'Linear API Key',
  },
  GOOGLE_OAUTH_CLIENT_ID: {
    consoleUrl: 'https://console.cloud.google.com/apis/credentials',
    label: 'Google OAuth Client ID',
  },
  GOOGLE_OAUTH_CLIENT_SECRET: {
    consoleUrl: 'https://console.cloud.google.com/apis/credentials',
    label: 'Google OAuth Client Secret',
  },
};

export function EnvVarModal({ preset, onSubmit, onCancel }: EnvVarModalProps) {
  const [envVars, setEnvVars] = useState<Record<string, string>>({});
  const [showValues, setShowValues] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const envRequired = preset.env_required || [];

  // Vérifier si toutes les clés sont renseignées et valides
  const isValid = envRequired.every((envVar) => {
    const value = envVars[envVar];
    if (!value) return false;

    // Validation du préfixe si configuré
    const config = ENV_VAR_CONFIG[envVar];
    if (config?.prefix && !value.startsWith(config.prefix)) {
      return false;
    }

    return true;
  });

  function handleValueChange(envVar: string, value: string) {
    setEnvVars((prev) => ({ ...prev, [envVar]: value }));

    // Validation en temps réel
    const config = ENV_VAR_CONFIG[envVar];
    if (config?.prefix && value && !value.startsWith(config.prefix)) {
      setErrors((prev) => ({
        ...prev,
        [envVar]: `Doit commencer par "${config.prefix}"`,
      }));
    } else {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[envVar];
        return newErrors;
      });
    }
  }

  function toggleShowValue(envVar: string) {
    setShowValues((prev) => ({ ...prev, [envVar]: !prev[envVar] }));
  }

  function handleSubmit() {
    if (isValid) {
      onSubmit(envVars);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-surface border border-border rounded-xl p-6 max-w-lg w-full shadow-2xl max-h-[80vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-text mb-1">
            Configuration {preset.name}
          </h3>
          <p className="text-sm text-text-muted">{preset.description}</p>
        </div>

        {/* Info */}
        <div className="flex items-start gap-3 p-3 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg mb-6">
          <AlertCircle className="w-5 h-5 text-accent-cyan shrink-0 mt-0.5" />
          <div className="text-sm text-text-muted">
            <p>Ce serveur nécessite des clés API pour fonctionner.</p>
            <p className="mt-1">Vos clés seront chiffrées et stockées localement.</p>
          </div>
        </div>

        {/* Env Vars Inputs */}
        <div className="space-y-4 mb-6">
          {envRequired.map((envVar) => {
            const config = ENV_VAR_CONFIG[envVar] || {
              consoleUrl: '',
              label: envVar,
            };
            const value = envVars[envVar] || '';
            const show = showValues[envVar] || false;
            const error = errors[envVar];
            const hasValue = !!value;
            const isValidValue = hasValue && !error;

            return (
              <div key={envVar}>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-text">
                    {config.label}
                  </label>
                  {config.consoleUrl && (
                    <a
                      href={config.consoleUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-accent-cyan hover:underline flex items-center gap-1"
                    >
                      Obtenir une clé
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>

                <div className="relative">
                  <input
                    type={show ? 'text' : 'password'}
                    value={value}
                    onChange={(e) => handleValueChange(envVar, e.target.value)}
                    placeholder={config.prefix ? `${config.prefix}...` : 'Entrez la clé API'}
                    className={`w-full px-3 py-2 pr-20 bg-background/60 border rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 ${
                      error
                        ? 'border-red-500/50 focus:ring-red-500/50'
                        : isValidValue
                        ? 'border-green-500/50 focus:ring-green-500/50'
                        : 'border-border/50 focus:ring-accent-cyan/50'
                    }`}
                  />

                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    {/* Indicateur de validation */}
                    {isValidValue && (
                      <Check className="w-4 h-4 text-green-400" />
                    )}
                    {error && (
                      <AlertCircle className="w-4 h-4 text-red-400" />
                    )}

                    {/* Toggle show/hide */}
                    {hasValue && (
                      <button
                        type="button"
                        onClick={() => toggleShowValue(envVar)}
                        className="p-1 hover:bg-border/30 rounded transition-colors"
                      >
                        {show ? (
                          <EyeOff className="w-4 h-4 text-text-muted" />
                        ) : (
                          <Eye className="w-4 h-4 text-text-muted" />
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* Error message */}
                {error && (
                  <p className="text-xs text-red-400 mt-1">{error}</p>
                )}

                {/* Hint */}
                {config.prefix && !error && (
                  <p className="text-xs text-text-muted mt-1">
                    Format attendu : {config.prefix}...
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-border/30">
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Annuler
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            disabled={!isValid}
          >
            Installer
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
