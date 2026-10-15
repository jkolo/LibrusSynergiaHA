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
- **Poprawy ocen są powiązane z poprawianą oceną.** Librus oznacza poprawę tylko linią „Poprawa oceny: 1 (kartkówka)” (ocena i kategoria, bez daty), a samej poprawianej oceny nie wyróżnia. Integracja dopasowuje ją w obrębie przedmiotu po wartości i kategorii (z datą nie późniejszą niż poprawa) i dodaje do każdego wpisu w `grade_details` pola `correction_of` (na poprawie: `grade`, `category`, `date` poprawianej oceny) oraz `corrected_by` (na poprawianej ocenie: ocena, która ją poprawiła). Gdy pasuje kilka ocen, poprawa pozostaje niepowiązana (`date: null`), zamiast zgadywać. Karta `librus-subject-grades-card` pokazuje poprawę jako `1 → 6` (poprawiana ocena przekreślona), a `librus-grades-card` oznacza wiersz plakietką „POPRAWA”, a poprawianą ocenę przygasza i przekreśla; okno szczegółów podaje, co zostało poprawione i kiedy.
- **Karta `librus-schedule-card` — sprawdziany i lektury.** Dwie sekcje: sprawdziany/kartkówki z „dziś / jutro / za N dni” (kolor wg pilności) i opisem, oraz lektury z terminem. Źródło: `sensor.librus_<dziecko>_terminarz`.
- **Lektury w terminarzu: `event_type: reading`.** Librus zapisuje je jako „Inne.” z opisem „Lektury - …”; klasyfikator sprawdza słowo „lektur” w tytule i opisie (po sprawdzianach, więc „Sprawdzian z lektury” zostaje sprawdzianem). Kalendarz „Terminarz” oznacza je `📖 [LEKTURA]`.
- **Średnia ważona tam, gdzie szkoła jej używa.** Sensory średnich uwzględniają wagę z dymka oceny i pomijają oceny z „Licz do średniej: nie” (lub wagą 0). Gdy Librus nie podaje tych linii (szkoły bez średniej ważonej), wynik to zwykła średnia jak dotąd. Oceny opisowe z cyfrą mają teraz `counts`/`weight` równe `null` zamiast `false`/`0`, więc nadal liczą się do średniej.
- **Uwagi.** Sensor `sensor.librus_<dziecko>_uwagi` (stan: liczba uwag; atrybuty `notes` — 20 najnowszych z treścią, kategorią, nauczycielem i rodzajem `positive`/`negative`/`neutral` — oraz liczniki i `latest`) i encja zdarzenia `new_note` dla nowej uwagi. Dane z JSON API Librusa (to samo, którego używa `librus-apix` przy frekwencji); sposób odczytu wzorowany na forku [procaktomasz/LibrusSynergiaHA](https://github.com/procaktomasz/LibrusSynergiaHA) ([LukMaverick/LibrusSynergiaHA#13](https://github.com/LukMaverick/LibrusSynergiaHA/issues/13)).

### Naprawiono

- **Średnie nie liczą już ocen, które zostały poprawione.** Poprawiana `1` i jej poprawa `6` dawały średnią 3,5 zamiast 6,0. Dotyczy `sensor.librus_<dziecko>_srednia_<przedmiot>`, atrybutu `average` sensora przedmiotu oraz średniej ogólnej. Historia ocen (`grade_list`, `grade_count`, `grade_details`) pozostaje pełna.

- **`librus-subject-grades-card` pokazywała entity_id zamiast nazwy przedmiotu w nagłówku.** Sensor przedmiotu wystawia teraz atrybut `subject`.
- **Kartkówki nie były rozpoznawane jako sprawdziany.** Librus pisze „Kartkówka” przez „ó”, a klasyfikator szukał „kartkow”. Wpisy trafiały do `other`, nie liczyły się do `is_exam`/`exams_in_*` i nie tworzyły obowiązków nauki. Klasyfikator porównuje teraz tekst bez polskich znaków.
- **Nieobecność nauczyciela traktowana jak dzień wolny.** Wpisy „Nieobecność: / Nauczyciel: …” (Librus linkuje je jak dni wolne) dostawały `day_off`, więc `is_school_day` uznawał dzień za wolny i synchronizacja zwalniała (np. wakat nauczyciela zaznaczał tak cały tydzień). Mają teraz osobny typ `teacher_absence` (tag `[NIEOBECNOSC-NAUCZYCIELA]` w kalendarzu) i `is_day_off: false`.
- **Karty Librusa ładowane w kilku wersjach naraz.** Zasoby Lovelace zawierały duplikaty (`?v=3.8.0`, `?v=3.8.1`, `?v=4.0.0`), przeglądarka zgłaszała „has already been used with this registry”, a wygrywała przypadkowa, często stara wersja karty. Rejestracja zostawia teraz dokładnie jeden wpis na kartę i usuwa pozostałe.
- **Każda ocena „nie liczyła się do średniej” i miała wagę 0.** Szkoły bez średniej ważonej nie pokazują w dymku oceny linii „Licz do średniej” ani „Waga”, a `librus-apix` zamienia ich brak na `False`/`0` (i `value` na napis `"Does not count"`). Integracja czyta teraz obie linie z dymka sama: gdy Librus ich nie podaje, `counts` i `weight` mają wartość `null`, a kalendarz ocen i obie karty ocen nie pokazują wtedy tych wierszy. `value` jest zawsze liczbą (`4+` → 4.5) albo `null` dla ocen nieliczbowych (`np`, `+`).
- **Konto bez modułu ocen (np. zerówka) wymuszało ponowne logowanie całej integracji.** Librus odpowiada przy ocenach „Brak dostępu”, a `librus-apix` zgłasza to tak samo jak wygasły token. Po dwóch próbach integracja uznawała dane logowania za złe i uruchamiała reauth. Teraz sprawdza token na stronie informacji o uczniu: gdy działa, oceny są puste, a reszta (terminarz, plan, wiadomości…) działa normalnie ([LukMaverick/LibrusSynergiaHA#10](https://github.com/LukMaverick/LibrusSynergiaHA/issues/10)).
- **Przeglądarka pokazywała stare wersje kart po aktualizacji.** URL karty miał `?v=<wersja z manifestu>`, więc przebudowany JS przy tej samej wersji trafiał pod stary adres i przeglądarki brały go z cache. `?v=` to teraz skrót treści pliku: każda zmiana karty to nowy URL. Integracja usuwa też przy starcie pliki `*.js.gz` starsze od swojego `.js` (lub bez niego) — serwer podawał je zamiast nowej karty. Naprawiony też duplikat wpisu karty w zasobach Lovelace: przy starcie HA, gdy kolekcja zasobów nie była jeszcze wczytana, integracja dokładała drugi wpis obok zapisanego w pliku.
- **Atrybuty sensora nieobecności przekraczały 16 KB i nie trafiały do historii.** Listy `absences` i `lates` rosły z rokiem szkolnym (63 nieobecności = 26,5 KB). Teraz zawierają 30 / 15 najnowszych wpisów z flagami `absences_truncated` / `lates_truncated`; liczniki i `absence_dates` / `late_dates` liczą całość, pełne dane są w kalendarzu „Obecności”. **Usunięto atrybut `excused`** — dublował `absences` (każdy wpis ma `is_excused`); filtr: `absences | selectattr('is_excused')`.
- **„Ostatnie odświeżenie” nie przeskakiwało, gdy dane się nie zmieniły.** Koordynator nie powiadamiał encji po cyklu z identycznymi danymi, więc sensor diagnostyczny pokazywał stary czas mimo wykonanego pobrania. Teraz encje są odświeżane po każdym cyklu; niezmienione stany nie tworzą nowych wpisów w historii.
- **Kalendarz planu lekcji: zastępstwa jako surowy słownik Pythona, dni wolne bez flagi.** Opis lekcji pokazywał `zastępstwo: {'teacher_swap': …}`. Teraz: „Zastępstwo: / Nauczyciel: wakat → Głuchowska Monika / Sala: s31 → brak / Dodano: …”. Tytuł lekcji dostaje tag jak w terminarzu: `🔄 [ZASTEPSTWO]`, `❌ [ODWOLANE]`, `🏖️ [WOLNE]` (dzień wolny szkoły), więc automatyzacje i dashboardy nie muszą parsować opisu.
- **Terminarz: sprawdziany i lektury nie wypadają z atrybutów; czystsze opisy w kalendarzu.** Lista `events` jest przycinana do ok. 12 KB — wcześniej od końca, więc dziesiątki wpisów „Nieobecność: wakat…” mogły wypchnąć dalszy sprawdzian (i zniknąłby z karty). Teraz budżet najpierw dostają sprawdziany i lektury. Opis wpisu w kalendarzu „Terminarz” nie zawiera już linii technicznych (`Godzina: unknown`, `Lekcja nr: unknown`, `Dzień:`, `event_type:` — typ jest w tagu tytułu).
- **`librus-apix` 1.6.0** (z 1.5.1). Plan lekcji pokazuje wszystkie grupy z lekcji dzielonej (np. `Język angielski / Język niemiecki`); wcześniej widać było tylko pierwszą. Oceny opisowe w nowym schemacie Librusa (tabela ładowana JavaScriptem) są pobierane. Parser ocen działa z soupsieve 3.x — HA 2026.10 ma już soupsieve 3.0.1, a kolejne wersje mogą usunąć składnię selektorów, której używała 1.5.1.
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
