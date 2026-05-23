"""Pure helpers that make Librus syncs look less robotic.

This module contains side-effect-free functions used by the coordinator:
- User-Agent rotation and browser-like header construction.
- Random refresh intervals with jitter and quiet-hours awareness.
- Endpoint-order shuffling and inter-fetch pause durations.
- School-day detection from the Librus calendar (`schedule_events`).

All randomness is parameterised via `random.Random` so tests can pass a
deterministic instance (e.g. `Random(42)`).
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta


USER_AGENTS: tuple[str, ...] = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
)


DEFAULT_HEADERS_TEMPLATE: dict[str, str] = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.7,en;q=0.6",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    # Content-Type is library-required for POST authorize calls.
    "Content-Type": "application/x-www-form-urlencoded",
}


def pick_user_agent(rng: random.Random) -> str:
    """Return one User-Agent string from the pool using `rng`."""
    return rng.choice(USER_AGENTS)


def build_headers(user_agent: str) -> dict[str, str]:
    """Build a full headers dict combining template + a chosen User-Agent."""
    headers = dict(DEFAULT_HEADERS_TEMPLATE)
    headers["User-Agent"] = user_agent
    return headers


def random_endpoint_order(rng: random.Random, names: list[str]) -> list[str]:
    """Return a shuffled copy of `names` using `rng` (does not mutate input)."""
    out = list(names)
    rng.shuffle(out)
    return out


def jitter_pause_seconds(
    rng: random.Random, lo: float = 3.0, hi: float = 15.0
) -> float:
    """Return a uniform random pause in seconds within [lo, hi]."""
    return rng.uniform(lo, hi)


def is_school_day(today: date, schedule_events: list[dict] | None) -> bool:
    """Return True if `today` looks like a typical school day.

    Sygnały (priorytet):
    1. Weekend → False (terminarz Librusa nie zawsze oznacza Sb/Nd wprost).
    2. Event z `is_day_off=True` lub `event_type=="day_off"` na dzisiaj
       w `schedule_events` → False (ferie, wakacje, święta państwowe i
       religijne, majówki, dzień patrona, rekolekcje — Librus oznacza
       wszystkie te dni).
    3. Inaczej → True.

    Brak terminarza (None / pusta lista) → optymistyczne True (nie wiemy);
    jeden refresh w wakacje na bazowym interwale to akceptowalna degradacja.
    """
    if today.weekday() >= 5:
        return False
    today_iso = today.isoformat()
    for event in schedule_events or []:
        if event.get("date") != today_iso:
            continue
        if event.get("is_day_off") or event.get("event_type") == "day_off":
            return False
    return True


def _in_quiet_hours(t: time, quiet: tuple[time, time]) -> bool:
    """True if `t` falls inside [quiet_start, quiet_end), supporting wraparound."""
    start, end = quiet
    if start <= end:
        return start <= t < end
    # Wraparound (e.g. 22:30 → 06:30): the quiet interval crosses midnight.
    return t >= start or t < end


def next_run_delay(
    rng: random.Random,
    *,
    base_minutes: float,
    jitter: float,
    quiet_hours: tuple[time, time] | None,
    is_school_day_now: bool,
    off_school_multiplier: float,
    now: datetime,
) -> float:
    """Return seconds until the next refresh.

    1. `effective_base = base_minutes * (off_school_multiplier if not is_school_day_now else 1)`.
    2. Apply ±`jitter` around `effective_base`.
    3. If `quiet_hours` is set and the resulting target falls inside the
       quiet window, push the target forward to a random 0–15 min after
       `quiet_end`.

    Returns: float, seconds (>= 60.0 floor to avoid hot loops).
    """
    effective_base = base_minutes * (1.0 if is_school_day_now else off_school_multiplier)
    delta = rng.uniform(-jitter, jitter)
    delay_minutes = effective_base * (1.0 + delta)
    delay_seconds = delay_minutes * 60.0

    if quiet_hours is not None:
        target = now + timedelta(seconds=delay_seconds)
        if _in_quiet_hours(target.time(), quiet_hours):
            quiet_end = quiet_hours[1]
            # Find the next occurrence of quiet_end in the future.
            candidate = target.replace(
                hour=quiet_end.hour,
                minute=quiet_end.minute,
                second=quiet_end.second,
                microsecond=0,
            )
            while candidate <= target:
                candidate += timedelta(days=1)
            # Add a small random tail (0–15 min) so wakeups aren't aligned.
            candidate += timedelta(seconds=rng.uniform(0.0, 15.0 * 60.0))
            delay_seconds = (candidate - now).total_seconds()

    return max(60.0, delay_seconds)
