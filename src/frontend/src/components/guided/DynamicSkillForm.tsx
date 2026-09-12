/**
 * THÉRÈSE v2 - Dynamic Skill Form
 *
 * Génère dynamiquement un formulaire basé sur le schéma d'un skill.
 */

import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import { FormField } from '../ui/FormField';

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
      <div className="flex flex-wrap items-center gap-3 mb-6 pb-4 border-b border-border">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onBack}
          disabled={isSubmitting}
          aria-label="Retour"
        >
          <ArrowLeft className="w-5 h-5 text-text-muted" />
        </Button>
        <div>
          <h3 className="text-lg font-semibold text-text">{skillName}</h3>
          <p className="text-sm text-text-muted">Remplis les champs ci-dessous</p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
        {/* px-2 et non pr-2 : la marge n'existait qu'à DROITE. Un champ en
              w-full touchait donc le bord gauche, et son anneau de focus, qui
              se dessine À L'EXTÉRIEUR de l'élément, était rogné — overflow-y
              rend l'axe horizontal découpant lui aussi. Signalé par Ludo le
              30/08/2026 : « le cadre de saisie est tronqué à gauche ». */}
          <div className="flex-1 overflow-y-auto space-y-5 px-2">
          {Object.entries(schema).map(([key, field]) => (
            <FormField
              key={key}
              label={field.label}
              htmlFor={`field-${key}`}
              required={field.required}
              description={field.help_text || undefined}
            >

              {/* Text input */}
              {field.type === 'text' && (
                <Input
                  id={`field-${key}`}
                  type="text"
                  value={inputs[key] || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  placeholder={field.placeholder}
                  disabled={isSubmitting}
                />
              )}

              {/* Textarea */}
              {field.type === 'textarea' && (
                <Textarea
                  id={`field-${key}`}
                  value={inputs[key] || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  placeholder={field.placeholder}
                  rows={4}
                  disabled={isSubmitting}
                  className="min-h-[100px] resize-y"
                />
              )}

              {/* Select */}
              {field.type === 'select' && (
                <Select
                  id={`field-${key}`}
                  value={inputs[key] || field.default || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  disabled={isSubmitting}
                  placeholder={!field.required ? '-- Choisir --' : undefined}
                  options={(field.options || []).map((opt) => ({ value: opt, label: opt }))}
                />
              )}

              {/* Number input */}
              {field.type === 'number' && (
                <Input
                  id={`field-${key}`}
                  type="number"
                  value={inputs[key] || ''}
                  onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
                  placeholder={field.placeholder}
                  disabled={isSubmitting}
                />
              )}

            </FormField>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="flex flex-wrap gap-3 mt-6 pt-4 border-t border-border">
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
                <Spinner taille="bouton" className="mr-2" />
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
