/**
 * Lot 13 de la boucle d'amélioration (cycle 3, RP15 + RP16) : gardes de
 * régression sur la source pour les correctifs dont le comportement se
 * vérifie mal en jsdom (Rust, libellés, sondages, états d'erreur).
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = path.resolve(__dirname, '..');
const lire = (rel: string) => readFileSync(path.join(SRC, rel), 'utf-8');

describe('lot 13 - gardes de régression', () => {
  it('B-509 : plus aucun alert() natif dans le panneau Mémoire', () => {
    expect(lire('components/memory/MemoryPanel.tsx')).not.toMatch(/\balert\(/);
  });

  it('B-514 : Ollama « non mesuré » ne passe pas pour « indisponible »', () => {
    const src = lire('components/onboarding/LLMStep.tsx');
    expect(src).toMatch(/ollamaNonMesure/);
    expect(src).toMatch(/Non vérifié/);
  });

  it("B-517 : un cloisonnement de profil impossible bloque le démarrage au lieu d'être réessayé", () => {
    const src = lire('App.tsx');
    expect(src).toMatch(/erreurDeCloisonnement/);
    expect(src).toMatch(/Cloisonnement du profil impossible/);
  });

  it('B-518 : un statut de voix locale illisible se dit, avec une reprise', () => {
    const src = lire('components/settings/VoiceLocalSection.tsx');
    expect(src).toMatch(/loadError/);
    expect(src).toMatch(/Statut de la voix locale illisible/);
  });

  it("B-522 : un profil d'agent introuvable est annoncé", () => {
    const src = lire('components/atelier/AgentSession.tsx');
    expect(src).toMatch(/profilIntrouvable/);
    expect(src).toMatch(/introuvable/);
  });

  it('B-524 : un changement de tâche refusé par le serveur est notifié', () => {
    expect(lire('components/tasks/TaskKanban.tsx')).toMatch(/addNotification\(/);
    expect((lire('components/tasks/TaskList.tsx').match(/addNotification\(/g) ?? []).length).toBeGreaterThanOrEqual(2);
  });

  it('B-526 : chaque champ de clé a son propre interrupteur de visibilité', () => {
    expect(lire('components/settings/SettingsModal.tsx')).toMatch(/clesVisibles/);
    const services = lire('components/settings/ServicesTab.tsx');
    expect(services).toMatch(/clesVisibles\[provider\.apiKeyId\]/);
    expect(services).toMatch(/clesVisibles\.groq/);
    expect(services).not.toMatch(/showApiKey/);
  });

  it("B-528 : un échec de création d'activité est dit dans la modale", () => {
    expect(lire('components/crm/CRMPanel.tsx')).toMatch(/setActivityError\('L’activité n’a pas été enregistrée/);
  });

  it('B-529 : un échec de vérification des identifiants est visible', () => {
    const src = lire('components/email/wizard/CredentialsStep.tsx');
    expect(src).toMatch(/validationError/);
  });

  it('B-532 : un rechargement de tâches qui échoue le dit même avec une liste en cache', () => {
    expect(lire('components/tasks/TasksPanel.tsx')).not.toMatch(/if \(!hasCachedTasks\) \{\s*setError/);
  });

  it("B-533 : une suppression non confirmée ne retire plus le message de l'écran", () => {
    expect(lire('components/email/EmailDetail.tsx')).not.toMatch(/probablement déjà traité/);
    expect(lire('components/email/EmailList.tsx')).not.toMatch(/probablement déjà traité/);
    expect(lire('components/email/EmailDetail.tsx')).toMatch(/Le message est conservé/);
  });

  it('B-535 : un dossier disparu ou une lecture impossible sont distingués', () => {
    const src = lire('components/onboarding/WorkingDirStep.tsx');
    expect(src).toMatch(/dossierDisparu/);
    expect(src).toMatch(/lectureImpossible/);
    expect(src).not.toMatch(/\.catch\(\(\) => \(\{ path: null, exists: false \}\)\)/);
  });

  it('B-537 : la liste des sessions distingue « aucune » de « non lues »', () => {
    expect(lire('components/atelier/SessionList.tsx')).toMatch(/Sessions non lues/);
  });

  it("B-547 : la fermeture Windows ne tue plus tout backend.exe par nom d'image", () => {
    const src = readFileSync(path.resolve(SRC, '..', 'src-tauri/src/lib.rs'), 'utf-8');
    expect(src).not.toMatch(/"\/IM", "backend\.exe"/);
  });

  it("B-356 : le bouton d'effacement de la recherche a un nom", () => {
    expect(lire('components/prompts/PromptLibrary.tsx')).toMatch(/aria-label="Effacer la recherche"/);
  });

  it('B-360 : les boutons de ligne du panneau Mémoire ont un nom accessible', () => {
    const src = lire('components/memory/MemoryPanel.tsx');
    expect(src).toMatch(/aria-label="Actions RGPD"/);
    expect(src).toMatch(/aria-label=\{`Supprimer /);
  });

  it('B-364 : le badge RGPD reste dans la palette et sans glyphe brut', () => {
    const src = lire('components/memory/MemoryPanel.tsx');
    expect(src).not.toMatch(/bg-gray-500/);
    expect(src).not.toMatch(/'⚠'/);
  });

  it('B-366 : les littéraux JSX suivent le lexique (service d’IA, Paramètres)', () => {
    expect(lire('components/onboarding/LLMStep.tsx')).not.toMatch(/provider LLM/);
    const board = lire('components/prototype/BoardConversationCard.tsx');
    expect(board).not.toMatch(/Providers configurés/);
    expect(board).not.toMatch(/appels LLM/);
    expect(lire('components/prototype/CapabilityCenter.tsx')).not.toMatch(/Réglages > Services/);
  });

  it('B-368 : Mémoire et CommandExecutor utilisent le Spinner partagé', () => {
    for (const rel of ['components/memory/MemoryPanel.tsx', 'components/home/CommandExecutor.tsx']) {
      const src = lire(rel);
      expect(src, rel).not.toMatch(/border-t-transparent rounded-full animate-spin|animate-spin w-6 h-6/);
      expect(src, rel).toMatch(/<Spinner /);
    }
  });

  it('B-372 : le fieldset du Board en display:contents ne porte pas disabled:opacity', () => {
    expect(lire('components/prototype/BoardConversationCard.tsx')).not.toMatch(/contents disabled:opacity-70/);
  });
});
