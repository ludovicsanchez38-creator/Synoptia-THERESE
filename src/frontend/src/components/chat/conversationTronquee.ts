/**
 * Lot F (revue 30/08) : une conversation dont le listing annonce plus de
 * messages que l'écran n'en a chargé. Sans ça, rouvrir un fil de 110
 * messages faisait croire que les 10 derniers n'existaient pas.
 */
export function conversationEstTronquee(conv: {
  messageCount?: number;
  messages: { length: number };
} | null): boolean {
  if (!conv) return false;
  return (conv.messageCount ?? 0) > conv.messages.length;
}
