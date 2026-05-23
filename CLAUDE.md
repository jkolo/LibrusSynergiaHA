# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repozytorium

Custom Home Assistant integration **`librus_apix`** dla polskiego dziennika Librus Synergia. Dystrybucja: HACS (kategoria *Integration*). Jedyny komponent znajduje się w `custom_components/librus_apix/`.

Język w kodzie i komentarzach jest polski (`oceny`, `terminarz`, `plan_lekcji`, `zapowiedzi`, `srednia`, …) — utrzymuj ten styl.

## Branch policy (WAŻNE)

- Główny branch upstream: `main`. Repo ma dwa remote'y: `origin` (fork `jkolo/LibrusSynergiaHA`) i `upstream` (`LukMaverick/LibrusSynergiaHA`).
- **Wszystkie ficzery powstające w tej kopii integruj do brancha `develop`.** To jest aktywny branch developerski tego forka — nie merguj prosto do `main` ani nie pushuj feature branchy bezpośrednio na `origin/main`. Każdy feature branch (`feat/*`, `fix/*`) powinien być mergowany do `develop`.
- Branch `develop` powstał z renamingu `integration/choreops-extensions` (historia ciągła). Konwencja PR: feature → `develop` → (release) → `main`.
- Dotychczasowe ficzery zintegrowane do brancha: `feat/zapowiedzi-sensor`, `feat/calendar-platform`, `fix/config-entry-not-ready`, refactor v2.0.0 (12 epików), human-like sync v2.2.0 (6 PR-ów). Patrz `git log --oneline`.

## Komendy

### Środowisko testowe (Docker)

```bash
./start.sh                       # pierwsze uruchomienie: kopiuje custom_components do config/ i startuje stack
docker-compose up -d             # kolejne uruchomienia
docker-compose logs -f homeassistant
docker-compose down
```

- HA: <http://localhost:8123>
- Code Server: <http://localhost:8443> (hasło `homeassistant`)
- `docker-compose.yml` montuje `./custom_components` do `/config/custom_components` **read-only**, więc edycja w hoście jest natychmiastowa, ale zmiany zwykle wymagają restartu HA: `docker-compose restart homeassistant`.
- Reset stanu HA (usuwa konfigurację UI i config entries integracji): `rm -rf config/.storage && docker-compose restart homeassistant`.

### Testy

```bash
pip install -r requirements_test.txt
pytest tests/
pytest tests/test_init.py::test_setup_entry   # pojedynczy test
```

Testy używają `pytest-homeassistant-custom-component`, które dostarcza fixture `hass`. Mockuj `LibrusApiClient` przez `unittest.mock.patch("custom_components.librus_apix.LibrusApiClient", …)` — zobacz `tests/test_init.py` dla wzorca.

### Logging w runtime

Włączenie debug logów (już aktywne w `config/configuration.yaml`):

```yaml
logger:
  logs:
    custom_components.librus_apix: debug
    librus_apix: debug
```

### CI

W `.github/workflows/`: `hassfest.yml` (walidacja manifestu integracji HA) i `validate.yml` (HACS action z `category: integration`). Oba odpalane na push/PR/daily cron.

## Architektura

### Moduły

- `__init__.py` — `async_setup_entry`, klasa **`LibrusApiClient`** (cienki wrapper na bibliotekę `librus-apix`).
- `sensor.py` — koordynator i wszystkie sensory (oceny, średnie, wiadomości, zapowiedzi sprawdzianów, info o uczniu, szczęśliwy numerek).
- `calendar.py` — dwa kalendarze per config entry: `Terminarz` (z tagami w summary) i `Plan Lekcji`.
- `config_flow.py` — UI do podawania login/hasło, weryfikuje przez próbne logowanie.
- `const.py` — `DOMAIN = "librus_apix"`, `SCAN_INTERVAL = timedelta(hours=2)`.

`PLATFORMS = ["sensor", "calendar"]`.

### Wzorzec koordynatora — KLUCZOWY

W `__init__.async_setup_entry` tworzony jest **jeden** `LibrusDataUpdateCoordinator` (zdefiniowany w `sensor.py`), zapisany pod kluczem `f"{entry.entry_id}_coordinator"` w `hass.data[DOMAIN]`. Zarówno platforma `sensor`, jak i `calendar` **pobierają ten sam coordinator** — nie tworzą własnego. `sensor.py` ma fallback na lokalne tworzenie (legacy install), ale `calendar.py` zakłada, że już istnieje (rzuci `KeyError` jeśli nie). **Nie duplikuj fetcherów** — dodawaj nowe pola do słownika zwracanego przez `_async_update_data()` i konsumuj w nowych entity.

Struktura `coordinator.data`:
```
student_info, oceny, oceny_wg_przedmiotu, wiadomosci,
zapowiedzi (filtr is_exam), terminarz (pełny, z is_day_off i event_type),
plan_lekcji, semestr_biezacy
```

### Bibliotekę `librus-apix` wołaj przez executor

Biblioteka `librus-apix` jest **synchroniczna**. Każde wywołanie owija `loop.run_in_executor(None, fn, …)`. Stan klienta (`self._client`, `self._token`) jest chroniony `asyncio.Lock` i resetowany przez `_reset_auth()` na każdym błędzie. Każda metoda fetchująca ma pętlę `for attempt in range(2)` z obsługą `TokenError` (re-auth + retry).

### Resilience: maintenance Librusa

Librus ma okresowe przerwy (zwykle raz dziennie). Wzorzec:
- `async_setup_entry` rzuca `ConfigEntryNotReady` jeśli pierwsze logowanie się nie uda — HA retryuje setup z exponential backoff.
- W `_async_update_data`: jeśli pobranie ocen zwróci `None`, **zachowaj poprzednie dane z cache** (`self.data`) zamiast fail-out. Dotyczy też wiadomości/zapowiedzi/terminarza/planu lekcji. To zapobiega znikaniu encji z dashboardu podczas maintenance'u.

### Logika semestru

`_current_semester()` w `__init__.py`: miesiące 9–1 → semestr 1, 2–6 → semestr 2 (lipiec/sierpień traktowane jako semestr 2). Wszystkie pobrania ocen (numeric + descriptive) są **filtrowane do bieżącego semestru** już w warstwie `LibrusApiClient`.

### Parsowanie ocen do średniej

`_srednia_ocen()` w `sensor.py`: bazowa cyfra + `+` daje `+0.5`, `-` daje `-0.25`. Sensory średnich (`LibrusSredniaOcenSensor`, `LibrusSredniaPrzedmiotuSensor`) mają `state_class = MEASUREMENT` — HA automatycznie rysuje wykres historyczny.

### Sensory tworzone dynamicznie

`async_setup_entry` w `sensor.py` tworzy sensor per przedmiot (`LibrusPrzedmiotSensor` + `LibrusSredniaPrzedmiotuSensor`) na podstawie kluczy `oceny_wg_przedmiotu` z **pierwszego refreshu**. Nowy przedmiot pojawiający się w trakcie sesji nie utworzy nowych encji bez restartu integracji — to świadoma decyzja.

### Eventy do automatyzacji

Koordynator emituje na `hass.bus`:
- `librus_apix_nowa_wiadomosc` (pola: `nadawca`, `temat`, `data`, `ma_zalacznik`)
- `librus_apix_nowa_ocena` (`przedmiot`, `ocena`, `data`, `kategoria`, `nauczyciel`)
- `librus_apix_nowa_zapowiedz` (`tytul`, `przedmiot`, `kategoria`, `data`, `godzina`, `dni_do`)

**Pierwsze pobranie tylko zapamiętuje stan** w `_seen_message_hrefs` / `_seen_grade_ids` / `_seen_zapowiedzi_ids` (flaga `_first_run`). Bez tego po (re)starcie wystrzeliłyby duplikaty dla wszystkich istniejących elementów.

### Privacy: nie pobieraj treści wiadomości

`async_get_messages` używa `get_received` i wyciąga tylko `author`, `title`, `date`, `href`, `unread`, `has_attachment`. **Nie wołaj funkcji `get_message_content` / nie otwieraj `href`** — to oznaczyłoby wiadomość jako przeczytaną w Librusie, a użytkownik zauważy. Komentarz w README ostrzega o tym; zachowaj tę umowę przy rozszerzaniu.

### Klasyfikacja eventów terminarza

`async_get_schedule_events` heurystyką klasyfikuje event do `event_type ∈ {sprawdzian, kartkowka, praca_klasowa, praca_kontrolna, wypracowanie_klasowe, test, dzien_wolny, inne}` po słowach kluczowych w `title + Kategoria + Typ` oraz fragmentach w `href`. `is_exam` to disjunction pierwszych sześciu. `is_day_off` zawiera m.in. „dzień wolny" i `href` zawierający `wolne`/`szczegoly_wolne`. Calendar `Terminarz` zamienia `event_type` na prefix `[TAG]` w summary (zobacz `EVENT_TYPE_TAGS` w `calendar.py`) — to umożliwia użytkownikom filtrowanie po regexie w automatyzacjach.

## Konwencje

- **`unique_id` encji**: zawsze prefix `f"{config_entry.entry_id}_…"` żeby wiele dzieci (wiele config entries) nie kolidowało.
- **`device_info` współdzielone** przez `_device_info()` w `sensor.py` i `calendar.py` — wszystkie encje danego config entry trafiają do jednego device "Librus - {imię ucznia}".
- Manifest `version` bumpuj przy każdym wydaniu (HACS go używa) w `manifest.json`.
- `hacs.json` deklaruje minimalną wersję HA — sprawdź przy zmianach API HA.
