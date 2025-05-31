from typing import List, Tuple

from pydantic import BaseModel

from enigma_engines.village_simulation.agents.villager import Villager
from enigma_engines.village_simulation.resources.food import (
    Food,
)


class Field(BaseModel):
    """
    Represents a field in the village simulation.
    Fields can be used for growing crops, which can be harvested and used as food or raw materials.

    Attributes:
        name (str): The name of the field.
        size (int): The size of the field, indicating how many crops it can support.
        crop_type (Optional[str]): The type of crop currently being grown in the field.
        is_fertile (bool): Indicates whether the field is fertile and suitable for growing crops.
        owner (Villager): The villager who owns the field, if any.
    """

    name: str
    size: int = 100  # Size of the field in square meters
    plantation: List[Tuple[Food, int, int]] = []
    fertility: float = 100.0
    owner: Villager = None
    days_remaining: int = 0  # Days until the crop is ready to harvest
    icon: str = "🌾"  # Default icon for field

    def plant_crop(self, crop: Food, quantity: int) -> bool:
        if (
            self.plantation is not None
            or self.fertility < quantity
            or self.size < quantity
        ):
            return False  # Field is already planted
        self.plantation.append((crop, quantity, crop.making_time))
        self.fertility -= quantity
        self.size -= quantity
        return True

    def harvest_crop(self) -> List[Food] | None:
        if not self.plantation or self.days_remaining > 0:
            return None
        for crop, quantity, making_time in self.plantation:
            if quantity > 0 and making_time == 0:
                self.size += quantity
                self.days_remaining = making_time
                self.plantation[
                    self.plantation.index((crop, quantity, making_time))
                ] = (crop, 0, 0)
            elif quantity > 0:
                self.plantation[
                    self.plantation.index((crop, quantity, making_time))
                ] = (crop, quantity, making_time - 1)

        harvested_crops = [
            crop for crop, quantity, _ in self.plantation if quantity == 0
        ]
        self.plantation = [
            (crop, quantity, making_time)
            for crop, quantity, making_time in self.plantation
            if quantity > 0
        ]

        return harvested_crops if harvested_crops else None
