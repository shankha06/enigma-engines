from typing import Optional

from enigma_engines.animal_crossing.resources.item import Item


class Food(Item):
    """
    Represents food items that villagers can consume.
    Food items can have a nutritional value and validity period.

    Attributes:
        nutritional_value (int): The nutritional value of the food item.
        validity (Optional[int]): The number of days the food item remains valid.
    """

    food_type: str
    nutritional_value: int = None
    validity: Optional[int] = None
    making_time: Optional[int] = 0  #
    icon: str


# Creating food items
wheat = Food(
    name="Wheat",
    base_value=0.2,
    nutritional_value=5,
    validity=365,  # Assuming stored properly
    description="Raw grains of wheat, a staple food.",
    weight=1.0,  # e.g., per sack or bundle
    making_time=5,
    icon="🌾",
)

apple = Food(
    name="Apple",
    base_value=0.5,
    nutritional_value=50,
    validity=7,
    description="A crisp and juicy red apple.",
    weight=0.15,
    making_time=1,
    icon="🍎",
)

bread = Food(
    name="Loaf of Bread",
    base_value=1.0,
    nutritional_value=200,
    validity=5,
    description="A freshly baked loaf of bread.",
    weight=0.5,
    making_time=2,  # Time to bake bread
    icon="🍞",
)

roast_meat = Food(
    name="Roast Meat",
    base_value=3.0,
    nutritional_value=300,
    validity=2,  # Perishable quickly once cooked
    description="A hearty portion of roasted meat.",
    weight=0.8,
    making_time=0,  # Time to roast meat
    icon="🍖",
)

fish = Food(
    name="Cooked Fish",
    base_value=1.5,
    nutritional_value=180,
    validity=1,
    description="A freshly cooked fish.",
    weight=0.4,
    making_time=0,  # Time to cook fish
    icon="🐟",
)

beer = Food(
    name="Beer",
    base_value=2.0,
    nutritional_value=50,
    validity=30,  # Assuming it can be stored for a month
    description="A refreshing beverage made from fermented grains.",
    weight=0.33,  # e.g., per bottle
    making_time=10,  # Time to brew beer
    icon="🍺",
)

wine = Food(
    name="Wine",
    base_value=5.0,
    nutritional_value=100,
    validity=365,  # Can be stored for a long time
    description="A fine wine made from the best grapes.",
    weight=0.75,  # e.g., per bottle
    making_time=15,  # Time to ferment wine
    icon="🍷",
)
