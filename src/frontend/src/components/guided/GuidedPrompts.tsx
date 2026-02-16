import { useState, useCallback, useEffect, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { GUIDED_ACTIONS, type GuidedAction, type SubOption, type FileFormat, type ImageProvider } from './actionData';
import { ActionCard } from './ActionCard';
import { SubOptionsPanel } from './SubOptionsPanel';
import { SkillPromptPanel } from './SkillPromptPanel';
import { SkillExecutionPanel, type SkillExecutionStatus } from './SkillExecutionPanel';
import { ImageGenerationPanel, type ImageGenerationStatus } from './ImageGenerationPanel';
import { DynamicSkillForm, type SkillSchema } from './DynamicSkillForm';
import { CreateCommandForm } from './CreateCommandForm';
import { useChatStore } from '../../stores/chatStore';
import {
  executeSkill,
  downloadSkillFile,
  generateImage,
  downloadGeneratedImage,
  getImageDownloadUrl,
  getSkillInputSchema,
  type SkillExecuteResponse,
  type ImageResponse,
} from '../../services/api';
import { listUserCommands, createUserCommand, type UserCommand } from '../../services/api/commands';

interface GuidedPromptsProps {
  onPromptSelect: (prompt: string, skillId?: string) => void;
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

  // P0-B: Error state for schema loading failures
  const [schemaLoadError, setSchemaLoadError] = useState<string | null>(null);

  // P1-A: Create command form visibility
  const [showCreateCommand, setShowCreateCommand] = useState(false);

  // P1-C: User commands for dynamic homepage
  const [userCommands, setUserCommands] = useState<UserCommand[]>([]);

  // Get chat store functions to add messages to conversation
  const { addMessage } = useChatStore();

  // P1-C: Fetch user commands on mount
  useEffect(() => {
    listUserCommands()
      .then(setUserCommands)
      .catch(() => {
        // Silently ignore - user commands are optional
      });
  }, []);

  // P1-C: Merge static actions with user commands that have show_on_home
  const mergedActions = useMemo(() => {
    const homeCommands = userCommands.filter((cmd) => cmd.show_on_home);
    if (homeCommands.length === 0) return GUIDED_ACTIONS;

    // Convert user commands to SubOptions and add them to Personnaliser
    const userSubOptions: SubOption[] = homeCommands.map((cmd) => ({
      id: `user-cmd-${cmd.name}`,
      label: `${cmd.icon || ''} ${cmd.description || cmd.name}`.trim(),
      prompt: cmd.content,
    }));

    return GUIDED_ACTIONS.map((action) => {
      if (action.id === 'personnaliser') {
        return {
          ...action,
          options: [...action.options, ...userSubOptions],
        };
      }
      return action;
    });
  }, [userCommands]);

  // P0-B: Auto-clear schema load error after 5s
  useEffect(() => {
    if (schemaLoadError) {
      const timer = setTimeout(() => setSchemaLoadError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [schemaLoadError]);

  const handleActionClick = useCallback((action: GuidedAction) => {
    setSelectedAction(action);
  }, []);

  const handleBack = useCallback(() => {
    setSelectedAction(null);
  }, []);

  const handleOptionSelect = useCallback(async (option: SubOption) => {
    // P1-A: Check behavior BEFORE skillId
    if (option.behavior) {
      setSelectedAction(null);
      if (option.behavior === 'create-command') {
        setShowCreateCommand(true);
        return;
      }
      // P2 stubs: create-skill and create-automation -> guided prompt
      if (option.behavior === 'create-skill' || option.behavior === 'create-automation') {
        onPromptSelect(option.prompt);
        return;
      }
    }

    // Priorite 1 : Si l'option a un skillId, utiliser le systeme enrichi
    if (option.skillId) {
      setIsLoadingSchema(true);
      setSelectedAction(null);

      try {
        // Recuperer le schema des inputs du skill
        const schema = await getSkillInputSchema(option.skillId);

        setPendingDynamicSkill({
          option,
          schema,
        });
      } catch (error) {
        console.error(`Failed to load skill schema for "${option.skillId}":`, error);
        // Fallback : si l'option a generatesFile, utiliser le legacy flow
        if (option.generatesFile) {
          setPendingSkillOption(option);
        } else {
          setSchemaLoadError(`Impossible de charger le formulaire pour "${option.label}". Prompt libre utilisé.`);
          onPromptSelect(`${option.label}\n${option.prompt}`);
        }
      } finally {
        setIsLoadingSchema(false);
      }
    }
    // Priorite 2 : Legacy - Si l'option genere un fichier, montrer le panel de prompting
    else if (option.generatesFile) {
      setPendingSkillOption(option);
      setSelectedAction(null);
    }
    // Priorite 3 : Si l'option genere une image, montrer le panel de prompting image
    else if (option.generatesImage) {
      setPendingImageOption(option);
      setSelectedAction(null);
    }
    // Priorite 4 : Comportement standard : remplir le prompt
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

    // Determiner si c'est un skill TEXT ou FILE
    const isTextSkill = schema.output_type === 'text' || schema.output_type === 'analysis';

    if (isTextSkill) {
      // Skills TEXT/ANALYSIS : construire un prompt structuré pour le chat
      // et passer le skillId pour que le backend injecte le system prompt enrichi
      const promptParts = Object.entries(inputs)
        .filter(([, value]) => value)
        .map(([key, value]) => `- ${key}: ${value}`);
      const prompt = `${option.label}\n${promptParts.join('\n')}`;
      onPromptSelect(prompt, skillId);
      setPendingDynamicSkill(null);
    } else {
      // Skills FILE : montrer le panel d'execution
      const format = option.generatesFile?.format || 'docx';

      setSkillState({
        skillId,
        format: format as FileFormat,
        status: 'generating',
      });
      setPendingDynamicSkill(null);

      try {
        const promptParts = Object.entries(inputs).map(([key, value]) => `${key}: ${value}`);
        const constructedPrompt = promptParts.join('\n');

        const response = await executeSkill(skillId, {
          prompt: constructedPrompt,
          inputs,
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
    setSelectedAction(null);
  }, []);

  // Quand l'utilisateur a saisi son prompt et lance la generation (legacy FILE skills)
  const handleSkillGenerate = useCallback(async (customPrompt: string) => {
    if (!pendingSkillOption?.generatesFile) return;

    const { skillId, format } = pendingSkillOption.generatesFile;

    setSkillState({
      skillId,
      format,
      status: 'generating',
    });
    setPendingSkillOption(null);

    try {
      const response = await executeSkill(skillId, {
        prompt: customPrompt,
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
    setSkillState(null);
  }, []);

  const handleCloseSkill = useCallback(() => {
    setSkillState(null);
  }, []);

  // Handlers pour la generation d'images
  const handleImageGenerate = useCallback(async (customPrompt: string) => {
    if (!pendingImageOption?.generatesImage) return;

    const { provider, defaultSize, defaultQuality } = pendingImageOption.generatesImage;

    const store = useChatStore.getState();
    let conversationId = store.currentConversationId;
    if (!conversationId) {
      conversationId = store.createConversation();
    }

    addMessage({
      role: 'user',
      content: `Genere une image : ${customPrompt}`,
    });

    setImageState({
      provider,
      status: 'generating',
      prompt: customPrompt,
    });
    setPendingImageOption(null);

    try {
      const request: Parameters<typeof generateImage>[0] = {
        prompt: customPrompt,
        provider,
        quality: defaultQuality,
      };

      if (provider === 'gpt-image-1.5' && defaultSize) {
        request.size = defaultSize as '1024x1024' | '1536x1024' | '1024x1536';
      } else if (provider === 'nanobanan-pro' && defaultSize) {
        request.image_size = defaultSize as '1K' | '2K' | '4K';
      }

      const response = await generateImage(request);

      const imageUrl = getImageDownloadUrl(response.id);
      addMessage({
        role: 'assistant',
        content: `![${customPrompt}](${imageUrl})\n\n*Image générée avec ${provider === 'gpt-image-1.5' ? 'GPT Image 1.5' : 'Nano Banana Pro'}*\n\n[Télécharger ${response.file_name}](${imageUrl})`,
      });

      setImageState({
        provider,
        status: 'success',
        prompt: customPrompt,
        response,
      });

      onImageGenerated?.(customPrompt, imageUrl, response.file_name);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur de generation';
      addMessage({
        role: 'assistant',
        content: `Erreur lors de la generation de l'image : ${errorMessage}`,
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
    setImageState(null);
  }, []);

  const handleCloseImage = useCallback(() => {
    setImageState(null);
  }, []);

  // P1-C: Handle create command form submission
  const handleCreateCommand = useCallback(async (data: {
    name: string;
    description: string;
    category: string;
    icon: string;
    show_on_home: boolean;
    content: string;
  }) => {
    await createUserCommand(data);
    // Refresh user commands
    const updated = await listUserCommands();
    setUserCommands(updated);
    setShowCreateCommand(false);
  }, []);

  const handleCreateCommandBack = useCallback(() => {
    setShowCreateCommand(false);
  }, []);

  return (
    <div className="w-full flex flex-col items-center justify-center px-4">
      {/* THERESE Avatar and greeting */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        {/* Glowing avatar */}
        <div className="relative w-20 h-20 mx-auto mb-4">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-accent-cyan/40 to-accent-magenta/40 blur-xl animate-pulse" />
          <div className="relative w-full h-full rounded-2xl overflow-hidden border-2 border-accent-cyan/30 shadow-[0_0_40px_rgba(34,211,238,0.3)]">
            <img
              src="/therese-avatar.png"
              alt="THERESE"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
        <h2 className="text-xl font-semibold text-text mb-2 gradient-text">
          Comment puis-je t'aider ?
        </h2>
        <p className="text-sm text-text-muted">
          Choisis une action ou ecris directement ton message
        </p>
      </motion.div>

      {/* P0-B: Schema load error banner */}
      <AnimatePresence>
        {schemaLoadError && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="w-full max-w-2xl mb-4 px-4 py-2 rounded-lg bg-error/10 border border-error/20 text-sm text-error"
          >
            {schemaLoadError}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions Grid / Sub-options / Dynamic Skill Form / Create Command / Skill Prompt / Skill Execution / Image Generation */}
      <AnimatePresence mode="wait">
        {showCreateCommand ? (
          <CreateCommandForm
            key="create-command-form"
            onSubmit={handleCreateCommand}
            onBack={handleCreateCommandBack}
          />
        ) : pendingDynamicSkill ? (
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
            imageUrl={imageState.response?.id ? getImageDownloadUrl(imageState.response.id) : undefined}
            fileName={imageState.response?.file_name}
            fileSize={imageState.response?.file_size}
            error={imageState.error}
            onDownload={handleImageDownload}
            onRetry={handleImageRetry}
            onClose={handleCloseImage}
            onUse={handleCloseImage}
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
            className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-2xl w-full"
          >
            {mergedActions.map((action, index) => (
              <ActionCard
                key={action.id}
                icon={action.icon}
                title={action.title}
                description={action.description}
                onClick={() => handleActionClick(action)}
                index={index}
                variant={action.variant}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keyboard hints */}
    </div>
  );
}
