from typing import Any, Dict, List, Optional
import random
import datetime
import math  # For math.ceil

from enigma_engines.animal_crossing.core.load_data import ACNHItemDataset
from enigma_engines.animal_crossing.core.villager import ACNHVillager

class ACNHEnvironment:
    # Constants for fishing probability
    BASE_FISH_CATCH_PROBABILITY = 0.6
    FISHING_PROBABILITY_DECREMENT_PER_ATTEMPT = 0.05  # 10% reduction per attempt
    MIN_FISH_CATCH_PROBABILITY = 0.10                 # Minimum 10% chance
    
    def __init__(
        self,
        num_villagers=3,
        dataset: ACNHItemDataset = None, # Type hint with placeholder
        data_path="data",
        max_plots=10,
        # New parameters for dynamic villager addition
        villager_addition_interval_days: int = 3,
        villager_addition_percentage: float = 0.20, # e.g., 20% of current, or at least 1
        max_total_villagers: int = 500
    ):
        self.dataset = dataset if dataset else ACNHItemDataset(data_path=data_path)
        self._initial_num_villagers = num_villagers
        self.max_farm_plots = max_plots # Ensure this is set before reset if reset uses it

        # --- Saturation Constants ---
        self.FISH_SATURATION_IMPACT_PER_ITEM = 0.03  # How much selling one fish impacts its factor
        self.FISH_SATURATION_MIN_FACTOR = 0.2
        self.FISH_SATURATION_DAILY_RECOVERY_RATE = 0.05 # Additive recovery
        
        self.TURNIP_SATURATION_IMPACT_PER_100_SOLD = 0.05 # How much selling 100 turnips impacts factor
        self.TURNIP_SATURATION_MIN_FACTOR = 0.2
        self.TURNIP_SATURATION_DAILY_RECOVERY_RATE = 0.03 # Additive recovery
        self.TURNIP_SATURATION_MAX_FACTOR = 1.2 # Allows for "good market" days
        
        # Tracker for fishing attempts per villager per day
        self.fishing_attempts_today: Dict[str, int] = {}
        
        # Villager addition dynamics
        self.VILLAGER_ADDITION_INTERVAL_DAYS = villager_addition_interval_days
        self.VILLAGER_ADDITION_PERCENTAGE = villager_addition_percentage
        self.MAX_TOTAL_VILLAGERS = max_total_villagers
        
        self.reset() # Calls most initializations

    def _populate_initial_villagers(self, num_to_populate: int):
        if not self.dataset.villager_names: 
            self.villagers = []
            return
            
        current_villager_names = {v.name for v in self.villagers}
        potential_new_names = [name for name in self.dataset.villager_names if name not in current_villager_names]
        
        num_can_add = min(num_to_populate, len(potential_new_names))
        
        if num_can_add > 0:
            names_to_add = random.sample(potential_new_names, num_can_add)
            for name in names_to_add: 
                self.villagers.append(ACNHVillager(name))
    def _conditionally_add_new_villagers(self):
        """
        Checks if new villagers should be added based on interval and capacity, then adds them.
        """
        if len(self.villagers) >= self.MAX_TOTAL_VILLAGERS:
            # print(f"DEBUG: Max villagers ({self.MAX_TOTAL_VILLAGERS}) reached. No new villagers added on day {self.current_day}.")
            return

        # Calculate number to potentially add based on percentage of current villagers
        num_to_potentially_add = math.ceil(len(self.villagers) * self.VILLAGER_ADDITION_PERCENTAGE)
        
        # Ensure at least 1 is considered if percentage is non-zero, island isn't full, and calculation resulted in 0
        if num_to_potentially_add == 0 and self.VILLAGER_ADDITION_PERCENTAGE > 0.0 and len(self.villagers) < self.MAX_TOTAL_VILLAGERS and len(self.villagers) > 0 :
            num_to_potentially_add = 1
        elif len(self.villagers) == 0 and self.VILLAGER_ADDITION_PERCENTAGE > 0.0 and self._initial_num_villagers > 0: # Special case if island is empty but should have villagers
             num_to_potentially_add = min(1, self.MAX_TOTAL_VILLAGERS)


        if num_to_potentially_add > 0:
            remaining_capacity = self.MAX_TOTAL_VILLAGERS - len(self.villagers)
            actual_num_to_add = min(num_to_potentially_add, remaining_capacity)

            if actual_num_to_add > 0:
                # print(f"DEBUG: Day {self.current_day}. Attempting to add {actual_num_to_add} new villagers (current: {len(self.villagers)}, max: {self.MAX_TOTAL_VILLAGERS}).")
                self._populate_villagers(actual_num_to_add)
            # else:
                # print(f"DEBUG: Day {self.current_day}. Calculated {num_to_potentially_add} to add, but remaining capacity is 0 or less.")
        # else:
            # print(f"DEBUG: Day {self.current_day}. Calculated 0 villagers to add based on percentage or island is full/empty with no initial target.")

    def reset(self):
        self.current_day = 0
        self.current_catch_probability = self.BASE_FISH_CATCH_PROBABILITY # Reset to base probability
        self.current_date = datetime.date(2025, 4, 6) # Example start date
        self.villagers: List[ACNHVillager] = []
        
        # Ensure initial population respects MAX_TOTAL_VILLAGERS
        num_for_reset = min(self._initial_num_villagers, self.MAX_TOTAL_VILLAGERS)
        if self.dataset.villager_names:
            self._populate_initial_villagers(num_for_reset)

        for v in self.villagers: v.reset_daily_log()
        
        # Reset fishing attempts tracker
        self.fishing_attempts_today.clear()

        self.bells = 1000
        self.nook_miles = 500
        self.turnips_owned_by_island = 0
        self.turnip_buy_price = 0 # Daisy Mae's price for the week
        self.turnip_sell_price = 0 # Nook's price for the current day
        self.turnip_market_saturation_factor = 1.0 # Starts at no saturation
        
        self.fish_market_saturation: Dict[str, float] = {} # fish_name: factor

        self.farm_plots: Dict[int, Dict] = {
            i: {"crop_name": None, "plant_day": -1, "ready_day": -1, "owner_villager": None}
            for i in range(self.max_farm_plots)
        }
        self.active_nook_tasks: Dict[str, Dict] = {}
        
        self.update_turnip_prices() # Sets initial turnip prices for day 0
        self.assign_daily_nook_tasks()

        # Conditionally add new villagers
        if self.current_day > 0 and self.VILLAGER_ADDITION_INTERVAL_DAYS > 0 and \
           self.current_day % self.VILLAGER_ADDITION_INTERVAL_DAYS == 0:
            self._conditionally_add_new_villagers()

    def update_turnip_prices(self):
        """Updates turnip buy/sell prices for the current day."""
        # Daily recovery of turnip market saturation happens here implicitly before new price is set
        # Or could be in advance_day_cycle. Let's make it explicit here.
        # self.turnip_market_saturation_factor = min(self.TURNIP_SATURATION_MAX_FACTOR, self.turnip_market_saturation_factor + self.TURNIP_SATURATION_DAILY_RECOVERY_RATE)
        # The above line is moved to advance_day_cycle for clearer separation.

        day_of_week = self.current_date.weekday() # Monday is 0, Sunday is 6

        if day_of_week == 6:  # Sunday - Daisy Mae sells
            self.turnip_buy_price = random.randint(90, 110)
            self.turnip_sell_price = 0 # Can't sell to Nook's on Sunday
        else:  # Monday to Saturday - Nooklings buy
            self.turnip_buy_price = 0 # Can't buy from Daisy Mae
            
            # Determine base price trend (highly simplified)
            # Real ACNH has patterns (random, decreasing, small spike, large spike)
            base_sell_price = random.randint(40, 150) # Base for "normal" days
            if random.random() < 0.15: # Chance of a spike
                 base_sell_price = random.randint(150, 600)
            
            # Apply saturation factor (capped at 1.0 for price calculation to prevent inflation over 100% of base)
            effective_saturation = min(1.0, self.turnip_market_saturation_factor)
            self.turnip_sell_price = int(base_sell_price * effective_saturation)
            self.turnip_sell_price = max(10, self.turnip_sell_price) # Price floor

    def _get_saturated_fish_price(self, fish_name: str, base_price: int) -> int:
        factor = self.fish_market_saturation.get(fish_name, 1.0)
        return int(base_price * factor)

    def _update_fish_market_on_sale(self, fish_name: str, quantity_sold: int):
        current_factor = self.fish_market_saturation.get(fish_name, 1.0)
        impact = quantity_sold * self.FISH_SATURATION_IMPACT_PER_ITEM
        new_factor = max(self.FISH_SATURATION_MIN_FACTOR, current_factor - impact)
        self.fish_market_saturation[fish_name] = new_factor
        # print(f"DEBUG: Fish market for {fish_name} updated. Factor: {new_factor:.2f} (sold {quantity_sold})")

    def _update_turnip_market_on_sale(self, quantity_sold: int):
        impact = (quantity_sold / 100.0) * self.TURNIP_SATURATION_IMPACT_PER_100_SOLD
        self.turnip_market_saturation_factor = max(self.TURNIP_SATURATION_MIN_FACTOR, self.turnip_market_saturation_factor - impact)
        # print(f"DEBUG: Turnip market updated. Factor: {self.turnip_market_saturation_factor:.2f} (sold {quantity_sold})")


    def assign_daily_nook_tasks(self, count=3): # Reduced default count for quicker testing
        self.active_nook_tasks = self.dataset.get_daily_nook_miles_task_templates(count=count)

    def _check_task_criteria(self, agent: "ACNHVillager", task_name: str) -> bool:
        task_details = self.active_nook_tasks.get(task_name)

        # If task details are missing or no criteria are defined, assume completable.
        # This handles cases where "criteria" key is missing or is an empty dict.
        if not task_details or not task_details.get("criteria"):
            return True

        criteria = task_details["criteria"]
        # If criteria is an empty dictionary (e.g. criteria: {}), it's also considered completable.
        if not criteria:
            return True

        c_type = criteria.get("type")
        c_item_name = criteria.get("item_name")
        c_quantity = criteria.get(
            "quantity", 1
        )  # Default to 1 if quantity not specified
        c_category = criteria.get("category")

        if c_type == "collect_item":  # Check current inventory
            return agent.inventory.get(c_item_name, 0) >= c_quantity

        elif (
            c_type == "sell_item_category"
        ):  # Check daily log for sales of this category
            sold_amount = 0
            for sale_event in agent.daily_activity_log.get("sold_items", []):
                if sale_event.get("category") == c_category:
                    sold_amount += sale_event.get("quantity", 0)
            return sold_amount >= c_quantity

        elif c_type == "catch_specific_fish":  # Requires logging fish catches
            return agent.inventory.get(c_item_name, 0) >= c_quantity

        elif (
            c_type == "earn_bells_selling"
        ):  # Check daily log for total bells earned from sales
            total_earned_from_sales = sum(
                s.get("value", 0)
                for s in agent.daily_activity_log.get("sold_items", [])
            )
            return (
                total_earned_from_sales >= c_quantity
            )  # Here c_quantity is the bell amount

        elif c_type == "plant_crop":
            planted_count = 0
            for plant_event in agent.daily_activity_log.get("planted_crops", []):
                if c_item_name:  # Specific crop name provided in task criteria
                    if plant_event.get("crop_name") == c_item_name:
                        planted_count += plant_event.get("quantity", 0)
                else:  # Any crop
                    planted_count += plant_event.get("quantity", 0)
            return planted_count >= c_quantity

        elif c_type == "talk_to_villagers":
            interactions = agent.daily_activity_log.get("talked_to_villagers", [])
            if c_item_name:  # Task is to talk to a specific villager
                count_specific_villager = interactions.count(c_item_name)
                return count_specific_villager >= c_quantity
            else:  # Task is to talk to a number of unique villagers
                unique_villagers_talked_to = set(interactions)
                return len(unique_villagers_talked_to) >= c_quantity

        elif c_type == "spend_bells":
            total_spent = 0
            for spend_event in agent.daily_activity_log.get("spent_bells_events", []):
                total_spent += spend_event.get("amount", 0)
            return total_spent >= c_quantity
        return False

    def step(self, action: Dict, agent_obj: Optional[ACNHVillager] = None ): # agent_obj is the acting villager
        delta_friendship_total = 0
        delta_bells = 0  # For the acting agent/player
        delta_nook_miles = 0 # For the acting agent/player

        acting_villager: Optional[ACNHVillager] = None
        if isinstance(agent_obj, ACNHVillager):
            acting_villager = agent_obj
        elif "villager_name" in action: # Resolve from action if agent_obj not passed directly
            actor_name = action.get("villager_name")
            if actor_name:
                acting_villager = next((v for v in self.villagers if v.name == actor_name), None)
                if not acting_villager and actor_name == "Player": # Special case if Player is not in self.villagers list
                    # This implies the "Player" agent is separate. For now, let's assume Player actions affect island bells/miles.
                    # For _check_task_criteria, a Player object with inventory/logs would be needed.
                    # Let's create a dummy "Player" villager object if needed for actions that require one
                    # but it's better if the agent calling env.step IS the ACNHVillager object.
                    # For now, we'll proceed if actor_name is "Player" and assume island resources.
                    pass


        action_type = action.get("type")
        # print(f"DEBUG ENV (Day {self.current_day}): Action '{action_type}' by '{action.get('villager_name', 'N/A')}'")

        # --- Actions primarily affecting the acting_villager or island resources ---
        if acting_villager:
            if action_type == "RECEIVE_GIFT":
                villager_name = action.get("villager_name")
                # gift_details should be a dictionary, for example:
                # {"item_name": "rare fossil", "friendship_points": 10}
                # The 'friendship_points' key is used by ACNHVillager.receive_gift
                gift_details = action.get("gift_details")

                # --- Begin: Code for the if block ---
                if not villager_name:
                    print("Error: 'villager_name' not provided for RECEIVE_GIFT action.")
                    # Optionally, return or raise an error
                    return

                if not gift_details:
                    print(f"Error: 'gift_details' not provided for villager '{villager_name}' for RECEIVE_GIFT action.")
                    # Optionally, return or raise an error
                    return

                # Assuming 'self.villagers' is a dictionary mapping villager names to ACNHVillager objects
                # and 'self.current_day' holds the current day in the environment.
                if villager_name in self.villagers:
                    villager = self.villagers[villager_name]
                    
                    points_earned = villager.receive_gift(gift_details, self.current_day)
                    
                    item_name_display = gift_details.get('item_name', 'a gift')
                    friendship_points_value = gift_details.get('friendship_points', 0)

                    if points_earned > 0:
                        print(f"{villager.name} received {item_name_display} (worth {friendship_points_value} points). Friendship points earned: {points_earned}.")
                        print(f"{villager.name}'s new friendship level: {villager.friendship_level}.")
                    elif villager.last_gifted_day == self.current_day and points_earned == 0 : # Check if it's because already gifted
                        print(f"{villager.name} was already gifted {item_name_display} today. No additional friendship points earned.")
                    else:
                        print(f"{villager.name} received {item_name_display}, but no friendship points were earned (e.g. gift had 0 points value).")

                else:
                    print(f"Error: Villager '{villager_name}' not found in the environment.")
            
            elif action_type == "GIVE_GIFT":
                target_villager_name = action.get("target_villager_name")
                gift_name = action.get("gift_name")
                
                # --- DEBUG Lines for GIVE_GIFT ---
                print(f"DEBUG ENV: Attempting GIVE_GIFT. Actor: {acting_villager.name}, Target: {target_villager_name}, Gift: {gift_name}")

                target_villager = next(
                    (v for v in self.villagers if v.name == target_villager_name), None
                )
                gift_details = self.dataset.get_gift_details(gift_name)

                print(f"DEBUG ENV: Target Villager found: {target_villager.name if target_villager else 'None'}")
                print(f"DEBUG ENV: Gift Details from dataset for '{gift_name}': {gift_details}")

                if target_villager and gift_details:
                    print(gift_details)
                    cost_of_gift = gift_details.get("cost", 0)
                    friendship_points_potential = gift_details.get("friendship_points", 0)
                    print(f"DEBUG ENV: Gift cost: {cost_of_gift}, Potential friendship points: {friendship_points_potential}, Island bells: {self.bells}")

                    if self.bells >= cost_of_gift: # Island pays or facilitates
                        can_proceed_with_gifting = False
                        if gift_name == "Wrapped Fruit": # Example special item
                            can_proceed_with_gifting = True
                            print("DEBUG ENV: 'Wrapped Fruit' gift, proceeding.")
                        elif acting_villager.remove_from_inventory(gift_name, 1):
                            can_proceed_with_gifting = True
                            print(f"DEBUG ENV: Gift '{gift_name}' removed from {acting_villager.name}'s inventory.")
                        else:
                            # Allow gift if island pays, even if not in inventory (design choice)
                            can_proceed_with_gifting = True
                            print(f"DEBUG ENV: Gift '{gift_name}' not in {acting_villager.name}'s inventory, but island pays. Proceeding.")
                        
                        if can_proceed_with_gifting:
                            self.bells -= cost_of_gift
                            delta_bells -= cost_of_gift
                            
                            # This is the crucial call to the villager object
                            friendship_gain = target_villager.receive_gift(
                                gift_details, self.current_day
                            )
                            # --- DEBUG Line for friendship_gain ---
                            print(f"DEBUG ENV: `target_villager.receive_gift()` returned friendship_gain: {friendship_gain}")
                            
                            if not isinstance(friendship_gain, (int, float)):
                                print(f"WARNING ENV: `receive_gift` for {target_villager.name} returned non-numeric value: {friendship_gain}. Treating as 0.")
                                friendship_gain = 0

                            delta_friendship_total += friendship_gain
                            print(f"DEBUG ENV: Gift given. delta_friendship_total is now: {delta_friendship_total}. Target {target_villager.name} new friendship: {target_villager.friendship_level} (check villager's internal state)")
                        else:
                            print(f"DEBUG ENV: Gifting conditions not fully met for {gift_name} to {target_villager_name}.")
                    else:
                        print(f"DEBUG ENV: Island cannot afford gift. Cost: {cost_of_gift}, Bells: {self.bells}")
                else:
                    if not target_villager: print(f"DEBUG ENV: Target villager '{target_villager_name}' not found.")
                    if not gift_details: print(f"DEBUG ENV: Gift details for '{gift_name}' not found.")
            
            
            elif action_type == "TALK_TO_VILLAGER": # New action
                target_villager_name = action.get("target_villager_name")
                target_villager = next((v for v in self.villagers if v.name == target_villager_name), None)
                if target_villager and target_villager != acting_villager:
                    # Simulate a small, fixed friendship boost for talking
                    base_friendship_gain = 5 # Example value
                    # In a real scenario, use target_villager.receive_interaction("talk") or similar
                    target_villager.friendship_level = min(255, target_villager.friendship_level + base_friendship_gain)
                    delta_friendship_total += base_friendship_gain
                    # print(f"DEBUG: {acting_villager.name} talked to {target_villager.name}. Friendship +{base_friendship_gain}")

            elif action_type == "DO_NOOK_MILES_TASK":
                task_name = action.get("task_name")
                if task_name in self.active_nook_tasks:
                    if self._check_task_criteria(acting_villager, task_name): # Pass the specific villager
                        task_info = self.active_nook_tasks.pop(task_name) # Task consumed
                        # Nook Miles awarded to the island pool or player agent
                        self.nook_miles += task_info["miles"]; delta_nook_miles += task_info["miles"]
                    # else: print(f"DEBUG: Criteria not met for task {task_name} by {acting_villager.name}")
                # else: print(f"DEBUG: Task {task_name} not active or already completed.")

            elif action_type == "SELL_ITEMS":
                items_to_sell_list = action.get("items_to_sell_list", []) # e.g. [{"name": "Sea Bass", "quantity": 1}, ...]
                total_earnings_for_action = 0
                for item_sale_info in items_to_sell_list:
                    item_name = item_sale_info.get("name")
                    quantity_to_sell = item_sale_info.get("quantity", 0)

                    if not item_name or quantity_to_sell <= 0: continue
                    if acting_villager.inventory.get(item_name, 0) >= quantity_to_sell:
                        item_data = self.dataset.get_item_details(item_name) # Gets base details
                        base_sell_price = item_data.get("SellPrice", 0)
                        category = item_data.get("Category", "unknown")
                        actual_sell_price = base_sell_price

                        if category == "fish":
                            actual_sell_price = self._get_saturated_fish_price(item_name, base_sell_price)
                            self._update_fish_market_on_sale(item_name, quantity_to_sell)
                        # Add other categories like "bug" if they also have saturation

                        earnings_this_item = quantity_to_sell * actual_sell_price
                        if acting_villager.remove_from_inventory(item_name, quantity_to_sell):
                            # Bells go to the acting villager, which then could contribute to island or be their own.
                            # For simplicity, let's assume they go to the island's main bell pool.
                            self.bells += earnings_this_item
                            delta_bells += earnings_this_item # This action's direct bell impact
                            total_earnings_for_action += earnings_this_item
                            acting_villager.log_sale(item_name, quantity_to_sell, earnings_this_item, category)
                        # else: print(f"DEBUG: Failed to remove {item_name} from {acting_villager.name} inventory for selling.")
                    # else: print(f"DEBUG: {acting_villager.name} does not have enough {item_name} to sell {quantity_to_sell}.")
                # print(f"DEBUG: {acting_villager.name} sold items for {total_earnings_for_action} bells.")
            elif action_type == "PLANT_CROP":
                # ... (implementation from previous, ensure acting_villager.name is used for owner_villager)
                crop_name = action.get("crop_name"); plot_id = action.get("plot_id")
                crop_def = self.dataset.get_crop_definition(crop_name)
                if (crop_def and plot_id is not None and plot_id in self.farm_plots and self.farm_plots[plot_id]["crop_name"] is None):
                    if self.bells >= crop_def["SeedCost"]: # Island pays for seeds
                        self.bells -= crop_def["SeedCost"] # delta_bells for this action for player is 0, island pays
                        self.farm_plots[plot_id] = {"crop_name": crop_name, "plant_day": self.current_day, 
                                                  "ready_day": self.current_day + crop_def["GrowthTimeDays"], 
                                                  "owner_villager": acting_villager.name}
            
            elif action_type == "HARVEST_CROP":
                # ... (implementation from previous, ensure acting_villager gets the crop)
                plot_id = action.get("plot_id")
                if plot_id is not None and plot_id in self.farm_plots:
                    plot_info = self.farm_plots[plot_id]
                    if (plot_info["crop_name"] and plot_info.get("owner_villager") == acting_villager.name and 
                        self.current_day >= plot_info["ready_day"]):
                        crop_def = self.dataset.get_crop_definition(plot_info["crop_name"])
                        if crop_def:
                            acting_villager.add_to_inventory(plot_info["crop_name"], crop_def["Yield"])
                            self.farm_plots[plot_id] = {"crop_name": None, "plant_day": -1, "ready_day": -1, "owner_villager": None}
            elif action_type == "GO_FISHING":
                fish_name = self.dataset.get_random_fish()
                if fish_name:
                    villager_id = acting_villager.name
                    
                    # Get the number of attempts already made today by this villager
                    attempts_this_day = self.fishing_attempts_today.get(villager_id, 0)
                    
                    # Calculate current catch probability - decreases with each attempt today
                    current_catch_probability = max(
                        self.MIN_FISH_CATCH_PROBABILITY,
                        self.current_catch_probability - (attempts_this_day * self.FISHING_PROBABILITY_DECREMENT_PER_ATTEMPT)
                    )
                    self.current_catch_probability = current_catch_probability # For debugging or UI feedback
                    
                    # Increment attempts for this villager for today
                    self.fishing_attempts_today[villager_id] = attempts_this_day + 1
                    
                    if random.random() < current_catch_probability: # Dynamic catch success rate
                        acting_villager.add_to_inventory(fish_name, 1)
                        # print(f"DEBUG: {acting_villager.name} caught a {fish_name}! (Attempt: {attempts_this_day + 1}, Prob: {current_catch_probability:.2f})")
                        # Immediate bell reward is 0, value comes from selling
                    # else: print(f"DEBUG: {acting_villager.name} tried fishing but failed. (Attempt: {attempts_this_day + 1}, Prob: {current_catch_probability:.2f})")
                # else: print(f"DEBUG: No fish defined in dataset for fishing.")
            
        elif action_type == "WORK_FOR_BELLS_ISLAND": # Island benefits
            earnings = random.randint(100, 500)
            self.bells += earnings; delta_bells += earnings
        
        elif action_type == "BUY_TURNIPS": # Island buys, affects island bells
            if self.current_date.weekday() == 6 and self.turnip_buy_price > 0:
                quantity_to_buy = action.get("quantity", 0)
                cost = quantity_to_buy * self.turnip_buy_price
                if self.bells >= cost and quantity_to_buy > 0:
                    self.bells -= cost; delta_bells -= cost
                    self.turnips_owned_by_island += quantity_to_buy
                    # Optionally record who bought them if agent is part of self.villagers
                    # print(f"DEBUG: Island bought {quantity_to_buy} turnips at {self.turnip_buy_price} each.")
                else: print(f"DEBUG: Cannot buy turnips. Cost: {cost}, Bells: {self.bells}")
            else: print(f"DEBUG: Cannot buy turnips. Not Sunday or no buy price.")

        elif action_type == "SELL_TURNIPS": # Island sells, affects island bells & saturation
            if self.current_date.weekday() != 6 and self.turnip_sell_price > 0 and self.turnips_owned_by_island > 0:
                quantity_to_sell = min(action.get("quantity", 0), self.turnips_owned_by_island)
                if quantity_to_sell > 0:
                    # Price for *this* sale is based on current day's already saturated price
                    earnings = quantity_to_sell * self.turnip_sell_price 
                    self.bells += earnings; delta_bells += earnings
                    self.turnips_owned_by_island -= quantity_to_sell
                    
                    # This sale now impacts market saturation for future prices
                    self._update_turnip_market_on_sale(quantity_to_sell)
                    # print(f"DEBUG: Island sold {quantity_to_sell} turnips at {self.turnip_sell_price} each. Earnings: {earnings}. New Saturation: {self.turnip_market_saturation_factor:.3f}")
                else: print(f"DEBUG: No turnips to sell or quantity zero.")
            else: print(f"DEBUG: Cannot sell turnips. Market closed, no price, or no turnips owned. Owned: {self.turnips_owned_by_island}, Price: {self.turnip_sell_price}")


        elif action_type == "ADVANCE_DAY":
            self.advance_day_cycle() # This method now handles all daily updates including saturation recovery
        
        elif not acting_villager and action_type not in ["WORK_FOR_BELLS_ISLAND", "BUY_TURNIPS", "SELL_TURNIPS", "ADVANCE_DAY", "IDLE"]:
             print(f"WARN: Action '{action_type}' might require a specific acting_villager but none was resolved or action is unhandled for island.")


        # Calculate average friendship delta based on total points gained this step
        avg_friendship_delta = (delta_friendship_total / len(self.villagers) if self.villagers and delta_friendship_total != 0 else 0)
        return (avg_friendship_delta, delta_bells, delta_nook_miles)

    def _conditionally_add_new_villagers(self):
        """Checks if new villagers should be added based on interval and capacity, then adds them."""
        if len(self.villagers) >= self.MAX_TOTAL_VILLAGERS:
            return

        # Calculate number to potentially add based on percentage of current villagers
        # Ensure at least 1 is considered if percentage is non-zero and island isn't full
        num_to_potentially_add = math.ceil(len(self.villagers) * self.VILLAGER_ADDITION_PERCENTAGE)
        if num_to_potentially_add == 0 and self.VILLAGER_ADDITION_PERCENTAGE > 0.0 and len(self.villagers) < self.MAX_TOTAL_VILLAGERS:
            num_to_potentially_add = 1
        
        if num_to_potentially_add > 0:
            remaining_capacity = self.MAX_TOTAL_VILLAGERS - len(self.villagers)
            actual_num_to_add = min(num_to_potentially_add, remaining_capacity)

            if actual_num_to_add > 0:
                self._populate_initial_villagers(actual_num_to_add)

    def advance_day_cycle(self):
        self.current_day += 1
        self.current_date += datetime.timedelta(days=1)
        for villager in self.villagers:
            villager.reset_daily_log()
            
        # Reset fishing attempts tracker for the new day
        self.fishing_attempts_today.clear()

        # Recover Fish Market Saturation
        for fish_name in list(self.fish_market_saturation.keys()): # Iterate over keys copy for safe deletion
            current_factor = self.fish_market_saturation[fish_name]
            recovered_factor = min(1.0, current_factor + self.FISH_SATURATION_DAILY_RECOVERY_RATE)
            if recovered_factor >= 0.99: # If almost fully recovered, remove from dict to save space
                del self.fish_market_saturation[fish_name]
            else:
                self.fish_market_saturation[fish_name] = recovered_factor
        
        # Recover Turnip Market Saturation
        self.turnip_market_saturation_factor = min(
            self.TURNIP_SATURATION_MAX_FACTOR, # Can recover slightly above 1.0 for "good market" feel
            self.turnip_market_saturation_factor + self.TURNIP_SATURATION_DAILY_RECOVERY_RATE
        )

        self.update_turnip_prices() # This will use the recovered saturation factor
        self.assign_daily_nook_tasks()
        
        # Conditionally add new villagers
        if self.current_day > 0 and self.current_day % self.VILLAGER_ADDITION_INTERVAL_DAYS == 0:
            self._conditionally_add_new_villagers()


    def get_state(self) -> Dict[str, Any]: # Added type hint for clarity
        avg_friendship = sum(v.friendship_level for v in self.villagers) / len(self.villagers) if self.villagers else 0
        # Ensure player_inventory is part of the state if agent needs it
        # This assumes 'Player' is an ACNHVillager instance in self.villagers or handled separately.
        player_obj = next((v for v in self.villagers if v.name == "Player"), None) # Example: find Player
        player_inv_for_state = []
        if player_obj:
             player_inv_for_state = [{"name": name, "quantity": qty, "sell_price": self.dataset.get_item_details(name).get("SellPrice",0) } 
                                     for name, qty in player_obj.inventory.items()]


        return {
            "current_day": self.current_day,
            "current_date": self.current_date.strftime("%Y-%m-%d"), # For older agent compat
            "date_str": self.current_date.strftime("%Y-%m-%d (%A)"), # For new agent
            "bells": self.bells,
            "nook_miles": self.nook_miles,
            "avg_friendship": avg_friendship,
            "villagers_friendship": {v.name: v.friendship_level for v in self.villagers}, # For agent to see individual levels
            "player_inventory": player_inv_for_state, # Crucial for SELL_ITEMS
            "turnips_owned": self.turnips_owned_by_island, # Assuming island owns turnips
            "turnip_buy_price": self.turnip_buy_price,
            "turnip_sell_price": self.turnip_sell_price,
            "active_nook_tasks": self.active_nook_tasks.copy(), # Return a copy
            "farm_plots": self.farm_plots.copy(), # Return a copy
            # Potentially add market saturation factors if agent needs to be aware of them directly
            "current_turnip_saturation": self.turnip_market_saturation_factor,
            # "current_fish_saturation": self.fish_market_saturation.copy(), # Could be large
            "fishing_attempts_today": self.fishing_attempts_today.copy(), # For debugging or UI feedback
            "current_catch_probability": self.current_catch_probability, # For debugging or UI feedback
            "max_total_villagers": self.MAX_TOTAL_VILLAGERS,
            "current_villager_count": len(self.villagers),
        }




# Example Usage (optional, for testing purposes):
# if __name__ == '__main__':
#     # Assuming your data CSVs are in a folder named 'data' at the same level as this script
#     # or provide the correct path to your data folder.
#     # For example: data_folder_path = os.path.join(os.path.dirname(__file__), '..', 'data')
#     data_folder_path = "d:\\Codes\\enigma-engines\\data" # Or your actual path

#     print(f"Attempting to load data from: {os.path.abspath(data_folder_path)}")

#     dataset = ACNHItemDataset(data_path=data_folder_path)

#     print("\\n--- Loaded Villager Names ---")
#     if dataset.villager_names:
#         print(f"Found {len(dataset.villager_names)} villagers. First 5: {dataset.villager_names[:5]}")
#         print(f"Random villager: {dataset.get_random_villager_name()}")
#     else:
#         print("No villager names loaded.")

#     print("\\n--- Loaded Gift Options ---")
#     if dataset.gift_options:
#         print(f"Found {len(dataset.gift_options)} gift options.")
#         random_gift_name, random_gift_details = dataset.get_random_gift_option()
#         print(f"Random gift: {random_gift_name} -> {random_gift_details}")
#         # Check a specific gift if needed, e.g.
#         # print(f"Details for 'Pear': {dataset.get_gift_details('Pear')}")
#         # print(f"Details for 'Sea Bass': {dataset.get_gift_details('Sea Bass')}")
#     else:
#         print("No gift options loaded.")

#     print("\\n--- Loaded Nook Miles Tasks ---")
#     if dataset.nook_miles_tasks_daily:
#         print(f"Found {len(dataset.nook_miles_tasks_daily)} Nook Miles tasks.")
#         print(f"Daily tasks sample: {dataset.get_daily_nook_miles_tasks(count=3)}")
#     else:
#         print("No Nook Miles tasks loaded.")

#     print("\\n--- Environment Test ---")
#     env = ACNHEnvironment(num_villagers=3, data_path=data_folder_path)
#     print(f"Initial state: {env.get_state()}")
#     # Example action
#     if env.villagers and dataset.gift_options:
#         random_villager_for_gift = env.villagers[0].name
#         random_gift_name_for_action, _ = dataset.get_random_gift_option()

#         action = {"type": "GIVE_GIFT", "villager_name": random_villager_for_gift, "gift_name": random_gift_name_for_action}
#         print(f"Performing action: {action}")
#         reward = env.step(action, None) # agent_state not used in this simple step
#         print(f"Reward from action: {reward}")
#         print(f"State after action: {env.get_state()}")
#     else:
#         print("Skipping environment action test due to missing villagers or gift options.")
