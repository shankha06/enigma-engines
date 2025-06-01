import math
import random
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel
from pydantic import Field as PydanticField

from enigma_engines.village_simulation.agents.action_plan import (
    ActionPlan, 
    ActionType,
    create_sleep_action,
    create_eating_action,
    create_buying_action,
    create_foraging_action,
    create_fishing_action,
    create_hunting_action,
    create_woodcutting_action,
    create_selling_goods_action,
    create_tannery_work_action,
    create_working_action,
)
from enigma_engines.village_simulation.environment.forest import Forest
from enigma_engines.village_simulation.environment.river import River
from enigma_engines.village_simulation.environment.tannery import Tannery
from enigma_engines.village_simulation.environment.weather import (
    Season,
    TimeOfDay,
    WeatherCondition,
    WeatherSystem,
)
from enigma_engines.village_simulation.resources.clothing import Clothing
from enigma_engines.village_simulation.resources.food import (
    Food, apple, bread, beer, fish, berries, fish_food, wild_meat_food
)
from enigma_engines.village_simulation.resources.item import Item
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial, wood, raw_hide, leather, herbs
)
from enigma_engines.village_simulation.utilities.id_generator import generate_medieval_villager_name
from enigma_engines.village_simulation.utilities.logger import backend_logger

# --- Villager Class ---
class Villager(BaseModel):
    name: str
    age: int
    occupation: str # e.g., "Farmer", "Hunter", "Fisherman", "Tanner", "Woodcutter", "Forager"
    skills: Dict[str, float] = PydanticField(default_factory=dict) # Skill levels as floats for finer progression
    inventory: Dict[Item, int] = PydanticField(default_factory=dict)
    money: float = 20.0
    health: int = 100 # Max 100
    happiness: int = 70 # Max 100
    energy: int = 100 # Max 100
    is_alive: bool = True
    
    # Environment context (can be set by the simulation)
    current_river: Optional[Any] = None # RiverPlaceholder or actual River
    current_forest: Optional[Any] = None # ForestPlaceholder or actual Forest
    current_tannery: Optional[Any] = None # Tannery or placeholder
    weather_system: Optional[Any] = None # WeatherSystemPlaceholder or actual WeatherSystem

    current_action_plan_list: List[ActionPlan] = PydanticField(default_factory=list) # Renamed to avoid Pydantic confusion
    action_history: List[ActionPlan] = PydanticField(default_factory=list)

    # Constants for needs thresholds
    FOOD_LOW_THRESHOLD: int = 40 # Health below which villager prioritizes eating/getting food
    ENERGY_LOW_THRESHOLD: int = 30 # Energy below which villager prioritizes sleeping
    MIN_FOOD_STOCK: int = 2 # Minimum units of any food type before trying to acquire more

    class Config:
        arbitrary_types_allowed = True

    def get_skill(self, skill_name: str) -> float:
        return self.skills.get(skill_name, 0.0)

    def increase_skill(self, skill_name: str, amount: float = 0.1):
        current_skill = self.get_skill(skill_name)
        self.skills[skill_name] = round(min(current_skill + amount, 10.0), 2) # Max skill level 10

    def _get_best_food_in_inventory(self) -> Optional[Food]:
        best_food: Optional[Food] = None
        max_nutrition = -1
        for item, quantity in self.inventory.items():
            if isinstance(item, Food) and quantity > 0:
                if item.nutritional_value > max_nutrition:
                    max_nutrition = item.nutritional_value
                    best_food = item
        return best_food

    def plan_next_actions(self, world_knowledge: Optional[Dict[str, Any]] = None) -> None:
        """
        Plans a series of actions based on needs and opportunities.
        Populates self.current_action_plan_list.
        `world_knowledge` can provide context like available forests, rivers, market prices.
        """
        if not self.is_alive:
            return

        # Clear previous plan if not empty, or decide if to continue multi-step plans
        self.current_action_plan_list.clear()
        potential_actions: List[ActionPlan] = []

        # 1. Survival: Sleep if energy is very low
        if self.energy < self.ENERGY_LOW_THRESHOLD:
            potential_actions.append(create_sleep_action(duration=8))

        # 2. Survival: Eat if health is low and has food
        if self.health < self.FOOD_LOW_THRESHOLD:
            food_to_eat = self._get_best_food_in_inventory()
            if food_to_eat:
                potential_actions.append(create_eating_action(food_to_eat))
            else:
                # No food, need to acquire it. This will be prioritized below.
                self.happiness = max(0, self.happiness - 5) # Unhappy if hungry and no food

        # 3. Acquire Food if low on health/food stock
        has_any_food = any(isinstance(item, Food) and qty > 0 for item, qty in self.inventory.items())
        if self.health < 70 or not has_any_food:
            # Option A: Forage (if forest available and skill is okay)
            if self.current_forest and self.get_skill("foraging") >= 0: # No min skill for basic foraging
                potential_actions.append(create_foraging_action(self.current_forest, hours=2))
            
            # Option B: Fish (if river available and skill is okay)
            if self.current_river and self.get_skill("fishing") >= 0.5:
                potential_actions.append(create_fishing_action(self.current_river, hours=3, target_fish="any"))

            # Option C: Hunt (if forest available and skill is okay)
            if self.current_forest and self.get_skill("hunting") >= 1.0:
                 # Simplification: try to hunt most common/easiest animal or any
                huntable = self.current_forest.get_huntable_wildlife() if hasattr(self.current_forest, 'get_huntable_wildlife') else {"deer": 5}
                if huntable:
                    target_animal = random.choice(list(huntable.keys())) # Simplistic choice
                    potential_actions.append(create_hunting_action(self.current_forest, target_species=target_animal, hours=4))
            
            # Option D: Buy food (if has money and market accessible - simplified)
            # This part is complex without a market system, so we'll simplify to "try to buy apple"
            if self.money >= apple.base_value and not any(item.name == "Apple" and qty > 0 for item, qty in self.inventory.items()):
                potential_actions.append(create_buying_action(apple, quantity=2))


        # 4. Work based on occupation / earn money
        if self.energy > 50 and self.health > 50:
            if self.occupation == "Woodcutter" and self.current_forest:
                potential_actions.append(create_woodcutting_action(self.current_forest, hours=4))
            elif self.occupation == "Hunter" and self.current_forest and self.get_skill("hunting") > 0.5:
                huntable = self.current_forest.get_huntable_wildlife() if hasattr(self.current_forest, 'get_huntable_wildlife') else {"rabbit": 10}
                if huntable:
                    potential_actions.append(create_hunting_action(self.current_forest, target_species=random.choice(list(huntable.keys())), hours=4))
            elif self.occupation == "Fisherman" and self.current_river:
                potential_actions.append(create_fishing_action(self.current_river, hours=4))
            elif self.occupation == "Forager" and self.current_forest:
                 potential_actions.append(create_foraging_action(self.current_forest, hours=3))
            elif self.occupation == "Tanner" and self.current_tannery:
                if self.inventory.get(raw_hide, 0) > 0: # Needs hides to work
                    potential_actions.append(create_tannery_work_action(self.current_tannery, hours=4))
                else: # Try to acquire hides if tanner and no hides
                    if self.money > raw_hide.base_value * 2:
                         potential_actions.append(create_buying_action(raw_hide, quantity=2))
            # Add other occupations: Farmer (Field), Blacksmith, etc.
            # Generic work action if no specific task
            # potential_actions.append(create_working_action(location="Village", duration=4, job_type="general labor"))


        # 5. Sell surplus goods (if inventory is full or has valuable items)
        # Simplified: sell some logs if woodcutter and has many, or sell leather if tanner
        if self.occupation == "Woodcutter" and self.inventory.get(wood, 0) > 10:
            potential_actions.append(create_selling_goods_action(wood, quantity=5))
        if self.occupation == "Tanner" and self.inventory.get(leather, 0) > 2:
            potential_actions.append(create_selling_goods_action(leather, quantity=1))
        
        # Sort by priority and add to plan
        potential_actions.sort(key=lambda x: x.priority, reverse=True)
        if potential_actions:
            self.current_action_plan_list.append(potential_actions[0]) # Takes the highest priority action for now
            # A more complex planner could build a sequence.

    def execute_next_action(self) -> bool:
        if not self.is_alive or not self.current_action_plan_list:
            # Try to plan if no actions
            if self.is_alive: self.plan_next_actions()
            if not self.current_action_plan_list:
                # If still no plan, villager is idle
                idle_action = ActionPlan(action_type=ActionType.IDLE, priority=0, duration_hours=1, description="Idling")
                idle_action.apply_impact(self) # Consume a little energy even when idle
                self.action_history.append(idle_action)
                return True # Idling is a valid state
            
        action = self.current_action_plan_list.pop(0) # Get and remove the first action

        if not action.can_execute(self):
            # print(f"{self.name} cannot execute action: {action.description}. Re-planning might be needed.")
            return False

        # print(f"{self.name} executing: {action.description} (Energy: {self.energy}, Health: {self.health})")
        
        success = True # Assume success unless specific action fails
        action_message = f"{self.name} completed {action.description}."

        # --- Handle specific action types ---
        # Get duration from either duration_hours or duration field
        duration = action.duration_hours if action.duration_hours is not None else action.duration
        
        if action.action_type == ActionType.SLEEPING:
            self.energy = min(100, self.energy + duration * 10) # Energy recovery
            self.health = min(100, self.health + duration * 1) # Slight health recovery
        
        elif action.action_type == ActionType.EATING:
            if action.target_item and isinstance(action.target_item, Food) and self.inventory.get(action.target_item, 0) >= action.quantity:
                self.inventory[action.target_item] -= action.quantity
                self.health = min(100, self.health + action.target_item.nutritional_value * action.quantity)
                self.happiness = min(100, self.happiness + 5 * action.quantity)
                if self.inventory[action.target_item] == 0:
                    del self.inventory[action.target_item]
            else:
                success = False; action_message = f"{self.name} failed to eat: {action.target_item.name if action.target_item else 'N/A'} not enough in inventory."

        elif action.action_type == ActionType.BUYING:
            if action.target_item and self.money >= action.target_item.base_value * action.quantity:
                self.inventory[action.target_item] = self.inventory.get(action.target_item, 0) + action.quantity
                self.money -= action.target_item.base_value * action.quantity
            else:
                success = False; action_message = f"{self.name} failed to buy: Not enough money or item unavailable."

        elif action.action_type == ActionType.SELLING_GOODS: # Generic selling
            if action.target_item and self.inventory.get(action.target_item, 0) >= action.quantity:
                self.inventory[action.target_item] -= action.quantity
                # Assume selling price is 80% of base value
                self.money += action.target_item.base_value * action.quantity * 0.8 
                if self.inventory[action.target_item] == 0:
                    del self.inventory[action.target_item]
            else:
                success = False; action_message = f"{self.name} failed to sell: Not enough {action.target_item.name if action.target_item else 'N/A'} in inventory."
        
        elif action.action_type == ActionType.FISHING:
            river_target = action.target_location
            if river_target and hasattr(river_target, 'attempt_fishing') and self.weather_system:
                # Pass villager instance for skill checks etc. within river's method
                time_of_day = self.weather_system.get_time_of_day()
                fish_result = river_target.attempt_fishing(self, str(action.target_entity), time_of_day, duration)
                action_message = fish_result.message
                if fish_result.success and fish_result.catch and fish_result.quantity > 0:
                    # The River's attempt_fishing should ideally handle adding to villager inventory.
                    # If not, add it here. Assuming it does.
                    # For now, let's assume the fish_result.catch is the Food item to add.
                    # And the River class already updated inventory.
                    self.increase_skill("fishing", 0.1 * fish_result.quantity)
                    self.happiness = min(100, self.happiness + 2 * fish_result.quantity)
                elif not fish_result.success:
                    self.happiness = max(0, self.happiness - 2)
            else: success = False; action_message = f"{self.name} cannot fish: No valid river or weather system."

        elif action.action_type == ActionType.HUNTING:
            forest_target = action.target_location
            species_to_hunt = str(action.target_entity)
            if forest_target and hasattr(forest_target, 'record_animal_hunted') and species_to_hunt:
                # Skill check can influence success before calling record_animal_hunted
                hunt_skill = self.get_skill("hunting")
                success_chance = 0.3 + hunt_skill * 0.05 # Base 30% + 5% per skill level
                if random.random() < success_chance:
                    if forest_target.record_animal_hunted(species_name=species_to_hunt, count=1):
                        # Add meat/hide to inventory
                        self.inventory[wild_meat_food] = self.inventory.get(wild_meat_food, 0) + 1
                        self.inventory[raw_hide] = self.inventory.get(raw_hide, 0) + 1
                        action_message = f"{self.name} successfully hunted a {species_to_hunt}."
                        self.increase_skill("hunting", 0.2)
                        self.happiness = min(100, self.happiness + 10)
                    else:
                        success = False; action_message = f"{self.name} failed to hunt {species_to_hunt} (forest reported failure or none available)."
                        self.happiness = max(0, self.happiness - 5)
                else:
                    success = False; action_message = f"{self.name} tried to hunt {species_to_hunt} but failed (skill check)."
                    self.increase_skill("hunting", 0.05) # Small skill gain for trying
                    self.happiness = max(0, self.happiness - 3)
            else: success = False; action_message = f"{self.name} cannot hunt: No valid forest or target."

        elif action.action_type == ActionType.WOODCUTTING:
            forest_target = action.target_location
            if forest_target and hasattr(forest_target, 'cut_trees'):
                # Amount to cut based on skill and duration
                woodcutting_skill = self.get_skill("woodcutting")
                amount_to_try_cut = int(duration * (1 + woodcutting_skill * 0.5))
                
                actually_cut, wood_types_yield = forest_target.cut_trees(amount_to_try_cut)
                if actually_cut > 0:
                    self.inventory[wood] = self.inventory.get(wood, 0) + actually_cut
                    action_message = f"{self.name} cut {actually_cut} logs. Yield: {wood_types_yield}."
                    self.increase_skill("woodcutting", 0.1 * actually_cut)
                    self.happiness = min(100, self.happiness + 1 * actually_cut)
                else:
                    action_message = f"{self.name} tried to cut wood but got none."
                    self.happiness = max(0, self.happiness - 1)
            else: success = False; action_message = f"{self.name} cannot cut wood: No valid forest."

        elif action.action_type == ActionType.FORAGING:
            forest_target = action.target_location
            if forest_target and hasattr(forest_target, 'health'): # Use forest health/undergrowth
                foraging_skill = self.get_skill("foraging")
                # Success and yield based on skill, forest health, undergrowth
                forage_chance = 0.4 + foraging_skill * 0.05 + forest_target.undergrowth_density * 0.2 + forest_target.health * 0.1
                if random.random() < forage_chance:
                    # Determine what was found (simplified)
                    found_item = random.choice([berries, herbs])
                    found_quantity = random.randint(1, int(1 + foraging_skill + duration))
                    self.inventory[found_item] = self.inventory.get(found_item, 0) + found_quantity
                    action_message = f"{self.name} foraged and found {found_quantity} {found_item.name}."
                    self.increase_skill("foraging", 0.15 * found_quantity)
                    self.happiness = min(100, self.happiness + 3 * found_quantity)
                else:
                    action_message = f"{self.name} foraged but found nothing."
                    self.increase_skill("foraging", 0.05)
                    self.happiness = max(0, self.happiness - 2)
            else: success = False; action_message = f"{self.name} cannot forage: No valid forest."

        elif action.action_type == ActionType.TANNERY_WORK:
            tannery_target = action.target_location
            if isinstance(tannery_target, Tannery) and hasattr(tannery_target, 'process_hides'):
                hides_to_process = self.inventory.get(raw_hide, 0)
                tanning_skill = self.get_skill("tanning")
                if hides_to_process > 0:
                    leather_produced, hides_used = tannery_target.process_hides(hides_to_process, int(tanning_skill))
                    
                    self.inventory[raw_hide] -= hides_used
                    if self.inventory[raw_hide] == 0: del self.inventory[raw_hide]
                    self.inventory[leather] = self.inventory.get(leather, 0) + leather_produced
                    
                    money_earned = leather_produced * (leather.base_value * 0.2) # Earn a fraction for work
                    self.money += money_earned
                    action_message = f"{self.name} worked at the tannery, produced {leather_produced} leather, earned {money_earned:.1f}."
                    self.increase_skill("tanning", 0.1 * leather_produced)
                    self.happiness = min(100, self.happiness + 2 * leather_produced)
                else:
                    action_message = f"{self.name} wanted to work at tannery but had no raw hides."
            else: success = False; action_message = f"{self.name} cannot work at tannery: Invalid target."
        
        elif action.action_type == ActionType.WORKING: # Generic work, e.g. farming if employer is Field
            # This part remains more abstract without specific Field interactions defined
            # For now, just consumes energy and gives some money/happiness
            self.money += duration * 2 # Simple wage
            self.happiness = min(100, self.happiness + duration * 1)
            action_message = f"{self.name} worked at {action.target_location} for {duration} hours."


        # Apply general impact of the action (energy, etc.)
        action.apply_impact(self)
        self.action_history.append(action)
        # print(action_message)
        # print(f"  {self.name} state: E:{self.energy}, H:{self.health}, Hap:{self.happiness}, M:{self.money:.1f}")


        # Basic needs check after action
        if self.health <= 0:
            self.is_alive = False
            # print(f"{self.name} has died.")
            return False # Stop further actions if dead
            
        return success

    def daily_needs_check_and_death(self):
        """Checks for critical needs and handles death."""
        if not self.is_alive: return

        # Starvation/Dehydration (simplified by low health)
        if self.energy <= 0 and self.health < 10: # Critically low on both
            self.health -= random.randint(5,15) # Rapid health decline
            # print(f"{self.name} is starving and exhausted! Health critically low.")
        elif self.health < 10: # Low health for other reasons
             self.health -= random.randint(1,5)


        if self.health <= 0:
            self.is_alive = False
            self.health = 0
            # print(f"{self.name} has succumbed to their hardships and died.")

    def daily_update_cycle(self, world_knowledge: Optional[Dict[str, Any]] = None):
        """Simulates a full day cycle of planning and acting for the villager."""
        if not self.is_alive:
            return

        # print(f"\n--- {self.name}'s Day Begins (E:{self.energy} H:{self.health} Hap:{self.happiness}) ---")
        
        # 1. Plan actions for the day (could be one or a sequence)
        self.plan_next_actions(world_knowledge)
        
        # 2. Execute planned actions throughout the day (simplified loop)
        # A real game loop would advance hours and let villager execute actions at appropriate times.
        # Here, we'll just execute the first few high-priority actions or until energy runs low.
        actions_this_day = 0
        MAX_ACTIONS_PER_DAY_SIM = 3 # Limit simulation complexity per cycle

        while self.current_action_plan_list and self.energy > self.ENERGY_LOW_THRESHOLD / 2 and actions_this_day < MAX_ACTIONS_PER_DAY_SIM:
            if not self.execute_next_action():
                # print(f"{self.name} failed to execute an action, re-evaluating.")
                self.plan_next_actions(world_knowledge) # Re-plan if an action fails critically
            actions_this_day += 1
            if not self.is_alive: break
        
        # If no actions were planned or executed, villager was idle or sleeping
        if actions_this_day == 0 and not self.current_action_plan_list:
             self.execute_next_action() # Will likely execute IDLE or SLEEP

        self.daily_needs_check_and_death()
        # print(f"--- {self.name}'s Day Ends (E:{self.energy} H:{self.health} Hap:{self.happiness}, Alive: {self.is_alive}) ---")