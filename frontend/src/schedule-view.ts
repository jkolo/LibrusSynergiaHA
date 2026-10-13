import type { HassScheduleEvent } from "./types.js";

const EXAM_LABELS: Record<string, string> = {
  exam: "Sprawdzian",
  quiz: "Kartkówka",
  class_test: "Praca klasowa",
  assessment: "Praca kontrolna",
  essay_test: "Wypracowanie",
  test: "Test",
};

export function examLabel(eventType: string): string {
  return EXAM_LABELS[eventType] ?? "Sprawdzian";
}

/** "dziś", "jutro", "za N dni" — Polish uses "dni" for every N ≥ 2. */
export function daysUntilLabel(days: number): string {
  if (days <= 0) return "dziś";
  if (days === 1) return "jutro";
  return `za ${days} dni`;
}

export type Urgency = "urgent" | "soon" | "later";

export function urgency(days: number): Urgency {
  if (days <= 1) return "urgent";
  if (days <= 3) return "soon";
  return "later";
}

function upcomingByDate(events: HassScheduleEvent[]): HassScheduleEvent[] {
  return events
    .filter(e => (e.days_until ?? 0) >= 0)
    .sort((a, b) => a.date.localeCompare(b.date));
}

export function pickExams(events: HassScheduleEvent[]): HassScheduleEvent[] {
  return upcomingByDate(events.filter(e => e.is_exam));
}

export function pickReadings(events: HassScheduleEvent[]): HassScheduleEvent[] {
  return upcomingByDate(events.filter(e => e.event_type === "reading"));
}

const WEEKDAY_SHORT: Record<string, string> = {
  "poniedziałek": "pn",
  "wtorek": "wt",
  "środa": "śr",
  "czwartek": "czw",
  "piątek": "pt",
  "sobota": "sob",
  "niedziela": "nd",
};

export function shortWeekday(weekday: string): string {
  return WEEKDAY_SHORT[weekday] ?? weekday;
}
