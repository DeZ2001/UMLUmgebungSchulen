from js import window, document
from pyodide.ffi import create_proxy
import asyncio

# Zähler für eindeutige Diagramm-IDs
diagram_counter = 0

# Liste der Attribute und Methoden
# Liste von Dictionaries: {"type": "attribute"/"method", "visibility": "public"/"private"/"protected", "name": "name"}
items_list = []  

# Sichtbarkeitssymbole als Konstante
VISIBILITY_SYMBOLS = {"public": "+", "private": "-", "protected": "#"}

def generate_diagram(className):
    """Erzeugt das Mermaid-Diagramm basierend auf dem Klassennamen und den Items"""
    global items_list
    
    # Bestimme den Klassennamen
    if not className or className.strip() == "":
        clean_name = "PythonKlasse"
    else:
        clean_name = className.strip().replace(" ", "")
    
    # Erstelle den Diagramm-String
    diagram_lines = [f"classDiagram", f"    class {clean_name} {{"]
    
    # Füge Attribute hinzu
    attributes = [item for item in items_list if item.get("type") == "attribute"]
    if attributes:
        for attr in attributes:
            visibility_symbol = VISIBILITY_SYMBOLS.get(attr.get("visibility", "public"), "+")
            attr_name = attr.get("name", "").strip()
            if attr_name:
                diagram_lines.append(f"        {visibility_symbol}{attr_name}")
    
    # Füge Methoden hinzu
    methods = [item for item in items_list if item.get("type") == "method"]
    if methods:
        # Leerzeile zwischen Attributen und Methoden
        if attributes:
            diagram_lines.append("")
        for method in methods:
            visibility_symbol = VISIBILITY_SYMBOLS.get(method.get("visibility", "public"), "+")
            method_name = method.get("name", "").strip()
            if method_name:
                diagram_lines.append(f"        {visibility_symbol}{method_name}()")
    
    diagram_lines.append("    }")
    
    return "\n".join(diagram_lines)

def update_items_list():
    """Aktualisiert die Anzeige der Items-Liste mit editierbaren Feldern"""
    global items_list
    
    try:
        items_list_elem = document.getElementById("itemsList")
        if not items_list_elem:
            return
        
        if not items_list:
            items_list_elem.innerHTML = "<p style='color: #666; font-style: italic; padding: 1rem;'>Keine Attribute/Methoden hinzugefügt.</p>"
        for item_index, item in enumerate(items_list):
            item_type = item.get("type", "attribute")
            visibility = item.get("visibility", "public")
            item_name = item.get("name", "")
            
            # Escape quotes im Namen
            escaped_name = item_name.replace('"', '&quot;').replace("'", "&#39;")
            
            html += f"""
                    <div class="item-entry" id="item-entry-{i}">
                    <span class="item-label">Element {i+1}:</span>
                    <select id="item-type-{i}">
                        <option value="attribute" {"selected" if item_type == "attribute" else ""}>Attribut</option>
                        <option value="method" {"selected" if item_type == "method" else ""}>Methode</option>
                    </select>
                    <select id="item-visibility-{i}">
                        <option value="public" {"selected" if visibility == "public" else ""}>Public (+)</option>
                        <option value="private" {"selected" if visibility == "private" else ""}>Private (-)</option>
                        <option value="protected" {"selected" if visibility == "protected" else ""}>Protected (#)</option>
                    </select>
                <input type="text" id="item-name-{i}" value="{escaped_name}" />
                <button id="remove-btn-{i}" data-index="{i}" type="button">Entfernen</button>
                <button id="edit-btn-{i}" data-index="{i}" type="button">Bearbeiten</button>
            </div>
        """
        
        items_list_elem.innerHTML = html
        
        # Dictionary to store proxies for cleanup and memory management
        if not hasattr(update_items_list, "proxies"):
            update_items_list.proxies = {}
        proxies = update_items_list.proxies
        proxies.clear()

        # Füge Event-Listener zu allen neuen Elementen hinzu
        for i in range(len(items_list)):
            type_elem = document.getElementById(f"item-type-{i}")
            visibility_elem = document.getElementById(f"item-visibility-{i}")
            name_elem = document.getElementById(f"item-name-{i}")

            if type_elem:
                def make_type_handler(idx):
                    def handler(e):
                        update_item_field(idx, "type", e.target.value)
                    return handler
                type_proxy = create_proxy(make_type_handler(i))
                type_elem.addEventListener("change", type_proxy)
                type_elem.onchange = type_proxy
                proxies[f"type-{i}"] = type_proxy

            if visibility_elem:
                def make_visibility_handler(idx):
                    def handler(e):
                        update_item_field(idx, "visibility", e.target.value)
                    return handler
                visibility_proxy = create_proxy(make_visibility_handler(i))
                visibility_elem.addEventListener("change", visibility_proxy)
                visibility_elem.onchange = visibility_proxy
                proxies[f"visibility-{i}"] = visibility_proxy

            if name_elem:
                def make_name_handler(idx):
                    def handler(e):
                        update_item_field(idx, "name", e.target.value)
                    return handler
                name_proxy = create_proxy(make_name_handler(i))
                name_elem.addEventListener("input", name_proxy)
                name_elem.addEventListener("change", name_proxy)
            remove_btn = document.getElementById(f"remove-btn-{i}")
            if remove_btn:
                def make_remove_handler(idx):
                    def handler(e):
                        remove_item(idx)
                    return handler
                remove_proxy = create_proxy(make_remove_handler(i))
                remove_btn.addEventListener("click", remove_proxy)
                remove_btn.onclick = remove_proxy
                remove_btn._click_proxy = remove_proxy

            edit_btn = document.getElementById(f"edit-btn-{i}")
            if edit_btn:
                def make_edit_handler(idx):
                    def handler(e):
    """Aktualisiert ein einzelnes Feld eines Items"""
    global items_list
    try:
        if 0 <= index < len(items_list):
            items_list[index][field] = value
            # Update das Diagramm sofort
            update_diagram()
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Aktualisieren: {str(e)}"


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

def add_item():
    """Fügt ein neues Attribut oder eine Methode hinzu"""
    global items_list
    try:
        item_type_elem = document.getElementById("itemType")
        visibility_elem = document.getElementById("visibility")
        name_elem = document.getElementById("itemName")
        
        if not item_type_elem or not visibility_elem or not name_elem:
            return
        
        item_type = item_type_elem.value
        visibility = visibility_elem.value
        name = name_elem.value.strip()
        
        if not name:
            output = document.getElementById("out")
            if output:
                output.textContent = "Bitte geben Sie einen Namen ein."
            return
        
        # Füge das Item zur Liste hinzu
        new_item = {
            "type": item_type,
            "visibility": visibility,
            "name": name
        }
        items_list.append(new_item)
        
        # Leere das Eingabefeld
        name_elem.value = ""
        
        # Update die Items-Liste
        update_items_list()
        
        # Update das Diagramm
        update_diagram()
        
        output = document.getElementById("out")
        if output:
            output.textContent = f"{'Attribut' if item_type == 'attribute' else 'Methode'} '{name}' hinzugefügt."
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Hinzufügen: {str(e)}"

def remove_item(index):
    """Entfernt ein Item aus der Liste"""
    global items_list
    try:
        if 0 <= index < len(items_list):
            removed = items_list.pop(index)
            update_items_list()
            update_diagram()
            output = document.getElementById("out")
            if output:
                output.textContent = f"{'Attribut' if removed['type'] == 'attribute' else 'Methode'} '{removed['name']}' entfernt."
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Entfernen: {str(e)}"

def open_edit_modal(item_index):
    """Öffnet das Edit-Modal für ein bestimmtes Item"""
    global items_list
    try:
        if item_index < 0 or item_index >= len(items_list):
            return
        
        item = items_list[item_index]
        
        # Setze die Werte im Modal
        edit_type = document.getElementById("editType")
        edit_visibility = document.getElementById("editVisibility")
        edit_name = document.getElementById("editName")
        modal = document.getElementById("editModal")
        
        if edit_type and edit_visibility and edit_name and modal:
            edit_type.value = item.get("type", "attribute")
            edit_visibility.value = item.get("visibility", "public")
            edit_name.value = item.get("name", "")
            
            # Speichere den aktuellen Index im Modal
            modal.setAttribute("data-edit-index", str(item_index))
            
            # Öffne das Modal
            modal.classList.add("active")
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Öffnen des Modals: {str(e)}"

def close_edit_modal():
    """Schließt das Edit-Modal"""
    modal = document.getElementById("editModal")
    if modal:
        modal.classList.remove("active")

def save_item_from_modal():
    """Speichert Änderungen aus dem Modal"""
    global items_list
    try:
        modal = document.getElementById("editModal")
        if not modal:
            return
        
        item_index_str = modal.getAttribute("data-edit-index")
        if not item_index_str:
            return
        
        item_index = int(item_index_str)
        if item_index < 0 or item_index >= len(items_list):
            return
        
        edit_type = document.getElementById("editType")
        edit_visibility = document.getElementById("editVisibility")
        edit_name = document.getElementById("editName")
        
        if edit_type and edit_visibility and edit_name:
            items_list[item_index]["type"] = edit_type.value
            items_list[item_index]["visibility"] = edit_visibility.value
            items_list[item_index]["name"] = edit_name.value.strip()
            
            # Schließe das Modal
            close_edit_modal()
            
            # Update das Diagramm
            update_diagram()
            
            output = document.getElementById("out")
            if output:
                output.textContent = "Änderungen gespeichert!"
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Speichern: {str(e)}"

def delete_item_from_modal():
    """Löscht ein Item aus dem Modal"""
    global items_list
    try:
        modal = document.getElementById("editModal")
        if not modal:
            return
        
        item_index_str = modal.getAttribute("data-edit-index")
        if not item_index_str:
            return
        
        item_index = int(item_index_str)
        if item_index < 0 or item_index >= len(items_list):
            return
        
        # Entferne das Item
        removed = items_list.pop(item_index)
        
        # Schließe das Modal
        close_edit_modal()
        
        # Update das Diagramm
        update_diagram()
        
        output = document.getElementById("out")
        if output:
            output.textContent = f"{'Attribut' if removed['type'] == 'attribute' else 'Methode'} '{removed['name']}' wurde gelöscht."
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Löschen: {str(e)}"

def update_item_field(index, field, value):
    """Aktualisiert ein einzelnes Feld eines Items"""
    global items_list
    try:
        if 0 <= index < len(items_list):
            items_list[index][field] = value
            # Update das Diagramm sofort
            update_diagram()
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Aktualisieren: {str(e)}"

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

def on_item_name_keypress(event):
    """Callback-Funktion für Enter-Taste im Item-Name-Feld"""
    try:
        if event.key == "Enter":
            event.preventDefault()
            add_item()
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler in on_item_name_keypress: {str(e)}"

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
    
    # Füge Event-Listener für Item-Hinzufügen hinzu
    try:
        add_item_btn = document.getElementById("addItemBtn")
        item_name_input = document.getElementById("itemName")
        
        if add_item_btn:
            def add_item_wrapper(e):
                add_item()
            add_item_proxy = create_proxy(add_item_wrapper)
            add_item_btn.addEventListener("click", add_item_proxy)
            add_item_btn.onclick = add_item_proxy
            add_item_btn._click_proxy = add_item_proxy
        
        if item_name_input:
            item_name_keypress_proxy = create_proxy(on_item_name_keypress)
            item_name_input.addEventListener("keypress", item_name_keypress_proxy)
            item_name_input.onkeypress = item_name_keypress_proxy
            item_name_input._keypress_proxy = item_name_keypress_proxy
        
        # Initialisiere die Items-Liste
        update_items_list()

        
        
        # Initialisiere Modal-Event-Listener
        modal = document.getElementById("editModal")
        save_btn = document.getElementById("saveBtn")
        cancel_btn = document.getElementById("cancelBtn")
        delete_btn = document.getElementById("deleteBtn")
        
        if save_btn:
            def save_handler(e):
                save_item_from_modal()
            save_proxy = create_proxy(save_handler)
            save_btn.addEventListener("click", save_proxy)
            save_btn.onclick = save_proxy
            save_btn._click_proxy = save_proxy
        
        if cancel_btn:
            def cancel_handler(e):
                close_edit_modal()
            cancel_proxy = create_proxy(cancel_handler)
            cancel_btn.addEventListener("click", cancel_proxy)
            cancel_btn.onclick = cancel_proxy
            cancel_btn._click_proxy = cancel_proxy
        
        if delete_btn:
            def delete_handler(e):
                delete_item_from_modal()
            delete_proxy = create_proxy(delete_handler)
            delete_btn.addEventListener("click", delete_proxy)
            delete_btn.onclick = delete_proxy
            delete_btn._click_proxy = delete_proxy
        
        # Schließe Modal bei Klick außerhalb
        if modal:
            def modal_click_handler(e):
                if e.target == modal:
                    close_edit_modal()
            modal_proxy = create_proxy(modal_click_handler)
            modal.addEventListener("click", modal_proxy)
            modal.onclick = modal_proxy
            modal._click_proxy = modal_proxy
    except Exception as e:
        if output:
            output.textContent = f"Fehler beim Initialisieren der Items: {str(e)}"
    
    # Rendere initial ein leeres Diagramm
    await render_uml("")
    
    # Update Output
    if output:
        output.textContent = "Bereit! Klicken Sie im UML-Diagramm auf Attribute/Methoden zum Bearbeiten."

# Warte kurz, damit das DOM vollständig geladen ist
async def delayed_init():
    await asyncio.sleep(0.5)  # Warte 0.5 Sekunden
    await init()

# Starte die Initialisierung
asyncio.ensure_future(delayed_init())