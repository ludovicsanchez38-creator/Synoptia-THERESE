# Vue « Accueil » — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le dashboard « Ma journée » (inaccessible, vide-donc-muet, truffé de faux) par une vraie vue « Accueil » persistante, hybride (lanceur + journée), honnête et actionnable.

**Architecture:** Nouvelle `AppView` `home` rendue dans `ChatLayout` (content-swap, sans back-bar). Conteneur `HomeView` qui compose 6 sous-composants à responsabilité unique. Réutilise `GET /api/dashboard/today` (inchangé) + un nouveau `GET /api/dashboard/setup-status`. Le composant `DashboardToday` et le gating `showDashboard` disparaissent.

**Tech Stack:** React 19 + Zustand + TailwindCSS 4 + lucide-react (frontend) ; FastAPI + SQLModel + pytest (backend) ; Vitest (tests front).

**Branche :** `feat/dashboard-accueil` (basée sur `fix/bugs-post-0.20`). Lock `.agents-sync-paused` en place pendant le dev.

**Convention tests (repo) :** pytest depuis la RACINE du repo (`uv run pytest ...`). Front : `npx tsc --noEmit`, `npx vitest run`, `npm run -s lint` (seuil `--max-warnings 27`). Couverture composant ~6 % → tests ciblés sur la logique (backend, stores, tri/filtre), vérif visuelle navigateur pour le purement présentationnel.

---

## Structure de fichiers

**Backend**
- Modifier `src/backend/app/routers/dashboard.py` : ajouter `GET /setup-status`.
- Test `tests/test_routers_dashboard.py` (créer si absent) : couvre `/setup-status`.

**Frontend — créés**
- `src/frontend/src/components/home/HomeView.tsx` — conteneur.
- `src/frontend/src/components/home/HomeHeader.tsx` — salutation, date, badges.
- `src/frontend/src/components/home/QuickActions.tsx` — actions rapides (actionRegistry).
- `src/frontend/src/components/home/RecentConversations.tsx` — conversations récentes.
- `src/frontend/src/components/home/TodayPanels.tsx` — Agenda du jour + À traiter.
- `src/frontend/src/components/home/SetupChecklist.tsx` — mise en route guidée.
- `src/frontend/src/components/home/RecentConversations.test.ts` + `SetupChecklist.test.tsx` — tests logique.

**Frontend — modifiés**
- `src/frontend/src/services/api/dashboard.ts` — `fetchSetupStatus`.
- `src/frontend/src/stores/navigationStore.ts` — `'home'` dans `AppView`.
- `src/frontend/src/stores/navigationStore.test.ts` — test `home`/`home.open`.
- `src/frontend/src/lib/actionRegistry.ts` — action `home.open`.
- `src/frontend/src/components/chat/ChatLayout.tsx` — rendu `home` sans back-bar, landing, suppression du gating `showDashboard`.
- `src/frontend/src/components/chat/ChatHeader.tsx` — bouton « Accueil ».
- `src/frontend/src/components/settings/AdvancedTab.tsx` — libellé « Afficher l'Accueil au lancement ».
- **Supprimer** `src/frontend/src/components/home/DashboardToday.tsx` (remplacé).

---

## Task 1 : Endpoint backend `GET /api/dashboard/setup-status`

**Files:**
- Modify: `src/backend/app/routers/dashboard.py`
- Test: `tests/test_routers_dashboard.py` (create)

- [ ] **Step 1 : Écrire le test qui échoue**

Create `tests/test_routers_dashboard.py` :

```python
"""Tests du router dashboard (setup-status pour la vue Accueil)."""
import pytest
from httpx import AsyncClient

from app.models.entities import Calendar, EmailAccount


class TestSetupStatus:
    @pytest.mark.asyncio
    async def test_setup_status_all_empty(self, client: AsyncClient):
        """Instance vierge : rien de branché."""
        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {
            "has_calendar": False,
            "has_email": False,
            "billing_complete": False,
        }

    @pytest.mark.asyncio
    async def test_setup_status_with_calendar_and_email(
        self, client: AsyncClient, db_session
    ):
        """Un calendrier + un compte mail => has_calendar/has_email True."""
        db_session.add(
            Calendar(
                id="cal-1",
                provider="local",
                external_id="local-1",
                name="Perso",
                timezone="Europe/Paris",
            )
        )
        db_session.add(
            EmailAccount(id="acc-1", email="x@y.com", provider="gmail")
        )
        await db_session.commit()

        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_calendar"] is True
        assert data["has_email"] is True
```

- [ ] **Step 2 : Lancer le test, vérifier l'échec**

Run: `uv run pytest tests/test_routers_dashboard.py -v --cov=app.routers.dashboard > /tmp/t.txt 2>&1; sed -n '/FAILURES/,/====/p' /tmp/t.txt | head -30`
Expected: FAIL/404 (endpoint inexistant).

> NB : vérifier d'abord les champs réels de `Calendar`/`EmailAccount` (`grep -nA15 "class Calendar" src/backend/app/models/entities.py`) et ajuster les kwargs du fixture si un champ obligatoire manque. Le test doit échouer pour la BONNE raison (route 404), pas sur la construction d'entité.

- [ ] **Step 3 : Implémenter l'endpoint**

Dans `src/backend/app/routers/dashboard.py`, ajouter après l'import existant `from app.models.entities import ...` la classe `UserProfile`, et ajouter la route :

```python
@router.get("/setup-status")
async def get_setup_status(session: AsyncSession = Depends(get_session)):
    """Indique ce qui reste à brancher (mise en route guidée de l'Accueil)."""
    has_calendar = False
    has_email = False
    billing_complete = False

    # has_calendar : au moins un Calendar configuré
    try:
        from app.models.entities import Calendar
        res = await session.execute(select(Calendar.id).limit(1))
        has_calendar = res.first() is not None
    except Exception as e:
        logger.warning(f"setup-status calendar: {e}")

    # has_email : au moins un compte mail
    try:
        from app.models.entities import EmailAccount
        res = await session.execute(select(EmailAccount.id).limit(1))
        has_email = res.first() is not None
    except Exception as e:
        logger.warning(f"setup-status email: {e}")

    # billing_complete : profil émetteur complet (SIRET, etc.)
    try:
        from app.models.entities import UserProfile
        res = await session.execute(select(UserProfile).limit(1))
        profile = res.scalars().first()
        billing_complete = bool(profile and profile.is_billing_complete())
    except Exception as e:
        logger.warning(f"setup-status billing: {e}")

    return {
        "has_calendar": has_calendar,
        "has_email": has_email,
        "billing_complete": billing_complete,
    }
```

> Retirer la ligne « placeholder » : la garder telle quelle est une erreur. Le vrai corps commence à `# has_calendar`. Vérifier que `UserProfile.is_billing_complete()` existe (`grep -n "is_billing_complete" src/backend/app/models/entities.py`) ; sinon, dériver de `billing_profile_status` (`invoices.py:517`).

- [ ] **Step 4 : Lancer le test, vérifier le succès**

Run: `uv run pytest tests/test_routers_dashboard.py -v --cov=app.routers.dashboard > /tmp/t.txt 2>&1; grep -E "passed|failed" /tmp/t.txt | tail -1`
Expected: 2 passed.

- [ ] **Step 5 : Commit**

```bash
git add src/backend/app/routers/dashboard.py tests/test_routers_dashboard.py
git commit -m "feat(home): endpoint /api/dashboard/setup-status (mise en route guidée)"
```

---

## Task 2 : Vue `home` dans navigationStore + action ⌘K

**Files:**
- Modify: `src/frontend/src/stores/navigationStore.ts`
- Modify: `src/frontend/src/lib/actionRegistry.ts`
- Test: `src/frontend/src/stores/navigationStore.test.ts`

- [ ] **Step 1 : Test qui échoue**

Ajouter dans `navigationStore.test.ts` (avant la `}` de fermeture du `describe`) :

```ts
  it("la vue 'home' existe et l'action ⌘K home.open y navigue", async () => {
    const { runAction } = await import('../lib/actionRegistry');
    const ok = runAction('home.open');
    expect(ok).toBe(true);
    expect(useNavigationStore.getState().activeView).toBe('home');
  });
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `cd src/frontend && npx vitest run src/stores/navigationStore.test.ts 2>&1 | tail -5`
Expected: FAIL (action `home.open` inconnue → `runAction` renvoie false / type `'home'` absent).

- [ ] **Step 3 : Implémenter**

`navigationStore.ts` — ajouter `'home'` au type union :

```ts
export type AppView =
  | 'chat'
  | 'home' // Vue Accueil persistante (refonte dashboard)
  | 'memory'
  | 'crm'
  | 'email'
  | 'calendar'
  | 'tasks'
  | 'invoices'
  | 'files'
  | 'projects';
```

`actionRegistry.ts` — ajouter dans le groupe Navigation (juste après l'ouverture de `APP_ACTIONS` array, en tête de liste) :

```ts
  { id: 'home.open', label: 'Accueil', description: 'Revenir à la page d\'accueil', group: 'Navigation', shortcut: 'H', keywords: ['accueil', 'home', 'journée'], run: () => nav().setView('home') },
```

- [ ] **Step 4 : Vérifier le succès**

Run: `cd src/frontend && npx vitest run src/stores/navigationStore.test.ts 2>&1 | tail -3`
Expected: tests passent.

- [ ] **Step 5 : Commit**

```bash
git add src/frontend/src/stores/navigationStore.ts src/frontend/src/stores/navigationStore.test.ts src/frontend/src/lib/actionRegistry.ts
git commit -m "feat(home): vue 'home' dans navigationStore + action ⌘K home.open"
```

---

## Task 3 : Client API `fetchSetupStatus`

**Files:**
- Modify: `src/frontend/src/services/api/dashboard.ts`

- [ ] **Step 1 : Implémenter (typage + fetch)**

Ajouter à `dashboard.ts` :

```ts
export interface SetupStatus {
  has_calendar: boolean;
  has_email: boolean;
  billing_complete: boolean;
}

/** Mise en route : ce qui reste à brancher (Accueil). 100 % local. */
export async function fetchSetupStatus(): Promise<SetupStatus> {
  return request<SetupStatus>('/api/dashboard/setup-status');
}
```

- [ ] **Step 2 : Vérifier les types**

Run: `cd src/frontend && npx tsc --noEmit 2>&1 | grep -c "error TS"`
Expected: 0.

- [ ] **Step 3 : Commit**

```bash
git add src/frontend/src/services/api/dashboard.ts
git commit -m "feat(home): client API fetchSetupStatus"
```

---

## Task 4 : `HomeHeader` (salutation, date, badges honnêtes)

**Files:**
- Create: `src/frontend/src/components/home/HomeHeader.tsx`

- [ ] **Step 1 : Implémenter**

```tsx
/**
 * THÉRÈSE v2 - HomeHeader : salutation + date FR + badges honnêtes.
 * Badge fournisseur = provider/modèle RÉELLEMENT actif (getLLMConfig), pas codé en dur.
 */
import { useEffect, useState } from 'react';
import { ShieldCheck, Cpu } from 'lucide-react';
import { getLLMConfig } from '../../services/api/config';

const PROVIDER_LABEL: Record<string, string> = {
  claude: 'Claude',
  mistral: 'Mistral',
  ollama: 'Ollama',
};

export function HomeHeader() {
  const [provider, setProvider] = useState<{ label: string; model: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    getLLMConfig()
      .then((cfg) => {
        if (cancelled) return;
        setProvider({ label: PROVIDER_LABEL[cfg.provider] ?? cfg.provider, model: cfg.model });
      })
      .catch(() => {
        /* badge masqué si indisponible (honnêteté : pas de valeur inventée) */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Bonjour' : now.getHours() < 18 ? 'Bon après-midi' : 'Bonsoir';
  const dateStr = now.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="flex items-start gap-4 flex-wrap">
      <div>
        <h1 className="text-[26px] font-extrabold tracking-tight leading-tight text-text">
          {greeting} <span className="text-accent">!</span>
        </h1>
        <p className="text-sm text-text-muted mt-1.5 first-letter:capitalize">{dateStr}</p>
      </div>
      <div className="ml-auto flex gap-2 flex-wrap">
        <span className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-full text-[12.5px] font-medium bg-surface border text-accent"
          style={{ borderColor: 'color-mix(in srgb, var(--color-accent) 45%, transparent)' }}>
          <ShieldCheck className="w-3.5 h-3.5" /> Données locales
        </span>
        {provider && (
          <span className="inline-flex items-center gap-1.5 h-[30px] px-3 rounded-full text-[12.5px] font-medium bg-surface border border-border text-text-muted">
            <Cpu className="w-3.5 h-3.5" /> {provider.label}
            <span className="text-text-muted/70">· {provider.model}</span>
          </span>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2 : Types OK**

Run: `cd src/frontend && npx tsc --noEmit 2>&1 | grep -c "error TS"`
Expected: 0.

- [ ] **Step 3 : Commit**

```bash
git add src/frontend/src/components/home/HomeHeader.tsx
git commit -m "feat(home): HomeHeader (date + badge fournisseur réel, plus de faux)"
```

---

## Task 5 : `QuickActions` (réutilise actionRegistry)

**Files:**
- Create: `src/frontend/src/components/home/QuickActions.tsx`

- [ ] **Step 1 : Implémenter**

```tsx
/**
 * THÉRÈSE v2 - QuickActions : lanceur d'actions rapides depuis le registre unique.
 * Pas de logique métier dupliquée : on délègue à runAction(id).
 */
import { MessageSquarePlus, FileText, UserPlus, Receipt } from 'lucide-react';
import { runAction } from '../../lib/actionRegistry';

const ACTIONS: { id: string; label: string; icon: React.ElementType }[] = [
  { id: 'chat.new', label: 'Nouvelle conversation', icon: MessageSquarePlus },
  { id: 'guided.open', label: 'Produire un document', icon: FileText },
  { id: 'contact.new', label: 'Ajouter un contact', icon: UserPlus },
  { id: 'invoices.open', label: 'Factures', icon: Receipt },
];

export function QuickActions() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {ACTIONS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => runAction(id)}
          className="flex items-center gap-2.5 p-3 rounded-xl bg-surface border border-border text-left hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] transition-colors"
        >
          <span className="w-8 h-8 rounded-lg grid place-items-center bg-accent-tint text-accent shrink-0">
            <Icon className="w-4 h-4" />
          </span>
          <span className="text-[13px] font-medium text-text leading-tight">{label}</span>
        </button>
      ))}
    </div>
  );
}
```

> NB : `chat.new` reste sur la vue `home` (l'action crée la conv mais ne change pas de vue). Pour amener au chat, `QuickActions` enrobe `chat.new` : `onClick={() => { runAction(id); if (id === 'chat.new') useNavigationStore.getState().setView('chat'); }}`. Importer `useNavigationStore`. (Vérifier le comportement de `chat.new` à l'exécution et ajuster.)

- [ ] **Step 2 : Types OK** — Run: `cd src/frontend && npx tsc --noEmit 2>&1 | grep -c "error TS"` → 0.

- [ ] **Step 3 : Commit**

```bash
git add src/frontend/src/components/home/QuickActions.tsx
git commit -m "feat(home): QuickActions (lanceur basé sur actionRegistry)"
```

---

## Task 6 : `RecentConversations`

**Files:**
- Create: `src/frontend/src/components/home/RecentConversations.tsx`
- Test: `src/frontend/src/components/home/RecentConversations.test.ts`

- [ ] **Step 1 : Test qui échoue (logique de tri/filtre)**

Extraire la sélection dans une fonction pure testable. Test :

```ts
import { describe, it, expect } from 'vitest';
import { selectRecentConversations } from './RecentConversations';

const conv = (id: string, updatedAt: string, msgs = 1, ephemeral = false) => ({
  id, title: `Conv ${id}`, messages: Array(msgs).fill({ id: 'm', role: 'user', content: 'x', timestamp: new Date() }),
  createdAt: new Date(updatedAt), updatedAt: new Date(updatedAt), ephemeral,
});

describe('selectRecentConversations', () => {
  it('trie par updatedAt desc, exclut vides et éphémères, max 5', () => {
    const list = [
      conv('a', '2026-06-01'), conv('b', '2026-06-09'), conv('c', '2026-06-05'),
      conv('empty', '2026-06-08', 0), conv('eph', '2026-06-10', 1, true),
    ] as never[];
    const out = selectRecentConversations(list, 5);
    expect(out.map((c) => c.id)).toEqual(['b', 'c', 'a']);
  });
});
```

- [ ] **Step 2 : Vérifier l'échec**

Run: `cd src/frontend && npx vitest run src/components/home/RecentConversations.test.ts 2>&1 | tail -4`
Expected: FAIL (fonction inexistante).

- [ ] **Step 3 : Implémenter**

```tsx
/**
 * THÉRÈSE v2 - RecentConversations : reprendre une conversation récente.
 */
import { MessageSquare } from 'lucide-react';
import { useChatStore, type Conversation } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';

/** Pure : conversations non vides, non éphémères, triées récentes d'abord, top N. */
export function selectRecentConversations(conversations: Conversation[], limit: number): Conversation[] {
  return [...conversations]
    .filter((c) => !c.ephemeral && c.messages.length > 0)
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, limit);
}

export function RecentConversations() {
  const conversations = useChatStore((s) => s.conversations);
  const loadConversation = useChatStore((s) => s.loadConversation);
  const recent = selectRecentConversations(conversations, 5);

  function open(id: string) {
    loadConversation(id);
    useNavigationStore.getState().setView('chat');
  }

  return (
    <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)]">
      <h2 className="text-base font-bold text-text mb-4">Reprendre une conversation</h2>
      {recent.length === 0 ? (
        <p className="text-sm text-text-muted py-2">Aucune conversation pour l'instant.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {recent.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => open(c.id)}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] transition-colors text-left"
              >
                <MessageSquare className="w-4 h-4 text-accent shrink-0" />
                <span className="text-sm text-text truncate flex-1">{c.title || 'Sans titre'}</span>
                <span className="text-xs text-text-muted shrink-0">
                  {new Date(c.updatedAt).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
```

- [ ] **Step 4 : Vérifier le succès** — Run: `cd src/frontend && npx vitest run src/components/home/RecentConversations.test.ts 2>&1 | tail -3` → passent.

- [ ] **Step 5 : Commit**

```bash
git add src/frontend/src/components/home/RecentConversations.tsx src/frontend/src/components/home/RecentConversations.test.ts
git commit -m "feat(home): RecentConversations (reprise conv récente, tri testé)"
```

---

## Task 7 : `TodayPanels` (Agenda du jour + À traiter)

**Files:**
- Create: `src/frontend/src/components/home/TodayPanels.tsx`

- [ ] **Step 1 : Implémenter**

Le composant reçoit le `TodayDashboard` déjà chargé par `HomeView` (pas de fetch ici → unité pure d'affichage). Clics → vues via `useNavigationStore`.

```tsx
/**
 * THÉRÈSE v2 - TodayPanels : Agenda du jour | À traiter (factures/prospects/tâches).
 * Reçoit les données ; ne fetch pas (séparation des responsabilités).
 */
import { Calendar, AlertCircle, Users, AlarmClock } from 'lucide-react';
import type { TodayDashboard } from '../../services/api/dashboard';
import { useNavigationStore } from '../../stores/navigationStore';

function go(view: 'calendar' | 'invoices' | 'crm' | 'tasks') {
  useNavigationStore.getState().setView(view);
}

export function TodayPanels({ data }: { data: TodayDashboard }) {
  const events = data.events.slice(0, 4);
  const overdue = data.overdue_invoices.slice(0, 3);
  const stale = data.stale_prospects.slice(0, 3);
  const tasks = data.urgent_tasks.slice(0, 3);
  const hasActionables = overdue.length + stale.length + tasks.length > 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Agenda */}
      <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-text">Agenda du jour</h2>
          <button onClick={() => go('calendar')} className="text-[12.5px] text-accent font-semibold hover:underline">Tout voir</button>
        </div>
        {events.length === 0 ? (
          <p className="text-sm text-text-muted py-2">Rien de prévu aujourd'hui.</p>
        ) : (
          <ul className="flex flex-col gap-2.5">
            {events.map((e, i) => (
              <li key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-surface-2 border border-border">
                <Calendar className="w-4 h-4 text-accent shrink-0" />
                <span className="text-sm text-text truncate flex-1">{e.summary}</span>
                <span className="text-xs text-text-muted tabular-nums">
                  {e.all_day ? 'Jour.' : e.start_datetime ? new Date(e.start_datetime).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* À traiter */}
      <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)]">
        <h2 className="text-base font-bold text-text mb-4">À traiter</h2>
        {!hasActionables ? (
          <p className="text-sm text-text-muted py-2">Aucune relance en attente.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {overdue.map((inv) => (
              <li key={inv.id}>
                <button onClick={() => go('invoices')} className="w-full flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] text-left">
                  <AlertCircle className="w-4 h-4 text-warning shrink-0" />
                  <span className="text-[13px] text-text truncate flex-1">Relancer {inv.invoice_number}</span>
                  <span className="text-xs text-text-muted">{(inv.total_ttc || 0).toLocaleString('fr-FR')} €</span>
                </button>
              </li>
            ))}
            {stale.map((p) => (
              <li key={p.id}>
                <button onClick={() => go('crm')} className="w-full flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] text-left">
                  <Users className="w-4 h-4 text-accent shrink-0" />
                  <span className="text-[13px] text-text truncate flex-1">Relancer {p.name}</span>
                  <span className="text-xs text-text-muted truncate">{p.company || ''}</span>
                </button>
              </li>
            ))}
            {tasks.map((t) => (
              <li key={t.id}>
                <button onClick={() => go('tasks')} className="w-full flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] text-left">
                  <AlarmClock className="w-4 h-4 text-accent shrink-0" />
                  <span className="text-[13px] text-text truncate flex-1">{t.title}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
```

- [ ] **Step 2 : Types OK** — `cd src/frontend && npx tsc --noEmit 2>&1 | grep -c "error TS"` → 0.

- [ ] **Step 3 : Commit**

```bash
git add src/frontend/src/components/home/TodayPanels.tsx
git commit -m "feat(home): TodayPanels (agenda du jour + à traiter, états vides sobres)"
```

---

## Task 8 : `SetupChecklist` (mise en route guidée qui se retire)

**Files:**
- Create: `src/frontend/src/components/home/SetupChecklist.tsx`
- Test: `src/frontend/src/components/home/SetupChecklist.test.tsx`

- [ ] **Step 1 : Test qui échoue (masquage)**

```tsx
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { SetupChecklist } from './SetupChecklist';

describe('SetupChecklist', () => {
  it('ne rend rien quand tout est branché', () => {
    const { container } = render(
      <SetupChecklist status={{ has_calendar: true, has_email: true, billing_complete: true }} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('affiche seulement les étapes non faites', () => {
    const { queryByText } = render(
      <SetupChecklist status={{ has_calendar: false, has_email: true, billing_complete: false }} />
    );
    expect(queryByText('Connecter votre agenda')).toBeTruthy();
    expect(queryByText('Compléter le profil de facturation')).toBeTruthy();
    expect(queryByText('Connecter votre messagerie')).toBeNull();
  });
});
```

- [ ] **Step 2 : Vérifier l'échec** — `cd src/frontend && npx vitest run src/components/home/SetupChecklist.test.tsx 2>&1 | tail -4` → FAIL.

- [ ] **Step 3 : Implémenter**

```tsx
/**
 * THÉRÈSE v2 - SetupChecklist : mise en route guidée qui se retire.
 * N'affiche que les étapes NON faites ; se masque entièrement quand tout est branché.
 */
import { Calendar, Mail, FileSignature, ArrowRight } from 'lucide-react';
import type { SetupStatus } from '../../services/api/dashboard';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';

export function SetupChecklist({ status }: { status: SetupStatus }) {
  const steps = [
    { done: status.has_calendar, label: 'Connecter votre agenda', icon: Calendar, action: () => useNavigationStore.getState().setView('calendar') },
    { done: status.has_email, label: 'Connecter votre messagerie', icon: Mail, action: () => useNavigationStore.getState().setView('email') },
    { done: status.billing_complete, label: 'Compléter le profil de facturation', icon: FileSignature, action: () => usePanelStore.getState().openSettings() },
  ].filter((s) => !s.done);

  if (steps.length === 0) return null;

  return (
    <section className="rounded-xl border border-border bg-surface-2 p-4">
      <h2 className="text-sm font-semibold text-text mb-3">Mise en route</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {steps.map(({ label, icon: Icon, action }) => (
          <button
            key={label}
            type="button"
            onClick={action}
            className="flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-surface hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] transition-colors text-left"
          >
            <Icon className="w-4 h-4 text-accent shrink-0" />
            <span className="text-[13px] text-text leading-tight flex-1">{label}</span>
            <ArrowRight className="w-3.5 h-3.5 text-text-muted shrink-0" />
          </button>
        ))}
      </div>
    </section>
  );
}
```

> Vérifier que `usePanelStore` expose `openSettings` (vu dans ChatLayout : `ps.openSettings`). OK.

- [ ] **Step 4 : Vérifier le succès** — `cd src/frontend && npx vitest run src/components/home/SetupChecklist.test.tsx 2>&1 | tail -3` → passent.

- [ ] **Step 5 : Commit**

```bash
git add src/frontend/src/components/home/SetupChecklist.tsx src/frontend/src/components/home/SetupChecklist.test.tsx
git commit -m "feat(home): SetupChecklist (mise en route guidée qui se retire)"
```

---

## Task 9 : `HomeView` (conteneur)

**Files:**
- Create: `src/frontend/src/components/home/HomeView.tsx`

- [ ] **Step 1 : Implémenter**

```tsx
/**
 * THÉRÈSE v2 - HomeView : vue Accueil hybride (lanceur + journée).
 * Compose les sous-composants ; charge /today + /setup-status en parallèle.
 */
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { fetchTodayDashboard, fetchSetupStatus, type TodayDashboard, type SetupStatus } from '../../services/api/dashboard';
import { HomeHeader } from './HomeHeader';
import { QuickActions } from './QuickActions';
import { RecentConversations } from './RecentConversations';
import { TodayPanels } from './TodayPanels';
import { SetupChecklist } from './SetupChecklist';

export function HomeView() {
  const [today, setToday] = useState<TodayDashboard | null>(null);
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [todayError, setTodayError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchTodayDashboard().then((d) => !cancelled && setToday(d)).catch(() => !cancelled && setTodayError(true));
    fetchSetupStatus().then((s) => !cancelled && setSetup(s)).catch(() => { /* bande masquée si indispo */ });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="flex-1 min-w-0 overflow-y-auto px-7 py-6">
      <div className="flex flex-col gap-[22px] max-w-[1100px] mx-auto">
        <HomeHeader />
        {setup && <SetupChecklist status={setup} />}
        <QuickActions />
        <RecentConversations />

        {/* Aujourd'hui */}
        {today ? (
          <TodayPanels data={today} />
        ) : todayError ? (
          <p className="text-sm text-text-muted">Aperçu du jour indisponible pour le moment.</p>
        ) : (
          <div className="flex items-center justify-center gap-2 py-8 text-sm text-text-muted">
            <Loader2 className="w-5 h-5 animate-spin text-accent" /> Chargement de votre journée…
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2 : Types OK** — `cd src/frontend && npx tsc --noEmit 2>&1 | grep -c "error TS"` → 0.

- [ ] **Step 3 : Commit**

```bash
git add src/frontend/src/components/home/HomeView.tsx
git commit -m "feat(home): HomeView (conteneur composant la vue Accueil)"
```

---

## Task 10 : Câblage ChatLayout + ChatHeader, suppression des faux et de DashboardToday

**Files:**
- Modify: `src/frontend/src/components/chat/ChatLayout.tsx`
- Modify: `src/frontend/src/components/chat/ChatHeader.tsx`
- Delete: `src/frontend/src/components/home/DashboardToday.tsx`

- [ ] **Step 1 : ChatLayout — lazy import HomeView, retirer DashboardToday + showDashboard, rendre `home` sans back-bar, landing**

Dans `ChatLayout.tsx` :
1. Remplacer le lazy `DashboardToday` par `HomeView` :
```tsx
const HomeView = lazy(() => import('../home/HomeView').then((m) => ({ default: m.HomeView })));
```
2. Supprimer `const PREF_SKIP_DASHBOARD`, l'état `showDashboard`, le `useEffect` qui le passe à false, et `handleDismissDashboard`.
3. Initialiser la vue de lancement : au montage, si la préférence l'autorise, aller sur `home`.
```tsx
useEffect(() => {
  if (localStorage.getItem('therese-skip-dashboard') !== 'true') {
    useNavigationStore.getState().setView('home');
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);
```
4. Dans le routeur de vues : rendre `home` SANS la back-bar « ← Chat ». Restructurer le bloc `{activeView !== 'chat' ? (...)}` ainsi :
```tsx
{activeView === 'home' ? (
  <Suspense fallback={<div className="flex-1 flex items-center justify-center"><div className="text-text-muted text-sm">Chargement...</div></div>}>
    <HomeView />
  </Suspense>
) : activeView !== 'chat' ? (
  <div className="flex-1 overflow-hidden flex flex-col">
    {/* back-bar + Suspense + vues crm/email/calendar/tasks/invoices/memory/files/projects (inchangé) */}
    ...
  </div>
) : (
  <>{/* chat (inchangé) */}</>
)}
```
> Le bloc dashboard `) : showDashboard ? (...DashboardToday...)` est entièrement supprimé.

- [ ] **Step 2 : ChatHeader — bouton « Accueil »**

Importer `Home` de lucide, ajouter une prop `onHome?: () => void`, et placer un bouton en tête de la barre d'outils :
```tsx
<Button variant="ghost" size="icon" onClick={onHome} className="w-8 h-8 hover:bg-accent-cyan/10" title="Accueil" aria-label="Accueil">
  <Home className="w-4 h-4" />
</Button>
```
Dans `ChatLayout`, passer `onHome={() => useNavigationStore.getState().setView('home')}` au `ChatHeader`.

- [ ] **Step 3 : Supprimer DashboardToday**

```bash
mv "src/frontend/src/components/home/DashboardToday.tsx" ~/.Trash/
grep -rn "DashboardToday" src/frontend/src   # doit ne plus rien retourner
```
Mettre à jour `src/frontend/src/components/home/index.ts` (retirer l'export `DashboardToday`, exporter `HomeView`).

- [ ] **Step 4 : Vérifier types + lint + build mental**

Run:
```bash
cd src/frontend && npx tsc --noEmit 2>&1 | grep -c "error TS"   # 0
npm run -s lint 2>&1 | tail -2                                  # 0 erreur, ≤27 warnings
```

- [ ] **Step 5 : Commit**

```bash
git add src/frontend/src/components/chat/ChatLayout.tsx src/frontend/src/components/chat/ChatHeader.tsx src/frontend/src/components/home/index.ts
git rm src/frontend/src/components/home/DashboardToday.tsx
git commit -m "feat(home): vue Accueil branchée (landing + bouton header), DashboardToday retiré"
```

---

## Task 11 : Libellé du réglage de lancement

**Files:**
- Modify: `src/frontend/src/components/settings/AdvancedTab.tsx`

- [ ] **Step 1 : Renommer le libellé**

Repérer le toggle `therese-skip-dashboard` (`grep -n "therese-skip-dashboard" AdvancedTab.tsx`) et mettre à jour son libellé visible : « Afficher l'Accueil au lancement » (la préférence stockée reste `therese-skip-dashboard`, valeur `true` = NE PAS afficher). Vérifier que la sémantique du toggle reste cohérente (coché = Accueil affiché → stocke `'false'`).

- [ ] **Step 2 : Types + lint** — `cd src/frontend && npx tsc --noEmit 2>&1 | grep -c "error TS"` → 0.

- [ ] **Step 3 : Commit**

```bash
git add src/frontend/src/components/settings/AdvancedTab.tsx
git commit -m "chore(home): libellé réglage « Afficher l'Accueil au lancement »"
```

---

## Task 12 : Vérification finale

- [ ] **Step 1 : Frontend complet**

```bash
cd src/frontend
npx tsc --noEmit 2>&1 | grep -c "error TS"        # 0
npx vitest run 2>&1 | grep -E "Test Files|Tests " # tout vert
npm run -s lint 2>&1 | tail -2                     # 0 erreur, ≤27 warnings
```

- [ ] **Step 2 : Backend ciblé**

```bash
cd "$(git rev-parse --show-toplevel)"
uv run pytest tests/test_routers_dashboard.py -q --cov=app.routers.dashboard > /tmp/be.txt 2>&1; grep -E "passed|failed" /tmp/be.txt | tail -1
```

- [ ] **Step 3 : Vérification visuelle navigateur (Chrome MCP)**

Lancer l'app (`make dev`) et vérifier dans le navigateur : lancement sur l'Accueil, bouton header « Accueil » qui y revient, actions rapides fonctionnelles, conversations récentes cliquables, agenda/à-traiter, bande « Mise en route » qui n'affiche que les étapes non faites, AUCUN élément factice (pas de barre de recherche morte, badge fournisseur = provider réel, pas de fausse barre de saisie). Thème clair ET sombre.

- [ ] **Step 4 : MAJ dette/CHANGELOG**

Ajouter une entrée CHANGELOG « Vue Accueil » (sous 0.21.0 à venir) et noter dans le CLAUDE.md projet tout reliquat. Commit `docs`.

---

## Notes d'exécution
- Ordre strict T1→T12 (dépendances : composants avant HomeView avant câblage).
- `chat.new` : à l'exécution, confirmer s'il bascule déjà sur le chat ; sinon enrober dans QuickActions (Task 5 NB).
- Vérifier en T1 les champs obligatoires de `Calendar`/`EmailAccount`/`UserProfile` avant d'écrire les fixtures.
- Garder le lock `.agents-sync-paused` jusqu'à la fin ; ne PAS committer ce fichier.
