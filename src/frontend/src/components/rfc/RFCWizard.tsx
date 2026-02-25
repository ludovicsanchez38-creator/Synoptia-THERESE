/**
 * THÉRÈSE V3 - RFCWizard
 *
 * Wizard 3 étapes : Réfléchir - Faire - Capturer
 * Pour créer des commandes personnalisées avec l'aide de THÉRÈSE.
 */

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight, Lightbulb, Wrench, Save } from 'lucide-react';
import { Button } from '../ui/Button';
import { RFCChat } from './RFCChat';
import { RFCCapture } from './RFCCapture';
import { useCommandsStore } from '../../stores/commandsStore';
import { generateTemplate } from '../../services/api/commands-v3';
import { cn } from '../../lib/utils';

type RFCStep = 'reflect' | 'make' | 'capture';

interface RFCMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface RFCWizardProps {
  onClose: () => void;
  /** Si fourni, reprend la modification d'une commande existante à l'étape Faire */
  editCommand?: {
    id: string;
    name: string;
    description: string;
    icon: string;
    category: string;
    prompt_template: string;
  };
}

const STEPS: { id: RFCStep; label: string; icon: typeof Lightbulb }[] = [
  { id: 'reflect', label: 'Réfléchir', icon: Lightbulb },
  { id: 'make', label: 'Faire', icon: Wrench },
  { id: 'capture', label: 'Capturer', icon: Save },
];

const REFLECT_SYSTEM_PROMPT = `Tu es un concepteur de commandes pour THÉRÈSE, une assistante IA pour entrepreneurs.
L'utilisateur veut créer une commande personnalisée. Aide-le à brainstormer :
- Quel est l'objectif de la commande ?
- Dans quel contexte sera-t-elle utilisée ?
- Quelles informations variables faut-il demander à l'utilisateur ?
Pose des questions pour bien comprendre le besoin. Sois concis et pratique.`;

const MAKE_SYSTEM_PROMPT = `Tu es un concepteur de commandes pour THÉRÈSE, une assistante IA.
L'utilisateur a brainstormé et veut maintenant créer sa commande.
Aide-le à rédiger un prompt template efficace avec des {{placeholders}}.
Propose une ébauche, puis itère avec l'utilisateur jusqu'à perfection.
Quand la commande est prête, résume-la clairement (nom, description, template).`;

export function RFCWizard({ onClose, editCommand }: RFCWizardProps) {
  const [step, setStep] = useState<RFCStep>(editCommand ? 'make' : 'reflect');
  const [reflectMessages, setReflectMessages] = useState<RFCMessage[]>([]);
  const [makeMessages, setMakeMessages] = useState<RFCMessage[]>([]);
  const [captureData, setCaptureData] = useState(editCommand || {
    name: '',
    description: '',
    icon: '',
    category: 'personnaliser',
    prompt_template: '',
  });
  const [isGenerating, setIsGenerating] = useState(false);

  const { createCommand, updateCommand } = useCommandsStore();

  const currentStepIndex = STEPS.findIndex((s) => s.id === step);

  const goToMake = useCallback(async () => {
    setStep('make');
  }, []);

  const goToCapture = useCallback(async () => {
    // Essayer de générer un template depuis la conversation
    setIsGenerating(true);
    try {
      const allMessages = [...reflectMessages, ...makeMessages];
      const brief = allMessages
        .map((m) => `${m.role}: ${m.content}`)
        .join('\n');

      const template = await generateTemplate({
        brief,
        context: allMessages.map((m) => ({ role: m.role, content: m.content })),
      });

      setCaptureData({
        name: template.name || captureData.name,
        description: template.description || captureData.description,
        icon: template.icon || captureData.icon,
        category: template.category || captureData.category,
        prompt_template: template.prompt_template || captureData.prompt_template,
      });
    } catch (err) {
      console.error('Failed to generate template:', err);
      // Pas grave, l'utilisateur remplira manuellement
    } finally {
      setIsGenerating(false);
      setStep('capture');
    }
  }, [reflectMessages, makeMessages, captureData]);

  const handleSave = useCallback(async (data: typeof captureData) => {
    if (editCommand) {
      await updateCommand(`user-${editCommand.name}`, {
        name: data.name,
        description: data.description,
        icon: data.icon,
        category: data.category,
        prompt_template: data.prompt_template,
        show_on_home: true,
        show_in_slash: true,
      });
    } else {
      await createCommand({
        name: data.name,
        description: data.description,
        icon: data.icon,
        category: data.category,
        prompt_template: data.prompt_template,
        show_on_home: true,
        show_in_slash: true,
      });
    }
    onClose();
  }, [editCommand, createCommand, updateCommand, onClose]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="w-full max-w-2xl mx-auto"
    >
      {/* Header avec stepper */}
      <div className="flex items-center justify-between mb-4">
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>

        <div className="flex items-center gap-2">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const isActive = s.id === step;
            const isPast = i < currentStepIndex;
            return (
              <div key={s.id} className="flex items-center gap-1">
                {i > 0 && (
                  <div className={cn('w-6 h-px', isPast ? 'bg-accent-cyan' : 'bg-border')} />
                )}
                <div
                  className={cn(
                    'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors',
                    isActive && 'bg-accent-cyan/15 text-accent-cyan',
                    isPast && 'text-accent-cyan/60',
                    !isActive && !isPast && 'text-text-muted',
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {s.label}
                </div>
              </div>
            );
          })}
        </div>

        <div className="w-8" /> {/* Spacer */}
      </div>

      {/* Contenu de l'étape */}
      <div className="bg-surface/60 border border-border rounded-xl overflow-hidden" style={{ height: '450px' }}>
        <AnimatePresence mode="wait">
          {step === 'reflect' && (
            <motion.div
              key="reflect"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full flex flex-col"
            >
              <div className="px-4 py-3 border-b border-border bg-surface-elevated/30">
                <h4 className="text-sm font-medium text-text">Réfléchir</h4>
                <p className="text-xs text-text-muted">Dis à THÉRÈSE ce que ta commande doit faire</p>
              </div>
              <div className="flex-1 overflow-hidden">
                <RFCChat
                  systemPrompt={REFLECT_SYSTEM_PROMPT}
                  placeholder="Décris ta commande idéale..."
                  onConversationUpdate={setReflectMessages}
                />
              </div>
              <div className="px-4 py-3 border-t border-border flex justify-end">
                <Button
                  variant="primary"
                  onClick={goToMake}
                  disabled={reflectMessages.length === 0}
                  className="flex items-center gap-2 text-sm"
                >
                  Passer à Faire
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          )}

          {step === 'make' && (
            <motion.div
              key="make"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="h-full flex flex-col"
            >
              <div className="px-4 py-3 border-b border-border bg-surface-elevated/30">
                <h4 className="text-sm font-medium text-text">Faire</h4>
                <p className="text-xs text-text-muted">THÉRÈSE t'aide à construire le prompt template</p>
              </div>
              <div className="flex-1 overflow-hidden">
                <RFCChat
                  systemPrompt={MAKE_SYSTEM_PROMPT}
                  placeholder="Itère sur le template..."
                  initialMessage={
                    editCommand
                      ? `Je veux modifier ma commande "${editCommand.name}". Voici le template actuel :\n\n${editCommand.prompt_template}`
                      : reflectMessages.length > 0
                        ? `Voici le résumé de notre réflexion :\n\n${reflectMessages.map((m) => `${m.role === 'user' ? 'Moi' : 'THÉRÈSE'}: ${m.content}`).join('\n\n')}\n\nMaintenant, génère-moi une ébauche de prompt template avec des {{placeholders}}.`
                        : undefined
                  }
                  onConversationUpdate={setMakeMessages}
                />
              </div>
              <div className="px-4 py-3 border-t border-border flex justify-between">
                {!editCommand && (
                  <Button variant="ghost" onClick={() => setStep('reflect')} className="text-sm">
                    <ArrowLeft className="w-4 h-4 mr-1" />
                    Retour
                  </Button>
                )}
                <Button
                  variant="primary"
                  onClick={goToCapture}
                  disabled={makeMessages.length === 0 || isGenerating}
                  className="flex items-center gap-2 text-sm ml-auto"
                >
                  {isGenerating ? 'Génération...' : 'Capturer'}
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          )}

          {step === 'capture' && (
            <motion.div
              key="capture"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="h-full overflow-y-auto p-4"
            >
              <RFCCapture
                initialData={captureData}
                onSave={handleSave}
                onBack={() => setStep('make')}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
