from typing import Dict, List, Optional, Tuple, Union
import random
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from enigma_engines.village_simulation.agents.villager import Villager
from enigma_engines.village_simulation.resources.food import Food, fish
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial,
    wood,
    stone,
)
from enigma_engines.village_simulation.resources.item import Item


class WeatherCondition(Enum):
    """Enumeration of weather conditions affecting fishing."""

    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    FOGGY = "foggy"


class TimeOfDay(Enum):
    """Enumeration of time periods affecting fish activity."""

    DAWN = "dawn"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


@dataclass
class FishSpecies:
    """Represents a species of fish in the river."""

    name: str
    food_item: Food
    rarity: float  # 0.0 to 1.0 (1.0 being most common)
    size_range: Tuple[float, float]  # min and max size in kg
    preferred_depth: float  # meters
    active_times: List[TimeOfDay]
    weather_preference: List[WeatherCondition]
    min_skill_required: int
    escape_chance: float
    icon: str


@dataclass
class FishingResult:
    """Represents the result of a fishing attempt."""

    success: bool
    catch: Optional[Food] = None
    quantity: int = 0
    special_item: Optional[Item] = None
    message: str = ""


@dataclass
class EnvironmentalFactors:
    """Environmental factors affecting fishing."""

    weather: WeatherCondition
    time_of_day: TimeOfDay
    water_temperature: float
    water_clarity: float  # 0.0 to 1.0
    season_modifier: float  # 0.5 to 1.5


class River(BaseModel):
    """
    Represents a river in the village simulation.
    Rivers can be used for fishing, gathering water, and transportation.

    Rivers are vital for the village's ecosystem, providing water for crops and drinking.
    They also serve as a habitat for various aquatic life.
    But there are only fixed locations where villagers can access the river, so they must be careful not to overfish or pollute it.

    Attributes:
        name (str): The name of the river.
        length (int): The length of the river in meters.
        depth (float): The average depth of the river in meters.
        flow_rate (float): The flow rate of the river in cubic meters per second.
        fish_population (Dict[str, int]): A dictionary mapping fish species names to their populations.
        villagers_present (List[Villager]): A list of villagers currently present at the river.
        pollution_level (float): The pollution level of the river (0.0 to 1.0).
        days_since_last_replenishment (int): Counter for natural replenishment cycle.
        icon (str): An icon representing the river.

    Functions:
        _get_fish_species(): Defines available fish species with their properties.
        _calculate_max_fish_population(): Calculate maximum fish population based on river size and depth.
        _get_environmental_factors(): Get current environmental factors affecting fishing.
        _check_fishing_prerequisites(villager: Villager): Check if villager meets all prerequisites for fishing.
    """

    name: str
    length: int
    depth: float
    flow_rate: float
    fish_population: Dict[str, int] = Field(default_factory=dict)
    villagers_present: List[Villager] = Field(default_factory=list)
    pollution_level: float = 0.0
    days_since_last_replenishment: int = 0
    icon: str = "🌊"

    # Special items that can be caught
    special_items: Dict[Item, int] = Field(default_factory=dict)

    # Configuration constants
    MIN_FISH_PERCENTAGE: float = 0.25  # Keep at least 25% of max population
    FISH_REPLENISH_RATE: float = 0.04  # 4% daily growth rate
    MAX_DAILY_CATCH_PER_VILLAGER: int = 10
    MIN_FISHING_SKILL: int = 1
    POLLUTION_IMPACT: float = 0.1  # Impact of fishing on pollution

    # Fishing mechanics
    BASE_CATCH_CHANCE: float = 0.3
    SKILL_BONUS_PER_LEVEL: float = 0.05
    EQUIPMENT_BONUS: float = 0.2  # If villager has fishing equipment

    class Config:
        arbitrary_types_allowed = True

    def _get_fish_species(self) -> Dict[str, FishSpecies]:
        """Define available fish species with their properties."""
        return {
            "trout": FishSpecies(
                name="trout",
                food_item=fish,
                rarity=0.7,
                size_range=(0.5, 2.0),
                preferred_depth=1.5,
                active_times=[TimeOfDay.DAWN, TimeOfDay.EVENING],
                weather_preference=[WeatherCondition.CLOUDY, WeatherCondition.RAINY],
                min_skill_required=2,
                escape_chance=0.3,
                icon="🐟",
            ),
            "salmon": FishSpecies(
                name="salmon",
                food_item=fish,
                rarity=0.5,
                size_range=(2.0, 8.0),
                preferred_depth=2.5,
                active_times=[TimeOfDay.MORNING, TimeOfDay.EVENING],
                weather_preference=[WeatherCondition.CLOUDY],
                min_skill_required=3,
                escape_chance=0.4,
                icon="🐟",
            ),
            "catfish": FishSpecies(
                name="catfish",
                food_item=fish,
                rarity=0.6,
                size_range=(1.0, 5.0),
                preferred_depth=3.0,
                active_times=[TimeOfDay.NIGHT, TimeOfDay.EVENING],
                weather_preference=[WeatherCondition.RAINY, WeatherCondition.STORMY],
                min_skill_required=2,
                escape_chance=0.25,
                icon="🐟",
            ),
            "minnow": FishSpecies(
                name="minnow",
                food_item=fish,
                rarity=0.9,
                size_range=(0.01, 0.05),
                preferred_depth=0.5,
                active_times=[TimeOfDay.MORNING, TimeOfDay.AFTERNOON],
                weather_preference=[WeatherCondition.SUNNY],
                min_skill_required=1,
                escape_chance=0.5,
                icon="🐠",
            ),
        }

    def _calculate_max_fish_population(self) -> Dict[str, int]:
        """Calculate maximum fish population based on river size and depth."""
        base_population = self.length * self.depth * self.flow_rate / 100
        return {
            "trout": int(base_population * 30),
            "salmon": int(base_population * 20),
            "catfish": int(base_population * 25),
            "minnow": int(base_population * 100),
        }

    def _get_environmental_factors(self) -> EnvironmentalFactors:
        """Get current environmental factors affecting fishing."""
        # Simulate random weather
        weather = random.choice(list(WeatherCondition))

        # Simulate time of day (could be linked to actual game time)
        time_of_day = random.choice(list(TimeOfDay))

        # Water temperature varies with weather and time
        base_temp = 15.0
        weather_impact = {
            WeatherCondition.SUNNY: 3.0,
            WeatherCondition.CLOUDY: 0.0,
            WeatherCondition.RAINY: -2.0,
            WeatherCondition.STORMY: -3.0,
            WeatherCondition.FOGGY: -1.0,
        }
        water_temperature = base_temp + weather_impact.get(weather, 0)

        # Water clarity affected by weather and pollution
        clarity_base = 0.8
        weather_clarity = {
            WeatherCondition.SUNNY: 0.9,
            WeatherCondition.CLOUDY: 0.8,
            WeatherCondition.RAINY: 0.6,
            WeatherCondition.STORMY: 0.4,
            WeatherCondition.FOGGY: 0.7,
        }
        water_clarity = weather_clarity.get(weather, clarity_base) * (
            1 - self.pollution_level
        )

        # Seasonal modifier (simplified)
        season_modifier = random.uniform(0.7, 1.3)

        return EnvironmentalFactors(
            weather=weather,
            time_of_day=time_of_day,
            water_temperature=water_temperature,
            water_clarity=water_clarity,
            season_modifier=season_modifier,
        )

    def _check_fishing_prerequisites(self, villager: Villager) -> Tuple[bool, str]:
        """
        Check if villager meets all prerequisites for fishing.

        Returns:
            Tuple of (can_fish, reason_if_not)
        """
        # Check if villager is present at the river
        if villager not in self.villagers_present:
            return False, f"{villager.name} must be at the {self.name} to fish."

        # Check villager health
        if villager.health < 20:
            return (
                False,
                f"{villager.name} is too weak to fish (health: {villager.health}).",
            )

        # Check fishing skill
        fishing_skill = villager.skills.get("fishing", 0)
        if fishing_skill < self.MIN_FISHING_SKILL:
            return (
                False,
                f"{villager.name} lacks basic fishing skills (requires level {self.MIN_FISHING_SKILL}).",
            )

        # Check if villager has already fished too much today
        # This would need daily tracking in a real implementation
        # For now, we'll use a simple check based on current inventory
        current_fish_count = villager.inventory.get(fish, 0)
        if current_fish_count >= self.MAX_DAILY_CATCH_PER_VILLAGER:
            return False, f"{villager.name} has reached the daily fishing limit."

        return True, ""

    def _calculate_catch_probability(
        self,
        villager: Villager,
        target_species: FishSpecies,
        env_factors: EnvironmentalFactors,
    ) -> float:
        """Calculate the probability of catching a specific fish species."""
        fishing_skill = villager.skills.get("fishing", 0)

        # Base probability
        base_prob = self.BASE_CATCH_CHANCE

        # Skill bonus
        skill_bonus = min(fishing_skill * self.SKILL_BONUS_PER_LEVEL, 0.5)

        # Equipment bonus (check if villager has fishing rod or net)
        equipment_bonus = 0.0
        if any(
            item.name.lower() in ["fishing rod", "net"]
            for item in villager.inventory.keys()
        ):
            equipment_bonus = self.EQUIPMENT_BONUS

        # Environmental factors
        time_bonus = (
            0.1 if env_factors.time_of_day in target_species.active_times else -0.1
        )
        weather_bonus = (
            0.1 if env_factors.weather in target_species.weather_preference else -0.1
        )

        # Water clarity impact
        clarity_impact = env_factors.water_clarity * 0.2

        # Species-specific factors
        rarity_penalty = (1 - target_species.rarity) * 0.3
        escape_penalty = target_species.escape_chance * 0.5

        # Pollution impact
        pollution_penalty = self.pollution_level * 0.3

        # Calculate final probability
        total_prob = (
            base_prob
            + skill_bonus
            + equipment_bonus
            + time_bonus
            + weather_bonus
            + clarity_impact
            - rarity_penalty
            - escape_penalty
            - pollution_penalty
        ) * env_factors.season_modifier

        return max(0.05, min(0.95, total_prob))  # Clamp between 5% and 95%

    def _attempt_special_catch(self, villager: Villager) -> Optional[Item]:
        """Attempt to catch special items (trash, treasures, etc.)."""
        special_catch_chance = 0.1 + (self.pollution_level * 0.2)

        if random.random() < special_catch_chance:
            # Define possible special catches
            if self.pollution_level > 0.5:
                # More likely to catch trash in polluted water
                return wood  # Driftwood as trash
            elif villager.skills.get("fishing", 0) > 5:
                # Skilled fishers might find treasures
                return stone  # Precious stones

        return None

    def _update_villager_state(self, villager: Villager, result: FishingResult) -> None:
        """Update villager's health, skills, and happiness based on fishing result."""
        # Base health cost for fishing activity
        health_cost = 5

        # Additional costs/benefits based on result
        if result.success:
            # Successful fishing improves happiness
            villager.happiness = min(100, villager.happiness + 3)

            # Skill improvement
            skill_gain = 0.1 + (0.05 * result.quantity)
            if "fishing" in villager.skills:
                villager.skills["fishing"] += skill_gain
            else:
                villager.skills["fishing"] = skill_gain
        else:
            # Failed fishing decreases happiness
            villager.happiness = max(0, villager.happiness - 2)
            health_cost += 2  # Extra fatigue from failure

        # Apply health cost
        villager.health = max(0, villager.health - health_cost)

        # Random events
        if random.random() < 0.02:  # 2% chance of accident
            accident_damage = random.randint(5, 15)
            villager.health = max(0, villager.health - accident_damage)
            print(f"{villager.name} slipped on wet rocks and got injured!")

    def _update_river_state(self, species_caught: str, quantity: int) -> None:
        """Update river state after fishing."""
        # Reduce fish population
        if species_caught in self.fish_population:
            self.fish_population[species_caught] = max(
                0, self.fish_population[species_caught] - quantity
            )

        # Increase pollution slightly
        self.pollution_level = min(
            1.0, self.pollution_level + (self.POLLUTION_IMPACT * quantity / 100)
        )

    def fish(
        self, villager: Villager, fish_type: str, desired_quantity: int
    ) -> FishingResult:
        """
        Allows a villager to fish in the river.

        Args:
            villager: The villager attempting to fish
            fish_type: The type of fish to catch
            desired_quantity: The desired quantity to catch

        Returns:
            FishingResult: The result of the fishing attempt
        """
        # Check prerequisites
        can_fish, reason = self._check_fishing_prerequisites(villager)
        if not can_fish:
            return FishingResult(success=False, quantity=0, message=reason)

        # Get available fish species
        fish_species_dict = self._get_fish_species()

        # Validate fish type
        if fish_type not in fish_species_dict:
            return FishingResult(
                success=False,
                quantity=0,
                message=f"Unknown fish type: {fish_type}. Available types: {', '.join(fish_species_dict.keys())}",
            )

        target_species = fish_species_dict[fish_type]

        # Check if villager has minimum skill for this fish
        fishing_skill = villager.skills.get("fishing", 0)
        if fishing_skill < target_species.min_skill_required:
            return FishingResult(
                success=False,
                quantity=0,
                message=f"{villager.name} needs fishing skill level {target_species.min_skill_required} to catch {fish_type}",
            )

        # Check fish availability in river
        available_fish = self.fish_population.get(fish_type, 0)
        if available_fish == 0:
            return FishingResult(
                success=False,
                quantity=0,
                message=f"No {fish_type} available in {self.name}",
            )

        # Get environmental factors
        env_factors = self._get_environmental_factors()

        # Calculate catch probability
        catch_probability = self._calculate_catch_probability(
            villager, target_species, env_factors
        )

        # Attempt to catch fish
        fish_caught = 0
        actual_attempts = min(desired_quantity, available_fish)

        for _ in range(actual_attempts):
            if random.random() < catch_probability:
                fish_caught += 1

                # Early exit if we've caught enough
                if fish_caught >= desired_quantity:
                    break

        # Check for special catch (only if fishing was attempted)
        special_item = None
        if actual_attempts > 0:
            special_item = self._attempt_special_catch(villager)

        # Prepare result
        if fish_caught > 0:
            # Add fish to villager's inventory
            fish_food_item = target_species.food_item
            current_count = villager.inventory.get(fish_food_item, 0)
            villager.inventory[fish_food_item] = current_count + fish_caught

            # Add special item if caught
            if special_item:
                special_count = villager.inventory.get(special_item, 0)
                villager.inventory[special_item] = special_count + 1

            result = FishingResult(
                success=True,
                catch=fish_food_item,
                quantity=fish_caught,
                special_item=special_item,
                message=f"{villager.name} caught {fish_caught} {fish_type}"
                + (f" and found {special_item.name}!" if special_item else ""),
            )

            # Update river state
            self._update_river_state(fish_type, fish_caught)
        else:
            result = FishingResult(
                success=False,
                quantity=0,
                special_item=special_item,
                message=f"{villager.name} failed to catch any {fish_type}"
                + (f" but found {special_item.name}!" if special_item else ""),
            )

            # Add special item even if no fish caught
            if special_item:
                special_count = villager.inventory.get(special_item, 0)
                villager.inventory[special_item] = special_count + 1

        # Update villager state (health, skills, happiness)
        self._update_villager_state(villager, result)

        return result
