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
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  suffix?: string;
  min?: number;
  max?: number;
}) {
  return (
    <label className="text-xs font-semibold text-text">
      {label}
      <span className="relative mt-1.5 block">
        <input
          aria-label={label}
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
    <section className="rounded-[13px] border border-accent-cyan/30 bg-accent-tint p-4" data-testid="calculator-result">
      <div className="text-[10px] font-semibold uppercase tracking-[0.13em] text-text-muted">{presentation.title}</div>
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
  const [pending, setPending] = useState(false);
  const pendingRef = useRef(false);
  const activeInfo = useMemo(() => CALCULATORS.find((item) => item.id === active) ?? CALCULATORS[0], [active]);

  function update(name: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setResult(null);
    setError(null);
  }

  function select(id: CalculatorId) {
    setActive(id);
    setResult(null);
    setError(null);
  }

  async function calculate() {
    if (pendingRef.current) return;
    pendingRef.current = true;
    setError(null);
    setResult(null);
    setPending(true);
    try {
      if (active === 'roi') {
        const investment = parseNumber(values.investment);
        const gain = parseNumber(values.gain);
        if (investment === null || investment <= 0 || gain === null) throw new Error('Renseigne un investissement strictement positif et un gain valide.');
        const data = await calculateROI(investment, gain);
        assertFiniteResult(data, ['investment', 'gain', 'roi_percent', 'profit']);
        setResult({ id: active, data });
      } else if (active === 'ice') {
        const impact = parseNumber(values.impact);
        const confidence = parseNumber(values.confidence);
        const ease = parseNumber(values.ease);
        if ([impact, confidence, ease].some((value) => value === null || value < 1 || value > 10)) throw new Error('Impact, confiance et facilité doivent être compris entre 1 et 10.');
        const data = await calculateICE(impact!, confidence!, ease!);
        assertFiniteResult(data, ['impact', 'confidence', 'ease', 'score']);
        setResult({ id: active, data });
      } else if (active === 'rice') {
        const reach = parseNumber(values.reach);
        const impact = parseNumber(values.riceImpact);
        const confidence = parseNumber(values.riceConfidence);
        const effort = parseNumber(values.effort);
        if (reach === null || reach <= 0 || impact === null || impact <= 0 || confidence === null || confidence < 0 || confidence > 100 || effort === null || effort <= 0) {
          throw new Error('La portée, l’impact et l’effort doivent être positifs. La confiance doit être comprise entre 0 et 100 %.');
        }
        const data = await calculateRICE(reach, impact, confidence, effort);
        assertFiniteResult(data, ['reach', 'impact', 'confidence', 'effort', 'score']);
        setResult({ id: active, data });
      } else if (active === 'npv') {
        const initialInvestment = parseNumber(values.initialInvestment);
        const cashFlows = parseCashFlows(values.cashFlows);
        const discountPercent = parseNumber(values.discountRate);
        if (initialInvestment === null || initialInvestment < 0 || !cashFlows || discountPercent === null || discountPercent < 0 || discountPercent > 100) {
          throw new Error('Renseigne un investissement positif ou nul, au moins un flux valide et un taux compris entre 0 et 100 %.');
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
          throw new Error('Les coûts doivent être positifs ou nuls et le prix doit être strictement supérieur au coût variable.');
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
    <aside className="absolute inset-y-0 right-0 z-20 flex h-full w-full max-w-[620px] flex-col border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] sm:w-[calc(100%-48px)] xl:relative xl:w-[43%] xl:min-w-[440px] xl:shadow-none" data-testid="calculator-workspace-canvas">
      <button type="button" onClick={onClose} aria-label="Fermer les calculateurs" className="absolute right-4 top-3.5 z-30 grid h-9 w-9 place-items-center rounded-[9px] border border-border bg-surface text-text-muted shadow-sm hover:text-text"><PanelRightClose className="h-4 w-4" /></button>
      <header className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted"><Calculator className="h-3.5 w-3.5" />Moteurs déterministes</div>
        <h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">Calculateurs vérifiables</h2>
        <p className="mt-1 text-sm text-text-muted">Les valeurs sont envoyées au moteur de calcul local, jamais estimées par le modèle.</p>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
        <div className="grid grid-cols-5 gap-1 rounded-[11px] border border-border bg-surface p-1">
          {CALCULATORS.map((calculator) => (
            <button key={calculator.id} type="button" disabled={pending} onClick={() => select(calculator.id)} className={`rounded-[8px] px-2 py-2 text-[11px] font-semibold disabled:cursor-not-allowed disabled:opacity-60 ${active === calculator.id ? 'bg-text text-white' : 'text-text-muted hover:bg-bg'}`}>{calculator.label}</button>
          ))}
        </div>

        <section className="mt-4 rounded-[13px] border border-border bg-surface p-4">
          <h3 className="text-sm font-bold text-text">{activeInfo.description}</h3>
          <div className="mt-2 flex items-center gap-2 rounded-[9px] bg-surface-2 px-3 py-2 text-[11px] text-text-muted"><ChevronRight className="h-3.5 w-3.5 shrink-0 text-[var(--k3)]" />{activeInfo.formula}</div>

          <fieldset disabled={pending} className="mt-4 grid gap-3 sm:grid-cols-2">
            {active === 'roi' && <><InputField label="Investissement" value={values.investment} onChange={(value) => update('investment', value)} suffix="€" min={0} /><InputField label="Gain total" value={values.gain} onChange={(value) => update('gain', value)} suffix="€" /></>}
            {active === 'ice' && <><InputField label="Impact" value={values.impact} onChange={(value) => update('impact', value)} suffix="/ 10" min={1} max={10} /><InputField label="Confiance" value={values.confidence} onChange={(value) => update('confidence', value)} suffix="/ 10" min={1} max={10} /><InputField label="Facilité" value={values.ease} onChange={(value) => update('ease', value)} suffix="/ 10" min={1} max={10} /></>}
            {active === 'rice' && <><InputField label="Portée par trimestre" value={values.reach} onChange={(value) => update('reach', value)} min={0} /><label className="text-xs font-semibold text-text">Impact<select aria-label="Impact RICE" value={values.riceImpact} onChange={(event) => update('riceImpact', event.target.value)} className="mt-1.5 w-full rounded-[9px] border border-border bg-surface px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]"><option value="0.25">Minimal · 0,25</option><option value="0.5">Faible · 0,5</option><option value="1">Moyen · 1</option><option value="2">Fort · 2</option><option value="3">Massif · 3</option></select></label><InputField label="Confiance" value={values.riceConfidence} onChange={(value) => update('riceConfidence', value)} suffix="%" min={0} max={100} /><InputField label="Effort" value={values.effort} onChange={(value) => update('effort', value)} suffix="mois-personne" min={0} /></>}
            {active === 'npv' && <><InputField label="Investissement initial" value={values.initialInvestment} onChange={(value) => update('initialInvestment', value)} suffix="€" min={0} /><InputField label="Taux d’actualisation par période" value={values.discountRate} onChange={(value) => update('discountRate', value)} suffix="%" min={0} max={100} /><label className="text-xs font-semibold text-text sm:col-span-2">Flux de trésorerie par période<textarea aria-label="Flux de trésorerie par période" value={values.cashFlows} onChange={(event) => update('cashFlows', event.target.value)} rows={3} placeholder="30000 ; 40000 ; 50000" className="mt-1.5 w-full resize-y rounded-[9px] border border-border px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]" /><span className="mt-1 block text-[10px] font-normal text-text-muted">Sépare les périodes par un point-virgule ou un retour à la ligne. Le taux et les flux doivent utiliser la même période, par exemple une année.</span></label></>}
            {active === 'break-even' && <><InputField label="Coûts fixes" value={values.fixedCosts} onChange={(value) => update('fixedCosts', value)} suffix="€" min={0} /><InputField label="Coût variable par unité" value={values.variableCost} onChange={(value) => update('variableCost', value)} suffix="€" min={0} /><InputField label="Prix de vente par unité" value={values.price} onChange={(value) => update('price', value)} suffix="€" min={0} /></>}
          </fieldset>
          {error && <div role="alert" className="mt-3 rounded-[9px] border border-warning/40 bg-[var(--color-warning-tint)] px-3 py-2 text-xs leading-5 text-warning">{error}</div>}
          <button type="button" disabled={pending} onClick={() => void calculate()} className="mt-4 flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">{pending && <Loader2 className="h-4 w-4 animate-spin" />}Calculer avec le moteur local</button>
        </section>

        {result && <div className="mt-4"><ResultCard result={result} /></div>}
        <div className="mt-4 flex items-start gap-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3 text-xs leading-5 text-accent"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />Le résultat vient de la formule affichée et de l’API locale. Il n’est ni mémorisé ni transmis à un modèle IA.</div>
      </div>
    </aside>
  );
}
