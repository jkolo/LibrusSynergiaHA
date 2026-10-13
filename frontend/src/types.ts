export interface HassMessage {
  sender: string;
  title: string;
  date: string;
  unread: boolean;
  is_recent: boolean;
  notification_dismissed: boolean;
  has_attachment: boolean;
  href: string;
}

export interface LibrusCardConfig {
  type: string;
  entity: string;
  entry_id: string;
  title?: string;
  only_unread?: boolean;
  count?: number;
}

export interface MessageListResponse {
  messages: HassMessage[];
  has_more: boolean;
  total_count: number;
}

/**
 * Link between a correcting grade and the grade it replaces. `date` is `null`
 * on `correction_of` when the integration could not identify the original.
 */
export interface HassGradeRef {
  grade: string | null;
  category: string | null;
  date: string | null;
}

export interface HassGrade {
  subject: string;
  grade: string;
  value: number | null;
  /** null when Librus does not show "Licz do średniej" (no weighted averages). */
  counts: boolean | null;
  /** null when Librus does not show "Waga". */
  weight: number | null;
  date: string;
  category: string;
  description: string;
  title: string;
  comment: string;
  teacher: string;
  is_recent: boolean;
  /** Set on a correction: the grade it replaces. */
  correction_of?: HassGradeRef | null;
  /** Set on a replaced grade: the grade that corrected it. */
  corrected_by?: HassGradeRef | null;
}

export interface LibrusGradesCardConfig {
  type: string;
  /** Any entity of the student (e.g. the aggregate grades sensor); subject sensors on its device are discovered automatically. */
  entity?: string;
  entities?: string[];
  title?: string;
  only_recent?: boolean;
  sort_order?: "asc" | "desc";
  height?: number;
}

export interface HassEntityRegistryEntry {
  entity_id: string;
  device_id?: string | null;
  platform?: string;
}

export interface HomeAssistant {
  states: Record<string, HassState>;
  entities?: Record<string, HassEntityRegistryEntry>;
  callService(
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>,
    target?: unknown,
    notifyOnError?: boolean,
    returnResponse?: boolean,
  ): Promise<unknown>;
}

export interface HassState {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}
