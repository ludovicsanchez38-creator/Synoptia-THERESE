# Story E2-05 : Ajouter le support Markdown dans les réponses

## Description

En tant que **utilisateur**,
Je veux **voir les réponses formatées en Markdown**,
Afin de **lire facilement les listes, code et titres**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E2-01
- **Fichiers concernés** :
  - `src/frontend/src/components/chat/MarkdownRenderer.tsx` (nouveau)
  - `src/frontend/src/styles/markdown.css` (nouveau)

## Critères d'acceptation

- [ ] Titres (h1-h4) stylés
- [ ] Listes ordonnées et non-ordonnées
- [ ] Code inline avec fond différent
- [ ] Code blocks avec syntax highlighting
- [ ] Liens cliquables (ouvrent dans navigateur externe)
- [ ] Gras et italique
- [ ] Tableaux basiques
- [ ] Citations (blockquote)

## Notes techniques

### Installation

```bash
npm install react-markdown remark-gfm rehype-highlight
```

### Composant MarkdownRenderer

```tsx
// components/chat/MarkdownRenderer.tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { open } from '@tauri-apps/plugin-shell';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeHighlight]}
      components={{
        // Headings
        h1: ({ children }) => (
          <h1 className="text-xl font-bold text-text mt-4 mb-2">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-lg font-semibold text-text mt-3 mb-2">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-base font-semibold text-text mt-2 mb-1">{children}</h3>
        ),

        // Paragraphs
        p: ({ children }) => (
          <p className="text-text-muted mb-2 leading-relaxed">{children}</p>
        ),

        // Lists
        ul: ({ children }) => (
          <ul className="list-disc list-inside mb-2 text-text-muted">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside mb-2 text-text-muted">{children}</ol>
        ),
        li: ({ children }) => <li className="mb-1">{children}</li>,

        // Code
        code: ({ inline, className, children }) => {
          if (inline) {
            return (
              <code className="px-1.5 py-0.5 bg-surface-elevated rounded text-accent-cyan text-sm font-mono">
                {children}
              </code>
            );
          }
          return (
            <code className={className}>
              {children}
            </code>
          );
        },
        pre: ({ children }) => (
          <pre className="bg-surface-elevated rounded-lg p-4 overflow-x-auto mb-3 text-sm">
            {children}
          </pre>
        ),

        // Links
        a: ({ href, children }) => (
          <a
            href={href}
            onClick={(e) => {
              e.preventDefault();
              if (href) open(href);
            }}
            className="text-accent-cyan hover:underline cursor-pointer"
          >
            {children}
          </a>
        ),

        // Blockquote
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-accent-magenta pl-4 italic text-text-muted my-2">
            {children}
          </blockquote>
        ),

        // Table
        table: ({ children }) => (
          <table className="w-full border-collapse mb-3">{children}</table>
        ),
        th: ({ children }) => (
          <th className="border border-border px-3 py-2 bg-surface-elevated text-left font-medium">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-border px-3 py-2">{children}</td>
        ),

        // Strong & Em
        strong: ({ children }) => (
          <strong className="font-semibold text-text">{children}</strong>
        ),
        em: ({ children }) => (
          <em className="italic">{children}</em>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
```

### Styles syntax highlighting

```css
/* styles/markdown.css */

/* Code blocks - theme dark */
.hljs {
  background: var(--color-surface-elevated);
  color: var(--color-text);
}

.hljs-keyword,
.hljs-selector-tag {
  color: var(--color-accent-magenta);
}

.hljs-string,
.hljs-attr {
  color: var(--color-accent-cyan);
}

.hljs-comment {
  color: var(--color-text-subtle);
  font-style: italic;
}

.hljs-function,
.hljs-title {
  color: #fbbf24; /* yellow */
}

.hljs-number {
  color: #a78bfa; /* purple */
}

.hljs-variable,
.hljs-params {
  color: var(--color-text);
}
```

### Utilisation dans MessageItem

```tsx
// components/chat/MessageItem.tsx
import { MarkdownRenderer } from './MarkdownRenderer';

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={/* ... */}>
      {/* ... avatar et header ... */}
      <div className="flex-1 min-w-0">
        {isUser ? (
          <p className="text-text-muted whitespace-pre-wrap">{message.content}</p>
        ) : (
          <MarkdownRenderer content={message.content} />
        )}
      </div>
    </div>
  );
}
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Exemples de rendu

### Code block

```python
def hello():
    print("Hello THÉRÈSE!")
```

### Liste

- Item 1
- Item 2
  - Sub-item

### Tableau

| Col 1 | Col 2 |
|-------|-------|
| A     | B     |

## Definition of Done

- [ ] Tous les éléments MD rendus correctement
- [ ] Syntax highlighting fonctionne
- [ ] Liens ouvrent dans navigateur externe
- [ ] Tests visuels passent

---

*Sprint : 2*
*Assigné : Agent Dev Frontend*
