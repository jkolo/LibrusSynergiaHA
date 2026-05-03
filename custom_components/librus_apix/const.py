"""Constants for the Librus APIX integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "librus_apix"
DEFAULT_NAME = "Librus"

# Update intervals
SCAN_INTERVAL = timedelta(hours=2)

# Default values
DEFAULT_MESSAGES_COUNT = 10
