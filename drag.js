class UMLDragger {
  constructor() {
    this.umlElement = document.getElementById('umlDiagram');
    this.classId = this.umlElement.getAttribute('data-class-id');
    this.isDragging = false;
    this.currentX = 0;
    this.currentY = 0;
    this.initialX = 0;
    this.initialY = 0;
    this.xOffset = 0;
    this.yOffset = 0;
    this.init();
  }

  init() {
    this.umlElement.addEventListener('mousedown', (e) => this.dragStart(e));
    document.addEventListener('mousemove', (e) => this.drag(e));
    document.addEventListener('mouseup', () => this.dragEnd());
    this.umlElement.addEventListener('touchstart', (e) => this.dragStart(e.touches[0]));
    document.addEventListener('touchmove', (e) => this.drag(e.touches[0]));
    document.addEventListener('touchend', () => this.dragEnd());
    this.loadPosition();
  }

  dragStart(e) {
    if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'button') {
      return;
    }
    if (this.umlElement.contains(e.target)) {
      this.initialX = e.clientX - this.xOffset;
      this.initialY = e.clientY - this.yOffset;
      if (this.umlElement.contains(e.target)) {
        this.isDragging = true;
        this.umlElement.style.cursor = 'grabbing';
        this.umlElement.style.boxShadow = '0 0 0 rgba(0,0,0,0.3)';
        this.umlElement.style.transition = 'box-shadow 0.2s ease';
      }
    }
  }

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

  dragEnd() {
    this.isDragging = false;
    this.umlElement.style.cursor = 'move';
    this.umlElement.style.boxShadow = '';
    this.savePosition();
  }

  setTranslate(xPos, yPos) {
    this.umlElement.style.transform = `translate(${xPos}px, ${yPos}px)`;
  }

  savePosition() {
    const position = JSON.parse(localStorage.getItem('umlPosition')) || '{}';
    position[this.classId] =
    {
      x: this.currentX,
      y: this.currentY
    };
    localStorage.setItem('umlPosition', JSON.stringify(position));
  }

  loadPosition() {
    const saved = localStorage.getItem('umlPosition');
    if (saved) {
      const position = JSON.parse(saved);
      this.xOffset = position.x;
      this.yOffset = position.y;
      this.setTranslate(this.xOffset, this.yOffset);
    }
  }

  resetPosition() {
    this.xOffset = 0;
    this.yOffset = 0;
    this.setTranslate(0, 0);
    localStorage.removeItem('umlPosition');
  }
}

let umlDragger;

document.addEventListener('DOMContentLoaded', function() {
  umlDragger = new UMLDragger();
  umlDragger.loadPosition();
});

function addResetButton() {
  const resetBtn = document.getElementById('resetSvg');
  resetBtn.onclick = () => {
    if (umlDragger) {
      umlDragger.resetPosition();
    }
  };
}
document.addEventListener('DOMContentLoaded', addResetButton);
