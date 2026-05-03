"""Pytest fixtures for the Librus APIX integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.librus_apix.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in /tests/custom_components."""
    yield


@pytest.fixture(autouse=True)
def no_human_pauses():
    """Cut human-like pauses to ~0 s for fast tests.

    With the human-like sync feature each refresh inserts 3–15 s of pause
    between endpoint fetches. Tests would block for ~30–60 s; we patch
    `jitter_pause_seconds` in the coordinator module to return 0.0 so
    `asyncio.sleep(0)` is a real no-op (yields once, doesn't disrupt
    event loop scheduling like an AsyncMock would).
    """
    # Unique sentinel value lets tests filter for "our" pauses among any
    # other asyncio.sleep calls in the runtime.
    with patch(
        "custom_components.librus_apix.coordinator.jitter_pause_seconds",
        return_value=0.0001,
    ):
        yield


@pytest.fixture
def mock_student_info():
    """Return a fake student_information object."""
    info = MagicMock()
    info.name = "Jan Kowalski"
    info.class_name = "5A"
    info.number = "12"
    info.tutor = "Anna Nowak"
    info.school = "SP 1"
    info.lucky_number = 7
    return info


@pytest.fixture
def mock_librus_client(mock_student_info) -> Generator[MagicMock, None, None]:
    """Return a patched LibrusApiClient with happy-path returns."""
    with patch(
        "custom_components.librus_apix.LibrusApiClient", autospec=True
    ) as client_cls:
        instance = client_cls.return_value
        instance.username = "test_user"
        instance.async_authenticate = AsyncMock(return_value=True)
        instance.async_get_student_information = AsyncMock(return_value=mock_student_info)
        instance.async_get_grades = AsyncMock(return_value=[
            {
                "subject": "Matematyka",
                "grade": "5",
                "date": "2025-09-15",
                "category": "Sprawdzian",
                "teacher": "Anna Nowak",
                "semester": 1,
                "type": "numeric",
            },
        ])
        instance.async_get_messages = AsyncMock(return_value=[])
        instance.async_get_schedule_events = AsyncMock(return_value=[])
        instance.async_get_timetable_events = AsyncMock(return_value=[])
        instance.async_get_attendance = AsyncMock(return_value=[])
        instance.async_get_announcements = AsyncMock(return_value=[])
        yield instance


@pytest.fixture
def mock_config_entry():
    """Return a MockConfigEntry for the integration."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain=DOMAIN,
        title="Librus APIX (test_user)",
        data={"username": "test_user", "password": "test_password"},
        unique_id="test_user",
    )
