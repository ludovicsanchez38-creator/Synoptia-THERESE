/**
 * THÉRÈSE v2 - Mission Stepper
 *
 * Indicateur horizontal de progression : Spec → Analyse → Implémentation → Tests → Review
 */

import React from 'react';
import { FileText, Search, Code, TestTube, Eye, Check } from 'lucide-react';
import type { MissionPhase } from '../../services/api/agents';
import { cn } from '../../lib/utils';

const STEPS: { phase: MissionPhase; label: string; icon: React.ReactNode }[] = [
  { phase: 'spec', label: 'Spec', icon: <FileText size={14} /> },
  { phase: 'analysis', label: 'Analyse', icon: <Search size={14} /> },
  { phase: 'implementation', label: 'Code', icon: <Code size={14} /> },
  { phase: 'testing', label: 'Tests', icon: <TestTube size={14} /> },
  { phase: 'review', label: 'Review', icon: <Eye size={14} /> },
];

const PHASE_ORDER: MissionPhase[] = ['spec', 'analysis', 'implementation', 'testing', 'review', 'done'];

interface Props {
  currentPhase: MissionPhase;
}

export function MissionStepper({ currentPhase }: Props) {
  const currentIdx = PHASE_ORDER.indexOf(currentPhase);

  return (
    <div className="flex items-center gap-1 px-3 py-2">
      {STEPS.map((step, i) => {
        const stepIdx = PHASE_ORDER.indexOf(step.phase);
        const isActive = stepIdx === currentIdx;
        const isDone = stepIdx < currentIdx;

        return (
          <React.Fragment key={step.phase}>
            {i > 0 && (
              <div className={cn('h-px flex-1', isDone ? 'bg-accent' : 'bg-border')} />
            )}
            <div
              className={cn(
                'flex items-center gap-1 rounded-sm border px-2 py-1 text-xs font-medium transition-colors',
                isActive && 'border-accent/30 bg-accent-tint text-accent',
                isDone && 'border-transparent bg-surface-2 text-accent',
                !isActive && !isDone && 'border-transparent bg-surface text-text-muted',
              )}
            >
              {isDone ? <Check size={12} /> : step.icon}
              <span className="hidden sm:inline">{step.label}</span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}
