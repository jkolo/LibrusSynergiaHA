# librus-messages-card

Niestandardowa karta Lovelace dla integracji [Librus Synergia HA](../).
Pokazuje listę wiadomości szkolnych z możliwością podglądu pełnej treści
i oznaczania jako przeczytane — bez opuszczania Home Assistant.

## Instalacja przez HACS

1. W HACS → Frontend → przycisk **+** → wyszukaj **Librus Synergia HA**
   (albo dodaj ręcznie: Custom Repositories → URL repo → kategoria **Lovelace**).
2. Zainstaluj.
3. Odśwież cache przeglądarki (Ctrl+Shift+R).

## Konfiguracja

```yaml
type: custom:librus-messages-card
entity: sensor.librus_jan_kowalski_wiadomosci
entry_id: 1234567890abcdef
```

### Gdzie znaleźć `entry_id`

Wejdź w **Settings → Devices & Services → Librus → (konto)** i skopiuj
ostatni segment z adresu URL (np. `/config/integrations/integration/librus_apix/entry/1234567890abcdef`).

### Opcje

| Klucz | Typ | Domyślnie | Opis |
|-------|-----|-----------|------|
| `entity` | string | wymagane | `sensor.<dziecko>_wiadomosci` |
| `entry_id` | string | wymagane | ID wpisu konfiguracyjnego Librus |
| `title` | string | `Wiadomości Librus` | Nagłówek karty |
| `only_unread` | bool | `false` | Pokaż tylko nieprzeczytane przy starcie |

## Funkcje

- Lista ostatnich wiadomości z nadawcą, tytułem i datą.
- Przycisk **Pokaż treść** — pobiera i wyświetla treść inline (HTML z Librusa po sanityzacji).
- Przycisk **Oznacz jako przeczytaną** — ustawia lokalną flagę `is_read_in_ha`.
- Filtr **tylko nieprzeczytane** — toggle per sesja.

> **Uwaga privacy:** kliknięcie „Pokaż treść" wywołuje `librus_apix.fetch_message_content`,
> który pobiera wiadomość z Librusa — to server-side oznacza ją jako przeczytaną
> w Librusie. Drugi rodzic na osobnym koncie nie jest dotknięty.
> Szczegóły: [MIGRATION.md](../MIGRATION.md).

## Wymagania

- Home Assistant 2024.2.0+
- Integracja `librus_apix` v3.1.0+

## Przykładowa automatyzacja

```yaml
automation:
  trigger:
    - platform: event
      event_type: librus_apix_nowa_wiadomosc
  condition:
    - condition: template
      value_template: "{{ not trigger.event.data.initial }}"
  action:
    - service: librus_apix.fetch_message_content
      data:
        entry: "TWÓJ_ENTRY_ID"
        message_href: "{{ trigger.event.data.href }}"
      response_variable: tresc
    - service: notify.mobile_app_telefon
      data:
        title: "Librus: {{ trigger.event.data.sender }}"
        message: "{{ tresc.content | striptags }}"
```
