"""DataUpdateCoordinator for the Librus APIX integration."""

from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

if TYPE_CHECKING:
    from . import LibrusApiClient

_LOGGER = logging.getLogger(__name__)

# Trim seen-id sets to this many entries (LRU). A long-running HA instance
# would otherwise let these grow unbounded over months/years.
_MAX_SEEN_ITEMS = 500

EVENT_NOWA_WIADOMOSC = f"{DOMAIN}_nowa_wiadomosc"
EVENT_NOWA_OCENA = f"{DOMAIN}_nowa_ocena"
EVENT_NOWA_ZAPOWIEDZ = f"{DOMAIN}_nowa_zapowiedz"


def _jest_nowa(date_str: str) -> bool:
    """Sprawdz czy data miesci sie w ostatnich 24 godzinach (dzis lub wczoraj)."""
    if not date_str:
        return False
    wczoraj = date.today() - timedelta(days=1)
    for fmt in (
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            d = datetime.strptime(date_str.strip(), fmt).date()
            return d >= wczoraj
        except ValueError:
            continue
    return False


def _add_lru(items: OrderedDict[Any, None], key: Any) -> None:
    """Add an item to an OrderedDict-as-LRU set, evicting oldest if over cap."""
    if key in items:
        items.move_to_end(key)
    else:
        items[key] = None
        if len(items) > _MAX_SEEN_ITEMS:
            items.popitem(last=False)


class LibrusDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Klasa zarzadzajaca pobieraniem danych z Librus."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: LibrusApiClient,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Inicjalizacja koordynatora."""
        self.client = client
        self._seen_message_hrefs: OrderedDict[str, None] = OrderedDict()
        self._seen_grade_ids: OrderedDict[tuple, None] = OrderedDict()
        self._seen_zapowiedzi_ids: OrderedDict[tuple, None] = OrderedDict()
        self._first_run: bool = True
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )

    async def _async_setup(self) -> None:
        """One-time initialization: first login.

        Called automatically by HA on the first refresh. If Librus is in
        maintenance, raises ConfigEntryNotReady so HA retries with backoff.
        """
        if not await self.client.async_authenticate():
            raise ConfigEntryNotReady(
                f"Nie udalo sie zalogowac do Librus dla {self.client.username} "
                "(mozliwy maintenance Librus). HA wykona retry automatycznie."
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Pobierz aktualne dane z API Librus."""
        current_sem = 1 if date.today().month >= 9 else 2

        try:
            student_info = await self.client.async_get_student_information()
            grades = await self.client.async_get_grades()
            messages = await self.client.async_get_messages(count=10)
            # Pobierz pelen terminarz (sprawdziany + dni wolne + inne) raz; sensor.zapowiedzi
            # uzywa tylko exam events, calendar.terminarz uzywa wszystkiego.
            terminarz_all = await self.client.async_get_schedule_events(
                months_ahead=2, only_exams=False
            )
            zapowiedzi = (
                [e for e in terminarz_all if e.get("is_exam")]
                if terminarz_all is not None
                else None
            )
            plan_lekcji = await self.client.async_get_timetable_events(weeks_ahead=4)

            if grades is None:
                # Zachowaj poprzednie dane o ocenach jesli dostepne, wiadomosci zaktualizuj jesli OK
                prev = self.data or {}
                if not prev.get("oceny"):
                    raise UpdateFailed("Nie udalo sie pobrac ocen i brak danych w cache")
                _LOGGER.warning(
                    "Nie udalo sie pobrac ocen - uzywam poprzednich danych z cache"
                )
                return {
                    "student_info": student_info or prev.get("student_info"),
                    "oceny": prev.get("oceny", []),
                    "oceny_wg_przedmiotu": prev.get("oceny_wg_przedmiotu", {}),
                    "wiadomosci": (
                        self._build_wiadomosci(messages)
                        if messages is not None
                        else prev.get("wiadomosci", [])
                    ),
                    "zapowiedzi": (
                        zapowiedzi
                        if zapowiedzi is not None
                        else prev.get("zapowiedzi", [])
                    ),
                    "terminarz": (
                        terminarz_all
                        if terminarz_all is not None
                        else prev.get("terminarz", [])
                    ),
                    "plan_lekcji": (
                        plan_lekcji
                        if plan_lekcji is not None
                        else prev.get("plan_lekcji", [])
                    ),
                }

            # Grupuj oceny wg przedmiotu i oznacz nowe
            oceny_wg_przedmiotu: dict[str, list[dict]] = {}
            for grade in grades:
                subject = grade["subject"]
                if subject not in oceny_wg_przedmiotu:
                    oceny_wg_przedmiotu[subject] = []
                oceny_wg_przedmiotu[subject].append({
                    "ocena": grade["grade"],
                    "data": grade["date"],
                    "kategoria": grade["category"],
                    "nauczyciel": grade["teacher"],
                    "semestr": grade.get("semester"),
                    "jest_nowa": _jest_nowa(grade["date"]),
                })

            wiadomosci = self._build_wiadomosci(messages)

            zapowiedzi_list = zapowiedzi if zapowiedzi is not None else []

            result = {
                "student_info": student_info,
                "oceny": grades,
                "oceny_wg_przedmiotu": oceny_wg_przedmiotu,
                "wiadomosci": wiadomosci,
                "zapowiedzi": zapowiedzi_list,
                "terminarz": terminarz_all if terminarz_all is not None else [],
                "plan_lekcji": plan_lekcji if plan_lekcji is not None else [],
                "semestr_biezacy": current_sem,
            }

            # Pierwsze pobranie - tylko zapamietaj stan, nie wysylaj powiadomien
            if self._first_run:
                self._first_run = False
                for msg in wiadomosci:
                    _add_lru(self._seen_message_hrefs, msg["href"])
                for grade in grades:
                    _add_lru(
                        self._seen_grade_ids,
                        (grade["subject"], grade["date"], grade["grade"]),
                    )
                for zap in zapowiedzi_list:
                    _add_lru(
                        self._seen_zapowiedzi_ids,
                        (zap["date"], zap["subject"], zap["title"]),
                    )
            else:
                self._fire_events(wiadomosci, grades, zapowiedzi_list)

            return result

        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Blad komunikacji z API: {err}") from err

    def _fire_events(
        self,
        messages: list[dict],
        grades: list[dict],
        zapowiedzi: list[dict] | None = None,
    ) -> None:
        """Wyslij zdarzenia HA dla nowych wiadomosci, ocen i zapowiedzi."""
        for msg in messages:
            href = msg.get("href", "")
            if href and href not in self._seen_message_hrefs:
                _add_lru(self._seen_message_hrefs, href)
                _LOGGER.debug("Nowa wiadomosc: %s", msg.get("title"))
                self.hass.bus.fire(
                    EVENT_NOWA_WIADOMOSC,
                    {
                        "nadawca": msg.get("author", ""),
                        "temat": msg.get("title", ""),
                        "data": msg.get("date", ""),
                        "ma_zalacznik": msg.get("has_attachment", False),
                    },
                )

        for grade in grades:
            grade_id = (grade["subject"], grade["date"], grade["grade"])
            if grade_id not in self._seen_grade_ids:
                _add_lru(self._seen_grade_ids, grade_id)
                _LOGGER.debug("Nowa ocena: %s %s", grade["subject"], grade["grade"])
                self.hass.bus.fire(
                    EVENT_NOWA_OCENA,
                    {
                        "przedmiot": grade["subject"],
                        "ocena": grade["grade"],
                        "data": grade["date"],
                        "kategoria": grade["category"],
                        "nauczyciel": grade["teacher"],
                    },
                )

        for zap in zapowiedzi or []:
            zap_id = (zap["date"], zap["subject"], zap["title"])
            if zap_id not in self._seen_zapowiedzi_ids:
                _add_lru(self._seen_zapowiedzi_ids, zap_id)
                _LOGGER.debug(
                    "Nowa zapowiedz: %s %s (%s)",
                    zap.get("subject"),
                    zap.get("title"),
                    zap.get("date"),
                )
                self.hass.bus.fire(
                    EVENT_NOWA_ZAPOWIEDZ,
                    {
                        "tytul": zap.get("title", ""),
                        "przedmiot": zap.get("subject", ""),
                        "kategoria": zap.get("category", ""),
                        "data": zap.get("date", ""),
                        "godzina": zap.get("hour", ""),
                        "dni_do": zap.get("days_until", 0),
                    },
                )

    def _build_wiadomosci(self, messages: list[dict] | None) -> list[dict]:
        """Oznacz nowe wiadomosci i zwroc liste."""
        result = []
        for msg in messages or []:
            msg["jest_nowa"] = _jest_nowa(msg.get("date", ""))
            result.append(msg)
        return result
