from typing import Any, Dict, List, Optional, Union
import pandas as pd
import random
import datetime
import csv
import os

# --- 1. ACNH Item Dataset with CSV Loading ---
class ACNHItemDataset:
    """
    Loads and accesses ACNH item, villager, fish, and other data from CSV files.
    """
    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.villager_names = self._load_villager_names()
        self.gift_options = self._load_item_data_for_gifts() # Consolidated item loading
        self.nook_miles_tasks_daily = self._load_nook_miles_tasks()
        self.fish = self._load_fish_data() # Added fish data

        if not self.villager_names:
            print(f"Warning: Villager names could not be loaded. Using fallback data.")
            self.villager_names = ["Audie", "Raymond", "Marshal"] # Fallback
        if not self.gift_options:
            print(f"Warning: Gift options could not be loaded. Using fallback data.")
            self.gift_options = {"Wrapped Fruit": {"cost": 100, "friendship_points": 3, "sell_price": 100}} # Fallback
        if not self.nook_miles_tasks_daily:
            print(f"Warning: Nook Miles tasks could not be loaded. Using fallback data.")
            self.nook_miles_tasks_daily = {"Catch 5 Bugs": 150} # Fallback
        if not self.fish:
            print(f"Warning: Fish data could not be loaded. Using fallback data.")
            self.fish = [{"Name": "Sea Bass", "Sell": 400, "Shadow": "Large", "Location": "Sea"}] # Fallback

    def _load_csv_data(self, filename: str, required_columns: Optional[List[str]] = None) -> Union[List[Any], List[Dict[str, Any]]]:
        """
        Reads a CSV file and returns data as a list of values or a list of dictionaries,
        based on the number of columns specified in `required_columns`.
        """
        file_path = os.path.join(self.data_path, filename)
        try:
            df = pd.read_csv(file_path, dtype=str, keep_default_na=True, na_values=['N/A', 'NA', ''])
        except FileNotFoundError:
            raise
        except pd.errors.EmptyDataError:
            if required_columns is None or not required_columns:
                return []
            else:
                raise ValueError(
                    f"CSV file '{filename}' is empty and has no headers. "
                    f"Cannot extract columns: {', '.join(required_columns)}"
                )
        except Exception as e:
            raise ValueError(f"Error reading or parsing CSV file '{filename}': {e}")

        if df.empty and required_columns and not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(
                    f"The following required columns are missing from the CSV '{filename}': {', '.join(missing_cols)}"
                )

        if required_columns is None:
            # Convert to dicts, ensuring NaNs become None for all columns
            return df.astype(object).where(pd.notnull(df), None).to_dict(orient='records')

        if not isinstance(required_columns, list):
            raise TypeError(
                f"required_columns must be a list or None, but got {type(required_columns).__name__}"
            )

        if not required_columns:
            return []

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"The following required columns are missing from the CSV '{filename}': {', '.join(missing_cols)}"
            )

        if len(required_columns) == 1:
            column_name = required_columns[0]
            return df[column_name].astype(object).where(pd.notnull(df[column_name]), None).tolist()
        else:
            return df[required_columns].astype(object).where(pd.notnull(df[required_columns]), None).to_dict(orient='records')


    def _load_villager_names(self):
        """Loads villager names from villagers.csv."""
        try:
            villagers_data = self._load_csv_data("villagers.csv", required_columns=['Name'])
            return [name for name in villagers_data if name is not None]
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: Could not load villager names from villagers.csv: {e}")
            return []

    def _load_item_data_for_gifts(self):
        """Loads item data from various CSVs to be used as gift options."""
        gift_options = {}
        item_files_info = {
            "fossils.csv": ("Name", "Sell"), "housewares.csv": ("Name", "Sell"),
            "miscellaneous.csv": ("Name", "Sell"), "accessories.csv": ("Name", "Sell"),
            "tools.csv": ("Name", "Sell"), "bugs.csv": ("Name", "Sell"), # Added bugs
            "fish.csv": ("Name", "Sell"), # Added fish for gifting
            # Add other item CSVs here: "art.csv", "clothing.csv", etc.
        }
        default_friendship_points = 3 # Default points for generic items

        for filename, (name_col, price_col) in item_files_info.items():
            try:
                items_data = self._load_csv_data(filename, required_columns=[name_col, price_col])
                for item in items_data:
                    item_name = item.get(name_col)
                    sell_price_str = item.get(price_col)
                    
                    sell_price = 0
                    if sell_price_str is not None:
                        try:
                            # Attempt to convert to float first for cases like "123.0", then to int
                            sell_price = int(float(sell_price_str))
                        except ValueError:
                            # If conversion fails, it might be non-numeric (e.g. from a different column accidentally)
                            # print(f"Warning: Could not parse sell price '{sell_price_str}' for item '{item_name}' in {filename}. Using 0.")
                            pass 

                    if item_name: # Ensure item_name is not None or empty
                        gift_options[item_name] = {
                            "cost": sell_price, # Cost to acquire (assume it's same as sell price for non-craftables)
                            "friendship_points": default_friendship_points,
                            "sell_price": sell_price # Price player gets when selling
                        }
            except (FileNotFoundError, ValueError) as e:
                print(f"Warning: Could not load items from {filename} for gifts: {e}")
            except Exception as e:
                print(f"Unexpected error processing {filename} for gift options: {e}")
        
        # Add special/manual gift options
        gift_options.update({
            "Wrapped Fruit": {"cost": 250, "friendship_points": 3, "sell_price": 250}, # Cost might be wrapping paper + fruit
            "Non-Native Fruit Basket": {"cost": 1500, "friendship_points": 4, "sell_price": 1500},
            # Could add more specific high-value gifts here
        })
        return gift_options

    def _load_nook_miles_tasks(self):
        tasks = {}
        try:
            achievements_data = self._load_csv_data("achievements.csv")
            
            tier_miles_cols_templates = ["Tier {} Nook Miles", "Tier{} Internal Nook Miles"]
            max_tiers_to_check = 5

            for achievement in achievements_data:
                task_name = achievement.get("Name")
                if not task_name:
                    continue

                num_tiers_str = str(achievement.get("Num of Tiers", "1"))
                num_tiers = 1
                if num_tiers_str.isdigit():
                    num_tiers = int(num_tiers_str)
                
                for tier_num in range(1, num_tiers + 1):
                    miles_val = None
                    for template in tier_miles_cols_templates:
                        col_name = template.format(tier_num)
                        if achievement.get(col_name) is not None and str(achievement[col_name]).isdigit():
                            miles_val = int(achievement[col_name])
                            break 
                    if miles_val is not None and miles_val > 0:
                        unique_task_name = f"{task_name} (Tier {tier_num})" if num_tiers > 1 else task_name
                        tasks[unique_task_name] = miles_val
                
                if not any(f"{task_name} (Tier" in t for t in tasks) and task_name not in tasks:
                     general_miles_cols = ["Nook Miles", "Total Nook Miles"]
                     for col in general_miles_cols:
                         if achievement.get(col) is not None and str(achievement[col]).isdigit():
                             miles_val = int(achievement[col])
                             if miles_val > 0:
                                 tasks[task_name] = miles_val
                                 break
                                 
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: Could not load Nook Miles tasks from achievements.csv: {e}")
        except Exception as e:
            print(f"Unexpected error processing achievements.csv for Nook Miles tasks: {e}")

        return {name: miles for name, miles in tasks.items() if miles > 0}

    def _load_fish_data(self):
        """Loads fish data from fish.csv."""
        try:
            # Load all columns for fish, as details like shadow, location might be useful
            fish_data = self._load_csv_data("fish.csv") 
            # Basic validation: ensure 'Name' and 'Sell' columns are present and usable
            valid_fish = []
            for fish_item in fish_data:
                name = fish_item.get("Name")
                sell_price_str = fish_item.get("Sell")
                if name and sell_price_str is not None:
                    try:
                        # Ensure sell price is a number
                        fish_item["Sell"] = int(float(sell_price_str)) 
                        valid_fish.append(fish_item)
                    except ValueError:
                        print(f"Warning: Could not parse sell price for fish '{name}'. Skipping.")
                # else:
                    # print(f"Warning: Fish item missing Name or Sell price. Data: {fish_item}")
            return valid_fish
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: Could not load fish data from fish.csv: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error loading fish.csv: {e}")
            return []

    def get_random_villager_name(self):
        if not self.villager_names:
            return "Unknown Villager"
        return random.choice(self.villager_names)

    def get_gift_details(self, gift_name):
        return self.gift_options.get(gift_name)

    def get_random_gift_option(self):
        if not self.gift_options:
            return "Generic Gift", {"cost": 10, "friendship_points": 1, "sell_price": 10}
        name = random.choice(list(self.gift_options.keys()))
        return name, self.gift_options[name]

    def get_daily_nook_miles_tasks(self, count=10):
        if not self.nook_miles_tasks_daily:
            return {}
        
        available_tasks = list(self.nook_miles_tasks_daily.items())
        num_to_sample = min(count, len(available_tasks))
        if num_to_sample == 0:
            return {}
            
        tasks = random.sample(available_tasks, k=num_to_sample)
        return dict(tasks)

    def get_random_fish(self) -> Optional[Dict[str, Any]]:
        """Returns a random fish from the loaded fish data."""
        if not self.fish:
            return None
        return random.choice(self.fish)

    def get_fish_details(self, fish_name: str) -> Optional[Dict[str, Any]]:
        """Returns details for a specific fish by name."""
        if not self.fish:
            return None
        for fish_item in self.fish:
            if fish_item.get("Name") == fish_name:
                return fish_item
        return None


# --- 2. Simplified ACNH Villager Class ---
class ACNHVillager:
    def __init__(self, name):
        self.name = name
        self.friendship_level = 25
        self.last_gifted_day = -1
        self.inventory = {} # Could store items like fish

    def receive_gift(self, gift_details, current_day):
        if self.last_gifted_day == current_day:
            return 0 # Already gifted today
        
        points = gift_details.get("friendship_points", 0)
        self.friendship_level = min(255, self.friendship_level + points)
        self.last_gifted_day = current_day
        return points
    
    def add_to_inventory(self, item_name, quantity=1):
        self.inventory[item_name] = self.inventory.get(item_name, 0) + quantity

    def remove_from_inventory(self, item_name, quantity=1):
        if item_name in self.inventory and self.inventory[item_name] >= quantity:
            self.inventory[item_name] -= quantity
            if self.inventory[item_name] == 0:
                del self.inventory[item_name]
            return True
        return False

    def __str__(self):
        return f"{self.name} (Friendship: {self.friendship_level}, Inv: {self.inventory})"


# --- 3. Simplified ACNH Environment Class ---
class ACNHEnvironment:
    def __init__(self, num_villagers=5, dataset=None, data_path="d:\\\\Codes\\\\enigma-engines\\\\data",
                 population_increase_daily_chance=0.02,
                 min_population_increase_percentage=0.05,
                 max_population_increase_percentage=0.15):
        
        self.dataset = dataset if dataset else ACNHItemDataset(data_path=data_path)
        self._initial_num_villagers = num_villagers
        
        self.current_day = 0
        self.current_date = datetime.date(2024, 1, 1)
        
        self.villagers: List[ACNHVillager] = []
        if self.dataset.villager_names:
            self._populate_initial_villagers(self._initial_num_villagers)
        else:
            print("Warning: No villager names in dataset. Environment starting with 0 villagers.")

        self.bells = 1000
        self.nook_miles = 500
        
        # Turnip market state
        self.turnips_owned_by_island = 0 # Total turnips held by player/island, not individual villagers yet
        self.turnip_buy_price = 0       # Daisy Mae's price
        self.turnip_sell_price = 0      # Nook's Cranny price
        self.turnips_sold_today_volume = 0 # Volume of turnips sold by agents today
        self.turnip_market_saturation_factor = 1.0 # Affects sell price based on volume

        self.daily_nook_tasks = {}

        self.population_increase_daily_chance = population_increase_daily_chance
        self.min_population_increase_percentage = min_population_increase_percentage
        self.max_population_increase_percentage = max_population_increase_percentage
        
        self.fish_market_saturation = {} # Tracks saturation per fish type {fish_name: factor}
        self.reset() 

    def _populate_initial_villagers(self, num_to_populate):
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
        
        if len(self.villagers) < self._initial_num_villagers and num_to_populate == self._initial_num_villagers:
             needed_more = self._initial_num_villagers - len(self.villagers)
             current_villager_names = {v.name for v in self.villagers}
             potential_new_names = [name for name in self.dataset.villager_names if name not in current_villager_names]
             num_can_add_extra = min(needed_more, len(potential_new_names))
             if num_can_add_extra > 0:
                 names_to_add_extra = random.sample(potential_new_names, num_can_add_extra)
                 for name in names_to_add_extra:
                      self.villagers.append(ACNHVillager(name))


    def _try_increase_population(self):
        if not self.dataset.villager_names:
            return

        max_possible_total_villagers = len(self.dataset.villager_names)
        current_villager_count = len(self.villagers)

        if current_villager_count >= max_possible_total_villagers:
            return

        increase_percentage = random.uniform(self.min_population_increase_percentage, self.max_population_increase_percentage)
        base_for_increase = current_villager_count if current_villager_count > 0 else 1
        num_new_villagers_float = base_for_increase * increase_percentage
        num_new_villagers = max(1, int(round(num_new_villagers_float)))

        actual_can_add = max_possible_total_villagers - current_villager_count
        num_to_add = min(num_new_villagers, actual_can_add)

        if num_to_add > 0:
            current_names = {v.name for v in self.villagers}
            available_new_names = [name for name in self.dataset.villager_names if name not in current_names]
            
            if len(available_new_names) < num_to_add:
                num_to_add = len(available_new_names)

            if num_to_add > 0:
                names_to_add = random.sample(available_new_names, num_to_add)
                for name in names_to_add:
                    self.villagers.append(ACNHVillager(name))
                print(f"INFO: Population increased by {num_to_add} villagers to {len(self.villagers)} on day {self.current_day}.")


    def reset(self):
        self.current_day = 0
        self.current_date = datetime.date(2024, 1, 1)
        
        target_population_size = len(self.villagers) if self.villagers else self._initial_num_villagers
        
        self.villagers = []
        if self.dataset.villager_names:
            num_to_sample = min(target_population_size, len(self.dataset.villager_names))
            if num_to_sample > 0:
                sampled_names = random.sample(self.dataset.villager_names, num_to_sample)
                self.villagers = [ACNHVillager(name) for name in sampled_names]
        
        if len(self.villagers) < self._initial_num_villagers and self.dataset.villager_names:
            needed = self._initial_num_villagers - len(self.villagers)
            self._populate_initial_villagers(needed)

        self.bells = 1000
        self.nook_miles = 500
        self.turnips_owned_by_island = 0
        self.turnips_sold_today_volume = 0
        self.turnip_market_saturation_factor = 1.0 
        self.fish_market_saturation = {}

        self.update_turnip_prices() # Initialize prices
        self.assign_daily_nook_tasks()


    def update_turnip_prices(self):
        """Updates turnip buy and sell prices, considering market saturation."""
        day_of_week = self.current_date.weekday()

        # Decay saturation factor slightly each day (market recovers)
        self.turnip_market_saturation_factor = max(0.2, self.turnip_market_saturation_factor * 0.95) # Recovers by 5%, min factor 0.2

        if day_of_week == 6:  # Sunday: Daisy Mae sells
            self.turnip_buy_price = random.randint(90, 110)
            self.turnip_sell_price = 0  # Nook's not buying on Sunday
        else:  # Monday to Saturday: Nook's Cranny buys
            self.turnip_buy_price = 0 # Not buying from Daisy Mae
            
            # Base price fluctuation
            if random.random() < 0.05: # Small chance of very high price
                base_sell_price = random.randint(300, 600)
            elif random.random() < 0.25: # Moderate chance of good price
                base_sell_price = random.randint(150, 299)
            elif random.random() < 0.60: # Common prices
                base_sell_price = random.randint(80, 149)
            else: # Lower prices
                base_sell_price = random.randint(40, 79)
            
            # Apply saturation factor: more sales -> lower price
            self.turnip_sell_price = int(base_sell_price * self.turnip_market_saturation_factor)
            self.turnip_sell_price = max(10, self.turnip_sell_price) # Ensure price doesn't drop too low

        # Reset daily sales volume at the beginning of a new day for Nook's prices
        if day_of_week != 6: # For Mon-Sat
            self.turnips_sold_today_volume = 0

    def update_fish_market_saturation(self, fish_name, quantity_sold):
        """Updates the saturation factor for a given fish."""
        current_factor = self.fish_market_saturation.get(fish_name, 1.0)
        # Increase saturation (decrease factor) based on quantity sold.
        # This is a simple model, could be more complex.
        # Max reduction per sale action, to avoid single large sale crashing market.
        impact = quantity_sold * 0.02 # e.g., selling 10 fish makes it 20% more saturated
        new_factor = max(0.1, current_factor - impact) # Minimum 10% of original price
        self.fish_market_saturation[fish_name] = new_factor
        # print(f"Debug: Fish {fish_name} saturation updated to {new_factor} due to {quantity_sold} sold.")


    def assign_daily_nook_tasks(self):
        self.daily_nook_tasks = self.dataset.get_daily_nook_miles_tasks()

    def step(self, action, agent_state): # agent_state might be relevant for villager specific actions
        # `agent_state` could be the villager object itself or its name/ID
        # For now, let's assume action can contain 'villager_name' if relevant
        
        delta_friendship_total = 0
        delta_bells = 0
        delta_nook_miles = 0
        action_type = action.get("type")
        acting_villager_name = action.get("villager_name") # Used for actions tied to a villager
        
        acting_villager = None
        if acting_villager_name:
            acting_villager = next((v for v in self.villagers if v.name == acting_villager_name), None)

        if action_type == "GIVE_GIFT":
            villager_name_target = action.get("target_villager_name", acting_villager_name) # Gift to self? Or another?
            gift_name = action.get("gift_name")
            
            target_villager = next((v for v in self.villagers if v.name == villager_name_target), None)
            gift_details = self.dataset.get_gift_details(gift_name)

            if target_villager and gift_details:
                cost_of_gift = gift_details.get("cost", 0)
                # Assuming island bells are used for gifts for now
                if self.bells >= cost_of_gift or cost_of_gift == 0: # Allow free gifts
                    if target_villager.last_gifted_day != self.current_day:
                        if cost_of_gift > 0:
                             self.bells -= cost_of_gift
                             delta_bells -= cost_of_gift
                        friendship_gain = target_villager.receive_gift(gift_details, self.current_day)
                        delta_friendship_total += friendship_gain
        
        elif action_type == "WORK_FOR_BELLS":
            earnings = random.randint(500, 2000)
            self.bells += earnings
            delta_bells += earnings
        
        elif action_type == "DO_NOOK_MILES_TASK":
            task_name = action.get("task_name")
            if task_name in self.daily_nook_tasks:
                miles_reward = self.daily_nook_tasks.pop(task_name)
                self.nook_miles += miles_reward
                delta_nook_miles += miles_reward
        
        elif action_type == "BUY_TURNIPS": # Player/Island buys turnips
            if self.current_date.weekday() == 6 and self.turnip_buy_price > 0: # Sunday
                quantity_to_buy = action.get("quantity", 0)
                cost = quantity_to_buy * self.turnip_buy_price
                if self.bells >= cost and quantity_to_buy > 0:
                    self.bells -= cost
                    delta_bells -= cost
                    self.turnips_owned_by_island += quantity_to_buy
        
        elif action_type == "SELL_TURNIPS": # Player/Island sells turnips
            if self.current_date.weekday() != 6 and self.turnip_sell_price > 0 and self.turnips_owned_by_island > 0:
                quantity_to_sell = action.get("quantity", self.turnips_owned_by_island) # Sell all if not specified
                quantity_to_sell = min(quantity_to_sell, self.turnips_owned_by_island)

                if quantity_to_sell > 0:
                    earnings = quantity_to_sell * self.turnip_sell_price
                    self.bells += earnings
                    delta_bells += earnings
                    self.turnips_owned_by_island -= quantity_to_sell
                    
                    self.turnips_sold_today_volume += quantity_to_sell
                    # Update saturation factor based on volume - more sales, price goes down more next time
                    # This is a simple model: a fixed impact per 100 turnips.
                    self.turnip_market_saturation_factor = max(0.1, self.turnip_market_saturation_factor - (quantity_to_sell / 100) * 0.05)
        
        elif action_type == "GO_FISHING":
            if acting_villager and self.dataset.fish: # Villager specific action
                # Basic fishing logic: random chance to catch a fish
                if random.random() < 0.7: # 70% chance to catch something
                    caught_fish = self.dataset.get_random_fish()
                    if caught_fish:
                        acting_villager.add_to_inventory(caught_fish["Name"], 1)
                        # print(f"Debug: {acting_villager.name} caught a {caught_fish['Name']}!")
                        # Reward could be intrinsic (enjoyment) or delayed (sell later)
                        # For now, no direct bells/miles, just item in inventory
                # else:
                    # print(f"Debug: {acting_villager.name} fished but caught nothing.")

        elif action_type == "SELL_FISH":
            if acting_villager: # Villager specific action
                fish_name_to_sell = action.get("fish_name")
                quantity_to_sell = action.get("quantity", 1) # Default to selling 1

                if fish_name_to_sell and acting_villager.inventory.get(fish_name_to_sell, 0) >= quantity_to_sell:
                    fish_details = self.dataset.get_fish_details(fish_name_to_sell)
                    if fish_details:
                        base_sell_price = fish_details.get("Sell", 0)
                        current_saturation_factor = self.fish_market_saturation.get(fish_name_to_sell, 1.0)
                        actual_sell_price = int(base_sell_price * current_saturation_factor)
                        
                        earnings = quantity_to_sell * actual_sell_price
                        
                        if acting_villager.remove_from_inventory(fish_name_to_sell, quantity_to_sell):
                            self.bells += earnings # Island gets the bells for now
                            delta_bells += earnings
                            # print(f"Debug: {acting_villager.name} sold {quantity_to_sell} {fish_name_to_sell} for {earnings} bells (price: {actual_sell_price}, sat: {current_saturation_factor:.2f}).")
                            self.update_fish_market_saturation(fish_name_to_sell, quantity_to_sell)
                        # else:
                            # print(f"Debug: Failed to remove {fish_name_to_sell} from {acting_villager.name}'s inventory.")
                    # else:
                        # print(f"Debug: Could not find details for fish {fish_name_to_sell} to sell.")
                # else:
                    # print(f"Debug: {acting_villager.name} does not have {quantity_to_sell} of {fish_name_to_sell} to sell.")

        elif action_type == "IDLE":
            pass # No change from idling

        # --- Daily Updates ---
        is_new_day = False
        if self.current_day != action.get("simulation_day_count", self.current_day): # If external loop manages day
             is_new_day = True
        
        # If step implies a new day by itself (internal day counter)
        # For now, assume step advances the day for the environment
        # This part needs to be clear: does step() advance the day OR is it called multiple times per day?
        # Assuming step() is called for *each action*, and a day might have multiple actions.
        # So, day advancement should be a separate call or triggered at the end of a "round" of actions.

        # Let's assume for now `advance_day()` is called separately.
        # The current `self.current_day += 1` in the original code is problematic if step is per action.
        # I will move day advancement to a separate method `advance_day_cycle`.

        avg_friendship_delta = delta_friendship_total / len(self.villagers) if self.villagers and delta_friendship_total != 0 else 0
        return (avg_friendship_delta, delta_bells, delta_nook_miles)

    def advance_day_cycle(self):
        """Advances the simulation by one day, performing daily updates."""
        self.current_day += 1
        self.current_date += datetime.timedelta(days=1)
        
        # Update turnip prices for the new day (also resets daily volume and applies decay)
        self.update_turnip_prices() 
        
        # Assign new Nook Miles tasks
        self.assign_daily_nook_tasks()

        # Attempt population increase
        if random.random() < self.population_increase_daily_chance:
            self._try_increase_population()

        # Daily decay for fish market saturation (market recovers over time)
        for fish_name in list(self.fish_market_saturation.keys()):
            self.fish_market_saturation[fish_name] = min(1.0, self.fish_market_saturation[fish_name] * 1.05) # Recovers by 5%
            if self.fish_market_saturation[fish_name] > 0.98: # If almost fully recovered, remove from tracking
                del self.fish_market_saturation[fish_name]
        # print(f"Debug: Day {self.current_day} advanced. Date: {self.current_date}")


    def get_state(self):
        avg_friendship = sum(v.friendship_level for v in self.villagers) / len(self.villagers) if self.villagers else 0
        villager_details = []
        for v in self.villagers:
            villager_details.append({
                "name": v.name,
                "friendship": v.friendship_level,
                "inventory": dict(v.inventory) # Make a copy
            })

        return {
            "day": self.current_day,
            "date_str": self.current_date.strftime("%Y-%m-%d (%A)"),
            "bells": self.bells,
            "nook_miles": self.nook_miles,
            "avg_friendship": avg_friendship,
            # "villagers_friendship": {v.name: v.friendship_level for v in self.villagers},
            "villagers": villager_details, # More detailed villager info
            "current_population": len(self.villagers),
            "turnips_owned_by_island": self.turnips_owned_by_island,
            "turnip_buy_price": self.turnip_buy_price,
            "turnip_sell_price": self.turnip_sell_price,
            "turnip_market_saturation_factor": round(self.turnip_market_saturation_factor, 3),
            "fish_market_saturation": {k: round(v, 3) for k,v in self.fish_market_saturation.items()},
            "available_nook_tasks": list(self.daily_nook_tasks.keys())
        }


# Example Usage (optional, for testing purposes):
if __name__ == '__main__':
    data_folder_path = "d:\\Codes\\enigma-engines\\data" 
    print(f"Attempting to load data from: {os.path.abspath(data_folder_path)}")

    dataset = ACNHItemDataset(data_path=data_folder_path)

    print("\n--- Loaded Villager Names ---")
    if dataset.villager_names:
        print(f"Found {len(dataset.villager_names)} villagers. First 5: {dataset.villager_names[:5]}")
    else:
        print("No villager names loaded.")

    print("\n--- Loaded Gift Options ---")
    if dataset.gift_options:
        print(f"Found {len(dataset.gift_options)} gift options.")
        # print(f"Random gift: {dataset.get_random_gift_option()}")
    else:
        print("No gift options loaded.")

    print("\n--- Loaded Fish Data ---")
    if dataset.fish:
        print(f"Found {len(dataset.fish)} fish types. First 2: {dataset.fish[:2]}")
        random_fish = dataset.get_random_fish()
        if random_fish:
            print(f"Random fish: {random_fish['Name']}, Sells for: {random_fish['Sell']}")
            print(f"Details for 'Sea Bass': {dataset.get_fish_details('Sea Bass')}")
        else:
            print("Could not get a random fish (fish list might be empty).")
    else:
        print("No fish data loaded.")
    
    print("\n--- Environment Test ---")
    env = ACNHEnvironment(num_villagers=2, data_path=data_folder_path)
    print(f"Initial state (Day {env.current_day}): {env.get_state()}")

    # Simulate a few days with actions
    for i in range(3): # Simulate 3 days
        print(f"\n--- Simulating Day {env.current_day} ---")
        # Example actions for the day
        if env.villagers:
            villager1 = env.villagers[0]
            
            # Action: Villager 1 tries to fish
            action_fish = {"type": "GO_FISHING", "villager_name": villager1.name}
            print(f"Action: {villager1.name} is fishing.")
            env.step(action_fish, None) # Agent state not strictly needed for this simplified setup
            print(f"State after fishing: Bells: {env.bells}, {villager1.name} Inv: {villager1.inventory}")

            # Action: Villager 1 tries to sell a fish if they caught one
            if "Sea Bass" in villager1.inventory: # Example fish
                 action_sell_fish = {"type": "SELL_FISH", "villager_name": villager1.name, "fish_name": "Sea Bass", "quantity": 1}
                 print(f"Action: {villager1.name} is selling Sea Bass.")
                 env.step(action_sell_fish, None)
                 print(f"State after selling fish: Bells: {env.bells}, {villager1.name} Inv: {villager1.inventory}")
            elif villager1.inventory: # Sell any other fish
                first_fish_in_inv = list(villager1.inventory.keys())[0]
                action_sell_fish = {"type": "SELL_FISH", "villager_name": villager1.name, "fish_name": first_fish_in_inv, "quantity": villager1.inventory[first_fish_in_inv]}
                print(f"Action: {villager1.name} is selling {villager1.inventory[first_fish_in_inv]} {first_fish_in_inv}(s).")
                env.step(action_sell_fish, None)
                print(f"State after selling fish: Bells: {env.bells}, {villager1.name} Inv: {villager1.inventory}")


            # Action: Buy turnips on Sunday
            if env.current_date.weekday() == 6 and env.turnip_buy_price > 0:
                action_buy_turnips = {"type": "BUY_TURNIPS", "quantity": 50} # Buy 50 turnips
                print(f"Action: Buying 50 turnips at {env.turnip_buy_price} each.")
                env.step(action_buy_turnips, None)
                print(f"State after buying turnips: Bells: {env.bells}, Turnips owned: {env.turnips_owned_by_island}")

            # Action: Sell turnips if it's not Sunday and player has some
            if env.current_date.weekday() != 6 and env.turnips_owned_by_island > 0 and env.turnip_sell_price > 0:
                action_sell_turnips = {"type": "SELL_TURNIPS", "quantity": env.turnips_owned_by_island // 2} # Sell half
                if action_sell_turnips["quantity"] > 0 :
                    print(f"Action: Selling {action_sell_turnips['quantity']} turnips at {env.turnip_sell_price} each.")
                    env.step(action_sell_turnips, None)
                    print(f"State after selling turnips: Bells: {env.bells}, Turnips owned: {env.turnips_owned_by_island}")
        
        env.advance_day_cycle() # Advance to the next day
        print(f"End of Day {env.current_day-1} state: {env.get_state()}")

    print(f"\nFinal state after simulation (Day {env.current_day}): {env.get_state()}")


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
