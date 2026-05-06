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
}

export interface HomeAssistant {
  states: Record<string, HassState>;
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
