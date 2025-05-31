from enigma_engines.animal_crossing.resources.item import Item


class RawMaterial(Item):
    """
    Represents raw materials that villagers can use for crafting or building.
    Raw materials can have material types and can be used in various crafting recipes.

    It can be used to craft clothing items to protect villagers from the elements,
    or to build structures in the village.

    material_type can be one of the following:
    - wood
    - stone
    - metal
    - skin
    - fabric
    - glass
    - clay

    Attributes:
        material_type (str): The type of raw material, used for categorization in crafting.
    """

    material_type: str
    icon: str


# Example raw materials

wood = RawMaterial(
    name="Wood",
    base_value=0.1,
    material_type="wood",
    description="A sturdy piece of wood, useful for building and crafting.",
    weight=2.0,  # e.g., per log
    icon="🌳",
)
stone = RawMaterial(
    name="Stone",
    base_value=0.2,
    material_type="stone",
    description="A solid piece of stone, useful for construction.",
    weight=5.0,  # e.g., per rock
    icon="⛰️",
)
skin = RawMaterial(
    name="Raw Animal Skin",
    base_value=0.4,
    material_type="skin",
    description="A piece of raw animal skin, useful for crafting clothing.",
    weight=1.0,  # e.g., per hide
    icon="🦌",
)
leather = RawMaterial(
    name="Leather",
    base_value=0.5,
    material_type="leather",
    description="A piece of tanned leather, useful for crafting durable items.",
    weight=1.5,  # e.g., per hide
    icon="🧤",
)
fabric = RawMaterial(
    name="Fabric",
    base_value=0.3,
    material_type="fabric",
    description="A piece of cloth, useful for crafting clothing.",
    weight=0.2,  # e.g., per meter
    icon="🧵",
)
