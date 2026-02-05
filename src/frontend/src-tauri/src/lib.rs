//! THÉRÈSE v2 - Tauri Library
//!
//! L'assistante souveraine des entrepreneurs français.

use tauri::Manager;

/// IPC Commands module
mod commands;

/// Initialize Tauri plugins and setup
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_mic_recorder::init())
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

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::greet,
            commands::get_system_info,
        ])
        .run(tauri::generate_context!())
        .expect("error while running THÉRÈSE");
}
