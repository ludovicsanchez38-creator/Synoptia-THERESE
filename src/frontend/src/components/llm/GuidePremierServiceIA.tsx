import { useState, type ReactNode } from 'react';
import { open } from '@tauri-apps/plugin-shell';
import { Button } from '../ui/Button';

export function GuidePremierServiceIA({ provider, onRetest, retesting = false }: {
  provider: string;
  onRetest?: () => void;
  retesting?: boolean;
}) {
  const [erreur, setErreur] = useState<string | null>(null);
  function lien(href: string, texte: ReactNode) {
    return <a href={href} className="text-accent-cyan-ink underline" onClick={(event) => {
      event.preventDefault();
      setErreur(null);
      void open(href).catch(() => setErreur('Le navigateur n’a pas pu s’ouvrir. Réessaie.'));
    }}>{texte}</a>;
  }
  return <section aria-label="Obtenir une IA qui répond" className="mb-5 space-y-3 rounded-md border border-border bg-surface p-4 text-sm text-text">
    <p className="font-semibold">Pour recevoir ta première réponse</p>
    <p>Choisis un service en ligne, payant à l’usage, ou un modèle gratuit à installer sur ton ordinateur.</p>
    <details open={provider === 'anthropic'} className="space-y-2">
      <summary className="cursor-pointer font-medium">Avec Claude : obtenir ta clé, pas à pas</summary>
      <p>Une clé API est un code personnel qui permet à THÉRÈSE d’utiliser ton compte chez le fournisseur. La Console Claude est un espace distinct de l’application de discussion Claude.</p>
      <ol className="list-decimal space-y-2 pl-5">
        <li>{lien('https://platform.claude.com', 'Crée un compte dans la Console Claude')}. Les boutons de cet espace sont en anglais.</li>
        <li>{lien('https://claude.com/pricing#api', 'Voir les tarifs de Claude')}, dans la partie API. Le coût dépend du modèle choisi et de la quantité de texte échangée.</li>
        <li>Ouvre {lien('https://platform.claude.com/settings/billing', 'Facturation et crédits (Billing)')}. Ajoute des crédits avec « Buy credits » et fixe ton plafond dans « Spend limits ». Vérifie le réglage de recharge automatique.</li>
        <li>{lien('https://platform.claude.com/settings/keys', 'Créer une clé Claude')} : clique « Create key », nomme-la « THÉRÈSE » et rattache-la à un espace de travail (« Workspace »).</li>
        <li>Copie cette clé, reviens ici, colle-la dans le champ de clé et enregistre-la. Attends le résultat de la vérification, puis choisis ton modèle. Opus reste proposé par défaut.</li>
      </ol>
    </details>
    <details open={provider === 'ollama'} className="space-y-2">
      <summary className="cursor-pointer font-medium">Sur ton ordinateur : installer Ollama gratuitement</summary>
      <p>Le modèle conseillé est Qwen 3.5 4b. Il sait utiliser les outils de THÉRÈSE, sans compte ni clé. Les réponses peuvent être plus lentes qu’en ligne.</p>
      <ol className="list-decimal space-y-2 pl-5">
        <li>{lien('https://ollama.com/download', 'Télécharger Ollama')}, puis suis les instructions pour ton système et lance-le.</li>
        <li>Ouvre Terminal sur Mac ou Linux, ou PowerShell sur Windows. Copie cette commande, puis appuie sur Entrée : <code className="block select-all rounded-sm bg-bg p-2 my-1">ollama run qwen3.5:4b</code>Le téléchargement du modèle conseillé prend environ 3,3 Go. {lien('https://ollama.com/library/qwen3.5:4b', 'Voir le modèle Qwen conseillé')}.</li>
        <li>Quand le modèle répond, reviens dans THÉRÈSE en laissant Ollama lancé. Vérifie sa disponibilité, choisis « Ollama (Local) », puis « qwen3.5:4b ».</li>
      </ol>
      <p>La vérification de la mémoire de ton ordinateur s’affiche après le choix du modèle.</p>
      {onRetest && <Button size="sm" variant="secondary" disabled={retesting} onClick={onRetest}>Vérifier Ollama après l’installation</Button>}
    </details>
    {erreur && <p role="alert" className="text-error">{erreur}</p>}
  </section>;
}
