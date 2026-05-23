# Changelog

## [3.8.1] – 2026-05-23

### Naprawiono

- **Przerwa techniczna Librusa mylona z błędnym hasłem** — przy HTTP 503 od Librusa integracja nie uruchamia już przepływu ponownego uwierzytelnienia (reauth flow). Librus zwracał 503 podczas codziennej przerwy technicznej, co powodowało fałszywy komunikat „zmień hasło". Teraz przerwa jest wykrywana jako zdarzenie przejściowe: dane pozostają z cache, w logach pojawia się komunikat `Librus is in maintenance mode`, a HA ponowi połączenie automatycznie po powrocie serwisu.

- **Sensory języka angielskiego i polskiego jako `unavailable`** — po aktualizacji do v3.0 sensory `sensor.librus_*_jezyk_angielski` i `sensor.librus_*_jezyk_polski` trafiały do rejestru encji z sufiksem `_2` i flagą `disabled_by: integration`. Przyczyną był konflikt `unique_id` między starym zapisem z polskim znakiem `ę` a nowym ASCII, wynikający ze zmiany zachowania `slugify` w HA 2026.5+. Dodano normalizację nazw przedmiotów (`.lower()` + normalizacja białych znaków), która zapobiega przyszłym kolizjom.

- **Sensor z 0 ocenami pokazuje `unavailable` zamiast `0`** — `LibrusSubjectGradesSensor.native_value` zwracał `None` dla pustej listy ocen, co HA tłumaczył na stan `unavailable`. Teraz zwraca `0`.

### Techniczne (CI/walidacja)

- Dodano `http` do `dependencies` w `manifest.json` (wymagane przez hassfest — komponent jest używany do rejestracji statycznych zasobów JS kart Lovelace).
- Dodano `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)` — wymagane przez hassfest gdy `async_setup` jest zdefiniowane.
- Naprawiono format placeholderów w `strings.json` — cudzysłowy pojedyncze wokół `{href}` powodowały błąd walidacji ICU (HA traktuje `'` jako znak ucieczki).
- Włączono GitHub Issues i dodano wymagane przez HACS tematy repozytorium (`hacs`, `homeassistant`, `home-assistant`, `integration`).

---

## [3.8.0] – 2026-05-08

### Dodano

- **Karta `librus-subject-grades-card`** — kompaktowa karta Lovelace pokazująca oceny z wybranego przedmiotu w trybie listy z możliwością rozwinięcia szczegółów w dialogu. Obsługuje oceny opisowe (z polem Komentarz) oraz sortowanie malejące po dacie.

### Naprawiono

- Naprawa atrybutów sensorów ocen (limit 16 KB Lovelace).
- Popup ocen otwiera się poprawnie przy pierwszym kliknięciu (dialog zawsze w DOM).
- Kategoria ocen opisowych pobierana z pola `Umiejętność` zamiast syntetycznego `Ocena: X`.
