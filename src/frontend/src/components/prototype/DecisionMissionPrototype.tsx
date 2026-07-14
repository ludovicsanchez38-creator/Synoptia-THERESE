const portraitPositions = [
  ['0.48%', '1.42%'],
  ['33.49%', '1.42%'],
  ['66.51%', '1.42%'],
  ['99.52%', '1.42%'],
  ['0.48%', '98.58%'],
  ['33.49%', '98.58%'],
  ['66.51%', '98.58%'],
  ['99.52%', '98.58%'],
] as const;

/**
 * Portrait issu de l'atlas généré pour Thérèse, le Board et l'Atelier.
 * Le fond de secours reste volontairement relié au thème de l'application.
 */
export function CharacterPortrait({
  index,
  className = 'h-10 w-10 rounded-[12px]',
}: {
  index: number;
  className?: string;
}) {
  const [x, y] = portraitPositions[index] ?? portraitPositions[0];
  return (
    <span
      aria-hidden="true"
      className={`block shrink-0 overflow-hidden bg-text bg-no-repeat ${className}`}
      style={{
        backgroundImage: "url('/prototype/therese-character-atlas-v1.png')",
        backgroundPosition: `${x} ${y}`,
        backgroundSize: '412% 206%',
      }}
    />
  );
}
