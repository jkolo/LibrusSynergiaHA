import { formatDate, formatShortDate } from "./grade-format.js";
import type { HassGrade } from "./types.js";

export interface GradeEntry {
  /** The grade shown in its own right: the newest one of a correction chain. */
  grade: HassGrade;
  /** Grades it replaced, oldest first. Empty for an ordinary grade. */
  replaced: HassGrade[];
}

/** The grade a correction replaces, when the integration identified it. */
export function findReplaced(correction: HassGrade, grades: HassGrade[]): HassGrade | undefined {
  const ref = correction.correction_of;
  if (!ref?.date) return undefined;
  return grades.find(
    other =>
      other !== correction &&
      other.date === ref.date &&
      other.grade === ref.grade &&
      other.corrected_by?.date === correction.date &&
      other.corrected_by?.grade === correction.grade,
  );
}

/** True when following the replaced-grade links from `from` reaches `target`. */
function leadsTo(
  from: HassGrade,
  target: HassGrade,
  originalOf: Map<HassGrade, HassGrade>,
): boolean {
  const seen = new Set<HassGrade>();
  for (let cur: HassGrade | undefined = from; cur && !seen.has(cur); cur = originalOf.get(cur)) {
    if (cur === target) return true;
    seen.add(cur);
  }
  return false;
}

/**
 * Fold every replaced grade into the correction that replaced it, so each
 * assessment appears once. Expects `grades` in display order; the order is kept.
 * Grades whose original could not be identified stay as entries of their own.
 */
export function collapseCorrections(grades: HassGrade[]): GradeEntry[] {
  const originalOf = new Map<HassGrade, HassGrade>();
  const folded = new Set<HassGrade>();

  for (const correction of grades) {
    const original = findReplaced(correction, grades);
    if (!original || folded.has(original)) continue;
    // Never let inconsistent data make a grade disappear from the card.
    if (leadsTo(original, correction, originalOf)) continue;
    originalOf.set(correction, original);
    folded.add(original);
  }

  return grades
    .filter(grade => !folded.has(grade))
    .map(grade => {
      const replaced: HassGrade[] = [];
      for (let cur = originalOf.get(grade); cur; cur = originalOf.get(cur)) {
        replaced.unshift(cur);
      }
      return { grade, replaced };
    });
}

/** "poprawa oceny 1 (kartkówka) z 17.09.2026" — for a grade that corrects another. */
export function correctionNote(grade: HassGrade): string | null {
  const ref = grade.correction_of;
  if (!ref) return null;
  const what = [ref.grade, ref.category ? `(${ref.category})` : null].filter(Boolean).join(" ");
  const when = ref.date ? ` z ${formatDate(ref.date)}` : "";
  return `poprawa oceny${what ? ` ${what}` : ""}${when}`;
}

/** "poprawiona oceną 6 z 28.09.2026" — for a grade that has been corrected. */
export function supersededNote(grade: HassGrade): string | null {
  const by = grade.corrected_by;
  if (!by) return null;
  const when = by.date ? ` z ${formatDate(by.date)}` : "";
  return `poprawiona oceną${by.grade ? ` ${by.grade}` : ""}${when}`;
}

/** "poprawa z 17.09" — short form for a list row. */
export function correctionLabel(grade: HassGrade): string | null {
  const ref = grade.correction_of;
  if (!ref) return null;
  return ref.date ? `poprawa z ${formatShortDate(ref.date)}` : "poprawa";
}

/** "poprawiona na 6" — short form for a list row. */
export function supersededLabel(grade: HassGrade): string | null {
  const by = grade.corrected_by;
  if (!by) return null;
  return by.grade ? `poprawiona na ${by.grade}` : "poprawiona";
}
