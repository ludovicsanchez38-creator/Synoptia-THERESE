import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cn, formatRelativeDate, generateId, debounce, isTauri } from './utils';

describe('cn', () => {
  it('should merge class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('should handle conditional classes', () => {
    const isActive = true;
    const isHidden = false;
    expect(cn('base', isActive && 'active', isHidden && 'hidden')).toBe('base active');
  });

  it('should merge Tailwind classes correctly', () => {
    expect(cn('px-4', 'px-6')).toBe('px-6');
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
  });
});

describe('formatRelativeDate', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-21T12:00:00'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should return "À l\'instant" for recent dates', () => {
    const now = new Date();
    expect(formatRelativeDate(now)).toBe("À l'instant");
  });

  it('should return minutes for dates within an hour', () => {
    const date = new Date('2026-01-21T11:30:00');
    expect(formatRelativeDate(date)).toBe('Il y a 30 min');
  });

  it('should return hours for dates within a day', () => {
    const date = new Date('2026-01-21T09:00:00');
    expect(formatRelativeDate(date)).toBe('Il y a 3h');
  });

  it('should return "Hier" for yesterday', () => {
    const date = new Date('2026-01-20T12:00:00');
    expect(formatRelativeDate(date)).toBe('Hier');
  });

  it('should return days for dates within a week', () => {
    const date = new Date('2026-01-18T12:00:00');
    expect(formatRelativeDate(date)).toBe('Il y a 3 jours');
  });

  it('should return formatted date for older dates', () => {
    const date = new Date('2026-01-01T12:00:00');
    expect(formatRelativeDate(date)).toBe('1 janv.');
  });

  it('should handle string dates', () => {
    expect(formatRelativeDate('2026-01-21T12:00:00')).toBe("À l'instant");
  });
});

describe('generateId', () => {
  it('should generate unique IDs', () => {
    const ids = new Set<string>();
    for (let i = 0; i < 100; i++) {
      ids.add(generateId());
    }
    expect(ids.size).toBe(100);
  });

  it('should generate string IDs', () => {
    const id = generateId();
    expect(typeof id).toBe('string');
    expect(id.length).toBeGreaterThan(10);
  });
});

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should delay function execution', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);

    debounced();
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('should only call once for multiple rapid calls', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);

    debounced();
    debounced();
    debounced();

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('should pass arguments to debounced function', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);

    debounced('arg1', 'arg2');
    vi.advanceTimersByTime(100);

    expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
  });
});

describe('isTauri', () => {
  it('should return false when __TAURI__ is not defined', () => {
    expect(isTauri()).toBe(false);
  });

  it('should return true when __TAURI__ is defined', () => {
    (window as unknown as { __TAURI__: boolean }).__TAURI__ = true;
    expect(isTauri()).toBe(true);
    delete (window as unknown as { __TAURI__?: boolean }).__TAURI__;
  });
});
