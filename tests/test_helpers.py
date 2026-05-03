"""Unit tests for pure helper functions in the Librus APIX integration."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from custom_components.librus_apix.coordinator import _is_recent, _add_lru, _MAX_SEEN_ITEMS
from custom_components.librus_apix.sensor import _grade_average


class TestGradeAverage:
    """_grade_average — averaging Polish-format grades."""

    def test_empty_returns_none(self):
        assert _grade_average([]) is None

    def test_only_invalid_returns_none(self):
        assert _grade_average([{"ocena": "X"}, {"ocena": ""}]) is None

    def test_single_grade(self):
        assert _grade_average([{"ocena": "4"}]) == 4.0

    def test_plus_adds_half(self):
        assert _grade_average([{"ocena": "4+"}]) == 4.5

    def test_minus_subtracts_quarter(self):
        assert _grade_average([{"ocena": "4-"}]) == 3.75

    def test_average_of_mixed(self):
        # (5 + 3 + 4.5) / 3 = 4.166... → 4.17
        assert _grade_average([
            {"ocena": "5"},
            {"ocena": "3"},
            {"ocena": "4+"},
        ]) == 4.17

    def test_invalid_skipped_not_failed(self):
        # 5 valid + 1 invalid → average from the valid one only
        assert _grade_average([
            {"ocena": "5"},
            {"ocena": "abc"},
        ]) == 5.0


class TestIsRecent:
    """_is_recent — date freshness within last 24h window."""

    def test_empty_string_false(self):
        assert _is_recent("") is False

    def test_unparseable_false(self):
        assert _is_recent("not a date") is False

    def test_today_polish_format(self):
        today = date.today().strftime("%d.%m.%Y")
        assert _is_recent(today) is True

    def test_yesterday_polish_format(self):
        yesterday = (date.today() - timedelta(days=1)).strftime("%d.%m.%Y")
        assert _is_recent(yesterday) is True

    def test_two_days_ago_false(self):
        old = (date.today() - timedelta(days=2)).strftime("%d.%m.%Y")
        assert _is_recent(old) is False

    def test_iso_format(self):
        today = date.today().strftime("%Y-%m-%d")
        assert _is_recent(today) is True

    def test_with_time(self):
        today = date.today().strftime("%d.%m.%Y 12:30")
        assert _is_recent(today) is True


class TestAddLru:
    """_add_lru — bounded OrderedDict-as-LRU helper."""

    def test_inserts_under_cap(self):
        from collections import OrderedDict
        d: OrderedDict[int, None] = OrderedDict()
        _add_lru(d, 1)
        _add_lru(d, 2)
        assert list(d.keys()) == [1, 2]

    def test_re_add_moves_to_end(self):
        from collections import OrderedDict
        d: OrderedDict[int, None] = OrderedDict()
        _add_lru(d, 1)
        _add_lru(d, 2)
        _add_lru(d, 1)  # touched, becomes most-recent
        assert list(d.keys()) == [2, 1]

    def test_evicts_oldest_over_cap(self):
        from collections import OrderedDict
        d: OrderedDict[int, None] = OrderedDict()
        # Fill exactly to cap.
        for i in range(_MAX_SEEN_ITEMS):
            _add_lru(d, i)
        assert len(d) == _MAX_SEEN_ITEMS
        # One more — oldest (0) must be evicted.
        _add_lru(d, _MAX_SEEN_ITEMS)
        assert len(d) == _MAX_SEEN_ITEMS
        assert 0 not in d
        assert _MAX_SEEN_ITEMS in d
