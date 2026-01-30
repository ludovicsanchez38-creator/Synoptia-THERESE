/**
 * THÉRÈSE v2 - Dynamic Skill Form
 *
 * Génère dynamiquement un formulaire basé sur le schéma d'un skill.
 */

import { motion } from 'framer-motion';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Button } from '../ui/Button';

/**
 * Types pour les champs de formulaire
 */
export interface InputField {
  type: 'text' | 'textarea' | 'select' | 'number' | 'file';
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
  default?: string | null;
  help_text?: string | null;
}

export interface SkillSchema {
  skill_id: string;
  output_type: 'text' | 'file' | 'analysis';
  schema: Record<string, InputField>;
}

interface DynamicSkillFormProps {
  skillName: string;
  schema: Record<string, InputField>;
  onSubmit: (inputs: Record<string, any>) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export function DynamicSkillForm({
  skillName,
  schema,
  onSubmit,
  onBack,
  isSubmitting = false,
}: DynamicSkillFormProps) {
  const [inputs, setInputs] = useState<Record<string, any>>(() => {
    // Initialiser avec les valeurs par défaut
    const initial: Record<string, any> = {};
    Object.entries(schema).forEach(([key, field]) => {
      if (field.default) {
        initial[key] = field.default;
      }
    });
    return initial;
  });

  // Validation : tous les champs requis doivent être remplis
  const isValid = useMemo(() => {
    return Object.entries(schema).every(([key, field]) => {
      if (!field.required) return true;
      const value = inputs[key];
      return value !== undefined && value !== '' && value !== null;
    });
  }, [inputs, schema]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isValid && !isSubmitting) {
      onSubmit(inputs);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
        <button
          onClick={onBack}
          disabled={isSubmitting}
          className="p-2 hover:bg-surface rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Retour"
        >
          <ArrowLeft className="w-5 h-5 text-muted" />
        </button>
        <div>
          <h3 className="text-lg font-semibold text-text">{skillName}</h3>
          <p className="text-sm text-muted">Remplis les champs ci-dessous</p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto space-y-5 pr-2">
          {Object.entries(schema).map(([key, field]) => (
            <div key={key}>
              <label
                htmlFor={`field-${key}`}
                className="block text-sm font-medium text-text mb-1.5"
              >
                {field.label}
                {field.required && <span className="text-red-400 ml-1">*</span>}
              </label>

              {/* Text input */}
              {field.type === 'text' && (
                <input
                  id={`field-${key}`}
                  type="text"
                  value={inputs[key] || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  placeholder={field.placeholder}
                  disabled={isSubmitting}
                  className="w-full px-3 py-2 bg-surface text-text rounded-lg border border-border focus:border-accent-cyan focus:ring-2 focus:ring-accent-cyan/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-describedby={field.help_text ? `help-${key}` : undefined}
                />
              )}

              {/* Textarea */}
              {field.type === 'textarea' && (
                <textarea
                  id={`field-${key}`}
                  value={inputs[key] || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  placeholder={field.placeholder}
                  rows={4}
                  disabled={isSubmitting}
                  className="w-full px-3 py-2 bg-surface text-text rounded-lg border border-border focus:border-accent-cyan focus:ring-2 focus:ring-accent-cyan/20 transition-all resize-y min-h-[100px] disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-describedby={field.help_text ? `help-${key}` : undefined}
                />
              )}

              {/* Select */}
              {field.type === 'select' && (
                <select
                  id={`field-${key}`}
                  value={inputs[key] || field.default || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  disabled={isSubmitting}
                  className="w-full px-3 py-2 bg-surface text-text rounded-lg border border-border focus:border-accent-cyan focus:ring-2 focus:ring-accent-cyan/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-describedby={field.help_text ? `help-${key}` : undefined}
                >
                  {!field.required && <option value="">-- Choisir --</option>}
                  {field.options?.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              )}

              {/* Number input */}
              {field.type === 'number' && (
                <input
                  id={`field-${key}`}
                  type="number"
                  value={inputs[key] || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  placeholder={field.placeholder}
                  disabled={isSubmitting}
                  className="w-full px-3 py-2 bg-surface text-text rounded-lg border border-border focus:border-accent-cyan focus:ring-2 focus:ring-accent-cyan/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-describedby={field.help_text ? `help-${key}` : undefined}
                />
              )}

              {/* Help text */}
              {field.help_text && (
                <p id={`help-${key}`} className="mt-1.5 text-xs text-muted">
                  {field.help_text}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="flex gap-3 mt-6 pt-4 border-t border-border">
          <Button
            type="button"
            variant="secondary"
            onClick={onBack}
            disabled={isSubmitting}
          >
            Retour
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={!isValid || isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Génération...
              </>
            ) : (
              'Générer'
            )}
          </Button>
        </div>
      </form>
    </motion.div>
  );
}
