# Story E1-05 : Créer la communication IPC Tauri ↔ Backend

## Description

En tant que **développeur**,
Je veux **avoir une communication fluide entre le frontend Tauri et le backend Python**,
Afin de **permettre aux composants React d'appeler les APIs backend**.

## Contexte technique

- **Composants impactés** : Tauri shell, React frontend, Backend Python
- **Dépendances** : E1-01, E1-02
- **Fichiers concernés** :
  - `src-tauri/src/main.rs` (màj)
  - `src-tauri/tauri.conf.json` (màj)
  - `src/frontend/src/lib/api.ts` (nouveau)

## Critères d'acceptation

- [ ] Backend Python lancé comme sidecar par Tauri
- [ ] Frontend peut appeler `/health` via fetch
- [ ] Gestion du lifecycle (start/stop backend avec l'app)
- [ ] Logs backend visibles dans la console Tauri
- [ ] Timeout et retry configurés
- [ ] CORS correctement configuré

## Notes techniques

### Architecture IPC

```
┌─────────────────────────────────────────────────────────┐
│                    Tauri Process                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐         ┌───────────────────────┐  │
│  │   Rust Core     │         │    WebView (React)    │  │
│  │                 │         │                       │  │
│  │  spawn_sidecar  │         │   fetch("localhost")  │  │
│  │       │         │         │         │             │  │
│  └───────┼─────────┘         └─────────┼─────────────┘  │
│          │                             │                │
│          ▼                             ▼                │
│  ┌─────────────────────────────────────────────────────┐│
│  │              Python Backend (sidecar)                ││
│  │                 localhost:8765                       ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Configuration Tauri sidecar

```json
// src-tauri/tauri.conf.json
{
  "bundle": {
    "externalBin": [
      "binaries/therese-backend"
    ]
  }
}
```

```rust
// src-tauri/src/main.rs
use tauri::Manager;
use tauri_plugin_shell::ShellExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let sidecar = app.shell()
                .sidecar("therese-backend")
                .expect("failed to create sidecar");

            let (mut rx, mut _child) = sidecar.spawn()
                .expect("failed to spawn sidecar");

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    if let tauri_plugin_shell::process::CommandEvent::Stdout(line) = event {
                        println!("[backend] {}", String::from_utf8_lossy(&line));
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Client API frontend

```typescript
// src/frontend/src/lib/api.ts
const API_BASE = "http://localhost:8765";

interface ApiOptions {
  timeout?: number;
  retries?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit & ApiOptions = {}
  ): Promise<T> {
    const { timeout = 30000, retries = 2, ...fetchOptions } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...fetchOptions.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async health(): Promise<{ status: string; version: string }> {
    return this.request("/health");
  }
}

export const api = new ApiClient(API_BASE);
```

### Hook React pour API

```typescript
// src/frontend/src/hooks/useApi.ts
import { useState, useCallback } from "react";
import { api } from "../lib/api";

export function useHealth() {
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  const checkHealth = useCallback(async () => {
    try {
      await api.health();
      setStatus("ok");
    } catch {
      setStatus("error");
    }
  }, []);

  return { status, checkHealth };
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Backend démarre avec l'app Tauri
- [ ] Frontend reçoit réponse de `/health`
- [ ] Backend s'arrête proprement à la fermeture
- [ ] Logs visibles dans la console dev
- [ ] Gestion d'erreur si backend ne démarre pas

---

*Sprint : 1*
*Assigné : Agent Dev*
