import { memo, useState, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
// US-010 : sans remark-gfm, react-markdown ne parse pas les tableaux GFM
// (| a | b |), le barré (~~) ni les listes de tâches -> texte brut à l'écran
import remarkGfm from 'remark-gfm';
// hljs Light build : ~10x plus leger que Prism full (UltraJury perf)
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import typescript from 'react-syntax-highlighter/dist/esm/languages/hljs/typescript';
import bash from 'react-syntax-highlighter/dist/esm/languages/hljs/bash';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import css from 'react-syntax-highlighter/dist/esm/languages/hljs/css';
import xml from 'react-syntax-highlighter/dist/esm/languages/hljs/xml';
import yaml from 'react-syntax-highlighter/dist/esm/languages/hljs/yaml';
import sql from 'react-syntax-highlighter/dist/esm/languages/hljs/sql';
import { User, Bot, Copy, Check, AlertCircle, Coins, Bookmark, Download, FileDown, Image as ImageIcon, Cpu, Cloud } from 'lucide-react';

SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('js', javascript);
SyntaxHighlighter.registerLanguage('typescript', typescript);
SyntaxHighlighter.registerLanguage('ts', typescript);
SyntaxHighlighter.registerLanguage('bash', bash);
SyntaxHighlighter.registerLanguage('shell', bash);
SyntaxHighlighter.registerLanguage('sh', bash);
SyntaxHighlighter.registerLanguage('json', json);
SyntaxHighlighter.registerLanguage('css', css);
SyntaxHighlighter.registerLanguage('xml', xml);
SyntaxHighlighter.registerLanguage('html', xml);
SyntaxHighlighter.registerLanguage('markup', xml);
SyntaxHighlighter.registerLanguage('yaml', yaml);
SyntaxHighlighter.registerLanguage('yml', yaml);
SyntaxHighlighter.registerLanguage('sql', sql);
import { downloadGeneratedImage, getImageDownloadUrl, downloadSkillFile } from '../../services/api';
import { cn } from '../../lib/utils';
import { messageVariants } from '../../lib/animations';
import type { Message } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';

interface MessageBubbleProps {
  message: Message;
  onSaveAsCommand?: () => void;
}

// Code block with copy button
/** Taille lisible en français : 4917 -> « 4,8 Ko ». */
function formatFileSize(bytes: number): string {
  if (!bytes || bytes < 0) return '';
  if (bytes < 1024) return `${bytes} o`;
  const units = ['Ko', 'Mo', 'Go'];
  let value = bytes;
  let unit = '';
  for (const u of units) {
    value /= 1024;
    unit = u;
    if (value < 1024) break;
  }
  return `${value.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} ${unit}`;
}

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
        style={atomOneDark}
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

/**
 * US-010 : comparateur de memo explicite.
 *
 * MessageList recrée la closure onSaveAsCommand à chaque rendu, ce qui
 * cassait React.memo (comparaison shallow) : TOUTES les bulles assistant se
 * re-rendaient à chaque chunk streamé. On compare le message par identité
 * (le store est immutable : un message non touché garde sa référence) et
 * onSaveAsCommand par présence seulement.
 */
export function arePropsEqual(
  prev: MessageBubbleProps,
  next: MessageBubbleProps
): boolean {
  return (
    prev.message === next.message &&
    !prev.onSaveAsCommand === !next.onSaveAsCommand
  );
}

export const MessageBubble = memo(function MessageBubble({
  message,
  onSaveAsCommand,
}: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isImage = !!message.imageId;
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [skillDownloading, setSkillDownloading] = useState(false);

  const copyToClipboard = useCallback(async () => {
    if (isImage && message.imageId) {
      // Copier l'image dans le presse-papier
      try {
        const url = getImageDownloadUrl(message.imageId);
        const response = await fetch(url);
        const blob = await response.blob();
        await navigator.clipboard.write([
          new ClipboardItem({ [blob.type]: blob }),
        ]);
      } catch {
        // Fallback : copier le texte
        await navigator.clipboard.writeText(message.content);
      }
    } else {
      await navigator.clipboard.writeText(message.content);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content, message.imageId, isImage]);

  const handleImageDownload = useCallback(async () => {
    if (!message.imageId) return;
    setDownloading(true);
    try {
      await downloadGeneratedImage(message.imageId);
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setDownloading(false);
    }
  }, [message.imageId]);

  // BUG-131 : téléchargement réel du fichier généré par un skill (URL absolue
  // + save natif via downloadSkillFile), au lieu d'un lien markdown relatif.
  // BUG-136 : liste des fichiers du tour (skillFiles), repli sur le champ
  // legacy skillFile (messages persistés avant le fix).
  const skillFilesList = useMemo(
    () => message.skillFiles ?? (message.skillFile ? [message.skillFile] : []),
    [message.skillFiles, message.skillFile]
  );

  const handleSkillFileDownload = useCallback(async (file: NonNullable<typeof message.skillFile>) => {
    setSkillDownloading(true);
    try {
      await downloadSkillFile(file.file_id, file.file_name);
    } catch (err) {
      // Cas typique : conversation rechargée dont le fichier n'est plus sur
      // disque (introuvable/expiré) -> 404. On le dit à l'utilisateur au lieu
      // d'un clic sans effet.
      console.error('Skill file download failed:', err);
      useStatusStore.getState().addNotification({
        type: 'error',
        title: 'Téléchargement impossible',
        message: `Le fichier « ${file.file_name} » est introuvable. Régénère-le depuis le chat.`,
      });
    } finally {
      setSkillDownloading(false);
    }
  }, []);

  // Fichiers générés visibles (10/07) : ouvrir le dossier local des sorties
  // dans le Finder/Explorateur. Rendu seulement quand local_dir est connu
  // (desktop) ; en contexte web l'ouverture échouerait -> notification.
  const handleRevealInFolder = useCallback(async (localDir: string) => {
    try {
      const { open } = await import('@tauri-apps/plugin-shell');
      await open(localDir);
    } catch (err) {
      console.error('Reveal in folder failed:', err);
      useStatusStore.getState().addNotification({
        type: 'info',
        title: 'Dossier des fichiers générés',
        message: localDir,
        duration: 10000,
      });
    }
  }, []);

  // BUG-130 : quand un fichier a été généré, le contenu du message est le code
  // brut du générateur (```python ... ``` openpyxl/python-docx/pptx) streamé par
  // le modèle. Le fichier est déjà produit côté backend (auto-exécution du skill)
  // et porté par le bouton de téléchargement -> on masque ce mur de code, on ne
  // garde que la prose éventuelle du modèle (« Voici le tableau demandé »).
  const displayContent = useMemo(() => {
    if (skillFilesList.length === 0 || message.isStreaming) return message.content;
    const stripped = message.content
      // blocs de code fermés (```lang ... ```)
      .replace(/```[\w-]*\n?[\s\S]*?```/g, '')
      // bloc de code ouvert non fermé (réponse tronquée par max_tokens)
      .replace(/```[\w-]*\n?[\s\S]*$/g, '')
      .trim();
    return stripped || 'Voici ton fichier.';
  }, [message.content, skillFilesList, message.isStreaming]);


  return (
    <motion.div
      variants={messageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      layout={!message.isStreaming}
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
            ? 'bg-accent-magenta/10 border-[1.5px] border-accent-magenta/25 hover:border-[var(--btn-ink)] hover:shadow-[3px_3px_0_var(--btn-shadow-color)]'
            : 'bg-surface-elevated border border-border hover:border-accent-cyan/20 hover:shadow-[0_0_20px_rgba(34,211,238,0.05)]'
        )}
        style={{
          contain: 'layout style paint',
          willChange: message.isStreaming ? 'contents' : 'auto',
          // 56px = py-3 (24px) + 1 ligne leading-relaxed (~32px) : évite un saut initial
          minHeight: message.isStreaming ? '56px' : 'auto',
        }}
      >
        {/* Action buttons (copy + save as shortcut) */}
        <div className={cn(
          'absolute top-2 right-2 flex items-center gap-1 z-10',
          'opacity-0 group-hover:opacity-100 transition-all'
        )}>
          {/* Sauvegarder comme raccourci (assistant uniquement, pas en streaming, pas pour les images) */}
          {!isUser && !message.isStreaming && !isImage && onSaveAsCommand && (
            <button
              onClick={onSaveAsCommand}
              className={cn(
                'p-1.5 rounded-md transition-all',
                'hover:bg-surface text-text-muted hover:text-accent-cyan'
              )}
              title="Sauvegarder comme raccourci"
            >
              <Bookmark className="w-4 h-4" />
            </button>
          )}
          {/* Télécharger l'image (images uniquement) */}
          {isImage && !message.isStreaming && (
            <button
              onClick={handleImageDownload}
              disabled={downloading}
              className={cn(
                'p-1.5 rounded-md transition-all',
                'hover:bg-surface text-text-muted hover:text-accent-cyan',
                downloading && 'opacity-50'
              )}
              title="Enregistrer l'image"
            >
              <Download className={cn('w-4 h-4', downloading && 'animate-pulse')} />
            </button>
          )}
          {/* Copier le message / l'image */}
          <button
            onClick={copyToClipboard}
            className={cn(
              'p-1.5 rounded-md transition-all',
              'hover:bg-surface text-text-muted hover:text-text'
            )}
            title={isImage ? "Copier l'image" : "Copier le message"}
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : isImage ? (
              <ImageIcon className="w-4 h-4" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Markdown content - texte brut pendant le streaming pour éviter les sauts */}
        <div className="prose prose-invert prose-sm max-w-none">
          {message.isStreaming ? (
            <div className="whitespace-pre-wrap break-words leading-relaxed">
              {message.content}
            </div>
          ) : isUser ? (
            <div className="whitespace-pre-wrap break-words leading-relaxed">
              {message.content}
            </div>
          ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
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
            {displayContent}
          </ReactMarkdown>
          )}
        </div>

        {/* Fichiers générés visibles (10/07, ex-BUG-131) : bloc « Fichier
            généré » explicite - nom, taille, téléchargement, dossier local. */}
        {skillFilesList.length > 0 && !message.isStreaming && skillFilesList.map((file) => (
          <div key={file.file_id} className="mt-3 rounded-lg w-full max-w-sm bg-surface/60 border border-border overflow-hidden">
            <div className="flex items-center gap-2 px-3 pt-2.5">
              <FileDown className="w-3.5 h-3.5 text-accent-cyan shrink-0" />
              <span className="text-[11px] font-semibold uppercase tracking-wide text-accent-cyan">
                Fichier généré
              </span>
              <span className="text-xs text-text-muted ml-auto shrink-0">
                {formatFileSize(file.file_size)}
              </span>
            </div>
            <p className="px-3 pt-1 text-sm text-text truncate">{file.file_name}</p>
            <div className="flex items-center gap-1.5 px-2 py-2">
              <button
                type="button"
                onClick={() => handleSkillFileDownload(file)}
                disabled={skillDownloading}
                className={cn(
                  'flex-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-text',
                  'bg-surface-2 border border-border hover:border-accent-cyan/50 transition-all',
                  skillDownloading && 'opacity-60 cursor-wait'
                )}
                title={`Télécharger ${file.file_name}`}
              >
                {skillDownloading ? 'Téléchargement…' : 'Télécharger'}
              </button>
              {file.local_dir && (
                <button
                  type="button"
                  onClick={() => handleRevealInFolder(file.local_dir!)}
                  className="flex-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-text bg-surface-2 border border-border hover:border-accent-cyan/50 transition-all"
                  title={file.local_dir}
                >
                  Afficher dans le dossier
                </button>
              )}
            </div>
          </div>
        ))}

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
                  'flex items-center gap-1.5 px-2 py-1 rounded-[6px]',
                  message.uncertainty.confidence_level === 'low'
                    ? 'bg-red-500/10 text-red-400'
                    : message.uncertainty.confidence_level === 'medium'
                    ? 'bg-yellow-500/10 text-warning'
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

            {/* P0-IA-3 : badge local/cloud par message (constat C1/C2) */}
            {(() => {
              const prov = message.provider ?? message.usage?.provider;
              if (!prov) return null;
              const isLocal = prov === 'ollama';
              return (
                <div
                  className={`flex items-center gap-1.5 px-2 py-1 rounded-[6px] ${
                    isLocal ? 'bg-green-500/10 text-green-300' : 'bg-orange-500/10 text-orange-300'
                  }`}
                  title={
                    isLocal
                      ? 'Réponse locale (Ollama) : le traitement est resté sur ta machine, rien ne sort'
                      : `Réponse cloud (${prov}) : le traitement est sorti vers le fournisseur du modèle`
                  }
                >
                  {isLocal ? <Cpu className="w-3 h-3" /> : <Cloud className="w-3 h-3" />}
                  <span>{isLocal ? 'Local' : 'Cloud'}</span>
                </div>
              );
            })()}

            {/* Usage/cost display */}
            {message.usage && (
              <div
                className="flex items-center gap-1.5 px-2 py-1 rounded-[6px] bg-surface"
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
}, arePropsEqual);
