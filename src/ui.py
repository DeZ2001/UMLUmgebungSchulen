from typing import Any
from js import window, document
from pyodide.ffi import create_proxy
import asyncio
import html

# Zähler für eindeutige Diagramm-IDs
diagram_counter = 0

# Liste der Attribute und Methoden
# Liste von Dictionaries: {"type": "attribute"/"method", "visibility": "public"/"private"/"protected", "name": "name"}
items_list = []

# Aktuell ausgewähltes Element in der Eingabemaske
selected_item_index = None

# Sichtbarkeitssymbole als Konstante
VISIBILITY_SYMBOLS = {"public": "+", "private": "-", "protected": "#"}

def format_parameters_for_label(item):
    """Formatiert Parameterliste für Anzeige/Datenattribute"""
    if item.get("type") != "method":
        return ""

    params = item.get("parameters") or []
    parts = []
    for param in params:
        if not isinstance(param, dict):
            continue
        pname = str(param.get("name", "") or "").strip()
        ptype = str(param.get("type", "") or "").strip()
        if pname or ptype:
            if pname and ptype:
                parts.append(f"{pname}:{ptype}")
            elif pname:
                parts.append(pname)
            else:
                parts.append(ptype)

    return ", ".join(parts)

def build_option_data_attributes(item):
    """Erstellt data-* Attribute für das Option-Element"""
    data_map = {
        "type": item.get("type", "") or "",
        "visibility": item.get("visibility", "") or "",
        "name": item.get("name", "") or "",
        "datatype": item.get("datatype", "") or "",
        "params": format_parameters_for_label(item) or "",
    }

    attr_parts = []
    for key, value in data_map.items():
        safe = html.escape(str(value), quote=True)
        attr_parts.append(f'data-{key}="{safe}"')

    return " ".join(attr_parts) + " " if attr_parts else ""

def parse_parameter_string(param_string):
    """Parst eine Kommaseparierte Parameterliste in eine Liste von Dictionaries"""
    params = []
    if not param_string:
        return params

    for chunk in str(param_string).split(","):
        entry = chunk.strip()
        if not entry:
            continue

        if ":" in entry:
            name_part, type_part = entry.split(":", 1)
            pname = name_part.strip()
            ptype = type_part.strip()
        else:
            pname = entry
            ptype = ""

        if pname or ptype:
            params.append({"name": pname, "type": ptype})

    return params

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
                # 修复：正确获取参数列表
                params = method.get("parameters", [])
                if params:
                    # 确保参数格式正确
                    param_str = ", ".join(f"{p.get('name', '')}: {p.get('type', '')}" for p in params)
                else:
                    param_str = ""

                line = f"        {visibility_symbol}{method_name}({param_str})"
                if return_type:
                    line += f" {return_type}"
                diagram_lines.append(line)
    
    diagram_lines.append("    }")
    
    return "\n".join(diagram_lines)

def format_item_label(item, index):
    """Erzeugt die Beschriftung für das Auswahlfeld"""
    item_type = item.get("type", "attribute")
    type_label = "Attribut" if item_type == "attribute" else "Methode"
    visibility = item.get("visibility", "public")
    visibility_symbol = VISIBILITY_SYMBOLS.get(visibility, "+")
    name = item.get("name", "").strip() or "(ohne Namen)"
    datatype = item.get("datatype", "").strip()

    if item_type == "method":
        param_str = format_parameters_for_label(item)
        if param_str:
            signature = f"{name}({param_str})"
        else:
            signature = f"{name}()"
    else:
        signature = name

    if datatype:
        signature += f": {datatype}"

    label = f"{index + 1}. {type_label} {visibility_symbol}{signature}"
    return html.escape(label)

def set_manage_fields_enabled(enabled):
    """Aktiviert oder deaktiviert die Bearbeitungsfelder"""
    field_ids = ["manageItemType", "manageVisibility", "manageItemName", "manageItemDatatype", "deleteItemBtn"]
    for field_id in field_ids:
        elem = document.getElementById(field_id)
        if elem:
            elem.disabled = not enabled

def reset_item_form():

    """Leert das Eingabefeld und hebt die Auswahl auf"""
    global selected_item_index
    selected_item_index = None

    type_elem = document.getElementById("manageItemType")
    visibility_elem = document.getElementById("manageVisibility")
    name_elem = document.getElementById("manageItemName")
    datatype_elem = document.getElementById("manageItemDatatype")
    param_elem = document.getElementById("manageItemPara")  
    selector = document.getElementById("itemSelector")

    if type_elem:
        type_elem.value = "attribute"
    if visibility_elem:
        visibility_elem.value = "public"
    if name_elem:
        name_elem.value = ""
    if datatype_elem:
        datatype_elem.value = ""
    if param_elem:  # 新增：清空参数框
        param_elem.value = ""
        param_elem.style.display = "none"  # 隐藏参数框
    if selector:
        selector.value = ""

    set_manage_fields_enabled(False)

def load_item_into_form(index):
    """Lädt das Item mit dem gegebenen Index in das Formular"""
    global selected_item_index

    if index < 0 or index >= len(items_list):
        reset_item_form()
        return

    selected_item_index = index
    item = items_list[index]

    type_elem = document.getElementById("manageItemType")
    visibility_elem = document.getElementById("manageVisibility")
    name_elem = document.getElementById("manageItemName")
    datatype_elem = document.getElementById("manageItemDatatype")
    selector = document.getElementById("itemSelector")

    if type_elem:
        type_elem.value = item.get("type", "attribute")
    if visibility_elem:
        visibility_elem.value = item.get("visibility", "public")
    if name_elem:
        name_elem.value = item.get("name", "")
    if datatype_elem:
        datatype_elem.value = item.get("datatype", "")
    if selector:
        selector.value = str(index)

    set_manage_fields_enabled(True)

def update_item_selector():
    """Aktualisiert die Optionsliste für bestehende Elemente"""
    global selected_item_index

    selector = document.getElementById("itemSelector")
    if not selector:
        return

    if selected_item_index is not None and not (0 <= selected_item_index < len(items_list)):
        selected_item_index = None

    options = ["<option value=\"\">Bitte Element wählen</option>"]
    for idx, item in enumerate(items_list):
        selected_attr = " selected" if selected_item_index == idx else ""
        data_attrs = build_option_data_attributes(item)
        options.append(
            f"<option value=\"{idx}\" {data_attrs}{selected_attr}>{format_item_label(item, idx)}</option>"
        )

    selector.innerHTML = "".join(options)

    if selected_item_index is None:
        selector.value = ""
    else:
        selector.value = str(selected_item_index)

def on_item_selector_change(event):
    """Reagiert auf Änderungen im Auswahlfeld"""
    value = event.target.value
    if value == "":
        reset_item_form()
    else:
        try:
            load_item_into_form(int(value))
        except Exception:
            reset_item_form()

def update_selected_item_field(field, value):
    """Aktualisiert ein Feld des ausgewählten Elements"""
    global selected_item_index

    if selected_item_index is None or not (0 <= selected_item_index < len(items_list)):
        output = document.getElementById("out")
        if output:
            output.textContent = "Bitte wählen Sie zuerst ein Element aus."
        return

    if field == "name":
        items_list[selected_item_index]["name"] = value
    elif field == "datatype":
        items_list[selected_item_index]["datatype"] = value
    elif field == "type":
        items_list[selected_item_index]["type"] = value
    elif field == "visibility":
        items_list[selected_item_index]["visibility"] = value

    update_item_selector()
    update_diagram()

def update_selected_item_parameters(raw_value, normalize_field=False):
    """Aktualisiert Parameter der ausgewählten Methode"""
    global selected_item_index

    if selected_item_index is None or not (0 <= selected_item_index < len(items_list)):
        output = document.getElementById("out")
        if output:
            output.textContent = "Bitte wählen Sie zuerst ein Element aus."
        return

    item = items_list[selected_item_index]
    if item.get("type") != "method":
        output = document.getElementById("out")
        if output:
            output.textContent = "Parameter können nur für Methoden bearbeitet werden."
        return

    params = parse_parameter_string(raw_value or "")
    item["parameters"] = params

    if normalize_field:
        normalized_text = format_parameters_for_label(item)
        param_elem = document.getElementById("manageItemPara")
        if param_elem is not None:
            param_elem.value = normalized_text

    update_item_selector()
    update_diagram()

def delete_selected_item():
    """Entfernt das aktuell ausgewählte Item"""
    global items_list, selected_item_index

    if selected_item_index is None:
        output = document.getElementById("out")
        if output:
            output.textContent = "Es ist kein Element ausgewählt."
        return

    if 0 <= selected_item_index < len(items_list):
        removed = items_list.pop(selected_item_index)
        reset_item_form()
        update_item_selector()
        update_diagram()

        output = document.getElementById("out")
        if output:
            output.textContent = (
                f"{'Attribut' if removed.get('type') == 'attribute' else 'Methode'} "
                f"'{removed.get('name', '')}' gelöscht."
            )

def focus_item_from_diagram(item_index, focus_datatype=False):
    """Lädt ein Item in das Formular, z.B. nach Klick im Diagramm"""
    if item_index < 0 or item_index >= len(items_list):
        return

    load_item_into_form(item_index)
    update_item_selector()

    if focus_datatype:
        datatype_elem = document.getElementById("manageItemDatatype")
        if datatype_elem:
            datatype_elem.focus()
            datatype_elem.select()

    output = document.getElementById("out")
    if output:
        output.textContent = "Element zum Bearbeiten geladen."

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
            elif "() " in clean_text and not clean_text.endswith("()"):
                # Format: "methodName() returnType" (mit Leerzeichen)
                parts = clean_text.split("() ")
                if len(parts) >= 2:
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
            space_pos = -1
            if "() " in text_content and return_type:
            # Format: "methodName() returnType" (mit Leerzeichen)
                space_pos = text_content.find("() ")
                if space_pos >= 0:
                    space_pos += 2 
                
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
                
                if space_pos >= 0:
                    # Der Rückgabewert ist bereits im Text, finde die Position nach ":"
                    # Positioniere den Button so, dass er den ": returnType" Teil überdeckt
                    # colon_pos zeigt auf die Position nach "():" oder "() :"
                    # Wir müssen die Position des ":" finden
                    if "() " in text_content:
                        # Format mit Leerzeichen: "methodName() : returnType"
                        space_in_text = text_content.find("() :")
                        if space_in_text >= 0:
                            text_before_space = text_content[:space_in_text + 2]  # Bis einschließlich "() :"
                        else:
                            text_before_space = text_content[:space_pos]
                    
                    try:
                        svg_text_elem = text_elem
                        if hasattr(svg_text_elem, 'getSubStringLength'):
                            length_before = svg_text_elem.getSubStringLength(0, len(text_before_space))
                            # Positioniere den Button leicht nach links, damit er den Doppelpunkt vollständig überdeckt
                            # Der Button zeigt " : returnType" und beginnt leicht vor dem ":" im SVG
                            x_pos_abs = svg_x + method_bbox.x + length_before - 3  # -3px um den Doppelpunkt zu überdecken
                        else:
                            # Fallback: Schätze die Position (leicht nach links für Doppelpunkt-Überdeckung)
                            x_pos_abs = svg_x + method_bbox.x + len(text_before_space) * 6 - 3
                    except:
                        # Fallback: Schätze die Position (leicht nach links für Doppelpunkt-Überdeckung)
                        x_pos_abs = svg_x + method_bbox.x + len(text_before_space) * 6 - 3
                elif return_text_elem:
                    # Verwende die Position des gefundenen Rückgabewert-Text-Elements
                    return_bbox = return_text_elem.getBBox()
                    x_pos_abs = svg_x + return_bbox.x - 2
                else:
                    # Rückgabewert ist nicht im Text, platziere rechts daneben
                    x_pos_abs = svg_x + method_bbox.x + method_bbox.width + 10
                
                y_pos_abs = svg_y + method_bbox.y - 2
                
                if return_type:
                    # Berechne Breite basierend auf Rückgabewert-Länge
                    width = max(60, (len(return_type) + 1) * 7)  # +1 für Leerzeichen vor dem Doppelpunkt
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
                    button.textContent = f"{return_type}"
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
                        focus_item_from_diagram(idx, focus_datatype=True)
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
    global items_list, selected_item_index
    try:
        item_type_elem = document.getElementById("newItemType")
        visibility_elem = document.getElementById("newVisibility")
        name_elem = document.getElementById("newItemName")
        datatype_elem = document.getElementById("newItemDatatype")
        param_field = document.getElementById("newItemParameters")  # 修复：添加这行
        
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
        
        # 创建新项目
        new_item = {
            "type": item_type,
            "visibility": visibility,
            "name": name,
            "datatype": datatype,
            "parameters": []
        }
        
        # 参数处理 - 修复逻辑
        if item_type == "method" and param_field:
            param_string = param_field.value.strip()
            new_item["parameters"] = parse_parameter_string(param_string)
        
        # 添加到列表
        items_list.append(new_item)
        selected_item_index = len(items_list) - 1
        
        # 清空输入字段
        name_elem.value = ""
        datatype_elem.value = ""
        if param_field:
            param_field.value = ""  # 清空参数字段
        
        # 更新界面
        update_item_selector()
        load_item_into_form(selected_item_index)
        update_diagram()
        
        output = document.getElementById("out")
        if output:
            output.textContent = f"{'Attribut' if item_type == 'attribute' else 'Methode'} '{name}' hinzugefügt."
    except Exception as e:
        output = document.getElementById("out")
        if output:
            output.textContent = f"Fehler beim Hinzufügen: {str(e)}"


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
        item_name_input = document.getElementById("newItemName")
        
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
        
        # Initialisiere Auswahl-Elemente
        reset_item_form()
        update_item_selector()

        item_selector = document.getElementById("itemSelector")
        delete_btn = document.getElementById("deleteItemBtn")
        manage_type_elem = document.getElementById("manageItemType")
        manage_visibility_elem = document.getElementById("manageVisibility")
        manage_name_elem = document.getElementById("manageItemName")
        manage_datatype_elem = document.getElementById("manageItemDatatype")

        if item_selector:
            selector_proxy = create_proxy(on_item_selector_change)
            item_selector.addEventListener("change", selector_proxy)
            item_selector.onchange = selector_proxy
            item_selector._change_proxy = selector_proxy

        if delete_btn:
            def delete_handler(e):
                delete_selected_item()
            delete_proxy = create_proxy(delete_handler)
            delete_btn.addEventListener("click", delete_proxy)
            delete_btn.onclick = delete_proxy
            delete_btn._click_proxy = delete_proxy

        if manage_type_elem:
            def on_type_change(e):
                update_selected_item_field("type", e.target.value)
            type_proxy = create_proxy(on_type_change)
            manage_type_elem.addEventListener("change", type_proxy)
            manage_type_elem.onchange = type_proxy
            manage_type_elem._change_proxy = type_proxy

        if manage_visibility_elem:
            def on_visibility_change(e):
                update_selected_item_field("visibility", e.target.value)
            vis_proxy = create_proxy(on_visibility_change)
            manage_visibility_elem.addEventListener("change", vis_proxy)
            manage_visibility_elem.onchange = vis_proxy
            manage_visibility_elem._change_proxy = vis_proxy

        if manage_name_elem:
            def on_name_input(e):
                update_selected_item_field("name", e.target.value)
            name_proxy = create_proxy(on_name_input)
            manage_name_elem.addEventListener("input", name_proxy)
            manage_name_elem.addEventListener("change", name_proxy)
            manage_name_elem._input_proxy = name_proxy

        if manage_datatype_elem:
            def on_datatype_input(e):
                update_selected_item_field("datatype", e.target.value)
            datatype_proxy = create_proxy(on_datatype_input)
            manage_datatype_elem.addEventListener("input", datatype_proxy)
            manage_datatype_elem.addEventListener("change", datatype_proxy)
            manage_datatype_elem._input_proxy = datatype_proxy

        manage_param_elem = document.getElementById("manageItemPara")
        if manage_param_elem:
            def on_param_input(e):
                update_selected_item_parameters(e.target.value)
            param_proxy = create_proxy(on_param_input)
            manage_param_elem.addEventListener("input", param_proxy)
            manage_param_elem.addEventListener("change", param_proxy)
            manage_param_elem._input_proxy = param_proxy
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
