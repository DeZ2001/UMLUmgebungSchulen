# UML Klassenmodellierung (PyScript)

Browserbasierter UML Klasseneditor mit Live-Generierung von Python-Code.  
Stack: `index.html` + `styles.css` + `drag.js` + `main.py` (PyScript/Pyodide).

## Lokaler Start

macOS:

```bash
python3 -m http.server
```

Windows (PowerShell):

```powershell
py -m http.server
```

Windows (CMD, falls `py` nicht verfuegbar):

```bat
python -m http.server
```

Dann im Browser:

```text
http://localhost:8000/index.html
```

## Aktuelle Bedienlogik (wichtig)

### 1) UML Panel verschieben

- Das UML Panel (`#umlDiagram`) kann per Drag verschoben werden.
- Der Drag startet nur, wenn direkt das Container-Element getroffen wird (`e.target === #umlDiagram`).
- Praktisch bedeutet das: Ziehen funktioniert im Rand-/Padding-Bereich des UML Panels, nicht auf Inputs/Buttons innerhalb der Klasse.
- Position wird in `localStorage` unter `umlPosition` gespeichert.
- Button `Position zuruecksetzen` setzt die Position auf `(0,0)` und loescht `umlPosition`.
- Nach JSON-Import wird `umlPosition` ebenfalls geloescht.

### 2) Sortierung innerhalb einer Klasse

- Attribute und Methoden sind als sortierbare Listen umgesetzt.
- Reihenfolge wird per Drag-and-Drop geaendert.
- Sortierung ist nur innerhalb derselben Klasse und desselben Typs erlaubt:
  - Attribut nur in Attributliste
  - Methode nur in Methodenliste
- Konstruktoren (`c __init__...`) bleiben oben und werden nicht frei zwischen normalen Methoden einsortiert.

### 3) Bearbeiten / Ansicht

- `Bearbeitungsmodus`: UML voll editierbar.
- `Ansichtsmodus`: UML Felder readonly gerendert.
- `Code ein/ausblenden`: zeigt/versteckt die Python-Code-Seite.

## UML und Code-Generierung

- Zugriffsbuttons: `+`, `-`, `#`
- Konstruktor-Erkennung ueber Prefix `c __init__`
- Getter/Setter:
  - Erzeugung ueber `g` / `s` Button pro Attribut
  - Buttons werden deaktiviert, wenn passende Methode schon existiert
- Generierter Python-Code wird live im rechten Panel aktualisiert.

## JSON Export / Import

- Export als JSON in Modal (kopieren oder Datei herunterladen)
- Import per Textfeld oder Datei-Upload
- Erwartetes Format:

```json
{
  "umlClasses": [
    {
      "id": 1,
      "name": "ClassName",
      "attributes": [
        { "id": 1, "attr": "name:str", "access": "+" }
      ],
      "methods": [
        { "id": 1, "methode": "c __init__(name:str)", "access": "" }
      ]
    }
  ]
}
```

## Projektdateien

- `index.html`: Layout, Toolbar, Modal, Script-Einbindung
- `styles.css`: UI-Styling, responsive Regeln, Tooltip, Drag-Zustandsstile
- `drag.js`: Panel-Drag inkl. Persistenz
- `main.py`: Rendering, Event-Handling, Sortierung, Code-Generierung, JSON Import/Export
