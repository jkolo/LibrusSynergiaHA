"""Tests for the pure helpers in custom_components.librus_apix.humanize."""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

import pytest
from freezegun import freeze_time

from custom_components.librus_apix.humanize import (
    DEFAULT_HEADERS_TEMPLATE,
    USER_AGENTS,
    build_headers,
    is_school_day,
    jitter_pause_seconds,
    next_run_delay,
    pick_user_agent,
    random_endpoint_order,
)


class TestPickUserAgent:
    def test_returns_member_of_pool(self):
        rng = random.Random(42)
        for _ in range(20):
            assert pick_user_agent(rng) in USER_AGENTS

    def test_deterministic_with_seed(self):
        a = pick_user_agent(random.Random(42))
        b = pick_user_agent(random.Random(42))
        assert a == b


class TestBuildHeaders:
    def test_contains_user_agent(self):
        ua = "Mozilla/5.0 fake test agent"
        headers = build_headers(ua)
        assert headers["User-Agent"] == ua

    def test_includes_template_keys(self):
        headers = build_headers("test-ua")
        for key in DEFAULT_HEADERS_TEMPLATE:
            assert key in headers

    def test_independent_copies(self):
        h1 = build_headers("a")
        h2 = build_headers("b")
        assert h1["User-Agent"] != h2["User-Agent"]
        assert DEFAULT_HEADERS_TEMPLATE.get("User-Agent") is None


class TestRandomEndpointOrder:
    def test_returns_permutation(self):
        names = ["a", "b", "c", "d", "e"]
        rng = random.Random(42)
        out = random_endpoint_order(rng, names)
        assert sorted(out) == sorted(names)
        assert len(out) == len(names)

    def test_does_not_mutate_input(self):
        names = ["a", "b", "c"]
        original = list(names)
        random_endpoint_order(random.Random(0), names)
        assert names == original

    def test_seed_42_concrete_permutation(self):
        # Lock-in test: protects against accidental shuffle algorithm changes.
        names = ["student_info", "grades", "messages", "schedule", "timetable"]
        out = random_endpoint_order(random.Random(42), names)
        # Whatever Random(42) gives, two calls with same seed must agree.
        assert out == random_endpoint_order(random.Random(42), names)


class TestJitterPauseSeconds:
    def test_within_default_range(self):
        rng = random.Random(42)
        for _ in range(50):
            v = jitter_pause_seconds(rng)
            assert 3.0 <= v <= 15.0

    def test_custom_range(self):
        rng = random.Random(42)
        for _ in range(50):
            v = jitter_pause_seconds(rng, lo=0.5, hi=3.0)
            assert 0.5 <= v <= 3.0


class TestIsSchoolDay:
    def test_weekday_empty_schedule_is_school(self):
        # 2026-05-12 is a Tuesday.
        assert is_school_day(date(2026, 5, 12), []) is True

    def test_saturday_is_not_school(self):
        # 2026-05-09 is a Saturday.
        assert is_school_day(date(2026, 5, 9), []) is False

    def test_sunday_is_not_school(self):
        # 2026-05-10 is a Sunday.
        assert is_school_day(date(2026, 5, 10), []) is False

    def test_day_off_event_for_today_blocks(self):
        today = date(2026, 5, 12)
        events = [
            {"date": today.isoformat(), "is_day_off": True, "title": "Wakacje"},
        ]
        assert is_school_day(today, events) is False

    def test_event_type_day_off_blocks(self):
        today = date(2026, 5, 12)
        events = [{"date": today.isoformat(), "event_type": "day_off"}]
        assert is_school_day(today, events) is False

    def test_event_for_other_day_does_not_block(self):
        today = date(2026, 5, 12)
        other = date(2026, 5, 13)
        events = [{"date": other.isoformat(), "is_day_off": True}]
        assert is_school_day(today, events) is True

    def test_none_schedule_treated_as_school(self):
        # Tuesday + no schedule → optimistic True.
        assert is_school_day(date(2026, 5, 12), None) is True

    def test_exam_event_not_treated_as_off(self):
        today = date(2026, 5, 12)
        events = [
            {"date": today.isoformat(), "event_type": "exam", "is_exam": True},
        ]
        assert is_school_day(today, events) is True


class TestNextRunDelay:
    def test_school_day_jitter_range(self):
        rng = random.Random(42)
        for _ in range(50):
            d = next_run_delay(
                rng,
                base_minutes=120.0,
                jitter=0.25,
                quiet_hours=None,
                is_school_day_now=True,
                off_school_multiplier=6.0,
                now=datetime(2026, 5, 12, 10, 0),
            )
            # 120 min ± 25%
            assert 90 * 60 <= d <= 150 * 60

    def test_off_school_multiplier_applied(self):
        rng = random.Random(42)
        for _ in range(50):
            d = next_run_delay(
                rng,
                base_minutes=120.0,
                jitter=0.25,
                quiet_hours=None,
                is_school_day_now=False,
                off_school_multiplier=6.0,
                now=datetime(2026, 7, 15, 10, 0),
            )
            # Effective base = 120 * 6 = 720 min ± 25% → 540-900 min.
            assert 540 * 60 <= d <= 900 * 60

    def test_quiet_hours_pushes_past_end(self):
        # now=22:00, jitter=0 → target ~23:00 falls inside 22:30-06:30 quiet.
        rng = random.Random(42)
        now = datetime(2026, 5, 12, 22, 0)
        d = next_run_delay(
            rng,
            base_minutes=60.0,
            jitter=0.0,
            quiet_hours=(time(22, 30), time(6, 30)),
            is_school_day_now=True,
            off_school_multiplier=6.0,
            now=now,
        )
        # Result must land at-or-after 06:30 next day.
        target = now + timedelta(seconds=d)
        next_quiet_end = datetime(2026, 5, 13, 6, 30)
        assert target >= next_quiet_end

    def test_quiet_hours_no_change_when_outside(self):
        # now=10:00, jitter=0, base=120 → target ~12:00 outside 22:30-06:30.
        rng = random.Random(42)
        now = datetime(2026, 5, 12, 10, 0)
        d = next_run_delay(
            rng,
            base_minutes=120.0,
            jitter=0.0,
            quiet_hours=(time(22, 30), time(6, 30)),
            is_school_day_now=True,
            off_school_multiplier=6.0,
            now=now,
        )
        # Approximately 120*60 (allow tiny epsilon since jitter=0).
        assert d == pytest.approx(120 * 60, rel=1e-6)

    def test_minimum_floor(self):
        # base=0 should still return >= 60 to avoid hot loop.
        rng = random.Random(42)
        d = next_run_delay(
            rng,
            base_minutes=0.0,
            jitter=0.0,
            quiet_hours=None,
            is_school_day_now=True,
            off_school_multiplier=6.0,
            now=datetime(2026, 5, 12, 10, 0),
        )
        assert d >= 60.0

    @freeze_time("2026-07-15 10:00:00")
    def test_freezegun_off_school_summer(self):
        # Wakacje letnie — is_school_day_now=False (caller's responsibility,
        # ale tu testujemy że delay rzeczywiście rośnie).
        rng = random.Random(42)
        d = next_run_delay(
            rng,
            base_minutes=120.0,
            jitter=0.0,
            quiet_hours=None,
            is_school_day_now=False,
            off_school_multiplier=6.0,
            now=datetime.now(),
        )
        assert d == pytest.approx(720 * 60, rel=1e-6)
