
class UMLDragger {
  constructor() {
    // UML Diagramm Element holen
    this.umlElement = document.getElementById('umlDiagram');
    // ID der Klasse speichern
    this.classId = this.umlElement.getAttribute('data-class-id');
    // Status ob gezogen wird
    this.isDragging = false;
    this.currentX = 0; // Aktuelle Position
    this.currentY = 0;
    this.initialX = 0; // Anfangsposition beim Drag
    this.initialY = 0;
    this.xOffset = 0; // Offset für Translation
    this.yOffset = 0;
    this.init();
  }

   // Ereignisse initialisieren
  init() {
    this.umlElement.addEventListener('mousedown', (e) => this.dragStart(e));
    this.umlElement.addEventListener('mousemove', (e) => this.updateEdgeHover(e));
    this.umlElement.addEventListener('mouseleave', () => this.clearEdgeHover());
    document.addEventListener('mousemove', (e) => this.drag(e));
    document.addEventListener('mouseup', () => this.dragEnd());
    this.umlElement.addEventListener('touchstart', (e) => this.dragStart(e.touches[0]));
    document.addEventListener('touchmove', (e) => this.drag(e.touches[0]));
    document.addEventListener('touchend', () => this.dragEnd());
    // Gespeicherte Position laden
    this.loadPosition();
  }

  // Drag starten
  dragStart(e) {
    if (e.target !== this.umlElement) {
      return;
    }
    this.clearEdgeHover();
    this.initialX = e.clientX - this.xOffset;
    this.initialY = e.clientY - this.yOffset;
    this.isDragging = true;
    this.umlElement.style.cursor = 'grabbing';
    this.umlElement.style.boxShadow = '0 0 0 rgba(0,0,0,0.3)';
    this.umlElement.style.transition = 'box-shadow 0.2s ease';
  }

  // Drag bewegen
  drag(e) {
    if (this.isDragging) {
      e.preventDefault();
      this.currentX = e.clientX - this.initialX;
      this.currentY = e.clientY - this.initialY;
      this.xOffset = this.currentX;
      this.yOffset = this.currentY;
      this.setTranslate(this.currentX, this.currentY);
    }
  }

  // Drag beenden
  dragEnd() {
    this.isDragging = false;
    this.umlElement.style.cursor = 'grab';
    this.umlElement.style.boxShadow = '';
    this.savePosition();
  }

  // Hover-Status nur für Rand-Zone
  updateEdgeHover(e) {
    if (this.isDragging) {
      this.clearEdgeHover();
      return;
    }
    const isOnEdgeZone = e.target === this.umlElement;
    // this.umlElement.classList.toggle('edge-hover', isOnEdgeZone);
  }

  clearEdgeHover() {
    this.umlElement.classList.remove('edge-hover');
  }
 
  // Position anwenden
  setTranslate(xPos, yPos) {
    this.umlElement.style.transform = `translate(${xPos}px, ${yPos}px)`;
  }

  // Position in localStorage speichern
  savePosition() {
    let positions;
    try {
      positions = JSON.parse(localStorage.getItem("umlPosition")) || {};
    } catch (e) {
      // Falls Parsing fehlschlägt, leeres Objekt verwenden
      console.warn("Failed to parse umlPosition from localStorage:", e);
      positions = {};
    }
    
    // sicherstellen, dass positions ein Objekt ist
    if (typeof positions !== 'object' || positions === null) {
      positions = {};
    }
    
    // Aktuelle Position speichern
    positions[this.classId] = {
      x: this.currentX,
      y: this.currentY
    };
    
    localStorage.setItem("umlPosition", JSON.stringify(positions));
  }

  // Gespeicherte Position laden
  loadPosition() {
    const saved = localStorage.getItem('umlPosition');
    if (saved) {
      let position = null;
      try {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object') {
          if (this.classId && parsed[this.classId]) {
            position = parsed[this.classId];
          } else if (typeof parsed.x === 'number' && typeof parsed.y === 'number') {
            position = parsed;
          }
        }
      } catch (e) {
        console.warn('Failed to parse umlPosition from localStorage:', e);
      }

      if (position) {
        this.xOffset = position.x;
        this.yOffset = position.y;
      } else {
        this.xOffset = 0;
        this.yOffset = 0;
      }
      this.setTranslate(this.xOffset, this.yOffset);
    }
  }

  // Position zurücksetzen
  resetPosition() {
    this.xOffset = 0;
    this.yOffset = 0;
    this.setTranslate(0, 0);
    localStorage.removeItem('umlPosition');
  }
}

// UMLDragger Objekt erstellen
let umlDragger;

document.addEventListener('DOMContentLoaded', function() {
  umlDragger = new UMLDragger();
  umlDragger.loadPosition();
});

// Reset Button Funktion hinzufügen
function addResetButton() {
  const resetBtn = document.getElementById('resetSvg');
  resetBtn.onclick = () => {
    if (umlDragger) {
      umlDragger.resetPosition();
    }
  };
}
document.addEventListener('DOMContentLoaded', addResetButton);
