//! THÉRÈSE v2 - Tauri Library
//!
//! L'assistante souveraine des entrepreneurs français.
//! Gère le sidecar backend Python en mode release.

use std::net::TcpListener;
use std::sync::Mutex;
use tauri::Emitter;
use tauri::Manager;
use tauri::RunEvent;

/// IPC Commands module
mod commands;

/// Trouve un port TCP libre en laissant l'OS en assigner un.
fn find_free_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0")
        .expect("Impossible de trouver un port libre");
    let port = listener.local_addr().unwrap().port();
    drop(listener);
    port
}

/// Écrit dans ~/.therese/logs/sidecar.log
fn log_sidecar(msg: &str) {
    if let Some(home) = dirs::home_dir() {
        let log_dir = home.join(".therese").join("logs");
        let _ = std::fs::create_dir_all(&log_dir);
        let log_file = log_dir.join("sidecar.log");
        if let Ok(mut f) = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_file)
        {
            use std::io::Write;
            let _ = writeln!(f, "{}", msg);
        }
    }
}

/// Port du backend, accessible depuis le frontend via IPC
pub struct BackendPort(pub Mutex<u16>);

/// État du sidecar backend (release uniquement)
struct SidecarState {
    child: Mutex<Option<tauri_plugin_shell::process::CommandChild>>,
}

/// Initialize Tauri plugins and setup
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_mic_recorder::init())
        .manage(SidecarState {
            child: Mutex::new(None),
        })
        .manage(BackendPort(Mutex::new(8000)))
        .setup(|app| {
            // Get main window
            if let Some(window) = app.get_webview_window("main") {
                // macOS: Make the title bar transparent
                #[cfg(target_os = "macos")]
                {
                    use tauri::TitleBarStyle;
                    let _ = window.set_title_bar_style(TitleBarStyle::Overlay);
                }

                // Focus window
                let _ = window.set_focus();
            }

            // En release uniquement : lancer le sidecar backend
            #[cfg(not(debug_assertions))]
            {
                use tauri_plugin_shell::ShellExt;
                use tauri_plugin_shell::process::CommandEvent;

                let port = find_free_port();
                let port_str = port.to_string();

                // Stocker le port pour le frontend
                let backend_port = app.state::<BackendPort>();
                *backend_port.0.lock().unwrap() = port;

                let models_path = dirs::home_dir()
                    .unwrap_or_default()
                    .join(".therese/models")
                    .to_string_lossy()
                    .to_string();

                log_sidecar(&format!("Démarrage sidecar sur port {}", port));

                // macOS : supprimer la quarantaine préventivement (ciblé, pas tous les xattr)
                #[cfg(target_os = "macos")]
                {
                    if let Ok(exe) = std::env::current_exe() {
                        if let Some(macos_dir) = exe.parent() {
                            log_sidecar(&format!("Suppression quarantaine : {}", macos_dir.display()));
                            let _ = std::process::Command::new("xattr")
                                .args(["-dr", "com.apple.quarantine", &macos_dir.to_string_lossy()])
                                .output();
                        }
                    }
                }

                // Créer la commande sidecar (peut échouer si binaire introuvable)
                match app.shell().sidecar("backend") {
                    Ok(cmd) => {
                        let cmd = cmd
                            .args(["--host", "127.0.0.1", "--port", &port_str])
                            .env("THERESE_PORT", &port_str)
                            .env("THERESE_ENV", "production")
                            .env("SENTENCE_TRANSFORMERS_HOME", &models_path);

                        match cmd.spawn() {
                            Ok((mut rx, child)) => {
                                let msg = format!("Sidecar démarré (PID: {}, port: {})", child.pid(), port);
                                println!("[THÉRÈSE] {}", msg);
                                log_sidecar(&msg);

                                // Stocker le child pour le kill propre à la fermeture
                                let state = app.state::<SidecarState>();
                                *state.child.lock().unwrap() = Some(child);

                                // Logger stdout/stderr du sidecar dans le fichier de log
                                tauri::async_runtime::spawn(async move {
                                    while let Some(event) = rx.recv().await {
                                        match event {
                                            CommandEvent::Stdout(line) => {
                                                let text = String::from_utf8_lossy(&line);
                                                print!("[backend] {}", text);
                                                log_sidecar(&format!("[stdout] {}", text.trim()));
                                            }
                                            CommandEvent::Stderr(line) => {
                                                let text = String::from_utf8_lossy(&line);
                                                eprint!("[backend] {}", text);
                                                log_sidecar(&format!("[stderr] {}", text.trim()));
                                            }
                                            CommandEvent::Terminated(payload) => {
                                                let msg = format!(
                                                    "Sidecar terminé (code: {:?}, signal: {:?})",
                                                    payload.code, payload.signal
                                                );
                                                println!("[THÉRÈSE] {}", msg);
                                                log_sidecar(&msg);
                                                break;
                                            }
                                            _ => {}
                                        }
                                    }
                                });
                            }
                            Err(e) => {
                                let msg = format!("Erreur lancement sidecar : {}", e);
                                eprintln!("[THÉRÈSE] {}", msg);
                                log_sidecar(&msg);
                                if let Some(window) = app.get_webview_window("main") {
                                    let _ = window.emit("sidecar-error", &msg);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        let msg = format!("Binaire sidecar introuvable : {}", e);
                        eprintln!("[THÉRÈSE] {}", msg);
                        log_sidecar(&msg);
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.emit("sidecar-error", &msg);
                        }
                    }
                }
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::greet,
            commands::get_system_info,
            commands::get_backend_port,
        ])
        .build(tauri::generate_context!())
        .expect("error while building THÉRÈSE");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            // Kill propre du sidecar à la fermeture
            let state = app_handle.state::<SidecarState>();
            let mut guard = state.child.lock().unwrap();
            if let Some(child) = guard.take() {
                println!("[THÉRÈSE] Arrêt du sidecar backend...");
                let _ = child.kill();
            }
        }
    });
}
