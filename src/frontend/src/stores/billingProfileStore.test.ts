import { beforeEach, describe, expect, it, vi } from 'vitest';

const { getBillingProfileStatusMock } = vi.hoisted(() => ({
  getBillingProfileStatusMock: vi.fn(),
}));

vi.mock('../services/api', () => ({
  getBillingProfileStatus: getBillingProfileStatusMock,
}));

import { useBillingProfileStore } from './billingProfileStore';

describe('billingProfileStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null, statutLecture: 'jamais_lu' });
  });

  it('passe missing à null quand le profil est complet', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });

    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().missing).toBeNull();
  });

  it('remplit missing avec les champs manquants quand le profil est incomplet', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: false, missing: ['SIRET', 'adresse'] });

    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET', 'adresse']);
  });

  it('reflète un profil complété entre deux refresh, sans remontage de composant', async () => {
    getBillingProfileStatusMock.mockResolvedValueOnce({ is_complete: false, missing: ['SIRET'] });
    await useBillingProfileStore.getState().refresh();
    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET']);

    getBillingProfileStatusMock.mockResolvedValueOnce({ is_complete: true, missing: [] });
    await useBillingProfileStore.getState().refresh();
    expect(useBillingProfileStore.getState().missing).toBeNull();
  });

  it('ignore une erreur réseau sans planter (garde-fou best-effort)', async () => {
    useBillingProfileStore.setState({ missing: ['SIRET'] });
    getBillingProfileStatusMock.mockRejectedValue(new Error('network down'));

    await expect(useBillingProfileStore.getState().refresh()).resolves.toBeUndefined();
    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET']);
  });
});

/**
 * B-001 : `missing: null` disait deux choses à la fois.
 *
 * La même valeur servait d'état initial, de verdict « profil complet » et de
 * résultat d'un `refresh` en échec (le `catch` était vide). Depuis l'ouverture
 * du formulaire, une lecture impossible laissait donc l'écran exactement dans
 * l'état d'un profil vérifié et conforme : aucun avertissement, alors que rien
 * n'avait été lu. L'application avait déjà tranché ailleurs (le parcours
 * prototype range un échec de lecture dans ses sources indisponibles).
 *
 * Trois cas, pas deux : jamais lu (au montage, on ne promet rien), lu (le
 * verdict de `missing` vaut), illisible (on l'annonce).
 */
describe("B-001 : un statut jamais lu ne s'annonce pas complet", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockReset();
    useBillingProfileStore.setState({ missing: null, statutLecture: 'jamais_lu' });
  });

  it("distingue « jamais lu », « illisible » et « lu »", async () => {
    expect(useBillingProfileStore.getState().statutLecture).toBe('jamais_lu');

    getBillingProfileStatusMock.mockRejectedValue(new Error('backend éteint'));
    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().statutLecture).toBe('illisible');
    expect(useBillingProfileStore.getState().missing).toBeNull();

    getBillingProfileStatusMock.mockReset();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().statutLecture).toBe('lu');
  });

  it("un profil complet et un profil illisible ne portent pas le même statut", async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    await useBillingProfileStore.getState().refresh();
    const complet = useBillingProfileStore.getState().statutLecture;

    useBillingProfileStore.setState({ missing: null, statutLecture: 'jamais_lu' });
    getBillingProfileStatusMock.mockReset();
    getBillingProfileStatusMock.mockRejectedValue(new Error('backend éteint'));
    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().statutLecture).not.toBe(complet);
  });

  it("une panne après une lecture réussie garde le dernier verdict connu", async () => {
    getBillingProfileStatusMock.mockResolvedValueOnce({ is_complete: false, missing: ['SIRET'] });
    await useBillingProfileStore.getState().refresh();

    getBillingProfileStatusMock.mockRejectedValueOnce(new Error('network down'));
    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET']);
    expect(useBillingProfileStore.getState().statutLecture).toBe('lu');
  });
});

/**
 * B-002 : deux `refresh` concurrents, aucun jeton de requête.
 *
 * `refresh` a deux appelants vivants : le formulaire de facture au montage, et
 * les Réglages après une sauvegarde de profil. La réponse d'AVANT la
 * sauvegarde pouvait donc arriver en dernier et réafficher « SIRET manquant »
 * juste après que l'utilisateur l'a renseigné. Le contre-exemple existait déjà
 * dans le dépôt : le hook du parcours prototype garde son `requestId`.
 */
describe('B-002 : une réponse périmée ne recouvre pas la récente', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getBillingProfileStatusMock.mockReset();
    useBillingProfileStore.setState({ missing: null, statutLecture: 'jamais_lu' });
  });

  it("la dernière requête gagne, quel que soit l'ordre d'arrivée", async () => {
    let resoudreAncienne!: (valeur: unknown) => void;
    let resoudreRecente!: (valeur: unknown) => void;
    getBillingProfileStatusMock
      .mockImplementationOnce(() => new Promise((r) => { resoudreAncienne = r; }))
      .mockImplementationOnce(() => new Promise((r) => { resoudreRecente = r; }));

    const ancienne = useBillingProfileStore.getState().refresh();
    const recente = useBillingProfileStore.getState().refresh();

    resoudreRecente({ is_complete: true, missing: [] });
    await recente;
    expect(useBillingProfileStore.getState().missing).toBeNull();

    resoudreAncienne({ is_complete: false, missing: ['SIRET'] });
    await ancienne;

    expect(useBillingProfileStore.getState().missing).toBeNull();
    expect(useBillingProfileStore.getState().statutLecture).toBe('lu');
  });

  it("un échec périmé n'efface pas le verdict de la requête récente", async () => {
    let rejeterAncienne!: (raison: unknown) => void;
    let resoudreRecente!: (valeur: unknown) => void;
    getBillingProfileStatusMock
      .mockImplementationOnce(() => new Promise((_r, rej) => { rejeterAncienne = rej; }))
      .mockImplementationOnce(() => new Promise((r) => { resoudreRecente = r; }));

    const ancienne = useBillingProfileStore.getState().refresh();
    const recente = useBillingProfileStore.getState().refresh();

    resoudreRecente({ is_complete: false, missing: ['adresse'] });
    await recente;

    rejeterAncienne(new Error('backend éteint'));
    await ancienne;

    expect(useBillingProfileStore.getState().missing).toEqual(['adresse']);
    expect(useBillingProfileStore.getState().statutLecture).toBe('lu');
  });

  it("l'échec d'une requête dépassée n'alarme pas pendant que la récente est en vol", async () => {
    let rejeterAncienne!: (raison: unknown) => void;
    let resoudreRecente!: (valeur: unknown) => void;
    getBillingProfileStatusMock
      .mockImplementationOnce(() => new Promise((_r, rej) => { rejeterAncienne = rej; }))
      .mockImplementationOnce(() => new Promise((r) => { resoudreRecente = r; }));

    const ancienne = useBillingProfileStore.getState().refresh();
    const recente = useBillingProfileStore.getState().refresh();

    rejeterAncienne(new Error('requête dépassée'));
    await ancienne;

    // Sans jeton sur le chemin d'échec, l'écran afficherait « vérification
    // impossible » alors qu'une lecture plus récente est encore en route.
    expect(useBillingProfileStore.getState().statutLecture).toBe('jamais_lu');

    resoudreRecente({ is_complete: true, missing: [] });
    await recente;

    expect(useBillingProfileStore.getState().statutLecture).toBe('lu');
  });

  it('un refresh ultérieur reste appliqué (le jeton ne se bloque pas)', async () => {
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: false, missing: ['SIRET'] });
    await useBillingProfileStore.getState().refresh();
    await useBillingProfileStore.getState().refresh();

    expect(useBillingProfileStore.getState().missing).toEqual(['SIRET']);
  });
});
