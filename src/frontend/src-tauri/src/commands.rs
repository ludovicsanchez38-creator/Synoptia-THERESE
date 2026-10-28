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

/// Marque l'arrêt du backend comme VOLONTAIRE avant un POST /api/shutdown
/// (updater) : la fin du sidecar ne déclenchera aucune relance automatique
/// (revue 0.40.1, F8 - une relance pendant l'installation Windows reprenait
/// un verrou sur l'exécutable et faisait échouer la mise à jour).
#[tauri::command]
pub fn prepare_backend_shutdown(app: tauri::AppHandle) {
    use std::sync::atomic::Ordering;
    use tauri::Manager;

    app.state::<crate::SidecarState>()
        .shutting_down
        .store(true, Ordering::SeqCst);
}

/// Ouvre seulement le PDF de la facture résolue par le moteur authentifié.
/// Aucun chemin ni programme d'ouverture n'est accepté depuis la webview.
#[tauri::command]
pub async fn ouvrir_pdf_facture(
    app: tauri::AppHandle,
    invoice_id: String,
    token: String,
) -> Result<(), String> {
    use tauri::Manager;
    use tauri_plugin_opener::OpenerExt;

    if invoice_id.is_empty() || !invoice_id.chars().all(|c| c.is_ascii_alphanumeric() || c == '-') {
        return Err("Identifiant de facture invalide.".into());
    }
    let port = *app.state::<crate::BackendPort>().0.lock().unwrap();
    let client = reqwest::Client::builder()
        .no_proxy()
        .redirect(reqwest::redirect::Policy::none())
        .timeout(std::time::Duration::from_secs(10))
        .build().map_err(|_| "Impossible de joindre le moteur local.".to_string())?;
    let response = client.get(format!("http://127.0.0.1:{port}/api/invoices/{invoice_id}/pdf-ouverture"))
        .header("X-Therese-Token", token)
        .send().await.map_err(|_| "Impossible de joindre le moteur local.".to_string())?;
    if !response.status().is_success() {
        return Err("Le moteur n’a pas autorisé l’ouverture de cette facture.".into());
    }
    #[derive(serde::Deserialize)]
    struct Pdf { pdf_path: String }
    let pdf: Pdf = response.json().await.map_err(|_| "Réponse du moteur illisible.".to_string())?;
    let path = std::path::PathBuf::from(pdf.pdf_path);
    if !path.is_absolute() || path.extension().and_then(|s| s.to_str()) != Some("pdf") || !path.is_file() {
        return Err("Le fichier PDF de cette facture est introuvable.".into());
    }
    // La portée est le fichier que le moteur vient de résoudre pour cet ID.
    app.opener().open_path(path.to_string_lossy(), None::<&str>)
        .map_err(|_| "Le lecteur PDF n’a pas pu ouvrir cette facture.".to_string())
}
