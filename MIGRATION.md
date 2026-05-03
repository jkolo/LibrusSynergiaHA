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
