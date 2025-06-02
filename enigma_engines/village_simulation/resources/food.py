from typing import Optional, Dict, List, Union, Any # Added for context if Item is complex
from pydantic import BaseModel, Field # Assuming Item is a Pydantic BaseModel
from enigma_engines.village_simulation.resources.item import Item  # Assuming Item is a Pydantic BaseModel
# --- Corrected Food Class ---
class Food(Item):
    """
    Represents food items that villagers can consume.
    Food items can have a nutritional value, calories, spoilage time, weight, and making time.
    """
    nutritional_value: int
    calories: int = Field(default=0) # Added calories, common for food simulation
    validity: Optional[int] = None # Renamed from 'validity'
    making_time: Optional[int] = Field(default=0) # Time units to prepare/make
    weight: Optional[float] = Field(default=None) # Weight of the item, e.g., in kg
    icon: str = Field(default="🍽️")  # Default icon for food items
    
    # 'icon' is inherited from Item
    # 'food_type' was removed as it wasn't used in the instances.
    # 'name', 'description', 'base_value' are inherited from Item.

# --- Creating food items with corrected structure ---
# Note: 'weight' and 'making_time' are now part of the Food class.
# 'icon', 'name', 'description', 'base_value' are part of the Item base class.

wheat = Food(
    name="Wheat",
    description="Raw grains of wheat, a staple food.",
    base_value=0.2,
    icon="🌾",
    nutritional_value=5, # Low as it's raw
    calories=10, # Raw grains have some calories
    validity=365,  # Assuming stored properly
    weight=1.0,  # e.g., per sack or bundle
    making_time=0, # Raw material, no making time for the grain itself
)

apple = Food(
    name="Apple",
    description="A crisp and juicy red apple.",
    base_value=0.5,
    icon="🍎",
    nutritional_value=15, # Adjusted for realism, 50 was high for a single apple
    calories=80, # Approx calories for a medium apple
    validity=14, # Apples can last a couple of weeks
    weight=0.15, # kg
    making_time=0, # No making time, it's grown/picked
)

bread = Food(
    name="Loaf of Bread",
    description="A freshly baked loaf of bread.",
    base_value=1.0,
    icon="🍞",
    nutritional_value=70, # Per slice or small portion, 200 for a whole loaf is okay
    calories=250, # For a whole loaf
    validity=5,
    weight=0.5, # kg for a loaf
    making_time=2,  # Time units to bake bread
)

roast_meat = Food(
    name="Roast Meat",
    description="A hearty portion of roasted meat.",
    base_value=3.0,
    icon="🍖",
    nutritional_value=150, # Adjusted for a reasonable portion
    calories=300, # For a good portion
    validity=2,  # Perishable quickly once cooked
    weight=0.3, # kg for a portion
    making_time=1,  # Time units to roast meat
)

fish = Food( # This instance was named 'fish', but represents 'Cooked Fish'
    name="Cooked Fish",
    description="A freshly cooked fish.",
    base_value=1.5,
    icon="🐟", # Using a fish icon, could be 🎣 for raw, 🍲 for cooked
    nutritional_value=100, # Adjusted
    calories=200,
    validity=1, # Very perishable
    weight=0.25, # kg for a cooked portion
    making_time=1,  # Time units to cook fish
)

beer = Food(
    name="Mug of Beer", # More specific unit
    description="A refreshing beverage made from fermented grains.",
    base_value=0.8, # Per mug
    icon="🍺",
    nutritional_value=10, # Low nutritional_value, mostly calories/happiness
    calories=150, # For a mug
    validity=7,  # Once opened or in a cask
    weight=0.5, # kg for a mug (liquid)
    making_time=10,  # Time units to brew a batch
)

wine = Food(
    name="Goblet of Wine", # More specific unit
    description="A fine wine made from the best grapes.",
    base_value=2.0, # Per goblet
    icon="🍷",
    nutritional_value=5, # Low nutritional_value
    calories=120, # For a goblet
    validity=365,  # If bottled well; once opened, much less
    weight=0.2, # kg for a goblet
    making_time=15,  # Time units to ferment a batch
)

# Additional food items needed by villager.py
berries = Food(
    name="Berries",
    description="Fresh wild berries found in the forest.",
    base_value=0.3,
    icon="🫐", # Changed to a berry icon
    nutritional_value=10, # Adjusted
    calories=60, # For a handful
    validity=3,
    weight=0.1, # kg for a handful
    making_time=0, # Gathered
)

wild_meat_food = Food( # This could represent a generic "portion of cooked wild game"
    name="Cooked Wild Meat",
    description="Cooked meat from hunted wild animals.",
    base_value=2.5,
    icon="🥩", # Raw meat icon, could be 🍖 if cooked
    nutritional_value=120, # Adjusted
    calories=280,
    validity=3,
    weight=0.25, # kg for a portion
    making_time=1, # Time to cook
)

# Example of a raw food item if needed for crafting (e.g., raw fish for cooking)
raw_fish_item = Food(
    name="Raw Fish",
    description="A freshly caught fish, needs cooking.",
    base_value=0.8,
    icon="🎣",
    nutritional_value=5, # Low nutritional value raw
    calories=70,
    validity=1, # Very perishable
    weight=0.3, # Average raw fish weight
    making_time=0, # Caught, not made
)
