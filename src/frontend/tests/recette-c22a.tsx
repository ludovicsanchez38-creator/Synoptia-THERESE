import { createRoot } from 'react-dom/client';
import { SecurityStep } from '../src/components/onboarding/SecurityStep';
import { Aide } from '../src/components/Aide';
import '../src/styles/globals.css';

const securite = new URLSearchParams(location.search).get('ecran') === 'securite';
createRoot(document.getElementById('root')!).render(
  securite ? <main className="h-screen bg-bg flex items-center justify-center p-6">
    <div className="flex h-full w-full max-w-2xl flex-col overflow-hidden rounded-md bg-surface">
      <header className="shrink-0 p-6" style={{ height: 180 }}>Configuration de THÉRÈSE : Sécurité</header>
      <div data-testid="defilement" className="min-h-0 flex-1 overflow-y-auto relative">
        <SecurityStep provider="ollama" onNext={() => {}} onBack={() => {}} />
      </div>
    </div>
  </main> : <main className="p-6"><Aide /></main>,
);
