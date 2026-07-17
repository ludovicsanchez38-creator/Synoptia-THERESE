//! Tauri IPC Commands
//!
//! Commands callable from the frontend via invoke().

use serde::Serialize;

/// Simple greeting command for testing
#[tauri::command]
pub fn greet(name: &str) -> String {
    format!("Bonjour {} ! Je suis THÉRÈSE, votre assistante.", name)
}

/// System information for debugging
#[derive(Serialize)]
pub struct SystemInfo {
    pub os: String,
    pub arch: String,
    pub version: String,
}

#[tauri::command]
pub fn get_system_info() -> SystemInfo {
    SystemInfo {
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    }
}

/// Retourne le port du backend (17293 par défaut)
#[tauri::command]
pub fn get_backend_port(state: tauri::State<'_, crate::BackendPort>) -> u16 {
    *state.0.lock().unwrap()
}

/// Relance le moteur local à la demande (bouton « Relancer le moteur local »).
///
/// Revue 0.40 : après 3 relances automatiques épuisées, l'interface offre une
/// relance manuelle qui remet le compteur à zéro. En dev, le backend est géré
/// par `make dev` : la commande répond une erreur explicite.
#[tauri::command]
pub fn restart_backend(app: tauri::AppHandle) -> Result<(), String> {
    #[cfg(not(debug_assertions))]
    {
        use std::sync::atomic::Ordering;
        use tauri::Manager;

        let state = app.state::<crate::SidecarState>();
        state.shutting_down.store(false, Ordering::SeqCst);
        state.restart_attempts.store(0, Ordering::SeqCst);
        // Un éventuel process suspendu (vivant mais muet) ne doit pas survivre
        // à la relance : le port doit être libre pour le nouveau sidecar.
        if let Some(old) = state.child.lock().unwrap().take() {
            let _ = old.kill();
        }
        crate::spawn_backend_sidecar(&app);
        Ok(())
    }
    #[cfg(debug_assertions)]
    {
        let _ = app;
        Err("Mode développement : relance le backend via make dev".to_string())
    }
}
