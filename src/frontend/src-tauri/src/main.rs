//! THÉRÈSE v2 - Desktop Application
//!
//! L'assistante souveraine des entrepreneurs français.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    therese_lib::run();
}
