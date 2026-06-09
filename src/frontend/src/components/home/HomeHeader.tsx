/**
 * THÉRÈSE v2 - HomeHeader : salutation + date FR + badges honnêtes.
 * Badge fournisseur = provider/modèle RÉELLEMENT actif (getLLMConfig), pas codé en dur.
 */
import { useEffect, useState } from 'react';
import { ShieldCheck, Cpu } from 'lucide-react';
import { getLLMConfig } from '../../services/api/config';

const PROVIDER_LABEL: Record<string, string> = {
  anthropic: 'Claude',
  openai: 'OpenAI',
  gemini: 'Gemini',
  mistral: 'Mistral',
  grok: 'Grok',
  openrouter: 'OpenRouter',
  perplexity: 'Perplexity',
  deepseek: 'DeepSeek',
  infomaniak: 'Infomaniak',
  ollama: 'Ollama',
};

export function HomeHeader() {
  const [provider, setProvider] = useState<{ label: string; model: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    getLLMConfig()
      .then((cfg) => {
        if (cancelled) return;
        setProvider({ label: PROVIDER_LABEL[cfg.provider] ?? cfg.provider, model: cfg.model });
      })
      .catch(() => {
        /* badge masqué si indisponible (honnêteté : pas de valeur inventée) */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Bonjour' : now.getHours() < 18 ? 'Bon après-midi' : 'Bonsoir';
  const dateStr = now.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="flex items-start gap-4 flex-wrap">
      <div>
        <h1 className="text-[26px] font-extrabold tracking-tight leading-tight text-text">
          {greeting} <span className="text-accent">!</span>
        </h1>
        <p className="text-sm text-text-muted mt-1.5 first-letter:capitalize">{dateStr}</p>
      </div>
      <div className="ml-auto flex gap-2 flex-wrap">
        <span
          className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-full text-[12.5px] font-medium bg-surface border text-accent"
          style={{ borderColor: 'color-mix(in srgb, var(--color-accent) 45%, transparent)' }}
        >
          <ShieldCheck className="w-3.5 h-3.5" /> Données locales
        </span>
        {provider && (
          <span className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-full text-[12.5px] font-medium bg-surface border border-border text-text-muted">
            <Cpu className="w-3.5 h-3.5" /> {provider.label}
            <span className="text-text-muted/70">· {provider.model}</span>
          </span>
        )}
      </div>
    </div>
  );
}
