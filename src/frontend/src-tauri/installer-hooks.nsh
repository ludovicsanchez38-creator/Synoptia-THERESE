; Hooks NSIS personnalises pour l'installeur Windows de THERESE (Tauri v2).
;
; BUG-111 : a la desinstallation, quand l'utilisateur coche
; "Supprimer les donnees de l'application", Tauri efface bien les dossiers
; standards de l'app ($APPDATA / $LOCALAPPDATA\fr.synoptia.therese), MAIS pas
; le dossier de donnees backend de THERESE, situe dans le profil utilisateur
; (~/.therese, soit $PROFILE\.therese sous Windows). Resultat : parametrages,
; projets, conversations, comptes etc. survivaient a une desinstall "avec
; suppression des donnees", empechant de repartir d'un profil vierge.
;
; Ce hook s'execute APRES le bloc de suppression standard de Tauri, dans la
; section de desinstallation. La variable $DeleteAppDataCheckboxState vaut 1
; quand la case "supprimer les donnees" a ete cochee : on supprime alors aussi
; le dossier de donnees backend.

!macro NSIS_HOOK_POSTUNINSTALL
  ${If} $DeleteAppDataCheckboxState = 1
    ; Dossier de donnees backend THERESE (db, parametrages, projets, images,
    ; conversations, comptes, cle de chiffrement...).
    RMDir /r "$PROFILE\.therese"
  ${EndIf}
!macroend
