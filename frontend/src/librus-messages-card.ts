import { LitElement, html, css, nothing } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { sanitizeHtml } from "./sanitize.js";
import type { HassMessage, HomeAssistant, LibrusCardConfig, MessageListResponse } from "./types.js";

// Stała wysokość wiersza — musi zgadzać się z CSS .message-item { height: 52px }
const ROW_HEIGHT = 52;
// Dodatkowe wiersze renderowane powyżej i poniżej widocznego okna
const BUFFER = 4;

type DialogContent = { author: string; title: string; date: string; content: string };

@customElement("librus-messages-card")
export class LibrusMessagesCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @state() private _config?: LibrusCardConfig;
  @state() private _onlyUnread = false;

  // Virtual scroll state
  @state() private _allMessages: (HassMessage | null)[] = [];
  @state() private _totalCount = 0;
  @state() private _scrollTop = 0;
  private _fetchingOffsets = new Set<number>();
  private _scrollRaf?: number;

  // Popup state
  @state() private _selectedMsg: HassMessage | null = null;
  @state() private _dialogContent: DialogContent | null = null;
  @state() private _dialogLoading = false;
  @query("dialog") private _dialog?: HTMLDialogElement;

  static getStubConfig() {
    return { entity: "", entry_id: "", count: 10 };
  }

  setConfig(config: LibrusCardConfig) {
    if (!config.entity) throw new Error("entity is required");
    if (!config.entry_id) throw new Error("entry_id is required");
    this._config = config;
  }

  getCardSize() {
    return 4;
  }

  firstUpdated() {
    // Pierwszy fetch: poznajemy total_count i ładujemy pierwsze wiersze.
    void this._fetchAt(0);
  }

  updated(changedProps: Map<string, unknown>) {
    super.updated(changedProps);
    // Gdy filtr właśnie się włączył — ładuj wszystkie strony, żeby filtrowanie
    // pokazywało kompletny zbiór nieprzeczytanych.
    if (changedProps.has("_onlyUnread") && this._onlyUnread && this._totalCount > 0) {
      this._fetchAll();
    }
  }

  private get _listHeight() {
    return (this._config?.count ?? 10) * ROW_HEIGHT;
  }

  private get _visibleRows() {
    return Math.ceil(this._listHeight / ROW_HEIGHT);
  }

  private get _filterActive() {
    return this._onlyUnread || Boolean(this._config?.only_unread);
  }

  // ---------------------------------------------------------------------------
  // Data loading
  // ---------------------------------------------------------------------------

  private async _fetchAt(offset: number) {
    if (this._fetchingOffsets.has(offset) || !this.hass || !this._config) return;
    if (this._totalCount > 0 && offset >= this._totalCount) return;
    this._fetchingOffsets.add(offset);
    const count = this._config.count ?? 10;
    try {
      const result = await this.hass.callService(
        "librus_apix",
        "list_messages",
        { entry: this._config.entry_id, offset, count },
        undefined,
        false,
        true,
      );
      const data = (
        (result as { response?: MessageListResponse })?.response ?? result
      ) as MessageListResponse;
      const newMsgs: HassMessage[] = data.messages ?? [];
      const total: number = data.total_count ?? (newMsgs.length + offset);

      // Resize array when total changes
      if (total !== this._totalCount || this._allMessages.length !== total) {
        const arr = new Array<HassMessage | null>(total).fill(null);
        this._allMessages.forEach((m, i) => {
          if (m) arr[i] = m;
        });
        this._allMessages = arr;
        this._totalCount = total;
        // Jeśli filtr aktywny i właśnie poznaliśmy total — załaduj resztę
        if (this._filterActive) this._fetchAll();
      }

      // Wstaw załadowane wiersze
      const arr = [...this._allMessages];
      newMsgs.forEach((msg, i) => {
        if (offset + i < arr.length) arr[offset + i] = msg;
      });
      this._allMessages = arr;
    } finally {
      this._fetchingOffsets.delete(offset);
    }
  }

  private _fetchAll() {
    if (!this._config) return;
    const count = this._config.count ?? 10;
    for (let offset = 0; offset < this._totalCount; offset += count) {
      if (this._fetchingOffsets.has(offset)) continue;
      const sliceEnd = Math.min(offset + count, this._totalCount);
      const hasNulls = this._allMessages.slice(offset, sliceEnd).some((m) => m === null);
      if (hasNulls) void this._fetchAt(offset);
    }
  }

  private _ensureLoaded(startIdx: number, endIdx: number) {
    const count = this._config?.count ?? 10;
    const pageStart = Math.floor(startIdx / count);
    const pageEnd = Math.floor(Math.max(0, endIdx - 1) / count);
    for (let page = pageStart; page <= pageEnd; page++) {
      const offset = page * count;
      if (offset >= this._totalCount) break;
      if (this._fetchingOffsets.has(offset)) continue;
      const sliceEnd = Math.min(offset + count, this._totalCount);
      const hasNulls = this._allMessages.slice(offset, sliceEnd).some((m) => m === null);
      if (hasNulls) void this._fetchAt(offset);
    }
  }

  private _onScroll(e: Event) {
    const scrollTop = (e.target as HTMLElement).scrollTop;
    if (this._scrollRaf) cancelAnimationFrame(this._scrollRaf);
    this._scrollRaf = requestAnimationFrame(() => {
      this._scrollTop = scrollTop;
      const startIdx = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - BUFFER);
      const endIdx = Math.min(
        this._totalCount,
        startIdx + this._visibleRows + BUFFER * 2,
      );
      this._ensureLoaded(startIdx, endIdx);
    });
  }

  // ---------------------------------------------------------------------------
  // Dialog
  // ---------------------------------------------------------------------------

  private async _openDialog(msg: HassMessage) {
    if (!this.hass || !this._config) return;
    this._selectedMsg = msg;
    this._dialogContent = null;
    this._dialogLoading = true;
    this._dialog?.showModal();
    try {
      const result = await this.hass.callService(
        "librus_apix",
        "fetch_message_content",
        { entry: this._config.entry_id, message_href: msg.href },
        undefined,
        true,
        true,
      );
      const data = (
        (result as { response?: DialogContent })?.response ?? result
      ) as DialogContent;
      this._dialogContent = data;
    } catch {
      this._dialogContent = {
        author: "",
        title: "",
        date: "",
        content: "<em>Błąd pobierania treści.</em>",
      };
    } finally {
      this._dialogLoading = false;
    }
  }

  private async _dismissFromDialog() {
    if (!this.hass || !this._config || !this._selectedMsg) return;
    const href = this._selectedMsg.href;
    await this.hass.callService("librus_apix", "dismiss_message_notification", {
      entry: this._config.entry_id,
      message_href: href,
    });
    // Zaktualizuj lokalnie bez czekania na refresh coordinatora
    this._allMessages = this._allMessages.map((m) =>
      m?.href === href ? { ...m, notification_dismissed: true } : m,
    );
    this._dialog?.close();
  }

  // ---------------------------------------------------------------------------
  // Styles
  // ---------------------------------------------------------------------------

  static styles = css`
    :host {
      display: block;
    }
    ha-card {
      padding: 0;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px 8px;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 500;
    }
    .filter-toggle {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
      cursor: pointer;
    }

    /* Lista — stała wysokość, wewnętrzny scroll */
    .message-list {
      overflow-y: auto;
      overflow-x: hidden;
      scrollbar-width: thin;
      scrollbar-color: var(--scrollbar-thumb-color, var(--divider-color)) transparent;
    }

    /* Wirtualna przestrzeń — wysokość = total_count * ROW_HEIGHT, scroll tu */
    .virtual-spacer {
      position: relative;
    }

    /* Okno renderowanych wierszy — absolutnie pozycjonowane wewnątrz spacera */
    .virtual-window {
      position: absolute;
      left: 0;
      right: 0;
    }

    /* KLUCZOWE: każdy wiersz ma ściśle 52px — musi zgadzać się z ROW_HEIGHT w TS */
    .message-item {
      height: 52px;
      box-sizing: border-box;
      padding: 0 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      border-radius: 6px;
      transition: background 0.12s;
      overflow: hidden;
    }
    .message-item:hover {
      background: color-mix(in srgb, var(--primary-color) 6%, transparent);
    }
    .message-item.unread {
      background: color-mix(in srgb, var(--primary-color) 12%, transparent);
    }
    .message-item.unread:hover {
      background: color-mix(in srgb, var(--primary-color) 18%, transparent);
    }
    .message-meta {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 2px;
    }
    .message-sender {
      font-weight: 500;
      font-size: 0.88rem;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.2;
    }
    .message-title {
      font-size: 0.82rem;
      color: var(--secondary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.2;
    }
    .attach-icon {
      --mdi-icon-size: 13px;
      vertical-align: middle;
      color: var(--secondary-text-color);
      margin-right: 2px;
    }
    .message-date {
      font-size: 0.72rem;
      color: var(--disabled-text-color);
      white-space: nowrap;
      flex-shrink: 0;
    }

    /* Szkielet dla niezaładowanych wierszy */
    .message-item.skeleton {
      cursor: default;
      pointer-events: none;
    }
    .skel {
      border-radius: 4px;
      background: linear-gradient(
        90deg,
        color-mix(in srgb, var(--primary-text-color) 6%, transparent) 0%,
        color-mix(in srgb, var(--primary-text-color) 12%, transparent) 50%,
        color-mix(in srgb, var(--primary-text-color) 6%, transparent) 100%
      );
      background-size: 200% 100%;
      animation: shimmer 1.4s infinite;
    }
    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }
    .skel.sender { width: 55%; height: 11px; margin-bottom: 4px; }
    .skel.title  { width: 38%; height: 10px; }
    .skel.date   { width: 60px; height: 9px; }

    .empty {
      text-align: center;
      padding: 16px;
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }

    /* Dialog */
    dialog {
      max-width: min(700px, 95vw);
      max-height: 85vh;
      border: none;
      border-radius: var(--ha-card-border-radius, 12px);
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
      padding: 0;
      overflow: hidden;
    }
    dialog[open] {
      display: flex;
      flex-direction: column;
    }
    dialog::backdrop {
      background: rgba(0, 0, 0, 0.5);
      backdrop-filter: blur(2px);
    }
    .dlg-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 16px 8px 16px 20px;
      border-bottom: 1px solid var(--divider-color);
      flex-shrink: 0;
      gap: 8px;
    }
    .dlg-meta { flex: 1; min-width: 0; }
    .dlg-sender {
      font-weight: 500;
      font-size: 0.85em;
      color: var(--secondary-text-color);
    }
    .dlg-title {
      font-size: 1.05em;
      font-weight: 600;
      margin: 4px 0 2px;
      word-break: break-word;
    }
    .dlg-date { font-size: 0.8em; color: var(--secondary-text-color); }
    .dlg-body { flex: 1; overflow-y: auto; padding: 16px 20px; }
    .dlg-loading { text-align: center; padding: 24px; color: var(--secondary-text-color); }
    .dlg-content { line-height: 1.6; font-size: 0.95em; }
    .dlg-content p { margin: 0 0 0.8em; }
    .dlg-content a { color: var(--primary-color); }
    .dlg-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 20px;
      border-top: 1px solid var(--divider-color);
      flex-shrink: 0;
      gap: 8px;
      flex-wrap: wrap;
    }
    .attach-note {
      display: flex;
      align-items: center;
      gap: 4px;
      color: var(--secondary-text-color);
      font-size: 0.85em;
    }
    .dlg-footer-actions { display: flex; gap: 8px; margin-left: auto; }
    .btn-dismiss {
      background: var(--error-color);
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9em;
    }
    .btn-close {
      background: var(--secondary-background-color);
      color: var(--primary-text-color);
      border: 1px solid var(--divider-color);
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9em;
    }
    ha-icon-button {
      --mdc-icon-button-size: 32px;
      flex-shrink: 0;
    }
  `;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  render() {
    if (!this._config) return nothing;
    return this._filterActive ? this._renderFiltered() : this._renderVirtual();
  }

  private _renderHeader() {
    const title = this._config?.title ?? "Wiadomości Librus";
    return html`
      <div class="card-header">
        <span class="card-title">${title}</span>
        <label class="filter-toggle">
          <input
            type="checkbox"
            .checked=${this._onlyUnread}
            @change=${(e: Event) => {
              this._onlyUnread = (e.target as HTMLInputElement).checked;
            }}
          />
          tylko nieprzeczytane
        </label>
      </div>
    `;
  }

  // Tryb wirtualny — pełny virtual scroll dla niezafiltrowanej listy
  private _renderVirtual() {
    const startIdx = Math.max(0, Math.floor(this._scrollTop / ROW_HEIGHT) - BUFFER);
    const endIdx = Math.min(
      this._totalCount,
      startIdx + this._visibleRows + BUFFER * 2,
    );
    const windowTop = startIdx * ROW_HEIGHT;
    const spacerHeight = this._totalCount * ROW_HEIGHT;

    return html`
      <ha-card>
        ${this._renderHeader()}
        <div
          class="message-list"
          style="height: ${this._listHeight}px"
          @scroll=${this._onScroll}
        >
          <div class="virtual-spacer" style="height: ${spacerHeight}px">
            <div class="virtual-window" style="top: ${windowTop}px">
              ${Array.from({ length: endIdx - startIdx }, (_, i) => {
                const msg = this._allMessages[startIdx + i];
                return msg ? this._renderRow(msg) : this._renderSkeleton();
              })}
            </div>
          </div>
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }

  // Tryb filtrowany — flat lista, eager-loaded
  private _renderFiltered() {
    const loaded = this._allMessages.filter(
      (m): m is HassMessage => m !== null && m.unread && !m.notification_dismissed,
    );
    return html`
      <ha-card>
        ${this._renderHeader()}
        <div class="message-list" style="height: ${this._listHeight}px">
          ${loaded.length === 0
            ? html`<div class="empty">Brak nieprzeczytanych wiadomości</div>`
            : loaded.map((msg) => this._renderRow(msg))}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }

  private _renderRow(msg: HassMessage) {
    return html`
      <div
        class="message-item ${msg.unread && !msg.notification_dismissed ? "unread" : ""}"
        role="button"
        tabindex="0"
        @click=${() => this._openDialog(msg)}
        @keydown=${(e: KeyboardEvent) => e.key === "Enter" && this._openDialog(msg)}
      >
        <div class="message-meta">
          <div class="message-sender">${msg.sender}</div>
          <div class="message-title">
            ${msg.has_attachment
              ? html`<ha-icon icon="mdi:paperclip" class="attach-icon"></ha-icon>`
              : nothing}
            ${msg.title}
          </div>
        </div>
        <span class="message-date">${msg.date}</span>
      </div>
    `;
  }

  private _renderSkeleton() {
    return html`
      <div class="message-item skeleton">
        <div class="message-meta">
          <div class="skel sender"></div>
          <div class="skel title"></div>
        </div>
        <div class="skel date"></div>
      </div>
    `;
  }

  private _renderDialog() {
    const msg = this._selectedMsg;
    return html`
      <dialog
        @close=${() => {
          this._selectedMsg = null;
          this._dialogContent = null;
        }}
      >
        <div class="dlg-header">
          <div class="dlg-meta">
            <div class="dlg-sender">${msg?.sender}</div>
            <div class="dlg-title">${msg?.title}</div>
            <div class="dlg-date">${msg?.date}</div>
          </div>
          <ha-icon-button
            .label=${"Zamknij"}
            .path=${"M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"}
            @click=${() => this._dialog?.close()}
          ></ha-icon-button>
        </div>
        <div class="dlg-body">
          ${this._dialogLoading
            ? html`<div class="dlg-loading">Ładowanie…</div>`
            : this._dialogContent
              ? html`<div class="dlg-content">
                  ${unsafeHTML(sanitizeHtml(this._dialogContent.content))}
                </div>`
              : nothing}
        </div>
        <div class="dlg-footer">
          ${msg?.has_attachment
            ? html`<span class="attach-note">
                <ha-icon icon="mdi:paperclip"></ha-icon>
                Zawiera załącznik
              </span>`
            : nothing}
          <div class="dlg-footer-actions">
            ${msg && !msg.notification_dismissed
              ? html`<button class="btn-dismiss" @click=${() => this._dismissFromDialog()}>
                  Usuń powiadomienie
                </button>`
              : nothing}
            <button class="btn-close" @click=${() => this._dialog?.close()}>
              Zamknij
            </button>
          </div>
        </div>
      </dialog>
    `;
  }
}

(window as Window & { customCards?: unknown[] }).customCards ??= [];
(window as Window & { customCards?: unknown[] }).customCards!.push({
  type: "librus-messages-card",
  name: "Librus — Wiadomości",
  description: "Wiadomości szkolne z podglądem treści i zarządzaniem powiadomieniami.",
});

declare global {
  interface HTMLElementTagNameMap {
    "librus-messages-card": LibrusMessagesCard;
  }
}
