from typing import Dict, Optional, Union

from pydantic import BaseModel

from enigma_engines.animal_crossing.resources.item import Item
from enigma_engines.village_simulation.resources.clothing import (
    Clothing,
    daily_clothes,
    men_armor,
    women_wear,
)
from enigma_engines.village_simulation.resources.food import (
    Food,
    apple,
    beer,
    bread,
    fish,
    roast_meat,
    wheat,
    wine,
)
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial,
    fabric,
    leather,
    skin,
    stone,
    wood,
)


class Vendor(BaseModel):
    """
    Represents a vendor in the village simulation.
    Vendors can sell various items, including raw materials, food, and clothing.
    Vendors can also have a name, description, and an inventory of items they sell.
    Attributes:
        name (str): The name of the vendor.
        description (Optional[str]): A brief description of the vendor.
        inventory (Dict[Union[RawMaterial, Food, Item], int]): A dictionary mapping items to their quantities.
    """

    name: str
    shop_name: Optional[str] = None
    description: Optional[str] = None
    inventory: Dict[Union[RawMaterial, Food, Item, Clothing], int] = {}

    money = 0.0  # Balance for transactions

    def add_to_inventory(self, item: Union[RawMaterial, Clothing], quantity: int):
        """Adds a specified quantity of an item to the vendor's inventory."""
        if quantity <= 0:
            return
        self.inventory[item] = self.inventory.get(item, 0) + quantity

    def remove_from_inventory(
        self, item: Union[RawMaterial, Clothing], quantity: int
    ) -> bool:
        """Removes a specified quantity of an item if available. Returns True on success."""
        if quantity <= 0:
            return False  # Cannot remove zero or negative quantity
        if item in self.inventory and self.inventory[item] >= quantity:
            self.inventory[item] -= quantity
            if self.inventory[item] == 0:
                del self.inventory[item]  # Clean up if quantity becomes zero
            return True
        return False  # Not enough in stock

    def buy_item_from_producer(
        self, item: Union[RawMaterial, Clothing], quantity: int, price_per_unit: float
    ) -> bool:
        """Vendor buys an item from a producer (e.g., Tannery)."""
        total_cost = quantity * price_per_unit
        if self.money >= total_cost and quantity > 0:
            self.money -= total_cost
            self.add_to_inventory(item, quantity)
            # backend_logger.info(f"Vendor '{self.name}' bought {quantity} x {item.name} for {total_cost:.2f}.")
            return True
        # backend_logger.info(f"Vendor '{self.name}' failed to buy {quantity} x {item.name}.")
        return False

    def sell_item_to_customer(
        self, item: Union[RawMaterial, Clothing], quantity: int, price_per_unit: float
    ) -> bool:
        """Vendor sells an item to a customer (e.g., Tannery)."""
        if quantity <= 0:
            return False
        if self.remove_from_inventory(item, quantity):
            self.money += quantity * price_per_unit
            # backend_logger.info(f"Vendor '{self.name}' sold {quantity} x {item.name} for {quantity * price_per_unit:.2f}.")
            return True
        # backend_logger.info(f"Vendor '{self.name}' failed to sell {quantity} x {item.name}.")
        return False

    def __str__(self):
        """Returns a string representation of the vendor."""
        return (
            f"Vendor(name={self.name}, description={self.description}, "
            f"inventory={self.inventory})"
        )


# Example vendor

Garrick_Ironheart = Vendor(
    name="Garrick Ironheart",
    shop_name="Ironheart Forge",
    description="A seasoned blacksmith known for his sturdy tools, armor and clothing.",
    inventory={
        wood: 50,
        stone: 30,
        leather: 20,
        fabric: 15,
        skin: 5,
        men_armor: 10,
        daily_clothes: 5,
        women_wear: 5,
    },
    icon="⚒️",
    money=100.0,  # Initial balance for transactions
)


Mira_Greenleaf = Vendor(
    name="Mira Greenleaf",
    shop_name="Greenleaf Grocer",
    description="A friendly grocer who sells fresh produce and baked goods.",
    inventory={
        wheat: 100,
        apple: 50,
        bread: 30,
    },
    icon="🥦",
    money=100.0,  # Initial balance for transactions
)

Lyra = Vendor(
    name="Lyra",
    shop_name="The Tipsy Griffin",
    description="A cheerful innkeeper who serves food and drinks to weary travelers.",
    inventory={
        beer: 10,
        wine: 20,
        fish: 15,
        roast_meat: 10,
        bread: 25,
    },
    icon="🏠",
    money=100.0,  # Initial balance for transactions
)
