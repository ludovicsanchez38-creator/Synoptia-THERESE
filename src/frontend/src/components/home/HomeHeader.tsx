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
        {/* Tags carrés bordés encre (DA brutaliste) - finis les pills.
            Texte en --color-text (AA : l'accent cyan sur tint ne tient pas
            4,5:1 en clair), seule l'icône porte l'accent. */}
        <span className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-[6px] text-[12.5px] font-semibold bg-accent-tint border-[1.5px] border-[var(--btn-ink)] text-text">
          <ShieldCheck className="w-3.5 h-3.5 text-accent" /> Données locales
        </span>
        {provider && (
          <span className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-[6px] text-[12.5px] font-medium bg-surface border-[1.5px] border-border text-text-muted">
            <Cpu className="w-3.5 h-3.5" /> {provider.label}
            <span className="text-text-muted/70">· {provider.model}</span>
          </span>
        )}
      </div>
    </div>
  );
}
