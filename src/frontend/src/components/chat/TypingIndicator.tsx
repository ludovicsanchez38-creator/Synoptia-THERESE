import { motion } from 'framer-motion';
import { Bot, Sparkles } from 'lucide-react';

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-3"
    >
      {/* Avatar with glow */}
      <div className="w-8 h-8 rounded-lg bg-accent-cyan/20 text-accent-cyan flex items-center justify-center flex-shrink-0 shadow-[0_0_12px_rgba(34,211,238,0.3)]">
        <Bot className="w-4 h-4" />
      </div>

      {/* Typing indicator with premium styling */}
      <div className="bg-surface-elevated border border-border hover:border-accent-cyan/20 rounded-2xl px-4 py-3 shadow-[0_4px_12px_rgba(0,0,0,0.2)] transition-all">
        <div className="flex items-center gap-2">
          <Sparkles className="w-3 h-3 text-accent-cyan/60" />
          <div className="flex items-center gap-1.5">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 bg-accent-cyan rounded-full shadow-[0_0_8px_rgba(34,211,238,0.5)]"
                animate={{
                  y: [0, -8, 0],
                  opacity: [0.4, 1, 0.4],
                  scale: [1, 1.2, 1],
                }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  delay: i * 0.15,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </div>
          <span className="text-xs text-text-muted ml-1">Réflexion...</span>
        </div>
      </div>
    </motion.div>
  );
}
