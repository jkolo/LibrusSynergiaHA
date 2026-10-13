import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HassScheduleEvent, HomeAssistant } from "./types.js";
import { formatShortDate } from "./grade-format.js";
import { daysUntilLabel, examLabel, pickExams, pickReadings, shortWeekday, urgency } from "./schedule-view.js";

interface LibrusScheduleCardConfig {
  type: string;
  /** `sensor.<uczeń>_terminarz` */
  entity: string;
  title?: string;
  show_exams?: boolean;
  show_readings?: boolean;
}

@customElement("librus-schedule-card")
export class LibrusScheduleCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @state() private _config?: LibrusScheduleCardConfig;

  static getStubConfig(): LibrusScheduleCardConfig {
    return { type: "librus-schedule-card", entity: "" };
  }

  setConfig(config: LibrusScheduleCardConfig): void {
    if (!config.entity) throw new Error("entity jest wymagany (sensor.<uczeń>_terminarz)");
    this._config = config;
  }

  getCardSize(): number {
    return 4;
  }

  private _renderWhen(e: HassScheduleEvent) {
    return html`<div class="when ${urgency(e.days_until)}">
      <span class="days">${daysUntilLabel(e.days_until)}</span>
      <span class="date">${e.weekday ? shortWeekday(e.weekday) + " " : ""}${formatShortDate(e.date)}</span>
    </div>`;
  }

  private _renderExam(e: HassScheduleEvent) {
    return html`<li class="row">
      ${this._renderWhen(e)}
      <div class="what">
        <div class="headline">
          <span class="kind kind-${e.event_type}">${examLabel(e.event_type)}</span>
          <span class="subject">${e.subject}</span>
        </div>
        ${e.description
          ? html`<div class="desc" title="${e.description}">${e.description}</div>`
          : nothing}
      </div>
    </li>`;
  }

  private _renderReading(e: HassScheduleEvent) {
    const text = e.description || e.title;
    return html`<li class="row">
      ${this._renderWhen(e)}
      <div class="what">
        <div class="headline"><span class="subject">${e.subject || "Lektura"}</span></div>
        <div class="desc reading" title="${text}">📖 ${text}</div>
      </div>
    </li>`;
  }

  private _renderSection(
    heading: string,
    events: HassScheduleEvent[],
    empty: string,
    row: (e: HassScheduleEvent) => unknown,
  ) {
    return html`<section>
      <h3>${heading}${events.length ? html` <span class="count">${events.length}</span>` : nothing}</h3>
      ${events.length
        ? html`<ul>${events.map(row)}</ul>`
        : html`<div class="empty">${empty}</div>`}
    </section>`;
  }

  render() {
    if (!this._config || !this.hass) return nothing;
    const st = this.hass.states[this._config.entity];
    if (!st) {
      return html`<ha-card><div class="empty pad">Brak encji ${this._config.entity}</div></ha-card>`;
    }
    const events = (st.attributes?.events as HassScheduleEvent[] | undefined) ?? [];
    const truncated = Boolean(st.attributes?.events_truncated);
    const showExams = this._config.show_exams !== false;
    const showReadings = this._config.show_readings !== false;

    return html`
      <ha-card>
        <div class="card-header">${this._config.title ?? "Sprawdziany i lektury"}</div>
        ${showExams
          ? this._renderSection(
              "Sprawdziany", pickExams(events), "Brak zapowiedzianych sprawdzianów",
              e => this._renderExam(e),
            )
          : nothing}
        ${showReadings
          ? this._renderSection(
              "Lektury", pickReadings(events), "Brak lektur w terminarzu",
              e => this._renderReading(e),
            )
          : nothing}
        ${truncated
          ? html`<div class="note">Terminarz przycięty — dalsze wpisy są w kalendarzu „Terminarz”.</div>`
          : nothing}
      </ha-card>
    `;
  }

  static styles = css`
    :host { display: block; }
    ha-card { padding: 0 0 8px; }

    .card-header {
      padding: 12px 16px 4px;
      font-size: 1.1em;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    section { padding: 4px 16px 0; }
    h3 {
      margin: 8px 0 4px;
      font-size: 0.8em;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--secondary-text-color);
    }
    .count {
      display: inline-block;
      min-width: 1.4em;
      padding: 0 5px;
      border-radius: 9px;
      background: var(--secondary-background-color, #eee);
      text-align: center;
      font-weight: 600;
    }

    ul { list-style: none; margin: 0; padding: 0; }
    .row {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      padding: 7px 0;
      border-top: 1px solid var(--divider-color, #e0e0e0);
    }
    .row:first-child { border-top: none; }

    .when {
      flex: 0 0 76px;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 3px 4px;
      border-radius: 8px;
      background: var(--when-bg);
      color: var(--when-fg);
    }
    .when .days { font-weight: 700; font-size: 0.9em; white-space: nowrap; }
    .when .date { font-size: 0.75em; opacity: 0.85; white-space: nowrap; }
    .when.urgent { --when-bg: var(--error-color, #db4437); --when-fg: #fff; }
    .when.soon   { --when-bg: var(--warning-color, #ffa600); --when-fg: #fff; }
    .when.later  {
      --when-bg: var(--secondary-background-color, #f2f2f2);
      --when-fg: var(--primary-text-color);
    }

    .what { flex: 1 1 auto; min-width: 0; }
    .headline { display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; }
    .kind { font-weight: 600; color: var(--primary-text-color); }
    .kind-quiz { color: var(--warning-color, #ffa600); }
    .subject { color: var(--primary-text-color); }
    .kind + .subject { color: var(--secondary-text-color); }
    .desc {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      word-break: break-word;
    }
    .desc.reading { color: var(--primary-text-color); }

    .empty { font-size: 0.85em; color: var(--secondary-text-color); padding: 4px 0 8px; }
    .empty.pad { padding: 16px; }
    .note {
      margin: 6px 16px 0;
      font-size: 0.75em;
      color: var(--secondary-text-color);
    }
  `;
}

(window as Window & { customCards?: unknown[] }).customCards ??= [];
(window as Window & { customCards?: unknown[] }).customCards!.push({
  type: "librus-schedule-card",
  name: "Librus — Sprawdziany i lektury",
  description: "Nadchodzące sprawdziany i kartkówki z liczbą dni do terminu oraz lektury z terminarza.",
});

declare global {
  interface HTMLElementTagNameMap {
    "librus-schedule-card": LibrusScheduleCard;
  }
}
