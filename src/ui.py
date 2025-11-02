from js import window, document
import asyncio

# Zähler für eindeutige Diagramm-IDs
diagram_counter = 0

def generate_diagram(className):
    """Erzeugt das Mermaid-Diagramm basierend auf dem Klassennamen"""
    if not className or className.strip() == "":
        # Leere Klasse ohne Inhalt (Platzhalter-Name)
        return """
classDiagram
    class Klasse {
    }
"""
    else:
        # Klasse mit dem eingegebenen Namen (leer, nur der Name)
        clean_name = className.strip()
        # Entferne Leerzeichen und Sonderzeichen, die Mermaid nicht mag
        clean_name = clean_name.replace(" ", "")
        return f"""
classDiagram
    class {clean_name} {{
    }}
"""

async def render_uml(className=""):
    """Rendert das UML-Diagramm mit dem gegebenen Klassennamen"""
    # Warte bis Mermaid verfügbar ist
    max_wait = 50  # 5 Sekunden
    wait_count = 0
    while not hasattr(window, 'mermaid') or window.mermaid is None:
        await asyncio.sleep(0.1)
        wait_count += 1
        if wait_count > max_wait:
            output = document.getElementById("out")
            output.textContent = "Fehler: Mermaid konnte nicht geladen werden"
            return
    
    try:
        global diagram_counter
        diagram_counter += 1
        diagram_id = f"uml-diagram-{diagram_counter}"
        
        # Generiere das Diagramm
        diagram = generate_diagram(className)
        
        # Rendere das UML-Diagramm
        result = await window.mermaid.render(diagram_id, diagram)
        container = document.getElementById("uml")
        container.innerHTML = result.svg
        
        # Update Output
        output = document.getElementById("out")
        if className and className.strip():
            output.textContent = f"Klasse '{className.strip()}' wurde erfolgreich geladen!"
        else:
            output.textContent = "Leere Klasse angezeigt. Geben Sie einen Klassennamen ein."
    except Exception as e:
        output = document.getElementById("out")
        output.textContent = f"Fehler beim Rendern: {str(e)}"

def update_diagram():
    """Liest den Klassennamen aus dem Input und rendert das Diagramm"""
    try:
        input_element = document.getElementById("className")
        if input_element:
            className = input_element.value
            # Debug-Ausgabe
            output = document.getElementById("out")
            if output:
                output.textContent = f"Update Diagramm mit Klasse: '{className}'..."
            # Starte das Rendern
            asyncio.ensure_future(render_uml(className))
        else:
            output = document.getElementById("out")
            if output:
                output.textContent = "Fehler: Input-Element nicht gefunden"
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler in update_diagram: {str(e)}"

def on_class_name_change(event):
    """Callback-Funktion für Input-Änderungen (optional - live update)"""
    try:
        update_diagram()
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler in on_class_name_change: {str(e)}"

def on_submit_click(event=None):
    """Callback-Funktion für Submit-Button"""
    try:
        output = document.getElementById("out")
        if output:
            output.textContent = "Button geklickt - Update Diagramm..."
        update_diagram()
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler in on_submit_click: {str(e)}"

def on_input_keypress(event):
    """Callback-Funktion für Enter-Taste im Input-Feld"""
    try:
        if event.key == "Enter":
            event.preventDefault()
            update_diagram()
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler in on_input_keypress: {str(e)}"

async def init():
    """Initialisiert die Anwendung"""
    # Warte bis das Input-Element verfügbar ist
    max_wait = 50
    wait_count = 0
    
    input_element = None
    submit_button = None
    
    output = document.getElementById("out")
    if output:
        output.textContent = "Initialisiere..."
    
    while True:
        input_element = document.getElementById("className")
        submit_button = document.getElementById("submitBtn")
        if input_element and submit_button:
            break
        await asyncio.sleep(0.1)
        wait_count += 1
        if wait_count > max_wait:
            if output:
                output.textContent = "Fehler: UI-Elemente konnten nicht gefunden werden"
            return
    
    # Füge Event-Listener hinzu
    try:
        input_element.addEventListener("input", on_class_name_change)
        input_element.addEventListener("keypress", on_input_keypress)
        # Button-Event auch programmatisch hinzufügen (Fallback)
        submit_button.addEventListener("click", on_submit_click)
        # Zusätzlich: Setze onclick direkt für bessere Kompatibilität
        submit_button.onclick = on_submit_click
        
        if output:
            output.textContent = "Event-Listener registriert..."
    except Exception as e:
        if output:
            output.textContent = f"Fehler beim Registrieren der Event-Listener: {str(e)}"
        return
    
    # Rendere initial ein leeres Diagramm
    await render_uml("")
    
    # Update Output
    if output:
        output.textContent = "Bereit! Geben Sie einen Klassennamen ein und klicken Sie auf 'Übernehmen' oder drücken Sie Enter."

# Warte kurz, damit das DOM vollständig geladen ist
async def delayed_init():
    await asyncio.sleep(0.5)  # Warte 0.5 Sekunden
    await init()

# Starte die Initialisierung
asyncio.ensure_future(delayed_init())