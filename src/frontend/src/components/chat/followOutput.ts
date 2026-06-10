/**
 * US-010 : politique de suivi du scroll (react-virtuoso `followOutput`).
 *
 * Le scroll ne « colle » au bas que si l'utilisateur y est déjà : s'il a
 * remonté la conversation pour lire, on ne le ramène jamais de force.
 */
export type FollowOutputBehavior = 'auto' | 'smooth' | false;

export function computeFollowOutput(
  isAtBottom: boolean,
  isStreaming: boolean
): FollowOutputBehavior {
  if (!isAtBottom) return false;
  return isStreaming ? 'auto' : 'smooth';
}
