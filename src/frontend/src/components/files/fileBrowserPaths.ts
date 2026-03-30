export function normalizeBrowserPath(path: string) {
  return path.replace(/\\/g, '/');
}

export function isWindowsPath(path: string) {
  return /^[A-Za-z]:/.test(normalizeBrowserPath(path));
}

export function getParentBrowserPath(path: string): string | null {
  const normalized = normalizeBrowserPath(path);
  const parts = normalized.split('/').filter(Boolean);

  if (isWindowsPath(normalized)) {
    if (parts.length <= 1) return null;
    const parentParts = parts.slice(0, -1);
    return buildBrowserPathFromParts(parentParts, true);
  }

  if (parts.length <= 1) {
    return null;
  }

  return '/' + parts.slice(0, -1).join('/');
}

export function buildBrowserPathFromParts(parts: string[], isWindows: boolean) {
  const joined = parts.join('/');
  if (isWindows) {
    return parts.length === 1 && /^[A-Za-z]:$/.test(parts[0]) ? `${parts[0]}/` : joined;
  }
  return '/' + joined;
}
