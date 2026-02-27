/**
 * THÉRÈSE V3 - HomeCommands
 *
 * Page d'accueil : 3 blocs catégorie (style v0.2.13 ActionCard)
 * alimentés par le commandsStore V3.
 * Clic sur un bloc -> affiche les commandes en pills.
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Brain, GitBranch, ChevronLeft, Plus, Trash2, ArrowRightLeft, type LucideIcon } from 'lucide-react';
import { useCommandsStore } from '../../stores/commandsStore';
import { CommandExecutor } from './CommandExecutor';
import { CommandCard } from './CommandCard';
import { RFCWizard } from '../rfc/RFCWizard';
import type { CommandDefinition } from '../../types/command';
import { cn } from '../../lib/utils';

interface HomeCommandsProps {
  onPromptSelect: (prompt: string) => void;
  onImageGenerated?: (prompt: string, imageUrl: string, fileName: string) => void;
  onGuidedPanelChange?: (active: boolean) => void;
}

/** Les 3 catégories affichées comme blocs */
const CATEGORY_BLOCKS: Array<{
  id: string;
  icon: LucideIcon;
  title: string;
  description: string;
  question: string;
}> = [
  {
    id: 'production',
    icon: Sparkles,
    title: 'Produire',
    description: 'Créer du contenu nouveau',
    question: 'Que veux-tu produire ?',
  },
  {
    id: 'analyse',
    icon: Brain,
    title: 'Comprendre',
    description: 'Analyser et apprendre',
    question: 'Que veux-tu comprendre ?',
  },
  {
    id: 'organisation',
    icon: GitBranch,
    title: 'Organiser',
    description: 'Planifier et automatiser',
    question: 'Que veux-tu organiser ?',
  },
];

export function HomeCommands({ onPromptSelect, onGuidedPanelChange }: HomeCommandsProps) {
  const { commands, fetchCommands, updateCommand, deleteCommand, isLoading } = useCommandsStore();
  const [selectedCategory, setSelectedCategory] = useState<typeof CATEGORY_BLOCKS[number] | null>(null);
  const [activeCommand, setActiveCommand] = useState<CommandDefinition | null>(null);
  const [showRFC, setShowRFC] = useState(false);
  /** ID de la commande en cours de confirmation de suppression */
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  /** ID de la commande dont on affiche le menu de déplacement */
  const [showMoveMenuId, setShowMoveMenuId] = useState<string | null>(null);

  useEffect(() => {
    fetchCommands();
  }, [fetchCommands]);

  const homeCommands = useMemo(() => {
    return commands.filter((c) => c.show_on_home);
  }, [commands]);

  /** Commandes groupées par catégorie */
  const grouped = useMemo(() => {
    const groups: Record<string, CommandDefinition[]> = {};
    for (const cat of CATEGORY_BLOCKS) {
      groups[cat.id] = homeCommands
        .filter((c) => c.category === cat.id)
        .sort((a, b) => a.sort_order - b.sort_order);
    }
    return groups;
  }, [homeCommands]);

  const handleCategoryClick = useCallback((cat: typeof CATEGORY_BLOCKS[number]) => {
    setSelectedCategory(cat);
  }, []);

  const handleBack = useCallback(() => {
    setSelectedCategory(null);
  }, []);

  const handleCommandClick = useCallback((cmd: CommandDefinition) => {
    setActiveCommand(cmd);
    setSelectedCategory(null);
    onGuidedPanelChange?.(true);
  }, [onGuidedPanelChange]);

  const handleClose = useCallback(() => {
    setActiveCommand(null);
    onGuidedPanelChange?.(false);
  }, [onGuidedPanelChange]);

  const handleStartRFC = useCallback(() => {
    setShowRFC(true);
  }, []);

  const handleCreateCommand = useCallback(() => {
    setActiveCommand({
      id: '__rfc__',
      name: 'Créer une commande',
      description: 'Créer une commande personnalisée avec l\'aide de THÉRÈSE',
      icon: 'Plus',
      category: 'production',
      source: 'builtin',
      action: 'rfc',
      prompt_template: '',
      skill_id: null,
      system_prompt: null,
      show_on_home: false,
      show_in_slash: false,
      sort_order: 999,
      image_config: null,
      navigate_target: null,
      is_editable: false,
    });
    setSelectedCategory(null);
  }, []);

  const handleDeleteCommand = useCallback(async (commandId: string) => {
    try {
      await deleteCommand(commandId);
      setConfirmDeleteId(null);
    } catch (err) {
      console.error('Erreur suppression commande:', err);
    }
  }, [deleteCommand]);

  const handleMoveCommand = useCallback(async (commandId: string, newCategory: string) => {
    try {
      await updateCommand(commandId, { category: newCategory });
      setShowMoveMenuId(null);
    } catch (err) {
      console.error('Erreur déplacement commande:', err);
    }
  }, [updateCommand]);

  return (
    <div className="w-full flex flex-col items-center justify-center px-4">
      {/* Avatar THÉRÈSE et greeting */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
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

      {/* Contenu principal */}
      <AnimatePresence mode="wait">
        {showRFC ? (
          <RFCWizard
            key="rfc-wizard"
            onClose={() => {
              setShowRFC(false);
              fetchCommands();
            }}
          />
        ) : activeCommand ? (
          <CommandExecutor
            key="executor"
            command={activeCommand}
            onClose={handleClose}
            onPromptSelect={onPromptSelect}
            onStartRFC={handleStartRFC}
          />
        ) : selectedCategory ? (
          /* --- Panel sous-options (pills) --- */
          <motion.div
            key="suboptions"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="w-full max-w-lg"
          >
            {/* Bouton retour */}
            <motion.button
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              onClick={handleBack}
              className="flex items-center gap-2 text-sm text-text-muted hover:text-text transition-colors duration-150 mb-4 focus:outline-none focus:text-accent-cyan"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Retour</span>
            </motion.button>

            {/* Header avec icône et question */}
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20">
                <selectedCategory.icon className="w-6 h-6 text-accent-cyan" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text">{selectedCategory.title}</h3>
                <p className="text-sm text-text-muted">{selectedCategory.question}</p>
              </div>
            </div>

            {/* Commandes en pills */}
            <div className="flex flex-wrap gap-3">
              {(grouped[selectedCategory.id] || []).map((cmd, index) => (
                <div key={cmd.id} className="relative group/cmd flex items-center gap-1">
                  <CommandCard
                    command={cmd}
                    onClick={handleCommandClick}
                    index={index}
                  />
                  {/* Actions pour commandes utilisateur */}
                  {cmd.is_editable && (
                    <div className="hidden group-hover/cmd:flex items-center gap-0.5">
                      {/* Bouton déplacer */}
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowMoveMenuId(showMoveMenuId === cmd.id ? null : cmd.id);
                            setConfirmDeleteId(null);
                          }}
                          className="p-1 rounded-full hover:bg-accent-cyan/15 text-text-muted hover:text-accent-cyan transition-colors"
                          title="Déplacer"
                        >
                          <ArrowRightLeft className="w-3 h-3" />
                        </button>
                        {/* Menu de déplacement */}
                        {showMoveMenuId === cmd.id && (
                          <div className="absolute top-full left-0 mt-1 z-20 bg-surface border border-border rounded-lg shadow-xl py-1 min-w-[140px]">
                            {CATEGORY_BLOCKS.filter((cat) => cat.id !== selectedCategory.id).map((cat) => (
                              <button
                                key={cat.id}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMoveCommand(cmd.id, cat.id);
                                }}
                                className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-text hover:bg-accent-cyan/10 hover:text-accent-cyan transition-colors"
                              >
                                <cat.icon className="w-3.5 h-3.5" />
                                {cat.title}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      {/* Bouton supprimer */}
                      {confirmDeleteId === cmd.id ? (
                        <div className="flex items-center gap-1 ml-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteCommand(cmd.id);
                            }}
                            className="px-2 py-0.5 rounded text-xs font-medium bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                          >
                            Confirmer
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setConfirmDeleteId(null);
                            }}
                            className="px-2 py-0.5 rounded text-xs font-medium text-text-muted hover:text-text transition-colors"
                          >
                            Annuler
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfirmDeleteId(cmd.id);
                            setShowMoveMenuId(null);
                          }}
                          className="p-1 rounded-full hover:bg-red-500/15 text-text-muted hover:text-red-400 transition-colors"
                          title="Supprimer"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {/* Bouton "Créer une commande" en dernier */}
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: 0.1 + (grouped[selectedCategory.id]?.length || 0) * 0.05 }}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleCreateCommand}
                className={cn(
                  'px-4 py-2 rounded-full text-sm font-medium',
                  'bg-surface-elevated border border-dashed border-accent-cyan/30',
                  'hover:border-accent-cyan/50 hover:bg-accent-cyan/10',
                  'text-accent-cyan hover:text-accent-cyan',
                  'transition-all duration-150',
                  'flex items-center gap-2'
                )}
              >
                <Plus className="w-4 h-4" />
                Créer une commande
              </motion.button>
            </div>
          </motion.div>
        ) : (
          /* --- Grille 3 blocs --- */
          <motion.div
            key="actions-grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="grid grid-cols-3 gap-3 max-w-2xl w-full"
          >
            {isLoading ? (
              <div className="col-span-3 flex items-center justify-center py-8">
                <div className="animate-spin w-6 h-6 border-2 border-accent-cyan border-t-transparent rounded-full" />
              </div>
            ) : (
              CATEGORY_BLOCKS.map((cat, index) => (
                <motion.button
                  key={cat.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05, ease: [0.4, 0, 0.2, 1] }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleCategoryClick(cat)}
                  className={cn(
                    'group relative flex flex-col items-start p-4 rounded-xl',
                    'bg-surface-elevated/60 backdrop-blur-sm',
                    'border border-border hover:border-accent-cyan/50',
                    'hover:shadow-[0_0_20px_rgba(34,211,238,0.15)]',
                    'transition-all duration-200 text-left',
                    'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30',
                  )}
                >
                  {/* Gradient glow on hover */}
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-accent-cyan/5 to-accent-magenta/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                  {/* Icon container */}
                  <div className="relative flex items-center justify-center w-10 h-10 rounded-lg mb-3 bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 group-hover:from-accent-cyan/30 group-hover:to-accent-magenta/30 transition-all duration-200">
                    <cat.icon className="w-5 h-5 text-accent-cyan group-hover:text-white transition-colors duration-200" />
                  </div>

                  {/* Title */}
                  <h3 className="relative text-sm font-semibold text-text group-hover:text-white transition-colors duration-200">
                    {cat.title}
                  </h3>

                  {/* Description */}
                  <p className="relative text-xs mt-1 text-text-muted line-clamp-2">
                    {cat.description}
                  </p>
                </motion.button>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
