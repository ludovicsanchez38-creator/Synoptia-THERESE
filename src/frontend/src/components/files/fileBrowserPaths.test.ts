import { describe, expect, it } from 'vitest';

import { buildBrowserPathFromParts, getParentBrowserPath } from './fileBrowserPaths';

describe('fileBrowserPaths', () => {
  it('remonte correctement un chemin Windows', () => {
    expect(getParentBrowserPath('C:\\Users\\Ludo\\Documents')).toBe('C:/Users/Ludo');
  });

  it('remonte vers la racine Windows avec slash final', () => {
    expect(getParentBrowserPath('C:/Users')).toBe('C:/');
  });

  it('désactive la remontée à la racine Windows', () => {
    expect(getParentBrowserPath('C:\\')).toBeNull();
  });

  it('construit un breadcrumb Windows sans slash initial parasite', () => {
    expect(buildBrowserPathFromParts(['C:', 'Users', 'Ludo'], true)).toBe('C:/Users/Ludo');
  });

  it('conserve le slash final pour la racine Windows', () => {
    expect(buildBrowserPathFromParts(['C:'], true)).toBe('C:/');
  });

  it('construit un breadcrumb POSIX avec slash initial', () => {
    expect(buildBrowserPathFromParts(['home', 'ludo'], false)).toBe('/home/ludo');
  });
});
