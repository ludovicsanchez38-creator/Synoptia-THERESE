/**
 * THERESE v2 - Create Command Form
 *
 * Formulaire de creation de commande utilisateur personnalisee.
 * Style identique a DynamicSkillForm.
 */

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';

interface CreateCommandFormProps {
  onSubmit: (data: {
    name: string;
    description: string;
    category: string;
    icon: string;
    show_on_home: boolean;
    content: string;
  }) => Promise<void>;
  onBack: () => void;
  initialContent?: string;
  initialDescription?: string;
  capturedPreview?: string;
}

const CATEGORY_OPTIONS = [
  'general',
  'production',
  'analyse',
  'organisation',
  'communication',
  'autre',
];

export function CreateCommandForm({ onSubmit, onBack, initialContent, initialDescription, capturedPreview }: CreateCommandFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState(initialDescription || '');
  const [category, setCategory] = useState('general');
  const [icon, setIcon] = useState('');
  const [showOnHome, setShowOnHome] = useState(true);
  const [content, setContent] = useState(initialContent || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValid = name.trim().length > 0 && content.trim().length > 0;

  const handleSubmit = useCallback(async () => {
    if (!isValid || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      // Slugify le nom
      const slug = name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');

      await onSubmit({
        name: slug,
        description,
        category,
        icon,
        show_on_home: showOnHome,
        content,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la creation');
    } finally {
      setIsSubmitting(false);
    }
  }, [name, description, category, icon, showOnHome, content, isValid, isSubmitting, onSubmit]);

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
      className="w-full max-w-lg"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={onBack}
          className="flex items-center justify-center w-8 h-8 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 text-text-muted hover:text-text transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h3 className="text-lg font-semibold text-text">Creer une commande</h3>
          <p className="text-xs text-text-muted">Definis un raccourci personnalise pour THERESE</p>
        </div>
      </div>

      {/* Form */}
      <div className="space-y-4">
        {/* Nom */}
        <div>
          <label htmlFor="cmd-name" className="block text-sm font-medium text-text mb-1">
            Nom *
          </label>
          <input
            id="cmd-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ex: brief-client"
            className={cn(
              'w-full px-3 py-2 rounded-lg text-sm',
              'bg-surface-elevated border border-border text-text',
              'placeholder:text-text-muted/50',
              'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30 focus:border-accent-cyan/50'
            )}
          />
          {name && (
            <p className="text-xs text-text-muted mt-1">
              Slug : /{name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}
            </p>
          )}
        </div>

        {/* Description */}
        <div>
          <label htmlFor="cmd-desc" className="block text-sm font-medium text-text mb-1">
            Description
          </label>
          <input
            id="cmd-desc"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Ex: Genere un brief pour un nouveau client"
            className={cn(
              'w-full px-3 py-2 rounded-lg text-sm',
              'bg-surface-elevated border border-border text-text',
              'placeholder:text-text-muted/50',
              'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30 focus:border-accent-cyan/50'
            )}
          />
        </div>

        {/* Aperçu de la réponse capturée */}
        {capturedPreview && (
          <div className="px-3 py-2 rounded-lg bg-accent-cyan/5 border border-accent-cyan/20">
            <p className="text-xs font-medium text-accent-cyan mb-1">Réponse capturée</p>
            <p className="text-xs text-text-muted line-clamp-4">{capturedPreview}</p>
          </div>
        )}

        {/* Categorie + Icon */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="cmd-category" className="block text-sm font-medium text-text mb-1">
              Categorie
            </label>
            <select
              id="cmd-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={cn(
                'w-full px-3 py-2 rounded-lg text-sm',
                'bg-surface-elevated border border-border text-text',
                'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30 focus:border-accent-cyan/50'
              )}
            >
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt.charAt(0).toUpperCase() + opt.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="cmd-icon" className="block text-sm font-medium text-text mb-1">
              Icone (emoji)
            </label>
            <input
              id="cmd-icon"
              type="text"
              value={icon}
              onChange={(e) => setIcon(e.target.value)}
              placeholder="Ex: />"
              maxLength={4}
              className={cn(
                'w-full px-3 py-2 rounded-lg text-sm',
                'bg-surface-elevated border border-border text-text',
                'placeholder:text-text-muted/50',
                'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30 focus:border-accent-cyan/50'
              )}
            />
          </div>
        </div>

        {/* Show on home */}
        <div className="flex items-center gap-3">
          <input
            id="cmd-home"
            type="checkbox"
            checked={showOnHome}
            onChange={(e) => setShowOnHome(e.target.checked)}
            className="w-4 h-4 rounded border-border bg-surface-elevated text-accent-cyan focus:ring-accent-cyan/30"
          />
          <label htmlFor="cmd-home" className="text-sm text-text">
            Afficher sur la page d'accueil
          </label>
        </div>

        {/* Contenu / Prompt */}
        <div>
          <label htmlFor="cmd-content" className="block text-sm font-medium text-text mb-1">
            Prompt / Contenu *
          </label>
          <textarea
            id="cmd-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Ecris le prompt que THERESE utilisera quand cette commande sera declenchee..."
            rows={6}
            className={cn(
              'w-full px-3 py-2 rounded-lg text-sm resize-none',
              'bg-surface-elevated border border-border text-text',
              'placeholder:text-text-muted/50',
              'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30 focus:border-accent-cyan/50'
            )}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="px-3 py-2 rounded-lg bg-error/10 border border-error/20 text-sm text-error">
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="ghost" onClick={onBack} disabled={isSubmitting}>
            Annuler
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Sauvegarder
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
