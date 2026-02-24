# UML Class Designer (PyScript)

A lightweight, browser-based UML class diagram editor that generates Python class code in real time. Built with PyScript (Python in the browser), plain HTML/CSS, and a small drag helper.

## What it does

- Create UML classes with attributes and methods
- Set access modifiers (`+`, `-`, `#`)
- Auto-sync constructors with attributes
- Auto-generate getter/setter method bodies
- Generate formatted Python code alongside the diagram
- Toggle between edit and view modes
- Export/import the diagram state as JSON
- Drag the UML panel and persist its position in `localStorage`

## How it works

- **`index.html`** loads PyScript, the UI layout, and the drag handler.
- **`main.py`** renders UML cards, handles UI events, and generates Python code.
- **`drag.js`** enables dragging the UML panel and saves its position.
- **`styles.css`** styles the editor, code panel, and modal dialogs.

## Run locally

Because PyScript loads resources via ES modules, you should serve the project with a local web server.

```bash
python3 -m http.server
```

Then open:

```
http://localhost:8000/index.html
```

## Usage

1. Enter a class name, then add attributes and methods.
2. Use access buttons (`+`, `-`, `#`) to set visibility.
3. Add `c __init__(...)` to create a constructor; attributes are synced automatically.
4. To move the UML diagram, click and drag only on empty space in the outer dashed area around the classes.
5. Toggle the code panel with the code icon.
6. Export or import JSON via the toolbar.

## Drag Zone

- You can drag the UML diagram only from the empty outer padded area of `#umlDiagram` (the dashed/hover-highlighted border zone around class cards).
- You cannot start dragging from class cards, inputs, buttons, or method/attribute rows; those areas are for editing and sorting.
- On hover, the zone gets a highlighted dashed border and pulse effect (`.edge-hover`) to show it is draggable.
- The panel position is persisted in `localStorage` under `umlPosition` and restored on reload.
- Use the reset control (`#resetSvg`) to return the panel to `(0, 0)` and clear the saved position.

## Data format (export/import)

The editor exports a JSON object like:

```json
{
  "umlClasses": [
    {
      "id": 1,
      "name": "ClassName",
      "attributes": [{ "id": 1, "attr": "name:str", "access": "+" }],
      "methods": [{ "id": 1, "methode": "get_name():str", "access": "+" }]
    }
  ]
}
```

## Notes

- Constructor methods are recognized by the prefix `c __init__`.
- Getter/setter methods are detected by name (`get_` / `set_`) and generate bodies automatically.
- The drag position is saved in `localStorage` under `umlPosition`.

## License

Add your license here.
