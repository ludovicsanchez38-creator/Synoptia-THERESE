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

/// Retourne le port du backend (dynamique en release, 8000 en dev)
#[tauri::command]
pub fn get_backend_port(state: tauri::State<'_, crate::BackendPort>) -> u16 {
    *state.0.lock().unwrap()
}
