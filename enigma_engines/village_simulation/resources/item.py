from typing import Any, Optional, Union

from pydantic import BaseModel


class Item(BaseModel):
    """
    Represents an item with a name, value, and optional attributes.
    The Base Item for the Simulation Village.

    This class models an item in the village simulation with a base value.
    Items can be combined or have their values adjusted.

    Attributes:
        name (str): The name of the item.
        base_value (float): The base monetary value of the item.
        description (Optional[str]): Optional description of the item.
        weight (Optional[float]): Optional weight of the item.
    """

    name: str
    base_value: float  # Changed from Float to float
    description: Optional[str] = None
    weight: Optional[float] = None  # Changed from Float to float

    # Pydantic automatically generates __init__ based on field definitions.
    # The 'value' attribute from the original __init__ has been removed
    # as it was redundant with base_value for a Pydantic model structure.
    # If a mutable 'current_value' different from 'base_value' is needed,
    # it should be a separate field or handled via methods.

    # model_config can be used for settings like 'frozen'
    # For example, to make instances immutable and automatically hashable:
    # model_config = ConfigDict(frozen=True)
    # If frozen=True, Pydantic handles __hash__ automatically.
    # Since we have custom __eq__, we also provide __hash__ if not frozen.

    def __str__(self) -> str:
        """Returns a string representation of the item."""
        return (
            f"Item(name={self.name}, base_value={self.base_value}, "
            f"description={self.description}, weight={self.weight})"
        )

    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the item."""
        return (
            f"Item(name={self.name!r}, base_value={self.base_value!r}, "
            f"description={self.description!r}, weight={self.weight!r})"
        )

    def __hash__(self) -> int:
        """Returns the hash of the item based on its attributes."""
        # Required if __eq__ is implemented and instances need to be hashable.
        # If model_config = ConfigDict(frozen=True) is used, Pydantic handles this.
        return hash((self.name, self.base_value, self.description, self.weight))

    def __add__(self, other: Union["Item", int, float]) -> "Item":
        """Adds another Item or a numeric value to this item's base_value,
        combining attributes if applicable."""
        if isinstance(other, Item):
            # Combine descriptions
            new_description: Optional[str] = None
            if self.description and other.description:
                new_description = f"{self.description} + {other.description}"
            elif self.description:
                new_description = self.description
            elif other.description:
                new_description = other.description

            # Combine weights
            new_weight: Optional[float] = None
            if self.weight is not None and other.weight is not None:
                new_weight = self.weight + other.weight
            elif self.weight is not None:
                new_weight = self.weight
            elif other.weight is not None:
                new_weight = other.weight

            return Item(
                name=f"{self.name} + {other.name}",
                base_value=self.base_value + other.base_value,
                description=new_description,
                weight=new_weight,
            )
        elif isinstance(other, (int, float)):
            return Item(
                name=self.name,
                base_value=self.base_value + float(other),
                description=self.description,  # Description remains self's description
                weight=self.weight,  # Weight remains self's weight
            )
        else:
            return NotImplemented

    def __sub__(self, other: Union["Item", int, float]) -> "Item":
        """Subtracts another Item's or a numeric value from this item's base_value."""
        if isinstance(other, Item):
            # Description handling for subtraction can be tricky.
            # Here, we'll just indicate a subtraction, or keep self's if other has none.
            new_description: Optional[str] = None
            if self.description and other.description:
                new_description = f"{self.description} - {other.description}"
            elif self.description:
                new_description = self.description
            # No description from 'other' if 'self' has none.

            # Weight handling for subtraction
            new_weight: Optional[float] = None
            if self.weight is not None and other.weight is not None:
                new_weight = self.weight - other.weight
            elif self.weight is not None:
                new_weight = self.weight
            # If other has weight but self doesn't, result might be negative or None depending on desired logic.
            # For simplicity, if self.weight is None, new_weight remains None unless other.weight is subtracted from 0.
            # Current logic: keeps self.weight if other.weight is None.

            return Item(
                name=f"{self.name} - {other.name}",
                base_value=self.base_value - other.base_value,
                description=new_description,
                weight=new_weight,
            )
        elif isinstance(other, (int, float)):
            return Item(
                name=self.name,
                base_value=self.base_value - float(other),
                description=self.description,
                weight=self.weight,
            )
        else:
            return NotImplemented

    def __eq__(self, other: Any) -> bool:
        """Checks equality based on all attributes."""
        if not isinstance(other, Item):
            return NotImplemented
        # Pydantic's default __eq__ compares all fields.
        # This implementation is equivalent to the default if all fields are included.
        return (
            self.name == other.name
            and self.base_value == other.base_value
            and self.description == other.description
            and self.weight == other.weight
        )

    # __ne__ is automatically provided if __eq__ is defined.

    def __lt__(self, other: Any) -> bool:
        """Compares items based on base_value."""
        if not isinstance(other, Item):
            return NotImplemented
        return self.base_value < other.base_value

    def __le__(self, other: Any) -> bool:
        """Compares items based on base_value."""
        if not isinstance(other, Item):
            return NotImplemented
        return self.base_value <= other.base_value


soggy_boot = Item(
    name="Soggy Boot",
    base_value=0.1,
    description="A wet and muddy boot, not very useful.",
    weight=0.5
)

old_coin = Item(
    name="Old Coin",
    base_value=0.5,
    description="An ancient coin, slightly tarnished but still valuable.",
    weight=0.02
)

rusty_sword = Item(
    name="Rusty Sword",
    base_value=5.0,
    description="A sword that has seen better days, still sharp enough to cut.",
    weight=2.5
)

lost_locket = Item(
    name="Lost Locket",
    base_value=10.0,
    description="A tarnished silver locket.",
    weight=0.1
)

scraps = Item(
    name="Scraps",
    base_value=0.05,
    description="A handful of metal scraps, useful for crafting.",
    weight=0.1
)