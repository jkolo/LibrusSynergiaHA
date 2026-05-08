import { LitElement, html, css, nothing } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import type { HassGrade, HomeAssistant, LibrusGradesCardConfig } from "./types.js";

function parseDateForSort(dateStr: string): number {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(dateStr)) {
    const [d, m, y] = dateStr.split(".");
    return new Date(`${y}-${m}-${d}`).getTime();
  }
  return new Date(dateStr).getTime();
}

function formatDate(dateStr: string): string {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(dateStr)) return dateStr;
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const [y, m, d] = dateStr.split("-");
    return `${d}.${m}.${y}`;
  }
  return dateStr;
}

function gradeTypeInfo(category: string): { label: string; cssClass: string } {
  const cat = category.toLowerCase();
  if (cat.includes("sprawdzian") || cat.includes("test"))
    return { label: "SPRAWDZ", cssClass: "type-test" };
  if (cat.includes("kartkówka") || cat.includes("kartkowka"))
    return { label: "KARTK", cssClass: "type-quiz" };
  if (cat.includes("praca klasow") || cat.includes("praca kontrolna"))
    return { label: "PR.KL", cssClass: "type-classwork" };
  if (cat.includes("praca domow"))
    return { label: "PR.DOM", cssClass: "type-homework" };
  if (cat.includes("wypracowanie"))
    return { label: "WYPRAC", cssClass: "type-essay" };
  const truncated = cat.slice(0, 5).toUpperCase();
  return { label: truncated || "INNE", cssClass: "type-other" };
}

@customElement("librus-grades-card")
export class LibrusGradesCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @state() private _config?: LibrusGradesCardConfig;
  @state() private _selectedGrade: HassGrade | null = null;

  @query("dialog") private _dialog?: HTMLDialogElement;

  static getStubConfig(): LibrusGradesCardConfig {
    return { type: "librus-grades-card", entities: [], title: "Oceny" };
  }

  setConfig(config: LibrusGradesCardConfig): void {
    if (!config.entities || !Array.isArray(config.entities)) {
      throw new Error("entities (lista sensorów per-przedmiot) jest wymagana");
    }
    this._config = config;
  }

  getCardSize(): number {
    return 6;
  }

  private get _grades(): HassGrade[] {
    if (!this.hass || !this._config) return [];
    const all: HassGrade[] = [];
    for (const entityId of this._config.entities) {
      const state = this.hass.states[entityId];
      const details = state?.attributes?.grade_details as HassGrade[] | undefined;
      if (details) all.push(...details);
    }
    const filtered = this._config.only_recent ? all.filter(g => g.is_recent) : all;
    const sorted = filtered.sort((a, b) => parseDateForSort(a.date) - parseDateForSort(b.date));
    return (this._config.sort_order ?? "desc") === "desc" ? sorted.reverse() : sorted;
  }

  private _openDialog(grade: HassGrade): void {
    this._selectedGrade = grade;
    this._dialog?.showModal();
  }

  private _renderRow(grade: HassGrade) {
    const { label, cssClass } = gradeTypeInfo(grade.category);
    const tooltip = [
      grade.teacher,
      grade.weight != null ? `waga ${grade.weight}` : "",
    ].filter(Boolean).join(" · ");
    return html`
      <div
        class="grade-row ${grade.is_recent ? "recent" : ""}"
        data-tooltip="${tooltip || nothing}"
        role="button"
        tabindex="0"
        @click="${() => this._openDialog(grade)}"
        @keydown="${(e: KeyboardEvent) => e.key === "Enter" && this._openDialog(grade)}"
      >
        <span class="grade-badge ${cssClass}">${label}</span>
        <span class="grade-subject">${grade.subject}</span>
        <span class="grade-value">${grade.grade}</span>
        <span class="grade-date">${formatDate(grade.date)}</span>
      </div>
    `;
  }

  private _renderDialog() {
    const g = this._selectedGrade;
    return html`
      <dialog @close="${() => { this._selectedGrade = null; }}">
        ${g ? html`
          <div class="dlg-header">
            <div class="dlg-meta">
              <div class="dlg-subject">${g.subject}</div>
              <div class="dlg-category">${g.category || "—"}${g.category && g.date ? " · " : ""}${formatDate(g.date)}</div>
            </div>
            <ha-icon-button
              .label=${"Zamknij"}
              .path=${"M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"}
              @click="${() => this._dialog?.close()}"
            ></ha-icon-button>
          </div>
          <div class="dlg-body">
            <div class="dlg-grade-large ${gradeTypeInfo(g.category).cssClass}">${g.grade}</div>
            <div class="dlg-details">
              ${g.teacher ? html`<div class="dlg-detail-row"><span class="dlg-detail-label">Nauczyciel</span><span>${g.teacher}</span></div>` : nothing}
              ${g.weight != null ? html`<div class="dlg-detail-row"><span class="dlg-detail-label">Waga</span><span>${g.weight}</span></div>` : nothing}
              <div class="dlg-detail-row"><span class="dlg-detail-label">Liczy do średniej</span><span>${g.counts ? "Tak" : "Nie"}</span></div>
              ${g.title ? html`<div class="dlg-detail-row"><span class="dlg-detail-label">Temat</span><span>${g.title}</span></div>` : nothing}
              ${g.description ? html`<div class="dlg-detail-row"><span class="dlg-detail-label">Poprawa</span><span>${g.description}</span></div>` : nothing}
            </div>
          </div>
        ` : nothing}
      </dialog>
    `;
  }

  render() {
    if (!this._config) return nothing;
    const grades = this._grades;
    const title = this._config.title ?? "Oceny";
    const newCount = grades.filter(g => g.is_recent).length;
    return html`
      <ha-card>
        <div class="card-header">
          <span class="card-title">${title}</span>
          <span class="card-count">${grades.length}${newCount > 0 ? html` <span class="new-badge">${newCount} nowe</span>` : nothing}</span>
        </div>
        <div class="grade-list">
          ${grades.length === 0
            ? html`<div class="empty">Brak ocen</div>`
            : grades.map(g => this._renderRow(g))}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }

  static styles = css`
    :host { display: block; height: 100%; }
    ha-card {
      padding: 0;
      overflow: hidden;
      height: 100%;
      display: flex;
      flex-direction: column;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px 8px;
    }
    .card-title {
      font-size: 1.1em;
      font-weight: 500;
      color: var(--primary-text-color);
    }
    .card-count {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .new-badge {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-radius: 10px;
      padding: 1px 7px;
      font-size: 0.8em;
    }

    .grade-list {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
      max-height: 480px;
    }

    .grade-row {
      display: grid;
      grid-template-columns: 68px 1fr auto auto;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-bottom: 1px solid var(--divider-color);
      cursor: pointer;
      position: relative;
      transition: background 0.15s;
    }
    .grade-row:hover {
      background: var(--secondary-background-color);
    }
    .grade-row.recent {
      background: color-mix(in srgb, var(--primary-color) 8%, transparent);
    }
    .grade-row.recent:hover {
      background: color-mix(in srgb, var(--primary-color) 15%, transparent);
    }

    /* CSS tooltip */
    .grade-row[data-tooltip]:not([data-tooltip=""]):hover::after {
      content: attr(data-tooltip);
      position: absolute;
      bottom: calc(100% + 4px);
      left: 50%;
      transform: translateX(-50%);
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 0.75em;
      white-space: nowrap;
      z-index: 10;
      pointer-events: none;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
      color: var(--primary-text-color);
    }

    .grade-badge {
      display: inline-block;
      background: var(--badge-bg, #888);
      color: #fff;
      font-size: 0.65em;
      font-weight: 600;
      letter-spacing: 0.04em;
      padding: 2px 5px;
      border-radius: 3px;
      text-align: center;
      min-width: 52px;
    }
    .type-test      { --badge-bg: var(--error-color, #f44336); }
    .type-quiz      { --badge-bg: #ff9800; }
    .type-classwork { --badge-bg: var(--info-color, #2196f3); }
    .type-homework  { --badge-bg: #4caf50; }
    .type-essay     { --badge-bg: #9c27b0; }
    .type-other     { --badge-bg: var(--secondary-text-color, #888); }

    .grade-subject {
      font-size: 0.9em;
      color: var(--primary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .grade-value {
      font-size: 1em;
      font-weight: 600;
      color: var(--primary-text-color);
      min-width: 28px;
      text-align: right;
    }
    .grade-date {
      font-size: 0.78em;
      color: var(--secondary-text-color);
      white-space: nowrap;
      min-width: 72px;
      text-align: right;
    }

    .empty {
      padding: 24px 16px;
      text-align: center;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }

    /* Dialog */
    dialog[open] {
      max-width: min(480px, 95vw);
      max-height: 80vh;
      border: none;
      border-radius: var(--ha-card-border-radius, 12px);
      box-shadow: var(--ha-card-box-shadow, 0 4px 16px rgba(0, 0, 0, 0.4));
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
      padding: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    dialog::backdrop {
      background: rgba(0, 0, 0, 0.45);
      backdrop-filter: blur(2px);
    }

    .dlg-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 16px 8px 12px 20px;
      border-bottom: 1px solid var(--divider-color);
      flex-shrink: 0;
    }
    .dlg-subject {
      font-size: 1.1em;
      font-weight: 600;
    }
    .dlg-category {
      font-size: 0.82em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }

    .dlg-body {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .dlg-grade-large {
      font-size: 2.8em;
      font-weight: 700;
      text-align: center;
      padding: 12px;
      border-radius: 8px;
      color: #fff;
      background: var(--badge-bg, var(--secondary-text-color, #888));
      flex-shrink: 0;
    }

    .dlg-details {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .dlg-detail-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      font-size: 0.9em;
    }
    .dlg-description {
      align-items: flex-start;
    }
    .dlg-description span:last-child {
      text-align: right;
      flex-shrink: 1;
    }
    .dlg-detail-label {
      color: var(--secondary-text-color);
      white-space: nowrap;
      flex-shrink: 0;
    }

  `;
}

(window as Window & { customCards?: unknown[] }).customCards ??= [];
(window as Window & { customCards?: unknown[] }).customCards!.push({
  type: "librus-grades-card",
  name: "Librus — Oceny",
  description: "Chronologiczna lista ocen z kolorowym badgem typu, tooltipem i popupem ze szczegółami.",
});

declare global {
  interface HTMLElementTagNameMap {
    "librus-grades-card": LibrusGradesCard;
  }
}
