import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { sanitizeHtml } from "./sanitize.js";
import type { HassMessage, HomeAssistant, LibrusCardConfig } from "./types.js";

@customElement("librus-messages-card")
export class LibrusMessagesCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @state() private _config?: LibrusCardConfig;
  @state() private _expandedHref: string | null = null;
  @state() private _content: Record<string, string> | null = null;
  @state() private _loading = false;
  @state() private _onlyUnread = false;

  static getStubConfig() {
    return { entity: "", entry_id: "" };
  }

  setConfig(config: LibrusCardConfig) {
    if (!config.entity) throw new Error("entity is required");
    if (!config.entry_id) throw new Error("entry_id is required");
    this._config = config;
  }

  getCardSize() {
    return 4;
  }

  private get _messages(): HassMessage[] {
    if (!this.hass || !this._config) return [];
    const state = this.hass.states[this._config.entity];
    if (!state) return [];
    const msgs = (state.attributes["messages"] as HassMessage[]) ?? [];
    if (this._onlyUnread || this._config.only_unread) {
      return msgs.filter((m) => m.unread && !m.notification_dismissed);
    }
    return msgs;
  }

  private async _showContent(msg: HassMessage) {
    if (!this.hass || !this._config) return;
    this._expandedHref = msg.href;
    this._content = null;
    this._loading = true;
    try {
      const result = await this.hass.callService(
        "librus_apix",
        "fetch_message_content",
        { entry: this._config.entry_id, message_href: msg.href },
        undefined,
        true,
        true,
      );
      const r = result as { response?: Record<string, string> } | Record<string, string>;
      this._content = (r as { response?: Record<string, string> }).response ?? r as Record<string, string>;
    } catch {
      this._content = { content: "<em>Błąd pobierania treści.</em>" };
    } finally {
      this._loading = false;
    }
  }

  private async _markRead(msg: HassMessage) {
    if (!this.hass || !this._config) return;
    await this.hass.callService("librus_apix", "dismiss_message_notification", {
      entry: this._config.entry_id,
      message_href: msg.href,
    });
  }

  private _closeContent() {
    this._expandedHref = null;
    this._content = null;
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
      overflow: hidden;
    }
    .message-item.unread {
      background: color-mix(in srgb, var(--primary-color) 12%, transparent);
    }
    .message-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 10px 12px 6px;
      gap: 8px;
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
    }
    .message-actions {
      display: flex;
      gap: 4px;
      flex-shrink: 0;
    }
    ha-icon-button {
      --mdc-icon-button-size: 32px;
    }
    .message-content {
      padding: 8px 12px 10px;
      font-size: 0.9rem;
      border-top: 1px solid var(--divider-color);
      line-height: 1.5;
    }
    .loading {
      text-align: center;
      padding: 8px;
      color: var(--secondary-text-color);
    }
    .empty {
      text-align: center;
      padding: 16px;
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }
  `;

  render() {
    if (!this._config) return nothing;
    const messages = this._messages;
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
          ${messages.length === 0
            ? html`<div class="empty">${filterActive ? "Brak nieprzeczytanych wiadomości" : "Brak wiadomości"}</div>`
            : messages.map((msg) => this._renderMessage(msg))}
        </div>
      </ha-card>
    `;
  }

  private _renderMessage(msg: HassMessage) {
    const isExpanded = this._expandedHref === msg.href;
    return html`
      <div class="message-item ${msg.unread && !msg.notification_dismissed ? "unread" : ""}">
        <div class="message-header">
          <div class="message-meta">
            <div class="message-sender">${msg.sender}</div>
            <div class="message-title">
              ${msg.has_attachment ? html`<ha-icon icon="mdi:paperclip" class="attach-icon"></ha-icon>` : nothing}
              ${msg.title}
            </div>
          </div>
          <span class="message-date">${msg.date}</span>
          <div class="message-actions">
            <ha-icon-button
              .label=${"Pokaż treść"}
              .path=${"M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"}
              @click=${() => isExpanded ? this._closeContent() : this._showContent(msg)}
            ></ha-icon-button>
            ${!msg.notification_dismissed
              ? html`
                <ha-icon-button
                  .label=${"Odrzuć powiadomienie"}
                  .path=${"M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"}
                  @click=${() => this._markRead(msg)}
                ></ha-icon-button>
              `
              : nothing}
          </div>
        </div>
        ${isExpanded
          ? html`
            <div class="message-content">
              ${this._loading
                ? html`<div class="loading">Ładowanie…</div>`
                : this._content
                  ? unsafeHTML(sanitizeHtml(this._content["content"] ?? ""))
                  : nothing}
            </div>
          `
          : nothing}
      </div>
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
