import { useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { GUIDED_ACTIONS, type GuidedAction, type SubOption, type FileFormat, type ImageProvider } from './actionData';
import { ActionCard } from './ActionCard';
import { SubOptionsPanel } from './SubOptionsPanel';
import { SkillPromptPanel } from './SkillPromptPanel';
import { SkillExecutionPanel, type SkillExecutionStatus } from './SkillExecutionPanel';
import { ImageGenerationPanel, type ImageGenerationStatus } from './ImageGenerationPanel';
import { DynamicSkillForm, type SkillSchema } from './DynamicSkillForm';
import { useChatStore } from '../../stores/chatStore';
import {
  executeSkill,
  downloadSkillFile,
  generateImage,
  downloadGeneratedImage,
  getSkillInputSchema,
  API_BASE,
  type SkillExecuteResponse,
  type ImageResponse,
} from '../../services/api';

interface GuidedPromptsProps {
  onPromptSelect: (prompt: string) => void;
  onImageGenerated?: (prompt: string, imageUrl: string, fileName: string) => void;
}

// Skill execution state
interface SkillState {
  skillId: string;
  format: FileFormat;
  status: SkillExecutionStatus;
  response?: SkillExecuteResponse;
  error?: string;
}

// Image generation state
interface ImageState {
  provider: ImageProvider;
  status: ImageGenerationStatus;
  prompt?: string;
  response?: ImageResponse;
  error?: string;
}

export function GuidedPrompts({ onPromptSelect, onImageGenerated }: GuidedPromptsProps) {
  const [selectedAction, setSelectedAction] = useState<GuidedAction | null>(null);
  const [pendingSkillOption, setPendingSkillOption] = useState<SubOption | null>(null);
  const [skillState, setSkillState] = useState<SkillState | null>(null);
  const [pendingImageOption, setPendingImageOption] = useState<SubOption | null>(null);
  const [imageState, setImageState] = useState<ImageState | null>(null);

  // States pour les skills enrichis avec formulaires dynamiques
  const [pendingDynamicSkill, setPendingDynamicSkill] = useState<{
    option: SubOption;
    schema: SkillSchema;
  } | null>(null);
  const [isLoadingSchema, setIsLoadingSchema] = useState(false);

  // Get chat store functions to add messages to conversation
  const { addMessage } = useChatStore();

  const handleActionClick = useCallback((action: GuidedAction) => {
    setSelectedAction(action);
  }, []);

  const handleBack = useCallback(() => {
    setSelectedAction(null);
  }, []);

  const handleOptionSelect = useCallback(async (option: SubOption) => {
    // Priorité 1 : Si l'option a un skillId, utiliser le système enrichi
    if (option.skillId) {
      setIsLoadingSchema(true);
      setSelectedAction(null);

      try {
        // Récupérer le schéma des inputs du skill
        const schema = await getSkillInputSchema(option.skillId);

        setPendingDynamicSkill({
          option,
          schema,
        });
      } catch (error) {
        console.error('Failed to load skill schema:', error);
        // Fallback sur le prompt libre
        onPromptSelect(option.prompt);
      } finally {
        setIsLoadingSchema(false);
      }
    }
    // Priorité 2 : Legacy - Si l'option génère un fichier, montrer le panel de prompting
    else if (option.generatesFile) {
      setPendingSkillOption(option);
      setSelectedAction(null);
    }
    // Priorité 3 : Si l'option génère une image, montrer le panel de prompting image
    else if (option.generatesImage) {
      setPendingImageOption(option);
      setSelectedAction(null);
    }
    // Priorité 4 : Comportement standard : remplir le prompt
    else {
      onPromptSelect(option.prompt);
      setSelectedAction(null);
    }
  }, [onPromptSelect]);

  // Handler pour les skills enrichis avec formulaires dynamiques
  const handleDynamicSkillSubmit = useCallback(async (inputs: Record<string, any>) => {
    if (!pendingDynamicSkill) return;

    const { option, schema } = pendingDynamicSkill;
    const skillId = option.skillId!;

    // Déterminer si c'est un skill TEXT ou FILE
    // text et analysis = réponse dans le chat, file = fichier téléchargeable
    const isTextSkill = schema.output_type === 'text' || schema.output_type === 'analysis';

    if (isTextSkill) {
      // Skills TEXT/ANALYSIS : construire un prompt structuré pour le chat
      const promptParts = Object.entries(inputs)
        .filter(([, value]) => value)
        .map(([key, value]) => `- ${key}: ${value}`);
      const prompt = `${option.label}\n${promptParts.join('\n')}`;
      onPromptSelect(prompt);
      setPendingDynamicSkill(null);
    } else {
      // Skills FILE : montrer le panel d'exécution
      const format = option.generatesFile?.format || 'docx';

      setSkillState({
        skillId,
        format: format as FileFormat,
        status: 'generating',
      });
      setPendingDynamicSkill(null);

      try {
        // Construire un prompt à partir des inputs structurés
        const promptParts = Object.entries(inputs).map(([key, value]) => `${key}: ${value}`);
        const constructedPrompt = promptParts.join('\n');

        const response = await executeSkill(skillId, {
          prompt: constructedPrompt,
          inputs, // Passer les inputs structurés
          title: option.label,
        });

        if (response.success) {
          setSkillState({
            skillId,
            format: format as FileFormat,
            status: 'success',
            response,
          });
        } else {
          setSkillState({
            skillId,
            format: format as FileFormat,
            status: 'error',
            error: response.error || 'Generation failed',
          });
        }
      } catch (error) {
        setSkillState({
          skillId,
          format: format as FileFormat,
          status: 'error',
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }
  }, [pendingDynamicSkill, onPromptSelect]);

  const handleDynamicSkillBack = useCallback(() => {
    setPendingDynamicSkill(null);
    // Retourner à la liste des actions
    setSelectedAction(null);
  }, []);

  // Quand l'utilisateur a saisi son prompt et lance la génération (legacy FILE skills)
  const handleSkillGenerate = useCallback(async (customPrompt: string) => {
    if (!pendingSkillOption?.generatesFile) return;

    const { skillId, format } = pendingSkillOption.generatesFile;

    // Initialiser l'état skill
    setSkillState({
      skillId,
      format,
      status: 'generating',
    });
    setPendingSkillOption(null);

    try {
      // Exécuter le skill avec le prompt personnalisé
      const response = await executeSkill(skillId, {
        prompt: customPrompt,
        title: pendingSkillOption.label,
      });

      if (response.success) {
        setSkillState({
          skillId,
          format,
          status: 'success',
          response,
        });
      } else {
        setSkillState({
          skillId,
          format,
          status: 'error',
          error: response.error || 'Erreur inconnue',
        });
      }
    } catch (err) {
      setSkillState({
        skillId,
        format,
        status: 'error',
        error: err instanceof Error ? err.message : 'Erreur de connexion',
      });
    }
  }, [pendingSkillOption]);

  const handleSkillPromptBack = useCallback(() => {
    setPendingSkillOption(null);
  }, []);

  const handleDownload = useCallback(async () => {
    if (skillState?.response?.file_id) {
      try {
        await downloadSkillFile(skillState.response.file_id, skillState.response.file_name);
      } catch (err) {
        console.error('Download error:', err);
      }
    }
  }, [skillState]);

  const handleRetry = useCallback(() => {
    // Réinitialiser pour revenir à la sélection
    setSkillState(null);
  }, []);

  const handleCloseSkill = useCallback(() => {
    setSkillState(null);
  }, []);

  // Handlers pour la génération d'images
  const handleImageGenerate = useCallback(async (customPrompt: string) => {
    if (!pendingImageOption?.generatesImage) return;

    const { provider, defaultSize, defaultQuality } = pendingImageOption.generatesImage;

    // S'assurer qu'une conversation existe AVANT d'ajouter des messages
    // pour éviter la création de multiples conversations
    const store = useChatStore.getState();
    let conversationId = store.currentConversationId;
    if (!conversationId) {
      // Créer une conversation explicitement
      conversationId = store.createConversation();
    }

    // Ajouter le message utilisateur à la conversation
    addMessage({
      role: 'user',
      content: `🎨 Génère une image : ${customPrompt}`,
    });

    // Initialiser l'état image
    setImageState({
      provider,
      status: 'generating',
      prompt: customPrompt,
    });
    setPendingImageOption(null);

    try {
      // Construire la requête selon le provider
      const request: Parameters<typeof generateImage>[0] = {
        prompt: customPrompt,
        provider,
        quality: defaultQuality,
      };

      // OpenAI utilise 'size', Gemini utilise 'image_size'
      if (provider === 'gpt-image-1.5' && defaultSize) {
        request.size = defaultSize as '1024x1024' | '1536x1024' | '1024x1536';
      } else if (provider === 'nanobanan-pro' && defaultSize) {
        request.image_size = defaultSize as '1K' | '2K' | '4K';
      }

      const response = await generateImage(request);

      // Ajouter le message assistant avec l'image (dans la même conversation)
      const imageUrl = `${API_BASE}${response.download_url}`;
      addMessage({
        role: 'assistant',
        content: `![${customPrompt}](${imageUrl})\n\n*Image générée avec ${provider === 'gpt-image-1.5' ? 'GPT Image 1.5' : 'Nano Banana Pro'}*\n\n📥 [Télécharger ${response.file_name}](${imageUrl})`,
      });

      setImageState({
        provider,
        status: 'success',
        prompt: customPrompt,
        response,
      });

      // Callback optionnel
      onImageGenerated?.(customPrompt, imageUrl, response.file_name);
    } catch (err) {
      // Ajouter un message d'erreur
      const errorMessage = err instanceof Error ? err.message : 'Erreur de génération';
      addMessage({
        role: 'assistant',
        content: `❌ Erreur lors de la génération de l'image : ${errorMessage}`,
      });

      setImageState({
        provider,
        status: 'error',
        prompt: customPrompt,
        error: errorMessage,
      });
    }
  }, [pendingImageOption, addMessage, onImageGenerated]);

  const handleImagePromptBack = useCallback(() => {
    setPendingImageOption(null);
  }, []);

  const handleImageDownload = useCallback(async () => {
    if (imageState?.response?.id) {
      try {
        await downloadGeneratedImage(imageState.response.id);
      } catch (err) {
        console.error('Image download error:', err);
      }
    }
  }, [imageState]);

  const handleImageRetry = useCallback(() => {
    // Réinitialiser pour revenir à la sélection
    setImageState(null);
  }, []);

  const handleCloseImage = useCallback(() => {
    setImageState(null);
  }, []);

  return (
    <div className="w-full flex flex-col items-center justify-center px-4">
      {/* THÉRÈSE Avatar and greeting */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        {/* Glowing avatar - carré avec bords arrondis */}
        <div className="relative w-20 h-20 mx-auto mb-4">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-accent-cyan/40 to-accent-magenta/40 blur-xl animate-pulse" />
          <div className="relative w-full h-full rounded-2xl overflow-hidden border-2 border-accent-cyan/30 shadow-[0_0_40px_rgba(34,211,238,0.3)]">
            <img
              src="/therese-avatar.png"
              alt="THÉRÈSE"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
        <h2 className="text-xl font-semibold text-text mb-2 gradient-text">
          Comment puis-je t'aider ?
        </h2>
        <p className="text-sm text-text-muted">
          Choisis une action ou écris directement ton message
        </p>
      </motion.div>

      {/* Actions Grid / Sub-options / Dynamic Skill Form / Skill Prompt / Skill Execution / Image Generation */}
      <AnimatePresence mode="wait">
        {pendingDynamicSkill ? (
          <DynamicSkillForm
            key="dynamic-skill-form"
            skillName={pendingDynamicSkill.option.label}
            schema={pendingDynamicSkill.schema.schema}
            onSubmit={handleDynamicSkillSubmit}
            onBack={handleDynamicSkillBack}
            isSubmitting={isLoadingSchema}
          />
        ) : imageState ? (
          <ImageGenerationPanel
            key="image-execution"
            provider={imageState.provider}
            status={imageState.status}
            prompt={imageState.prompt}
            imageUrl={imageState.response?.download_url ? `${API_BASE}${imageState.response.download_url}` : undefined}
            fileName={imageState.response?.file_name}
            fileSize={imageState.response?.file_size}
            error={imageState.error}
            onDownload={handleImageDownload}
            onRetry={handleImageRetry}
            onClose={handleCloseImage}
          />
        ) : pendingImageOption ? (
          <SkillPromptPanel
            key="image-prompt"
            option={pendingImageOption}
            onGenerate={handleImageGenerate}
            onBack={handleImagePromptBack}
          />
        ) : skillState ? (
          <SkillExecutionPanel
            key="skill-execution"
            skillId={skillState.skillId}
            format={skillState.format}
            status={skillState.status}
            fileName={skillState.response?.file_name}
            fileSize={skillState.response?.file_size}
            downloadUrl={skillState.response?.download_url}
            error={skillState.error}
            onDownload={handleDownload}
            onRetry={handleRetry}
            onClose={handleCloseSkill}
          />
        ) : pendingSkillOption ? (
          <SkillPromptPanel
            key="skill-prompt"
            option={pendingSkillOption}
            onGenerate={handleSkillGenerate}
            onBack={handleSkillPromptBack}
          />
        ) : selectedAction ? (
          <SubOptionsPanel
            key="suboptions"
            action={selectedAction}
            onSelect={handleOptionSelect}
            onBack={handleBack}
          />
        ) : (
          <motion.div
            key="actions-grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl w-full"
          >
            {GUIDED_ACTIONS.map((action, index) => (
              <ActionCard
                key={action.id}
                icon={action.icon}
                title={action.title}
                description={action.description}
                onClick={() => handleActionClick(action)}
                index={index}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keyboard hints */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="flex flex-wrap items-center justify-center gap-3 mt-8"
      >
        <div className="px-3 py-1.5 rounded-full bg-surface-elevated border border-border text-xs text-text-muted">
          <kbd className="font-mono">⌘B</kbd> conversations
        </div>
        <div className="px-3 py-1.5 rounded-full bg-surface-elevated border border-border text-xs text-text-muted">
          <kbd className="font-mono">⌘M</kbd> mémoire
        </div>
        <div className="px-3 py-1.5 rounded-full bg-surface-elevated border border-border text-xs text-text-muted">
          <kbd className="font-mono">⌘K</kbd> commandes
        </div>
        <div className="px-3 py-1.5 rounded-full bg-surface-elevated border border-border text-xs text-text-muted">
          <kbd className="font-mono">/</kbd> raccourcis
        </div>
      </motion.div>
    </div>
  );
}
