from js import document, window, JSON, localStorage, navigator
from pyodide.ffi import create_proxy
import math
import json

# ===================================
# UML-Datenmodell & globale Variablen
# ===================================

# Liste aller UML-Klassen
umlClasses = [
    {
        "id": 1,
        "name": "",
        "attributes": [
        ],
        "methods": [
            {
                "id": 1,
                "methode": "c __init__()",
                "access": "",
                "auto": True
            }
        ],
    }
]
# Zähler für eindeutige Attribut-IDs
nextAttributeId = 1
# Zähler für eindeutige Methoden-IDs
nextMethodId = 2
# Schriftart für Textmessungen im UI
UI_FONT = "15px 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
# Textbreiten messen
measureTextWidth_canvas = None
# Aktueller Zustand für Listen-Sortierung (Drag & Drop)
current_sort_drag = {
    "kind": None,
    "class_id": None,
    "item_id": None,
}

# ============================
# DOM-Referenzen (UI-Elemente)
# ============================

jsonModalOverlay = document.getElementById("jsonModalOverlay")
jsonModalTitle = document.getElementById("jsonModalTitle")
jsonModalTextarea = document.getElementById("jsonModalTextarea")
jsonModalPrimary = document.getElementById("jsonModalPrimary")
jsonModalTertiary = document.getElementById("jsonModalTertiary")
jsonModalSecondary = document.getElementById("jsonModalSecondary")
jsonModalClose = document.getElementById("jsonModalClose")
jsonFileInput = document.getElementById("jsonFileInput")

# Speicherung aller Event-Proxies
event_proxies = []

def generate_getter_name(attr_name):
    """getter Methode name generieren"""
    return f"get_{attr_name}"

def generate_setter_name(attr_name):
    """setter Methode name generieren"""
    return f"set_{attr_name}"

def extract_attr_name_from_method(method_name):
    """Extract attribute name from getter/setter method name"""
    if method_name.startswith("get_"):
        return method_name[4:]
    elif method_name.startswith("set_"):
        return method_name[4:]
    return None

def get_attr_type(attr_value):
    """Extract type from attribute string"""
    if ":" in attr_value:
        return attr_value.split(":")[1].strip()
    return ""

def build_getter_signature(attr_name, attr_type):
    """Build getter method signature"""
    return_type = f"{attr_type}" if attr_type else ""
    return f"{generate_getter_name(attr_name)}():{return_type}"

def build_setter_signature(attr_name, attr_type):
    """Build setter method signature"""
    param_type = f":{attr_type}" if attr_type else ""
    return f"{generate_setter_name(attr_name)}({attr_name}{param_type})"

def get_existing_getter_setter(umlClass, attr_name):
    """Überprüft, ob Getter/Setter-Methoden existieren"""
    getter_name = generate_getter_name(attr_name)
    setter_name = generate_setter_name(attr_name)
    
    has_getter = False
    has_setter = False
    
    for method in umlClass["methods"]:
        method_name = method["methode"].split("(")[0].strip()
        if method_name == getter_name:
            has_getter = True
        elif method_name == setter_name:
            has_setter = True
    
    return {
        "has_getter": has_getter,
        "has_setter": has_setter,
        "is_getter_manual": has_getter,  # Da immer deaktiviert, wenn vorhanden
        "is_setter_manual": has_setter   # Da immer deaktiviert, wenn vorhanden
    }

def is_getter_button_disabled(umlClass, attribute):
    """Bestimmt, ob Getter-Button deaktiviert sein soll"""
    attr_str = attribute.get("attr", "")
    if not attr_str or attr_str.strip() == "":
        return False  # Kein Attributname, Button aktiv
    
    attr_name = attr_str.split(":")[0].strip() if ":" in attr_str else attr_str.strip()
    if not attr_name:
        return False
    
    existing = get_existing_getter_setter(umlClass, attr_name)
    # Deaktivieren, wenn Getter existiert (egal ob manuell oder automatisch)
    return existing["has_getter"]

def is_setter_button_disabled(umlClass, attribute):
    """Bestimmt, ob Setter-Button deaktiviert sein soll"""
    attr_str = attribute.get("attr", "")
    if not attr_str or attr_str.strip() == "":
        return False  # Kein Attributname, Button aktiv
    
    attr_name = attr_str.split(":")[0].strip() if ":" in attr_str else attr_str.strip()
    if not attr_name:
        return False
    
    existing = get_existing_getter_setter(umlClass, attr_name)
    # Deaktivieren, wenn Setter existiert (egal ob manuell oder automatisch)
    return existing["has_setter"]

def add_listener(element, event_name, handler):
    """ Fügt einen EventListener hinzu und speichert den Proxy """
    # Wenn Element nicht existiert → abbrechen
    if not element:
        return
    # Python-Funktion in JS-Proxy umwandeln
    proxy = create_proxy(handler)
    element.addEventListener(event_name, proxy) # Event registrieren
    event_proxies.append(proxy) # Speichern

def set_onclick(element, handler):
    """ Setzt eine onclick-Funktion """
    if not element:
        return
    proxy = create_proxy(handler)
    element.onclick = proxy
    event_proxies.append(proxy)

# =========================
# Zugriffstypen (+ / - / #)
# =========================

def changeAccessModifier(event):
    """ Ändert den Access Modifier eines Attributs oder einer Methode """
    target = event.target
    accessType = target.dataset.access
    classId = int(target.dataset.classId)

    # Wenn ein Attribut geklickt wurde
    if target.hasAttribute("data-attr-id"):
        attributeId = int(target.getAttribute("data-attr-id"))
        setAccessModifier(classId, attributeId, None, accessType)
        # Alte Auswahl entfernen
        for btn in document.querySelectorAll(
            f'button[data-attr-id="{attributeId}"].access-btn'
        ):
            btn.classList.remove("selected")
    # Wenn eine Methode geklickt wurde
    elif target.hasAttribute("data-method-id"):
        methodId = int(target.getAttribute("data-method-id"))
        setAccessModifier(classId, None, methodId, accessType)
        for btn in document.querySelectorAll(
            f'button[data-method-id="{methodId}"].access-btn'
        ):
            if btn.id == "remove":
                continue
            btn.classList.remove("selected")
    # Aktuelle Button markieren
    target.classList.add("selected")
    generateCode()

def getSelected(current, expected):
    """ Prüft, ob ein Button ausgewählt ist """
    return "selected" if current == expected else ""

# ========================
# Text- & Größenberechnung
# ========================

def measureTextWidth(text=""):
    """ Berechnet die Textbreite in Pixel """
    global measureTextWidth_canvas

    # Canvas erzeugen (nur 1-mal)
    if measureTextWidth_canvas is None:
        measureTextWidth_canvas = document.createElement("canvas")
    context = measureTextWidth_canvas.getContext("2d")
    # Fallback bei Fehler
    if not context:
        return len(text) * 8
    context.font = UI_FONT
    return context.measureText(text).width

def calculateClassWidth(umlClass):
    padding = 100
    minWidth = 350
    umlDiagram = document.getElementById("umlDiagram")
    # Containerbreite bestimmen (für zukünftige Erweiterungen behalten)
    containerWidth = (
        (umlDiagram.parentElement.clientWidth if umlDiagram and umlDiagram.parentElement else None)
        or (umlDiagram.clientWidth if umlDiagram else None)
        or window.innerWidth
    )
    containerWidth -= 40

    # Maximale Textbreite ermitteln
    maxTextWidth = measureTextWidth(umlClass["name"])
    for attr in umlClass["attributes"]:
        maxTextWidth = max(maxTextWidth, measureTextWidth(attr["attr"]))
    for method in umlClass["methods"]:
        maxTextWidth = max(maxTextWidth, measureTextWidth(method["methode"]))

    # Keine harte Obergrenze, damit lange Methoden den Rahmen erweitern können
    return max(minWidth, math.ceil((maxTextWidth + padding)))

def resizeUmlClasses():
    """ Die Breite des UML-Diagramm anpassen"""
    umlDiagram = document.getElementById("umlDiagram")
    if not umlDiagram:
        return
    for index, umlClass in enumerate(umlClasses):
        classElement = umlDiagram.children[index]
        if classElement:
            classElement.style.width = f"{calculateClassWidth(umlClass)}px"


# ===========================
# Rendering des UML-Diagramms
# ===========================

def renderUmlDiagram():
    """ Erstellt das komplette UML-Diagramm neu """
    # speichert das aktive Element
    active_element = document.activeElement
    active_id = active_element.id if active_element else None
    active_attr_id = active_element.getAttribute("data-attr-id") if active_element else None
    active_method_id = active_element.getAttribute("data-method-id") if active_element else None
    active_class_id = active_element.getAttribute("data-class-id") if active_element else None
    active_field = active_element.getAttribute("data-field") if active_element else None
    cursor_position = active_element.selectionStart if hasattr(active_element, 'selectionStart') else None
    
    umlDiagram = document.getElementById("umlDiagram")
    umlDiagram.innerHTML = ""
    for umlClass in umlClasses:
        classElement = document.createElement("div")
        classElement.className = "uml-class"
        # HTML für Attribute
        attributes_html = "".join(
            [
                f"""
                  <div class=\"uml-item sortable-item\" draggable=\"true\" data-no-class-drag=\"true\" data-sort-kind=\"attr\" data-item-id=\"{attri['id']}\" data-class-id=\"{umlClass['id']}\">
                    <span class=\"drag-handle\" title=\"Attribut ziehen\" data-no-class-drag=\"true\">::</span>
                    <button class=\"btn-small access-btn {getSelected(attri.get('access'), '+')}\" data-access=\"+\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">+</button>
                    <button class=\"btn-small access-btn {getSelected(attri.get('access'), '-')}\" data-access=\"-\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">-</button>
                    <button class=\"btn-small access-btn {getSelected(attri.get('access'), '#')}\" data-access=\"#\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">#</button>
                    <input type=\"text\" value=\"{attri['attr']}\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\" data-field=\"attr\" placeholder=\"Attributname:Datentyp\">
                    <button class=\"remove-attr\" id=\"remove\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">×</button>
                    <!-- Getter-Button mit Tooltip -->
                    <button class=\"btn-small-getter-setter access-btn-getter-setter getter \" data-access=\"g\"
                            data-class-id=\"{umlClass['id']}\" 
                            data-attr-id=\"{attri['id']}\" 
                            {'disabled' if is_getter_button_disabled(umlClass, attri) else ''}
                            title=\"{"Getter bereits vorhanden" if is_getter_button_disabled(umlClass, attri) else "Getter-Methode generieren"}\"
                            >g</button>
                    <!-- Setter-Button mit Tooltip -->
                    <button class=\"btn-small-getter-setter access-btn-getter-setter setter \" data-access=\"s\"
                            data-class-id=\"{umlClass['id']}\" 
                            data-attr-id=\"{attri['id']}\" 
                            {'disabled' if is_setter_button_disabled(umlClass, attri) else ''}
                            title=\"{"Setter bereits vorhanden" if is_setter_button_disabled(umlClass, attri) else "Setter-Methode generieren"}\"
                            ">s</button>
                  </div>
                """
                for attri in umlClass["attributes"]
            ]
        )
        # HTML für Methoden
        methods_html = "".join(
            [
                (
                    f"""
                  <div class=\"uml-item sortable-item\" draggable=\"true\" data-no-class-drag=\"true\" data-sort-kind=\"method\" data-item-id=\"{method['id']}\" data-class-id=\"{umlClass['id']}\">
                    <span class=\"drag-handle\" title=\"Methode ziehen\" data-no-class-drag=\"true\">::</span>
                    <button class=\"btn-small access-btn {getSelected(method.get('access'), '+')}\" data-access=\"+\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">+</button>
                    <button class=\"btn-small access-btn {getSelected(method.get('access'), '-')}\" data-access=\"-\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">-</button>
                    <button class=\"btn-small access-btn {getSelected(method.get('access'), '#')}\" data-access=\"#\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">#</button>
                    <input type=\"text\" value=\"{method['methode']}\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\" data-field=\"methode\" placeholder=\"Methodenname(Parameter):Rückgabetyp\">
                    <button class=\"remove-method\" id=\"remove\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">×</button>
                  </div>
                    """
                    if not is_constructor_method(method.get("methode")) 
                    else f"""
                  <div class=\"uml-item constructor-item\" data-no-class-drag=\"true\">
                    <span class=\"drag-handle-placeholder\" aria-hidden=\"true\"></span>
                    <input type=\"text\" value=\"{method['methode']}\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\" data-field=\"methode\" placeholder=\"Methodenname(Parameter):Rückgabetyp\">
                  </div>
                    """
                )
                for method in get_sorted_methods(umlClass)
            ]
        )
        # Zusammensetzen der Klassenstruktur
        classElement.innerHTML = f"""
            <div class=\"uml-class-header\">
              <input type=\"text\" value=\"{umlClass['name']}\" data-class-id=\"{umlClass['id']}\"data-field=\"name\" placeholder=\"Klassenname\" style=\"text-align: center; border: none; background-color: white; width:90%\">
            </div>
            <div class=\"uml-class-attributes\">
              <div class=\"attributes-list sortable-list\" data-class-id=\"{umlClass['id']}\">
                {attributes_html}
              </div>
              <button class=\"add-attr add-btn\" data-class-id=\"{umlClass['id']}\" style=\"width:100%; background-color: white; color:#000000 !important;\">+ </button>
            </div>

            <div class=\"uml-class-methods\">
              <div class=\"methods-list sortable-list\" data-class-id=\"{umlClass['id']}\">
                {methods_html}
              </div>
              <button class=\"add-method add-btn\" data-class-id=\"{umlClass['id']}\" style=\"width:100%; background-color: white; color:#000000 !important;\">+ </button>
            </div>
          """
        umlDiagram.appendChild(classElement)
    # Events registrieren und Größen anpassen
    addEventListeners()
    resizeUmlClasses()
    updateGetterSetterButtons()
    
    # zurück zum aktiven Element
    if active_element and active_element.tagName == "INPUT":
        # versuche, das gleiche Eingabefeld wieder zu fokussieren
        if active_method_id:
            new_input = document.querySelector(
                f'input[data-method-id="{active_method_id}"][data-field="{active_field}"][data-class-id="{active_class_id}"]'
            )
        elif active_attr_id:
            new_input = document.querySelector(
                f'input[data-attr-id="{active_attr_id}"][data-field="{active_field}"][data-class-id="{active_class_id}"]'
            )
        else:
            new_input = document.querySelector(
                f'.uml-class-header input[data-field="name"][data-class-id="{active_class_id}"]'
            )
        
        if new_input:
            new_input.focus()
            if cursor_position is not None and hasattr(new_input, 'setSelectionRange'):
                new_input.setSelectionRange(cursor_position, cursor_position)

# =============================
# Sortierung (Drag & Drop Liste)
# =============================

def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def clear_sort_drop_markers():
    """Entfernt visuelle Marker für mögliche Drop-Positionen."""
    for item in document.querySelectorAll(".sortable-item.drop-before, .sortable-item.drop-after"):
        item.classList.remove("drop-before")
        item.classList.remove("drop-after")
    for sortable_list in document.querySelectorAll(".sortable-list.drop-at-end"):
        sortable_list.classList.remove("drop-at-end")

def reset_sort_drag_state():
    """Setzt den Drag-Zustand zurück."""
    current_sort_drag["kind"] = None
    current_sort_drag["class_id"] = None
    current_sort_drag["item_id"] = None

def is_matching_sort_drag(kind, class_id):
    """Prüft, ob der aktuelle Drag-Vorgang zu Liste und Klasse passt."""
    return (
        current_sort_drag["kind"] == kind
        and current_sort_drag["class_id"] == class_id
        and current_sort_drag["item_id"] is not None
    )

def get_sort_kind_from_list_element(sort_list_elem):
    if sort_list_elem.classList.contains("attributes-list"):
        return "attr"
    if sort_list_elem.classList.contains("methods-list"):
        return "method"
    return None

def get_closest_sortable_item(target):
    if target and hasattr(target, "closest"):
        return target.closest(".sortable-item")
    return None

def reorder_class_items(classId, item_kind, source_item_id, target_item_id=None, place_before=True):
    """Ordnet Attribute oder Methoden in einer Klasse neu an."""
    for umlClass in umlClasses:
        if umlClass["id"] != classId:
            continue

        items = umlClass["attributes"] if item_kind == "attr" else umlClass["methods"]
        original_order = [item.get("id") for item in items]

        source_index = None
        for idx, item in enumerate(items):
            if item.get("id") == source_item_id:
                source_index = idx
                break
        if source_index is None:
            return False

        if target_item_id is not None and source_item_id == target_item_id:
            return False

        source_item = items.pop(source_index)

        if target_item_id is None:
            insert_index = len(items)
        else:
            target_index = None
            for idx, item in enumerate(items):
                if item.get("id") == target_item_id:
                    target_index = idx
                    break
            if target_index is None:
                items.insert(source_index, source_item)
                return False
            insert_index = target_index if place_before else target_index + 1

        if item_kind == "method":
            first_non_constructor = 0
            while first_non_constructor < len(items) and is_constructor_method(items[first_non_constructor].get("methode")):
                first_non_constructor += 1
            insert_index = max(insert_index, first_non_constructor)

        insert_index = max(0, min(insert_index, len(items)))
        items.insert(insert_index, source_item)

        if item_kind == "method":
            constructors = [m for m in items if is_constructor_method(m.get("methode"))]
            others = [m for m in items if not is_constructor_method(m.get("methode"))]
            umlClass["methods"] = constructors + others
            new_order = [item.get("id") for item in umlClass["methods"]]
        else:
            new_order = [item.get("id") for item in items]

        return original_order != new_order
    return False

def handle_sort_drag_start(event):
    target = event.currentTarget if event.currentTarget else event.target
    if not target:
        return

    kind = target.getAttribute("data-sort-kind")
    class_id = _safe_int(target.getAttribute("data-class-id"))
    item_id = _safe_int(target.getAttribute("data-item-id"))
    if kind not in ["attr", "method"] or class_id is None or item_id is None:
        return

    current_sort_drag["kind"] = kind
    current_sort_drag["class_id"] = class_id
    current_sort_drag["item_id"] = item_id

    target.classList.add("sorting-drag")
    if event.dataTransfer:
        event.dataTransfer.effectAllowed = "move"
        event.dataTransfer.setData("text/plain", f"{kind}:{class_id}:{item_id}")

def handle_sort_drag_end(event):
    target = event.currentTarget if event.currentTarget else event.target
    if target and target.classList:
        target.classList.remove("sorting-drag")
    clear_sort_drop_markers()
    reset_sort_drag_state()

def handle_sort_list_dragover(event):
    sort_list_elem = event.currentTarget if event.currentTarget else None
    if not sort_list_elem:
        return

    kind = get_sort_kind_from_list_element(sort_list_elem)
    class_id = _safe_int(sort_list_elem.getAttribute("data-class-id"))
    if not kind or class_id is None or not is_matching_sort_drag(kind, class_id):
        return

    event.preventDefault()
    if event.dataTransfer:
        event.dataTransfer.dropEffect = "move"

    clear_sort_drop_markers()
    target_item = get_closest_sortable_item(event.target)
    if (
        target_item
        and target_item.getAttribute("data-sort-kind") == kind
        and _safe_int(target_item.getAttribute("data-class-id")) == class_id
    ):
        rect = target_item.getBoundingClientRect()
        place_before = event.clientY < (rect.top + rect.height / 2)
        target_item.classList.add("drop-before" if place_before else "drop-after")
    else:
        sort_list_elem.classList.add("drop-at-end")

def handle_sort_list_drop(event):
    sort_list_elem = event.currentTarget if event.currentTarget else None
    if not sort_list_elem:
        return

    kind = get_sort_kind_from_list_element(sort_list_elem)
    class_id = _safe_int(sort_list_elem.getAttribute("data-class-id"))
    if not kind or class_id is None or not is_matching_sort_drag(kind, class_id):
        return

    event.preventDefault()

    source_item_id = current_sort_drag["item_id"]
    target_item = get_closest_sortable_item(event.target)
    moved = False

    if (
        target_item
        and target_item.getAttribute("data-sort-kind") == kind
        and _safe_int(target_item.getAttribute("data-class-id")) == class_id
    ):
        target_item_id = _safe_int(target_item.getAttribute("data-item-id"))
        rect = target_item.getBoundingClientRect()
        place_before = event.clientY < (rect.top + rect.height / 2)
        moved = reorder_class_items(class_id, kind, source_item_id, target_item_id, place_before)
    else:
        moved = reorder_class_items(class_id, kind, source_item_id, None, False)

    clear_sort_drop_markers()
    reset_sort_drag_state()

    if moved:
        renderUmlDiagram()
        generateCode()

# ====================================
# Event-Handling & Benutzerinteraktion
# ====================================

def addEventListeners():
    """ Registriert alle EventListener für das UML-Diagramm """
    # Klassenname ändern
    for input_elem in document.querySelectorAll(".uml-class-header input"):
        def on_class_input(event):
            classId = int(event.target.getAttribute("data-class-id"))
            updateClassName(classId, event.target.value)
        add_listener(input_elem, "input", on_class_input)
    # Attribute und Methoden bearbeiten
    for input_elem in document.querySelectorAll(".uml-item input"):
        def on_item_input(event):
            classId = int(event.target.getAttribute("data-class-id"))
            field = event.target.getAttribute("data-field")
            # Attribut ändern
            if event.target.hasAttribute("data-attr-id"):
                attrId = int(event.target.getAttribute("data-attr-id"))
                updateAttribute(classId, attrId, field, event.target.value)
            # Methode ändern
            elif event.target.hasAttribute("data-method-id"):
                methodId = int(event.target.getAttribute("data-method-id"))
                updateMethod(classId, methodId, field, event.target.value)
        add_listener(input_elem, "input", on_item_input)

    # Neues Attribut hinzufügen
    for button in document.querySelectorAll(".add-attr"):
        def on_add_attr(event):
            classId = int(event.target.getAttribute("data-class-id"))
            addAttribute(classId)
        add_listener(button, "click", on_add_attr)
    # Neue Methode hinzufügen
    for button in document.querySelectorAll(".add-method"):
        def on_add_method(event):
            classId = int(event.target.getAttribute("data-class-id"))
            addMethod(classId)
        add_listener(button, "click", on_add_method)

    # Attribut löschen
    for button in document.querySelectorAll(".remove-attr"):
        def on_remove_attr(event):
            classId = int(event.target.getAttribute("data-class-id"))
            attrId = int(event.target.getAttribute("data-attr-id"))
            removeAttribute(classId, attrId)
        add_listener(button, "click", on_remove_attr)
    # Methode löschen
    for button in document.querySelectorAll(".remove-method"):
        def on_remove_method(event):
            classId = int(event.target.getAttribute("data-class-id"))
            methodId = int(event.target.getAttribute("data-method-id"))
            removeMethod(classId, methodId)
        add_listener(button, "click", on_remove_method)
    
    # Zugriffstyp (+ / - / #) ändern
    for button in document.querySelectorAll(".access-btn"):
        add_listener(button, "click", changeAccessModifier)

    for button in document.querySelectorAll(".getter"):
        add_listener(button, "click", handle_getter_click)
    
    for button in document.querySelectorAll(".setter"):
        add_listener(button, "click", handle_setter_click)

    # Drag & Drop Sortierung für Attribute/Methoden
    for sortable_item in document.querySelectorAll(".sortable-item"):
        add_listener(sortable_item, "dragstart", handle_sort_drag_start)
        add_listener(sortable_item, "dragend", handle_sort_drag_end)

    for sortable_list in document.querySelectorAll(".sortable-list"):
        add_listener(sortable_list, "dragover", handle_sort_list_dragover)
        add_listener(sortable_list, "drop", handle_sort_list_drop)


def updateClassName(classId, newName):
    """ Aktualisiert den Namen einer UML-Klasse """
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["name"] = newName
            generateCode()
            resizeUmlClasses()
            return

# =====================
# Konstruktor-Erkennung
# =====================
 
def is_constructor_method(value):
    """ Prüft, ob eine Methode ein Konstruktor ist """
    return str(value).lstrip().startswith("c __init__")

def is_explicit_empty_constructor(value):
    """True, wenn der Nutzer explizit einen leeren Konstruktor eingibt (c __init__())."""
    method_text = str(value).strip()
    if not method_text.lstrip().startswith("c __init__"):
        return False
    if "(" not in method_text or ")" not in method_text:
        return False
    inside = method_text.split("(", 1)[1].split(")", 1)[0].strip()
    return inside == ""

def build_constructor_signature(umlClass):
    """ Erstellt die Konstruktor-Signatur automatisch """
    params = [attr["attr"] for attr in umlClass["attributes"]]
    params = [p for p in params if str(p).strip() != ""]
    params_text = ", ".join(params)
    return f"c __init__({params_text})"

def get_attribute_param_list(umlClass):
    """ Liefert Attribut-Parameterliste """
    params = [attr["attr"] for attr in umlClass["attributes"]]
    return [p.strip() for p in params if str(p).strip() != ""]

def sync_constructor_method(umlClass):
    """ Synchronisiert Konstruktor mit Attributen """
    signature = build_constructor_signature(umlClass)
    for method in umlClass["methods"]:
        if is_constructor_method(method.get("methode")) and method.get("auto", True):
            method["methode"] = signature
            method["access"] = ""

def refresh_constructor_inputs(umlClass):
    """ Aktualisiert Konstruktor-Eingabefelder im UI """
    for method in umlClass["methods"]:
        if is_constructor_method(method.get("methode")):
            input_elem = document.querySelector(
                f'input[data-method-id="{method["id"]}"][data-field="methode"]'
            )
            if input_elem:
                input_elem.value = method["methode"]
                
def refresh_inputs(umlClass):
    """ Aktualisiert Eingabefelder im UI """
    for method in umlClass["methods"]:
        input_elem = document.querySelector(
            f'input[data-method-id="{method["id"]}"][data-field="methode"]'
        )
        if input_elem:
            input_elem.value = method["methode"]


# ====================================
# Daten-Updates (Attribute & Methoden)
# ====================================

def updateAttribute(classId, attrId, field, value):
    """Aktualisiert Attribut + synchronisiert Getter/Setter automatisch"""

    for umlClass in umlClasses:
        if umlClass["id"] != classId:
            continue
        for attribute in umlClass["attributes"]:
            if attribute["id"] != attrId:
                continue

            # ===== Alter Attributname =====
            old_full = attribute.get("attr", "")
            old_attr_name = old_full.split(":")[0].strip() if ":" in old_full else old_full.strip()

            # ===== Attribut aktualisieren =====
            attribute[field] = value

            # ===== Neuer Attributname =====
            new_full = attribute.get("attr", "")
            new_attr_name = new_full.split(":")[0].strip() if ":" in new_full else new_full.strip()

            # ⭐⭐⭐ Zentrale Synchronisierungslogik ⭐⭐⭐
            if old_attr_name or new_attr_name:
                update_getter_setter_names(
                    umlClass,
                    old_attr_name,
                    new_attr_name
                )

            # Konstruktor synchronisieren
            sync_constructor_method(umlClass)
            refresh_constructor_inputs(umlClass)

            # UI aktualisieren
            updateGetterSetterButtons()
            generateCode()
            resizeUmlClasses()

            return

def update_getter_setter_names(umlClass, old_attr_name, new_attr_name):
    """
    Wenn ein Attribut umbenannt wird oder sich der Typ aendert:
    Getter/Setter-Methodensignaturen automatisch synchronisieren
    """

    # Neuen Attributtyp finden
    new_attr_type = ""
    for attr in umlClass["attributes"]:
        full = attr.get("attr", "")
        if ":" in full:
            name, typ = [x.strip() for x in full.split(":", 1)]
        else:
            name = full.strip()
            typ = ""

        if name == new_attr_name:
            new_attr_type = typ
            break

    # Getter/Setter-Methoden aktualisieren
    for method in umlClass["methods"]:
        text = method.get("methode", "")
        if not text:
            continue

        method_name = text.split("(")[0].strip()

        # ===== getter =====
        if method_name.startswith("get_"):
            attr = method_name[4:]
            if attr == old_attr_name or attr == new_attr_name:
                method["methode"] = build_getter_signature(
                    new_attr_name,
                    new_attr_type
                )

        # ===== setter =====
        elif method_name.startswith("set_"):
            attr = method_name[4:]
            if attr == old_attr_name or attr == new_attr_name:
                method["methode"] = build_setter_signature(
                    new_attr_name,
                    new_attr_type
                )

    refresh_inputs(umlClass)


def updateMethod(classId, methodId, field, value):
    """ Aktualisiert eine Methode """
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for method in umlClass["methods"]:
                if method["id"] == methodId:
                    was_constructor = is_constructor_method(method.get("methode"))
                    old_value = method.get(field, "")
                    
                    # Methode aktualisieren
                    method[field] = value
                    rerender = False
                    
                    if field == "methode":
                        is_constructor = is_constructor_method(value)

                        if is_constructor:
                            method["access"] = ""

                            # Wenn der Nutzer explizit einen leeren Konstruktor einträgt, soll er NICHT automatisch
                            # mit den Attributen synchronisiert werden.
                            if is_explicit_empty_constructor(value):
                                method["auto"] = False
                            else:
                                signature = build_constructor_signature(umlClass)
                                typed_params = get_constructor_params(umlClass, value, False)
                                attr_params = get_attribute_param_list(umlClass)

                                # Auto-Sync nur, wenn Nutzer "c __init__" (ohne explizite leere Klammern) nutzt,
                                # die Signatur exakt der Auto-Signatur entspricht, oder Parameter den Attributen entsprechen.
                                if value.strip() in ["c __init__", signature] or typed_params == attr_params:
                                    method["auto"] = True
                                    sync_constructor_method(umlClass)
                                else:
                                    method["auto"] = False

                            rerender = True
                        elif was_constructor:
                            method["auto"] = False
                            rerender = True

                        # Wenn sich der Methodenname aendert, Getter/Setter-Buttonstatus aktualisieren
                        renderUmlDiagram()
                    
                    # Code immer generieren (auch bei normalen Updates)
                    generateCode()
                    resizeUmlClasses()
                    
                    # UML-Diagramm bei Bedarf neu rendern
                    if rerender:
                        renderUmlDiagram()
                    return

# ======================
# Hinzufügen & Entfernen
# ======================

# Setzt Zugriffstyp
def setAccessModifier(classId, attrId, methodId, accessType):
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            if attrId is not None:
                for attribute in umlClass["attributes"]:
                    if attribute["id"] == attrId:
                        attribute["access"] = accessType
            if methodId is not None:
                for method in umlClass["methods"]:
                    if method["id"] == methodId:
                        method["access"] = accessType
            return

# Fügt ein Attribut hinzu
def addAttribute(classId):
    global nextAttributeId
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["attributes"].append({
                "id": nextAttributeId, 
                "attr": "", 
                "access": "",
                "has_getter": False,
                "has_setter": False
            })
            nextAttributeId += 1
            sync_constructor_method(umlClass)
            renderUmlDiagram()
            return

# Fügt eine Methode hinzu
def addMethod(classId):
    global nextMethodId
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["methods"].append({
                "id": nextMethodId, 
                "methode": "", 
                "access": "",
                "auto_generated": False
            })
            nextMethodId += 1
            updateGetterSetterButtons()
            renderUmlDiagram()
            return
        
def handle_getter_click(event):
    """Handhabt Getter-Button-Klick"""
    target = event.target
    classId = int(target.dataset.classId)
    attrId = int(target.dataset.attrId)
    
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for attribute in umlClass["attributes"]:
                if attribute["id"] == attrId:
                    attr_str = attribute["attr"]
                    if not attr_str or attr_str.strip() == "":
                        return  # Kein Attributname vorhanden
                    
                    attr_name = attr_str.split(":")[0].strip() if ":" in attr_str else attr_str.strip()
                    attr_type = get_attr_type(attr_str)
                    
                    # Prüfen, ob bereits Getter vorhanden ist
                    existing = get_existing_getter_setter(umlClass, attr_name)
                    if existing["has_getter"]:
                        # Getter bereits vorhanden, Button sollte bereits deaktiviert sein
                        return
                    
                    # Automatisch generierten Getter hinzufügen
                    add_getter_method(umlClass, attr_name, attr_type)
                    attribute["has_getter"] = True
                    
                    renderUmlDiagram()  # Neu rendern, um Button zu deaktivieren
                    generateCode()
                    return

def handle_setter_click(event):
    """Handhabt Setter-Button-Klick"""
    target = event.target
    classId = int(target.dataset.classId)
    attrId = int(target.dataset.attrId)
    
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for attribute in umlClass["attributes"]:
                if attribute["id"] == attrId:
                    attr_str = attribute["attr"]
                    if not attr_str or attr_str.strip() == "":
                        return  # Kein Attributname vorhanden
                    
                    attr_name = attr_str.split(":")[0].strip() if ":" in attr_str else attr_str.strip()
                    attr_type = get_attr_type(attr_str)
                    
                    # Prüfen, ob bereits Setter vorhanden ist
                    existing = get_existing_getter_setter(umlClass, attr_name)
                    if existing["has_setter"]:
                        # Setter bereits vorhanden, Button sollte bereits deaktiviert sein
                        return
                    
                    # Automatisch generierten Setter hinzufügen
                    add_setter_method(umlClass, attr_name, attr_type)
                    attribute["has_setter"] = True
                    
                    renderUmlDiagram()  # Neu rendern, um Button zu deaktivieren
                    generateCode()
                    return

def add_getter_method(umlClass, attr_name, attr_type):
    
    """Fügt eine Getter-Methode hinzu"""
    global nextMethodId
    getter_signature = build_getter_signature(attr_name, attr_type)
    
    # Prüfen, ob bereits vorhanden (manuell oder automatisch)
    for method in umlClass["methods"]:
        if method["methode"].startswith(f"{generate_getter_name(attr_name)}("):
            return
    
    umlClass["methods"].append({
        "id": nextMethodId,
        "methode": getter_signature,
        "access": "",
        "auto_generated": True  # Automatisch generierte Methode
    })
    nextMethodId += 1

def add_setter_method(umlClass, attr_name, attr_type):
    """Fügt eine Setter-Methode hinzu"""
    global nextMethodId
    setter_signature = build_setter_signature(attr_name, attr_type)
    
    # Prüfen, ob bereits vorhanden (manuell oder automatisch)
    for method in umlClass["methods"]:
        if method["methode"].startswith(f"{generate_setter_name(attr_name)}("):
            return
    
    umlClass["methods"].append({
        "id": nextMethodId,
        "methode": setter_signature,
        "access": "",
        "auto_generated": True  # Automatisch generierte Methode
    })
    nextMethodId += 1
    
def updateGetterSetterButtons():
    """Aktualisiert den Getter/Setter-Buttonstatus aller Attribute anhand vorhandener Methoden"""
    for umlClass in umlClasses:
        class_id = umlClass["id"]
        
        for attr in umlClass["attributes"]:
            attr_id = attr["id"]
            attr_full = attr["attr"]
            
            # Attributnamen sicher extrahieren (leere Werte beruecksichtigen)
            if not attr_full:
                attr_name = ""
            else:
                attr_parts = attr_full.split(":")
                attr_name = attr_parts[0].strip() if len(attr_parts) > 0 else attr_full.strip()
            
            if not attr_name:  # Wenn der Attributname leer ist, ueberspringen
                continue
            
            # Pruefen, ob die entsprechende Methode existiert
            has_getter = False
            has_setter = False
            
            for method in umlClass["methods"]:
                method_text = method.get("methode", "")
                if not method_text:
                    continue
                
                # Methodennamen extrahieren (ohne Parameter)
                if "(" in method_text:
                    method_name = method_text.split("(")[0].strip()
                else:
                    method_name = method_text.strip()
                
                # Getter exakt abgleichen (muss get_Attributname sein)
                if method_name == f"get_{attr_name}":
                    has_getter = True
                
                # Setter exakt abgleichen (muss set_Attributname sein)
                if method_name == f"set_{attr_name}":
                    has_setter = True
            
            # Buttons aktualisieren
            getter_btn = document.querySelector(f'.getter[data-class-id="{class_id}"][data-attr-id="{attr_id}"]')
            setter_btn = document.querySelector(f'.setter[data-class-id="{class_id}"][data-attr-id="{attr_id}"]')
            
            if getter_btn:
                if has_getter:
                    if checkObGetterTypeRichtigIst(class_id, attr_name, get_attr_type(attr_full)):
                        getter_btn.title = f"Getter für '{attr_name}' existiert und ist korrekt"
                        getter_btn.style.color = "black"
                        getter_btn.disabled = True  
                    else:
                        getter_btn.title = f"Getter für '{attr_name}' existiert, aber hat falschen Typ"
                        getter_btn.disabled = False
                else:
                    getter_btn.title = f"Getter für '{attr_name}' hinzufügen"
                    getter_btn.disabled = False  
            
            if setter_btn:
                if has_setter:
                    if checkObSetterParamGeändert(class_id, attr_name, get_attr_type(attr_full)):
                        if checkObRückgabeTypHandelt(class_id, attr_name) != "":
                            return
                        setter_btn.title = f"Setter für '{attr_name}' existiert und ist korrekt"
                        setter_btn.style.color = "black"
                        setter_btn.disabled = True  
                    else:
                        setter_btn.title = f"Setter für '{attr_name}' existiert, aber hat falschen Typ"
                        setter_btn.disabled = False
                else:
                    setter_btn.title = f"Setter für '{attr_name}' hinzufügen"
                    setter_btn.disabled = False  
                    
def checkObRückgabeTypHandelt(classId, attr_name):
    """checkt, ob der vorhandene Setter überhaupt einen Rückgabetyp hat"""
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for method in umlClass["methods"]:
                method_text = method.get("methode", "")
                if method_text.startswith(f"set_{attr_name}("):
                    # Parameter-Teil extrahieren
                    if "(" in method_text and ")" in method_text:
                        typ = method_text.split(")", 1)[1].strip()
                        return typ
    return None

def checkObGetterTypeRichtigIst(classId, attr_name, attr_type):
    """checkt, ob der vorhandene Getter den richtigen Rückgabetyp hat"""
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for method in umlClass["methods"]:
                method_text = method.get("methode", "")
                if method_text.startswith(f"get_{attr_name}("):
                    # rückgabetyp extrahieren
                    if ":" in method_text:
                        return_type = method_text.split(":")[-1].strip()
                        return return_type == attr_type
    return False
    
def checkObSetterParamGeändert(classId, attr_name, attr_type):
    """checkt, ob der vorhandene Setter den richtigen Parameter-Typ hat"""
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for method in umlClass["methods"]:
                method_text = method.get("methode", "")
                if method_text.startswith(f"set_{attr_name}("):
                    if "(" in method_text and ")" in method_text:
                        params_part = method_text.split("(", 1)[1].split(")", 1)[0].strip()
                        if ":" in params_part:
                            param_name = params_part.split(":")[0].strip()
                            param_type = params_part.split(":")[-1].strip()
                            return param_type == attr_type and param_name == attr_name
                        return params_part.strip() == attr_name
    return False

def removeAttribute(classId, attrId):
    """Entfernt ein Attribut aus der Klasse"""
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            # Zuerst den zu loeschenden Attributnamen ermitteln
            for attr in umlClass["attributes"]:
                if attr["id"] == attrId:
                    attr_name = attr["attr"].split(":")[0].strip() if ":" in attr["attr"] else attr["attr"].strip()
                    
                    # Zugehoerige Getter-/Setter-Methoden loeschen
                    umlClass["methods"] = [
                        m for m in umlClass["methods"] 
                        if not (
                            m.get("methode", "").split("(")[0].strip() in [f"get_{attr_name}", f"set_{attr_name}"]
                        )
                    ]
                    break
            
            # Danach das Attribut selbst loeschen
            umlClass["attributes"] = [a for a in umlClass["attributes"] if a["id"] != attrId]
            sync_constructor_method(umlClass)
            updateGetterSetterButtons()  # Buttonstatus aktualisieren
            renderUmlDiagram()
            generateCode()
            return

# Entfernt eine Methode
def removeMethod(classId, methodId):
    """Entfernt eine Methode aus der Klasse"""
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            method_to_delete = None
            for method in umlClass["methods"]:
                if method["id"] == methodId:
                    method_to_delete = method
                    break
            
            if method_to_delete:
                # Prüfen, ob es eine Getter/Setter-Methode ist
                method_name = method_to_delete["methode"].split("(")[0].strip()
                attr_name = extract_attr_name_from_method(method_name)
                
                if attr_name and not method_to_delete.get("auto_generated", False):
                    # Manuell hinzugefügte Getter/Setter-Methode
                    # Entsprechenden Button wieder aktivieren
                    for attr in umlClass["attributes"]:
                        attr_str = attr.get("attr", "")
                        current_attr_name = attr_str.split(":")[0].strip() if ":" in attr_str else attr_str.strip()
                        if current_attr_name == attr_name:
                            if method_name.startswith("get_"):
                                attr["has_getter"] = True  # Getter-Button aktivieren
                            elif method_name.startswith("set_"):
                                attr["has_setter"] = True  # Setter-Button aktivieren
            
            # Methode entfernen
            umlClass["methods"] = [m for m in umlClass["methods"] if m["id"] != methodId]
            updateGetterSetterButtons()
            renderUmlDiagram()
            generateCode()
            return

# ====================
# UI & Hilfsfunktionen
# ====================

def toggleCodePanel(event=None):
    """ Öffnet oder schließt das Code-Panel """
    codePanel = document.getElementById("codePanel")
    if codePanel.classList.contains("collapsed"):
        codePanel.classList.remove("collapsed")
    else:
        codePanel.classList.add("collapsed")

# Liefert Standardwert für Datentyp
def getValueForType(type_value):
    typeMapping = {
        "String": '""',
        "str": '""',
        "Integer": "0",
        "int": "0",
        "Float": "0.0",
        "float": "0.0",
        "Boolean": "True",
        "bool": "True",
        "List": "[]",
        "list": "[]",
        "Dict": "{}",
        "dict": "{}",
        "Tuple": "()",
        "tuple": "()",
    }
    return typeMapping.get(type_value, "None")

# Liest Parameter aus Konstruktor
def get_constructor_params(umlClass, method_value, is_auto):
    if is_auto:
        params = [attr["attr"] for attr in umlClass["attributes"]]
        return [p for p in params if str(p).strip() != ""]
    method_text = str(method_value)
    if "(" not in method_text or ")" not in method_text:
        return []
    parameters_part = method_text.split("(", 1)[1].split(")", 1)[0].strip()
    if parameters_part == "":
        return []
    return [p.strip() for p in parameters_part.split(",")]

# ===================
# Methoden-Sortierung
# ===================

def get_sorted_methods(umlClass):
    """ Sortiert Methoden so, dass Konstruktoren zuerst kommen """
    methods = list(umlClass["methods"])
    constructors = [m for m in methods if is_constructor_method(m.get("methode"))]
    others = [m for m in methods if not is_constructor_method(m.get("methode"))]
    return constructors + others

# ================
# Code-Generierung
# ================

def generateCode():
    """ Generiert Python-Code aus dem UML-Modell """
    codeContainer = document.getElementById("codeContainer")
    code = ""

    # Alle Klassen durchlaufen
    for umlClass in umlClasses:
        # Klassendefinition generieren
        code += f"<div class=\"code-line\"><span class=\"code-keyword\">class</span> <span class=\"code-class\">{umlClass['name']}</span>:</div>"

        """ Konstruktor generieren """
        constructor_method = None
        for method in umlClass["methods"]:
            if is_constructor_method(method.get("methode")):
                constructor_method = method
                break
        if constructor_method:
            methodename = "__init__"
            code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">def</span> <span class=\"code-function\">{methodename}</span>(<span class=\"code-keyword\">self</span>"

            params_text = ""
            if "(" in constructor_method["methode"] and ")" in constructor_method["methode"]:
                params_text = constructor_method["methode"].split("(", 1)[1].split(")", 1)[0].strip()
            if params_text:
                parameters = params_text.split(",")
                for i, param in enumerate(parameters):
                    param = param.strip()
                    code += ", "
                    code += f"{param}"

            code += "):</div>"

            # Konstruktor-Body generieren
            param_list = get_constructor_params(umlClass, constructor_method["methode"], constructor_method.get("auto", True))
            for param in param_list:
                paramName = param.split(":")[0].strip() if ":" in param else param.strip()
                paramAccess = ""
                for attr in umlClass["attributes"]:
                    attribute = attr["attr"]
                    parts = [a.strip() for a in attribute.split(":")]
                    current_attr_name = parts[0] if len(parts) > 0 else ""
                    current_attr_type = parts[1] if len(parts) > 1 else ""
                    if current_attr_name == paramName:
                        access = attr.get("access", "")
                        if access == "-":  # privates Attribut
                            paramAccess = "__"
                        elif access == "#":  # protected Attribut
                            paramAccess = "_"
                        break
                code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{paramAccess}{paramName}: {current_attr_type} = {paramName}</span></div>"
            if not param_list:
                for attr in umlClass["attributes"]:
                    attribute = attr["attr"]
                    parts = [a.strip() for a in attribute.split(":")]
                    current_attr_name = parts[0] if len(parts) > 0 else ""
                    current_attr_type = parts[1] if len(parts) > 1 else ""
                    access = attr.get("access", "")
                    if access == "-":  # privates Attribut
                        paramAccess = "__"
                    elif access == "#":  # protected Attribut
                        paramAccess = "_"
                    code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{paramAccess}{current_attr_name}: {current_attr_type} = {getValueForType(current_attr_type)}</span></div>"
            code += "<div class=\"code-line\"></div>"
        
               
        # Normale Methoden generieren
        for method in get_sorted_methods(umlClass):
            if str(method["methode"]).strip() == "":
                continue
            if is_constructor_method(method.get("methode")):
                continue
            
            methodename = method["methode"].split("(")[0].strip()
            #checken des Zugriffstyps eine Methode
            methodAccess = method.get("access", "")
            if methodAccess == "-":  # privates Attribut
                vorParam = "__"
            elif methodAccess == "#":  # protected Attribut
                vorParam = "_"
            else:  # öffentliches Attribut
                vorParam = ""
            code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">def</span> <span class=\"code-function\">{vorParam}{methodename}</span>(<span class=\"code-keyword\">self</span>"
            if "(" in method["methode"] and ")" in method["methode"]:
                params_text = method["methode"].split("(", 1)[1].split(")", 1)[0].strip()
                if params_text:
                    code += ", "
                    parameters = params_text.split(",")
                    for i, param in enumerate(parameters):
                        param = param.strip()
                        # Prüfen, ob Typ angegeben ist
                        if ":" in param:
                            try:
                                vorParam = ""
                                # Typ und Name extrahieren
                                paramName, paramTyp = [p.strip() for p in param.split(":", 1)]
                                if i > 0:
                                    code += ", "
                                code += f"{paramName}:{paramTyp}"
                            except:
                                if i > 0:
                                    code += ", "
                                code += f"{param}"
                        else:
                            if i > 0:
                                code += ", "
                            code += f"{param}"

            code += ")"
            methodeInhalt = False
            
            # Methode Rückgabewert
            for methode in umlClass["methods"]:
                if methode["id"] == method["id"]:
                    if "):" in methode["methode"] and methode["methode"].split("):")[-1].strip() != "":
                        return_type = methode["methode"].split("):")[-1].strip()
                        code += f"&nbsp; -> <span class=\"code-type\">{return_type}:</span></div>"
                        methodeInhalt= True
                    break
            
            if(not methodeInhalt):
                code += ":"
            
            parametersPart = []
            if "(" in method["methode"] and ")" in method["methode"]:
                params_text = method["methode"].split("(", 1)[1].split(")", 1)[0].strip()
                if params_text:
                    parametersPart = [p.strip() for p in params_text.split(",")]
            
            # Getter Methode
            if(methodename.startswith("get_")):
                attr_name = methodename[4:]
                for attr in umlClass["attributes"]:
                    attribute = attr["attr"]
                    parts = [a.strip() for a in attribute.split(":")]
                    current_attr_name = parts[0] if len(parts) > 0 else ""
                    if current_attr_name == attr_name:
                        paramAccess = attr.get("access", "")
                        break
                if paramAccess == "-":  # privates Attribut
                    vorParam = "__"
                elif paramAccess == "#":  # protected Attribut
                    vorParam = "_"
                else:  # öffentliches Attribut
                    vorParam = ""
                code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">return</span> <span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{vorParam}{attr_name}</span></div>"
            
            # Setter Methode
            elif(methodename.startswith("set_")):
                attr_name = methodename[4:]
                if len(parametersPart) > 0:
                    param_name = parametersPart[0].split(":")[0].strip()  
                else:
                    # Fallback, falls kein Parameter definiert ist, sollte eine Werte nach der Type der Attribute nehmen
                    for attr in umlClass["attributes"]:
                        attribute = attr["attr"]
                        parts = [a.strip() for a in attribute.split(":")]
                        current_attr_name = parts[0] if len(parts) > 0 else ""
                        if current_attr_name == attr_name:
                            attrType = parts[1] if len(parts) > 1 else ""
                            param_name = getValueForType(attrType)
                            break
                    if 'param_name' not in locals():
                        code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-warning\">!! keine Attribute / Parameter</span></div>"
                        code += "<div class=\"code-line\"></div>"
                        continue
                for attr in umlClass["attributes"]:
                    attribute = attr["attr"]
                    parts = [a.strip() for a in attribute.split(":")]
                    current_attr_name = parts[0] if len(parts) > 0 else ""
                    if current_attr_name == attr_name:
                        paramAccess = attr.get("access", "")
                        break
                if paramAccess == "-":  # privates Attribut
                    vorParam = "__"
                elif paramAccess == "#":  # protected Attribut
                    vorParam = "_"
                else:  # öffentliches Attribut
                    vorParam = ""
                code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{vorParam}{attr_name} = {param_name}</span></div>"
            # Sonstige Methoden
            else:
                #code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">pass</span></div>"
                """ testen ob return typ vorhanden ist """
                methodeType = ""
                if "):" in method["methode"] and method["methode"].split("):")[-1].strip() != "":
                    methodeType = method["methode"].split("):")[-1].strip()
                if methodeType != "":
                    code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">return</span> <span> {getValueForType(methodeType)} </span> </div>"
                else:
                    code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">pass</span></div>"

            code += "<div class=\"code-line\"></div>"
    codeContainer.innerHTML = code

# ========================
# Modussteuerung & Ansicht
# ========================

def modusWechselnNachAnsicht(event=None):
    """ Wechselt in den Ansichtsmodus (nur Lesen) """
    button = document.getElementById("ansichtmodus")
    umlPanel = document.getElementById('umlDiagram')
    umlPanel.classList.add('collapsed')
    #button.innerHTML = '<img src = "button/pencil-slash-svgrepo-com.svg" alt= "Ansicht" class = "button-icon"><span class="tooltiptext">Ansichtsmodus</span>'
    ansichtModus()

def modusWechselnNachBearbeiten(event=None):
    """ Wechselt in den Bearbeitungsmodus """
    button = document.getElementById("bearbeitenModus")
    umlPanel = document.getElementById('umlDiagram')
    #button.innerHTML = '<img src = "button/pencil-svgrepo-com.svg" alt= "bearbeiten" class = "button-icon"><span class="tooltiptext">Bearbeitungsmodus</span>'
    umlPanel.classList.remove('collapsed')
    renderUmlDiagram()

def access_display(value):
    """ Hilfsfunktion zur Anzeige von Zugriffsmodifikatoren """
    return "null" if value is None else value

def ansichtModus():
    """Rendert das UML-Diagramm im Ansichtsmodus  """
    umlDiagram = document.getElementById("umlDiagram")
    umlDiagram.innerHTML = ""

    for umlClass in umlClasses:
        classElement = document.createElement("div")
        classElement.className = "uml-class"
        # Attribute (readonly)
        attributes_html = "".join(
            [
                f"""
                  <div class=\"uml-item\">
                    <input type=\"text\" value=\"{access_display(attri.get('access'))} {attri['attr']}\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\" data-field=\"attr\" placeholder=\"Attributname:Datentyp\" readonly>
                  </div>
                """
                for attri in umlClass["attributes"]
            ]
        )
        # Methoden (readonly)
        methods_html = "".join(
            [
                f"""
                  <div class=\"uml-item\">
                    <input type=\"text\" value=\"{access_display(method.get('access'))} {method['methode']}\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\" data-field=\"methode\" placeholder=\"Methodenname(Parameter):Rückgabetyp\" readonly>
                  </div>
                """
                for method in get_sorted_methods(umlClass)
            ]
        )
        # Klassendarstellung zusammensetzen
        classElement.innerHTML = f"""
            <div class=\"uml-class-header\">
              <input type=\"text\" value=\"{umlClass['name']}\" data-class-id=\"{umlClass['id']}\" data-field=\"name\" placeholder=\"Klassenname\" readonly style=\"text-align: center; border: none; background-color: white;\">
            </div>
            <div class=\"uml-class-attributes\">
              <div class=\"attributes-list\" data-class-id=\"{umlClass['id']}\">
                {attributes_html}
              </div>
            </div>

            <div class=\"uml-class-methods\">
              <div class=\"methods-list\" data-class-id=\"{umlClass['id']}\">
                {methods_html}
              </div>
            </div>
          """
        umlDiagram.appendChild(classElement)

    addEventListeners()
    resizeUmlClasses()

# =========================
# JSON-Export & Import (UI)
# =========================

# Öffnet den Export-Dialog
def openExportModal(event=None):
    jsonModalTitle.textContent = "JSON exportieren"
    jsonModalTextarea.value = json.dumps({"umlClasses": umlClasses}, indent=2)
    jsonModalTextarea.readOnly = True
    jsonModalPrimary.textContent = "Kopieren"
    jsonModalTertiary.textContent = "Als JSON herunterladen"
    jsonModalSecondary.textContent = "Schließen"
    set_onclick(jsonModalPrimary, copyJsonToClipboard)
    set_onclick(jsonModalTertiary, downloadJsonFromTextarea)
    set_onclick(jsonModalSecondary, closeJsonModal)
    set_onclick(jsonModalClose, closeJsonModal)
    jsonModalOverlay.classList.add("active")
    jsonModalOverlay.setAttribute("aria-hidden", "false")
    jsonModalTextarea.focus()
    jsonModalTextarea.select()

# Öffnet den Import-Dialog
def openImportModal(event=None):
    jsonModalTitle.textContent = "JSON importieren"
    jsonModalTextarea.value = ""
    jsonModalTextarea.readOnly = False
    jsonModalPrimary.textContent = "Importieren"
    jsonModalTertiary.textContent = "Als JSON hochladen"
    jsonModalSecondary.textContent = "Schließen"
    set_onclick(jsonModalPrimary, importJsonState)
    set_onclick(jsonModalTertiary, triggerJsonFilePicker)
    set_onclick(jsonModalSecondary, closeJsonModal)
    set_onclick(jsonModalClose, closeJsonModal)
    jsonModalOverlay.classList.add("active")
    jsonModalOverlay.setAttribute("aria-hidden", "false")
    jsonModalTextarea.focus()

# Schließt das Modal-Fenster
def closeJsonModal(event=None):
    jsonModalOverlay.classList.remove("active")
    jsonModalOverlay.setAttribute("aria-hidden", "true")

# Kopiert JSON in die Zwischenablage
def copyJsonToClipboard(event=None):
    text = jsonModalTextarea.value
    if not text:
        return
    # Prüft, ob die moderne Clipboard-API im Browser verfügbar ist 
    if navigator.clipboard and navigator.clipboard.writeText:
        """  Versucht, den Text asynchron in die Zwischenablage zu kopieren"""
        promise = navigator.clipboard.writeText(text)
        # Callback-Funktion bei erfolgreichem Kopieren
        def on_copy_success(e=None):
            closeJsonModal()
        # Callback-Funktion bei Fehler während des Kopiervorgangs
        def on_copy_error(e=None):
            """ Markiert den Text zur manuellen Kopie """
            jsonModalTextarea.select() 
            document.execCommand("copy")
            closeJsonModal()
        # Erstellt Proxies für die Callback-Funktionen (Pyodide erforderlich)
        success_proxy = create_proxy(on_copy_success)
        error_proxy = create_proxy(on_copy_error)
        """  Speichert die Proxies, um Garbage Collection zu verhindern """
        event_proxies.append(success_proxy)
        event_proxies.append(error_proxy)
        promise.then(success_proxy).catch(error_proxy)
    else:
        jsonModalTextarea.select()
        document.execCommand("copy")
        closeJsonModal()

# Liest den JSON-Text aus dem Export-Textfeld 
def downloadJsonFromTextarea(event=None):
    text = jsonModalTextarea.value.strip()
    if not text:
        return
    downloadJsonFile(text)

# Lädt JSON als Datei herunter
def downloadJsonFile(text):
    filename = "uml-classes.json"
    blob = window.Blob.new([text], {"type": "application/json"})
    url = window.URL.createObjectURL(blob)
    link = document.createElement("a")
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

# Öffnet Dateiauswahl für JSO
def triggerJsonFilePicker(event=None):
    if jsonFileInput:
        jsonFileInput.value = ""
        jsonFileInput.click()

# Liest ausgewählte JSON-Datei
def handleJsonFileInput(event=None):
    files = jsonFileInput.files
    if not files or files.length == 0:
        return
    file = files.item(0)
    reader = window.FileReader.new()

    # Wird aufgerufen, wenn eine JSON-Datei ausgewählt wird
    def on_load(e=None):
        jsonModalTextarea.value = reader.result
        jsonModalTextarea.focus()
        importJsonState()
    # Fehler-Handler für Datei-Lesevorgang
    def on_error(e=None):
        window.alert("Datei konnte nicht gelesen werden.")

    load_proxy = create_proxy(on_load)
    error_proxy = create_proxy(on_error)
    event_proxies.append(load_proxy)
    event_proxies.append(error_proxy)
    reader.addEventListener("load", load_proxy)
    reader.addEventListener("error", error_proxy)
    reader.readAsText(file)

# ===================
# JSON Normalisierung
# ===================

def normalizeImportedClasses(data):
    """ Normalisiert die importierten UML-Klassen aus JSON """
    # Falls JSON ein Array von Klassen ist, verwenden, sonst nach "umlClasses" suchen
    incoming = data if isinstance(data, list) else data.get("umlClasses")
    if not isinstance(incoming, list):
        raise ValueError('Ungültiges JSON: erwartet ein Array oder { "umlClasses": [...] }.')

    normalized = []
    # Prüft, ob eine gültige ID vorhanden ist, sonst Index +1 verwenden
    for index, umlClass in enumerate(incoming):
        class_id = umlClass.get("id")
        class_id = class_id if isinstance(class_id, (int, float)) and math.isfinite(class_id) else index + 1

        # Normale Struktur für UML-Klassen erzeugen
        normalized.append(
            {
                "id": class_id,
                "name": umlClass.get("name") if isinstance(umlClass.get("name"), str) else "",
                "attributes": [
                    {
                        "id": attr.get("id") if isinstance(attr.get("id"), (int, float)) and math.isfinite(attr.get("id")) else idx + 1,
                        "attr": attr.get("attr") if isinstance(attr.get("attr"), str) else "",
                        "access": attr.get("access") if isinstance(attr.get("access"), str) else "",
                        "has_getter": bool(attr.get("has_getter", False)),
                        "has_setter": bool(attr.get("has_setter", False))
                    }
                    for idx, attr in enumerate(umlClass.get("attributes") or [])
                ],
                "methods": [
                    {
                        "id": method.get("id") if isinstance(method.get("id"), (int, float)) and math.isfinite(method.get("id")) else idx + 1,
                        "methode": method.get("methode") if isinstance(method.get("methode"), str) else "",
                        "access": method.get("access") if isinstance(method.get("access"), str) else "",
                        "auto_generated": bool(method.get("auto_generated", False))
                    }
                    for idx, method in enumerate(umlClass.get("methods") or [])
                ],
            }
        )
    return normalized

# =================
# IDs aktualisieren
# =================

def updateNextIdsFromState():
    """ Aktualisiert die globalen nächsten IDs für 
       Attribute und Methoden """
    global nextAttributeId, nextMethodId
    maxAttrId = 0
    maxMethodId = 0
    for umlClass in umlClasses:
        for attr in umlClass["attributes"]:
            if isinstance(attr.get("id"), (int, float)) and math.isfinite(attr.get("id")):
                maxAttrId = max(maxAttrId, attr["id"])
        for method in umlClass["methods"]:
            if isinstance(method.get("id"), (int, float)) and math.isfinite(method.get("id")):
                maxMethodId = max(maxMethodId, method["id"])
    nextAttributeId = maxAttrId + 1
    nextMethodId = maxMethodId + 1

# ===========
# JSON Import
# ===========

def importJsonState(event=None):
    """ Liest die JSON-Daten aus dem Modal und 
        importiert sie in das UML-System """

    global umlClasses
    raw = jsonModalTextarea.value.strip()
    if not raw:
        window.alert("Bitte JSON-Daten einfügen.") 
        return
    try:
        data = json.loads(raw)
        umlClasses = normalizeImportedClasses(data)
        for umlClass in umlClasses:
            sync_constructor_method(umlClass)
        updateNextIdsFromState()
        renderUmlDiagram()
        generateCode()
        localStorage.removeItem("umlPosition")
        closeJsonModal()
    except Exception:
        window.alert("Ungültiges JSON-Format.")

# ================================
# DOMContentLoaded Initialisierung
# ================================

def on_dom_content_loaded(event=None):
    """ Wird ausgeführt, wenn DOM fertig geladen ist """
    renderUmlDiagram()
    generateCode()
    updateGetterSetterButtons()
    add_listener(document.getElementById("ansichtmodus"), "click", modusWechselnNachAnsicht)
    add_listener(document.getElementById("bearbeitenModus"), "click", modusWechselnNachBearbeiten)
    add_listener(document.getElementById("toggleCode"), "click", toggleCodePanel)
    add_listener(document.getElementById("exportJson"), "click", openExportModal)
    add_listener(document.getElementById("importJson"), "click", openImportModal)

def init_handlers():
    """ Initialisiert Event-Handler beim Laden der Seite """
    if document.readyState == "loading":
        add_listener(document, "DOMContentLoaded", on_dom_content_loaded)
    else:
        on_dom_content_loaded()

    add_listener(jsonFileInput, "change", handleJsonFileInput)

# Event-Handler initialisieren
init_handlers()
