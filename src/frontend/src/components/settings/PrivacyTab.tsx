/**
 * THÉRÈSE v2 - Privacy Tab (US-017)
 *
 * Onglet Confidentialité dans les paramètres.
 * Politique de confidentialité in-app + configuration purge RGPD.
 */

import { useState, useEffect } from 'react';
import { Shield, Database, Clock, UserCheck, HardDrive, Loader2, Download, Trash2, EyeOff } from 'lucide-react';
import { Button } from '../ui/Button';
import { getPurgeSettings, updatePurgeSettings } from '../../services/api/rgpd';

// Types de données stockées
const DATA_TYPES = [
  { type: 'Contacts', description: 'Noms, emails, téléphones, adresses de tes contacts et prospects' },
  { type: 'Emails', description: 'Messages synchronisés depuis ton compte email' },
  { type: 'Factures', description: 'Factures, devis et avoirs créés dans THÉRÈSE' },
  { type: 'Conversations', description: 'Historique de tes échanges avec l\'assistant IA' },
  { type: 'Mémoire', description: 'Notes, contexte et connaissances mémorisées par l\'IA' },
  { type: 'Calendrier', description: 'Événements et rendez-vous synchronisés' },
  { type: 'Tâches', description: 'Liste de tâches et projets en cours' },
  { type: 'Fichiers', description: 'Métadonnées des fichiers indexés (pas les fichiers eux-mêmes)' },
];

// Durées de conservation
const RETENTION_TABLE = [
  { type: 'Contacts (prospects)', duree: '3 ans après dernier contact', justification: 'CNIL - prospection commerciale' },
  { type: 'Contacts (clients)', duree: '5 ans après fin de contrat', justification: 'Obligation comptable (Code de commerce)' },
  { type: 'Factures', duree: '10 ans', justification: 'Obligation fiscale (CGI art. 286)' },
  { type: 'Emails', duree: 'Selon ta configuration', justification: 'Synchronisation locale' },
  { type: 'Conversations IA', duree: 'Illimitée (locale)', justification: 'Pas de données personnelles tierces' },
  { type: 'Mémoire IA', duree: 'Illimitée (locale)', justification: 'Contexte personnel' },
];

export function PrivacyTab() {
  const [purgeEnabled, setPurgeEnabled] = useState(true);
  const [purgeMonths, setPurgeMonths] = useState(36);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    setLoading(true);
    try {
      const settings = await getPurgeSettings();
      setPurgeEnabled(settings.enabled);
      setPurgeMonths(settings.months);
    } catch (err) {
      console.error('Erreur chargement paramètres purge:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSavePurge() {
    setSaving(true);
    setError(null);
    try {
      await updatePurgeSettings(purgeEnabled, purgeMonths);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* En-tête */}
      <div>
        <h3 className="text-base font-semibold text-text flex items-center gap-2">
          <Shield className="w-5 h-5 text-accent-cyan" />
          Confidentialité et données personnelles
        </h3>
        <p className="mt-1 text-sm text-text-muted">
          THÉRÈSE respecte le RGPD. Voici comment tes données sont gérées.
        </p>
      </div>

      {/* Section : Stockage */}
      <section className="rounded-lg border border-border/50 p-4">
        <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
          <HardDrive className="w-4 h-4 text-green-400" />
          Stockage
        </h4>
        <div className="rounded-lg bg-green-500/5 border border-green-500/20 p-3">
          <p className="text-sm text-green-300">
            Toutes tes données sont stockées localement sur ta machine. Aucune donnée n'est
            envoyée à un serveur externe (sauf les requêtes aux modèles IA si tu utilises un
            provider cloud comme Anthropic, OpenAI ou Google).
          </p>
          <p className="text-xs text-green-300/70 mt-2">
            Base de données SQLite + index vectoriel Qdrant, le tout dans ton dossier utilisateur.
          </p>
        </div>
      </section>

      {/* Section : Tes données */}
      <section className="rounded-lg border border-border/50 p-4">
        <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
          <Database className="w-4 h-4 text-accent-cyan" />
          Tes données
        </h4>
        <div className="space-y-2">
          {DATA_TYPES.map(({ type, description }) => (
            <div
              key={type}
              className="flex items-start gap-3 rounded-lg bg-surface-elevated/30 px-3 py-2"
            >
              <span className="text-xs font-medium text-accent-cyan min-w-[100px]">{type}</span>
              <span className="text-xs text-text-muted">{description}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Section : Durées de conservation */}
      <section className="rounded-lg border border-border/50 p-4">
        <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
          <Clock className="w-4 h-4 text-amber-400" />
          Durées de conservation
        </h4>
        <div className="overflow-hidden rounded-lg border border-border/30">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-surface-elevated/50">
                <th className="px-3 py-2 text-left font-medium text-text-muted">Type</th>
                <th className="px-3 py-2 text-left font-medium text-text-muted">Durée</th>
                <th className="px-3 py-2 text-left font-medium text-text-muted">Justification</th>
              </tr>
            </thead>
            <tbody>
              {RETENTION_TABLE.map(({ type, duree, justification }) => (
                <tr key={type} className="border-t border-border/20">
                  <td className="px-3 py-2 text-text">{type}</td>
                  <td className="px-3 py-2 text-accent-cyan">{duree}</td>
                  <td className="px-3 py-2 text-text-muted">{justification}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Section : Tes droits */}
      <section className="rounded-lg border border-border/50 p-4">
        <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
          <UserCheck className="w-4 h-4 text-purple-400" />
          Tes droits
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded-lg bg-surface-elevated/30 p-3 text-center">
            <Download className="w-5 h-5 text-accent-cyan mx-auto mb-2" />
            <span className="block text-xs font-medium text-text mb-1">Exporter</span>
            <span className="block text-[10px] text-text-muted">
              Tu peux exporter les données de chaque contact via le CRM (bouton RGPD &gt; Exporter).
            </span>
          </div>
          <div className="rounded-lg bg-surface-elevated/30 p-3 text-center">
            <EyeOff className="w-5 h-5 text-amber-400 mx-auto mb-2" />
            <span className="block text-xs font-medium text-text mb-1">Anonymiser</span>
            <span className="block text-[10px] text-text-muted">
              Tu peux anonymiser un contact à tout moment via le CRM (bouton RGPD &gt; Anonymiser).
            </span>
          </div>
          <div className="rounded-lg bg-surface-elevated/30 p-3 text-center">
            <Trash2 className="w-5 h-5 text-red-400 mx-auto mb-2" />
            <span className="block text-xs font-medium text-text mb-1">Supprimer</span>
            <span className="block text-[10px] text-text-muted">
              Tu peux supprimer toutes tes données via Paramètres &gt; Avancé &gt; Réinitialiser.
            </span>
          </div>
        </div>
      </section>

      {/* Section : Purge automatique */}
      <section className="rounded-lg border border-border/50 p-4">
        <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
          <Clock className="w-4 h-4 text-accent-magenta" />
          Purge automatique
        </h4>
        <p className="text-xs text-text-muted mb-4">
          THÉRÈSE peut anonymiser automatiquement les contacts inactifs après une durée configurable.
          Un avertissement est envoyé 30 jours avant. Les contacts exclus de la purge ne sont jamais
          anonymisés automatiquement.
        </p>

        {/* Toggle */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-sm font-medium text-text">Purge automatique</span>
            <span className="block text-xs text-text-muted">
              {purgeEnabled ? 'Activée' : 'Désactivée'}
            </span>
          </div>
          <button
            onClick={() => setPurgeEnabled(!purgeEnabled)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              purgeEnabled ? 'bg-accent-cyan' : 'bg-surface-elevated'
            }`}
            role="switch"
            aria-checked={purgeEnabled}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                purgeEnabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Slider durée */}
        {purgeEnabled && (
          <div className="mb-4">
            <label className="text-xs font-medium text-text-muted block mb-2">
              Durée de rétention : <span className="text-accent-cyan font-semibold">{purgeMonths} mois</span>
            </label>
            <input
              type="range"
              min={12}
              max={60}
              step={6}
              value={purgeMonths}
              onChange={(e) => setPurgeMonths(parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-surface-elevated
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4
                [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:bg-accent-cyan [&::-webkit-slider-thumb]:cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-text-muted mt-1">
              <span>12 mois</span>
              <span>36 mois</span>
              <span>60 mois</span>
            </div>
          </div>
        )}

        {/* Bouton sauvegarder */}
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            onClick={handleSavePurge}
            disabled={saving}
          >
            {saving ? (
              <>
                <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
                Enregistrement...
              </>
            ) : saved ? (
              'Enregistré !'
            ) : (
              'Enregistrer'
            )}
          </Button>
          {error && (
            <span className="text-xs text-red-400">{error}</span>
          )}
        </div>
      </section>
    </div>
  );
}
