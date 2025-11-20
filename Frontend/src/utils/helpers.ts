/**
 * Formatea una fecha en formato legible
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? parseIsoToDate(date) : date;
  return d.toLocaleString('es-CL', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'America/Santiago'
  });
}

/**
 * Parse an ISO datetime string that may be missing timezone info.
 * If the string already contains a timezone (Z or ±hh:mm) it is parsed as-is.
 * Otherwise the string is treated as UTC by appending a 'Z' before parsing.
 */
export function parseIsoToDate(iso: string): Date {
  if (!iso) return new Date(NaN);
  // If it already has timezone info (Z or +hh:mm / -hh:mm), parse directly
  if (/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso)) {
    return new Date(iso);
  }

  // Parse components YYYY-MM-DDTHH:mm:ss(.sss...)
  const m = iso.match(/^\s*(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?\s*$/);
  if (!m) {
    // fallback: try plain Date parse
    return new Date(iso);
  }

  const year = Number(m[1]);
  const month = Number(m[2]);
  const day = Number(m[3]);
  const hour = Number(m[4]);
  const minute = Number(m[5]);
  const second = m[6] ? Number(m[6]) : 0;
  const ms = m[7] ? Number((m[7] + '000').slice(0, 3)) : 0;

  // Build a UTC candidate from the same numeric fields
  const utcCandidate = Date.UTC(year, month - 1, day, hour, minute, second, ms);

  // Helper to get timezone offset in minutes for a given timeZone at a given UTC date
  const tzOffsetMinutes = (dateUtc: Date, timeZone: string) => {
    const dtf = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hour12: false,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    const parts: Record<string, string> = {};
    for (const p of dtf.formatToParts(dateUtc)) {
      if (p.type !== 'literal') parts[p.type] = p.value;
    }
    // Build a UTC timestamp from the timezone-formatted fields
    const asUtc = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
      Number(parts.second)
    );
    // offset = asUtc - dateUtc.getTime()
    return (asUtc - dateUtc.getTime()) / 60000;
  };

  // Compute offset for America/Santiago at that instant
  const offsetMinutes = tzOffsetMinutes(new Date(utcCandidate), 'America/Santiago');
  const realUtcMs = utcCandidate - offsetMinutes * 60000;
  return new Date(realUtcMs);
}

/**
 * Formatea un número con decimales especificados
 */
export function formatNumber(value: number, decimals: number = 1): string {
  return value.toFixed(decimals);
}

/**
 * Trunca un texto a una longitud máxima
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Valida un email
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Capitaliza la primera letra de una cadena
 */
export function capitalize(text: string): string {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

/**
 * Convierte un objeto a query string
 */
export function objectToQueryString(obj: Record<string, unknown>): string {
  return Object.entries(obj)
    .filter(([, value]) => value !== null && value !== undefined)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
