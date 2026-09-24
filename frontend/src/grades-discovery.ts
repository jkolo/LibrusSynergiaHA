import type { HomeAssistant, LibrusGradesCardConfig } from "./types.js";

/**
 * Subject sensors are created only once a subject gets its first grade, and their
 * set changes between school years — so instead of a fixed list the card can take
 * any entity of the student and collect every sensor on the same device that
 * carries `grade_details`.
 */
export function resolveGradeEntities(hass: HomeAssistant, config: LibrusGradesCardConfig): string[] {
  const result = new Set<string>(config.entities ?? []);
  const deviceId = config.entity ? hass.entities?.[config.entity]?.device_id : undefined;
  if (deviceId) {
    for (const entry of Object.values(hass.entities ?? {})) {
      if (entry.device_id !== deviceId) continue;
      if (Array.isArray(hass.states[entry.entity_id]?.attributes?.grade_details)) {
        result.add(entry.entity_id);
      }
    }
  }
  return [...result];
}
