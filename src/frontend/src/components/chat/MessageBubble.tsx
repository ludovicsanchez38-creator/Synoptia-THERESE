import { memo, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, Copy, Check, AlertCircle, Coins } from 'lucide-react';
import { cn } from '../../lib/utils';
import { messageVariants } from '../../lib/animations';
import type { Message } from '../../stores/chatStore';

interface MessageBubbleProps {
  message: Message;
}

// Code block with copy button
function CodeBlock({
  language,
  children,
}: {
  language: string;
  children: string;
}) {
  const [copied, setCopied] = useState(false);

  const copyCode = useCallback(async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [children]);

  return (
    <div className="relative group/code my-3">
      {/* Language badge + Copy button */}
      <div className="absolute top-0 right-0 left-0 flex items-center justify-between px-3 py-1 bg-[#1e1e1e] rounded-t-lg border-b border-gray-700">
        <span className="text-xs text-gray-400 font-mono">{language}</span>
        <button
          onClick={copyCode}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              <span>Copié</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copier</span>
            </>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
          paddingTop: '2.5rem', // Space for header
        }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
}

export const MessageBubble = memo(function MessageBubble({
  message,
}: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const copyToClipboard = useCallback(async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content]);

  return (
    <motion.div
      variants={messageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      layout
      className={cn(
        'flex gap-3 group',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar with glow effect */}
      <div
        className={cn(
          'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all',
          isUser
            ? 'bg-accent-magenta/20 text-accent-magenta shadow-[0_0_12px_rgba(225,29,141,0.2)]'
            : 'bg-accent-cyan/20 text-accent-cyan shadow-[0_0_12px_rgba(34,211,238,0.2)]'
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Content with premium styling */}
      <div
        className={cn(
          'relative flex-1 max-w-[85%] rounded-2xl px-4 py-3 transition-all',
          isUser
            ? 'bg-gradient-to-br from-accent-magenta/12 to-accent-magenta/6 border border-accent-magenta/20 hover:border-accent-magenta/30 hover:shadow-[0_0_20px_rgba(225,29,141,0.1)]'
            : 'bg-surface-elevated border border-border hover:border-accent-cyan/20 hover:shadow-[0_0_20px_rgba(34,211,238,0.05)]'
        )}
      >
        {/* Copy full message button */}
        <button
          onClick={copyToClipboard}
          className={cn(
            'absolute top-2 right-2 p-1.5 rounded-md transition-all z-10',
            'opacity-0 group-hover:opacity-100',
            'hover:bg-surface text-text-muted hover:text-text'
          )}
          title="Copier le message"
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-500" />
          ) : (
            <Copy className="w-4 h-4" />
          )}
        </button>

        {/* Markdown content */}
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                const codeString = String(children).replace(/\n$/, '');
                const isInline = !match && !codeString.includes('\n');

                if (isInline) {
                  return (
                    <code
                      className="px-1.5 py-0.5 rounded bg-bg text-accent-cyan text-sm font-mono"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                }

                return (
                  <CodeBlock language={match?.[1] || 'text'}>
                    {codeString}
                  </CodeBlock>
                );
              },
              p({ children }) {
                return <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>;
              },
              ul({ children }) {
                return <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>;
              },
              ol({ children }) {
                return <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>;
              },
              li({ children }) {
                return <li className="text-text">{children}</li>;
              },
              a({ href, children }) {
                return (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent-cyan hover:underline"
                  >
                    {children}
                  </a>
                );
              },
              img({ src, alt }) {
                return (
                  <div className="my-3 rounded-xl overflow-hidden border border-border bg-black/20">
                    <img
                      src={src}
                      alt={alt || 'Image'}
                      className="w-full h-auto max-h-96 object-contain"
                      loading="lazy"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        target.parentElement!.innerHTML = `
                          <div class="p-8 flex flex-col items-center justify-center text-text-muted">
                            <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                            </svg>
                            <span class="text-sm">Impossible de charger l'image</span>
                          </div>
                        `;
                      }}
                    />
                  </div>
                );
              },
              h1({ children }) {
                return <h1 className="text-xl font-bold mb-3 mt-4 first:mt-0">{children}</h1>;
              },
              h2({ children }) {
                return <h2 className="text-lg font-bold mb-2 mt-4 first:mt-0">{children}</h2>;
              },
              h3({ children }) {
                return <h3 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h3>;
              },
              blockquote({ children }) {
                return (
                  <blockquote className="border-l-4 border-accent-cyan/50 pl-4 my-3 text-text-muted italic">
                    {children}
                  </blockquote>
                );
              },
              hr() {
                return <hr className="my-4 border-border" />;
              },
              strong({ children }) {
                return <strong className="font-semibold text-text">{children}</strong>;
              },
              em({ children }) {
                return <em className="italic">{children}</em>;
              },
              table({ children }) {
                return (
                  <div className="overflow-x-auto my-3">
                    <table className="min-w-full border border-border rounded-lg overflow-hidden">
                      {children}
                    </table>
                  </div>
                );
              },
              th({ children }) {
                return (
                  <th className="px-3 py-2 bg-surface text-left text-sm font-medium border-b border-border">
                    {children}
                  </th>
                );
              },
              td({ children }) {
                return (
                  <td className="px-3 py-2 text-sm border-b border-border">
                    {children}
                  </td>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Streaming cursor indicator */}
        {message.isStreaming && (
          <span className="inline-block w-0.5 h-5 bg-accent-cyan animate-pulse ml-1 rounded-full shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
        )}

        {/* Message metadata (US-ESC-01, US-ESC-02) */}
        {!isUser && !message.isStreaming && (message.uncertainty || message.usage) && (
          <div className="mt-3 pt-2 border-t border-border/50 flex flex-wrap items-center gap-3 text-xs text-text-muted">
            {/* Uncertainty indicator */}
            {message.uncertainty?.is_uncertain && (
              <div
                className={cn(
                  'flex items-center gap-1.5 px-2 py-1 rounded-full',
                  message.uncertainty.confidence_level === 'low'
                    ? 'bg-red-500/10 text-red-400'
                    : message.uncertainty.confidence_level === 'medium'
                    ? 'bg-yellow-500/10 text-yellow-400'
                    : 'bg-green-500/10 text-green-400'
                )}
                title={message.uncertainty.uncertainty_phrases.join(', ')}
              >
                <AlertCircle className="w-3 h-3" />
                <span>
                  {message.uncertainty.confidence_level === 'low'
                    ? 'Confiance faible'
                    : message.uncertainty.confidence_level === 'medium'
                    ? 'Confiance moyenne'
                    : 'Confiance haute'}
                </span>
              </div>
            )}

            {/* Usage/cost display */}
            {message.usage && (
              <div
                className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-surface"
                title="Coût estimé de cette requête API (consommation de tokens). Ce n'est pas une facture."
              >
                <Coins className="w-3 h-3" />
                <span>
                  {message.usage.input_tokens + message.usage.output_tokens} tokens
                  {message.usage.cost_eur > 0 && (
                    <> - {message.usage.cost_eur.toFixed(4)} EUR</>
                  )}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
});
