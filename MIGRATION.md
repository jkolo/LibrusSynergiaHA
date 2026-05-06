# Migracja v2.x → v3.0

⚠️ **v3.0.0 zawiera breaking changes**:
1. **Bus eventy znikają** — `librus_apix_new_grade/_message/_exam` zastąpione
   przez Event Entity (HA 2024.5+). Trigger automation `platform: event`
   trzeba przepisać na `platform: state` na encji `event.<dziecko>_*`.
2. **Atrybuty `next_*` na sensorze `zapowiedzi` znikają** — przeniesione do
   dedykowanego sensora `sensor.<dziecko>_next_exam`.
3. **Per-subject sensory enabled by default** — nowe instalacje dostaną
   wszystkie przedmioty włączone od razu. Istniejące entity registry
   zachowuje stary `disabled_by` stan; włączasz/wyłączasz zaznaczając
   przedmioty w **Settings → Devices & Services → Librus → Configure →
   "Wybrane przedmioty"** (multi-select).

Nowe ficzery dostępne od v3.0:
- 8 nowych sensorów: `latest_grade`, `latest_message`, `latest_announcement`,
  `latest_absence`, `next_exam`, `frekwencja` (% obecności),
  `nieobecnosci` (z listami dat), `ogloszenia`.
- 5 event entities: `event.<dziecko>_new_grade/_message/_exam/
  _announcement/_absence` — z payloadem w atrybutach state, perystencja
  w historii HA.
- 2 nowe kalendarze: `calendar.<dziecko>_obecnosci` (z tagami
  `[NIEOBECNOSC]/[SPOZNIENIE]/[USPRAWIEDLIWIONA]/[ZWOLNIENIE]/...`)
  oraz `calendar.<dziecko>_oceny` (`[OCENA 5]/[OCENA 4+]/[OCENA OPISOWA]`).
- Per-subject sensory wystawiają w atrybutach `grade_details` z kompletnym
  kontekstem każdej oceny (data/kategoria/waga/opis nauczyciela).

## 1. Bus eventy → Event entities

Z bus eventu `librus_apix_*` migrujesz na trigger po `state` event entity.
State zmienia się gdy trafia nowe zdarzenie; payload jest w atrybutach.

| v2.x | v3.0 |
|---|---|
| `event_type: librus_apix_new_grade` | `entity_id: event.<dziecko>_new_grade` |
| `event_type: librus_apix_new_message` | `entity_id: event.<dziecko>_new_message` |
| `event_type: librus_apix_new_exam` | `entity_id: event.<dziecko>_new_exam` |

Plus **nowe** event entities (nie miały odpowiednika w v2):
- `event.<dziecko>_new_announcement` — nowe ogłoszenie szkoły.
- `event.<dziecko>_new_absence` — nowa nieobecność/spóźnienie.

### Przykład — automation „nowa ocena"

#### v2.x (DZIAŁA, ale firowanie znika w v3.0)

```yaml
- alias: "Librus - new grade"
  trigger:
    platform: event
    event_type: librus_apix_new_grade
  action:
    - service: notify.mobile_app_telefon
      data:
        title: "🎓 {{ trigger.event.data.grade }}"
        message: "{{ trigger.event.data.subject }} - {{ trigger.event.data.category }}"
```

#### v3.0

```yaml
- alias: "Librus - new grade"
  trigger:
    platform: state
    entity_id: event.jan_kowalski_new_grade
  action:
    - service: notify.mobile_app_telefon
      data:
        title: "🎓 {{ state_attr('event.jan_kowalski_new_grade', 'grade') }}"
        message: >
          {{ state_attr('event.jan_kowalski_new_grade', 'subject') }}
          - {{ state_attr('event.jan_kowalski_new_grade', 'category') }}
```

Zaleta state-based: w UI widać kiedy ostatnio fired (state), historię w
HA Statistics, dashboard cards działają natywnie bez template'u.

## 2. Atrybuty `next_*` na sensorze `zapowiedzi` → `sensor.next_exam`

| v2.x | v3.0 zamiennik |
|---|---|
| `state_attr('sensor.<dziecko>_zapowiedzi', 'next_date')` | `state_attr('sensor.<dziecko>_next_exam', 'date')` |
| `state_attr('sensor.<dziecko>_zapowiedzi', 'next_subject')` | `state_attr('sensor.<dziecko>_next_exam', 'subject')` |
| `state_attr('sensor.<dziecko>_zapowiedzi', 'next_title')` | `state_attr('sensor.<dziecko>_next_exam', 'title')` |
| `state_attr('sensor.<dziecko>_zapowiedzi', 'next_category')` | `state_attr('sensor.<dziecko>_next_exam', 'category')` |
| `state_attr('sensor.<dziecko>_zapowiedzi', 'next_days_until')` | `states('sensor.<dziecko>_next_exam')` (state = liczba dni) |

`sensor.<dziecko>_next_exam` ma `state_class=measurement` i jednostkę
`d` — wykres w HA Statistics pokazuje "ile dni do najbliższego sprawdzianu"
w czasie.

## 3. Per-subject sensory enabled by default

W v2.x każdy `sensor.librus_<dziecko>_<przedmiot>` był disabled — user musiał
ręcznie włączać. W v3.0:

- Nowe instalacje: wszystkie przedmioty włączone od razu.
- Istniejące instalacje: entity registry zachowuje twój `disabled_by` stan.
- Kontrola wyboru: **Settings → Devices & Services → Librus → Configure →
  "Wybrane przedmioty"**. Odznacz przedmiot → reload integracji →
  encja znika z registry.

## 4. Nowy ficzer: per-subject `grade_details`

Atrybuty `sensor.librus_<dziecko>_<przedmiot>` i
`sensor.librus_<dziecko>_srednia_<przedmiot>` zawierają teraz pole
`grade_details`: lista każdej oceny z pełnym kontekstem.

```yaml
{% set details = state_attr('sensor.librus_jan_matematyka', 'grade_details') %}
{% for g in details %}
- {{ g.date }}: {{ g.grade }} ({{ g.category }}, waga {{ g.weight }})
  {% if g.description %}— {{ g.description }}{% endif %}
{% endfor %}
```

Pola: `grade`, `value`, `date`, `category`, `description`, `weight`, `counts`,
`teacher`, `title`, `is_recent`.

---

# Migracja v1.x → v2.0

⚠️ **v2.0.0 zawiera breaking changes w publicznym API.** Wszystkie nazwy
custom events, kluczy event payload i atrybutów encji zostały przemianowane
z polskich na angielskie. Trzeba przepisać automatyzacje i template'y.

Zalecana ścieżka: zaktualizuj integrację → otwórz Developer Tools → States,
sprawdź atrybuty swoich encji `sensor.librus_*` po nowych nazwach → przepisz
swoje automatyzacje.

## Custom events

| v1.x | v2.0 |
|---|---|
| `librus_apix_nowa_wiadomosc` | `librus_apix_new_message` |
| `librus_apix_nowa_ocena` | `librus_apix_new_grade` |
| `librus_apix_nowa_zapowiedz` | `librus_apix_new_exam` |

## Event data (payload kluczy)

### `librus_apix_new_message`

| v1.x | v2.0 |
|---|---|
| `nadawca` | `sender` |
| `temat` | `title` |
| `data` | `date` |
| `ma_zalacznik` | `has_attachment` |

### `librus_apix_new_grade`

| v1.x | v2.0 |
|---|---|
| `przedmiot` | `subject` |
| `ocena` | `grade` |
| `data` | `date` |
| `kategoria` | `category` |
| `nauczyciel` | `teacher` |

### `librus_apix_new_exam`

| v1.x | v2.0 |
|---|---|
| `tytul` | `title` |
| `przedmiot` | `subject` |
| `kategoria` | `category` |
| `data` | `date` |
| `godzina` | `time` |
| `dni_do` | `days_until` |

## Atrybuty encji

### `sensor.librus_<dziecko>_uczen` (Student information)

| v1.x | v2.0 |
|---|---|
| `klasa` | `class_name` |
| `numer_w_klasie` | `class_number` |
| `wychowawca` | `homeroom_teacher` |
| `szkola` | `school` |
| `szczesliwy_numerek` | `lucky_number` |

### `sensor.librus_<dziecko>_oceny` (Grades)

| v1.x | v2.0 |
|---|---|
| `oceny_wg_przedmiotu` | `grades_by_subject` |
| `liczba_ocen` | `grade_count` |
| `liczba_przedmiotow` | `subject_count` |
| `sa_nowe_oceny` | `has_new_grades` |
| `semestr` | `semester` |

W każdym slowniku wewnątrz `grades_by_subject[subject]`:

| v1.x | v2.0 |
|---|---|
| `ocena` | `grade` |
| `data` | `date` |
| `kategoria` | `category` |
| `nauczyciel` | `teacher` |
| `semestr` | `semester` |
| `jest_nowa` | `is_recent` |

### `sensor.librus_<dziecko>_srednia_ocen` (Overall average)

| v1.x | v2.0 |
|---|---|
| `srednie_wg_przedmiotow` | `averages_by_subject` |
| `semestr` | `semester` |

### `sensor.librus_<dziecko>_wiadomosci` (Messages)

| v1.x | v2.0 |
|---|---|
| `wiadomosci` | `messages` |
| `liczba_nieprzeczytanych` | `unread_count` |
| `sa_nowe_wiadomosci` | `has_new_messages` |

W każdym slowniku wewnątrz `messages`:

| v1.x | v2.0 |
|---|---|
| `nadawca` | `sender` |
| `temat` | `title` |
| `data` | `date` |
| `nieprzeczytana` | `unread` |
| `jest_nowa` | `is_recent` |
| `ma_zalacznik` | `has_attachment` |

### `sensor.librus_<dziecko>_zapowiedzi` (Upcoming exams)

| v1.x | v2.0 |
|---|---|
| `zapowiedzi` | `exams` |
| `liczba_w_3_dni` | `count_in_3_days` |
| `liczba_w_7_dni` | `count_in_7_days` |
| `liczba_w_14_dni` | `count_in_14_days` |
| `liczba_lacznie` | `total_count` |
| `najblizsza_data` | `next_date` |
| `najblizszy_przedmiot` | `next_subject` |
| `najblizszy_tytul` | `next_title` |
| `najblizsza_kategoria` | `next_category` |
| `najblizsza_dni_do` | `next_days_until` |

### `sensor.librus_<dziecko>_<przedmiot>` (Per-subject grades)

| v1.x | v2.0 |
|---|---|
| `oceny` | `grades` |
| `lista_ocen` | `grade_list` |
| `srednia` | `average` |
| `najnowsza_ocena` | `latest_grade` |
| `sa_nowe_oceny` | `has_new_grades` |

### `sensor.librus_<dziecko>_srednia_<przedmiot>` (Per-subject average)

| v1.x | v2.0 |
|---|---|
| `przedmiot` | `subject` |
| `lista_ocen` | `grade_list` |
| `liczba_ocen` | `grade_count` |

## Co NIE zmieniło się

- **`entity_id`** — Twoje encje zachowały `sensor.librus_<dziecko>_oceny`,
  `sensor.librus_<dziecko>_wiadomosci` itp. Historia danych jest zachowana.
- **Tagi w summary kalendarza** — `[SPRAWDZIAN]`, `[KARTKOWKA]`, `[WOLNE]`
  itd. dalej polskie. Filtry regex w automatyzacjach działają bez zmian.
- **Friendly names w UI** — z translation_key + `pl.json` nadal po polsku.
- **Domena (`librus_apix`)** — bez zmian.

## Przykład: powiadomienie o nowej ocenie

### v1.x

```yaml
- alias: "Librus - nowa ocena"
  trigger:
    platform: event
    event_type: librus_apix_nowa_ocena
  action:
    - service: notify.mobile_app_telefon
      data:
        title: "🎓 {{ trigger.event.data.ocena }}"
        message: "{{ trigger.event.data.przedmiot }} - {{ trigger.event.data.kategoria }}"
```

### v2.0

```yaml
- alias: "Librus - new grade"
  trigger:
    platform: event
    event_type: librus_apix_new_grade
  action:
    - service: notify.mobile_app_telefon
      data:
        title: "🎓 {{ trigger.event.data.grade }}"
        message: "{{ trigger.event.data.subject }} - {{ trigger.event.data.category }}"
```

## Przykład: template z atrybutu encji

### v1.x

```yaml
{% set msg = state_attr('sensor.librus_jan_wiadomosci', 'wiadomosci')[0] %}
Od: {{ msg.nadawca }}
Temat: {{ msg.temat }}
```

### v2.0

```yaml
{% set msg = state_attr('sensor.librus_jan_wiadomosci', 'messages')[0] %}
Od: {{ msg.sender }}
Temat: {{ msg.title }}
```

---

# Migracja v3.0 → v3.1

v3.1.0 jest **w pełni additive** — żadne istniejące encje, atrybuty ani eventy nie znikają ani się nie zmieniają. Wystarczy zaktualizować integrację przez HACS.

**Wymaga HA 2024.2.0+** (service `fetch_message_content` używa `SupportsResponse.ONLY`).

## Nowe ficzery v3.1

### Lokalny mark-as-read

Trzy nowe serwisy zarządzają lokalną flagą `is_read_in_ha` per wiadomość:

```yaml
# Oznacz jako przeczytaną (stan przeżywa restart HA; nie wpływa na Librusa)
service: librus_apix.mark_message_read
data:
  entry: "TWÓJ_ENTRY_ID"
  message_href: "12345"

# Cofnij oznaczenie
service: librus_apix.mark_message_unread
data:
  entry: "TWÓJ_ENTRY_ID"
  message_href: "12345"

# Wyczyść wszystkie flagi dla konta
service: librus_apix.clear_read_messages
data:
  entry: "TWÓJ_ENTRY_ID"
```

`message_href` to numeryczny ID widoczny w atrybucie sensora wiadomości:
```
{{ state_attr('sensor.librus_jan_wiadomosci', 'messages')[0].href }}
```

### Nowe atrybuty sensora wiadomości

`sensor.<dziecko>_wiadomosci` ma teraz:
- `messages[].href` — numeryczny ID wiadomości
- `messages[].is_read_in_ha` — lokalnie oznaczona jako przeczytana
- `unread_count_locally` — liczba nieprzeczytanych po odjęciu lokalnie oznaczonych

`sensor.<dziecko>_latest_message` analogicznie: `href` + `is_read_in_ha`.

### Pobieranie treści wiadomości

```yaml
service: librus_apix.fetch_message_content
data:
  entry: "TWÓJ_ENTRY_ID"
  message_href: "12345"
response_variable: tresc
```

Zwraca `{content, author, title, date}` gdzie `content` to inner HTML treści wiadomości.

> **UWAGA PRIVACY:** pobranie treści SERVER-SIDE oznacza wiadomość jako przeczytaną
> w Librusie (efekt uboczny Librusa — nie do uniknięcia). Drugi rodzic na osobnym
> koncie Librus nie jest dotknięty. Service automatycznie ustawia też `is_read_in_ha=True`.

### Baner powiadomień (opt-in)

W **Settings → Devices & Services → Librus → Configure** pojawia się checkbox
**"Pokazuj baner powiadomienia przy nowej wiadomości"**.

Po włączeniu: każda nowa wiadomość (nie przy pierwszym uruchomieniu) tworzy
`persistent_notification` ze stabilnym ID — `mark_message_read` automatycznie go odrzuca.

### Flag `initial` w bus evencie

`librus_apix_nowa_wiadomosc` (nowy event, zastępuje legacy w automatyzacjach)
ma teraz pole `initial: bool`:
- `initial: true` — wiadomości istniejące przy starcie/restarcie HA
- `initial: false` — nowa wiadomość wykryta w trakcie działania

Użyj `condition: "{{ not trigger.event.data.initial }}"` żeby uniknąć powiadomień
przy każdym restarcie HA.
