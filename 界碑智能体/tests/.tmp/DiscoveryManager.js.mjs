export class DiscoveryManager {
  constructor({ world, interactions, quest, ui }) {
    this.world = world;
    this.interactions = interactions;
    this.quest = quest;
    this.ui = ui;
    this.items = [];
  }

  addAll(definitions) {
    definitions.forEach((definition) => this.addOne(definition));
  }

  addOne(definition) {
    const marker = this.world.createDebugMarker(definition.position, 0xd6a74f, `Discovery:${definition.id}`);
    marker.visible = false;
    this.items.push(marker);
    this.interactions.register({
      ...definition,
      object: marker,
      actionLabel: definition.actionLabel || "自由发现",
      onInteract: () => {
        const isNew = this.quest.addFragment(definition.id);
        this.ui.showDiscovery(definition, this.quest.fragments.size, this.items.length, isNew);
      },
    });
    return marker;
  }

  setDebugVisible(visible) {
    this.items.forEach((item) => { item.visible = visible; });
  }
}
