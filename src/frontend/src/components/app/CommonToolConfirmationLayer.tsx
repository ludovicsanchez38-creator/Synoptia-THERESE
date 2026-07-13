import { ToolConfirmationCard } from '../chat/ToolConfirmationCard';
import { Z_LAYER } from '../../styles/z-layers';

/**
 * Couche commune aux interfaces classique et 0.40.
 *
 * Une confirmation sensible ne doit jamais disparaître parce qu'un canevas,
 * un panneau guidé ou une autre interface remplace le contenu principal.
 */
export function CommonToolConfirmationLayer() {
  return (
    <div
      className={`pointer-events-none fixed inset-x-0 bottom-24 ${Z_LAYER.WIZARD} flex justify-center px-4`}
      data-testid="common-tool-confirmation-layer"
    >
      <div className="pointer-events-auto w-full max-w-2xl">
        <ToolConfirmationCard />
      </div>
    </div>
  );
}

