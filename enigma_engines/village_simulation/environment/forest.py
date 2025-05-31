import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from enigma_engines.village_simulation.agents.villager import Villager
from enigma_engines.village_simulation.resources.food import (
    Food,
    roast_meat,
)
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial,
    fabric,
    skin,
    stone,
    wood,
)


@dataclass
class AnimalType:
    """Represents a type of animal that can be hunted in the forest."""

    name: str
    danger_level: float  # 0.0 to 1.0
    food_yield: Food
    material_yield: Optional[Tuple[RawMaterial, int]] = None
    min_skill_required: int = 1
    escape_chance: float = 0.3
    icon: str = "🐾"  # Default icon for animal types


class Forest(BaseModel):
    """
    Represents a forest in the village simulation.

    Forests can be used for gathering resources such as wood, stone, and various raw materials.
    Villagers can also hunt animals in the forest for food and materials.

    Forest natural resources will regenerate over time, allowing villagers to sustainably gather resources.

    Attributes:
        name (str): The name of the forest.
        size (int): The size of the forest, indicating how many resources it can support.
        resources (Dict[RawMaterial, int]): A dictionary mapping raw materials to their quantities.
        animals (Dict[str, int]): A dictionary mapping animal names to their populations.
        villagers_present (List[Villager]): List of villagers currently in the forest.
        icon (str): Icon representing the forest.
        days_since_last_replenishment (int): Counter for natural replenishment cycle.
    """

    name: str
    size: int
    resources: Dict[RawMaterial, int] = Field(default_factory=dict)
    animals: Dict[str, int] = Field(default_factory=dict)
    villagers_present: List[Villager] = Field(default_factory=list)
    icon: str = "🌲"
    days_since_last_replenishment: int = 0

    # Configuration constants
    MIN_RESOURCE_PERCENTAGE: float = 0.2  # Keep at least 20% of max capacity
    MIN_ANIMAL_PERCENTAGE: float = 0.3  # Keep at least 30% of max animal population
    RESOURCE_REPLENISH_RATE: float = 0.05  # 5% daily growth rate
    ANIMAL_REPLENISH_RATE: float = 0.03  # 3% daily growth rate
    REPLENISH_CYCLE_DAYS: int = 7  # Full replenishment check every week

    # Skill requirements
    MIN_GATHERING_SKILL: int = 0
    MIN_HUNTING_SKILL: int = 2

    # Risk factors
    GATHERING_ACCIDENT_CHANCE: float = 0.02
    WEATHER_PENALTY_CHANCE: float = 0.15

    class Config:
        arbitrary_types_allowed = True

    def _get_animal_types(self) -> Dict[str, AnimalType]:
        """Define available animal types with their properties."""
        return {
            "rabbit": AnimalType(
                name="rabbit",
                danger_level=0.1,
                food_yield=roast_meat,
                material_yield=(skin, 1),
                min_skill_required=1,
                escape_chance=0.4,
                icon="🐇",
            ),
            "deer": AnimalType(
                name="deer",
                danger_level=0.3,
                food_yield=roast_meat,
                material_yield=(skin, 2),
                min_skill_required=3,
                escape_chance=0.5,
                icon="🦌",
            ),
            "wild_boar": AnimalType(
                name="wild_boar",
                danger_level=0.6,
                food_yield=roast_meat,
                material_yield=(skin, 3),
                min_skill_required=5,
                escape_chance=0.3,
                icon="🐗",
            ),
            "tiger": AnimalType(
                name="tiger",
                danger_level=0.9,
                food_yield=roast_meat,
                material_yield=(skin, 4),
                min_skill_required=8,
                escape_chance=0.2,
                icon="🐅",
            ),
            "fox": AnimalType(
                name="fox",
                danger_level=0.2,
                food_yield=roast_meat,
                material_yield=(skin, 1),
                min_skill_required=2,
                escape_chance=0.6,
                icon="🦊",
            ),
        }

    def _calculate_max_resources(self) -> Dict[RawMaterial, int]:
        """Calculate maximum resource capacity based on forest size."""
        return {
            wood: self.size * 50,
            stone: self.size * 30,
            fabric: self.size * 10,  # From plants like cotton
        }

    def _calculate_max_animals(self) -> Dict[str, int]:
        """Calculate maximum animal population based on forest size."""
        return {
            "rabbit": self.size * 20,
            "deer": self.size * 10,
            "wild_boar": self.size * 5,
            "tiger": self.size * 1,
            "fox": self.size * 4,
        }

    def gather_resources(
        self, villager: Villager, resource: RawMaterial, quantity: int
    ) -> bool:
        """
        Allows a villager to gather resources from the forest.

        Args:
            villager: The villager attempting to gather resources
            resource: The type of resource to gather
            quantity: The amount to gather

        Returns:
            bool: True if gathering was successful, False otherwise

        Notes:
            Gathering resources can be affected by weather conditions and villager skills.
            Accidents may occur, leading to potential injuries.
            Villagers should be cautious and aware of their surroundings while gathering.
        """
        # Check if villager is present in the forest
        if villager not in self.villagers_present:
            print(f"{villager.name} must be in the {self.name} to gather resources.")
            return False

        # Check villager health
        if villager.health < 20:
            print(
                f"{villager.name} is too weak to gather resources (health: {villager.health})."
            )
            return False

        # Check gathering skill
        gathering_skill = villager.skills.get("gathering", 0)
        if gathering_skill < self.MIN_GATHERING_SKILL:
            print(f"{villager.name} lacks the gathering skill to collect resources.")
            return False

        # Check resource availability
        available = self.resources.get(resource, 0)
        max_resources = self._calculate_max_resources()
        min_required = int(
            max_resources.get(resource, 0) * self.MIN_RESOURCE_PERCENTAGE
        )

        if available <= min_required:
            print(
                f"The {self.name} needs to preserve its {resource.name} for regeneration."
            )
            return False

        # Calculate actual gathering amount based on skill and randomness
        skill_modifier = 1 + (gathering_skill * 0.1)
        weather_modifier = 0.7 if random.random() < self.WEATHER_PENALTY_CHANCE else 1.0

        if weather_modifier < 1.0:
            print(
                f"Poor weather conditions affect {villager.name}'s gathering efficiency."
            )

        max_gatherable = min(
            quantity,
            available - min_required,
            int(10 * skill_modifier),  # Max gathering per attempt based on skill
        )

        actual_gathered = int(
            max_gatherable * weather_modifier * random.uniform(0.7, 1.0)
        )

        if actual_gathered <= 0:
            print(f"{villager.name} couldn't gather any {resource.name} this time.")
            return False

        # Apply gathering effects
        self.resources[resource] -= actual_gathered

        # Add to villager inventory
        if resource in villager.inventory:
            villager.inventory[resource] += actual_gathered
        else:
            villager.inventory[resource] = actual_gathered

        # Health and fatigue effects
        health_cost = 3 + int(actual_gathered * 0.5)

        # Check for accidents
        if random.random() < self.GATHERING_ACCIDENT_CHANCE:
            health_cost += 10
            print(f"{villager.name} had a minor accident while gathering!")

        villager.health = max(0, villager.health - health_cost)

        # Improve gathering skill
        skill_improvement = min(0.1 * (actual_gathered / 10), 0.5)
        if "gathering" in villager.skills:
            villager.skills["gathering"] += skill_improvement
        else:
            villager.skills["gathering"] = skill_improvement

        # Update happiness based on success
        villager.happiness = min(100, villager.happiness + 2)

        print(
            f"{villager.name} successfully gathered {actual_gathered} {resource.name}."
        )
        return True

    def hunt_animal(self, villager: Villager, animal: str) -> Optional[Food]:
        """
        Allows a villager to hunt animals in the forest.

        Args:
            villager: The villager attempting to hunt
            animal: The type of animal to hunt

        Returns:
            Optional[Food]: The food obtained from hunting, or None if unsuccessful

        Notes:
            Hunting requires the villager to have sufficient health and skills.
            The success of hunting is affected by weather conditions and animal escape chances.
            Villagers should be cautious of the dangers associated with hunting.
        """
        # Check if villager is present in the forest
        if villager not in self.villagers_present:
            print(f"{villager.name} must be in the {self.name} to hunt.")
            return None

        # Check villager health
        if villager.health < 30:
            print(f"{villager.name} is too weak to hunt (health: {villager.health}).")
            return None

        # Check hunting skill
        hunting_skill = villager.skills.get("hunting", 0)
        if hunting_skill < self.MIN_HUNTING_SKILL:
            print(
                f"{villager.name} lacks the hunting skill (requires level {self.MIN_HUNTING_SKILL})."
            )
            return None

        # Check animal availability
        animal_types = self._get_animal_types()
        if animal not in animal_types:
            print(f"Unknown animal type: {animal}")
            return None

        animal_type = animal_types[animal]
        available = self.animals.get(animal, 0)
        max_animals = self._calculate_max_animals()
        min_required = int(max_animals.get(animal, 0) * self.MIN_ANIMAL_PERCENTAGE)

        if available <= min_required:
            print(
                f"The {self.name} needs to preserve its {animal} population for regeneration."
            )
            return None

        # Check skill requirement for specific animal
        if hunting_skill < animal_type.min_skill_required:
            print(
                f"{villager.name} needs hunting skill {animal_type.min_skill_required} to hunt {animal}."
            )
            return None

        # Calculate hunting success
        skill_modifier = hunting_skill / 10
        base_success_chance = 0.3 + skill_modifier - animal_type.escape_chance

        # Weather affects hunting
        if random.random() < self.WEATHER_PENALTY_CHANCE:
            base_success_chance *= 0.7
            print(
                f"Poor weather conditions make hunting more difficult for {villager.name}."
            )

        # Attempt the hunt
        if random.random() > base_success_chance:
            print(f"{villager.name} failed to catch the {animal} - it escaped!")
            villager.health = max(0, villager.health - 5)
            villager.happiness = max(0, villager.happiness - 3)
            return None

        # Successful hunt
        self.animals[animal] -= 1

        # Get food yield
        food_obtained = animal_type.food_yield

        # Add food to villager inventory
        if food_obtained in villager.inventory:
            villager.inventory[food_obtained] += 1
        else:
            villager.inventory[food_obtained] = 1

        # Get material yield
        if animal_type.material_yield:
            material, quantity = animal_type.material_yield
            if material in villager.inventory:
                villager.inventory[material] += quantity
            else:
                villager.inventory[material] = quantity
            print(
                f"{villager.name} also obtained {quantity} {material.name} from the hunt."
            )

        # Health cost and danger
        base_health_cost = 10
        danger_cost = int(animal_type.danger_level * 20)

        # Check for hunting injuries based on danger level
        if random.random() < animal_type.danger_level:
            injury = int(animal_type.danger_level * 30)
            base_health_cost += injury
            print(f"{villager.name} was injured by the {animal} during the hunt!")

        villager.health = max(0, villager.health - (base_health_cost + danger_cost))

        # Improve hunting skill
        skill_improvement = 0.2 + (animal_type.danger_level * 0.3)
        if "hunting" in villager.skills:
            villager.skills["hunting"] += skill_improvement
        else:
            villager.skills["hunting"] = skill_improvement

        # Update happiness based on successful hunt
        villager.happiness = min(100, villager.happiness + 5)

        print(
            f"{villager.name} successfully hunted a {animal} and obtained {food_obtained.name}!"
        )
        return food_obtained

    def replenish_resources(self) -> None:
        """
        Naturally replenish forest resources and animal populations over time.
        This function should be called periodically (e.g., daily) in the simulation.
        """
        self.days_since_last_replenishment += 1

        # Get maximum capacities
        max_resources = self._calculate_max_resources()
        max_animals = self._calculate_max_animals()

        # Daily passive regeneration
        for resource, max_amount in max_resources.items():
            current = self.resources.get(resource, 0)
            if current < max_amount:
                # Natural growth with randomness
                growth_rate = self.RESOURCE_REPLENISH_RATE * random.uniform(0.5, 1.5)
                growth = int(max_amount * growth_rate)

                # Accelerated growth if below minimum threshold
                if current < max_amount * self.MIN_RESOURCE_PERCENTAGE:
                    growth *= 2

                self.resources[resource] = min(current + growth, max_amount)

        # Animal population growth
        for animal, max_population in max_animals.items():
            current = self.animals.get(animal, 0)
            if (
                current < max_population and current > 0
            ):  # Need at least 1 for reproduction
                # Natural reproduction with randomness
                growth_rate = self.ANIMAL_REPLENISH_RATE * random.uniform(0.3, 1.2)

                # Population growth is proportional to current population
                growth = int(current * growth_rate)
                growth = max(1, growth)  # At least 1 if population exists

                # Accelerated growth if below minimum threshold
                if current < max_population * self.MIN_ANIMAL_PERCENTAGE:
                    growth *= 2

                self.animals[animal] = min(current + growth, max_population)

        # Reset replenishment counter weekly
        if self.days_since_last_replenishment >= 7:
            self.days_since_last_replenishment = 0
