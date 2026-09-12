/**
 * THERESE v2 - Create Command Form
 *
 * Formulaire de creation de commande utilisateur personnalisee.
 * Style identique a DynamicSkillForm.
 */

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Save } from 'lucide-react';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import { FormField } from '../ui/FormField';
import { Alerte } from '../ui/Alerte';
import { slugDeCommande } from '../../lib/slugDeCommande';

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
      const slug = slugDeCommande(name);

      await onSubmit({
        name: slug,
        description,
        category,
        icon,
        show_on_home: showOnHome,
        content,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création');
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
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onBack}
          aria-label="Retour"
          title="Retour"
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h3 className="text-lg font-semibold text-text">Créer une commande</h3>
          <p className="text-xs text-text-muted">Définis un raccourci personnalisé pour THÉRÈSE</p>
        </div>
      </div>

      {/* Form */}
      <div className="space-y-4">
        {/* Nom */}
        <FormField label="Nom" htmlFor="cmd-name" required>
          <Input
            id="cmd-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ex: brief-client"
          />
          {name && (
            <p className="text-xs text-text-muted mt-1">
              Slug : /{slugDeCommande(name)}
            </p>
          )}
        </FormField>

        {/* Description */}
        <FormField label="Description" htmlFor="cmd-desc">
          <Input
            id="cmd-desc"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Ex : Génère un brief pour un nouveau client"
          />
        </FormField>

        {/* Aperçu de la réponse capturée */}
        {capturedPreview && (
          <div className="rounded-md border border-info/30 bg-[var(--color-info-tint)] px-3 py-2">
            <p className="mb-1 text-sm font-medium text-info">Réponse capturée</p>
            <p className="line-clamp-4 text-sm text-text-muted">{capturedPreview}</p>
          </div>
        )}

        {/* Catégorie + Icon */}
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Catégorie" htmlFor="cmd-category">
            <Select
              id="cmd-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              options={CATEGORY_OPTIONS.map((opt) => ({
                value: opt,
                label: opt.charAt(0).toUpperCase() + opt.slice(1),
              }))}
            />
          </FormField>
          <FormField label="Icône (emoji)" htmlFor="cmd-icon">
            <Input
              id="cmd-icon"
              type="text"
              value={icon}
              onChange={(e) => setIcon(e.target.value)}
              placeholder="Ex: />"
              maxLength={4}
            />
          </FormField>
        </div>

        {/* Show on home */}
        <div className="flex items-center gap-3">
          <Input
            id="cmd-home"
            type="checkbox"
            checked={showOnHome}
            onChange={(e) => setShowOnHome(e.target.checked)}
            className="h-4 min-h-4 w-4 p-0"
          />
          <label htmlFor="cmd-home" className="text-sm text-text">
            Afficher sur la page d'accueil
          </label>
        </div>

        {/* Contenu / Prompt */}
        <FormField label="Prompt / Contenu" htmlFor="cmd-content" required>
          <Textarea
            id="cmd-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Écris le prompt que THÉRÈSE utilisera quand cette commande sera déclenchée..."
            rows={6}
            className="resize-none"
          />
        </FormField>

        {/* Error */}
        {error && (
          <Alerte titre="Commande non enregistrée">{error}</Alerte>
        )}

        {/* Submit */}
        <div className="flex flex-wrap justify-end gap-3 pt-2">
          <Button variant="ghost" onClick={onBack} disabled={isSubmitting}>
            Annuler
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? (
              <Spinner taille="bouton" className="mr-2" />
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
