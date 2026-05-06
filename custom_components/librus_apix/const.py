"""Constants for the Librus APIX integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "librus_apix"
DEFAULT_NAME = "Librus"

# Update intervals
SCAN_INTERVAL = timedelta(hours=2)

# Default values
DEFAULT_MESSAGES_COUNT = 10

# Options keys (LibrusOptionsFlow). Stored on entry.options.
OPT_BASE_MINUTES = "base_minutes"
OPT_JITTER = "jitter"
OPT_QUIET_HOURS_ENABLED = "quiet_hours_enabled"
OPT_QUIET_START = "quiet_start"
OPT_QUIET_END = "quiet_end"
OPT_OFF_SCHOOL_MULTIPLIER = "off_school_multiplier"
OPT_HUMANIZE = "humanize"
OPT_ENABLED_SUBJECTS = "enabled_subjects"

# Defaults — also used by the coordinator when entry.options is empty.
DEFAULT_BASE_MINUTES = 120
DEFAULT_JITTER = 0.25
DEFAULT_QUIET_HOURS_ENABLED = False
DEFAULT_QUIET_START = "22:30"
DEFAULT_QUIET_END = "06:30"
DEFAULT_OFF_SCHOOL_MULTIPLIER = 6.0
DEFAULT_HUMANIZE = True

# Message notification opt-in
OPT_MESSAGE_NOTIFY = "message_notify"
DEFAULT_MESSAGE_NOTIFY = False

# Service names
SERVICE_DISMISS_MESSAGE_NOTIFICATION = "dismiss_message_notification"
SERVICE_RESTORE_MESSAGE_NOTIFICATION = "restore_message_notification"
SERVICE_CLEAR_DISMISSED_NOTIFICATIONS = "clear_dismissed_notifications"
SERVICE_FETCH_MESSAGE_CONTENT = "fetch_message_content"
SERVICE_LIST_MESSAGES = "list_messages"

# Bus events
EVENT_NOWA_WIADOMOSC = "librus_apix_nowa_wiadomosc"
