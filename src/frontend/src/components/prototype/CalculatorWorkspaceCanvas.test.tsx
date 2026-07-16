import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  calculateBreakEven,
  calculateICE,
  calculateNPV,
  calculateRICE,
  calculateROI,
} from '../../services/api/calculators';
import { CalculatorWorkspaceCanvas } from './CalculatorWorkspaceCanvas';

vi.mock('../../services/api/calculators', () => ({
  calculateROI: vi.fn(),
  calculateICE: vi.fn(),
  calculateRICE: vi.fn(),
  calculateNPV: vi.fn(),
  calculateBreakEven: vi.fn(),
}));

const mockedROI = vi.mocked(calculateROI);
const mockedICE = vi.mocked(calculateICE);
const mockedRICE = vi.mocked(calculateRICE);
const mockedNPV = vi.mocked(calculateNPV);
const mockedBreakEven = vi.mocked(calculateBreakEven);

describe('Calculateurs conversationnels 0.40', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('ne calcule rien au chargement puis affiche le ROI renvoyé par le moteur', async () => {
    mockedROI.mockResolvedValue({
      investment: 10000, gain: 15000, roi_percent: 50, profit: 5000,
      interpretation: 'Très bon ROI de 50 %.',
    });
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);

    expect(mockedROI).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText('Investissement'), { target: { value: '10000' } });
    fireEvent.change(screen.getByLabelText('Gain total'), { target: { value: '15000' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculer avec le moteur local' }));

    await waitFor(() => expect(mockedROI).toHaveBeenCalledWith(10000, 15000));
    expect(await screen.findByTestId('calculator-result')).toHaveTextContent('50 %');
    expect(screen.getByTestId('calculator-result')).toHaveTextContent('5 000,00 €');
  });

  it('bloque localement un score ICE hors limites', () => {
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('tab', { name: 'ICE' }));
    fireEvent.change(screen.getByLabelText('Impact'), { target: { value: '11' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculer avec le moteur local' }));

    expect(screen.getByRole('alert')).toHaveTextContent('compris entre 1 et 10');
    expect(mockedICE).not.toHaveBeenCalled();
  });

  it('envoie les valeurs ICE visibles au moteur', async () => {
    mockedICE.mockResolvedValue({
      impact: 8, confidence: 7, ease: 6, score: 336,
      interpretation: 'Bon score ICE.',
    });
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('tab', { name: 'ICE' }));
    fireEvent.change(screen.getByLabelText('Impact'), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText('Confiance'), { target: { value: '7' } });
    fireEvent.change(screen.getByLabelText('Facilité'), { target: { value: '6' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculer avec le moteur local' }));

    await waitFor(() => expect(mockedICE).toHaveBeenCalledWith(8, 7, 6));
    expect(await screen.findByTestId('calculator-result')).toHaveTextContent('336');
  });

  it('envoie les valeurs RICE visibles au moteur', async () => {
    mockedRICE.mockResolvedValue({
      reach: 1000, impact: 2, confidence: 80, effort: 2, score: 800,
      interpretation: 'Très bon score RICE.',
    });
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('tab', { name: 'RICE' }));
    fireEvent.change(screen.getByLabelText('Portée par trimestre'), { target: { value: '1000' } });
    fireEvent.change(screen.getByLabelText('Impact RICE'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Confiance'), { target: { value: '80' } });
    fireEvent.change(screen.getByLabelText('Effort'), { target: { value: '2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculer avec le moteur local' }));

    await waitFor(() => expect(mockedRICE).toHaveBeenCalledWith(1000, 2, 80, 2));
    expect(await screen.findByTestId('calculator-result')).toHaveTextContent('800');
  });

  it('convertit le taux VAN en décimal et sépare les flux par point-virgule', async () => {
    mockedNPV.mockResolvedValue({
      initial_investment: 100000, cash_flows: [30000, 40000], discount_rate: 0.1,
      npv: -39669.42, interpretation: 'VAN négative.',
    });
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('tab', { name: 'VAN' }));
    fireEvent.change(screen.getByLabelText('Investissement initial'), { target: { value: '100000' } });
    fireEvent.change(screen.getByLabelText('Taux d’actualisation par période'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Flux de trésorerie par période'), { target: { value: '30000 ; 40000' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculer avec le moteur local' }));

    await waitFor(() => expect(mockedNPV).toHaveBeenCalledWith(100000, [30000, 40000], 0.1));
  });

  it('refuse un seuil de rentabilité sans marge unitaire positive', () => {
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('tab', { name: 'Seuil' }));
    fireEvent.change(screen.getByLabelText('Coûts fixes'), { target: { value: '50000' } });
    fireEvent.change(screen.getByLabelText('Coût variable par unité'), { target: { value: '60' } });
    fireEvent.change(screen.getByLabelText('Prix de vente par unité'), { target: { value: '50' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculer avec le moteur local' }));

    expect(screen.getByRole('alert')).toHaveTextContent('strictement supérieur au coût variable');
    expect(mockedBreakEven).not.toHaveBeenCalled();
    expect(mockedRICE).not.toHaveBeenCalled();
  });

  it('rejette un résultat non fini renvoyé par le backend', async () => {
    mockedROI.mockResolvedValue({
      investment: 1, gain: 1, roi_percent: null, profit: 0,
      interpretation: 'Résultat extrême.',
    } as unknown as Awaited<ReturnType<typeof calculateROI>>);
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Investissement'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Gain total'), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Calculer avec le moteur local' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('résultat numérique hors limites');
    expect(screen.queryByTestId('calculator-result')).not.toBeInTheDocument();
  });

  it('ignore un double déclenchement pendant le calcul', async () => {
    let resolveCalculation: ((value: Awaited<ReturnType<typeof calculateROI>>) => void) | undefined;
    mockedROI.mockImplementation(() => new Promise((resolve) => { resolveCalculation = resolve; }));
    render(<CalculatorWorkspaceCanvas onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Investissement'), { target: { value: '10000' } });
    fireEvent.change(screen.getByLabelText('Gain total'), { target: { value: '15000' } });
    const button = screen.getByRole('button', { name: 'Calculer avec le moteur local' });
    fireEvent.click(button);
    fireEvent.click(button);
    expect(mockedROI).toHaveBeenCalledTimes(1);

    resolveCalculation?.({ investment: 10000, gain: 15000, roi_percent: 50, profit: 5000, interpretation: 'ROI correct.' });
    expect(await screen.findByTestId('calculator-result')).toHaveTextContent('50 %');
  });
});
