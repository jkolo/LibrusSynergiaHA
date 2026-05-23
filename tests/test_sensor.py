"""Tests for the new sensor value/attrs helper functions (PR 2)."""

from __future__ import annotations

import pytest

# These imports will fail until the corresponding helpers are implemented
# in custom_components/librus_apix/sensor.py — that's the RED state.
from custom_components.librus_apix.sensor import (
    _attrs_absences,
    _attrs_announcements,
    _attrs_frequency,
    _attrs_latest_absence,
    _attrs_latest_announcement,
    _attrs_latest_grade,
    _attrs_latest_message,
    _attrs_messages,
    _attrs_next_exam,
    _attrs_upcoming_exams,
    _val_absences_count,
    _val_announcements_count,
    _val_frequency,
    _val_latest_absence,
    _val_latest_announcement,
    _val_latest_grade,
    _val_latest_message,
    _val_next_exam,
    _val_unread_count,
)


# ---------------------------------------------------------------------------
# latest_grade
# ---------------------------------------------------------------------------


class TestValLatestGrade:
    def test_empty_grades_returns_none(self):
        assert _val_latest_grade({"grades": []}) is None

    def test_missing_grades_key_returns_none(self):
        assert _val_latest_grade({}) is None

    def test_returns_grade_with_latest_date_iso(self):
        data = {"grades": [
            {"subject": "Mat", "grade": "5", "date": "2026-04-12"},
            {"subject": "Pol", "grade": "3+", "date": "2026-04-15"},
            {"subject": "Hist", "grade": "4", "date": "2026-04-10"},
        ]}
        assert _val_latest_grade(data) == "3+"

    def test_returns_grade_with_latest_date_polish(self):
        # Librus zwraca daty czasem w formacie DD.MM.YYYY.
        data = {"grades": [
            {"subject": "Mat", "grade": "5", "date": "12.04.2026"},
            {"subject": "Pol", "grade": "3+", "date": "15.04.2026"},
        ]}
        assert _val_latest_grade(data) == "3+"


class TestAttrsLatestGrade:
    def test_empty_grades_returns_empty(self):
        assert _attrs_latest_grade({"grades": []}) == {}

    def test_attrs_contain_full_grade_context(self):
        data = {"grades": [
            {
                "subject": "Matematyka",
                "grade": "5",
                "value": 5.0,
                "counts": True,
                "weight": 3,
                "date": "2026-04-15",
                "category": "Sprawdzian",
                "description": "Świetna praca.",
                "title": "Funkcje kwadratowe",
                "teacher": "Anna Nowak",
                "semester": 2,
                "type": "numeric",
            },
        ]}
        attrs = _attrs_latest_grade(data)
        assert attrs["subject"] == "Matematyka"
        assert attrs["grade"] == "5"
        assert attrs["value"] == 5.0
        assert attrs["weight"] == 3
        assert attrs["counts"] is True
        assert attrs["date"] == "2026-04-15"
        assert attrs["category"] == "Sprawdzian"
        assert attrs["description"] == "Świetna praca."
        assert attrs["title"] == "Funkcje kwadratowe"
        assert attrs["teacher"] == "Anna Nowak"


# ---------------------------------------------------------------------------
# _attrs_messages / _val_unread_count
# ---------------------------------------------------------------------------

def _make_msg(i: int, *, unread: bool = False, dismissed: bool = False, attachment: bool = False, recent: bool = False) -> dict:
    return {
        "author": f"Nadawca {i}",
        "title": f"Temat {i}",
        "date": f"2026-04-{i:02d}",
        "href": f"href_{i}",
        "unread": unread,
        "notification_dismissed": dismissed,
        "has_attachment": attachment,
        "is_recent": recent,
    }


class TestAttrsMessages:
    def test_empty_messages(self):
        attrs = _attrs_messages({"messages": []})
        assert attrs["messages"] == []
        assert attrs["unread_count"] == 0
        assert attrs["undismissed_count"] == 0
        assert attrs["has_new_messages"] is False

    def test_returns_up_to_ten_messages(self):
        msgs = [_make_msg(i) for i in range(1, 12)]  # 11 wiadomości
        attrs = _attrs_messages({"messages": msgs})
        assert len(attrs["messages"]) == 10  # max 10, nie 5

    def test_fewer_than_ten_returns_all(self):
        msgs = [_make_msg(i) for i in range(1, 4)]  # 3 wiadomości
        attrs = _attrs_messages({"messages": msgs})
        assert len(attrs["messages"]) == 3

    def test_message_fields_mapped_correctly(self):
        msgs = [_make_msg(1, unread=True, attachment=True, recent=True, dismissed=False)]
        attrs = _attrs_messages({"messages": msgs})
        m = attrs["messages"][0]
        assert m["sender"] == "Nadawca 1"
        assert m["title"] == "Temat 1"
        assert m["date"] == "2026-04-01"
        assert m["href"] == "href_1"
        assert m["unread"] is True
        assert m["has_attachment"] is True
        assert m["is_recent"] is True
        assert m["notification_dismissed"] is False

    def test_unread_count(self):
        msgs = [_make_msg(i, unread=(i % 2 == 0)) for i in range(1, 7)]
        attrs = _attrs_messages({"messages": msgs})
        assert attrs["unread_count"] == 3  # i=2,4,6

    def test_undismissed_count(self):
        # unread=True, dismissed=False → liczy do undismissed
        # unread=True, dismissed=True → nie liczy
        msgs = [
            _make_msg(1, unread=True, dismissed=False),
            _make_msg(2, unread=True, dismissed=True),
            _make_msg(3, unread=False, dismissed=False),
        ]
        attrs = _attrs_messages({"messages": msgs})
        assert attrs["undismissed_count"] == 1

    def test_has_new_messages_true_when_recent(self):
        msgs = [_make_msg(1, recent=True), _make_msg(2)]
        attrs = _attrs_messages({"messages": msgs})
        assert attrs["has_new_messages"] is True

    def test_has_new_messages_false_when_none_recent(self):
        msgs = [_make_msg(1), _make_msg(2)]
        attrs = _attrs_messages({"messages": msgs})
        assert attrs["has_new_messages"] is False


class TestValUnreadCount:
    def test_empty(self):
        assert _val_unread_count({"messages": []}) == 0

    def test_counts_only_unread(self):
        msgs = [_make_msg(i, unread=(i <= 3)) for i in range(1, 6)]
        assert _val_unread_count({"messages": msgs}) == 3


# ---------------------------------------------------------------------------
# latest_message
# ---------------------------------------------------------------------------


class TestValLatestMessage:
    def test_empty_returns_none(self):
        assert _val_latest_message({"messages": []}) is None

    def test_returns_sender_of_first_message(self):
        # Coordinator sortuje messages najnowsze → najstarsze; pierwszy jest
        # tym najnowszym.
        data = {"messages": [
            {"author": "Anna Nowak", "title": "Wycieczka", "date": "2026-04-15",
             "unread": True, "has_attachment": False},
            {"author": "Marek", "title": "Konsultacje", "date": "2026-04-10",
             "unread": False, "has_attachment": False},
        ]}
        assert _val_latest_message(data) == "Anna Nowak"


class TestAttrsLatestMessage:
    def test_empty_returns_empty(self):
        assert _attrs_latest_message({"messages": []}) == {}

    def test_attrs_carry_full_message_context(self):
        data = {"messages": [
            {"author": "Anna", "title": "Wycieczka", "date": "2026-04-15",
             "unread": True, "has_attachment": True, "is_recent": True},
        ]}
        attrs = _attrs_latest_message(data)
        assert attrs["sender"] == "Anna"
        assert attrs["title"] == "Wycieczka"
        assert attrs["date"] == "2026-04-15"
        assert attrs["unread"] is True
        assert attrs["has_attachment"] is True
        assert attrs["is_recent"] is True


# ---------------------------------------------------------------------------
# next_exam (state = days_until) + upcoming_exams cleanup
# ---------------------------------------------------------------------------


class TestValNextExam:
    def test_empty_returns_none(self):
        assert _val_next_exam({"upcoming_exams": []}) is None

    def test_returns_days_until_of_first_exam(self):
        # upcoming_exams is sorted ascending by date in coordinator.
        data = {"upcoming_exams": [
            {"days_until": 2, "subject": "Mat", "title": "Funkcje", "date": "2026-04-17"},
            {"days_until": 5, "subject": "Pol", "title": "Lalka", "date": "2026-04-20"},
        ]}
        assert _val_next_exam(data) == 2


class TestAttrsNextExam:
    def test_empty_returns_empty(self):
        assert _attrs_next_exam({"upcoming_exams": []}) == {}

    def test_returns_full_exam_context(self):
        data = {"upcoming_exams": [
            {"days_until": 2, "subject": "Mat", "title": "Funkcje",
             "category": "Sprawdzian", "date": "2026-04-17", "hour": "10:30"},
        ]}
        attrs = _attrs_next_exam(data)
        assert attrs["subject"] == "Mat"
        assert attrs["title"] == "Funkcje"
        assert attrs["category"] == "Sprawdzian"
        assert attrs["date"] == "2026-04-17"
        assert attrs["hour"] == "10:30"


class TestUpcomingExamsAttrsCleanup:
    """BREAKING change: next_* atrybuty znikły z sensora `zapowiedzi`."""

    def test_no_next_keys_in_attrs(self):
        data = {"upcoming_exams": [
            {"days_until": 2, "subject": "Mat", "title": "Funkcje",
             "category": "Sprawdzian", "date": "2026-04-17", "hour": "10:30"},
        ]}
        attrs = _attrs_upcoming_exams(data)
        for key in ("next_date", "next_subject", "next_title",
                    "next_category", "next_days_until"):
            assert key not in attrs, f"{key} should be removed in v3.0"
        # Aggregate counts pozostają.
        assert "exams" in attrs
        assert "count_in_3_days" in attrs
        assert "total_count" in attrs


# ---------------------------------------------------------------------------
# frekwencja (% obecności bieżącego semestru)
# ---------------------------------------------------------------------------


class TestValFrequency:
    def test_empty_returns_zero(self):
        assert _val_frequency({"attendance_frequency": {}}) == 0.0

    def test_returns_current_semester(self):
        data = {"attendance_frequency": {
            "semester_1": 95.0, "semester_2": 88.5, "total": 91.0, "current": 88.5,
        }}
        assert _val_frequency(data) == 88.5


class TestAttrsFrequency:
    def test_empty_returns_empty(self):
        assert _attrs_frequency({"attendance_frequency": {}}) == {}

    def test_attrs_carry_per_semester_and_per_subject(self):
        data = {
            "attendance_frequency": {
                "semester_1": 95.0, "semester_2": 88.5,
                "total": 91.0, "current": 88.5,
            },
            "attendance_by_subject": {
                "Matematyka": {"present": 10, "missed": 1, "frequency": 90.91},
            },
        }
        attrs = _attrs_frequency(data)
        assert attrs["semester_1"] == 95.0
        assert attrs["semester_2"] == 88.5
        assert attrs["total"] == 91.0
        assert attrs["by_subject"] == data["attendance_by_subject"]


# ---------------------------------------------------------------------------
# nieobecnosci (count + listy dat per typ + listy obiektów)
# ---------------------------------------------------------------------------


@pytest.fixture
def attendance_sample():
    """Sample attendance entries spanning all relevant types."""
    return [
        {"date": "2026-04-01", "subject": "Mat", "period": 1, "teacher": "A",
         "topic": "F", "is_present": True, "is_absence": False, "is_late": False,
         "is_unjustified": False, "is_excused": False, "semester": 2},
        {"date": "2026-04-02", "subject": "Pol", "period": 2, "teacher": "B",
         "topic": "L", "is_present": False, "is_absence": True, "is_late": False,
         "is_unjustified": True, "is_excused": False, "semester": 2},
        {"date": "2026-04-03", "subject": "Hist", "period": 3, "teacher": "C",
         "topic": "X", "is_present": False, "is_absence": True, "is_late": False,
         "is_unjustified": False, "is_excused": True, "semester": 2},
        {"date": "2026-04-04", "subject": "Fiz", "period": 4, "teacher": "D",
         "topic": "Y", "is_present": False, "is_absence": False, "is_late": True,
         "is_unjustified": False, "is_excused": False, "semester": 2},
    ]


class TestValAbsencesCount:
    def test_empty_returns_zero(self):
        assert _val_absences_count({"attendance": []}) == 0

    def test_counts_only_absences_and_lates(self, attendance_sample):
        # 1 obecna + 1 unjustified + 1 excused + 1 late = 3 wpisy
        # liczone (nieobecność justified jest niepokonana — patrz spec).
        # Liczymy: total entries marked as absence OR late = 3.
        result = _val_absences_count({"attendance": attendance_sample})
        assert result == 3


class TestAttrsAbsences:
    def test_empty_returns_zeros(self):
        attrs = _attrs_absences({"attendance": []})
        assert attrs["total_absences"] == 0
        assert attrs["unjustified_count"] == 0
        assert attrs["lates_count"] == 0
        assert attrs["excused_count"] == 0
        assert attrs["absence_dates"] == []
        assert attrs["late_dates"] == []
        assert attrs["absences"] == []
        assert attrs["lates"] == []
        assert attrs["excused"] == []

    def test_buckets_split_correctly(self, attendance_sample):
        attrs = _attrs_absences({"attendance": attendance_sample})
        assert attrs["unjustified_count"] == 1
        assert attrs["excused_count"] == 1
        assert attrs["lates_count"] == 1
        assert attrs["total_absences"] == 2  # unjustified + excused
        assert attrs["absence_dates"] == ["2026-04-02", "2026-04-03"]
        assert attrs["late_dates"] == ["2026-04-04"]

    def test_absences_list_carries_full_context(self, attendance_sample):
        attrs = _attrs_absences({"attendance": attendance_sample})
        # Pierwsza nieobecność (Polski).
        first = attrs["absences"][0]
        assert first["date"] == "2026-04-02"
        assert first["subject"] == "Pol"
        assert first["period"] == 2
        assert first["teacher"] == "B"
        assert first["is_unjustified"] is True


# ---------------------------------------------------------------------------
# latest_absence
# ---------------------------------------------------------------------------


class TestLatestAbsence:
    def test_empty_returns_none(self):
        assert _val_latest_absence({"attendance": []}) is None
        assert _attrs_latest_absence({"attendance": []}) == {}

    def test_returns_most_recent_non_present_entry(self, attendance_sample):
        state = _val_latest_absence({"attendance": attendance_sample})
        # Najnowsza nieobecność/spóźnienie po dacie: 2026-04-04 (late, Fiz).
        assert state == "2026-04-04"
        attrs = _attrs_latest_absence({"attendance": attendance_sample})
        assert attrs["subject"] == "Fiz"
        assert attrs["period"] == 4
        assert attrs["is_late"] is True


# ---------------------------------------------------------------------------
# ogloszenia (count + list) + latest_announcement
# ---------------------------------------------------------------------------


@pytest.fixture
def announcements_sample():
    return [
        {"title": "Wycieczka", "author": "Dyrekcja",
         "description": "Klasy 5-8, 12 maja.", "date": "2026-04-15"},
        {"title": "Rekolekcje", "author": "Wychowawca",
         "description": "Trzy dni w marcu.", "date": "2026-03-01"},
    ]


class TestAnnouncementsCount:
    def test_empty_returns_zero(self):
        assert _val_announcements_count({"announcements": []}) == 0

    def test_returns_total_count(self, announcements_sample):
        assert _val_announcements_count(
            {"announcements": announcements_sample}
        ) == 2


class TestAnnouncementsAttrs:
    def test_empty_returns_empty(self):
        attrs = _attrs_announcements({"announcements": []})
        assert attrs["announcements"] == []
        assert attrs["total_count"] == 0

    def test_attrs_carry_top_5_and_count(self, announcements_sample):
        attrs = _attrs_announcements({"announcements": announcements_sample})
        assert attrs["total_count"] == 2
        assert len(attrs["announcements"]) == 2
        # Pierwszy jest najnowszy.
        assert attrs["announcements"][0]["title"] == "Wycieczka"


class TestLatestAnnouncement:
    def test_empty_returns_none(self):
        assert _val_latest_announcement({"announcements": []}) is None
        assert _attrs_latest_announcement({"announcements": []}) == {}

    def test_returns_first_announcement(self, announcements_sample):
        # Coordinator zwraca najnowsze pierwsze; pierwszy jest najnowszy.
        state = _val_latest_announcement(
            {"announcements": announcements_sample}
        )
        assert state == "Wycieczka"
        attrs = _attrs_latest_announcement(
            {"announcements": announcements_sample}
        )
        assert attrs["author"] == "Dyrekcja"
        assert attrs["date"] == "2026-04-15"
        assert "12 maja" in attrs["description"]
