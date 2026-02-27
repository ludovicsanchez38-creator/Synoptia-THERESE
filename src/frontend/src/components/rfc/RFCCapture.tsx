/**
 * THÉRÈSE V3 - RFCCapture
 *
 * Formulaire pré-rempli pour la phase Capturer du workflow RFC.
 * L'utilisateur valide/modifie → sauvegarde la commande.
 */

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Save, ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';

interface RFCCaptureData {
  name: string;
  description: string;
  icon: string;
  category: string;
  prompt_template: string;
}

interface RFCCaptureProps {
  initialData: RFCCaptureData;
  onSave: (data: RFCCaptureData) => Promise<void>;
  onBack: () => void;
}

const CATEGORIES = [
  { value: 'production', label: 'Produire' },
  { value: 'analyse', label: 'Comprendre' },
  { value: 'organisation', label: 'Organiser' },
];

export function RFCCapture({ initialData, onSave, onBack }: RFCCaptureProps) {
  const [data, setData] = useState<RFCCaptureData>(initialData);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = useCallback(async () => {
    if (!data.name.trim()) {
      setError('Le nom est obligatoire');
      return;
    }
    if (!data.prompt_template.trim()) {
      setError('Le template est obligatoire');
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await onSave(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de sauvegarde');
    } finally {
      setIsSaving(false);
    }
  }, [data, onSave]);

  const updateField = (field: keyof RFCCaptureData, value: string) => {
    setData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="w-full max-w-lg space-y-4"
    >
      <div className="flex items-center gap-2 mb-4">
        <Button variant="ghost" size="icon" onClick={onBack} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h3 className="text-lg font-semibold text-text">Capturer la commande</h3>
      </div>

      {/* Nom */}
      <div>
        <label className="block text-xs font-medium text-text-muted mb-1">Nom (slug)</label>
        <input
          type="text"
          value={data.name}
          onChange={(e) => updateField('name', e.target.value.toLowerCase().replace(/\s+/g, '-'))}
          placeholder="mon-email-pro"
          className="w-full px-3 py-2 rounded-lg bg-surface-elevated text-text text-sm border border-border focus:border-accent-cyan/50 focus:outline-none"
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-xs font-medium text-text-muted mb-1">Description</label>
        <input
          type="text"
          value={data.description}
          onChange={(e) => updateField('description', e.target.value)}
          placeholder="Rédige un email pro avec mon style"
          className="w-full px-3 py-2 rounded-lg bg-surface-elevated text-text text-sm border border-border focus:border-accent-cyan/50 focus:outline-none"
        />
      </div>

      {/* Icône + Catégorie */}
      <div className="flex gap-3">
        <div className="w-20">
          <label className="block text-xs font-medium text-text-muted mb-1">Icône</label>
          <input
            type="text"
            value={data.icon}
            onChange={(e) => updateField('icon', e.target.value.slice(0, 4))}
            placeholder="📧"
            maxLength={4}
            className="w-full px-3 py-2 rounded-lg bg-surface-elevated text-text text-sm text-center border border-border focus:border-accent-cyan/50 focus:outline-none"
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-text-muted mb-1">Catégorie</label>
          <select
            value={data.category}
            onChange={(e) => updateField('category', e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-surface-elevated text-text text-sm border border-border focus:border-accent-cyan/50 focus:outline-none"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Template */}
      <div>
        <label className="block text-xs font-medium text-text-muted mb-1">
          Template de prompt <span className="text-text-muted/50">(utilise {'{{placeholders}}'} pour les variables)</span>
        </label>
        <textarea
          value={data.prompt_template}
          onChange={(e) => updateField('prompt_template', e.target.value)}
          placeholder="Rédige un email à {{destinataire}} à propos de {{sujet}}. Ton : {{ton}}."
          rows={5}
          className="w-full px-3 py-2 rounded-lg bg-surface-elevated text-text text-sm border border-border focus:border-accent-cyan/50 focus:outline-none resize-none leading-5"
        />
      </div>

      {/* Erreur */}
      {error && (
        <div className="px-3 py-2 rounded-lg bg-error/10 border border-error/20 text-sm text-error">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3 pt-2">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2"
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Sauvegarder
        </Button>
        <Button variant="ghost" onClick={onBack}>
          Annuler
        </Button>
      </div>
    </motion.div>
  );
}
