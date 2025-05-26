from typing import Dict, List, Optional
import random
import datetime

from enigma_engines.animal_crossing.core.load_data import ACNHItemDataset
from enigma_engines.animal_crossing.core.villager import ACNHVillager


class ACNHEnvironment:
    def __init__(
        self,
        num_villagers=3,
        dataset=None,
        data_path="data",  # Corrected default data_path
        max_plots=10,
    ):  # Added max_plots for farming

        self.dataset = dataset if dataset else ACNHItemDataset(data_path=data_path)
        self._initial_num_villagers = num_villagers

        self.current_day = 0
        self.current_date = datetime.date(2025, 4, 6)

        self.villagers: List[ACNHVillager] = []
        if self.dataset.villager_names:
            self._populate_initial_villagers(self._initial_num_villagers)

        self.bells = 10
        self.nook_miles = 5

        self.turnips_owned_by_island = 0
        self.turnip_buy_price = 0
        self.turnip_sell_price = 0
        self.turnips_sold_today_volume = 0
        self.turnip_market_saturation_factor = 1.0

        self.active_nook_tasks: Dict[str, Dict] = (
            {}
        )  # task_name: task_details from dataset

        # Crop Farming System
        self.max_farm_plots = max_plots
        self.farm_plots: Dict[int, Dict] = {
            # plot_id: {"crop_name": None, "plant_day": -1, "ready_day": -1, "owner_villager": None}
        }
        for i in range(max_plots):  # Initialize empty plots
            self.farm_plots[i] = {
                "crop_name": None,
                "plant_day": -1,
                "ready_day": -1,
                "owner_villager": None,
            }

        self.fish_market_saturation = {}
        self.reset()

    def _populate_initial_villagers(self, num_to_populate):
        if not self.dataset.villager_names:
            self.villagers = []
            return

        current_villager_names = {v.name for v in self.villagers}
        potential_new_names = [
            name
            for name in self.dataset.villager_names
            if name not in current_villager_names
        ]

        num_can_add = min(num_to_populate, len(potential_new_names))

        if num_can_add > 0:
            names_to_add = random.sample(potential_new_names, num_can_add)
            for name in names_to_add:
                self.villagers.append(ACNHVillager(name))

    def reset(self):  # Simplified reset
        self.current_day = 0
        self.current_date = datetime.date(2025, 4, 6)

        self.villagers = []
        if self.dataset.villager_names:
            self._populate_initial_villagers(self._initial_num_villagers)

        for v in self.villagers:
            v.reset_daily_log()

        self.bells = 10
        self.nook_miles = 5
        self.turnips_owned_by_island = 0
        self.turnips_sold_today_volume = 0
        self.turnip_market_saturation_factor = 1.0
        self.fish_market_saturation = {}
        self.farm_plots = {
            i: {
                "crop_name": None,
                "plant_day": -1,
                "ready_day": -1,
                "owner_villager": None,
            }
            for i in range(self.max_farm_plots)
        }

        self.update_turnip_prices()
        self.assign_daily_nook_tasks()

    def update_turnip_prices(self):
        # (Same as original, ensure it's called appropriately)
        day_of_week = self.current_date.weekday()
        self.turnip_market_saturation_factor = max(
            0.2, self.turnip_market_saturation_factor * 0.95
        )
        if day_of_week == 6:  # Sunday
            self.turnip_buy_price = random.randint(90, 110)
            self.turnip_sell_price = 0
        else:  # Mon-Sat
            self.turnip_buy_price = 0
            base_sell_price = random.randint(40, 600)  # Simplified pricing
            self.turnip_sell_price = int(
                base_sell_price * self.turnip_market_saturation_factor
            )
            self.turnip_sell_price = max(10, self.turnip_sell_price)
        if day_of_week != 6:
            self.turnips_sold_today_volume = 0

    def update_fish_market_saturation(self, fish_name, quantity_sold):
        # (Same as original)
        current_factor = self.fish_market_saturation.get(fish_name, 1.0)
        impact = quantity_sold * 0.02
        new_factor = max(0.1, current_factor - impact)
        self.fish_market_saturation[fish_name] = new_factor

    def assign_daily_nook_tasks(self, count=5):
        # Gets task *templates* from dataset and makes them active for the day
        self.active_nook_tasks = self.dataset.get_daily_nook_miles_task_templates(
            count=count
        )
        # Reset progress for agents if tasks were to carry progress (not implemented yet)

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

    def step(
        self, action: Dict, agent_state: Optional[ACNHVillager] = None
    ):  # agent_state is the acting villager
        delta_friendship_total = 0
        delta_bells = 0  # For island/player
        delta_nook_miles = 0  # For island/player

        _resolved_acting_villager: Optional[ACNHVillager] = None
        if isinstance(agent_state, ACNHVillager):
            _resolved_acting_villager = agent_state
        else:
            if "villager_name" in action:
                actor_name = action.get("villager_name")
                if actor_name:
                    _resolved_acting_villager = next(
                        (v for v in self.villagers if v.name == actor_name), None
                    )
        acting_villager = _resolved_acting_villager
        action_type = action.get("type")

        actions_not_requiring_villager = [
            "ADVANCE_DAY",
            "WORK_FOR_BELLS_ISLAND",
            "BUY_TURNIPS",
            "SELL_TURNIPS",
        ]
        if not acting_villager and action_type not in actions_not_requiring_villager:
            return (0, 0, 0)
        possible_actions = [
            "GIVE_GIFT",
            "RECEIVE_GIFT",
            "DO_NOOK_MILES_TASK",
            "SELL_ITEMS",
            "PLANT_CROP",
            "HARVEST_CROP",
            "GO_FISHING",
            "WORK_FOR_BELLS_ISLAND",
            "BUY_TURNIPS",
            "SELL_TURNIPS",
            "ADVANCE_DAY",
        ]
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

                
            if action_type == "GIVE_GIFT":
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
            
            elif action_type == "DO_NOOK_MILES_TASK":
                task_name = action.get("task_name")
                if task_name in self.active_nook_tasks:
                    if self._check_task_criteria(acting_villager, task_name):
                        task_info = self.active_nook_tasks.pop(task_name)
                        self.nook_miles += task_info["miles"]
                        delta_nook_miles += task_info["miles"]

            elif action_type == "SELL_ITEMS":
                items_to_sell = action.get("items_to_sell", [])
                total_earnings_for_villager = 0
                for item_sale in items_to_sell:
                    item_name = item_sale.get("name")
                    quantity = item_sale.get("quantity", 0)
                    if not item_name or quantity <= 0:
                        continue

                    item_details = self.dataset.get_gift_details(item_name)
                    if (
                        item_details
                        and acting_villager.inventory.get(item_name, 0) >= quantity
                    ):
                        sell_price_per_unit = item_details.get("sell_price", 0)
                        category = item_details.get("category", "unknown")

                        if category == "fish":
                            saturation_factor = self.fish_market_saturation.get(
                                item_name, 1.0
                            )
                            sell_price_per_unit = int(
                                sell_price_per_unit * saturation_factor
                            )
                            self.update_fish_market_saturation(item_name, quantity)

                        earnings_for_item = quantity * sell_price_per_unit
                        if acting_villager.remove_from_inventory(item_name, quantity):
                            self.bells += earnings_for_item
                            delta_bells += earnings_for_item
                            total_earnings_for_villager += earnings_for_item
                            acting_villager.log_sale(
                                item_name, quantity, earnings_for_item, category
                            )
            elif action_type == "PLANT_CROP":
                crop_name = action.get("crop_name")
                plot_id = action.get("plot_id")
                crop_def = self.dataset.get_crop_definition(crop_name)

                if (
                    crop_def
                    and plot_id is not None
                    and plot_id in self.farm_plots
                    and self.farm_plots[plot_id]["crop_name"] is None
                ):
                    if self.bells >= crop_def["SeedCost"]:
                        self.bells -= crop_def["SeedCost"]
                        delta_bells -= crop_def["SeedCost"]
                        self.farm_plots[plot_id] = {
                            "crop_name": crop_name,
                            "plant_day": self.current_day,
                            "ready_day": self.current_day + crop_def["GrowthTimeDays"],
                            "owner_villager": acting_villager.name,
                        }
            elif action_type == "HARVEST_CROP":
                plot_id = action.get("plot_id")
                if plot_id is not None and plot_id in self.farm_plots:
                    plot_info = self.farm_plots[plot_id]
                    if (
                        plot_info["crop_name"]
                        and plot_info.get("owner_villager") == acting_villager.name
                    ):
                        if self.current_day >= plot_info["ready_day"]:
                            crop_def = self.dataset.get_crop_definition(
                                plot_info["crop_name"]
                            )
                            if crop_def:
                                acting_villager.add_to_inventory(
                                    plot_info["crop_name"], crop_def["Yield"]
                                )
                                self.farm_plots[plot_id] = {
                                    "crop_name": None,
                                    "plant_day": -1,
                                    "ready_day": -1,
                                    "owner_villager": None,
                                }
            elif action_type == "GO_FISHING":
                if self.dataset.fish_data:
                    if random.random() < 0.7:
                        caught_fish = self.dataset.get_random_fish()
                        if caught_fish:
                            acting_villager.add_to_inventory(caught_fish["Name"], 1)
            
        elif action_type == "WORK_FOR_BELLS_ISLAND":
            earnings = random.randint(100, 500)
            self.bells += earnings
            delta_bells += earnings

        elif action_type == "BUY_TURNIPS":
            if self.current_date.weekday() == 6 and self.turnip_buy_price > 0:
                quantity_to_buy = action.get("quantity", 0)
                cost = quantity_to_buy * self.turnip_buy_price
                if self.bells >= cost and quantity_to_buy > 0:
                    self.bells -= cost
                    delta_bells -= cost
                    self.turnips_owned_by_island += quantity_to_buy

        elif action_type == "SELL_TURNIPS":
            if (
                self.current_date.weekday() != 6
                and self.turnip_sell_price > 0
                and self.turnips_owned_by_island > 0
            ):
                quantity_to_sell = action.get("quantity", self.turnips_owned_by_island)
                quantity_to_sell = min(quantity_to_sell, self.turnips_owned_by_island)
                if quantity_to_sell > 0:
                    earnings = quantity_to_sell * self.turnip_sell_price
                    self.bells += earnings
                    delta_bells += earnings
                    self.turnips_owned_by_island -= quantity_to_sell
                    self.turnips_sold_today_volume += quantity_to_sell
                    self.turnip_market_saturation_factor = max(
                        0.1,
                        self.turnip_market_saturation_factor
                        - (quantity_to_sell / 100) * 0.05,
                    )
        elif action_type == "ADVANCE_DAY":
            self.advance_day_cycle()

        avg_friendship_delta = (
            delta_friendship_total / len(self.villagers)
            if self.villagers and delta_friendship_total != 0
            else 0
        )
        return (avg_friendship_delta, delta_bells, delta_nook_miles)

    def advance_day_cycle(self):
        self.current_day += 1
        self.current_date += datetime.timedelta(days=1)

        for villager in self.villagers:
            villager.reset_daily_log()

        self.update_turnip_prices()
        self.assign_daily_nook_tasks()

        for fish_name in list(self.fish_market_saturation.keys()):
            self.fish_market_saturation[fish_name] = min(
                1.0, self.fish_market_saturation[fish_name] * 1.1
            )
            if self.fish_market_saturation[fish_name] > 0.95:
                del self.fish_market_saturation[fish_name]

    def get_state(self):
        avg_friendship = (
            sum(v.friendship_level for v in self.villagers) / len(self.villagers)
            if self.villagers
            else 0
        )
        villager_states = []
        for v in self.villagers:
            villager_states.append(
                {
                    "name": v.name,
                    "friendship": v.friendship_level,
                    "inventory": v.inventory.copy(),
                    "last_gifted_day": v.last_gifted_day,
                }
            )

        active_tasks_summary = {}
        for name, details in self.active_nook_tasks.items():
            active_tasks_summary[name] = {
                "miles": details["miles"],
                "criteria": details.get("criteria", "None"),
            }
        farm_plots_summary = {}
        for plot_id, plot_data in self.farm_plots.items():
            if plot_data["crop_name"]:
                farm_plots_summary[plot_id] = {
                    "crop": plot_data["crop_name"],
                    "planted": plot_data["plant_day"],
                    "ready": plot_data["ready_day"],
                    "owner": plot_data["owner_villager"],
                }

        return {
            "current_day": self.current_day,
            "current_date": self.current_date.isoformat(),
            "bells": self.bells,
            "nook_miles": self.nook_miles,
            "villagers": villager_states,
            "turnips_owned": self.turnips_owned_by_island,
            "turnip_buy_price": self.turnip_buy_price,
            "turnip_sell_price": self.turnip_sell_price,
            "active_nook_tasks": active_tasks_summary,
            "farm_plots": farm_plots_summary,
            "fish_market_saturation": self.fish_market_saturation.copy(),
            "avg_friendship": avg_friendship,
            "turnips_sold_today": self.turnips_sold_today_volume,
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
