# Changelog

## [4.0.0] – 2026-09-25

### ⚠️ Zmiana łamiąca

- **`sensor.librus_<dziecko>_zapowiedzi` usunięty — zastępuje go `sensor.librus_<dziecko>_terminarz`.** Nowy sensor zawiera cały terminarz (sprawdziany, kartkówki, dni wolne, wycieczki, zebrania), a sprawdziany filtruje się flagą `is_exam`. Stary wpis znika z rejestru encji automatycznie przy starcie integracji. Mapowanie atrybutów: [MIGRATION.md](MIGRATION.md#migracja-v3x--v40).

### Dodano

- **Terminarz z opisem i nauczycielem.** Wpisy terminarza mają pola `description` (opis wpisany przez nauczyciela), `teacher`, `weekday` (polska nazwa dnia) i `details`. Kalendarz „Terminarz” pokazuje opis i nauczyciela w szczegółach wpisu.
- **`sensor.librus_<dziecko>_terminarz`**: stan to liczba nadchodzących wpisów. Atrybuty: `events`, `count`, `by_type`, `exams_in_3_days` / `exams_in_7_days` / `exams_in_14_days`, `exams_total`. Lista `events` jest przycinana do ok. 12 KB (flaga `events_truncated`, opis skracany do 150 znaków), żeby zmieścić się w limicie 16 KB recordera. Pełne dane są w kalendarzu.
- **Zadania domowe.** Sensor `sensor.librus_<dziecko>_zadania_domowe` (zadania z terminem w najbliższych 30 dniach; atrybuty `homework`, `by_subject`, `due_in_3_days`, `due_in_7_days`) i kalendarz `calendar.librus_<dziecko>_zadania_domowe` (wpisy całodniowe w dniu terminu). Integracja pobiera tylko listę zadań, nie otwiera szczegółów.
- **Nowe encje zdarzeń:** `new_homework` (nowe zadanie domowe) i `new_schedule_event` (każdy nowy wpis w terminarzu, nie tylko sprawdzian).
- README: przykładowe karty terminarza, sprawdzianów i zadań domowych.
- **Karta `librus-grades-card` sama wykrywa przedmioty.** Zamiast listy `entities` wystarczy `entity:` z dowolną encją ucznia (np. `sensor.librus_<dziecko>_grades`). Karta zbiera wszystkie sensory z `grade_details` z tego samego urządzenia. Stała lista psuła się przy zmianie przedmiotów (np. przejście z edukacji wczesnoszkolnej do klasy 4) i karta zostawała pusta, mimo że oceny były w HA. `entities` nadal działa i jest dołączane do wykrytych encji.

### Naprawiono

- **`librus-subject-grades-card` pokazywała entity_id zamiast nazwy przedmiotu w nagłówku.** Sensor przedmiotu wystawia teraz atrybut `subject`.
- **Karty Librusa ładowane w kilku wersjach naraz.** Zasoby Lovelace zawierały duplikaty (`?v=3.8.0`, `?v=3.8.1`, `?v=4.0.0`), przeglądarka zgłaszała „has already been used with this registry”, a wygrywała przypadkowa, często stara wersja karty. Rejestracja zostawia teraz dokładnie jeden wpis na kartę i usuwa pozostałe.
- **Akcje `list_messages` i `download_attachment` bez opisów.** Obie mają wpisy w `services.yaml`, więc w Narzędziach deweloperskich pokazują nazwy i pola.

### Synchronizacja z upstream

- Zmerge'owano [LukMaverick/LibrusSynergiaHA](https://github.com/LukMaverick/LibrusSynergiaHA) do v1.1.5. Wymaganie `librus-apix>=1.5.1` było już spełnione (`==1.5.1`). Zadania domowe i sensor terminarza przeniesiono na architekturę v3 (angielskie klucze atrybutów, encje zdarzeń zamiast `hass.bus`).

---

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
