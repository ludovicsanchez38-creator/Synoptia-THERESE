/**
 * Registre canonique des cartes du tiroir (B0, 0.48).
 *
 * Les ids du Centre de capacités, exportés pour que le manifeste puisse
 * référencer une carte (`binding: {registre: 'tiroir', carte}`) et que les
 * tests vérifient mécaniquement l'existence et la destination de chacune.
 * La source reste `CapabilityCenter` : ce module expose, il ne duplique pas.
 */
import {
  capabilities,
  type CapabilityItem,
} from '../../components/prototype/CapabilityCenter';

export const CARTES: readonly CapabilityItem[] = capabilities;

export const carteIds: readonly string[] = capabilities.map((c) => c.id);
