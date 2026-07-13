import { useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Eye,
  FileCode2,
  FileText,
  Gavel,
  Lock,
  RotateCcw,
  Search,
  ShieldCheck,
  Target,
  TestTube2,
  Users,
  Wrench,
} from 'lucide-react';

const portraitPositions = [
  ['0.48%', '1.42%'],
  ['33.49%', '1.42%'],
  ['66.51%', '1.42%'],
  ['99.52%', '1.42%'],
  ['0.48%', '98.58%'],
  ['33.49%', '98.58%'],
  ['66.51%', '98.58%'],
  ['99.52%', '98.58%'],
] as const;

export function CharacterPortrait({
  index,
  className = 'h-10 w-10 rounded-[12px]',
}: {
  index: number;
  className?: string;
}) {
  const [x, y] = portraitPositions[index] ?? portraitPositions[0];
  return (
    <span
      aria-hidden="true"
      className={`block shrink-0 overflow-hidden bg-[#101C36] bg-no-repeat ${className}`}
      style={{
        backgroundImage: "url('/prototype/therese-character-atlas-v1.png')",
        backgroundPosition: `${x} ${y}`,
        backgroundSize: '412% 206%',
      }}
    />
  );
}

export function BoardCard({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="rounded-[16px] border border-[#DCE4F1] bg-white p-4 shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]">
      <div className="flex items-start gap-3">
        <div className="flex shrink-0 -space-x-2" aria-hidden="true">
          {[1, 2, 3].map((index) => <CharacterPortrait key={index} index={index} className="h-10 w-10 rounded-[12px] border-2 border-white shadow-sm" />)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-[15px] font-semibold text-[#101C36]">Décision ÉCLORE</h3>
            <span className="rounded-full bg-[#E7F7EF] px-2 py-0.5 text-[10px] font-semibold text-[#08744C]">Délibération terminée</span>
          </div>
          <p className="mt-1 text-xs leading-5 text-[#5B6A82]">Les cinq regards convergent vers un lancement pilote à l’automne, avec deux réserves à sécuriser.</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2">
        <div className="rounded-[10px] bg-[#F7F9FD] px-3 py-2.5">
          <div className="text-[10px] uppercase tracking-wide text-[#7B8AA3]">Avis</div>
          <div className="mt-1 text-xs font-semibold text-[#101C36]">5 sur 5</div>
        </div>
        <div className="rounded-[10px] bg-[#F7F9FD] px-3 py-2.5">
          <div className="text-[10px] uppercase tracking-wide text-[#7B8AA3]">Confiance</div>
          <div className="mt-1 text-xs font-semibold text-[#08744C]">Élevée</div>
        </div>
        <div className="rounded-[10px] bg-[#F7F9FD] px-3 py-2.5">
          <div className="text-[10px] uppercase tracking-wide text-[#7B8AA3]">Réserves</div>
          <div className="mt-1 text-xs font-semibold text-[#9A6500]">2 à traiter</div>
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between border-t border-[#EDF1F7] pt-3">
        <div className="flex items-center gap-2 text-[11px] text-[#7B8AA3]">
          <Users className="h-3.5 w-3.5" />
          Analyse, stratégie, contradiction, pragmatisme, vision
        </div>
        <button type="button" onClick={onOpen} className="inline-flex items-center gap-1.5 rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white">
          Voir la décision
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

export function AtelierCard({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="rounded-[16px] border border-[#DCE4F1] bg-white p-4 shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]">
      <div className="flex items-start gap-3">
        <div className="flex shrink-0 -space-x-2" aria-hidden="true">
          <CharacterPortrait index={6} className="h-10 w-10 rounded-[12px] border-2 border-white shadow-sm" />
          <CharacterPortrait index={7} className="h-10 w-10 rounded-[12px] border-2 border-white shadow-sm" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-[15px] font-semibold text-[#101C36]">Mission · Simplifier l’onboarding</h3>
            <span className="rounded-full bg-[#FFF3D6] px-2 py-0.5 text-[10px] font-semibold text-[#946000]">Validation requise</span>
          </div>
          <p className="mt-1 text-xs leading-5 text-[#5B6A82]">Katia a cadré la mission, Zézette a préparé les changements et les tests sont passés.</p>
        </div>
      </div>
      <div className="mt-4 flex items-center gap-1.5">
        {['Cadrage', 'Plan', 'Exécution', 'Tests', 'Revue'].map((step, index) => (
          <div key={step} className="flex min-w-0 flex-1 items-center gap-1.5">
            <span className={`grid h-5 w-5 shrink-0 place-items-center rounded-full text-[9px] font-bold ${index < 4 ? 'bg-[#0F766E] text-white' : 'border border-[#0F766E] bg-[#DDF5F1] text-[#0F766E]'}`}>
              {index < 4 ? <Check className="h-3 w-3" /> : index + 1}
            </span>
            <span className="hidden truncate text-[9px] font-medium text-[#69788F] md:block">{step}</span>
            {index < 4 && <span className="h-px min-w-2 flex-1 bg-[#9EDBD1]" />}
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between border-t border-[#EDF1F7] pt-3">
        <div className="flex gap-2 text-[11px] text-[#5B6A82]">
          <span className="rounded-full bg-[#F3F6FC] px-2 py-1">4 fichiers</span>
          <span className="rounded-full bg-[#E7F7EF] px-2 py-1 text-[#08744C]">12 tests réussis</span>
          <span className="rounded-full bg-[#F3F6FC] px-2 py-1">0 action appliquée</span>
        </div>
        <button type="button" onClick={onOpen} className="inline-flex items-center gap-1.5 rounded-[9px] bg-[#101C36] px-3 py-2 text-xs font-semibold text-white">
          Vérifier la mission
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

const advisors = [
  { name: 'Analyste', portrait: 1, color: '#0F8FB3', text: 'La demande existe, mais le volume doit être testé avant d’augmenter les coûts fixes.' },
  { name: 'Stratège', portrait: 2, color: '#7C3AED', text: 'Une cohorte pilote protège la marque tout en créant des preuves commerciales réutilisables.' },
  { name: 'Contradicteur', portrait: 3, color: '#BE1A72', text: 'Le risque principal est la dispersion entre l’immersion et les offres déjà commercialisées.' },
  { name: 'Pragmatique', portrait: 4, color: '#0F766E', text: 'Fixer quatre participants minimum et verrouiller le lieu avant toute communication publique.' },
  { name: 'Visionnaire', portrait: 5, color: '#B45309', text: 'ÉCLORE peut devenir le format signature qui rend la promesse Synoptïa immédiatement tangible.' },
];

export function BoardCanvas() {
  const [showOpinions, setShowOpinions] = useState(false);
  const [planCreated, setPlanCreated] = useState(false);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-[#E4EAF3] bg-white px-5 py-4">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#7C3AED]">
          <Gavel className="h-3.5 w-3.5" />
          Board · Décision enregistrée
        </div>
        <h2 className="mt-2 pr-10 text-xl font-bold tracking-[-0.02em] text-[#101C36]">Lancer ÉCLORE à l’automne ?</h2>
        <p className="mt-1 text-sm text-[#5B6A82]">Thérèse a cadré la question et fait confronter cinq perspectives.</p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        <div className="mb-4 rounded-[14px] border border-[#CFE9EE] bg-[#F1FBFC] p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#0B7896]">
              <Target className="h-4 w-4" />
              Recommandation
            </div>
            <span className="rounded-full bg-[#E7F7EF] px-2 py-1 text-[10px] font-semibold text-[#08744C]">Confiance élevée</span>
          </div>
          <p className="mt-3 text-sm font-semibold leading-6 text-[#20304B]">Lancer une cohorte pilote de quatre dirigeants, avec une date limite de confirmation et un seuil de rentabilité défini avant communication.</p>
        </div>

        <div className="mb-4 grid grid-cols-2 gap-3">
          <div className="rounded-[13px] border border-[#D9EEE4] bg-white p-3">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-[#08744C]"><CheckCircle2 className="h-4 w-4" />Consensus</div>
            <p className="text-xs leading-5 text-[#5B6A82]">Le pilote limite le risque et produit les premières preuves de valeur.</p>
          </div>
          <div className="rounded-[13px] border border-[#F1E0B9] bg-white p-3">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-[#9A6500]"><AlertTriangle className="h-4 w-4" />Divergences</div>
            <p className="text-xs leading-5 text-[#5B6A82]">Positionnement prix et temps à consacrer par rapport à PROPULSER.</p>
          </div>
        </div>

        <button type="button" onClick={() => setShowOpinions((open) => !open)} className="mb-4 flex w-full items-center justify-between rounded-[12px] border border-[#DCE4F1] bg-white px-3 py-3 text-left">
          <span className="flex items-center gap-2 text-xs font-semibold text-[#33415C]">
            <span className="flex -space-x-1.5" aria-hidden="true">
              {advisors.map((advisor) => <CharacterPortrait key={advisor.name} index={advisor.portrait} className="h-6 w-6 rounded-full border-2 border-white shadow-sm" />)}
            </span>
            Les cinq avis
          </span>
          <span className="flex items-center gap-1 text-[10px] text-[#7B8AA3]">{showOpinions ? 'Réduire' : 'Consulter'}<ChevronDown className={`h-4 w-4 transition ${showOpinions ? 'rotate-180' : ''}`} /></span>
        </button>

        {showOpinions && (
          <div className="mb-4 space-y-2">
            {advisors.map((advisor) => {
              return (
                <div key={advisor.name} className="flex gap-3 rounded-[12px] border border-[#E4EAF3] bg-white p-3">
                  <CharacterPortrait index={advisor.portrait} className="h-10 w-10 rounded-[10px] border border-white shadow-sm" />
                  <div><div className="text-xs font-semibold" style={{ color: advisor.color }}>{advisor.name}</div><p className="mt-1 text-xs leading-5 text-[#69788F]">{advisor.text}</p></div>
                </div>
              );
            })}
          </div>
        )}

        <div className="rounded-[14px] border border-[#DCE4F1] bg-white p-4">
          <div className="mb-3 text-xs font-semibold text-[#33415C]">Prochaines étapes proposées</div>
          {['Valider un seuil minimum de quatre participants.', 'Chiffrer le lieu et les coûts variables.', 'Préparer une page pilote sans ouvrir les ventes.'].map((step, index) => (
            <div key={step} className="mb-2 flex gap-2.5 text-xs leading-5 text-[#5B6A82] last:mb-0"><span className="font-semibold text-[#7C3AED]">{index + 1}</span>{step}</div>
          ))}
        </div>

        {planCreated && <div className="mt-4 flex items-center gap-2 rounded-[12px] border border-[#BFE4D2] bg-[#E7F7EF] p-3 text-xs font-semibold text-[#08744C]"><CheckCircle2 className="h-4 w-4" />Plan d’action ajouté à la conversation et relié à cette décision.</div>}
      </div>

      <div className="border-t border-[#E4EAF3] bg-white p-4">
        <div className="mb-2 flex items-center justify-center gap-2 text-[10px] text-[#7B8AA3]"><ShieldCheck className="h-3.5 w-3.5 text-[#0F8FB3]" />Mode hybride · sources et modèles conservés avec la décision</div>
        <button type="button" onClick={() => setPlanCreated(true)} className={`flex w-full items-center justify-center gap-2 rounded-[10px] border px-4 py-3 text-sm font-semibold ${planCreated ? 'border-[#08744C] bg-[#08744C] text-white' : 'border-[#101C36] bg-[#101C36] text-white shadow-[3px_3px_0_#22D3EE]'}`}>
          {planCreated ? <Check className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
          {planCreated ? 'Plan d’action créé' : 'Transformer en plan d’action'}
        </button>
      </div>
    </div>
  );
}

export function AtelierCanvas() {
  const [showFiles, setShowFiles] = useState(false);
  const [approved, setApproved] = useState(false);

  const steps = [
    { label: 'Cadrage', icon: FileText },
    { label: 'Plan', icon: Search },
    { label: 'Exécution', icon: Wrench },
    { label: 'Tests', icon: TestTube2 },
    { label: 'Revue', icon: Eye },
  ];

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-[#E4EAF3] bg-white px-5 py-4">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#0F766E]">
          <span className="flex -space-x-1.5" aria-hidden="true">
            <CharacterPortrait index={6} className="h-6 w-6 rounded-[7px] border border-white" />
            <CharacterPortrait index={7} className="h-6 w-6 rounded-[7px] border border-white" />
          </span>
          Atelier · Prêt pour validation
        </div>
        <h2 className="mt-2 pr-10 text-xl font-bold tracking-[-0.02em] text-[#101C36]">Simplifier l’onboarding</h2>
        <p className="mt-1 text-sm text-[#5B6A82]">La mission est terminée. Rien n’est appliqué tant que tu n’as pas validé.</p>
      </div>

      <div className="border-b border-[#E4EAF3] bg-[#F8FAFD] px-4 py-3">
        <div className="flex items-center">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={step.label} className="flex min-w-0 flex-1 items-center">
                <div className="flex min-w-0 flex-col items-center gap-1">
                  <span className={`grid h-7 w-7 place-items-center rounded-full ${index < 4 ? 'bg-[#0F766E] text-white' : 'border border-[#0F766E] bg-[#DDF5F1] text-[#0F766E]'}`}>{index < 4 ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}</span>
                  <span className="truncate text-[9px] font-semibold text-[#69788F]">{step.label}</span>
                </div>
                {index < steps.length - 1 && <span className="mx-1 h-px flex-1 bg-[#9EDBD1]" />}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        <div className="mb-4 rounded-[14px] border border-[#CDE8E2] bg-[#F1FBF9] p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#0F766E]"><CheckCircle2 className="h-4 w-4" />Résultat obtenu</div>
          <p className="mt-2 text-sm font-semibold leading-6 text-[#20304B]">Le parcours passe de sept écrans à quatre étapes, sans modifier le stockage ni les données existantes.</p>
        </div>

        <div className="mb-4 grid grid-cols-3 gap-2">
          <div className="rounded-[11px] border border-[#DCE4F1] bg-white p-3 text-center"><div className="text-lg font-bold text-[#101C36]">4</div><div className="text-[10px] text-[#7B8AA3]">fichiers</div></div>
          <div className="rounded-[11px] border border-[#D9EEE4] bg-white p-3 text-center"><div className="text-lg font-bold text-[#08744C]">12/12</div><div className="text-[10px] text-[#7B8AA3]">tests réussis</div></div>
          <div className="rounded-[11px] border border-[#DCE4F1] bg-white p-3 text-center"><div className="text-lg font-bold text-[#101C36]">0,18 €</div><div className="text-[10px] text-[#7B8AA3]">coût estimé</div></div>
        </div>

        <div className="mb-4 rounded-[14px] border border-[#DCE4F1] bg-white p-4">
          <div className="mb-3 text-xs font-semibold text-[#33415C]">Ce qui change pour l’utilisateur</div>
          {['Une seule question par écran.', 'Le choix du modèle est déplacé dans les réglages avancés.', 'Une confirmation récapitule les données avant création.'].map((item) => (
            <div key={item} className="mb-2 flex gap-2.5 text-xs leading-5 text-[#5B6A82] last:mb-0"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#0F766E]" />{item}</div>
          ))}
        </div>

        <button type="button" onClick={() => setShowFiles((open) => !open)} className="flex w-full items-center justify-between rounded-[12px] border border-[#DCE4F1] bg-white px-3 py-3 text-left">
          <span className="flex items-center gap-2 text-xs font-semibold text-[#33415C]"><FileCode2 className="h-4 w-4 text-[#0F766E]" />Détails techniques · 4 fichiers</span>
          <ChevronDown className={`h-4 w-4 text-[#7B8AA3] transition ${showFiles ? 'rotate-180' : ''}`} />
        </button>
        {showFiles && (
          <div className="mt-2 overflow-hidden rounded-[12px] border border-[#DCE4F1] bg-white">
            {['OnboardingWizard.tsx', 'ProfileStep.tsx', 'SecurityStep.tsx', 'CompleteStep.test.tsx'].map((file, index) => (
              <div key={file} className="flex items-center gap-2 border-b border-[#EDF1F7] px-3 py-2.5 text-xs last:border-0"><FileCode2 className="h-3.5 w-3.5 text-[#7B8AA3]" /><span className="min-w-0 flex-1 truncate text-[#33415C]">{file}</span><span className={index === 3 ? 'text-[#0F766E]' : 'text-[#9A6500]'}>{index === 3 ? 'test ajouté' : 'modifié'}</span></div>
            ))}
          </div>
        )}

        <div className="mt-4 flex items-start gap-2.5 rounded-[12px] border border-[#D6F0F5] bg-[#F1FBFC] p-3 text-xs leading-5 text-[#315D69]"><Lock className="mt-0.5 h-4 w-4 shrink-0 text-[#0F8FB3]" />Dossier autorisé : Synoptia-THERESE. Écriture isolée, retour arrière disponible après application.</div>
        {approved && <div className="mt-4 flex items-center gap-2 rounded-[12px] border border-[#BFE4D2] bg-[#E7F7EF] p-3 text-xs font-semibold text-[#08744C]"><CheckCircle2 className="h-4 w-4" />Changements appliqués. Point de retour conservé.</div>}
      </div>

      <div className="border-t border-[#E4EAF3] bg-white p-4">
        <div className="mb-3 flex gap-2">
          <button type="button" className="flex flex-1 items-center justify-center gap-2 rounded-[10px] border border-[#DCE4F1] bg-white px-3 py-2.5 text-xs font-semibold text-[#5B6A82]"><RotateCcw className="h-4 w-4" />Demander une correction</button>
          <button type="button" className="grid h-10 w-10 place-items-center rounded-[10px] border border-[#DCE4F1] bg-white text-[#5B6A82]" aria-label="Refuser la mission"><ChevronDown className="h-4 w-4" /></button>
        </div>
        <button type="button" onClick={() => setApproved(true)} className={`flex w-full items-center justify-center gap-2 rounded-[10px] border px-4 py-3 text-sm font-semibold ${approved ? 'border-[#08744C] bg-[#08744C] text-white' : 'border-[#101C36] bg-[#101C36] text-white shadow-[3px_3px_0_#22D3EE]'}`}>
          {approved ? <CheckCircle2 className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
          {approved ? 'Changements appliqués' : 'Appliquer les changements'}
        </button>
      </div>
    </div>
  );
}
