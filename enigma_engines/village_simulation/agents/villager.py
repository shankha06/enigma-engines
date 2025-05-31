from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field as PydanticField

from enigma_engines.village_simulation.agents.action_plan import (
    ActionPlan,
    ActionType,
    create_buying_action,
    create_eating_action,
    create_sleep_action,
    create_working_action,
)
from enigma_engines.village_simulation.environment.field import Field
from enigma_engines.village_simulation.environment.river import River
from enigma_engines.village_simulation.environment.tannery import Tannery
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
    wine,
)
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial,
)
from enigma_engines.village_simulation.utilities import backend_logger


class Villager(BaseModel):
    """
    Represents a villager in the village simulation.
    Villagers can have a name, age, occupation, and a set of skills.
    Villagers can also have a list of items they own, which can include clothing, food, and raw materials.

    Attributes:
        name (str): The name of the villager.
        age (int): The age of the villager.
        occupation (str): The occupation of the villager.
        skills (Dict[str, int]): A dictionary mapping skill names to their levels.
        inventory (Dict[Union[RawMaterial, Food, Clothing], int]): A dictionary mapping items to their quantities.

        money (float): The amount of money the villager has.
        health (int): The health of the villager, indicating how well they can perform tasks.
        happiness (int): The happiness level of the villager, affecting their productivity.

    daily_work(): Simulates daily work for the villager, including crafting and selling items.
    eat_food(food: Food): Allows the villager to consume food, affecting health and happiness.

    buy_item(item: Union[RawMaterial, Food, Clothing], quantity: int, vendor: Vendor) -> bool:
        Allows the villager to buy items from a vendor, reducing their money and increasing their inventory.
    sell_item(item: Union[RawMaterial, Food, Clothing], quantity: int, vendor: Vendor) -> bool:
        Allows the villager to sell items to a vendor, increasing their money and reducing their inventory.

    """

    name: str
    age: int
    skills: Dict[str, int]
    inventory: Dict[Union[RawMaterial, Food, Clothing], int]
    money: float
    health: int
    happiness: int
    energy: int = 100  # Energy level for performing actions
    is_alive: bool = True  # Indicates if the villager is alive
    employer: Optional[Union[Tannery, Field, River]] = (
        None  # The villager's employer, if any
    )

    current_action_plan: List[ActionPlan] = PydanticField(default_factory=list)
    action_history: List[ActionPlan] = PydanticField(default_factory=list)

    def eat_food(self):
        """Allows the villager to consume food, affecting health and happiness."""
        # Loops over the inventory to find most optimal food item that can be eaten based on nutritional value and current health
        best_food = None
        for food in self.inventory:
            if isinstance(food, Food) and self.inventory[food] > 0:
                if (
                    best_food is None
                    or food.nutritional_value > best_food.nutritional_value
                ):
                    best_food = food

        if best_food:
            self.inventory[best_food] -= 1
            self.health += best_food.nutritional_value
            self.happiness += 5
        else:
            backend_logger.info(f"{self.name} does not have food to eat.")

    def buy_item(self):
        # Allows the villager to buy items from a vendor, reducing their money and increasing their inventory.
        # Villager prioritises buying food first, then clothing. The priority is based on the villager's needs.
        # If villager has enough health and food, they will not buy food.
        if self.health < 50 and self.money > 0:
            # Priotise which food to buy based on nutritional value, money available, and inventory count.
            best_food = None
            for food in [apple, bread, roast_meat, fish, beer, wine]:
                if self.inventory.get(food, 0) < 1 and self.money >= food.base_value:
                    if (
                        best_food is None
                        or food.nutritional_value > best_food.nutritional_value
                    ):
                        best_food = food
            if best_food:
                # Simulate buying the food item
                self.inventory[best_food] = self.inventory.get(best_food, 0) + 1
                self.money -= best_food.base_value
                backend_logger.info(f"{self.name} bought {best_food.name}.")
        else:
            backend_logger.info(f"{self.name} does not need to buy food right now.")
        # If villager has enough clothing, they will not buy clothing.
        if self.health > 50 and self.inventory.get(Clothing, 0) > 0:
            return
        best_clothing = None
        for clothing in daily_clothes + men_armor + women_wear:
            if (
                self.inventory.get(clothing, 0) < 1
                and self.money >= clothing.base_value
            ):
                if best_clothing is None or clothing.quality > best_clothing.quality:
                    best_clothing = clothing
        if best_clothing:
            # Simulate buying the clothing item
            self.inventory[best_clothing] = self.inventory.get(best_clothing, 0) + 1
            self.money -= best_clothing.base_value
            backend_logger.info(f"{self.name} bought {best_clothing.name}.")
        else:
            backend_logger.info(f"{self.name} does not need to buy clothing right now.")

    def plan_next_action(self) -> Optional[ActionPlan]:
        """
        Plans the next action for the villager based on their current state.
        Returns the highest priority action that can be executed.
        """
        potential_actions = []

        # Check if villager needs sleep
        if self.energy < 30:
            sleep_action = create_sleep_action()
            if sleep_action.can_execute(self):
                potential_actions.append(sleep_action)

        # Check if villager needs to eat
        if self.health < 70:
            for food in self.inventory:
                if isinstance(food, Food) and self.inventory[food] > 0:
                    eat_action = create_eating_action(food)
                    if eat_action.can_execute(self):
                        potential_actions.append(eat_action)
                        break

        # Check if villager needs to buy food
        if self.health < 50 and self.money > 10:
            for food in [apple, bread, roast_meat, fish]:
                if self.inventory.get(food, 0) < 2:
                    buy_action = create_buying_action(food)
                    if buy_action.can_execute(self):
                        potential_actions.append(buy_action)
                        break

        # Check if villager should work
        if self.energy > 40 and self.health > 40 and self.employer:
            work_action = create_working_action(
                location=str(type(self.employer).__name__), duration=8
            )
            if work_action.can_execute(self):
                potential_actions.append(work_action)

        # Sort by priority and return the highest priority action
        if potential_actions:
            potential_actions.sort(key=lambda x: x.priority, reverse=True)
            return potential_actions[0]

        return None

    def execute_action(self, action: ActionPlan) -> bool:
        """
        Executes the given action plan and updates the villager's state.

        Args:
            action: The ActionPlan to execute.

        Returns:
            bool: True if the action was successfully executed, False otherwise.
        """
        if not action.can_execute(self):
            backend_logger.info(f"{self.name} cannot execute action: {action}")
            return False

        backend_logger.info(f"{self.name} is executing action: {action}")

        # Handle specific action types
        if action.action_type == ActionType.EATING:
            if action.target_item and isinstance(action.target_item, Food):
                self.inventory[action.target_item] -= action.quantity
                # Apply food-specific benefits
                self.health += action.target_item.nutritional_value
                self.happiness += 5

        elif action.action_type == ActionType.BUYING:
            if action.target_item:
                self.inventory[action.target_item] = (
                    self.inventory.get(action.target_item, 0) + action.quantity
                )
                self.money -= action.target_item.base_value * action.quantity

        elif action.action_type == ActionType.SELLING:
            if action.target_item:
                self.inventory[action.target_item] -= action.quantity
                self.money += (
                    action.target_item.base_value * action.quantity * 0.8
                )  # 80% of base value

        # Apply general impact
        action.apply_impact(self)

        # Add to action history
        self.action_history.append(action)

        # Remove from current plan if it was there
        if action in self.current_action_plan:
            self.current_action_plan.remove(action)

        backend_logger.info(
            f"{self.name} completed action. Health: {self.health}, "
            f"Happiness: {self.happiness}, Energy: {self.energy}, Money: {self.money}"
        )

        return True

    def add_action_to_plan(self, action: ActionPlan) -> None:
        """Adds an action to the current action plan."""
        self.current_action_plan.append(action)
        # Sort by priority
        self.current_action_plan.sort(key=lambda x: x.priority, reverse=True)

    def clear_action_plan(self) -> None:
        """Clears the current action plan."""
        self.current_action_plan.clear()

    def get_next_planned_action(self) -> Optional[ActionPlan]:
        """
        Gets the next action from the current plan that can be executed.

        Returns:
            Optional[ActionPlan]: The next executable action, or None if no actions can be executed.
        """
        for action in self.current_action_plan:
            if action.can_execute(self):
                return action
        return None
