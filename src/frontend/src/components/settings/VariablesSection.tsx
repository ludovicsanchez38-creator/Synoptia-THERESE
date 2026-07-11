/**
 * THÉRÈSE v2 - Réglages > Services : Variables (chantier 4 Variables V1).
 *
 * Mémoire de travail réutilisable dans le chat via {nom} : valeur texte
 * (concaténable) ou liste de valeurs. Manipulable aussi depuis le chat en
 * zéro-LLM ({action: variable ...}). Présenté honnêtement : PAS un coffre à
 * secrets - les valeurs sont envoyées au modèle à l'usage et vivent dans la
 * base et l'historique.
 */
import { useCallback, useEffect, useState } from 'react';
import { Braces, Trash2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { useStatusStore } from '../../stores/statusStore';
import {
  createVariable,
  deleteVariable,
  listVariables,
  replaceVariable,
  type Variable,
  type VariableKind,
} from '../../services/api/variables';

const inputCls =
  'px-2.5 py-1.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text w-full focus:outline-none focus:ring-2 focus:ring-accent-cyan/50';
const labelCls = 'block text-xs text-text-muted mb-1';

function formatValue(variable: Variable): string {
  if (Array.isArray(variable.value)) {
    return variable.value.length
      ? variable.value.join(', ')
      : '(liste vide)';
  }
  return variable.value;
}

export function VariablesSection() {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [name, setName] = useState('');
  const [kind, setKind] = useState<VariableKind>('text');
  const [value, setValue] = useState('');
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [busy, setBusy] = useState(false);

  const notify = (type: 'success' | 'error', title: string, message?: string) =>
    useStatusStore.getState().addNotification({ type, title, message });

  const refresh = useCallback(async () => {
    try {
      setVariables(await listVariables());
    } catch (err) {
      console.error('Variables illisibles:', err);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await createVariable(
        name.trim(),
        kind,
        kind === 'list'
          ? value.trim()
            ? value.split(',').map((item) => item.trim()).filter(Boolean)
            : []
          : value
      );
      setName('');
      setValue('');
      await refresh();
      notify('success', `Variable « ${name.trim()} » créée`);
    } catch (err) {
      notify('error', 'Création refusée', err instanceof Error ? err.message : undefined);
    } finally {
      setBusy(false);
    }
  }

  async function handleReplace(variable: Variable) {
    setBusy(true);
    try {
      await replaceVariable(
        variable.name,
        variable.kind === 'list'
          ? editValue.split(',').map((item) => item.trim()).filter(Boolean)
          : editValue
      );
      setEditing(null);
      await refresh();
      notify('success', `Variable « ${variable.name} » remplacée`);
    } catch (err) {
      notify('error', 'Remplacement refusé', err instanceof Error ? err.message : undefined);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(variable: Variable) {
    setBusy(true);
    try {
      await deleteVariable(variable.name);
      await refresh();
      notify('success', `Variable « ${variable.name} » supprimée`);
    } catch (err) {
      notify('error', 'Suppression impossible', err instanceof Error ? err.message : undefined);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-lg border border-border/50 p-4">
      <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-1">
        <Braces className="w-4 h-4 text-accent-cyan" />
        Variables
      </h4>
      <p className="text-xs text-text-muted mb-1">
        Contenus réutilisables dans le chat : écris {'{nom}'} dans un message
        et la valeur est insérée à l'envoi. Gérables aussi depuis le chat :
        {' {action: variable creer nom "valeur"}'}.
      </p>
      <p className="text-xs text-warning mb-3">
        Les valeurs sont envoyées au modèle à l'usage et conservées dans la
        base et l'historique : n'y mets jamais un secret (mot de passe, clé).
      </p>

      <div className="grid grid-cols-[1fr_auto_2fr_auto] gap-2 items-end mb-4">
        <div>
          <label htmlFor="var-name" className={labelCls}>Nom</label>
          <input id="var-name" className={inputCls} value={name}
            placeholder="nom_client"
            onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label htmlFor="var-kind" className={labelCls}>Type</label>
          <select id="var-kind" className={inputCls} value={kind}
            onChange={(e) => setKind(e.target.value as VariableKind)}>
            <option value="text">Texte</option>
            <option value="list">Liste</option>
          </select>
        </div>
        <div>
          <label htmlFor="var-value" className={labelCls}>
            {kind === 'list' ? 'Éléments (séparés par des virgules)' : 'Valeur'}
          </label>
          <input id="var-value" className={inputCls} value={value}
            placeholder={kind === 'list' ? 'tomates, courgettes' : 'Ets Toto'}
            onChange={(e) => setValue(e.target.value)} />
        </div>
        <Button variant="primary" size="sm" onClick={handleCreate}
          disabled={busy || !name.trim()}>
          Créer
        </Button>
      </div>

      {variables.length === 0 ? (
        <p className="text-xs text-text-muted">Aucune variable pour l'instant.</p>
      ) : (
        <ul className="space-y-2">
          {variables.map((variable) => (
            <li key={variable.name}
              className="rounded-lg bg-background/40 border border-border/40 p-2.5">
              <div className="flex items-center gap-2">
                <code className="text-xs text-accent-cyan shrink-0">
                  {'{'}{variable.name}{'}'}
                </code>
                <span className="text-[10px] uppercase text-text-muted shrink-0">
                  {variable.kind === 'list' ? 'liste' : 'texte'}
                </span>
                {editing === variable.name ? (
                  <>
                    <input
                      className={inputCls}
                      value={editValue}
                      aria-label={`Nouvelle valeur de ${variable.name}`}
                      onChange={(e) => setEditValue(e.target.value)}
                    />
                    <Button variant="primary" size="sm" disabled={busy}
                      onClick={() => handleReplace(variable)}>
                      OK
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => setEditing(null)}>
                      Annuler
                    </Button>
                  </>
                ) : (
                  <>
                    <span className="text-xs text-text truncate flex-1"
                      title={formatValue(variable)}>
                      {formatValue(variable)}
                    </span>
                    <Button variant="ghost" size="sm"
                      onClick={() => {
                        setEditing(variable.name);
                        setEditValue(
                          Array.isArray(variable.value)
                            ? variable.value.join(', ')
                            : variable.value
                        );
                      }}>
                      Modifier
                    </Button>
                    <button
                      type="button"
                      aria-label={`Supprimer ${variable.name}`}
                      className="p-1 text-text-muted hover:text-error"
                      onClick={() => handleDelete(variable)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
