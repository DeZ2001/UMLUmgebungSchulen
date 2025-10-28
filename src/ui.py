# UI-Controller - verwaltet die Benutzeroberfläche und nutzt die Geschäftslogik aus app.py

from pyscript import document

# Geschäftslogik-Funktionen (aus app.py kopiert für PyScript-Kompatibilität)
def hello():
    """Gibt eine Begrüßungsnachricht zurück"""
    return "Hello World von Python!"

def get_current_time():
    """Gibt die aktuelle Zeit zurück"""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

def calculate_sum(a, b):
    """Berechnet die Summe zweier Zahlen"""
    return f"{a} + {b} = {a + b}"

def get_random_fact():
    """Gibt einen zufälligen Fakt zurück"""
    facts = [
        "Python wurde 1991 von Guido van Rossum entwickelt",
        "Der Name 'Python' kommt von der Comedy-Serie 'Monty Python'",
        "Python ist eine interpretierte Programmiersprache",
        "PyScript bringt Python direkt in den Browser!"
    ]
    import random
    return random.choice(facts)

def update_display():
    """Aktualisiert die Anzeige mit verschiedenen Informationen"""
    out = document.getElementById("out")
    
    if out:
        # Erstelle einen schönen Text mit mehreren Informationen
        content = f"""
🪶 PyScript Demo erfolgreich geladen!

📝 Begrüßung: {hello()}
⏰ Aktuelle Zeit: {get_current_time()}
🧮 Rechnung: {calculate_sum(15, 27)}
🎲 Zufälliger Fakt: {get_random_fact()}

✨ Alle Funktionen aus app.py funktionieren perfekt!
        """.strip()
        
        out.textContent = content
        print("✅ UI erfolgreich aktualisiert!")
    else:
        print("❌ Element 'out' nicht gefunden!")

# Führe die UI-Initialisierung aus
update_display()