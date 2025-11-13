from typing import Any
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
                datatype = attr.get("datatype", "").strip()
                line = f"        {visibility_symbol}{attr_name}"
                if datatype:
                    # Mermaid rendert besser ohne Leerzeichen: "name: type"
                    # Das Leerzeichen wird dann durch die Buttons hinzugefügt
                    line += f": {datatype}"
                diagram_lines.append(line)
    
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
                return_type = method.get("datatype", "").strip()
                line = f"{visibility_symbol}{method_name}()"
                if return_type:
                    # Mermaid rendert besser ohne Leerzeichen: "methodName(): returnType"
                    # Das Leerzeichen wird dann durch die Buttons hinzugefügt
                    line += f"{return_type}"
                diagram_lines.append(line)
    
    diagram_lines.append("    }")
    
    return "\n".join(diagram_lines)

def update_items_list():
    """Aktualisiert die Anzeige der Items-Liste mit editierbaren Feldern"""
    global items_list

    try:
        items_list_elem = document.getElementById("itemsList")
        if not items_list_elem:
            return

        # Wenn leer: Hinweis zeigen und fertig
        if not items_list:
            items_list_elem.innerHTML = (
                "<p style='color: #666; font-style: italic; padding: 1rem;'>"
                "Keine Attribute/Methoden hinzugefügt.</p>"
            )
            return

        # HTML neu aufbauen
        html = ""
        for i, item in enumerate(items_list):
            item_type = item.get("type", "attribute")
            visibility = item.get("visibility", "public")
            item_name = item.get("name", "")
            datatype = item.get("datatype", "")

            escaped_name = (
                item_name.replace('"', '&quot;').replace("'", "&#39;")
            )
            escaped_datatype = (
                datatype.replace('"', '&quot;').replace("'", "&#39;")
            )

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
                    <input type="text" id="item-datatype-{i}" value="{escaped_datatype}" placeholder="Datentyp" />
                    <button id="remove-btn-{i}" data-index="{i}" type="button">Entfernen</button>
                    <button id="edit-btn-{i}" data-index="{i}" type="button">Bearbeiten</button>
                </div>
            """

        # Re-Render
        items_list_elem.innerHTML = html

        # Proxies-Container (gegen GC)
        if not hasattr(update_items_list, "proxies"):
            update_items_list.proxies = {}
        old_proxies = update_items_list.proxies.copy()  # Kopie der alten Proxies
        proxies = {}
        
        # Event-Listener neu binden
        for i in range(len(items_list)):
            # Typ ändern
            type_elem = document.getElementById(f"item-type-{i}")
            if type_elem:
                def make_type_handler(idx):
                    def handler(e):
                        update_item_field(idx, "type", e.target.value)
                    return handler
                p = create_proxy(make_type_handler(i))
                type_elem.addEventListener("change", p)
                type_elem.onchange = p
                proxies[f"type-{i}"] = p

            # Sichtbarkeit ändern
            visibility_elem = document.getElementById(f"item-visibility-{i}")
            if visibility_elem:
                def make_visibility_handler(idx):
                    def handler(e):
                        update_item_field(idx, "visibility", e.target.value)
                    return handler
                p = create_proxy(make_visibility_handler(i))
                visibility_elem.addEventListener("change", p)
                visibility_elem.onchange = p
                proxies[f"visibility-{i}"] = p

            # Name ändern
            name_elem = document.getElementById(f"item-name-{i}")
            if name_elem:
                def make_name_handler(idx):
                    def handler(e):
                        update_item_field(idx, "name", e.target.value)
                    return handler
                p = create_proxy(make_name_handler(i))
                name_elem.addEventListener("input", p)
                name_elem.addEventListener("change", p)
                proxies[f"name-{i}"] = p
            
            #Entfernen-Button need check ???
            datatype_elem = document.getElementById(f"item-datatype-{i}")
            if datatype_elem:
                def make_datatype_handler(idx):
                    def handler(e):
                        update_item_field(idx, "datatype", e.target.value)
                    return handler
                p = create_proxy(make_datatype_handler(i))
                datatype_elem.addEventListener("input", p)
                datatype_elem.addEventListener("change", p)
                proxies[f"datatype-{i}"] = p
            
            
            # Entfernen-Button
            remove_btn = document.getElementById(f"remove-btn-{i}")
            if remove_btn:
                # Entferne alte Event-Listener, falls vorhanden
                old_proxy_key = f"remove-{i}"
                if old_proxy_key in old_proxies:
                    try:
                        old_proxy = old_proxies[old_proxy_key]
                        remove_btn.removeEventListener("click", old_proxy)
                        remove_btn.onclick = None
                    except:
                        pass
                
                # Erstelle einen eindeutigen Handler für diesen Button
                # Verwende eine Closure, die den Index aus dem data-index Attribut liest
                def create_remove_handler(btn_element):
                    handler_called = False
                    def handler(e):
                        nonlocal handler_called
                        if handler_called:
                            return  # Verhindere mehrfache Ausführung
                        handler_called = True
                        
                        e.stopPropagation()  # Verhindere Event-Bubbling
                        e.preventDefault()  # Verhindere Standard-Verhalten
                        
                        # Verwende NUR den Index aus dem data-index Attribut
                        data_index = btn_element.getAttribute("data-index")
                        if data_index is not None:
                            actual_index = int(data_index)
                            # Prüfe, ob der Index gültig ist
                            if 0 <= actual_index < len(items_list):
                                # Rufe remove_item nur einmal auf
                                remove_item(actual_index)
                        
                        # Setze den Flag nach kurzer Zeit zurück (für zukünftige Klicks)
                        def reset_flag():
                            nonlocal handler_called
                            handler_called = False
                        # Verwende setTimeout-Äquivalent
                        try:
                            window.setTimeout(reset_flag, 100)
                        except:
                            pass
                    return handler
                
                p = create_proxy(create_remove_handler(remove_btn))
                # Entferne alle alten Event-Listener
                remove_btn.onclick = None
                # Binde NUR einen Event-Listener (nicht beide!)
                remove_btn.addEventListener("click", p, False)
                # Setze onclick NICHT, um doppelte Aufrufe zu vermeiden
                proxies[f"remove-{i}"] = p

            # Bearbeiten-Button (Modal öffnen)
            edit_btn = document.getElementById(f"edit-btn-{i}")
            if edit_btn:
                def make_edit_handler(idx):
                    def handler(e):
                        open_edit_modal(idx)
                    return handler
                p = create_proxy(make_edit_handler(i))
                edit_btn.addEventListener("click", p)
                edit_btn.onclick = p
                proxies[f"edit-{i}"] = p
        
        # Aktualisiere die Proxies-Referenz
        update_items_list.proxies = proxies

    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Aktualisieren der Liste: {str(e)}"

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


def make_return_value_editable():
    """Macht Rückgabewerte im SVG bearbeitbar"""
    global items_list
    
    try:
        # Entferne alte Rückgabewert-Buttons
        container = document.getElementById("uml")
        if container:
            old_buttons = container.querySelectorAll(".edit-return-value-button")
            for btn in old_buttons:
                btn.remove()
        
        svg = document.querySelector("#uml svg")
        if not svg:
            return
        
        # Finde alle Methoden in der items_list (mit und ohne Rückgabewerte)
        all_methods = [(i, item) for i, item in enumerate(items_list) 
                      if item.get("type") == "method"]
        
        if not all_methods:
            return
        
        # Finde alle Text-Elemente im SVG
        text_elements = svg.querySelectorAll("text")
        
        # Erstelle eine Map von Methodennamen zu Indizes und Rückgabewerten
        method_info_map = {}
        for idx, method_item in all_methods:
            method_name = method_item.get("name", "").strip()
            return_type = method_item.get("datatype", "").strip()
            if method_name:
                method_info_map[method_name] = {
                    "index": idx,
                    "return_type": return_type
                }
        
        # Durchsuche Text-Elemente nach Methodennamen
        processed_methods = set[Any]()
        
        for text_elem in text_elements:
            text_content = text_elem.textContent.strip()
            
            # Prüfe verschiedene Formate:
            # 1. "methodName()" - nur Methodenname
            # 2. "methodName(): returnType" - Methode mit Rückgabewert in einem Element
            # 3. "+methodName()" - mit Sichtbarkeitssymbol
            
            method_name = None
            method_index = None
            return_type = None
            
            # Entferne Sichtbarkeitssymbole
            clean_text = text_content
            for sym in ["+", "-", "#"]:
                if clean_text.startswith(sym):
                    clean_text = clean_text[1:].strip()
                    break
            
            # Prüfe ob es eine Methode ist (endet mit "()")
            if clean_text.endswith("()"):
                method_name = clean_text[:-2].strip()
            elif "() :" in clean_text:
                # Format: "methodName() : returnType" (mit Leerzeichen)
                parts = clean_text.split("() :")
                if len(parts) == 2:
                    method_name = parts[0].strip()
                    return_type_from_text = parts[1].strip()
            elif "():" in clean_text:
                # Format: "methodName(): returnType" (ohne Leerzeichen - für Kompatibilität)
                parts = clean_text.split("():")
                if len(parts) == 2:
                    method_name = parts[0].strip()
                    return_type_from_text = parts[1].strip()
            
            if method_name and method_name in method_info_map:
                method_info = method_info_map[method_name]
                method_index = method_info["index"]
                if not return_type:
                    return_type = method_info["return_type"]
                
                if method_index in processed_methods:
                    continue
                
                # Finde Parent-Element
                parent = text_elem.parentElement
                if not parent:
                    continue
                
                # Berechne Position für den Rückgabewert-Button
                method_bbox = text_elem.getBBox()
                
                # Hole die SVG-Position relativ zum Container
                svg_rect = svg.getBoundingClientRect()
                container_rect = document.getElementById("uml").getBoundingClientRect()
                
                # Berechne absolute Position im Container
                svg_x = svg_rect.left - container_rect.left
                svg_y = svg_rect.top - container_rect.top
                
                # Wenn der Rückgabewert bereits im Text enthalten ist, suche nach dem " :" oder ":" Teil
                colon_pos = -1
                if "() :" in text_content and return_type:
                    # Format mit Leerzeichen: "methodName() : returnType"
                    colon_pos = text_content.find("() :")
                    if colon_pos >= 0:
                        colon_pos += 3  # Position nach "() :"
                elif "():" in text_content and return_type:
                    # Format ohne Leerzeichen: "methodName(): returnType" (für Kompatibilität)
                    colon_pos = text_content.find("():")
                    if colon_pos >= 0:
                        colon_pos += 2  # Position nach "():"
                
                # Suche nach dem Rückgabewert-Text-Element im SVG
                return_text_elem = None
                if return_type:
                    # Suche nach Text-Elementen, die den Rückgabewert enthalten
                    for other_text in text_elements:
                        other_content = other_text.textContent.strip()
                        # Prüfe ob es der Rückgabewert ist (kann ": returnType" oder nur "returnType" sein)
                        if (other_content == return_type or 
                            other_content == f": {return_type}" or
                            (other_content.startswith(":") and return_type in other_content)):
                            # Prüfe ob es in der Nähe der Methode ist
                            other_bbox = other_text.getBBox()
                            if abs(other_bbox.y - method_bbox.y) < 5:  # Gleiche Zeile
                                return_text_elem = other_text
                                break
                
                if colon_pos >= 0:
                    # Der Rückgabewert ist bereits im Text, finde die Position nach ":"
                    # Positioniere den Button so, dass er den ": returnType" Teil überdeckt
                    # colon_pos zeigt auf die Position nach "():" oder "() :"
                    # Wir müssen die Position des ":" finden
                    if "() :" in text_content:
                        # Format mit Leerzeichen: "methodName() : returnType"
                        colon_in_text = text_content.find("() :")
                        if colon_in_text >= 0:
                            text_before_colon = text_content[:colon_in_text + 3]  # Bis einschließlich "() :"
                        else:
                            text_before_colon = text_content[:colon_pos]
                    else:
                        # Format ohne Leerzeichen: "methodName(): returnType"
                        colon_in_text = text_content.find("():")
                        if colon_in_text >= 0:
                            text_before_colon = text_content[:colon_in_text + 2]  # Bis einschließlich "():"
                        else:
                            text_before_colon = text_content[:colon_pos]
                    
                    try:
                        svg_text_elem = text_elem
                        if hasattr(svg_text_elem, 'getSubStringLength'):
                            length_before = svg_text_elem.getSubStringLength(0, len(text_before_colon))
                            # Positioniere den Button leicht nach links, damit er den Doppelpunkt vollständig überdeckt
                            # Der Button zeigt " : returnType" und beginnt leicht vor dem ":" im SVG
                            x_pos_abs = svg_x + method_bbox.x + length_before - 3  # -3px um den Doppelpunkt zu überdecken
                        else:
                            # Fallback: Schätze die Position (leicht nach links für Doppelpunkt-Überdeckung)
                            x_pos_abs = svg_x + method_bbox.x + len(text_before_colon) * 6 - 3
                    except:
                        # Fallback: Schätze die Position (leicht nach links für Doppelpunkt-Überdeckung)
                        x_pos_abs = svg_x + method_bbox.x + len(text_before_colon) * 6 - 3
                elif return_text_elem:
                    # Verwende die Position des gefundenen Rückgabewert-Text-Elements
                    return_bbox = return_text_elem.getBBox()
                    x_pos_abs = svg_x + return_bbox.x - 2
                else:
                    # Rückgabewert ist nicht im Text, platziere rechts daneben
                    x_pos_abs = svg_x + method_bbox.x + method_bbox.width + 10
                
                y_pos_abs = svg_y + method_bbox.y - 2
                
                if return_type:
                    # Breite für " : returnType" (mit Leerzeichen und Doppelpunkt)
                    width = max(60, (len(return_type) + 3) * 7)  # +3 für " : "
                else:
                    width = 100  # Breite für "+ Rückgabewert"
                
                height = method_bbox.height + 4
                
                # Erstelle Button als Overlay-Element über dem SVG-Container
                container = document.getElementById("uml")
                if not container:
                    continue
                
                # Stelle sicher, dass der Container relative Position hat
                container.style.position = "relative"
                
                # Erstelle Button-Element
                button = document.createElement("button")
                button.className = "edit-return-value-button"
                if return_type:
                    # Zeige mit Leerzeichen vor dem Doppelpunkt: " : returnType"
                    # Der Button überdeckt den ursprünglichen ": returnType" Text im SVG
                    # Wichtig: Der Button beginnt genau beim ":" im SVG und zeigt " : returnType"
                    button.textContent = f" : {return_type}"
                else:
                    button.textContent = "+ Rückgabewert"
                button.setAttribute("data-method-index", str(method_index))
                
                # Positioniere den Button absolut über dem SVG
                button.style.position = "absolute"
                button.style.left = f"{x_pos_abs}px"
                button.style.top = f"{y_pos_abs}px"
                button.style.width = f"{width}px"
                button.style.height = f"{height}px"
                button.style.zIndex = "1000"
                
                if return_type:
                    button_style = (
                        "background: rgba(255, 255, 255, 0.98) !important; "
                        "border: 1px dashed #4a90e2 !important; "
                        "border-radius: 3px; "
                        "padding: 2px 6px; "
                        "font-size: 0.7rem; "
                        "cursor: pointer; "
                        "color: #4a90e2 !important; "
                        "white-space: nowrap; "
                        "font-weight: 500; "
                        "width: 100%; "
                        "height: 100%; "
                        "text-align: left; "
                        "min-width: 50px; "
                        "transition: all 0.2s; "
                        "box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important; "
                        "z-index: 1001; "
                        "position: relative; "
                        "display: block;"
                    )
                else:
                    button_style = (
                        "background: rgba(74, 144, 226, 0.2) !important; "
                        "border: 1px dashed #4a90e2 !important; "
                        "border-radius: 3px; "
                        "padding: 2px 6px; "
                        "font-size: 0.65rem; "
                        "cursor: pointer; "
                        "color: #4a90e2 !important; "
                        "white-space: nowrap; "
                        "font-weight: 400; "
                        "font-style: italic; "
                        "width: 100%; "
                        "height: 100%; "
                        "text-align: left; "
                        "min-width: 100px; "
                        "transition: all 0.2s; "
                        "box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important; "
                        "z-index: 1001; "
                        "position: relative; "
                        "display: block;"
                    )
                button.style.cssText = button_style
                
                def make_return_edit_handler(idx):
                    def handler(e):
                        e.stopPropagation()
                        open_return_value_modal(idx)
                    return handler
                
                return_edit_proxy = create_proxy(make_return_edit_handler(method_index))
                button.addEventListener("click", return_edit_proxy)
                button.onclick = return_edit_proxy
                
                # Hover-Effekt
                def hover_in(e):
                    e.target.style.background = "#4a90e2"
                    e.target.style.color = "white"
                    e.target.style.borderColor = "#357abd"
                def hover_out(e):
                    if return_type:
                        e.target.style.background = "rgba(255, 255, 255, 0.95)"
                    else:
                        e.target.style.background = "rgba(74, 144, 226, 0.15)"
                    e.target.style.color = "#4a90e2"
                    e.target.style.borderColor = "#4a90e2"
                
                hover_in_proxy = create_proxy(hover_in)
                hover_out_proxy = create_proxy(hover_out)
                button.addEventListener("mouseenter", hover_in_proxy)
                button.addEventListener("mouseleave", hover_out_proxy)
                
                # Speichere Proxies gegen GC
                if not hasattr(make_return_value_editable, "proxies"):
                    make_return_value_editable.proxies = []
                make_return_value_editable.proxies.extend([return_edit_proxy, hover_in_proxy, hover_out_proxy])
                
                # Füge Button zum Container hinzu
                container.appendChild(button)
                
                # Verstecke den ursprünglichen Rückgabewert-Text im SVG, falls vorhanden
                if return_text_elem:
                    return_text_elem.style.display = "none"
                elif colon_pos >= 0 and return_type:
                    # Wenn der Rückgabewert im Methoden-Text enthalten ist (z.B. "methodName(): returnType"),
                    # können wir den Text nicht teilweise verstecken. Der Button sollte den ": returnType" Teil überdecken.
                    # Stelle sicher, dass der Button einen undurchsichtigen Hintergrund hat und breit genug ist
                    button.style.background = "rgba(255, 255, 255, 1) !important"
                    # Erhöhe die Breite, um sicherzustellen, dass der gesamte ": returnType" Text überdeckt wird
                    original_width = width
                    width = max(width, (len(f": {return_type}") + 2) * 7)  # +2 für Sicherheit
                    button.style.width = f"{width}px"
                
                processed_methods.add(method_index)
                    
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Bearbeitbar-Machen: {str(e)}"

def open_return_value_modal(method_index):
    """Öffnet ein Modal zur Bearbeitung des Rückgabewerts einer Methode"""
    global items_list
    try:
        if method_index < 0 or method_index >= len(items_list):
            return
        
        item = items_list[method_index]
        if item.get("type") != "method":
            return
        
        # Erstelle ein einfaches Modal für Rückgabewert
        existing_modal = document.getElementById("returnValueModal")
        if existing_modal:
            existing_modal.remove()
        
        modal = document.createElement("div")
        modal.id = "returnValueModal"
        modal.className = "edit-modal active"
        modal.innerHTML = f"""
            <div class="edit-modal-content">
                <h3>Rückgabewert bearbeiten</h3>
                <div class="form-group">
                    <label for="returnValueInput">Rückgabewert:</label>
                    <input type="text" id="returnValueInput" value="{item.get('datatype', '').replace('"', '&quot;')}" placeholder="z.B. string, int, void" />
                </div>
                <div class="edit-modal-buttons">
                    <button id="returnValueCancelBtn" class="btn-cancel">Abbrechen</button>
                    <button id="returnValueSaveBtn" class="btn-save">Speichern</button>
                </div>
            </div>
        """
        document.body.appendChild(modal)
        
        # Event-Listener hinzufügen
        save_btn = document.getElementById("returnValueSaveBtn")
        cancel_btn = document.getElementById("returnValueCancelBtn")
        return_input = document.getElementById("returnValueInput")
        
        def save_return_value(e):
            new_return = return_input.value.strip()
            items_list[method_index]["datatype"] = new_return
            modal.remove()
            
            # Update die Items-Liste in der UI
            update_items_list()
            
            # Update das Diagramm
            update_diagram()
            
            output = document.getElementById("out")
            if output:
                output.textContent = f"Rückgabewert auf '{new_return}' geändert."
        
        def cancel_return_value(e):
            modal.remove()
        
        def on_return_keypress(e):
            if e.key == "Enter":
                save_return_value(e)
            elif e.key == "Escape":
                cancel_return_value(e)
        
        save_proxy = create_proxy(save_return_value)
        cancel_proxy = create_proxy(cancel_return_value)
        keypress_proxy = create_proxy(on_return_keypress)
        
        save_btn.addEventListener("click", save_proxy)
        cancel_btn.addEventListener("click", cancel_proxy)
        return_input.addEventListener("keydown", keypress_proxy)
        
        # Klick außerhalb schließt Modal
        def modal_click_handler(e):
            if e.target == modal:
                cancel_return_value(e)
        modal_click_proxy = create_proxy(modal_click_handler)
        modal.addEventListener("click", modal_click_proxy)
        
        # Fokussiere das Input-Feld
        return_input.focus()
        return_input.select()
        
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Öffnen des Rückgabewert-Modals: {str(e)}"

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
        
        # Warte länger, damit das SVG vollständig gerendert und im DOM ist
        await asyncio.sleep(0.3)
        
        # Mache Rückgabewerte bearbeitbar
        make_return_value_editable()
        
        # Warte nochmal kurz und versuche es erneut (falls SVG noch nicht vollständig geladen)
        await asyncio.sleep(0.2)
        make_return_value_editable()
        
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
        datatype_elem = document.getElementById("itemDatatype")
        
        if not item_type_elem or not visibility_elem or not name_elem or not datatype_elem:
            return
        
        item_type = item_type_elem.value
        visibility = visibility_elem.value
        name = name_elem.value.strip()
        datatype = datatype_elem.value.strip()
        
        if not name:
            output = document.getElementById("out")
            if output:
                output.textContent = "Bitte geben Sie einen Namen ein."
            return
        
        # Füge das Item zur Liste hinzu
        new_item = {
            "type": item_type,
            "visibility": visibility,
            "name": name,
            "datatype": datatype
        }
        items_list.append(new_item)
        
        # Leere das Eingabefeld
        name_elem.value = ""
        datatype_elem.value = ""
        
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
        # Doppelte Prüfung: Stelle sicher, dass der Index gültig ist
        if 0 <= index < len(items_list):
            removed = items_list.pop(index)
            # Update die Items-Liste (dies erstellt neue DOM-Elemente und entfernt alte Event-Listener)
            update_items_list()
            # Update das Diagramm
            update_diagram()
            output = document.getElementById("out")
            if output:
                output.textContent = f"{'Attribut' if removed['type'] == 'attribute' else 'Methode'} '{removed['name']}' entfernt."
        else:
            output = document.getElementById("out")
            if output:
                output.textContent = f"Fehler: Ungültiger Index {index} (Liste hat {len(items_list)} Elemente)"
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
        edit_datatype = document.getElementById("editDatatype")
        modal = document.getElementById("editModal")
        
        if edit_type and edit_visibility and edit_name and edit_datatype and modal:
            edit_type.value = item.get("type", "attribute")
            edit_visibility.value = item.get("visibility", "public")
            edit_name.value = item.get("name", "")
            edit_datatype.value = item.get("datatype", "")
            
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
        edit_datatype = document.getElementById("editDatatype")
        
        if edit_type and edit_visibility and edit_name and edit_datatype:
            items_list[item_index]["type"] = edit_type.value
            items_list[item_index]["visibility"] = edit_visibility.value
            items_list[item_index]["name"] = edit_name.value.strip()
            items_list[item_index]["datatype"] = edit_datatype.value.strip()
            
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
