import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HassGrade, HassGradeRef, HomeAssistant } from "./types.js";
import { formatDate, parseDateForSort } from "./grade-format.js";
import { collapseCorrections, correctionNote, supersededNote } from "./grade-corrections.js";
import type { GradeEntry } from "./grade-corrections.js";

interface LibrusSubjectGradesCardConfig {
  type: string;
  entity: string;
  title?: string;
}

function gradeTypeInfo(category: string): { cssClass: string } {
  const cat = category.toLowerCase();
  if (cat.includes("sprawdzian") || cat.includes("test"))
    return { cssClass: "type-test" };
  if (cat.includes("kartkówka") || cat.includes("kartkowka"))
    return { cssClass: "type-quiz" };
  if (cat.includes("praca klasow") || cat.includes("praca kontrolna"))
    return { cssClass: "type-classwork" };
  if (cat.includes("praca domow"))
    return { cssClass: "type-homework" };
  if (cat.includes("wypracowanie"))
    return { cssClass: "type-essay" };
  return { cssClass: "type-other" };
}

@customElement("librus-subject-grades-card")
export class LibrusSubjectGradesCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @state() private _config?: LibrusSubjectGradesCardConfig;
  @state() private _selectedGrade: HassGrade | null = null;
  @state() private _dlgOpen = false;

  static getStubConfig(): LibrusSubjectGradesCardConfig {
    return { type: "librus-subject-grades-card", entity: "" };
  }

  setConfig(config: LibrusSubjectGradesCardConfig): void {
    if (!config.entity) throw new Error("entity jest wymagany");
    this._config = config;
  }

  getCardSize(): number {
    return 2;
  }

  private get _grades(): HassGrade[] {
    if (!this.hass || !this._config) return [];
    const state = this.hass.states[this._config.entity];
    const details = state?.attributes?.grade_details as HassGrade[] | undefined;
    if (!details) return [];
    return [...details].sort(
      (a, b) => parseDateForSort(a.date) - parseDateForSort(b.date)
    );
  }

  private _openDialog(grade: HassGrade): void {
    this._selectedGrade = grade;
    this._dlgOpen = true;
  }

  private _closeDialog(): void {
    this._dlgOpen = false;
    this._selectedGrade = null;
  }

  private _describeRef(ref: HassGradeRef): string {
    const grade = [ref.grade, ref.category ? `(${ref.category})` : ""].filter(Boolean).join(" ");
    return [grade || "—", ref.date ? formatDate(ref.date) : ""].filter(Boolean).join(" · ");
  }

  private _renderChip(g: HassGrade) {
    const note = correctionNote(g) ?? supersededNote(g);
    const title = `${g.category}${g.date ? " · " + formatDate(g.date) : ""}${note ? " — " + note : ""}`;
    return html`<span
      class="grade-chip ${gradeTypeInfo(g.category).cssClass} ${g.is_recent ? "recent" : ""} ${g.corrected_by ? "superseded" : ""}"
      role="button"
      tabindex="0"
      title="${title}"
      @click="${() => this._openDialog(g)}"
      @keydown="${(e: KeyboardEvent) => e.key === "Enter" && this._openDialog(g)}"
    >${g.grade}</span>`;
  }

  /** A grade, preceded by what it replaced: `1 → 6` (or `1 → 3 → 5` for a chain). */
  private _renderEntry(entry: GradeEntry) {
    const { grade, replaced } = entry;
    // The original may be unknown while Librus still names the replaced grade.
    const unknownFrom = replaced.length === 0 ? grade.correction_of?.grade : null;
    if (replaced.length === 0 && !unknownFrom) return this._renderChip(grade);
    return html`<span class="chain" aria-label="${correctionNote(grade) ?? ""}">
      ${replaced.map(
        r => html`${this._renderChip(r)}<span class="arrow" aria-hidden="true">→</span>`
      )}
      ${unknownFrom
        ? html`<span class="grade-from" title="${correctionNote(grade) ?? ""}">${unknownFrom}</span><span class="arrow" aria-hidden="true">→</span>`
        : nothing}
      ${this._renderChip(grade)}
    </span>`;
  }

  private _renderDialog() {
    const g = this._selectedGrade;
    return html`
      <ha-dialog .open=${this._dlgOpen} @closed=${() => this._closeDialog()}>
        ${g
          ? html`
              <div class="dlg-title">${g.subject || g.category}</div>
              <div class="dlg-category-row">
                ${g.category}${g.category && g.date ? " · " : ""}${formatDate(g.date)}
              </div>
              <div class="dlg-grade-large ${gradeTypeInfo(g.category).cssClass}">
                ${g.correction_of?.grade
                  ? html`<span class="dlg-from">${g.correction_of.grade}</span><span class="dlg-arrow" aria-hidden="true">→</span>`
                  : nothing}
                <span class="${g.corrected_by ? "grade-struck" : ""}">${g.grade}</span>
              </div>
              <div class="dlg-details">
                ${g.teacher
                  ? html`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Nauczyciel</span>
                      <span>${g.teacher}</span>
                    </div>`
                  : nothing}
                ${g.weight != null
                  ? html`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Waga</span>
                      <span>${g.weight}</span>
                    </div>`
                  : nothing}
                <div class="dlg-detail-row">
                  <span class="dlg-detail-label">Liczy do średniej</span>
                  <span>${g.counts ? "Tak" : "Nie"}</span>
                </div>
                ${g.title
                  ? html`<div class="dlg-detail-row dlg-detail-row--block">
                      <span class="dlg-detail-label">Temat</span>
                      <span class="dlg-detail-text">${g.title}</span>
                    </div>`
                  : nothing}
                ${g.correction_of
                  ? html`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Poprawa oceny</span>
                      <span>${this._describeRef(g.correction_of)}</span>
                    </div>`
                  : nothing}
                ${g.corrected_by
                  ? html`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Poprawiona oceną</span>
                      <span>${this._describeRef(g.corrected_by)}</span>
                    </div>`
                  : nothing}
                ${!g.correction_of && g.description
                  ? html`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Poprawa</span>
                      <span>${g.description}</span>
                    </div>`
                  : nothing}
                ${g.comment
                  ? html`<div class="dlg-detail-row dlg-detail-row--block">
                      <span class="dlg-detail-label">Komentarz</span>
                      <span class="dlg-detail-text">${g.comment}</span>
                    </div>`
                  : nothing}
              </div>
            `
          : nothing}
      </ha-dialog>
    `;
  }

  render() {
    if (!this._config) return nothing;
    const grades = this._grades;
    const state = this.hass?.states[this._config.entity];
    const subject =
      this._config.title ??
      (state?.attributes?.subject as string | undefined) ??
      this._config.entity;
    const newCount = grades.filter(g => g.is_recent).length;

    return html`
      <ha-card>
        <div class="card-header">
          <span class="card-title">${subject}</span>
          ${newCount > 0
            ? html`<span class="new-badge">${newCount} nowe</span>`
            : nothing}
        </div>
        <div class="grades-line">
          ${grades.length === 0
            ? html`<span class="empty">Brak ocen</span>`
            : collapseCorrections(grades).map(
                (entry, i) => html`
                  ${i > 0 ? html`<span class="sep">,</span>` : nothing}
                  ${this._renderEntry(entry)}
                `
              )}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }

  static styles = css`
    :host { display: block; }

    ha-card {
      padding: 0;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px 6px;
    }
    .card-title {
      font-size: 1em;
      font-weight: 500;
      color: var(--primary-text-color);
    }
    .new-badge {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-radius: 10px;
      padding: 1px 7px;
      font-size: 0.78em;
    }

    .grades-line {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 2px;
      padding: 6px 16px 14px;
    }

    .sep {
      color: var(--secondary-text-color);
      font-size: 0.9em;
      line-height: 1;
      user-select: none;
    }

    .grade-chip {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 0.9em;
      font-weight: 600;
      color: #fff;
      background: var(--chip-bg, var(--secondary-text-color, #888));
      cursor: pointer;
      transition: filter 0.12s;
      line-height: 1.3;
      outline: none;
    }
    .grade-chip:hover { filter: brightness(1.15); }
    .grade-chip:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    .grade-chip.recent {
      box-shadow: 0 0 0 2px var(--primary-color);
    }
    .grade-chip.superseded {
      opacity: 0.55;
      text-decoration: line-through;
    }

    .chain {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 1px 6px 1px 3px;
      border: 1px dashed var(--divider-color, #bbb);
      border-radius: 14px;
    }
    .arrow {
      color: var(--secondary-text-color);
      font-size: 0.9em;
      line-height: 1;
      user-select: none;
    }
    .grade-from {
      padding: 3px 4px;
      font-size: 0.9em;
      font-weight: 600;
      color: var(--secondary-text-color);
      text-decoration: line-through;
    }
    .grade-struck { text-decoration: line-through; }

    .type-test      { --chip-bg: var(--error-color, #f44336); }
    .type-quiz      { --chip-bg: #ff9800; }
    .type-classwork { --chip-bg: var(--info-color, #2196f3); }
    .type-homework  { --chip-bg: #4caf50; }
    .type-essay     { --chip-bg: #9c27b0; }
    .type-other     { --chip-bg: var(--secondary-text-color, #888); }

    .empty {
      font-size: 0.85em;
      color: var(--secondary-text-color);
    }

    /* Popup */
    .dlg-title {
      font-size: 1.1em;
      font-weight: 600;
      color: var(--primary-text-color);
      margin-bottom: 2px;
    }
    .dlg-category-row {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-bottom: 16px;
    }
    .dlg-grade-large {
      font-size: 2.8em;
      font-weight: 700;
      text-align: center;
      padding: 12px;
      border-radius: 8px;
      color: #fff;
      background: var(--chip-bg, var(--secondary-text-color, #888));
      margin-bottom: 16px;
    }
    .dlg-from {
      text-decoration: line-through;
      opacity: 0.7;
      font-weight: 400;
    }
    .dlg-arrow { margin: 0 12px; font-weight: 400; }
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
    .dlg-detail-row--block { align-items: flex-start; }
    .dlg-detail-label {
      color: var(--secondary-text-color);
      white-space: nowrap;
      flex-shrink: 0;
    }
    .dlg-detail-text {
      text-align: right;
      word-break: break-word;
      white-space: pre-wrap;
      flex-shrink: 1;
    }
  `;
}

(window as Window & { customCards?: unknown[] }).customCards ??= [];
(window as Window & { customCards?: unknown[] }).customCards!.push({
  type: "librus-subject-grades-card",
  name: "Librus — Oceny przedmiotu",
  description: "Kompaktowa karta z ocenami jednego przedmiotu: kolorowe chipy po przecinku, popup ze szczegółami po kliknięciu.",
});

declare global {
  interface HTMLElementTagNameMap {
    "librus-subject-grades-card": LibrusSubjectGradesCard;
  }
}
