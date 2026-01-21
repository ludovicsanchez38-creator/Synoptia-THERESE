# Story E5-04 : Animer les transitions et micro-interactions

## Description

En tant que **utilisateur**,
Je veux **des animations fluides et agréables**,
Afin de **avoir une expérience premium et responsive**.

## Contexte technique

- **Composants impactés** : Frontend React, Framer Motion
- **Dépendances** : E1-01
- **Fichiers concernés** :
  - `src/frontend/src/lib/animations.ts` (nouveau)
  - `src/frontend/src/components/ui/AnimatedList.tsx` (nouveau)

## Critères d'acceptation

- [ ] Transitions de page fluides
- [ ] Animation des messages (apparition staggered)
- [ ] Feedback hover/click sur les boutons
- [ ] Animation de chargement élégante
- [ ] Animation typing indicator
- [ ] Performance 60fps maintenue
- [ ] Respect prefers-reduced-motion

## Notes techniques

### Variants d'animation

```typescript
// lib/animations.ts
import { Variants } from 'framer-motion';

// Transitions de base
export const transitions = {
  fast: { duration: 0.15, ease: 'easeOut' },
  normal: { duration: 0.2, ease: 'easeOut' },
  slow: { duration: 0.3, ease: 'easeOut' },
  spring: { type: 'spring', stiffness: 300, damping: 30 },
  bounce: { type: 'spring', stiffness: 400, damping: 15 },
};

// Fade
export const fadeVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
  exit: { opacity: 0 },
};

// Slide up
export const slideUpVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

// Slide in from side
export const slideInVariants: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
};

// Scale
export const scaleVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
};

// Stagger children
export const staggerContainerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

export const staggerItemVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
};

// Page transition
export const pageVariants: Variants = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
};

// Modal/overlay
export const overlayVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
  exit: { opacity: 0 },
};

export const modalVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95, y: -10 },
  visible: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: 10 },
};

// Hook pour respecter prefers-reduced-motion
export function useReducedMotion(): boolean {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(query.matches);

    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    query.addEventListener('change', handler);
    return () => query.removeEventListener('change', handler);
  }, []);

  return reducedMotion;
}

// Variants conditionnels
export function getVariants(variants: Variants, reducedMotion: boolean): Variants {
  if (reducedMotion) {
    return {
      hidden: { opacity: 0 },
      visible: { opacity: 1 },
      exit: { opacity: 0 },
    };
  }
  return variants;
}
```

### Composant AnimatedList

```tsx
// components/ui/AnimatedList.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { staggerContainerVariants, staggerItemVariants, useReducedMotion } from '../../lib/animations';

interface AnimatedListProps<T> {
  items: T[];
  keyExtractor: (item: T) => string;
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
}

export function AnimatedList<T>({
  items,
  keyExtractor,
  renderItem,
  className,
}: AnimatedListProps<T>) {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      className={className}
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
    >
      <AnimatePresence mode="popLayout">
        {items.map((item, index) => (
          <motion.div
            key={keyExtractor(item)}
            variants={staggerItemVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={reducedMotion ? { duration: 0 } : { duration: 0.2 }}
            layout
          >
            {renderItem(item, index)}
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
```

### Animation des messages

```tsx
// components/chat/MessageList.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { useReducedMotion, slideUpVariants } from '../../lib/animations';

export function MessageList({ messages }: { messages: Message[] }) {
  const reducedMotion = useReducedMotion();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth' });
  }, [messages, reducedMotion]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      <AnimatePresence initial={false}>
        {messages.map((message, index) => (
          <motion.div
            key={message.id}
            variants={slideUpVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{
              duration: reducedMotion ? 0 : 0.2,
              delay: reducedMotion ? 0 : index * 0.03,
            }}
          >
            <MessageBubble message={message} />
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={messagesEndRef} />
    </div>
  );
}
```

### Typing indicator

```tsx
// components/chat/TypingIndicator.tsx
import { motion } from 'framer-motion';

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 bg-accent-cyan rounded-full"
          animate={{
            y: [0, -6, 0],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * 0.15,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}
```

### Skeleton loader

```tsx
// components/ui/Skeleton.tsx
import { motion } from 'framer-motion';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
}

export function Skeleton({ className, variant = 'text' }: SkeletonProps) {
  return (
    <motion.div
      className={cn(
        'bg-surface-elevated',
        variant === 'text' && 'h-4 rounded',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-lg',
        className
      )}
      animate={{
        opacity: [0.5, 0.8, 0.5],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
  );
}

export function MessageSkeleton() {
  return (
    <div className="flex gap-3 p-4">
      <Skeleton variant="circular" className="w-10 h-10 flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="w-24" />
        <Skeleton className="w-full" />
        <Skeleton className="w-3/4" />
      </div>
    </div>
  );
}
```

### Button avec feedback

```tsx
// components/ui/Button.tsx (màj)
import { motion } from 'framer-motion';

export function Button({ children, ...props }: ButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.1 }}
      className={cn(/* ... styles */)}
      {...props}
    >
      {children}
    </motion.button>
  );
}
```

### Page transitions

```tsx
// components/PageTransition.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { pageVariants, useReducedMotion } from '../lib/animations';

export function PageTransition({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const reducedMotion = useReducedMotion();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{
          duration: reducedMotion ? 0 : 0.2,
          ease: 'easeOut',
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] Transitions de page fluides
- [ ] Messages animés (stagger)
- [ ] Typing indicator animé
- [ ] Skeleton loaders
- [ ] Button feedback hover/tap
- [ ] prefers-reduced-motion respecté
- [ ] 60fps constant

---

*Sprint : 2*
*Assigné : Agent Dev Frontend*
