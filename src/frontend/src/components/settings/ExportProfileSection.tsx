/**
 * THÉRÈSE v2 - Réglages > Données : profil d'export DOCX (chantier 5).
 *
 * Langue, polices, couleurs, pied de page et marges des exports
 * déterministes (Atelier documentaire + conversations). Les défauts
 * reproduisent la charte Synoptia - ne toucher que ce qu'on veut changer.
 * Export/Import JSON pour partager le profil entre postes (à la main).
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { FileDown } from 'lucide-react';
import { Button } from '../ui/Button';
import { useStatusStore } from '../../stores/statusStore';
import {
  getExportProfile,
  resetExportProfile,
  saveExportProfile,
  type ExportProfile,
} from '../../services/api/exportProfile';

export function ExportProfileSection() {
  const [profile, setProfile] = useState<ExportProfile | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getExportProfile();
      setProfile(data.profile);
      setWarning(data.warning);
    } catch (err) {
      console.error('Profil export illisible:', err);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const notify = (type: 'success' | 'error', title: string, message?: string) =>
    useStatusStore.getState().addNotification({ type, title, message });

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    try {
      const data = await saveExportProfile(profile);
      setProfile(data.profile);
      setWarning(null);
      notify('success', 'Profil d\'export enregistré');
    } catch (err) {
      notify('error', 'Profil invalide', err instanceof Error ? err.message : undefined);
    } finally {
      setSaving(false);
    }
  }

  async function handleReset() {
    await resetExportProfile();
    await refresh();
    notify('success', 'Profil réinitialisé', 'Charte Synoptia par défaut restaurée.');
  }

  function handleExportJson() {
    if (!profile) return;
    const blob = new Blob([JSON.stringify(profile, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'therese-export-profile.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleImportJson(file: File) {
    try {
      const text = await file.text();
      const data = await saveExportProfile(JSON.parse(text));
      setProfile(data.profile);
      setWarning(null);
      notify('success', 'Profil importé');
    } catch (err) {
      notify('error', 'Import impossible', err instanceof Error ? err.message : undefined);
    }
  }

  if (!profile) return null;

  const set = (patch: Partial<ExportProfile>) => setProfile({ ...profile, ...patch });
  const setMargin = (side: keyof ExportProfile['margins_cm'], value: number) =>
    setProfile({ ...profile, margins_cm: { ...profile.margins_cm, [side]: value } });

  const inputCls =
    'px-2.5 py-1.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text w-full focus:outline-none focus:ring-2 focus:ring-accent-cyan/50';
  const labelCls = 'block text-xs text-text-muted mb-1';

  return (
    <section className="rounded-lg border border-border/50 p-4">
      <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-1">
        <FileDown className="w-4 h-4 text-accent-cyan" />
        Exports Word (Atelier et conversations)
      </h4>
      <p className="text-xs text-text-muted mb-3">
        Langue, polices et habillage des fichiers Word générés. Les valeurs par
        défaut reproduisent la charte actuelle. Une police absente du poste du
        destinataire sera remplacée par Word.
      </p>

      {warning && (
        <div className="rounded-lg bg-warning/10 border border-warning/40 p-2.5 mb-3">
          <p className="text-xs text-text">{warning}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label htmlFor="ep-language" className={labelCls}>Langue du document</label>
          <input id="ep-language" className={inputCls} value={profile.language}
            onChange={(e) => set({ language: e.target.value })} placeholder="fr-FR" />
        </div>
        <div>
          <label htmlFor="ep-footer" className={labelCls}>Pied de page</label>
          <input id="ep-footer" className={inputCls} value={profile.footer_text}
            onChange={(e) => set({ footer_text: e.target.value })} />
        </div>
        <div>
          <label htmlFor="ep-body-font" className={labelCls}>Police du corps</label>
          <input id="ep-body-font" className={inputCls} value={profile.body_font}
            onChange={(e) => set({ body_font: e.target.value })} />
        </div>
        <div>
          <label htmlFor="ep-body-size" className={labelCls}>Taille du corps (pt)</label>
          <input id="ep-body-size" type="number" min={6} max={72} className={inputCls}
            value={profile.body_size_pt}
            onChange={(e) => set({ body_size_pt: Number(e.target.value) })} />
        </div>
        <div>
          <label htmlFor="ep-heading-font" className={labelCls}>Police des titres</label>
          <input id="ep-heading-font" className={inputCls} value={profile.heading_font}
            onChange={(e) => set({ heading_font: e.target.value })} />
        </div>
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <label htmlFor="ep-heading-color" className={labelCls}>Couleur titres</label>
            <input id="ep-heading-color" type="color" className="h-8 w-full rounded cursor-pointer bg-transparent"
              value={profile.heading_color}
              onChange={(e) => set({ heading_color: e.target.value, title_color: e.target.value })} />
          </div>
          <div className="flex-1">
            <label htmlFor="ep-h2-color" className={labelCls}>Couleur H2</label>
            <input id="ep-h2-color" type="color" className="h-8 w-full rounded cursor-pointer bg-transparent"
              value={profile.h2_color}
              onChange={(e) => set({ h2_color: e.target.value })} />
          </div>
          <div className="flex-1">
            <label htmlFor="ep-body-color" className={labelCls}>Couleur corps</label>
            <input id="ep-body-color" type="color" className="h-8 w-full rounded cursor-pointer bg-transparent"
              value={profile.body_color}
              onChange={(e) => set({ body_color: e.target.value })} />
          </div>
        </div>
      </div>

      <div className="mb-3">
        <span className={labelCls}>Marges (cm)</span>
        <div className="grid grid-cols-4 gap-2">
          {(['top', 'bottom', 'left', 'right'] as const).map((side) => (
            <div key={side}>
              <label htmlFor={`ep-margin-${side}`} className={labelCls}>
                {{ top: 'Haut', bottom: 'Bas', left: 'Gauche', right: 'Droite' }[side]}
              </label>
              <input id={`ep-margin-${side}`} type="number" min={0.5} max={8} step={0.5}
                className={inputCls} value={profile.margins_cm[side]}
                onChange={(e) => setMargin(side, Number(e.target.value))} />
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
          {saving ? 'Enregistrement…' : 'Enregistrer'}
        </Button>
        <Button variant="ghost" size="sm" onClick={handleReset}>
          Réinitialiser
        </Button>
        <Button variant="ghost" size="sm" onClick={handleExportJson}>
          Exporter JSON
        </Button>
        <Button variant="ghost" size="sm" onClick={() => fileInputRef.current?.click()}>
          Importer JSON
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleImportJson(f);
            e.target.value = '';
          }}
        />
      </div>
    </section>
  );
}
