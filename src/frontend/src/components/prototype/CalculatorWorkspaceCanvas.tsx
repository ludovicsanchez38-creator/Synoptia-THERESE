import { useMemo, useRef, useState } from 'react';
import {
  Calculator,
  ChevronRight,
  Loader2,
  PanelRightClose,
  ShieldCheck,
} from 'lucide-react';
import {
  calculateBreakEven,
  calculateICE,
  calculateNPV,
  calculateRICE,
  calculateROI,
  type BreakEvenResult,
  type ICEResult,
  type NPVResult,
  type RICEResult,
  type ROIResult,
} from '../../services/api/calculators';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { handleRovingFocus } from '../../lib/rovingFocus';

type CalculatorId = 'roi' | 'ice' | 'rice' | 'npv' | 'break-even';
type CalculatorResult =
  | { id: 'roi'; data: ROIResult }
  | { id: 'ice'; data: ICEResult }
  | { id: 'rice'; data: RICEResult }
  | { id: 'npv'; data: NPVResult }
  | { id: 'break-even'; data: BreakEvenResult };

interface FormValues {
  investment: string;
  gain: string;
  impact: string;
  confidence: string;
  ease: string;
  reach: string;
  riceImpact: string;
  riceConfidence: string;
  effort: string;
  initialInvestment: string;
  cashFlows: string;
  discountRate: string;
  fixedCosts: string;
  variableCost: string;
  price: string;
}

const CALCULATORS: Array<{ id: CalculatorId; label: string; description: string; formula: string }> = [
  { id: 'roi', label: 'ROI', description: 'Rendement d’un investissement', formula: '(gain − investissement) ÷ investissement × 100' },
  { id: 'ice', label: 'ICE', description: 'Priorisation simple', formula: 'impact × confiance × facilité' },
  { id: 'rice', label: 'RICE', description: 'Priorisation pondérée', formula: '(portée × impact × confiance) ÷ effort' },
  { id: 'npv', label: 'VAN', description: 'Valeur actuelle nette', formula: '− investissement + somme des flux actualisés' },
  { id: 'break-even', label: 'Seuil', description: 'Seuil de rentabilité', formula: 'coûts fixes ÷ (prix − coût variable)' },
];

const INITIAL_VALUES: FormValues = {
  investment: '', gain: '', impact: '5', confidence: '5', ease: '5', reach: '', riceImpact: '1', riceConfidence: '80', effort: '',
  initialInvestment: '', cashFlows: '', discountRate: '', fixedCosts: '', variableCost: '', price: '',
};

function parseNumber(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value.trim().replace(',', '.'));
  return Number.isFinite(parsed) ? parsed : null;
}

function parseCashFlows(value: string): number[] | null {
  const parts = value.split(/[;\n]/).map((item) => item.trim()).filter(Boolean);
  if (parts.length === 0) return null;
  const parsed = parts.map(parseNumber);
  return parsed.every((item): item is number => item !== null) ? parsed : null;
}

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });
const currencyFormatter = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 });

function cleanInterpretation(value: string): string {
  return value.replace(/^[^\p{L}\p{N}]+/u, '').trim();
}

function assertFiniteResult(result: object, fields: string[]): void {
  const values = result as Record<string, unknown>;
  if (fields.some((field) => typeof values[field] !== 'number' || !Number.isFinite(values[field]))) {
    throw new Error('Le moteur a renvoyé un résultat numérique hors limites. Réduis les hypothèses et relance le calcul.');
  }
}

function InputField({
  label,
  value,
  onChange,
  suffix,
  min,
  max,
  inputId,
  invalid,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  suffix?: string;
  min?: number;
  max?: number;
  inputId: string;
  invalid: boolean;
}) {
  return (
    <label className="text-xs font-semibold text-text">
      {label}
      <span className="relative mt-1.5 block">
        <input
          id={inputId}
          aria-label={label}
          aria-invalid={invalid}
          aria-describedby={invalid ? 'calculator-form-error' : undefined}
          type="number"
          inputMode="decimal"
          value={value}
          min={min}
          max={max}
          step="any"
          onChange={(event) => onChange(event.target.value)}
          className="w-full rounded-[9px] border border-border px-3 py-2 pr-12 text-sm font-normal outline-none focus:border-[#22D3EE]"
        />
        {suffix && <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs font-medium text-text-muted">{suffix}</span>}
      </span>
    </label>
  );
}

function ResultCard({ result }: { result: CalculatorResult }) {
  const presentation = (() => {
    switch (result.id) {
      case 'roi':
        return { title: 'ROI', main: `${numberFormatter.format(result.data.roi_percent)} %`, detail: `Résultat net : ${currencyFormatter.format(result.data.profit)}` };
      case 'ice':
        return { title: 'Score ICE', main: numberFormatter.format(result.data.score), detail: 'Échelle maximale : 1 000' };
      case 'rice':
        return { title: 'Score RICE', main: numberFormatter.format(result.data.score), detail: `Portée : ${numberFormatter.format(result.data.reach)} · Effort : ${numberFormatter.format(result.data.effort)}` };
      case 'npv':
        return { title: 'Valeur actuelle nette', main: currencyFormatter.format(result.data.npv), detail: `Taux : ${numberFormatter.format(result.data.discount_rate * 100)} %` };
      case 'break-even':
        return {
          title: 'Seuil de rentabilité',
          main: `${numberFormatter.format(Math.ceil(result.data.break_even_units))} unités minimum`,
          detail: `Seuil théorique : ${numberFormatter.format(result.data.break_even_units)} · Chiffre d’affaires au minimum entier : ${currencyFormatter.format(Math.ceil(result.data.break_even_units) * result.data.price_per_unit)}`,
        };
    }
  })();

  return (
    <section className="rounded-[13px] border border-accent-cyan/30 bg-accent-tint p-4" data-testid="calculator-result" role="status" aria-live="polite">
      <div className="text-xs font-semibold uppercase tracking-[0.13em] text-text-muted">{presentation.title}</div>
      <div className="mt-1 text-3xl font-bold tracking-[-0.035em] text-text">{presentation.main}</div>
      <div className="mt-1 text-xs text-text-muted">{presentation.detail}</div>
      <p className="mt-3 border-t border-accent-cyan/30 pt-3 text-xs leading-5 text-accent">{cleanInterpretation(result.data.interpretation)}</p>
    </section>
  );
}

export function CalculatorWorkspaceCanvas({ onClose }: { onClose: () => void }) {
  const [active, setActive] = useState<CalculatorId>('roi');
  const [values, setValues] = useState<FormValues>(INITIAL_VALUES);
  const [result, setResult] = useState<CalculatorResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorFieldId, setErrorFieldId] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const pendingRef = useRef(false);
  const dialogRef = useRef<HTMLElement>(null);
  useDialogFocusTrap(dialogRef, { active: true, onEscape: onClose, isolateBackground: true });
  const activeInfo = useMemo(() => CALCULATORS.find((item) => item.id === active) ?? CALCULATORS[0], [active]);

  function update(name: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setResult(null);
    setError(null);
    setErrorFieldId(null);
  }

  function select(id: CalculatorId) {
    setActive(id);
    setResult(null);
    setError(null);
    setErrorFieldId(null);
  }

  function invalid(message: string, fieldId: string): never {
    setErrorFieldId(fieldId);
    requestAnimationFrame(() => document.getElementById(fieldId)?.focus());
    throw new Error(message);
  }

  async function calculate() {
    if (pendingRef.current) return;
    pendingRef.current = true;
    setError(null);
    setErrorFieldId(null);
    setResult(null);
    setPending(true);
    try {
      if (active === 'roi') {
        const investment = parseNumber(values.investment);
        const gain = parseNumber(values.gain);
        if (investment === null || investment <= 0) invalid('Renseigne un investissement strictement positif.', 'calculator-investment');
        if (gain === null) invalid('Renseigne un gain valide.', 'calculator-gain');
        const data = await calculateROI(investment, gain);
        assertFiniteResult(data, ['investment', 'gain', 'roi_percent', 'profit']);
        setResult({ id: active, data });
      } else if (active === 'ice') {
        const impact = parseNumber(values.impact);
        const confidence = parseNumber(values.confidence);
        const ease = parseNumber(values.ease);
        if (impact === null || impact < 1 || impact > 10) invalid('L’impact doit être compris entre 1 et 10.', 'calculator-impact');
        if (confidence === null || confidence < 1 || confidence > 10) invalid('La confiance doit être comprise entre 1 et 10.', 'calculator-confidence');
        if (ease === null || ease < 1 || ease > 10) invalid('La facilité doit être comprise entre 1 et 10.', 'calculator-ease');
        const data = await calculateICE(impact!, confidence!, ease!);
        assertFiniteResult(data, ['impact', 'confidence', 'ease', 'score']);
        setResult({ id: active, data });
      } else if (active === 'rice') {
        const reach = parseNumber(values.reach);
        const impact = parseNumber(values.riceImpact);
        const confidence = parseNumber(values.riceConfidence);
        const effort = parseNumber(values.effort);
        if (reach === null || reach <= 0 || impact === null || impact <= 0 || confidence === null || confidence < 0 || confidence > 100 || effort === null || effort <= 0) {
          if (reach === null || reach <= 0) invalid('La portée doit être strictement positive.', 'calculator-reach');
          if (impact === null || impact <= 0) invalid('L’impact doit être strictement positif.', 'calculator-rice-impact');
          if (confidence === null || confidence < 0 || confidence > 100) invalid('La confiance doit être comprise entre 0 et 100 %.', 'calculator-rice-confidence');
          invalid('L’effort doit être strictement positif.', 'calculator-effort');
        }
        const data = await calculateRICE(reach, impact, confidence, effort);
        assertFiniteResult(data, ['reach', 'impact', 'confidence', 'effort', 'score']);
        setResult({ id: active, data });
      } else if (active === 'npv') {
        const initialInvestment = parseNumber(values.initialInvestment);
        const cashFlows = parseCashFlows(values.cashFlows);
        const discountPercent = parseNumber(values.discountRate);
        if (initialInvestment === null || initialInvestment < 0 || !cashFlows || discountPercent === null || discountPercent < 0 || discountPercent > 100) {
          if (initialInvestment === null || initialInvestment < 0) invalid('Renseigne un investissement positif ou nul.', 'calculator-initial-investment');
          if (!cashFlows) invalid('Renseigne au moins un flux de trésorerie valide.', 'calculator-cash-flows');
          invalid('Le taux doit être compris entre 0 et 100 %.', 'calculator-discount-rate');
        }
        const data = await calculateNPV(initialInvestment, cashFlows, discountPercent / 100);
        assertFiniteResult(data, ['initial_investment', 'discount_rate', 'npv']);
        if (!Array.isArray(data.cash_flows) || data.cash_flows.some((value) => !Number.isFinite(value))) {
          throw new Error('Le moteur a renvoyé des flux numériques hors limites. Réduis les hypothèses et relance le calcul.');
        }
        setResult({ id: active, data });
      } else {
        const fixedCosts = parseNumber(values.fixedCosts);
        const variableCost = parseNumber(values.variableCost);
        const price = parseNumber(values.price);
        if (fixedCosts === null || fixedCosts < 0 || variableCost === null || variableCost < 0 || price === null || price <= variableCost) {
          if (fixedCosts === null || fixedCosts < 0) invalid('Les coûts fixes doivent être positifs ou nuls.', 'calculator-fixed-costs');
          if (variableCost === null || variableCost < 0) invalid('Le coût variable doit être positif ou nul.', 'calculator-variable-cost');
          invalid('Le prix doit être strictement supérieur au coût variable.', 'calculator-price');
        }
        const data = await calculateBreakEven(fixedCosts, variableCost, price);
        assertFiniteResult(data, ['fixed_costs', 'variable_cost_per_unit', 'price_per_unit', 'break_even_units', 'break_even_revenue']);
        setResult({ id: active, data });
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Le calcul n’a pas pu être effectué.');
    } finally {
      pendingRef.current = false;
      setPending(false);
    }
  }

  return (
    <aside ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="calculator-workspace-title" tabIndex={-1} className="absolute inset-y-0 right-0 z-20 flex h-full w-full max-w-[620px] flex-col border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] sm:w-[calc(100%-48px)] xl:relative xl:w-[43%] xl:min-w-[440px] xl:shadow-none" data-testid="calculator-workspace-canvas">
      <button type="button" onClick={onClose} aria-label="Fermer les calculateurs" className="absolute right-3 top-3 z-30 grid h-11 w-11 place-items-center rounded-[9px] border border-border bg-surface text-text-muted shadow-sm hover:text-text"><PanelRightClose className="h-4 w-4" /></button>
      <header className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted"><Calculator className="h-3.5 w-3.5" />Moteurs déterministes</div>
        <h2 id="calculator-workspace-title" data-dialog-autofocus tabIndex={-1} className="mt-2 text-xl font-bold tracking-[-0.02em] text-text outline-none">Calculateurs vérifiables</h2>
        <p className="mt-1 text-sm text-text-muted">Les valeurs sont envoyées au moteur de calcul local, jamais estimées par le modèle.</p>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
        <div role="tablist" aria-label="Type de calcul" className="grid grid-cols-5 gap-1 rounded-[11px] border border-border bg-surface p-1">
          {CALCULATORS.map((calculator) => (
            <button key={calculator.id} id={`calculator-tab-${calculator.id}`} role="tab" aria-selected={active === calculator.id} aria-controls={`calculator-panel-${calculator.id}`} tabIndex={active === calculator.id ? 0 : -1} type="button" disabled={pending} onKeyDown={(event) => handleRovingFocus(event, '[role="tab"]', 'horizontal')} onClick={() => select(calculator.id)} className={`rounded-[8px] px-2 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-60 ${active === calculator.id ? 'bg-text text-white' : 'text-text-muted hover:bg-bg'}`}>{calculator.label}</button>
          ))}
        </div>

        <section id={`calculator-panel-${active}`} role="tabpanel" aria-labelledby={`calculator-tab-${active}`} className="mt-4 rounded-[13px] border border-border bg-surface p-4">
          <h3 className="text-sm font-bold text-text">{activeInfo.description}</h3>
          <div className="mt-2 flex items-center gap-2 rounded-[9px] bg-surface-2 px-3 py-2 text-xs text-text-muted"><ChevronRight className="h-3.5 w-3.5 shrink-0 text-[var(--k3)]" />{activeInfo.formula}</div>

          <fieldset disabled={pending} className="mt-4 grid gap-3 sm:grid-cols-2">
            <legend className="sr-only">Hypothèses pour {activeInfo.description}</legend>
            {active === 'roi' && <><InputField inputId="calculator-investment" invalid={errorFieldId === 'calculator-investment'} label="Investissement" value={values.investment} onChange={(value) => update('investment', value)} suffix="€" min={0} /><InputField inputId="calculator-gain" invalid={errorFieldId === 'calculator-gain'} label="Gain total" value={values.gain} onChange={(value) => update('gain', value)} suffix="€" /></>}
            {active === 'ice' && <><InputField inputId="calculator-impact" invalid={errorFieldId === 'calculator-impact'} label="Impact" value={values.impact} onChange={(value) => update('impact', value)} suffix="/ 10" min={1} max={10} /><InputField inputId="calculator-confidence" invalid={errorFieldId === 'calculator-confidence'} label="Confiance" value={values.confidence} onChange={(value) => update('confidence', value)} suffix="/ 10" min={1} max={10} /><InputField inputId="calculator-ease" invalid={errorFieldId === 'calculator-ease'} label="Facilité" value={values.ease} onChange={(value) => update('ease', value)} suffix="/ 10" min={1} max={10} /></>}
            {active === 'rice' && <><InputField inputId="calculator-reach" invalid={errorFieldId === 'calculator-reach'} label="Portée par trimestre" value={values.reach} onChange={(value) => update('reach', value)} min={0} /><label className="text-sm font-semibold text-text">Impact<select id="calculator-rice-impact" aria-label="Impact RICE" aria-invalid={errorFieldId === 'calculator-rice-impact'} aria-describedby={errorFieldId === 'calculator-rice-impact' ? 'calculator-form-error' : undefined} value={values.riceImpact} onChange={(event) => update('riceImpact', event.target.value)} className="mt-1.5 w-full rounded-[9px] border border-border bg-surface px-3 py-2 text-sm font-normal outline-none focus:border-accent"><option value="0.25">Minimal · 0,25</option><option value="0.5">Faible · 0,5</option><option value="1">Moyen · 1</option><option value="2">Fort · 2</option><option value="3">Massif · 3</option></select></label><InputField inputId="calculator-rice-confidence" invalid={errorFieldId === 'calculator-rice-confidence'} label="Confiance" value={values.riceConfidence} onChange={(value) => update('riceConfidence', value)} suffix="%" min={0} max={100} /><InputField inputId="calculator-effort" invalid={errorFieldId === 'calculator-effort'} label="Effort" value={values.effort} onChange={(value) => update('effort', value)} suffix="mois-personne" min={0} /></>}
            {active === 'npv' && <><InputField inputId="calculator-initial-investment" invalid={errorFieldId === 'calculator-initial-investment'} label="Investissement initial" value={values.initialInvestment} onChange={(value) => update('initialInvestment', value)} suffix="€" min={0} /><InputField inputId="calculator-discount-rate" invalid={errorFieldId === 'calculator-discount-rate'} label="Taux d’actualisation par période" value={values.discountRate} onChange={(value) => update('discountRate', value)} suffix="%" min={0} max={100} /><label className="text-sm font-semibold text-text sm:col-span-2">Flux de trésorerie par période<textarea id="calculator-cash-flows" aria-label="Flux de trésorerie par période" aria-invalid={errorFieldId === 'calculator-cash-flows'} aria-describedby={errorFieldId === 'calculator-cash-flows' ? 'calculator-form-error' : undefined} value={values.cashFlows} onChange={(event) => update('cashFlows', event.target.value)} rows={3} placeholder="30000 ; 40000 ; 50000" className="mt-1.5 w-full resize-y rounded-[9px] border border-border px-3 py-2 text-sm font-normal outline-none focus:border-accent" /><span className="mt-1 block text-xs font-normal text-text-muted">Sépare les périodes par un point-virgule ou un retour à la ligne. Le taux et les flux doivent utiliser la même période, par exemple une année.</span></label></>}
            {active === 'break-even' && <><InputField inputId="calculator-fixed-costs" invalid={errorFieldId === 'calculator-fixed-costs'} label="Coûts fixes" value={values.fixedCosts} onChange={(value) => update('fixedCosts', value)} suffix="€" min={0} /><InputField inputId="calculator-variable-cost" invalid={errorFieldId === 'calculator-variable-cost'} label="Coût variable par unité" value={values.variableCost} onChange={(value) => update('variableCost', value)} suffix="€" min={0} /><InputField inputId="calculator-price" invalid={errorFieldId === 'calculator-price'} label="Prix de vente par unité" value={values.price} onChange={(value) => update('price', value)} suffix="€" min={0} /></>}
          </fieldset>
          {error && <div id="calculator-form-error" role="alert" className="mt-3 rounded-[9px] border border-error/40 bg-[var(--color-error-tint)] px-3 py-2 text-sm leading-5 text-error">{error}</div>}
          <button type="button" disabled={pending} onClick={() => void calculate()} className="mt-4 flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">{pending && <Loader2 className="h-4 w-4 animate-spin" />}Calculer avec le moteur local</button>
          <div className="sr-only" role="progressbar" aria-label="Progression du calcul" aria-valuemin={0} aria-valuemax={1} aria-valuenow={result ? 1 : 0} aria-valuetext={pending ? 'Calcul en cours' : result ? 'Calcul terminé' : 'Calcul non lancé'} />
        </section>

        {result && <div className="mt-4"><ResultCard result={result} /></div>}
        <div className="mt-4 flex items-start gap-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3 text-xs leading-5 text-accent"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />Le résultat vient de la formule affichée et de l’API locale. Il n’est ni mémorisé ni transmis à un modèle IA.</div>
      </div>
    </aside>
  );
}
