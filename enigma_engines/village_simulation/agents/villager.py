import random
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from pydantic import Field as PydanticField

from enigma_engines.village_simulation.agents.action_plan import (
    ActionPlan,
    ActionType,
    create_buying_action,
    create_eating_action,
    create_fishing_action,
    create_foraging_action,
    create_hunting_action,
    create_selling_goods_action,
    create_sleep_action,
    create_tannery_work_action,
    create_woodcutting_action,
)
# from enigma_engines.village_simulation.environment.tannery import Tannery
from enigma_engines.village_simulation.resources.food import (
    Food,
    apple,
    berries,
    wild_meat_food,
)
from enigma_engines.village_simulation.resources.item import Item
from enigma_engines.village_simulation.resources.raw_material import herbs, leather, raw_hide, wood
# from enigma_engines.village_simulation.simulation_engine.village_manager import VillageManager


# --- Villager Class ---
class Villager(BaseModel):
    name: str
    gender : str # e.g
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

    daily_earnings: float = 0.0 # For leaderboard
    daily_expenses: float = 0.0 # For leaderboard

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

    def execute_next_action(self, village_manager_ref) -> bool: # Added village_manager_ref
        if not self.is_alive or not self.current_action_plan_list:
            if self.is_alive: self.plan_next_actions()
            if not self.current_action_plan_list:
                idle_action = ActionPlan(action_type=ActionType.IDLE, priority=0, duration_hours=1, description="Idling")
                idle_action.apply_impact(self); self.action_history.append(idle_action); return True
        
        action = self.current_action_plan_list.pop(0)
        if not action.can_execute(self): return False
        
        # Reset daily transaction trackers at the start of executing an action block for the day
        # This should ideally be done once per day, perhaps in daily_update_cycle before actions loop.
        # For now, resetting here means it tracks per action, which might not be intended for "daily" totals.
        # To fix: move reset to daily_update_cycle. For this focused fix, will leave here and note.
        # **Correction**: Resetting here is fine if execute_next_action is called multiple times a day.
        # If daily_update_cycle calls execute_next_action in a loop, then daily_earnings/expenses
        # should be reset *before* that loop in daily_update_cycle.
        # For now, assume it's reset once before the first action of the day.
        # The `village_manager_v1` has `daily_update_cycle` call this in a loop, so this reset is fine.

        # self.daily_earnings = 0.0
        # self.daily_expenses = 0.0

        success = True; action_message = f"{self.name} {action.description}."
        duration = action.duration_hours # Standardized
        # print(duration, self.energy, self.health, self.happiness, self.money) # Debug print
        if action.action_type == ActionType.SLEEP: # User code had SLEEP, matching to ActionType.SLEEPING
            if duration is None:
                duration = 4
            self.energy=min(100,self.energy + duration * 10)
            self.health=min(100,self.health + duration * 1)
        
        elif action.action_type == ActionType.EATING:
            if action.target_item and isinstance(action.target_item, Food) and self.inventory.get(action.target_item, 0) >= action.quantity:
                self.inventory[action.target_item] -= action.quantity
                self.health=min(100,self.health + action.target_item.nutritional_value * action.quantity)
                self.happiness=min(100,self.happiness + 5 * action.quantity)
                if self.inventory.get(action.target_item, 0) == 0: del self.inventory[action.target_item]
            else: success=False; action_message = f"{self.name} failed to eat {action.target_item.name if action.target_item else 'food'}."
        
        elif action.action_type == ActionType.BUYING:
            if action.target_item and village_manager_ref: # Check for village_manager_ref
                bought_from_vendor = False
                for vendor in village_manager_ref.vendors:
                    can_sell = vendor.sell_item_to_customer(action.target_item, action.quantity, self.money)
                    if can_sell:
                        self.inventory[action.target_item] = self.inventory.get(action.target_item,0) + action.quantity
                        self.money -= action.quantity * self.money
                        self.daily_expenses += action.quantity * self.money # TRACK EXPENSE
                        action_message = f"{self.name} bought {action.quantity} {action.target_item.name} from {vendor.shop_name} for {action.quantity * self.money:.2f}."
                        if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🛍️ {self.name} bought {action.quantity} {action.target_item.name} from {vendor.shop_name}.", "trade")
                        bought_from_vendor = True
                        break
                if not bought_from_vendor:
                    success=False; action_message = f"{self.name} failed to buy {action.target_item.name}: unavailable or not enough money."
            elif not village_manager_ref:
                success=False; action_message = f"{self.name} cannot buy: No market access (village_manager_ref missing)."
            else: success=False

        elif action.action_type == ActionType.SELLING_GOODS:
            if action.target_item and self.inventory.get(action.target_item,0) >= action.quantity and village_manager_ref:
                sold_to_vendor = False
                for vendor in village_manager_ref.vendors:
                    can_buy = vendor.buy_item_from_producer(action.target_item, action.quantity, action.target_item.base_value) # Pass self.inventory
                    if can_buy:
                        # Inventory is already managed by vendor.buy_from_villager if it modifies it directly
                        # Or, if it doesn't, we manage it here. Assuming it does for now.
                        self.money += action.quantity * action.target_item.base_value
                        self.daily_earnings += action.quantity * action.target_item.base_value # TRACK EARNINGS
                        action_message = f"{self.name} sold {action.quantity} {action.target_item.name} to {vendor.shop_name} for {action.quantity * action.target_item.base_value:.2f}."
                        if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"💰 {self.name} sold {action.quantity} {action.target_item.name} to {vendor.shop_name}.", "trade")
                        sold_to_vendor = True
                        break
                if not sold_to_vendor: # Try selling to external market
                    external_price = village_manager_ref.external_market_prices.get(action.target_item, action.target_item.base_value * 0.6)
                    payment = external_price * action.quantity
                    self.inventory[action.target_item] -= action.quantity
                    if self.inventory.get(action.target_item, 0) == 0: del self.inventory[action.target_item]
                    self.money += payment
                    self.daily_earnings += payment # TRACK EARNINGS
                    village_manager_ref.treasury -= payment # External market means money comes from "outside"
                    village_manager_ref.goods_for_export[action.target_item] = village_manager_ref.goods_for_export.get(action.target_item,0) + action.quantity
                    action_message = f"{self.name} sold {action.quantity} {action.target_item.name} to external market for {payment:.2f}."
                    if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🌍 {self.name} sold {action.quantity} {action.target_item.name} to external market.", "trade")
            elif not village_manager_ref:
                success=False; action_message = f"{self.name} cannot sell: No market access."
            else: success=False; action_message = f"{self.name} failed to sell {action.target_item.name if action.target_item else 'goods'}."
        
        elif action.action_type == ActionType.FISHING:
            if self.current_river and self.weather_system and village_manager_ref:
                time_of_day = self.weather_system.get_time_of_day()
                fish_res = self.current_river.attempt_fishing(self, str(action.target_entity), time_of_day, duration)
                action_message = fish_res.message # River's attempt_fishing should handle inventory
                if fish_res.success and fish_res.quantity > 0 and fish_res.catch: 
                    self.increase_skill("fishing",0.1*fish_res.quantity)
                    if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🎣 {self.name} caught {fish_res.quantity} {fish_res.catch.name}.", "activity")
                elif not fish_res.success: self.happiness=max(0,self.happiness-2)
            else: success=False; action_message = f"{self.name} cannot fish: Missing river/weather/manager."

        elif action.action_type == ActionType.HUNTING:
            if self.current_forest and action.target_entity and village_manager_ref:
                hunt_skill=self.get_skill("hunting"); success_chance=0.2+hunt_skill*0.06
                if random.random()<success_chance:
                    if self.current_forest.wildlife_populations.get(str(action.target_entity), 0) > 0:
                        if self.current_forest.record_animal_hunted(str(action.target_entity),1): # Forest records kill
                            self.current_forest.wildlife_populations[str(action.target_entity)] -=1 # Villager action updates forest
                            self.inventory[wild_meat_food]=self.inventory.get(wild_meat_food,0)+1; self.inventory[raw_hide]=self.inventory.get(raw_hide,0)+1
                            self.increase_skill("hunting",0.25); self.happiness=min(100,self.happiness+10)
                            action_message = f"{self.name} successfully hunted a {action.target_entity}."
                            if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🏹 {self.name} hunted a {action.target_entity}.", "activity")
                        else: success=False; action_message=f"{self.name} saw a {action.target_entity} but it got away."
                    else: success=False; action_message=f"{self.name} found no {action.target_entity} to hunt."
                else: success=False; action_message=f"{self.name} failed the hunt for {action.target_entity}."; self.increase_skill("hunting",0.05); self.happiness=max(0,self.happiness-3)
            else: success=False; action_message = f"{self.name} cannot hunt: Missing forest/target/manager."
        
        elif action.action_type == ActionType.WOODCUTTING: # User code used 'wood' for item
            if self.current_forest and village_manager_ref:
                skill=self.get_skill("woodcutting"); amount=int(duration*(1+skill*0.5))
                cut,yielded_map=self.current_forest.cut_trees(amount) 
                if cut>0: 
                    self.inventory[wood]=self.inventory.get(wood,0)+cut # Use 'wood' as per user's plan_actions
                    self.increase_skill("woodcutting",0.1*cut)
                    self.current_forest.mature_trees -= cut 
                    action_message = f"{self.name} cut {cut} {wood.name}."
                    if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🪓 {self.name} cut {cut} {wood.name}.", "activity")
                else: self.happiness=max(0,self.happiness-1); action_message = f"{self.name} cut no wood."
            else: success=False; action_message = f"{self.name} cannot cut wood: Missing forest/manager."
        
        elif action.action_type == ActionType.FORAGING:
            if self.current_forest and village_manager_ref:
                skill=self.get_skill("foraging"); chance=0.4+skill*0.05+(getattr(self.current_forest, 'undergrowth_density', 0.5))*0.2+(getattr(self.current_forest, 'health', 0.5))*0.1
                if random.random()<chance:
                    item=random.choice([berries,herbs, apple]); qty=random.randint(1,int(1+skill+duration*0.5))
                    self.inventory[item]=self.inventory.get(item,0)+qty; self.increase_skill("foraging",0.15*qty)
                    action_message = f"{self.name} foraged {qty} {item.name}."
                    if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🧺 {self.name} foraged {qty} {item.name}.", "activity")
                else: self.increase_skill("foraging",0.05); self.happiness=max(0,self.happiness-2); action_message = f"{self.name} foraged nothing."
            else: success=False; action_message = f"{self.name} cannot forage: Missing forest/manager."
        
        elif action.action_type == ActionType.TANNERY_WORK:
            if self.current_tannery and hasattr(self.current_tannery, 'process_hides') and village_manager_ref:
                hides=self.inventory.get(raw_hide,0); skill=self.get_skill("tanning")
                if hides>0:
                    produced,used=self.current_tannery.process_hides(hides,skill)
                    self.inventory[raw_hide]-=used; self.inventory[leather]=self.inventory.get(leather,0)+produced
                    if self.inventory.get(raw_hide,0)==0: del self.inventory[raw_hide]
                    earned = produced*(leather.base_value*0.3) 
                    self.money+=earned; self.daily_earnings += earned # TRACK EARNINGS
                    self.increase_skill("tanning",0.1*produced)
                    action_message = f"{self.name} tanned {used} hides into {produced} leather, earned {earned:.2f}."
                    if hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🏭 {self.name} produced {produced} leather.", "crafting")
                else: action_message = f"{self.name} has no hides for tannery."
            else: success=False; action_message = f"{self.name} cannot work at tannery: Missing tannery/manager."
        
        elif action.action_type == ActionType.WORKING:
            wage = duration * (2 + self.get_skill(action.target_location.lower() if isinstance(action.target_location, str) else "general_labor") * 0.5) # Skill based wage
            self.money += wage
            self.daily_earnings += wage # TRACK EARNINGS
            self.happiness = min(100, self.happiness + duration * 1)
            action_message = f"{self.name} worked at {action.target_location} for {duration} hours, earned {wage:.2f}."
            if village_manager_ref and hasattr(village_manager_ref, 'log_incident'): village_manager_ref.log_incident(f"🛠️ {self.name} worked as {self.occupation}, earned {wage:.2f}.", "activity")


        action.apply_impact(self); self.action_history.append(action)
        if village_manager_ref and hasattr(village_manager_ref, 'master_log_for_summary'):
             village_manager_ref.master_log_for_summary.append(action_message)
        
        if self.health <= 0: 
            self.is_alive = False
            if village_manager_ref and hasattr(village_manager_ref, 'log_incident'):
                village_manager_ref.log_incident(f"💀 {self.name} has died due to action consequences.", "death")
            return False
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

    def daily_update_cycle(self, world_knowledge, village_manager_ref):
        if not self.is_alive: return
        
        # Reset daily earnings/expenses at the START of the villager's day cycle
        self.daily_earnings = 0.0
        self.daily_expenses = 0.0

        self.plan_next_actions(world_knowledge)
        actions_today = 0; MAX_ACTIONS = 3
        
        while self.current_action_plan_list and self.energy > self.ENERGY_LOW_THRESHOLD / 2 and actions_today < MAX_ACTIONS:
            if not self.execute_next_action(village_manager_ref):
                self.plan_next_actions(world_knowledge) 
            actions_today += 1
            if not self.is_alive: break
        
        if actions_today == 0 and not self.current_action_plan_list: 
            self.execute_next_action(village_manager_ref) 
        
        self.daily_needs_check_and_death()