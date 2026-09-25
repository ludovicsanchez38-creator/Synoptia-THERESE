/**
 * Écran affiché pendant le chargement de l'application (composants différés,
 * lecture de la configuration). B-1474 : le nom s'écrivait « THERESE ».
 */
export function EcranDeChargement() {
  return (
    <div className="h-screen w-screen bg-bg flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent">
          THÉRÈSE
        </h1>
        <p className="text-text-muted mt-2 text-sm">Chargement...</p>
      </div>
    </div>
  );
}
