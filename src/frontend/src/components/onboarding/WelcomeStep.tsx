/**
 * THERESE v2 - Welcome Step
 *
 * First step of the onboarding wizard - Introduction to THERESE.
 */

import { motion } from 'framer-motion';
import { Brain, Shield, Zap } from 'lucide-react';

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
    title: '100% local',
    description: 'Tes données restent sur ta machine. Vie privée garantie.',
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
      className="flex flex-col items-center text-center px-8 py-6"
    >
      {/* Logo and Title */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 300 }}
        className="mb-8"
      >
        <img
          src="/therese-avatar.png"
          alt="THÉRÈSE"
          className="w-24 h-24 rounded-2xl mb-6 mx-auto border border-border/30"
        />
        <h1 className="text-4xl font-bold text-text mb-3">
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
        className="grid grid-cols-3 gap-6 w-full max-w-2xl mb-8"
      >
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className="p-4 rounded-xl bg-background/40 border border-border/30"
          >
            <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center mb-3 mx-auto">
              <feature.icon className="w-5 h-5 text-accent-cyan" />
            </div>
            <h3 className="font-medium text-text text-sm mb-1">{feature.title}</h3>
            <p className="text-text-muted text-xs">{feature.description}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* CTA */}
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        onClick={onNext}
        className="px-8 py-3 rounded-xl bg-accent-cyan text-background font-medium hover:bg-accent-cyan/90 transition-colors"
      >
        Commencer la configuration
      </motion.button>
    </motion.div>
  );
}
