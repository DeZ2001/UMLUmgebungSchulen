# UML Class Modeling (PyScript)

Browser-based UML class editor with live Python code generation.  
Stack: `index.html` + `styles.css` + `drag.js` + `main.py` (PyScript/Pyodide).

## Local Start

macOS:

```bash
python3 -m http.server
```

Windows (PowerShell):

```powershell
py -m http.server
```

Windows (CMD, if `py` is not available):

```bat
python -m http.server
```

Port note:

- Default port is `8000`.
- Custom port example (`8080`):

```bash
python3 -m http.server 8080
```

```powershell
py -m http.server 8080
```

Then open in your browser:

```text
http://localhost:8000/index.html
```

If you started the server with a custom port, use the same port in the URL.
Example for port `8080`:

```text
http://localhost:8080/index.html
```

## Open-Source Packages and Dependencies

This project is intentionally built with open-source dependencies only.

| Component | Version / Source | Used In | Purpose | License |
|---|---|---|---|---|
| PyScript | `2024.2.1` via `https://pyscript.net/releases/2024.2.1/core.js` and `core.css` | `index.html` | Run Python directly in the browser (`<py-script>`) | Open source (see upstream `LICENSE`) |
| Pyodide (runtime used by PyScript) | Included through the PyScript runtime | `main.py` (`from pyodide.ffi import create_proxy`) | Python runtime + JS/Python bridge in WebAssembly | Open source (see upstream `LICENSE`) |
| Python Standard Library | Built into Python (`json`, `math`, `http.server`) | `main.py`, local start commands | Data handling, calculations, local web server | PSF License |
| Browser Web APIs | Built into browser (`DOM`, `localStorage`, `FileReader`, `Clipboard API`) | `main.py`, `drag.js` | UI events, persistence, file import, clipboard fallback | Web standards (no extra package) |

Notes:

- No additional `pip` or `npm` packages are required for this project.
- Toolbar SVG icons in `button/` are third-party assets (`*-svgrepo-com.svg`) and should be documented with their exact source URLs and licenses for final distribution.

## Current Interaction Logic (Important)

### 1) Move UML Panel

- The UML panel (`#umlDiagram`) can be moved by dragging.
- Drag only starts when the container itself is the event target (`e.target === #umlDiagram`).
- In practice: dragging works in the panel border/padding area, not on inputs or buttons inside UML cards.
- Position is stored in `localStorage` under `umlPosition`.
- The `Position zuruecksetzen` button resets to `(0,0)` and clears `umlPosition`.
- After JSON import, `umlPosition` is also cleared.

### 2) Sorting Inside a Class

- Attributes and methods are implemented as sortable lists.
- Order is changed via drag-and-drop.
- Sorting is only allowed within the same class and same item type.
- Attribute items can only be dropped in the attribute list.
- Method items can only be dropped in the method list.
- Constructors (`c __init__...`) stay at the top and are not freely mixed with regular methods.

### 3) Edit / View Modes

- `Bearbeitungsmodus`: UML is fully editable.
- `Ansichtsmodus`: UML fields are rendered as readonly.
- `Code ein/ausblenden`: shows/hides the Python code panel.

## UML and Code Generation

- Access buttons: `+`, `-`, `#`
- Constructor detection by prefix `c __init__`
- Getter/Setter are generated via `g` / `s` buttons per attribute.
- Buttons are disabled when a matching method already exists.
- Generated Python code updates live in the right panel.

## JSON Export / Import

- Export JSON in a modal (copy or download as file).
- Import via textarea or file upload.
- Expected format:

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

## Project Files

- `index.html`: layout, toolbar, modal, script loading
- `styles.css`: UI styling, responsive rules, tooltips, drag states
- `drag.js`: panel dragging and persistence
- `main.py`: rendering, event handling, sorting, code generation, JSON import/export
