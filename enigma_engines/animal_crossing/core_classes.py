from typing import Any, Dict, List, Optional, Union
import pandas as pd
import random
import datetime
import csv
import os

from enigma_engines.animal_crossing.data_simulation import generate_crops_dataset

# --- 1. ACNH Item Dataset with CSV Loading ---
class ACNHItemDataset:
    """
    Loads and accesses ACNH item, villager, fish, crop, and other data from CSV files.
    """
    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.villager_names = self._load_villager_names()
        self.gift_options = self._load_item_data_for_gifts() # Consolidated item loading
        self.nook_miles_task_templates = self._load_nook_miles_tasks() # Achievement/task templates
        self.fish_data = self._load_fish_data()
        self.crop_definitions = self._load_crop_data()

        if not self.villager_names:
            print(f"Warning: Villager names could not be loaded. Using fallback data.")
            self.villager_names = ["Audie", "Raymond", "Marshal"] # Fallback
        if not self.gift_options:
            print(f"Warning: Gift options could not be loaded. Using fallback data.")
            self.gift_options = {"Wrapped Fruit": {"cost": 100, "friendship_points": 3, "sell_price": 100}} # Fallback
        if not self.nook_miles_task_templates:
            print(f"Warning: Nook Miles tasks could not be loaded. Using fallback data.")
            # Fallback with criteria example
            self.nook_miles_task_templates = {
                "Catch 5 Bugs": {
                    "miles": 150,
                    "criteria": {"type": "catch_category", "category": "Bug", "quantity": 5},
                    "duration_days": 1
                }
            }
        if not self.fish_data:
            print(f"Warning: Fish data could not be loaded. Using fallback data.")
            self.fish_data = [{"Name": "Sea Bass", "Sell": 400, "Shadow": "Large", "Location": "Sea"}] # Fallback
        if not self.crop_definitions:
            print(f"Warning: Crop definitions could not be loaded. Using fallback data.")
            self.crop_definitions = {"Tomato": {"Name": "Tomato", "GrowthTimeDays": 4, "SellPrice": 35, "SeedCost": 20, "Yield": 3}}


    def _load_csv_data(self, filename: str, required_columns: Optional[List[str]] = None) -> Union[List[Any], List[Dict[str, Any]]]:
        """
        Reads a CSV file and returns data as a list of values or a list of dictionaries,
        based on the number of columns specified in `required_columns`.
        Handles potential NaN values by converting them to None.
        """
        file_path = os.path.join(self.data_path, filename)
        try:
            # Read CSV, explicitly keep empty strings as is initially, then handle NaNs
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False, na_values=[''])
            # Replace pandas' NaT or other null types with None after conversion
            df = df.where(pd.notnull(df), None)
        except FileNotFoundError:
            print(f"Warning: CSV file '{filename}' not found at '{file_path}'.")
            return [] # Return empty list if file not found
        except pd.errors.EmptyDataError:
            print(f"Warning: CSV file '{filename}' is empty.")
            return []
        except Exception as e:
            print(f"Error reading or parsing CSV file '{filename}': {e}")
            return []

        if df.empty and required_columns:
            # Check if all required columns are at least present, even if df is empty
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"Warning: Required columns {missing_cols} missing in empty CSV '{filename}'.")
                return [] # Cannot proceed if required columns for structure are missing

        # If no specific columns are required, return all data as list of dicts
        if required_columns is None:
            return df.to_dict(orient='records')

        if not isinstance(required_columns, list):
            raise TypeError(
                f"required_columns must be a list or None, but got {type(required_columns).__name__}"
            )

        if not required_columns: # If list is empty, effectively no columns selected
            return []

        # Check for missing columns from the required list
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(f"Warning: The following required columns are missing from '{filename}': {', '.join(missing_cols)}")
            # Decide if partial data is acceptable or return empty
            # For robust loading, try to load with available columns if some are optional
            # However, if these are strictly required, this is an issue.
            # For now, we'll continue with available columns, Pandas will handle missing ones with NaN/None.
            # Filter df to only include existing required columns to avoid KeyError
            existing_required_cols = [col for col in required_columns if col in df.columns]
            if not existing_required_cols:
                return [] # No required columns exist at all
            df_subset = df[existing_required_cols]
        else:
            df_subset = df[required_columns]


        if len(required_columns) == 1:
            # Single column requested, return as a list of its values
            # Ensure NaNs become None
            return df_subset[required_columns[0]].tolist()
        else:
            # Multiple columns, return list of dicts for these columns
            return df_subset.to_dict(orient='records')


    def _load_villager_names(self):
        """Loads villager names from villagers.csv."""
        try:
            # Expects a 'Name' column
            villagers_data = self._load_csv_data("villagers.csv", required_columns=['Name'])
            return [name for name in villagers_data if name is not None]
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: Could not load villager names from villagers.csv: {e}")
            return []

    def _load_item_data_for_gifts(self):
        """Loads item data from various CSVs to be used as gift options and for selling."""
        gift_options = {}
        # Define files and relevant columns (name, sell_price)
        # Sell price is crucial for the SELL_ITEMS action too.
        item_files_info = {
            "fossils.csv": ("Name", "Sell"), "housewares.csv": ("Name", "Sell"),
            "miscellaneous.csv": ("Name", "Sell"), "accessories.csv": ("Name", "Sell"),
            "tools.csv": ("Name", "Sell"), "insects.csv": ("Name", "Sell"), # Changed from "bugs.csv"
            "fish.csv": ("Name", "Sell"),
            "art.csv": ("Name", "Sell"), "bottoms.csv": ("Name", "Sell"),
            "dress-up.csv": ("Name", "Sell"), "headwear.csv": ("Name", "Sell"),
            "photos.csv": ("Name", "Sell"), "posters.csv": ("Name", "Sell"),
            "rugs.csv": ("Name", "Sell"), "shoes.csv": ("Name", "Sell"),
            "socks.csv": ("Name", "Sell"), "tops.csv": ("Name", "Sell"),
            "umbrellas.csv": ("Name", "Sell"), "wall-mounted.csv": ("Name", "Sell"),
            "wallpaper.csv": ("Name", "Sell"), "floors.csv": ("Name", "Sell"),
            # If crops are sellable through general store, they'd need to be here or handled separately.
            # For now, crop sell prices are in their own definitions.
        }
        default_friendship_points = 3

        for filename, (name_col, price_col) in item_files_info.items():
            try:
                items_data = self._load_csv_data(filename, required_columns=[name_col, price_col])
                for item in items_data:
                    item_name = item.get(name_col)
                    sell_price_str = item.get(price_col)
                    
                    sell_price = 0
                    if sell_price_str is not None:
                        try:
                            sell_price = int(float(sell_price_str))
                        except ValueError:
                            # print(f"Warning: Could not parse sell price '{sell_price_str}' for item '{item_name}' in {filename}. Using 0.")
                            pass 

                    if item_name:
                        gift_options[item_name] = {
                            "cost": sell_price, # For gifting, cost might be different. For selling, this is sell_price.
                            "friendship_points": default_friendship_points, # Generic friendship
                            "sell_price": sell_price,
                            "category": filename.split('.')[0] # e.g., "fossils", "housewares"
                        }
            except Exception as e:
                print(f"Warning: Could not load items from {filename}: {e}")
        
        gift_options.update({
            "Wrapped Fruit": {"cost": 250, "friendship_points": 3, "sell_price": 250, "category": "special_gift"},
            "Non-Native Fruit Basket": {"cost": 1500, "friendship_points": 4, "sell_price": 1500, "category": "special_gift"},
        })
        return gift_options

    
    def _load_nook_miles_tasks(self):
        """Loads Nook Miles task templates from achievements.csv, including criteria."""
        tasks = {}
        try:
            # Assuming self._load_csv_data is part of the same class
            # and correctly returns a list of dictionaries (each dict is a row)
            achievements_data = self._load_csv_data("achievements.csv")
            if not achievements_data:
                print("Warning: achievements.csv is empty or could not be loaded. No Nook Miles tasks will be available.")
                return {}

            for achievement in achievements_data:
                base_task_name = achievement.get("Internal Name")
                if not base_task_name:
                    print(f"Skipping achievement due to missing 'Internal Name': {achievement.get('Name')}")
                    continue

                internal_category = achievement.get("Internal Category")
                award_criteria_text = achievement.get("Award Criteria", "") # Full text description

                num_tiers_str = str(achievement.get("Num of Tiers", "1")).strip()
                num_tiers = 1
                if num_tiers_str.isdigit() and int(num_tiers_str) > 0:
                    num_tiers = int(num_tiers_str)
                elif num_tiers_str: # Non-empty but not a positive digit
                    print(f"Warning: Invalid 'Num of Tiers' ('{num_tiers_str}') for {base_task_name}. Defaulting to 1 tier.")


                for tier_num in range(1, num_tiers + 1):
                    miles_val = None
                    # Corrected column name for Nook Miles rewards
                    reward_col_name = f"Reward Tier {tier_num}"
                    val_str = achievement.get(reward_col_name)

                    if val_str is not None and val_str.strip().isdigit():
                        miles_val = int(val_str.strip())
                        if miles_val <= 0: # Ignore non-positive miles values
                            miles_val = None
                    
                    if miles_val is None:
                        # If no miles for this specific tier, or miles are 0, skip this tier for this achievement
                        # print(f"Debug: No valid miles found for {base_task_name} Tier {tier_num} in column {reward_col_name}. Value: '{val_str}'")
                        continue

                    task_name_to_use = f"{base_task_name} (Tier {tier_num})" if num_tiers > 1 else base_task_name
                    
                    criteria = {
                        "description": award_criteria_text, # General description
                        "category": internal_category,
                        "quantity": None, # Will be filled from "Tier X" column
                        # "type" and "item_name" are harder to generically derive from this CSV per tier
                        # and might need specific logic per Internal Category if required.
                    }

                    # Corrected column name for criteria quantity
                    quantity_col_name = f"Tier {tier_num}"
                    quantity_str = achievement.get(quantity_col_name)
                    if quantity_str and quantity_str.strip().isdigit():
                        criteria["quantity"] = int(quantity_str.strip())
                    elif quantity_str and quantity_str.strip(): # If quantity is not a number but present (e.g. for event type)
                         # For some tasks (like the first sample "ImmigratetoIsland"), Tier 1 = 1 might mean 'completed once'.
                         # If it's just an event flag, an explicit quantity might not always be numeric in the same sense.
                         # For simplicity, we'll try to parse as int, otherwise leave as None or handle based on category.
                         # Here, we'll assume if it's not a digit, it's not a countable quantity for now.
                         pass


                    # Duration is not in the sample CSV, defaulting to 1 as in original code.
                    # If you add a "Duration Days Tier X" or similar column, you can parse it here.
                    duration_days = 1 

                    tasks[task_name_to_use] = {
                        "public_name": achievement.get("Name", base_task_name), # User-friendly name
                        "miles": miles_val,
                        "criteria": criteria,
                        "duration_days": duration_days,
                        "internal_id": achievement.get("Internal ID"),
                        "sequential": achievement.get("Sequential", "No").lower() == "yes"
                    }
            
        except Exception as e:
            print(f"Unexpected error processing achievements.csv for Nook Miles tasks: {e}")
            import traceback
            print(traceback.format_exc()) # Helpful for debugging during development
        
        # Final filter: ensure all returned tasks have positive miles (already handled by miles_val <= 0 check)
        return tasks



    def _load_fish_data(self):
        """Loads fish data from fish.csv."""
        try:
            fish_data_raw = self._load_csv_data("fish.csv") # Load all columns
            valid_fish = []
            if not fish_data_raw: return []

            for fish_item in fish_data_raw:
                name = fish_item.get("Name")
                sell_price_str = fish_item.get("Sell")
                if name and sell_price_str is not None:
                    try:
                        fish_item["Sell"] = int(float(sell_price_str)) 
                        valid_fish.append(fish_item)
                    except ValueError:
                        print(f"Warning: Could not parse sell price for fish '{name}'. Skipping.")
            return valid_fish
        except Exception as e:
            print(f"Unexpected error loading fish.csv: {e}")
            return []

    def _load_crop_data(self):
        """Loads crop definitions from crops.csv."""
        crop_defs = {}
        # Expected columns: Name, GrowthTimeDays, SellPrice, SeedCost, Yield
        try:
            crop_data_raw = self._load_csv_data("crops.csv", 
                                             required_columns=["Name", "GrowthTimeDays", "SellPrice", "SeedCost", "Yield"])
            if not crop_data_raw: 
                generate_crops_dataset()
                crop_data_raw = self._load_csv_data("crops.csv", 
                                             required_columns=["Name", "GrowthTimeDays", "SellPrice", "SeedCost", "Yield"])

            for crop_item in crop_data_raw:
                name = crop_item.get("Name")
                if not name:
                    continue
                try:
                    crop_defs[name] = {
                        "Name": name,
                        "GrowthTimeDays": int(crop_item.get("GrowthTimeDays", 0)),
                        "SellPrice": int(crop_item.get("SellPrice", 0)),
                        "SeedCost": int(crop_item.get("SeedCost", 0)),
                        "Yield": int(crop_item.get("Yield", 1))
                    }
                except ValueError as ve:
                    print(f"Warning: Could not parse data for crop '{name}'. Skipping. Error: {ve}")
            return crop_defs
        except Exception as e:
            print(f"Unexpected error loading crops.csv: {e}")
            return {}


    def get_random_villager_name(self):
        if not self.villager_names: return "Unknown Villager"
        return random.choice(self.villager_names)

    def get_gift_details(self, gift_name): # Also used for item sell price
        details = self.gift_options.get(gift_name)
        if not details and gift_name in self.crop_definitions: # Check if it's a crop
            crop_def = self.crop_definitions[gift_name]
            return {
                "cost": crop_def["SeedCost"], # Or perhaps its sell price if thinking of buying the crop itself
                "friendship_points": 2, # Generic for crops
                "sell_price": crop_def["SellPrice"],
                "category": "crop"
            }
        return details


    def get_random_gift_option(self):
        if not self.gift_options: return "Generic Gift", {"cost": 10, "friendship_points": 1, "sell_price": 10, "category":"unknown"}
        name = random.choice(list(self.gift_options.keys()))
        return name, self.gift_options[name]

    def get_daily_nook_miles_task_templates(self, count=5): # Renamed for clarity
        if not self.nook_miles_task_templates: return {}
        
        available_tasks = list(self.nook_miles_task_templates.items())
        num_to_sample = min(count, len(available_tasks))
        if num_to_sample == 0: return {}
            
        sampled_task_kv_pairs = random.sample(available_tasks, k=num_to_sample)
        return dict(sampled_task_kv_pairs)

    def get_random_fish(self) -> Optional[Dict[str, Any]]:
        if not self.fish_data: return None
        return random.choice(self.fish_data)

    def get_fish_details(self, fish_name: str) -> Optional[Dict[str, Any]]:
        if not self.fish_data: return None
        for fish_item in self.fish_data:
            if fish_item.get("Name") == fish_name:
                return fish_item
        return None

    def get_crop_definition(self, crop_name: str) -> Optional[Dict[str, Any]]:
        return self.crop_definitions.get(crop_name)


# --- 2. Simplified ACNH Villager Class ---\r
class ACNHVillager:
    def __init__(self, name):
        self.name = name
        self.friendship_level = 25
        self.last_gifted_day = -1
        self.inventory: Dict[str, int] = {} # item_name: quantity
        self.daily_activity_log: Dict[str, Any] = {"sold_items": []} # For tracking criteria

    def receive_gift(self, gift_details, current_day):
        if self.last_gifted_day == current_day:
            return 0 
        
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

    def log_sale(self, item_name: str, quantity: int, value: int, category: Optional[str]):
        self.daily_activity_log.setdefault("sold_items", []).append(
            {"name": item_name, "quantity": quantity, "value": value, "category": category}
        )
    
    def reset_daily_log(self):
        self.daily_activity_log = {"sold_items": []}


    def __str__(self):
        return f"{self.name} (Friendship: {self.friendship_level}, Inv: {self.inventory})"


# --- 3. Simplified ACNH Environment Class ---\r
class ACNHEnvironment:
    def __init__(self, num_villagers=3, dataset=None, data_path="data", # Corrected default data_path
                 max_plots=10): # Added max_plots for farming
        
        self.dataset = dataset if dataset else ACNHItemDataset(data_path=data_path)
        self._initial_num_villagers = num_villagers
        
        self.current_day = 0
        self.current_date = datetime.date(2024, 1, 1)
        
        self.villagers: List[ACNHVillager] = []
        if self.dataset.villager_names:
            self._populate_initial_villagers(self._initial_num_villagers)

        self.bells = 1000
        self.nook_miles = 500
        
        self.turnips_owned_by_island = 0
        self.turnip_buy_price = 0    
        self.turnip_sell_price = 0  
        self.turnips_sold_today_volume = 0 
        self.turnip_market_saturation_factor = 1.0 

        self.active_nook_tasks: Dict[str, Dict] = {} # task_name: task_details from dataset

        # Crop Farming System
        self.max_farm_plots = max_plots
        self.farm_plots: Dict[int, Dict] = {
            # plot_id: {"crop_name": None, "plant_day": -1, "ready_day": -1, "owner_villager": None}
        } 
        for i in range(max_plots): # Initialize empty plots
            self.farm_plots[i] = {"crop_name": None, "plant_day": -1, "ready_day": -1, "owner_villager": None}


        self.fish_market_saturation = {} 
        self.reset() 

    def _populate_initial_villagers(self, num_to_populate):
        # (Simplified from original, focusing on core functionality)
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


    def reset(self): # Simplified reset
        self.current_day = 0
        self.current_date = datetime.date(2024, 1, 1)
        
        self.villagers = []
        if self.dataset.villager_names:
            self._populate_initial_villagers(self._initial_num_villagers)
        
        for v in self.villagers: v.reset_daily_log()

        self.bells = 1000
        self.nook_miles = 500
        self.turnips_owned_by_island = 0
        self.turnips_sold_today_volume = 0
        self.turnip_market_saturation_factor = 1.0 
        self.fish_market_saturation = {}
        self.farm_plots = {i: {"crop_name": None, "plant_day": -1, "ready_day": -1, "owner_villager": None} for i in range(self.max_farm_plots)}


        self.update_turnip_prices()
        self.assign_daily_nook_tasks()


    def update_turnip_prices(self):
        # (Same as original, ensure it's called appropriately)
        day_of_week = self.current_date.weekday()
        self.turnip_market_saturation_factor = max(0.2, self.turnip_market_saturation_factor * 0.95)
        if day_of_week == 6:  # Sunday
            self.turnip_buy_price = random.randint(90, 110)
            self.turnip_sell_price = 0 
        else:  # Mon-Sat
            self.turnip_buy_price = 0
            base_sell_price = random.randint(40, 600) # Simplified pricing
            self.turnip_sell_price = int(base_sell_price * self.turnip_market_saturation_factor)
            self.turnip_sell_price = max(10, self.turnip_sell_price)
        if day_of_week != 6: self.turnips_sold_today_volume = 0


    def update_fish_market_saturation(self, fish_name, quantity_sold):
        # (Same as original)
        current_factor = self.fish_market_saturation.get(fish_name, 1.0)
        impact = quantity_sold * 0.02 
        new_factor = max(0.1, current_factor - impact) 
        self.fish_market_saturation[fish_name] = new_factor


    def assign_daily_nook_tasks(self, count=5):
        # Gets task *templates* from dataset and makes them active for the day
        self.active_nook_tasks = self.dataset.get_daily_nook_miles_task_templates(count=count)
        # Reset progress for agents if tasks were to carry progress (not implemented yet)


    def _check_task_criteria(self, agent: 'ACNHVillager', task_name: str) -> bool:
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
        c_quantity = criteria.get("quantity", 1)  # Default to 1 if quantity not specified
        c_category = criteria.get("category")

        if c_type == "collect_item":  # Check current inventory
            return agent.inventory.get(c_item_name, 0) >= c_quantity
        
        elif c_type == "sell_item_category":  # Check daily log for sales of this category
            sold_amount = 0
            for sale_event in agent.daily_activity_log.get("sold_items", []):
                if sale_event.get("category") == c_category:
                    sold_amount += sale_event.get("quantity", 0)
            return sold_amount >= c_quantity
        
        elif c_type == "catch_specific_fish":  # Requires logging fish catches
            # Current implementation (from snippet) checks inventory.
            # For consistency with other activity-based tasks, this could be changed
            # to check agent.daily_activity_log.get("caught_fish", [])
            # if fish catching is logged there.
            # e.g.,
            # caught_fish_count = 0
            # for fish_event in agent.daily_activity_log.get("caught_fish", []):
            #     if fish_event.get("name") == c_item_name:
            #         caught_fish_count += fish_event.get("quantity", 0) # Assuming "quantity" per catch event
            # return caught_fish_count >= c_quantity
            return agent.inventory.get(c_item_name, 0) >= c_quantity

        elif c_type == "earn_bells_selling":  # Check daily log for total bells earned from sales
            total_earned_from_sales = sum(s.get("value", 0) for s in agent.daily_activity_log.get("sold_items", []))
            return total_earned_from_sales >= c_quantity  # Here c_quantity is the bell amount

        elif c_type == "plant_crop":
            # Assumes agent.daily_activity_log["planted_crops"] is a list of dicts:
            # e.g., [{"crop_name": "Pumpkin", "quantity": 1}, ...]
            # c_item_name (optional): specific crop to plant.
            # c_quantity: number of crops to plant.
            planted_count = 0
            for plant_event in agent.daily_activity_log.get("planted_crops", []):
                if c_item_name:  # Specific crop name provided in task criteria
                    if plant_event.get("crop_name") == c_item_name:
                        planted_count += plant_event.get("quantity", 0)
                else:  # Any crop
                    planted_count += plant_event.get("quantity", 0)
            return planted_count >= c_quantity

        elif c_type == "talk_to_villagers":
            # Assumes agent.daily_activity_log["talked_to_villagers"] is a list of villager names:
            # e.g., ["Tom Nook", "Isabelle", "Tom Nook"]
            # c_item_name (optional): specific villager to talk to.
            # c_quantity: 
            #   - if c_item_name is set: number of times to talk to that specific villager.
            #   - if c_item_name is None: number of unique villagers to talk to.
            interactions = agent.daily_activity_log.get("talked_to_villagers", [])
            if c_item_name:  # Task is to talk to a specific villager
                count_specific_villager = interactions.count(c_item_name)
                return count_specific_villager >= c_quantity
            else:  # Task is to talk to a number of unique villagers
                unique_villagers_talked_to = set(interactions)
                return len(unique_villagers_talked_to) >= c_quantity
        
        elif c_type == "spend_bells":
            # Assumes agent.daily_activity_log["spent_bells_events"] is a list of dicts:
            # e.g., [{"amount": 100, "reason": "seeds"}, {"amount": 500, "reason": "item"}]
            # c_quantity: total amount of bells to be spent.
            total_spent = 0
            for spend_event in agent.daily_activity_log.get("spent_bells_events", []):
                total_spent += spend_event.get("amount", 0)
            return total_spent >= c_quantity
            
        # Fallback for unrecognized c_type.
        # Consider logging a warning if a c_type is not recognized.
        # print(f"Warning: Unrecognized task criteria type '{c_type}' for task '{task_name}'.")
        return False


    def step(self, action: Dict, agent_state: Optional[ACNHVillager] = None): # agent_state is the acting villager
        delta_friendship_total = 0
        delta_bells = 0 # For island/player
        delta_nook_miles = 0 # For island/player

        # --- Resolve acting villager ---
        # The 'agent_state' parameter is intended to be the ACNHVillager instance performing the action.
        # If it's not an ACNHVillager instance (e.g., if the full environment state, a name, or None was passed),
        # we try to find the villager by name using action.get("villager_name").
        
        _resolved_acting_villager: Optional[ACNHVillager] = None
        if isinstance(agent_state, ACNHVillager):
            _resolved_acting_villager = agent_state
        else: # agent_state is None, or not an ACNHVillager instance (e.g. the env state dict)
            if "villager_name" in action: # Check if action dict specifies the acting villager's name
                actor_name = action.get("villager_name")
                if actor_name: # Ensure actor_name is not None or empty
                    _resolved_acting_villager = next((v for v in self.villagers if v.name == actor_name), None)
        
        acting_villager = _resolved_acting_villager
        # --- End of acting villager resolution ---

        action_type = action.get("type")
        
        # Some actions don't require a specific villager (e.g. island-wide or system actions)
        # If an action requires a villager but none was resolved, return no change.
        actions_not_requiring_villager = ["ADVANCE_DAY", "WORK_FOR_BELLS_ISLAND", "BUY_TURNIPS", "SELL_TURNIPS"]
        if not acting_villager and action_type not in actions_not_requiring_villager:
            # print(f"Warning: Action '{action_type}' requires an acting_villager but none was found or provided.")
            return (0,0,0) # No change if action cannot be performed

        # --- VILLAGER SPECIFIC ACTIONS ---
        if acting_villager:
            if action_type == "GIVE_GIFT":
                target_villager_name = action.get("target_villager_name")
                gift_name = action.get("gift_name")
                target_villager = next((v for v in self.villagers if v.name == target_villager_name), None)
                gift_details = self.dataset.get_gift_details(gift_name)

                if target_villager and gift_details:
                    cost_of_gift = gift_details.get("cost", 0)
                    # Assume villager pays from their own (non-existent) bells, or island pays
                    if self.bells >= cost_of_gift: # Island pays for now
                        if acting_villager.remove_from_inventory(gift_name, 1) or gift_name == "Wrapped Fruit": # Special case or owned item
                            self.bells -= cost_of_gift
                            delta_bells -= cost_of_gift
                            friendship_gain = target_villager.receive_gift(gift_details, self.current_day)
                            delta_friendship_total += friendship_gain
            
            elif action_type == "DO_NOOK_MILES_TASK":
                task_name = action.get("task_name")
                if task_name in self.active_nook_tasks:
                    if self._check_task_criteria(acting_villager, task_name):
                        task_info = self.active_nook_tasks.pop(task_name) # Task is completed and removed for this day
                        self.nook_miles += task_info["miles"]
                        delta_nook_miles += task_info["miles"]
                        # print(f"INFO: {acting_villager.name} completed task '{task_name}' for {task_info['miles']} miles.")
                    # else:
                        # print(f"INFO: {acting_villager.name} attempted task '{task_name}' but criteria not met.")
            
            elif action_type == "SELL_ITEMS": # Replaces generic work for bells for villagers
                items_to_sell = action.get("items_to_sell", []) # List of {"name": str, "quantity": int}
                total_earnings_for_villager = 0
                for item_sale in items_to_sell:
                    item_name = item_sale.get("name")
                    quantity = item_sale.get("quantity", 0)
                    if not item_name or quantity <= 0: continue

                    item_details = self.dataset.get_gift_details(item_name) # Use this to get sell_price and category
                    if item_details and acting_villager.inventory.get(item_name, 0) >= quantity:
                        sell_price_per_unit = item_details.get("sell_price", 0)
                        category = item_details.get("category", "unknown")

                        # Apply fish market saturation if it's a fish
                        if category == "fish":
                           saturation_factor = self.fish_market_saturation.get(item_name, 1.0)
                           sell_price_per_unit = int(sell_price_per_unit * saturation_factor)
                           self.update_fish_market_saturation(item_name, quantity)


                        earnings_for_item = quantity * sell_price_per_unit
                        if acting_villager.remove_from_inventory(item_name, quantity):
                            self.bells += earnings_for_item # Island gets bells
                            delta_bells += earnings_for_item
                            total_earnings_for_villager += earnings_for_item
                            acting_villager.log_sale(item_name, quantity, earnings_for_item, category)
                # print(f"INFO: {acting_villager.name} sold items for {total_earnings_for_villager} bells.")

            elif action_type == "PLANT_CROP":
                crop_name = action.get("crop_name")
                plot_id = action.get("plot_id")
                crop_def = self.dataset.get_crop_definition(crop_name)

                if crop_def and plot_id is not None and plot_id in self.farm_plots and self.farm_plots[plot_id]["crop_name"] is None:
                    if self.bells >= crop_def["SeedCost"]: # Island pays for seeds
                        self.bells -= crop_def["SeedCost"]
                        delta_bells -= crop_def["SeedCost"]
                        self.farm_plots[plot_id] = {
                            "crop_name": crop_name,
                            "plant_day": self.current_day,
                            "ready_day": self.current_day + crop_def["GrowthTimeDays"],
                            "owner_villager": acting_villager.name # Track who planted
                        }
                        # print(f"INFO: {acting_villager.name} planted {crop_name} in plot {plot_id}.")
                    # else: print(f"INFO: Not enough bells to plant {crop_name}.")
                # else: print(f"INFO: Cannot plant {crop_name} in plot {plot_id}. Plot busy or crop unknown.")


            elif action_type == "HARVEST_CROP":
                plot_id = action.get("plot_id")
                if plot_id is not None and plot_id in self.farm_plots:
                    plot_info = self.farm_plots[plot_id]
                    if plot_info["crop_name"] and plot_info.get("owner_villager") == acting_villager.name: # Ensure harvester is owner
                        if self.current_day >= plot_info["ready_day"]:
                            crop_def = self.dataset.get_crop_definition(plot_info["crop_name"])
                            if crop_def:
                                acting_villager.add_to_inventory(plot_info["crop_name"], crop_def["Yield"])
                                # print(f"INFO: {acting_villager.name} harvested {crop_def['Yield']} {plot_info['crop_name']} from plot {plot_id}.")
                                # Reset plot for now (no regrowth in this version)
                                self.farm_plots[plot_id] = {"crop_name": None, "plant_day": -1, "ready_day": -1, "owner_villager": None}
                        # else: print(f"INFO: Crop in plot {plot_id} not ready for harvest.")
                    # else: print(f"INFO: Plot {plot_id} not harvestable by {acting_villager.name}.")


            elif action_type == "GO_FISHING": # Basic fishing
                if self.dataset.fish_data:
                    if random.random() < 0.7: 
                        caught_fish = self.dataset.get_random_fish()
                        if caught_fish:
                            acting_villager.add_to_inventory(caught_fish["Name"], 1)
                            # Log catch for potential criteria:
                            # acting_villager.daily_activity_log.setdefault("caught_fish", []).append({"name": caught_fish["Name"]})
                            # print(f"Debug: {acting_villager.name} caught a {caught_fish['Name']}!")

        # --- ISLAND WIDE ACTIONS / NO SPECIFIC VILLAGER ---
        elif action_type == "WORK_FOR_BELLS_ISLAND": # Generic island income
            earnings = random.randint(100, 500) # Less than specific sales
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
            if self.current_date.weekday() != 6 and self.turnip_sell_price > 0 and self.turnips_owned_by_island > 0:
                quantity_to_sell = action.get("quantity", self.turnips_owned_by_island)
                quantity_to_sell = min(quantity_to_sell, self.turnips_owned_by_island)
                if quantity_to_sell > 0:
                    earnings = quantity_to_sell * self.turnip_sell_price
                    self.bells += earnings
                    delta_bells += earnings
                    self.turnips_owned_by_island -= quantity_to_sell
                    self.turnips_sold_today_volume += quantity_to_sell
                    self.turnip_market_saturation_factor = max(0.1, self.turnip_market_saturation_factor - (quantity_to_sell / 100) * 0.05)
        
        elif action_type == "ADVANCE_DAY": # Special action to advance the day
            self.advance_day_cycle()
            # Deltas for advance_day are typically 0 unless it triggers passive income/loss
            # which is handled within advance_day_cycle if needed.

        avg_friendship_delta = delta_friendship_total / len(self.villagers) if self.villagers and delta_friendship_total != 0 else 0
        return (avg_friendship_delta, delta_bells, delta_nook_miles)


    def advance_day_cycle(self):
        self.current_day += 1
        self.current_date += datetime.timedelta(days=1)
        
        # Reset daily things for villagers
        for villager in self.villagers:
            villager.reset_daily_log()

        self.update_turnip_prices()
        self.assign_daily_nook_tasks() # Get new set of tasks for the new day
        
        # Fish market saturation recovers slightly
        for fish_name in list(self.fish_market_saturation.keys()):
            self.fish_market_saturation[fish_name] = min(1.0, self.fish_market_saturation[fish_name] * 1.1) # Recovers 10% towards 1.0
            if self.fish_market_saturation[fish_name] > 0.95: # Remove if close to normal
                del self.fish_market_saturation[fish_name]

        # Potentially population dynamics, crop growth updates (if passive) etc. would go here.
        # For current crop model, growth is checked at harvest time based on plant_day and current_day.
        # print(f"--- Advancing to Day {self.current_day} ({self.current_date.strftime('%Y-%m-%d %A')}) ---")


    def get_state(self):
        """Returns a dictionary representing the current state of the environment."""
        avg_friendship = sum(v.friendship_level for v in self.villagers) / len(self.villagers) if self.villagers else 0
        villager_states = []
        for v in self.villagers:
            villager_states.append({
                "name": v.name,
                "friendship": v.friendship_level,
                "inventory": v.inventory.copy(),
                "last_gifted_day": v.last_gifted_day
            })
        
        active_tasks_summary = {}
        for name, details in self.active_nook_tasks.items():
            active_tasks_summary[name] = {"miles": details["miles"], "criteria": details.get("criteria", "None")}

        farm_plots_summary = {}
        for plot_id, plot_data in self.farm_plots.items():
            if plot_data["crop_name"]:
                farm_plots_summary[plot_id] = {
                    "crop": plot_data["crop_name"],
                    "planted": plot_data["plant_day"],
                    "ready": plot_data["ready_day"],
                    "owner": plot_data["owner_villager"]
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
