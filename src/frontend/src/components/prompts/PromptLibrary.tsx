/**
 * TH\u00c9R\u00c8SE - Biblioth\u00e8que de prompts pr\u00eats \u00e0 l'emploi
 *
 * Affiche les prompts class\u00e9s par cat\u00e9gorie avec accord\u00e9ons,
 * recherche et insertion dans le ChatInput.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, ChevronRight, X, ArrowLeft, Copy, Check } from 'lucide-react';
import { Button } from '../ui/Button';
import {
  getPromptLibrary,
  searchPromptLibrary,
  type PromptCategory,
  type PromptItem,
} from '../../services/api';
// SVG inline pour les ic\u00f4nes de cat\u00e9gories (jamais d'emoji)
const CATEGORY_ICONS: Record<string, React.JSX.Element> = {
  email: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <polyline points="22,7 12,13 2,7" />
    </svg>
  ),
  commercial: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <line x1="12" y1="1" x2="12" y2="23" />
      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </svg>
  ),
  admin: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14,2 14,8 20,8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10,9 9,9 8,9" />
    </svg>
  ),
  redaction: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  ),
  organisation: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
  juridique: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </svg>
  ),
};

/**
 * Surligne les placeholders {xxx} dans un texte de prompt.
 */
function HighlightedPrompt({ text }: { text: string }) {
  const parts = text.split(/(\{[^}]+\})/g);
  return (
    <span>
      {parts.map((part, i) =>
        part.startsWith('{') && part.endsWith('}') ? (
          <span
            key={i}
            className="inline-block bg-accent-cyan/20 text-accent-cyan px-1 rounded font-medium"
          >
            {part}
          </span>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
}

/**
 * Carte d'un prompt individuel.
 */
function PromptCard({
  prompt,
  onSelect,
}: {
  prompt: PromptItem;
  onSelect: (prompt: PromptItem) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      navigator.clipboard.writeText(prompt.prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    },
    [prompt.prompt]
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="group bg-[#131B35] border border-border/30 rounded-lg p-4 hover:border-accent-cyan/30 hover:shadow-[0_0_15px_rgba(34,211,238,0.08)] transition-all duration-200 cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-text truncate">{prompt.title}</h4>
          <p className="text-xs text-text-muted mt-1 line-clamp-2">{prompt.description}</p>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-md text-text-muted hover:text-accent-cyan hover:bg-accent-cyan/10 transition-colors opacity-0 group-hover:opacity-100"
            title="Copier le prompt"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          </button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onSelect(prompt);
            }}
            className="text-xs text-accent-cyan hover:bg-accent-cyan/10 opacity-0 group-hover:opacity-100"
          >
            Utiliser
          </Button>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mt-2">
        {prompt.tags.slice(0, 4).map((tag) => (
          <span
            key={tag}
            className="text-[10px] px-1.5 py-0.5 rounded bg-surface/50 text-text-muted border border-border/20"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Contenu expandable */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-3 pt-3 border-t border-border/20">
              <p className="text-xs text-text-muted leading-relaxed whitespace-pre-line">
                <HighlightedPrompt text={prompt.prompt} />
              </p>
              <Button
                variant="primary"
                size="sm"
                className="mt-3 w-full"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(prompt);
                }}
              >
                Ins\u00e9rer dans le chat
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/**
 * Accord\u00e9on de cat\u00e9gorie.
 */
function CategoryAccordion({
  category,
  onSelectPrompt,
  defaultOpen,
}: {
  category: PromptCategory;
  onSelectPrompt: (prompt: PromptItem) => void;
  defaultOpen: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-border/20 rounded-xl overflow-hidden bg-[#0B1226]/80">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-surface/30 transition-colors text-left"
      >
        <span className="text-accent-cyan">
          {CATEGORY_ICONS[category.category] || CATEGORY_ICONS.email}
        </span>
        <span className="flex-1 font-medium text-sm text-text">{category.label}</span>
        <span className="text-xs text-text-muted mr-2">{category.prompts.length}</span>
        {isOpen ? (
          <ChevronDown className="w-4 h-4 text-text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-text-muted" />
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 grid gap-3">
              {category.prompts.map((prompt) => (
                <PromptCard
                  key={prompt.id}
                  prompt={prompt}
                  onSelect={onSelectPrompt}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Composant principal : Biblioth\u00e8que de prompts.
 */
export interface PromptLibraryProps {
  /** Appel\u00e9 quand l'utilisateur s\u00e9lectionne un prompt. */
  onSelectPrompt: (promptText: string) => void;
  /** Appel\u00e9 pour fermer la biblioth\u00e8que. */
  onClose: () => void;
}

export function PromptLibrary({ onSelectPrompt, onClose }: PromptLibraryProps) {
  const [categories, setCategories] = useState<PromptCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PromptCategory[] | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Chargement initial
  useEffect(() => {
    getPromptLibrary()
      .then((data) => {
        setCategories(data.categories);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Impossible de charger la biblioth\u00e8que');
        setLoading(false);
      });
  }, []);

  // Focus automatique sur la recherche
  useEffect(() => {
    if (!loading) {
      searchInputRef.current?.focus();
    }
  }, [loading]);

  // Recherche debounced
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!value.trim()) {
      setSearchResults(null);
      setTotalResults(0);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const data = await searchPromptLibrary(value.trim());
        setSearchResults(data.categories);
        setTotalResults(data.total);
      } catch {
        // Silently fail - keep showing previous results
      }
    }, 300);
  }, []);

  // S\u00e9lection d'un prompt
  const handleSelect = useCallback(
    (prompt: PromptItem) => {
      onSelectPrompt(prompt.prompt);
      onClose();
    },
    [onSelectPrompt, onClose]
  );

  const displayedCategories = searchResults !== null ? searchResults : categories;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col h-full bg-[#0B1226]"
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-border/30">
        <button
          onClick={onClose}
          className="p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface/50 transition-colors"
          title="Retour"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-text">Biblioth\u00e8que de prompts</h2>
          <p className="text-xs text-text-muted mt-0.5">
            {loading
              ? 'Chargement...'
              : searchResults !== null
                ? `${totalResults} r\u00e9sultat${totalResults !== 1 ? 's' : ''} pour "${searchQuery}"`
                : `${categories.reduce((acc, c) => acc + c.prompts.length, 0)} prompts pr\u00eats \u00e0 l'emploi`}
          </p>
        </div>
      </div>

      {/* Barre de recherche */}
      <div className="px-5 py-3 border-b border-border/20">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Rechercher un prompt (ex : relance, LinkedIn, CGV...)"
            className="w-full pl-10 pr-10 py-2.5 bg-surface/50 border border-border/30 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 focus:ring-1 focus:ring-accent-cyan/20 transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => handleSearchChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded text-text-muted hover:text-text transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Contenu */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-6 h-6 border-2 border-accent-cyan/30 border-t-accent-cyan rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-sm text-error">{error}</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              R\u00e9essayer
            </Button>
          </div>
        ) : displayedCategories.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-sm text-text-muted">
              Aucun prompt trouv\u00e9 pour "{searchQuery}"
            </p>
            <p className="text-xs text-text-muted/60 mt-1">
              Essaie avec d'autres mots-cl\u00e9s
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {displayedCategories.map((category, index) => (
              <CategoryAccordion
                key={category.category}
                category={category}
                onSelectPrompt={handleSelect}
                defaultOpen={searchResults !== null || index === 0}
              />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
