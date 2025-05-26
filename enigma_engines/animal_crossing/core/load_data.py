from typing import Any, Dict, List, Optional, Union
import pandas as pd
import random
import os

from enigma_engines.animal_crossing.core.data_simulation import generate_crops_dataset


class ACNHItemDataset:
    """
    Manages and provides access to Animal Crossing: New Horizons (ACNH) game data.

    This class loads various data types such as item details, villager names,
    fish information, crop definitions, and Nook Miles tasks from CSV files
    stored in a specified data path. It provides methods to retrieve random
    or specific pieces of this data. If data files are missing or corrupted,
    it falls back to default placeholder data and issues warnings.
    """

    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.villager_names = self._load_villager_names()
        self.gift_options = (
            self._load_item_data_for_gifts()
        )  # Consolidated item loading
        self.nook_miles_task_templates = (
            self._load_nook_miles_tasks()
        )  # Achievement/task templates
        self.fish_data = self._load_fish_data()
        self.crop_definitions = self._load_crop_data()

        if not self.villager_names:
            print("Warning: Villager names could not be loaded. Using fallback data.")
            self.villager_names = ["Audie", "Raymond", "Marshal"]  # Fallback
        if not self.gift_options:
            print("Warning: Gift options could not be loaded. Using fallback data.")
            self.gift_options = {
                "Wrapped Fruit": {
                    "cost": 100,
                    "friendship_points": 3,
                    "sell_price": 100,
                }
            }  # Fallback
        if not self.nook_miles_task_templates:
            print(
                "Warning: Nook Miles tasks could not be loaded. Using fallback data."
            )
            # Fallback with criteria example
            self.nook_miles_task_templates = {
                "Catch 5 Bugs": {
                    "miles": 150,
                    "criteria": {
                        "type": "catch_category",
                        "category": "Bug",
                        "quantity": 5,
                    },
                    "duration_days": 1,
                }
            }
        if not self.fish_data:
            print("Warning: Fish data could not be loaded. Using fallback data.")
            self.fish_data = [
                {"Name": "Sea Bass", "Sell": 400, "Shadow": "Large", "Location": "Sea"}
            ]  # Fallback
        if not self.crop_definitions:
            print(
                "Warning: Crop definitions could not be loaded. Using fallback data."
            )
            self.crop_definitions = {
                "Tomato": {
                    "Name": "Tomato",
                    "GrowthTimeDays": 4,
                    "SellPrice": 35,
                    "SeedCost": 20,
                    "Yield": 3,
                }
            }

    def _load_csv_data(
        self, filename: str, required_columns: Optional[List[str]] = None
    ) -> Union[List[Any], List[Dict[str, Any]]]:
        """
        Reads a CSV file and returns data as a list of values or a list of dictionaries,
        based on the number of columns specified in `required_columns`.
        Handles potential NaN values by converting them to None.
        """
        file_path = os.path.join(self.data_path, filename)
        try:
            # Read CSV, explicitly keep empty strings as is initially, then handle NaNs
            df = pd.read_csv(
                file_path, dtype=str, keep_default_na=False, na_values=[""]
            )
            # Replace pandas' NaT or other null types with None after conversion
            df = df.where(pd.notnull(df), None)
        except FileNotFoundError:
            print(f"Warning: CSV file '{filename}' not found at '{file_path}'.")
            return []  # Return empty list if file not found
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
                print(
                    f"Warning: Required columns {missing_cols} missing in empty CSV '{filename}'."
                )
                return (
                    []
                )  # Cannot proceed if required columns for structure are missing

        # If no specific columns are required, return all data as list of dicts
        if required_columns is None:
            return df.to_dict(orient="records")

        if not isinstance(required_columns, list):
            raise TypeError(
                f"required_columns must be a list or None, but got {type(required_columns).__name__}"
            )

        if not required_columns:  # If list is empty, effectively no columns selected
            return []

        # Check for missing columns from the required list
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(
                f"Warning: The following required columns are missing from '{filename}': {', '.join(missing_cols)}"
            )
            # Decide if partial data is acceptable or return empty
            # For robust loading, try to load with available columns if some are optional
            # However, if these are strictly required, this is an issue.
            # For now, we'll continue with available columns, Pandas will handle missing ones with NaN/None.
            # Filter df to only include existing required columns to avoid KeyError
            existing_required_cols = [
                col for col in required_columns if col in df.columns
            ]
            if not existing_required_cols:
                return []  # No required columns exist at all
            df_subset = df[existing_required_cols]
        else:
            df_subset = df[required_columns]

        if len(required_columns) == 1:
            # Single column requested, return as a list of its values
            # Ensure NaNs become None
            return df_subset[required_columns[0]].tolist()
        else:
            # Multiple columns, return list of dicts for these columns
            return df_subset.to_dict(orient="records")

    def _load_villager_names(self):
        """Loads villager names from villagers.csv."""
        try:
            # Expects a 'Name' column
            villagers_data = self._load_csv_data(
                "villagers.csv", required_columns=["Name"]
            )
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
            "fossils.csv": ("Name", "Sell"),
            "housewares.csv": ("Name", "Sell"),
            "miscellaneous.csv": ("Name", "Sell"),
            "accessories.csv": ("Name", "Sell"),
            "tools.csv": ("Name", "Sell"),
            "insects.csv": ("Name", "Sell"),  # Changed from "bugs.csv"
            "fish.csv": ("Name", "Sell"),
            "art.csv": ("Name", "Sell"),
            "bottoms.csv": ("Name", "Sell"),
            "dress-up.csv": ("Name", "Sell"),
            "headwear.csv": ("Name", "Sell"),
            "photos.csv": ("Name", "Sell"),
            "posters.csv": ("Name", "Sell"),
            "rugs.csv": ("Name", "Sell"),
            "shoes.csv": ("Name", "Sell"),
            "socks.csv": ("Name", "Sell"),
            "tops.csv": ("Name", "Sell"),
            "umbrellas.csv": ("Name", "Sell"),
            "wall-mounted.csv": ("Name", "Sell"),
            "wallpaper.csv": ("Name", "Sell"),
            "floors.csv": ("Name", "Sell"),
            # If crops are sellable through general store, they'd need to be here or handled separately.
            # For now, crop sell prices are in their own definitions.
        }
        default_friendship_points = 3

        for filename, (name_col, price_col) in item_files_info.items():
            try:
                items_data = self._load_csv_data(
                    filename, required_columns=[name_col, price_col]
                )
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
                            "cost": sell_price,  # For gifting, cost might be different. For selling, this is sell_price.
                            "friendship_points": default_friendship_points,  # Generic friendship
                            "sell_price": sell_price,
                            "category": filename.split(".")[
                                0
                            ],  # e.g., "fossils", "housewares"
                        }
            except Exception as e:
                print(f"Warning: Could not load items from {filename}: {e}")

        gift_options.update(
            {
                "Wrapped Fruit": {
                    "cost": 250,
                    "friendship_points": 3,
                    "sell_price": 250,
                    "category": "special_gift",
                },
                "Non-Native Fruit Basket": {
                    "cost": 1500,
                    "friendship_points": 4,
                    "sell_price": 1500,
                    "category": "special_gift",
                },
            }
        )
        return gift_options

    def _load_nook_miles_tasks(self):
        """Loads Nook Miles task templates from achievements.csv, including criteria."""
        tasks = {}
        try:
            # Assuming self._load_csv_data is part of the same class
            # and correctly returns a list of dictionaries (each dict is a row)
            achievements_data = self._load_csv_data("achievements.csv")
            if not achievements_data:
                print(
                    "Warning: achievements.csv is empty or could not be loaded. No Nook Miles tasks will be available."
                )
                return {}

            for achievement in achievements_data:
                base_task_name = achievement.get("Internal Name")
                if not base_task_name:
                    print(
                        f"Skipping achievement due to missing 'Internal Name': {achievement.get('Name')}"
                    )
                    continue

                internal_category = achievement.get("Internal Category")
                award_criteria_text = achievement.get(
                    "Award Criteria", ""
                )  # Full text description

                num_tiers_str = str(achievement.get("Num of Tiers", "1")).strip()
                num_tiers = 1
                if num_tiers_str.isdigit() and int(num_tiers_str) > 0:
                    num_tiers = int(num_tiers_str)
                elif num_tiers_str:  # Non-empty but not a positive digit
                    print(
                        f"Warning: Invalid 'Num of Tiers' ('{num_tiers_str}') for {base_task_name}. Defaulting to 1 tier."
                    )

                for tier_num in range(1, num_tiers + 1):
                    miles_val = None
                    # Corrected column name for Nook Miles rewards
                    reward_col_name = f"Reward Tier {tier_num}"
                    val_str = achievement.get(reward_col_name)

                    if val_str is not None and val_str.strip().isdigit():
                        miles_val = int(val_str.strip())
                        if miles_val <= 0:  # Ignore non-positive miles values
                            miles_val = None

                    if miles_val is None:
                        # If no miles for this specific tier, or miles are 0, skip this tier for this achievement
                        # print(f"Debug: No valid miles found for {base_task_name} Tier {tier_num} in column {reward_col_name}. Value: '{val_str}'")
                        continue

                    task_name_to_use = (
                        f"{base_task_name} (Tier {tier_num})"
                        if num_tiers > 1
                        else base_task_name
                    )

                    criteria = {
                        "description": award_criteria_text,  # General description
                        "category": internal_category,
                        "quantity": None,  # Will be filled from "Tier X" column
                        # "type" and "item_name" are harder to generically derive from this CSV per tier
                        # and might need specific logic per Internal Category if required.
                    }

                    # Corrected column name for criteria quantity
                    quantity_col_name = f"Tier {tier_num}"
                    quantity_str = achievement.get(quantity_col_name)
                    if quantity_str and quantity_str.strip().isdigit():
                        criteria["quantity"] = int(quantity_str.strip())
                    elif (
                        quantity_str and quantity_str.strip()
                    ):  # If quantity is not a number but present (e.g. for event type)
                        # For some tasks (like the first sample "ImmigratetoIsland"), Tier 1 = 1 might mean 'completed once'.
                        # If it's just an event flag, an explicit quantity might not always be numeric in the same sense.
                        # For simplicity, we'll try to parse as int, otherwise leave as None or handle based on category.
                        # Here, we'll assume if it's not a digit, it's not a countable quantity for now.
                        pass

                    # Duration is not in the sample CSV, defaulting to 1 as in original code.
                    # If you add a "Duration Days Tier X" or similar column, you can parse it here.
                    duration_days = 1

                    tasks[task_name_to_use] = {
                        "public_name": achievement.get(
                            "Name", base_task_name
                        ),  # User-friendly name
                        "miles": miles_val,
                        "criteria": criteria,
                        "duration_days": duration_days,
                        "internal_id": achievement.get("Internal ID"),
                        "sequential": achievement.get("Sequential", "No").lower()
                        == "yes",
                    }

        except Exception as e:
            print(
                f"Unexpected error processing achievements.csv for Nook Miles tasks: {e}"
            )
            import traceback

            print(traceback.format_exc())  # Helpful for debugging during development

        # Final filter: ensure all returned tasks have positive miles (already handled by miles_val <= 0 check)
        return tasks

    def _load_fish_data(self):
        """Loads fish data from fish.csv."""
        try:
            fish_data_raw = self._load_csv_data("fish.csv")  # Load all columns
            valid_fish = []
            if not fish_data_raw:
                return []

            for fish_item in fish_data_raw:
                name = fish_item.get("Name")
                sell_price_str = fish_item.get("Sell")
                if name and sell_price_str is not None:
                    try:
                        fish_item["Sell"] = int(float(sell_price_str))
                        valid_fish.append(fish_item)
                    except ValueError:
                        print(
                            f"Warning: Could not parse sell price for fish '{name}'. Skipping."
                        )
            return valid_fish
        except Exception as e:
            print(f"Unexpected error loading fish.csv: {e}")
            return []

    def _load_crop_data(self):
        """Loads crop definitions from crops.csv."""
        crop_defs = {}
        # Expected columns: Name, GrowthTimeDays, SellPrice, SeedCost, Yield
        try:
            crop_data_raw = self._load_csv_data(
                "crops.csv",
                required_columns=[
                    "Name",
                    "GrowthTimeDays",
                    "SellPrice",
                    "SeedCost",
                    "Yield",
                ],
            )
            if not crop_data_raw:
                generate_crops_dataset()
                crop_data_raw = self._load_csv_data(
                    "crops.csv",
                    required_columns=[
                        "Name",
                        "GrowthTimeDays",
                        "SellPrice",
                        "SeedCost",
                        "Yield",
                    ],
                )

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
                        "Yield": int(crop_item.get("Yield", 1)),
                    }
                except ValueError as ve:
                    print(
                        f"Warning: Could not parse data for crop '{name}'. Skipping. Error: {ve}"
                    )
            return crop_defs
        except Exception as e:
            print(f"Unexpected error loading crops.csv: {e}")
            return {}

    def get_random_villager_name(self):
        if not self.villager_names:
            return "Unknown Villager"
        return random.choice(self.villager_names)

    def get_gift_details(self, gift_name):  # Also used for item sell price
        details = self.gift_options.get(gift_name)
        if not details and gift_name in self.crop_definitions:  # Check if it's a crop
            crop_def = self.crop_definitions[gift_name]
            return {
                "cost": crop_def[
                    "SeedCost"
                ],  # Or perhaps its sell price if thinking of buying the crop itself
                "friendship_points": 2,  # Generic for crops
                "sell_price": crop_def["SellPrice"],
                "category": "crop",
            }
        return details

    def get_random_gift_option(self):
        if not self.gift_options:
            return "Generic Gift", {
                "cost": 10,
                "friendship_points": 1,
                "sell_price": 10,
                "category": "unknown",
            }
        name = random.choice(list(self.gift_options.keys()))
        return name, self.gift_options[name]

    def get_daily_nook_miles_task_templates(self, count=5):  # Renamed for clarity
        if not self.nook_miles_task_templates:
            return {}

        available_tasks = list(self.nook_miles_task_templates.items())
        num_to_sample = min(count, len(available_tasks))
        if num_to_sample == 0:
            return {}

        sampled_task_kv_pairs = random.sample(available_tasks, k=num_to_sample)
        return dict(sampled_task_kv_pairs)

    def get_random_fish(self) -> Optional[Dict[str, Any]]:
        if not self.fish_data:
            return None
        return random.choice(self.fish_data)

    def get_fish_details(self, fish_name: str) -> Optional[Dict[str, Any]]:
        if not self.fish_data:
            return None
        for fish_item in self.fish_data:
            if fish_item.get("Name") == fish_name:
                return fish_item
        return None

    def get_crop_definition(self, crop_name: str) -> Optional[Dict[str, Any]]:
        return self.crop_definitions.get(crop_name)
    
    def get_estimated_fish_value(self): # New method for GO_FISHING scoring
        if not self.fish_data:
            # print("Warning: Fish data is not loaded. Returning default estimated value.")
            return 250  # Default value if no fish data is available

        total_value = 0
        count = 0
        for fish_item in self.fish_data:
            sell_price = fish_item.get("Sell")
            if isinstance(sell_price, (int, float)): # Ensure 'Sell' price is a number
                total_value += sell_price
                count += 1
            # else:
                # Optionally, log a warning if a fish item has an invalid or missing sell price
                # print(f"Warning: Fish '{fish_item.get('Name')}' has invalid or missing 'Sell' price.")

        if count == 0:
            # print("Warning: No fish with valid sell prices found. Returning default estimated value.")
            return 250  # Default if no fish have valid sell prices
        
        average_value = total_value / count
        return round(average_value) # Return the rounded average value
