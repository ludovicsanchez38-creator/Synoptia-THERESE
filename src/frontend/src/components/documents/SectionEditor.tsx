/**
 * THÉRÈSE v2 - SectionEditor (Atelier documentaire, D3)
 *
 * Édite la section active de la trame : titre + consigne (PATCH au blur),
 * contenu markdown rendu, rédaction en streaming SSE (D1). Composant
 * purement présentationnel + interaction (props uniquement, aucun accès
 * direct au store) - la mécanique du flux chunk par chunk (concaténation,
 * rechargement canonique au chunk `done`, conservation du partiel au chunk
 * `error`) est celle de `documentStore.draftSection` et déjà couverte par
 * `documentStore.test.ts` ; ce composant se contente d'être réactif au
 * `section.content` qu'on lui passe, re-rendu à chaque chunk par le parent
 * (`DocumentWorkspace`, abonné au store).
 *
 * Rendu markdown : react-markdown + remark-gfm, config sémantique alignée
 * sur `MessageBubble.tsx` (chat) - dupliquée ici plutôt que factorisée pour
 * ne pas toucher au chat (hors périmètre D3) ; réduite (pas de coloration
 * syntaxique de code, les sections de document sont surtout de la prose).
 * Pendant le stream, texte brut préformaté (mêmes raisons que MessageBubble :
 * éviter les sauts de mise en page d'un parsing markdown partiel).
 */
import { useEffect, useState } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AlertCircle, CheckCircle2, FileEdit, RotateCcw, Sparkles } from 'lucide-react';
import { Button } from '../ui/Button';
import type { DocumentSection, SectionUpdateRequest } from '../../services/api/documents';

// =============================================================================
// STATUTS (mêmes tags carrés theme-aware que OutlineTree)
// =============================================================================

const STATUS_META: Record<DocumentSection['status'], { label: string; className: string }> = {
  vide: { label: 'Vide', className: 'text-text-muted border-border/40 bg-surface' },
  brouillon: { label: 'Brouillon', className: 'text-warning border-warning/30 bg-warning/10' },
  validee: { label: 'Validée', className: 'text-success border-success/30 bg-success/10' },
};

// =============================================================================
// RENDU MARKDOWN (config alignée sur MessageBubble.tsx)
// =============================================================================

const markdownComponents: Components = {
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
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:underline">
        {children}
      </a>
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
    return <blockquote className="border-l-4 border-accent-cyan/50 pl-4 my-3 text-text-muted italic">{children}</blockquote>;
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
  code({ className, children }) {
    const isBlock = /language-/.test(className || '');
    if (isBlock) {
      return (
        <pre className="my-3 p-3 rounded-lg bg-bg border border-border overflow-x-auto text-sm">
          <code>{children}</code>
        </pre>
      );
    }
    return <code className="px-1.5 py-0.5 rounded bg-bg text-accent-cyan text-sm font-mono">{children}</code>;
  },
  table({ children }) {
    return (
      <div className="overflow-x-auto my-3">
        <table className="min-w-full border border-border rounded-lg overflow-hidden">{children}</table>
      </div>
    );
  },
  th({ children }) {
    return <th className="px-3 py-2 bg-surface text-left text-sm font-medium border-b border-border">{children}</th>;
  },
  td({ children }) {
    return <td className="px-3 py-2 text-sm border-b border-border">{children}</td>;
  },
};

// =============================================================================
// PROPS
// =============================================================================

export interface SectionEditorProps {
  section: DocumentSection | null;
  isStreaming: boolean;
  error: string | null;
  onUpdateSection: (sectionId: string, payload: SectionUpdateRequest) => void;
  onDraft: (sectionId: string, instruction?: string) => void;
  onValidate: (sectionId: string) => void;
}

// =============================================================================
// COMPOSANT
// =============================================================================

export function SectionEditor({ section, isStreaming, error, onUpdateSection, onDraft, onValidate }: SectionEditorProps) {
  const [titleDraft, setTitleDraft] = useState('');
  const [briefDraft, setBriefDraft] = useState('');
  const [instruction, setInstruction] = useState('');
  const [lastInstruction, setLastInstruction] = useState<string | undefined>(undefined);

  // Reset des buffers locaux uniquement quand la SECTION ACTIVE change (pas
  // à chaque re-render pendant le stream, sinon un titre en cours de frappe
  // serait écrasé par le contenu qui arrive chunk par chunk).
  useEffect(() => {
    setTitleDraft(section?.title ?? '');
    setBriefDraft(section?.brief ?? '');
    setInstruction('');
    setLastInstruction(undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- volontaire : uniquement au changement de section.id
  }, [section?.id]);

  if (!section) {
    return (
      <div className="flex-1 min-h-0 flex items-center justify-center text-center px-6" data-testid="section-editor-empty">
        <div>
          <FileEdit className="w-8 h-8 text-text-muted/40 mx-auto mb-2" />
          <p className="text-sm text-text-muted">Sélectionne une section dans la trame pour la rédiger.</p>
        </div>
      </div>
    );
  }

  const isValidee = section.status === 'validee';
  const meta = STATUS_META[section.status];
  const canValidate = !isValidee && !isStreaming && section.content.trim().length > 0;

  function handleTitleBlur() {
    const value = titleDraft.trim();
    if (section && value !== section.title) {
      onUpdateSection(section.id, { title: value });
    }
  }

  function handleBriefBlur() {
    if (section && briefDraft !== section.brief) {
      onUpdateSection(section.id, { brief: briefDraft });
    }
  }

  function handleRedact() {
    if (!section) return;
    setLastInstruction(undefined);
    onDraft(section.id);
  }

  function handleRetouch() {
    if (!section) return;
    const value = instruction.trim();
    if (!value) return;
    setLastInstruction(value);
    onDraft(section.id, value);
    setInstruction('');
  }

  function handleResume() {
    if (!section) return;
    if (lastInstruction) {
      onDraft(section.id, lastInstruction);
    } else {
      onDraft(section.id);
    }
  }

  function handleValidate() {
    if (!section) return;
    onValidate(section.id);
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-y-auto" data-testid="section-editor">
      {/* Titre + consigne (PATCH au blur) */}
      <div className="px-5 py-4 border-b border-border/40 space-y-3 shrink-0">
        <div className="flex items-center gap-2">
          <input
            value={titleDraft}
            onChange={(e) => setTitleDraft(e.target.value)}
            onBlur={handleTitleBlur}
            placeholder="Titre de la section"
            aria-label="Titre de la section"
            className="flex-1 min-w-0 px-2.5 py-1.5 bg-transparent text-lg font-semibold text-text focus:outline-none focus:bg-background/40 rounded-md transition-colors"
          />
          <span className={`shrink-0 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide rounded-[6px] border ${meta.className}`}>
            {meta.label}
          </span>
        </div>
        <textarea
          value={briefDraft}
          onChange={(e) => setBriefDraft(e.target.value)}
          onBlur={handleBriefBlur}
          placeholder="Consigne de rédaction"
          aria-label="Consigne de la section"
          rows={2}
          className="w-full px-2.5 py-1.5 bg-background/40 border border-border/40 rounded-md text-sm text-text-muted placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
        />
      </div>

      {/* Erreur causale + Reprendre */}
      {error && (
        <div className="mx-5 mt-4 flex items-center justify-between gap-3 px-3 py-2 rounded-[6px] border border-error/30 bg-error/10 shrink-0">
          <span className="flex items-center gap-2 text-sm text-error min-w-0">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="truncate">{error}</span>
          </span>
          <Button variant="ghost" size="sm" onClick={handleResume} className="shrink-0">
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            Reprendre
          </Button>
        </div>
      )}

      {/* Contenu : texte brut pendant le stream, markdown rendu sinon */}
      <div className="flex-1 px-5 py-4">
        <div className="prose prose-invert prose-sm max-w-none" data-testid="section-content">
          {isStreaming ? (
            <div className="whitespace-pre-wrap break-words leading-relaxed">
              {section.content}
              <span className="inline-block w-0.5 h-5 bg-accent-cyan animate-pulse ml-1 rounded-full align-text-bottom" />
            </div>
          ) : section.content ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {section.content}
            </ReactMarkdown>
          ) : (
            <p className="text-sm text-text-muted italic">Pas encore de contenu - clique sur « Rédiger » pour démarrer.</p>
          )}
        </div>

        {isValidee && section.summary && (
          <div className="mt-6 pt-4 border-t border-border/30">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted mb-1.5">Résumé</p>
            <p className="text-sm text-text-muted italic" data-testid="section-summary">
              {section.summary}
            </p>
          </div>
        )}
      </div>

      {/* Actions : Rédiger / Retoucher (instruction) / Valider */}
      <div className="px-5 py-3.5 border-t border-border/40 shrink-0">
        <div className="flex items-center gap-2">
          {!isValidee && (
            <Button variant="ghost" size="sm" onClick={handleRedact} disabled={isStreaming}>
              <Sparkles className="w-4 h-4 mr-1.5" />
              Rédiger
            </Button>
          )}
          <input
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Instruction de retouche (ex. plus concis, ajouter un exemple...)"
            aria-label="Instruction de retouche"
            className="flex-1 min-w-0 px-2.5 py-1.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
            disabled={isStreaming}
          />
          <Button variant="secondary" size="sm" onClick={handleRetouch} disabled={isStreaming || !instruction.trim()}>
            <FileEdit className="w-4 h-4 mr-1.5" />
            Retoucher
          </Button>
          {!isValidee && (
            <Button variant="primary" size="sm" onClick={handleValidate} disabled={!canValidate}>
              <CheckCircle2 className="w-4 h-4 mr-1.5" />
              Valider
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
