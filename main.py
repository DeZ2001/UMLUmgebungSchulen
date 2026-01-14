from js import document, window, JSON, localStorage, navigator
from pyodide.ffi import create_proxy
import math
import json

umlClasses = [
    {
        "id": 1,
        "name": "",
        "attributes": [
            {"id": 1, "attr": "", "access": ""},
        ],
        "methods": [
            {"id": 1, "methode": "", "access": ""},
        ],
    }
]

nextAttributeId = 2
nextMethodId = 2

UI_FONT = "15px 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"

measureTextWidth_canvas = None

jsonModalOverlay = document.getElementById("jsonModalOverlay")
jsonModalTitle = document.getElementById("jsonModalTitle")
jsonModalTextarea = document.getElementById("jsonModalTextarea")
jsonModalPrimary = document.getElementById("jsonModalPrimary")
jsonModalSecondary = document.getElementById("jsonModalSecondary")
jsonModalClose = document.getElementById("jsonModalClose")

event_proxies = []


def add_listener(element, event_name, handler):
    if not element:
        return
    proxy = create_proxy(handler)
    element.addEventListener(event_name, proxy)
    event_proxies.append(proxy)


def set_onclick(element, handler):
    if not element:
        return
    proxy = create_proxy(handler)
    element.onclick = proxy
    event_proxies.append(proxy)


def changeAccessModifier(event):
    target = event.target
    accessType = target.dataset.access
    classId = int(target.dataset.classId)
    if target.hasAttribute("data-attr-id"):
        attributeId = int(target.getAttribute("data-attr-id"))
        setAccessModifier(classId, attributeId, None, accessType)
        for btn in document.querySelectorAll(
            f'button[data-attr-id="{attributeId}"].access-btn'
        ):
            btn.classList.remove("selected")
    elif target.hasAttribute("data-method-id"):
        methodId = int(target.getAttribute("data-method-id"))
        setAccessModifier(classId, None, methodId, accessType)
        for btn in document.querySelectorAll(
            f'button[data-method-id="{methodId}"].access-btn'
        ):
            if btn.id == "remove":
                continue
            btn.classList.remove("selected")
    target.classList.add("selected")


def getSelected(current, expected):
    return "selected" if current == expected else ""


def measureTextWidth(text=""):
    global measureTextWidth_canvas
    if measureTextWidth_canvas is None:
        measureTextWidth_canvas = document.createElement("canvas")
    context = measureTextWidth_canvas.getContext("2d")
    if not context:
        return len(text) * 8
    context.font = UI_FONT
    return context.measureText(text).width


def calculateClassWidth(umlClass):
    padding = 80
    minWidth = 365
    umlDiagram = document.getElementById("umlDiagram")
    containerWidth = (
        (umlDiagram.parentElement.clientWidth if umlDiagram and umlDiagram.parentElement else None)
        or (umlDiagram.clientWidth if umlDiagram else None)
        or window.innerWidth
    )
    containerWidth -= 40
    maxWidth = max(minWidth, containerWidth)

    maxTextWidth = measureTextWidth(umlClass["name"])
    for attr in umlClass["attributes"]:
        maxTextWidth = max(maxTextWidth, measureTextWidth(attr["attr"]))
    for method in umlClass["methods"]:
        maxTextWidth = max(maxTextWidth, measureTextWidth(method["methode"]))

    return min(maxWidth, max(minWidth, math.ceil(maxTextWidth + padding)))


def resizeUmlClasses():
    umlDiagram = document.getElementById("umlDiagram")
    if not umlDiagram:
        return
    for index, umlClass in enumerate(umlClasses):
        classElement = umlDiagram.children[index]
        if classElement:
            classElement.style.width = f"{calculateClassWidth(umlClass)}px"


def renderUmlDiagram():
    umlDiagram = document.getElementById("umlDiagram")
    umlDiagram.innerHTML = ""
    for umlClass in umlClasses:
        classElement = document.createElement("div")
        classElement.className = "uml-class"

        attributes_html = "".join(
            [
                f"""
                  <div class=\"uml-item\">
                    <button class=\"btn-small access-btn {getSelected(attri.get('access'), '+')}\" data-access=\"+\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">+</button>
                    <button class=\"btn-small access-btn {getSelected(attri.get('access'), '-')}\" data-access=\"-\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">-</button>
                    <button class=\"btn-small access-btn {getSelected(attri.get('access'), '#')}\" data-access=\"#\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">#</button>
                    <input type=\"text\" value=\"{attri['attr']}\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\" data-field=\"attr\" placeholder=\"Attributname:Datentyp\">
                    <button class=\"remove-attr\" id=\"remove\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\">×</button>
                    <button class=\"add-btn getter\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\" style=\"background: #00000033\">g</button>
                    <button class=\"add-btn setter\" data-class-id=\"{umlClass['id']}\" data-attr-id=\"{attri['id']}\" style=\"background: #00000033\">s</button>
                  </div>
                """
                for attri in umlClass["attributes"]
            ]
        )

        methods_html = "".join(
            [
                (
                    f"""
                  <div class=\"uml-item\">
                    <button class=\"btn-small access-btn {getSelected(method.get('access'), '+')}\" data-access=\"+\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">+</button>
                    <button class=\"btn-small access-btn {getSelected(method.get('access'), '-')}\" data-access=\"-\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">-</button>
                    <button class=\"btn-small access-btn {getSelected(method.get('access'), '#')}\" data-access=\"#\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">#</button>
                    <input type=\"text\" value=\"{method['methode']}\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\" data-field=\"methode\" placeholder=\"Methodenname(Parameter):Rückgabetyp\">
                    <button class=\"remove-method\" id=\"remove\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">×</button>
                  </div>
                    """
                    if not is_constructor_method(method.get("methode"))
                    else f"""
                  <div class=\"uml-item\">
                    <div style=\"display: inline-block;\"></div>
                    <input type=\"text\" value=\"{method['methode']}\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\" data-field=\"methode\" placeholder=\"Methodenname(Parameter):Rückgabetyp\">
                    <button class=\"remove-method\" id=\"remove\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\">×</button>
                  </div>
                    """
                )
                for method in get_sorted_methods(umlClass)
            ]
        )

        classElement.innerHTML = f"""
            <div class=\"uml-class-header\">
              <input type=\"text\" value=\"{umlClass['name']}\" data-class-id=\"{umlClass['id']}\"data-field=\"name\" placeholder=\"Klassenname\" style=\"text-align: center; border: none; background-color: white; width:90%\">
            </div>
            <div class=\"uml-class-attributes\">
              <div class=\"attributes-list\" data-class-id=\"{umlClass['id']}\">
                {attributes_html}
              </div>
              <button class=\"add-attr add-btn\" data-class-id=\"{umlClass['id']}\" style=\"width:100%; background-color: white; color:#ddd !important;\">+ </button>
            </div>

            <div class=\"uml-class-methods\">
              <div class=\"methods-list\" data-class-id=\"{umlClass['id']}\">
                {methods_html}
              </div>
              <button class=\"add-method add-btn\" data-class-id=\"{umlClass['id']}\" style=\"width:100%; background-color: white; color:#ddd !important;\">+ </button>
            </div>
          """
        umlDiagram.appendChild(classElement)

    addEventListeners()
    resizeUmlClasses()


def addEventListeners():
    for input_elem in document.querySelectorAll(".uml-class-header input"):
        def on_class_input(event):
            classId = int(event.target.getAttribute("data-class-id"))
            updateClassName(classId, event.target.value)
        add_listener(input_elem, "input", on_class_input)

    for input_elem in document.querySelectorAll(".uml-item input"):
        def on_item_input(event):
            classId = int(event.target.getAttribute("data-class-id"))
            field = event.target.getAttribute("data-field")
            if event.target.hasAttribute("data-attr-id"):
                attrId = int(event.target.getAttribute("data-attr-id"))
                updateAttribute(classId, attrId, field, event.target.value)
            elif event.target.hasAttribute("data-method-id"):
                methodId = int(event.target.getAttribute("data-method-id"))
                updateMethod(classId, methodId, field, event.target.value)
        add_listener(input_elem, "input", on_item_input)

    for button in document.querySelectorAll(".add-attr"):
        def on_add_attr(event):
            classId = int(event.target.getAttribute("data-class-id"))
            addAttribute(classId)
        add_listener(button, "click", on_add_attr)

    for button in document.querySelectorAll(".add-method"):
        def on_add_method(event):
            classId = int(event.target.getAttribute("data-class-id"))
            addMethod(classId)
        add_listener(button, "click", on_add_method)

    for button in document.querySelectorAll(".remove-attr"):
        def on_remove_attr(event):
            classId = int(event.target.getAttribute("data-class-id"))
            attrId = int(event.target.getAttribute("data-attr-id"))
            removeAttribute(classId, attrId)
        add_listener(button, "click", on_remove_attr)

    for button in document.querySelectorAll(".remove-method"):
        def on_remove_method(event):
            classId = int(event.target.getAttribute("data-class-id"))
            methodId = int(event.target.getAttribute("data-method-id"))
            removeMethod(classId, methodId)
        add_listener(button, "click", on_remove_method)

    for button in document.querySelectorAll(".access-btn"):
        add_listener(button, "click", changeAccessModifier)


def updateClassName(classId, newName):
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["name"] = newName
            generateCode()
            resizeUmlClasses()
            return


def is_constructor_method(value):
    return str(value).lstrip().startswith("c __init__")


def build_constructor_signature(umlClass):
    params = [attr["attr"] for attr in umlClass["attributes"]]
    params = [p for p in params if str(p).strip() != ""]
    params_text = ", ".join(params)
    return f"c __init__({params_text})"


def get_attribute_param_list(umlClass):
    params = [attr["attr"] for attr in umlClass["attributes"]]
    return [p.strip() for p in params if str(p).strip() != ""]


def sync_constructor_method(umlClass):
    signature = build_constructor_signature(umlClass)
    for method in umlClass["methods"]:
        if is_constructor_method(method.get("methode")) and method.get("auto", True):
            method["methode"] = signature
            method["access"] = ""


def refresh_constructor_inputs(umlClass):
    for method in umlClass["methods"]:
        if is_constructor_method(method.get("methode")):
            input_elem = document.querySelector(
                f'input[data-method-id="{method["id"]}"][data-field="methode"]'
            )
            if input_elem:
                input_elem.value = method["methode"]


def updateAttribute(classId, attrId, field, value):
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for attribute in umlClass["attributes"]:
                if attribute["id"] == attrId:
                    attribute[field] = value
                    sync_constructor_method(umlClass)
                    refresh_constructor_inputs(umlClass)
                    generateCode()
                    resizeUmlClasses()
                    return


def updateMethod(classId, methodId, field, value):
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            for method in umlClass["methods"]:
                if method["id"] == methodId:
                    was_constructor = is_constructor_method(method.get("methode"))
                    method[field] = value
                    rerender = False
                    if field == "methode":
                        is_constructor = is_constructor_method(value)
                        if is_constructor:
                            method["access"] = ""
                            signature = build_constructor_signature(umlClass)
                            typed_params = get_constructor_params(umlClass, value, False)
                            attr_params = get_attribute_param_list(umlClass)
                            if value.strip() in ["c __init__", "c __init__()", signature] or typed_params == attr_params:
                                method["auto"] = True
                                sync_constructor_method(umlClass)
                            else:
                                method["auto"] = False
                            rerender = True
                        elif was_constructor:
                            method["auto"] = False
                            rerender = True
                    generateCode()
                    resizeUmlClasses()
                    if rerender:
                        renderUmlDiagram()
                    return


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


def addAttribute(classId):
    global nextAttributeId
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["attributes"].append({"id": nextAttributeId, "attr": "", "access": None})
            nextAttributeId += 1
            sync_constructor_method(umlClass)
            renderUmlDiagram()
            generateCode()
            return


def addMethod(classId):
    global nextMethodId
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["methods"].append({"id": nextMethodId, "methode": "", "access": None})
            nextMethodId += 1
            renderUmlDiagram()
            generateCode()
            return


def removeAttribute(classId, attrId):
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["attributes"] = [a for a in umlClass["attributes"] if a["id"] != attrId]
            sync_constructor_method(umlClass)
            renderUmlDiagram()
            generateCode()
            return


def removeMethod(classId, methodId):
    for umlClass in umlClasses:
        if umlClass["id"] == classId:
            umlClass["methods"] = [m for m in umlClass["methods"] if m["id"] != methodId]
            renderUmlDiagram()
            generateCode()
            return


def toggleCodePanel(event=None):
    codePanel = document.getElementById("codePanel")
    toggleButton = document.getElementById("toggleCode")
    if codePanel.classList.contains("collapsed"):
        codePanel.classList.remove("collapsed")
    else:
        codePanel.classList.add("collapsed")


def getValueForType(type_value):
    typeMapping = {
        "String": '""',
        "str": '""',
        "Integer": "0",
        "int": "0",
        "Float": "0.0",
        "float": "0.0",
        "Boolean": "false",
        "bool": "false",
        "List": "[]",
        "list": "[]",
        "Dict": "{}",
        "dict": "{}",
        "Tuple": "()",
        "tuple": "()",
    }
    return typeMapping.get(type_value, "None")


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


def get_sorted_methods(umlClass):
    methods = list(umlClass["methods"])
    constructors = [m for m in methods if is_constructor_method(m.get("methode"))]
    others = [m for m in methods if not is_constructor_method(m.get("methode"))]
    return constructors + others


def generateCode():
    codeContainer = document.getElementById("codeContainer")
    code = ""
    generateKon = False

    for umlClass in umlClasses:
        code += f"<div class=\"code-line\"><span class=\"code-keyword\">class</span> <span class=\"code-class\">{umlClass['name']}</span>:</div>"

        for method1 in get_sorted_methods(umlClass):
            if is_constructor_method(method1.get("methode")):
                if len(umlClass["attributes"]) > 0:
                    is_auto = method1.get("auto", True)
                    code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">def</span> <span class=\"code-function\">__init__</span>(<span class=\"code-keyword\">self</span>"
                    parametersPart = get_constructor_params(umlClass, method1.get("methode"), is_auto)
                    for param in parametersPart:
                        paramName, paramTyp = [p.strip() for p in param.split(":")]
                        if param in parametersPart:
                            code += ", "
                        code += f"{paramName}:{paramTyp}</span>"
                    code += "):</div>"

                    for attr in umlClass["attributes"]:
                        attribute = attr["attr"]
                        parts = [a.strip() for a in attribute.split(":")]
                        attrName = parts[0] if len(parts) > 0 else ""
                        attrType = parts[1] if len(parts) > 1 else ""
                        value = getValueForType(attrType)
                        for param in parametersPart:
                            paramName = param.split(":")[0].strip()
                            if paramName == attrName:
                                value = paramName
                        code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{attrName} = {value}</div>"
                else:
                    code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">def</span> <span class=\"code-function\">__init__</span>(<span class=\"code-keyword\">self</span>):</div>"
                    code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">pass</span></div>"

                code += "<div class=\"code-line\"></div>"
                generateKon = True

        if not generateKon:
            code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">def</span> <span class=\"code-function\">__init__</span>(<span class=\"code-keyword\">self):</span>"

            if len(umlClass["attributes"]) > 0:
                for attr in umlClass["attributes"]:
                    attribute = attr["attr"]
                    parts = [a.strip() for a in attribute.split(":")]
                    attrName = parts[0] if len(parts) > 0 else ""
                    attrType = parts[1] if len(parts) > 1 else ""
                    value = getValueForType(attrType)
                    code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{attrName} = {value}</div>"
            else:
                code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">def</span> <span class=\"code-function\">__init__</span>(<span class=\"code-keyword\">self</span>):</div>"
                code += "<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">pass</span></div>"

            code += "<div class=\"code-line\"></div>"

        for method in get_sorted_methods(umlClass):
            if str(method["methode"]).strip() == "":
                continue
            if is_constructor_method(method.get("methode")):
                continue
            methodename = method["methode"].split("(")[0].strip()
            code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">def</span> <span class=\"code-function\">{methodename}</span>(<span class=\"code-keyword\">self</span>"

            parametersPart = method["methode"].split("(")[1].split(")")[0].strip()
            parametersPart = [] if parametersPart == "" else parametersPart.split(",")
            for param in parametersPart:
                paramName, paramTyp = [p.strip() for p in param.split(":")]
                if param in parametersPart:
                    code += ", "
                code += f"{paramName}:{paramTyp}</span>"

            code += "):</div>"
            if(methodename.startswith("get_")):
                attr_name = methodename[4:]
                code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">return</span> <span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{attr_name}</span></div>"
            elif(methodename.startswith("set_")):
                attr_name = methodename[4:]
                param_name = parametersPart[0].split(":")[0].strip() if len(parametersPart) > 0 else "value"
                code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">self</span>.<span class=\"code-attribute\">{attr_name} = {param_name}</span></div>"
            else:
                code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-comment\"># TODO: Implement {methodename} method</span></div>"
                """ testen ob return typ vorhanden ist """
                methodeType = ""
                if ":" in method["methode"] and method["methode"].split("):")[-1].strip() != "":
                    methodeType = method["methode"].split("):")[-1].strip()
                if methodeType != "":
                    code += f"<div class=\"code-line\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class=\"code-keyword\">return</span> <span class=\"code-keyword\"> {getValueForType(methodeType)} </span> </div>"

            code += "<div class=\"code-line\"></div>"

    codeContainer.innerHTML = code


def modusWechselnNachAnsicht(event=None):
    button = document.getElementById("ansichtmodus")
    umlPanel = document.getElementById('umlDiagram')
    umlPanel.classList.add('collapsed')
    button.innerHTML = '<img src = "button/pencil-slash-svgrepo-com.svg" alt= "Ansicht" class = "button-icon">'
    ansichtModus()

def modusWechselnNachBearbeiten(event=None):
    button = document.getElementById("bearbeitenModus")
    umlPanel = document.getElementById('umlDiagram')
    button.innerHTML = '<img src = "button/pencil-svgrepo-com.svg" alt= "bearbeiten" class = "button-icon">'
    umlPanel.classList.remove('collapsed')
    renderUmlDiagram()


def access_display(value):
    return "null" if value is None else value


def ansichtModus():
    umlDiagram = document.getElementById("umlDiagram")
    umlDiagram.innerHTML = ""

    for umlClass in umlClasses:
        classElement = document.createElement("div")
        classElement.className = "uml-class"
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

        methods_html = "".join(
            [
                f"""
                  <div class=\"uml-item\">
                    <input type=\"text\" value=\"{access_display(method.get('access'))} {method['methode']}\" data-class-id=\"{umlClass['id']}\" data-method-id=\"{method['id']}\" data-field=\"methode\" placeholder=\"Methodenname(Parameter):Rückgabetyp\" readonly>
                  </div>
                """
                for method in umlClass["methods"]
            ]
        )

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


def openExportModal(event=None):
    jsonModalTitle.textContent = "Export JSON"
    jsonModalTextarea.value = json.dumps({"umlClasses": umlClasses}, indent=2)
    jsonModalTextarea.readOnly = True
    jsonModalPrimary.textContent = "Copy"
    jsonModalSecondary.textContent = "Close"
    set_onclick(jsonModalPrimary, copyJsonToClipboard)
    set_onclick(jsonModalSecondary, closeJsonModal)
    set_onclick(jsonModalClose, closeJsonModal)
    jsonModalOverlay.classList.add("active")
    jsonModalOverlay.setAttribute("aria-hidden", "false")
    jsonModalTextarea.focus()
    jsonModalTextarea.select()


def openImportModal(event=None):
    jsonModalTitle.textContent = "Import JSON"
    jsonModalTextarea.value = ""
    jsonModalTextarea.readOnly = False
    jsonModalPrimary.textContent = "Import"
    jsonModalSecondary.textContent = "Cancel"
    set_onclick(jsonModalPrimary, importJsonState)
    set_onclick(jsonModalSecondary, closeJsonModal)
    set_onclick(jsonModalClose, closeJsonModal)
    jsonModalOverlay.classList.add("active")
    jsonModalOverlay.setAttribute("aria-hidden", "false")
    jsonModalTextarea.focus()


def closeJsonModal(event=None):
    jsonModalOverlay.classList.remove("active")
    jsonModalOverlay.setAttribute("aria-hidden", "true")


def copyJsonToClipboard(event=None):
    text = jsonModalTextarea.value
    if not text:
        return
    if navigator.clipboard and navigator.clipboard.writeText:
        promise = navigator.clipboard.writeText(text)
        def on_copy_success(e=None):
            closeJsonModal()
        def on_copy_error(e=None):
            jsonModalTextarea.select()
            document.execCommand("copy")
            closeJsonModal()
        success_proxy = create_proxy(on_copy_success)
        error_proxy = create_proxy(on_copy_error)
        event_proxies.append(success_proxy)
        event_proxies.append(error_proxy)
        promise.then(success_proxy).catch(error_proxy)
    else:
        jsonModalTextarea.select()
        document.execCommand("copy")
        closeJsonModal()


def normalizeImportedClasses(data):
    incoming = data if isinstance(data, list) else data.get("umlClasses")
    if not isinstance(incoming, list):
        raise ValueError('Invalid JSON: expected an array or { "umlClasses": [...] }.')

    normalized = []
    for index, umlClass in enumerate(incoming):
        class_id = umlClass.get("id")
        class_id = class_id if isinstance(class_id, (int, float)) and math.isfinite(class_id) else index + 1
        normalized.append(
            {
                "id": class_id,
                "name": umlClass.get("name") if isinstance(umlClass.get("name"), str) else "",
                "attributes": [
                    {
                        "id": attr.get("id") if isinstance(attr.get("id"), (int, float)) and math.isfinite(attr.get("id")) else idx + 1,
                        "attr": attr.get("attr") if isinstance(attr.get("attr"), str) else "",
                        "access": attr.get("access") if isinstance(attr.get("access"), str) else "",
                    }
                    for idx, attr in enumerate(umlClass.get("attributes") or [])
                ],
                "methods": [
                    {
                        "id": method.get("id") if isinstance(method.get("id"), (int, float)) and math.isfinite(method.get("id")) else idx + 1,
                        "methode": method.get("methode") if isinstance(method.get("methode"), str) else "",
                        "access": method.get("access") if isinstance(method.get("access"), str) else "",
                    }
                    for idx, method in enumerate(umlClass.get("methods") or [])
                ],
            }
        )
    return normalized


def updateNextIdsFromState():
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


def importJsonState(event=None):
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


def on_dom_content_loaded(event=None):
    renderUmlDiagram()
    generateCode()
    add_listener(document.getElementById("ansichtmodus"), "click", modusWechselnNachAnsicht)
    add_listener(document.getElementById("bearbeitenModus"), "click", modusWechselnNachBearbeiten)
    add_listener(document.getElementById("toggleCode"), "click", toggleCodePanel)
    add_listener(document.getElementById("exportJson"), "click", openExportModal)
    add_listener(document.getElementById("importJson"), "click", openImportModal)


def init_handlers():
    if document.readyState == "loading":
        add_listener(document, "DOMContentLoaded", on_dom_content_loaded)
    else:
        on_dom_content_loaded()


init_handlers()
