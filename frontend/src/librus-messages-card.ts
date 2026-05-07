import { LitElement, html, css, nothing } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { sanitizeHtml } from "./sanitize.js";
import type { HassMessage, HomeAssistant, LibrusCardConfig, MessageListResponse } from "./types.js";

type DialogContent = { author: string; title: string; date: string; content: string };

@customElement("librus-messages-card")
export class LibrusMessagesCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @state() private _config?: LibrusCardConfig;
  @state() private _onlyUnread = false;

  // Popup state
  @state() private _selectedMsg: HassMessage | null = null;
  @state() private _dialogContent: DialogContent | null = null;
  @state() private _dialogLoading = false;
  @query("dialog") private _dialog?: HTMLDialogElement;

  // Infinity scroll state
  @state() private _loadedMessages: HassMessage[] = [];
  @state() private _hasMore = true;
  @state() private _isLoadingMore = false;
  private _observer?: IntersectionObserver;
  private _sentinelEl?: Element;

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

  connectedCallback() {
    super.connectedCallback();
    this._observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !this._isLoadingMore && this._hasMore) {
          void this._loadMore();
        }
      },
      { rootMargin: "120px" },
    );
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._observer?.disconnect();
    this._observer = undefined;
    this._sentinelEl = undefined;
  }

  updated(changedProps: Map<string, unknown>) {
    super.updated(changedProps);

    if (changedProps.has("hass") && this._loadedMessages.length === 0) {
      const initial = this._messagesFromSensor;
      if (initial.length > 0) {
        this._loadedMessages = [...initial];
        this._hasMore = initial.length >= (this._config?.count ?? 10);
      }
    }

    const sentinel = this.shadowRoot?.querySelector(".sentinel");
    if (sentinel && sentinel !== this._sentinelEl) {
      if (this._sentinelEl) this._observer?.unobserve(this._sentinelEl);
      this._sentinelEl = sentinel;
      this._observer?.observe(sentinel);
    }
  }

  private get _messagesFromSensor(): HassMessage[] {
    if (!this.hass || !this._config) return [];
    const state = this.hass.states[this._config.entity];
    if (!state) return [];
    return (state.attributes["messages"] as HassMessage[]) ?? [];
  }

  private get _displayedMessages(): HassMessage[] {
    if (this._onlyUnread || this._config?.only_unread) {
      return this._loadedMessages.filter((m) => m.unread && !m.notification_dismissed);
    }
    return this._loadedMessages;
  }

  private async _loadMore() {
    if (!this.hass || !this._config || this._isLoadingMore) return;
    this._isLoadingMore = true;
    const count = this._config.count ?? 10;
    const offset = this._loadedMessages.length;
    try {
      const result = await this.hass.callService(
        "librus_apix",
        "list_messages",
        { entry: this._config.entry_id, offset, count },
        undefined,
        false,
        true,
      );
      const data = ((result as { response?: MessageListResponse })?.response ??
        result) as MessageListResponse;
      const newMsgs = data.messages ?? [];
      this._hasMore = data.has_more === true;
      const existing = new Set(this._loadedMessages.map((m) => m.href));
      const unique = newMsgs.filter((m) => !existing.has(m.href));
      this._loadedMessages = [...this._loadedMessages, ...unique];
    } catch {
      // Nie zerujemy _hasMore przy transientem błędzie (np. restart HA) —
      // IntersectionObserver odpali ponownie przy następnym scrollu.
    } finally {
      this._isLoadingMore = false;
    }
  }

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
      const data = ((result as { response?: DialogContent })?.response ??
        result) as DialogContent;
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
    // Update local copy immediately so filter reflects the dismiss without reload
    this._loadedMessages = this._loadedMessages.map((m) =>
      m.href === href ? { ...m, notification_dismissed: true } : m,
    );
    this._dialog?.close();
  }

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
    .message-list {
      padding: 0 8px 8px;
    }
    .message-item {
      border-radius: 8px;
      margin-bottom: 4px;
      padding: 10px 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 8px;
      cursor: pointer;
      transition: background 0.15s;
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
    }
    .message-sender {
      font-weight: 500;
      font-size: 0.9rem;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .message-title {
      font-size: 0.85rem;
      color: var(--secondary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .attach-icon {
      --mdi-icon-size: 14px;
      vertical-align: middle;
      color: var(--secondary-text-color);
      margin-right: 2px;
    }
    .message-date {
      font-size: 0.75rem;
      color: var(--disabled-text-color);
      white-space: nowrap;
      flex-shrink: 0;
    }
    .sentinel {
      height: 1px;
    }
    .loading-more {
      text-align: center;
      padding: 8px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
    }
    .empty {
      text-align: center;
      padding: 16px;
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }

    /* Dialog — display controlled by browser via [open] attribute */
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
    .dlg-meta {
      flex: 1;
      min-width: 0;
    }
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
    .dlg-date {
      font-size: 0.8em;
      color: var(--secondary-text-color);
    }
    .dlg-body {
      flex: 1;
      overflow-y: auto;
      padding: 16px 20px;
    }
    .dlg-loading {
      text-align: center;
      padding: 24px;
      color: var(--secondary-text-color);
    }
    .dlg-content {
      line-height: 1.6;
      font-size: 0.95em;
    }
    .dlg-content p {
      margin: 0 0 0.8em;
    }
    .dlg-content a {
      color: var(--primary-color);
    }
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
    .dlg-footer-actions {
      display: flex;
      gap: 8px;
      margin-left: auto;
    }
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

  render() {
    if (!this._config) return nothing;
    const msgs = this._displayedMessages;
    const title = this._config.title ?? "Wiadomości Librus";
    const filterActive = this._onlyUnread || this._config.only_unread;

    return html`
      <ha-card>
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
        <div class="message-list">
          ${msgs.length === 0 && !this._isLoadingMore
            ? html`<div class="empty">
                ${filterActive ? "Brak nieprzeczytanych wiadomości" : "Brak wiadomości"}
              </div>`
            : msgs.map((msg) => this._renderRow(msg))}
          ${this._hasMore ? html`<div class="sentinel"></div>` : nothing}
          ${this._isLoadingMore
            ? html`<div class="loading-more">Ładowanie…</div>`
            : nothing}
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
            <button class="btn-close" @click=${() => this._dialog?.close()}>Zamknij</button>
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
