/**
 * THERESE v2 - Welcome Step
 *
 * First step of the onboarding wizard - Introduction to THERESE.
 */

import { motion } from 'framer-motion';
import { CharacterPortrait } from '../prototype/DecisionMissionPrototype';
import { Brain, Shield, Zap } from 'lucide-react';
import { Button } from '../ui/Button';
import { Carte } from '../ui/Carte';

interface WelcomeStepProps {
  onNext: () => void;
}

const features = [
  {
    icon: Brain,
    title: 'Mémoire persistante',
    description: 'THÉRÈSE se souvient de tes contacts, projets et conversations.',
  },
  {
    icon: Shield,
    title: 'Données locales',
    description: 'Ton contexte reste sur ta machine. Les réponses passent par le provider IA de ton choix.',
  },
  {
    icon: Zap,
    title: 'Multi-LLM',
    description: 'Claude, GPT, Gemini, Mistral ou Ollama. Tu choisis.',
  },
];

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center px-4 py-5 text-center sm:px-8 sm:py-6"
    >
      {/* Logo and Title */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 300 }}
        className="mb-6 sm:mb-8"
      >
        <CharacterPortrait
          index={0}
          className="mx-auto mb-6 h-24 w-24 rounded-md border border-border/30"
        />
        <h1 className="mb-3 text-3xl font-bold text-text sm:text-4xl">
          Bienvenue sur THÉRÈSE
        </h1>
        <p className="text-text-muted text-lg max-w-md">
          Ton assistante IA souveraine. Ta mémoire, tes données, ton business.
        </p>
      </motion.div>

      {/* Features */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mb-8 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-6"
      >
        {features.map((feature) => (
          <Carte
            as="section"
            key={feature.title}
            className="p-4"
          >
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-accent-tint">
              <feature.icon className="h-5 w-5 text-accent" />
            </div>
            <h3 className="font-medium text-text text-sm mb-1">{feature.title}</h3>
            <p className="text-text-muted text-xs">{feature.description}</p>
          </Carte>
        ))}
      </motion.div>

      {/* CTA */}
      <Button
        variant="primary"
        size="lg"
        onClick={onNext}
        data-testid="onboarding-next-btn"
        className="px-8"
      >
        Commencer la configuration
      </Button>
    </motion.div>
  );
}
