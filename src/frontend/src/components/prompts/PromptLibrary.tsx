/**
 * THÉRÈSE - Bibliothèque de prompts prêts à l'emploi
 *
 * Affiche les prompts classés par catégorie avec accordéons,
 * recherche et insertion dans le ChatInput.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, ChevronRight, X, ArrowLeft, Copy, Check } from 'lucide-react';
import { Alerte, Button, EtatVide, Etiquette, Input } from '../ui';
import { Spinner } from '../ui/Spinner';
import {
  getPromptLibrary,
  searchPromptLibrary,
  type PromptCategory,
  type PromptItem,
} from '../../services/api';
// SVG inline pour les icônes de catégories (jamais d'emoji)
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
            className="inline-block rounded-sm bg-accent-tint px-1 font-medium text-accent"
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
  const copieTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // B-068 : même règle pour le retour visuel de la copie.
  useEffect(() => () => {
    if (copieTimeoutRef.current) clearTimeout(copieTimeoutRef.current);
  }, []);

  const [copieEchouee, setCopieEchouee] = useState(false);
  const handleCopy = useCallback(
    async (e: React.MouseEvent) => {
      e.stopPropagation();
      if (copieTimeoutRef.current) clearTimeout(copieTimeoutRef.current);
      // Cycle 6 (Sophie, sophie-03) : la coche s'affichait même quand le
      // navigateur refusait l'écriture ; on attend le résultat et on le dit.
      try {
        await navigator.clipboard.writeText(prompt.prompt);
        setCopieEchouee(false);
        setCopied(true);
      } catch {
        setCopied(false);
        setCopieEchouee(true);
      }
      copieTimeoutRef.current = setTimeout(() => { setCopied(false); setCopieEchouee(false); }, 2000);
    },
    [prompt.prompt]
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="group cursor-pointer rounded-md border border-border bg-surface p-4 shadow-sm transition-colors hover:border-accent"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-text truncate">{prompt.title}</h4>
          <p className="text-xs text-text-muted mt-1 line-clamp-2">{prompt.description}</p>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleCopy}
            title="Copier le prompt"
            aria-label="Copier le prompt"
            data-copie={copied ? 'ok' : copieEchouee ? 'echec' : 'idle'}
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          </Button>
          {copieEchouee && (
            <span role="status" className="text-xs text-error">Copie impossible : le presse-papiers est refusé.</span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onSelect(prompt);
            }}
            className="text-sm"
          >
            Utiliser
          </Button>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mt-2">
        {prompt.tags.slice(0, 4).map((tag) => (
          <Etiquette key={tag}>{tag}</Etiquette>
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
                Insérer dans le chat
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/**
 * Accordéon de catégorie.
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
  // Cycle 6 (Sophie, sophie-02) : une recherche annonçait « 3 résultats » sans
  // en montrer un seul si la catégorie avait été repliée avant ; l'accordéon
  // suit désormais l'intention du parent quand elle change.
  useEffect(() => { setIsOpen(defaultOpen); }, [defaultOpen]);

  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface shadow-sm">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex min-h-11 w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-surface-2"
        aria-expanded={isOpen}
      >
        <span className="text-accent">
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
 * Composant principal : Bibliothèque de prompts.
 */
export interface PromptLibraryProps {
  /** Appelé quand l'utilisateur sélectionne un prompt. */
  onSelectPrompt: (promptText: string) => void;
  /** Appelé pour fermer la bibliothèque. */
  onClose: () => void;
}

export function PromptLibrary({ onSelectPrompt, onClose }: PromptLibraryProps) {
  const [categories, setCategories] = useState<PromptCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PromptCategory[] | null>(null);
  const [resultsQuery, setResultsQuery] = useState('');
  const [searchError, setSearchError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Chargement initial. B-474 : relançable depuis « Réessayer », qui
  // rechargeait toute la fenêtre.
  const chargerLaBibliotheque = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPromptLibrary();
      setCategories(data.categories);
    } catch (err) {
      setError((err as Error).message || 'Impossible de charger la bibliothèque');
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void chargerLaBibliotheque();
  }, [chargerLaBibliotheque]);

  // Focus automatique sur la recherche
  useEffect(() => {
    if (!loading) {
      searchInputRef.current?.focus();
    }
  }, [loading]);

  // B-068 : le minuteur de recherche meurt avec le panneau. Il n'était annulé
  // qu'à la frappe suivante : fermer la bibliothèque entre-temps laissait
  // l'échéance courir et searchPromptLibrary() partait pour un écran démonté.
  useEffect(() => () => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
  }, []);

  // Recherche debounced
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    setSearchError(null);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!value.trim()) {
      setSearchResults(null);
      setResultsQuery('');
      setTotalResults(0);
      setSearchError(null);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const data = await searchPromptLibrary(value.trim());
        setSearchResults(data.categories);
        setTotalResults(data.total);
        setResultsQuery(value.trim());
        setSearchError(null);
      } catch {
        // Revue 30/08 : garder les anciens résultats sous le nouveau
        // libellé faisait croire que la nouvelle requête avait abouti.
        setSearchResults(null);
        setTotalResults(0);
        setResultsQuery('');
        setSearchError('Recherche impossible pour le moment.');
      }
    }, 300);
  }, []);

  // Sélection d'un prompt
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
      className="flex h-full flex-col bg-bg"
    >
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-border px-5 py-4">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onClose}
          title="Retour"
          aria-label="Retour au chat"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-text">Bibliothèque de prompts</h2>
          <p className="text-xs text-text-muted mt-0.5">
            {loading
              ? 'Chargement...'
              : searchError
                ? 'Recherche impossible'
                : searchResults !== null
                  ? `${totalResults} résultat${totalResults !== 1 ? 's' : ''} pour "${resultsQuery}"`
                  : `${categories.reduce((acc, c) => acc + c.prompts.length, 0)} prompts prêts à l'emploi`}
          </p>
        </div>
      </div>

      {/* Barre de recherche */}
      <div className="border-b border-border px-5 py-3">
        <div className="relative">
          <Input aria-label="Rechercher un prompt"
            ref={searchInputRef}
            type="text"
            icon={<Search className="h-4 w-4" />}
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Rechercher un prompt (ex : relance, LinkedIn, CGV...)"
            className="pr-12"
          />
          {searchQuery && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => handleSearchChange('')}
              aria-label="Effacer la recherche"
              className="absolute right-1 top-1/2 -translate-y-1/2"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Contenu */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-12" role="status" aria-label="Chargement de la bibliothèque">
            <Spinner taille="zone" />
          </div>
        ) : searchError ? (
          <Alerte titre="Recherche impossible">{searchError}</Alerte>
        ) : error ? (
          <Alerte
            titre="Bibliothèque indisponible"
            action={<Button
              variant="secondary"
              size="sm"
              onClick={() => void chargerLaBibliotheque()}
            >
              Réessayer
            </Button>}
          >{error}</Alerte>
        ) : displayedCategories.length === 0 ? (
          <EtatVide titre={searchQuery.trim() ? `Aucun prompt trouvé pour « ${searchQuery} »` : 'Bibliothèque vide'}>{searchQuery.trim() ? 'Essaie avec d’autres mots-clés.' : 'La bibliothèque de prompts est vide ou indisponible.'}</EtatVide>
        ) : (
          <div className="grid gap-4">
            {displayedCategories.map((category, index) => (
              <CategoryAccordion
                // Cycle 6 (Sophie, sophie-02) : une nouvelle recherche remonte
                // l'accordéon, donc rouvre une catégorie repliée à la main.
                key={`${category.category}-${searchResults !== null ? searchQuery : ''}`}
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
