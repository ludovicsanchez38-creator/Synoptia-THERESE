import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { cn } from '../../lib/utils';

const components: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  h1: ({ children }) => <h3 className="mb-2 mt-3 text-sm font-bold first:mt-0">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-2 mt-3 text-sm font-bold first:mt-0">{children}</h3>,
  h3: ({ children }) => <h3 className="mb-2 mt-3 text-sm font-bold first:mt-0">{children}</h3>,
  strong: ({ children }) => <strong className="font-semibold text-text">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-border pl-3 text-text-muted">
      {children}
    </blockquote>
  ),
  code: ({ children }) => (
    <code className="rounded-sm bg-surface-2 px-1 py-0.5 font-mono text-[0.92em] text-text">
      {children}
    </code>
  ),
  a: ({ href, children }) => {
    if (!href) return <span>{children}</span>;
    // B-435 : tout lien qui sort de la page (absolu ou relatif) s'ouvre isolé.
    const external = !href.startsWith('#');
    return (
      <a
        href={href}
        {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
        className="text-accent underline decoration-current/40 underline-offset-2"
      >
        {children}
      </a>
    );
  },
  img: ({ alt }) => (
    <span className="text-text-muted">{alt ? `Image non affichée : ${alt}` : 'Image non affichée'}</span>
  ),
};

function safeUrl(url: string): string {
  return /^(?:https?:|mailto:|tel:|\/|#)/i.test(url) ? url : '';
}

export function CompactMarkdown({
  children,
  className,
}: {
  children: string;
  className?: string;
}) {
  return (
    <div className={cn('break-words', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
        urlTransform={safeUrl}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
