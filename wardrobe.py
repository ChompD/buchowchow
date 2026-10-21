"""The pet's wardrobe: which outfits and accessories exist, when they unlock,
and what the pet is currently wearing.

No Pygame in here (drawing lives in ui.py), so the rules are easy to test.
To add an item: add it to ITEMS below, then teach ui.draw_outfit_item to draw it.
"""

from dataclasses import dataclass

SLOTS = ("head", "face", "neck", "body")
SLOT_NAMES = {"head": "Head", "face": "Face", "neck": "Neck", "body": "Outfit"}
COLORS = ("pink", "red", "orange", "yellow", "green", "blue", "purple")


@dataclass(frozen=True)
class Item:
    key: str
    name: str
    slot: str
    unlock_level: int = 1
    colorable: bool = True
    default_color: str = "pink"


ITEMS = {item.key: item for item in [
    # Head
    Item("bow", "Bow", "head", 1, True, "pink"),
    Item("flower", "Flower", "head", 1, True, "yellow"),
    Item("party_hat", "Party hat", "head", 2, True, "blue"),
    Item("beanie", "Beanie", "head", 3, True, "red"),
    Item("crown", "Crown", "head", 10, False, "yellow"),
    # Face
    Item("glasses", "Glasses", "face", 1, True, "purple"),
    Item("sunglasses", "Sunglasses", "face", 4, False, "purple"),
    Item("heart_shades", "Heart shades", "face", 6, True, "pink"),
    # Neck
    Item("bell_collar", "Bell collar", "neck", 1, True, "red"),
    Item("bandana", "Bandana", "neck", 2, True, "blue"),
    Item("bow_tie", "Bow tie", "neck", 3, True, "purple"),
    Item("scarf", "Scarf", "neck", 5, True, "green"),
    # Body
    Item("sweater", "Sweater", "body", 1, True, "blue"),
    Item("tshirt", "T-shirt", "body", 2, True, "yellow"),
    Item("raincoat", "Raincoat", "body", 4, True, "yellow"),
]}


def items_for(slot):
    """All items for one slot, in unlock order."""
    return [item for item in ITEMS.values() if item.slot == slot]


def unlocked_between(old_level, new_level):
    """Items that unlock when going from `old_level` up to `new_level`."""
    return [item for item in ITEMS.values() if old_level < item.unlock_level <= new_level]


class Outfit:
    """What the pet is wearing: at most one item (and its colour) per slot."""

    def __init__(self):
        self._worn = {}  # slot -> (item key, colour name)

    def item(self, slot):
        """The Item worn in `slot`, or None."""
        worn = self._worn.get(slot)
        return ITEMS[worn[0]] if worn else None

    def color(self, slot):
        worn = self._worn.get(slot)
        return worn[1] if worn else None

    def worn(self):
        """(slot, item key, colour) for everything being worn, in drawing order."""
        return [(slot, *self._worn[slot]) for slot in SLOTS if slot in self._worn]

    def is_wearing(self, key):
        return any(worn[0] == key for worn in self._worn.values())

    def wear(self, key, level, color=None):
        """Put an item on (replacing whatever is in its slot). Returns False if locked or unknown.

        If no colour is given, a colourable item keeps the slot's current colour,
        so swapping a red beanie for a party hat gives a red party hat.
        """
        item = ITEMS.get(key)
        if item is None or level < item.unlock_level:
            return False
        if not item.colorable:
            color = item.default_color
        elif color not in COLORS:
            current = self._worn.get(item.slot)
            current_colorable = current and ITEMS[current[0]].colorable
            color = current[1] if current_colorable else item.default_color
        self._worn[item.slot] = (key, color)
        return True

    def take_off(self, slot):
        self._worn.pop(slot, None)

    def set_color(self, slot, color):
        """Recolour the item in `slot`. Returns False if there is nothing to recolour."""
        item = self.item(slot)
        if item is None or not item.colorable or color not in COLORS:
            return False
        self._worn[slot] = (item.key, color)
        return True

    # ---- Saving ----

    def to_dict(self):
        return {slot: {"item": key, "color": color} for slot, key, color in self.worn()}

    @classmethod
    def from_dict(cls, data, level):
        """Rebuild an outfit, quietly skipping anything unknown, misplaced or still locked.

        Clothes are just for fun, so a damaged outfit never stops a save from loading.
        """
        outfit = cls()
        if not isinstance(data, dict):
            return outfit
        for slot, entry in data.items():
            if not isinstance(entry, dict):
                continue
            item = ITEMS.get(entry.get("item"))
            if item is not None and item.slot == slot:
                outfit.wear(item.key, level, entry.get("color"))
        return outfit

    @classmethod
    def for_stage(cls, stage, level):
        """What older versions of the game drew automatically at each evolution stage.

        Used for saves made before the wardrobe existed, so those pets keep their look.
        """
        outfit = cls()
        if stage == 1 or stage == 2:
            outfit.wear("bow", level)
        if stage >= 2:
            outfit.wear("bell_collar", level)
        if stage >= 3:
            outfit.wear("crown", level)
        return outfit
