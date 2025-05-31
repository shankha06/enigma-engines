from typing import Dict, Optional

from enigma_engines.animal_crossing.resources.item import Item
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial,
    fabric,
    leather,
    stone,
)


class Clothing(Item):
    """
    Represents clothes that the villagers can wear.

    Clothes can have a color and durability attribute. Color is not impactful
    in the simulation, but it can be used for aesthetic purposes. Durability
    indicates how long the clothing can be worn before it needs to be replaced.
    Attributes:
        color (Optional[str]): The color of the clothing.
        durability (Optional[int]): The durability of the clothing, indicating how long it can be worn.
    """

    icon: str = "👕"  # Default icon for clothing
    color: Optional[str] = None
    durability: Optional[int] = None
    required_materials: Optional[Dict[RawMaterial, int]] = (
        None  # e.g., {"fabric": 2, "leather": 1}
    )


men_armor = Clothing(
    name="Men's Armor",
    base_value=50.0,
    description="A sturdy piece of armor designed for men to protect them from the elements.",
    weight=10.0,  # e.g., per set
    color="Dark Gray",
    durability=100,
    icon="⚔️",
    required_materials={
        fabric: 2,
        leather: 1,
        stone: 1,
    },
)

daily_clothes = Clothing(
    name="Daily Clothes",
    base_value=20.0,
    description="Casual clothes for everyday wear.",
    weight=2.0,  # e.g., per outfit
    color="Blue",
    durability=50,
    icon="🧥",
    required_materials={fabric: 1, leather: 1},
)

women_wear = Clothing(
    name="Women's Wear",
    base_value=25.0,
    description="Stylish clothes designed for women.",
    weight=1.8,  # e.g., per outfit
    color="Pink",
    durability=45,
    icon="👘",
    required_materials={fabric: 1, leather: 1},
)
