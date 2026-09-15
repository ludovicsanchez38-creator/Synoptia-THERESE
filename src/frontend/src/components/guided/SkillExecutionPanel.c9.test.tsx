/**
 * B-776 (cycle 9) : un format hors catalogue (valeur venue du serveur) faisait
 * planter le panneau (`config` indéfini, puis `config.icon`). Une valeur
 * inconnue dégrade l'affichage, elle ne casse pas l'écran.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SkillExecutionPanel } from './SkillExecutionPanel';
import { ImageGenerationPanel } from './ImageGenerationPanel';

describe('Panneaux guidés - B-776, valeur hors catalogue sans plantage', () => {
  it('SkillExecutionPanel : un format inconnu affiche un libellé de repli', () => {
    expect(() =>
      render(<SkillExecutionPanel skillId="x" format={'odt' as never} status="success" fileName="rapport.odt" onClose={vi.fn()} />),
    ).not.toThrow();
    expect(screen.getByText(/Fichier odt/)).toBeInTheDocument();
  });

  it('ImageGenerationPanel : un fournisseur inconnu affiche son identifiant', () => {
    expect(() =>
      render(<ImageGenerationPanel provider={'dalle-9' as never} status="idle" onClose={vi.fn()} />),
    ).not.toThrow();
    expect(screen.getByText(/dalle-9/)).toBeInTheDocument();
  });

  it('SkillExecutionPanel : un format absent au repos ne casse pas le libellé (B-828)', () => {
    expect(() => render(<SkillExecutionPanel skillId="x" format={undefined as never} status="idle" onClose={vi.fn()} />)).not.toThrow();
  });
});
