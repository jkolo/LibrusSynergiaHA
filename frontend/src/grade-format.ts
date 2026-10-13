export function parseDateForSort(dateStr: string): number {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(dateStr)) {
    const [d, m, y] = dateStr.split(".");
    return new Date(`${y}-${m}-${d}`).getTime();
  }
  return new Date(dateStr).getTime();
}

export function formatDate(dateStr: string): string {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(dateStr)) return dateStr;
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const [y, m, d] = dateStr.split("-");
    return `${d}.${m}.${y}`;
  }
  return dateStr;
}

/** "17.09" — day and month only, for tight spaces. */
export function formatShortDate(dateStr: string): string {
  return formatDate(dateStr).replace(/^(\d{2}\.\d{2})\.\d{4}$/, "$1");
}
