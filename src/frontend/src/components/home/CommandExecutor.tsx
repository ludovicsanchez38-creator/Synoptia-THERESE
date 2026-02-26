/**
 * THÉRÈSE V3 - CommandExecutor
 *
 * Exécute une commande selon son action type.
 * Réutilise les composants existants (DynamicSkillForm, SkillExecutionPanel, etc.)
 */

import { useState, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import type { CommandDefinition } from '../../types/command';
import type { FileFormat, ImageProvider } from '../guided/actionData';
import { DynamicSkillForm, type SkillSchema } from '../guided/DynamicSkillForm';
import { SkillExecutionPanel, type SkillExecutionStatus } from '../guided/SkillExecutionPanel';
import { SkillPromptPanel } from '../guided/SkillPromptPanel';
import { ImageGenerationPanel, type ImageGenerationStatus } from '../guided/ImageGenerationPanel';
import { useChatStore } from '../../stores/chatStore';
import {
  executeSkill,
  downloadSkillFile,
  generateImage,
  downloadGeneratedImage,
  getImageDownloadUrl,
  type SkillExecuteResponse,
  type ImageResponse,
} from '../../services/api';
import { fetchCommandSchema } from '../../services/api/commands-v3';

interface SkillState {
  skillId: string;
  format: FileFormat;
  status: SkillExecutionStatus;
  response?: SkillExecuteResponse;
  error?: string;
}

interface ImageState {
  provider: ImageProvider;
  status: ImageGenerationStatus;
  prompt?: string;
  response?: ImageResponse;
  error?: string;
}

interface CommandExecutorProps {
  command: CommandDefinition | null;
  onClose: () => void;
  onPromptSelect: (prompt: string) => void;
  onStartRFC: () => void;
}

export function CommandExecutor({ command, onClose, onPromptSelect, onStartRFC }: CommandExecutorProps) {
  const [dynamicSkill, setDynamicSkill] = useState<{
    command: CommandDefinition;
    schema: SkillSchema;
  } | null>(null);
  const [skillState, setSkillState] = useState<SkillState | null>(null);
  const [imagePromptCommand, setImagePromptCommand] = useState<CommandDefinition | null>(null);
  const [imageState, setImageState] = useState<ImageState | null>(null);
  const [isLoadingSchema, setIsLoadingSchema] = useState(false);

  const { addMessage } = useChatStore();

  // Exécuter une commande selon son type d'action
  const execute = useCallback(async (cmd: CommandDefinition) => {
    switch (cmd.action) {
      case 'prompt': {
        onPromptSelect(cmd.prompt_template);
        onClose();
        break;
      }

      case 'form_then_prompt':
      case 'form_then_file': {
        if (!cmd.skill_id) {
          onPromptSelect(cmd.prompt_template || cmd.name);
          onClose();
          break;
        }

        setIsLoadingSchema(true);
        try {
          const schema = await fetchCommandSchema(cmd.id);
          setDynamicSkill({
            command: cmd,
            schema: schema as unknown as SkillSchema,
          });
        } catch (err) {
          console.error('Failed to load schema:', err);
          onPromptSelect(cmd.prompt_template || cmd.name);
          onClose();
        } finally {
          setIsLoadingSchema(false);
        }
        break;
      }

      case 'image': {
        setImagePromptCommand(cmd);
        break;
      }

      case 'navigate': {
        // TODO : navigation vers panel
        onClose();
        break;
      }

      case 'rfc': {
        onStartRFC();
        onClose();
        break;
      }
    }
  }, [onPromptSelect, onClose, onStartRFC]);

  // Déclencher l'exécution quand une commande est sélectionnée
  if (command && !dynamicSkill && !skillState && !imagePromptCommand && !imageState && !isLoadingSchema) {
    execute(command);
  }

  // Handler formulaire dynamique
  const handleDynamicSubmit = useCallback(async (inputs: Record<string, any>) => {
    if (!dynamicSkill) return;

    const { command: cmd, schema } = dynamicSkill;
    const skillId = cmd.skill_id!;
    const isTextSkill = schema.output_type === 'text' || schema.output_type === 'analysis';

    if (isTextSkill) {
      const promptParts = Object.entries(inputs)
        .filter(([, v]) => v)
        .map(([k, v]) => `- ${k}: ${v}`);
      onPromptSelect(`${cmd.name}\n${promptParts.join('\n')}`);
      setDynamicSkill(null);
      onClose();
    } else {
      // Déduire le format de sortie depuis le skill_id
      let format: FileFormat = 'docx';
      if (skillId.startsWith('pptx')) format = 'pptx';
      else if (skillId.startsWith('xlsx')) format = 'xlsx';
      else if (skillId.startsWith('pdf')) format = 'pdf';
      setSkillState({ skillId, format, status: 'generating' });
      setDynamicSkill(null);

      try {
        const promptParts = Object.entries(inputs).map(([k, v]) => `${k}: ${v}`);
        const response = await executeSkill(skillId, {
          prompt: promptParts.join('\n'),
          inputs,
        });

        setSkillState({
          skillId,
          format,
          status: response.success ? 'success' : 'error',
          response: response.success ? response : undefined,
          error: response.success ? undefined : (response.error || 'Erreur'),
        });
      } catch (err) {
        setSkillState({
          skillId,
          format,
          status: 'error',
          error: err instanceof Error ? err.message : 'Erreur inconnue',
        });
      }
    }
  }, [dynamicSkill, onPromptSelect, onClose]);

  // Handlers image
  const handleImageGenerate = useCallback(async (customPrompt: string) => {
    if (!imagePromptCommand?.image_config) return;

    const config = imagePromptCommand.image_config;
    const provider = config.provider as ImageProvider;

    const store = useChatStore.getState();
    let conversationId = store.currentConversationId;
    if (!conversationId) {
      conversationId = store.createConversation();
    }

    addMessage({ role: 'user', content: `Génère une image : ${customPrompt}` });
    setImageState({ provider, status: 'generating', prompt: customPrompt });
    setImagePromptCommand(null);

    try {
      const req: Parameters<typeof generateImage>[0] = {
        prompt: customPrompt,
        provider,
        quality: config.default_quality as 'low' | 'medium' | 'high' | undefined,
      };

      if (provider === 'gpt-image-1.5' && config.default_size) {
        req.size = config.default_size as '1024x1024' | '1536x1024' | '1024x1536';
      } else if (provider === 'nanobanan-pro' && config.default_size) {
        req.image_size = config.default_size as '1K' | '2K' | '4K';
      }

      const response = await generateImage(req);
      const imageUrl = getImageDownloadUrl(response.id);

      addMessage({
        role: 'assistant',
        content: `![${customPrompt}](${imageUrl})\n\n*Image générée avec ${provider === 'gpt-image-1.5' ? 'GPT Image 1.5' : 'Nano Banana 2'}*\n\n[Télécharger ${response.file_name}](${imageUrl})`,
      });

      setImageState({ provider, status: 'success', prompt: customPrompt, response });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Erreur de génération';
      addMessage({ role: 'assistant', content: `Erreur : ${errorMsg}` });
      setImageState({ provider, status: 'error', prompt: customPrompt, error: errorMsg });
    }
  }, [imagePromptCommand, addMessage]);

  // Rendu conditionnel
  return (
    <AnimatePresence mode="wait">
      {isLoadingSchema && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-accent-cyan border-t-transparent rounded-full" />
          <span className="ml-3 text-sm text-text-muted">Chargement du formulaire...</span>
        </div>
      )}

      {dynamicSkill && (
        <DynamicSkillForm
          key="dynamic-form"
          skillName={dynamicSkill.command.name}
          schema={dynamicSkill.schema.schema}
          onSubmit={handleDynamicSubmit}
          onBack={() => { setDynamicSkill(null); onClose(); }}
          isSubmitting={false}
        />
      )}

      {skillState && (
        <SkillExecutionPanel
          key="skill-execution"
          skillId={skillState.skillId}
          format={skillState.format}
          status={skillState.status}
          fileName={skillState.response?.file_name}
          fileSize={skillState.response?.file_size}
          downloadUrl={skillState.response?.download_url}
          error={skillState.error}
          onDownload={async () => {
            if (skillState.response?.file_id) {
              await downloadSkillFile(skillState.response.file_id, skillState.response.file_name);
            }
          }}
          onRetry={() => setSkillState(null)}
          onClose={() => { setSkillState(null); onClose(); }}
        />
      )}

      {imagePromptCommand && (
        <SkillPromptPanel
          key="image-prompt"
          option={{
            id: imagePromptCommand.id,
            label: imagePromptCommand.name,
            prompt: imagePromptCommand.prompt_template || `Décris l'image que tu veux générer`,
            generatesImage: {
              provider: (imagePromptCommand.image_config?.provider || 'gpt-image-1.5') as ImageProvider,
              defaultSize: imagePromptCommand.image_config?.default_size,
              defaultQuality: imagePromptCommand.image_config?.default_quality as 'low' | 'medium' | 'high' | undefined,
            },
          }}
          onGenerate={handleImageGenerate}
          onBack={() => { setImagePromptCommand(null); onClose(); }}
        />
      )}

      {imageState && (
        <ImageGenerationPanel
          key="image-execution"
          provider={imageState.provider}
          status={imageState.status}
          prompt={imageState.prompt}
          imageUrl={imageState.response?.id ? getImageDownloadUrl(imageState.response.id) : undefined}
          fileName={imageState.response?.file_name}
          fileSize={imageState.response?.file_size}
          error={imageState.error}
          onDownload={async () => {
            if (imageState.response?.id) {
              await downloadGeneratedImage(imageState.response.id);
            }
          }}
          onRetry={() => setImageState(null)}
          onClose={() => { setImageState(null); onClose(); }}
        />
      )}
    </AnimatePresence>
  );
}
