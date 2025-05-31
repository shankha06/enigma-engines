from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Union

from enigma_engines.village_simulation.resources.clothing import Clothing
from enigma_engines.village_simulation.resources.food import Food
from enigma_engines.village_simulation.resources.raw_material import RawMaterial


class ActionType(Enum):
    """Enumeration of possible actions a villager can take."""

    SLEEP = "sleep"
    FISHING = "fishing"
    BUYING = "buying"
    SELLING = "selling"
    EATING = "eating"
    INTERACTING = "interacting"
    WORKING = "working"
    CRAFTING = "crafting"
    RESTING = "resting"
    SOCIALIZING = "socializing"


@dataclass
class ActionImpact:
    """Represents the impact of an action on villager attributes."""

    health_change: int = 0
    happiness_change: int = 0
    money_change: float = 0.0
    energy_change: int = 0  # New attribute for energy management


@dataclass
class ActionPlan:
    """
    Represents an action plan for a villager.

    This class encapsulates what action a villager should perform,
    what interactions or resources it requires, and its impact on
    the villager's attributes.

    Attributes:
        action_type (ActionType): The type of action to be performed.
        target_item (Optional[Union[RawMaterial, Food, Clothing]]): The item involved in the action, if any.
        quantity (int): The quantity of items involved in the action.
        target_villager (Optional[str]): The name of another villager involved in interaction, if any.
        duration (int): The duration of the action in time units (e.g., hours).
        priority (int): The priority level of this action (higher values = higher priority).
        impact (ActionImpact): The expected impact of this action on villager attributes.
        requirements (Dict[str, Union[int, float]]): Requirements for the action (e.g., minimum health, money).
        location (Optional[str]): The location where the action should be performed.
    """

    action_type: ActionType
    target_item: Optional[Union[RawMaterial, Food, Clothing]] = None
    quantity: int = 1
    target_villager: Optional[str] = None
    duration: int = 1  # in hours
    priority: int = 5  # 1-10 scale, with 10 being highest priority
    impact: ActionImpact = None
    requirements: Dict[str, Union[int, float]] = None
    location: Optional[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass initialization."""
        if self.impact is None:
            self.impact = self._calculate_default_impact()

        if self.requirements is None:
            self.requirements = self._calculate_default_requirements()

    def _calculate_default_impact(self) -> ActionImpact:
        """Calculate default impact based on action type."""
        impact_map = {
            ActionType.SLEEP: ActionImpact(
                health_change=20, happiness_change=10, energy_change=50
            ),
            ActionType.FISHING: ActionImpact(
                health_change=-5, happiness_change=5, energy_change=-20
            ),
            ActionType.BUYING: ActionImpact(happiness_change=5, money_change=-10.0),
            ActionType.SELLING: ActionImpact(happiness_change=5, money_change=10.0),
            ActionType.EATING: ActionImpact(
                health_change=15, happiness_change=10, energy_change=10
            ),
            ActionType.INTERACTING: ActionImpact(happiness_change=15, energy_change=-5),
            ActionType.WORKING: ActionImpact(
                health_change=-10, money_change=20.0, energy_change=-30
            ),
            ActionType.CRAFTING: ActionImpact(happiness_change=5, energy_change=-15),
            ActionType.RESTING: ActionImpact(health_change=5, energy_change=20),
            ActionType.SOCIALIZING: ActionImpact(
                happiness_change=20, energy_change=-10
            ),
        }
        return impact_map.get(self.action_type, ActionImpact())

    def _calculate_default_requirements(self) -> Dict[str, Union[int, float]]:
        """Calculate default requirements based on action type."""
        requirements_map = {
            ActionType.SLEEP: {"min_energy": 0},
            ActionType.FISHING: {"min_health": 30, "min_energy": 20},
            ActionType.BUYING: {"min_money": 5.0},
            ActionType.SELLING: {"min_items": 1},
            ActionType.EATING: {"min_food": 1},
            ActionType.INTERACTING: {"min_energy": 10},
            ActionType.WORKING: {"min_health": 40, "min_energy": 30},
            ActionType.CRAFTING: {"min_energy": 15, "min_skill": 1},
            ActionType.RESTING: {"min_energy": 0},
            ActionType.SOCIALIZING: {"min_energy": 10, "min_happiness": 20},
        }
        return requirements_map.get(self.action_type, {})

    def can_execute(self, villager) -> bool:
        """
        Check if the villager can execute this action based on requirements.

        Args:
            villager: The villager object to check requirements against.

        Returns:
            bool: True if the villager meets all requirements, False otherwise.
        """
        if (
            "min_health" in self.requirements
            and villager.health < self.requirements["min_health"]
        ):
            return False

        if (
            "min_money" in self.requirements
            and villager.money < self.requirements["min_money"]
        ):
            return False

        if (
            "min_happiness" in self.requirements
            and villager.happiness < self.requirements["min_happiness"]
        ):
            return False

        if "min_energy" in self.requirements and hasattr(villager, "energy"):
            if villager.energy < self.requirements["min_energy"]:
                return False

        if self.action_type == ActionType.EATING and self.target_item:
            if (
                self.target_item not in villager.inventory
                or villager.inventory[self.target_item] < self.quantity
            ):
                return False

        if self.action_type == ActionType.SELLING and self.target_item:
            if (
                self.target_item not in villager.inventory
                or villager.inventory[self.target_item] < self.quantity
            ):
                return False

        return True

    def apply_impact(self, villager) -> None:
        """
        Apply the impact of this action to the villager's attributes.

        Args:
            villager: The villager object to apply the impact to.
        """
        villager.health = max(0, min(100, villager.health + self.impact.health_change))
        villager.happiness = max(
            0, min(100, villager.happiness + self.impact.happiness_change)
        )
        villager.money = max(0, villager.money + self.impact.money_change)

        if hasattr(villager, "energy"):
            villager.energy = max(
                0, min(100, villager.energy + self.impact.energy_change)
            )

    def __str__(self) -> str:
        """String representation of the action plan."""
        parts = [f"Action: {self.action_type.value}"]

        if self.target_item:
            parts.append(f"Item: {self.target_item.name} x{self.quantity}")

        if self.target_villager:
            parts.append(f"With: {self.target_villager}")

        if self.location:
            parts.append(f"At: {self.location}")

        parts.append(f"Duration: {self.duration}h")
        parts.append(f"Priority: {self.priority}/10")

        return " | ".join(parts)

    def __repr__(self) -> str:
        """Detailed representation of the action plan."""
        return (
            f"ActionPlan(action_type={self.action_type}, "
            f"target_item={self.target_item.name if self.target_item else None}, "
            f"quantity={self.quantity}, "
            f"target_villager={self.target_villager}, "
            f"duration={self.duration}, "
            f"priority={self.priority})"
        )


# Example factory functions for common action plans
def create_sleep_action(duration: int = 8) -> ActionPlan:
    """Create a sleep action plan."""
    return ActionPlan(
        action_type=ActionType.SLEEP, duration=duration, priority=8, location="home"
    )


def create_eating_action(food_item: Food, quantity: int = 1) -> ActionPlan:
    """Create an eating action plan."""
    return ActionPlan(
        action_type=ActionType.EATING,
        target_item=food_item,
        quantity=quantity,
        priority=9,
        duration=1,
    )


def create_buying_action(
    item: Union[RawMaterial, Food, Clothing],
    quantity: int = 1,
    location: str = "market",
) -> ActionPlan:
    """Create a buying action plan."""
    return ActionPlan(
        action_type=ActionType.BUYING,
        target_item=item,
        quantity=quantity,
        priority=6,
        duration=1,
        location=location,
    )


def create_interaction_action(target_villager: str, duration: int = 1) -> ActionPlan:
    """Create an interaction action plan."""
    return ActionPlan(
        action_type=ActionType.INTERACTING,
        target_villager=target_villager,
        duration=duration,
        priority=5,
    )


def create_working_action(location: str, duration: int = 8) -> ActionPlan:
    """Create a working action plan."""
    return ActionPlan(
        action_type=ActionType.WORKING, duration=duration, priority=7, location=location
    )
