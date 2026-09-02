export class InteractionManager {
  constructor({ player, ui }) {
    this.player = player;
    this.ui = ui;
    this.items = [];
    this.current = null;
    this.enabled = true;
  }

  register(item) {
    this.items.push(item);
    return item;
  }

  clear() {
    this.items.length = 0;
    this.current = null;
    this.ui.hideTip();
  }

  update() {
    if (!this.enabled || !this.player.enabled) {
      this.current = null;
      this.ui.hideTip();
      return;
    }
    let best = null;
    let bestDistance = Infinity;
    for (const item of this.items) {
      if (item.enabled === false) continue;
      const position = item.object?.position ?? item.position;
      const distance = this.player.group.position.distanceTo(position);
      if (distance <= item.radius && distance < bestDistance) {
        best = item;
        bestDistance = distance;
      }
    }
    this.current = best;
    if (best) this.ui.showTip(`<kbd>E</kbd> ${best.actionLabel || "互动"}`);
    else this.ui.hideTip();
  }

  interact() {
    if (!this.enabled || !this.current) return;
    this.current.onInteract?.(this.current);
  }
}
