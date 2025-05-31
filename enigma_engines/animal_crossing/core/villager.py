from typing import Any, Dict, Optional


class ACNHVillager:
    def __init__(self, name):
        self.name = name
        self.friendship_level = 10
        self.bells = 0
        self.nook_miles = 0
        self.last_gifted_day = -1
        self.inventory: Dict[str, int] = {}  # item_name: quantity
        self.daily_activity_log: Dict[str, Any] = {
            "sold_items": []
        }  # For tracking criteria

    def receive_gift(self, gift_details, current_day):
        if self.last_gifted_day == current_day:
            return 0

        points = gift_details.get("friendship_points", 0)
        self.friendship_level = min(255, self.friendship_level + points)
        self.last_gifted_day = current_day
        return points

    def give_gift(self, item_name: str, quantity: int = 1):
        if item_name in self.inventory and self.inventory[item_name] >= quantity:
            self.remove_from_inventory(item_name, quantity)
            return True
        return False

    def add_to_inventory(self, item_name_or_data, quantity=1):
        """
        Adds an item to the villager's inventory.
        item_name_or_data can be a string (the item's name) or a dictionary
        from which the item's name can be extracted (e.g., from a 'name' key).
        """
        actual_item_name = None
        if isinstance(item_name_or_data, dict):
            # If it's a dictionary, try to get the name from a 'name' key
            actual_item_name = item_name_or_data.get("Name")
            if actual_item_name is None:
                # If 'name' key is not found or is None, this is an unexpected dict structure
                raise ValueError(
                    f"If item_name_or_data is a dict, it must have a 'name' key with a string value. Got: {item_name_or_data}"
                )
        elif isinstance(item_name_or_data, str):
            actual_item_name = item_name_or_data
        else:
            # If it's neither a dict nor a string, it's an unsupported type
            raise TypeError(
                f"item_name_or_data must be a string or a dictionary, but got {type(item_name_or_data)}"
            )

        if not isinstance(actual_item_name, str) or not actual_item_name:
            # Ensure the extracted name is a non-empty string
            raise ValueError(
                f"Could not determine a valid string item name from: {item_name_or_data}"
            )

        print(self.inventory)
        self.inventory[actual_item_name] = (
            self.inventory.get(actual_item_name, 0) + quantity
        )

    def remove_from_inventory(self, item_name, quantity=1):
        if item_name in self.inventory and self.inventory[item_name] >= quantity:
            self.inventory[item_name] -= quantity
            if self.inventory[item_name] == 0:
                del self.inventory[item_name]
            return True
        return False

    def log_sale(
        self, item_name: str, quantity: int, value: int, category: Optional[str]
    ):
        self.daily_activity_log.setdefault("sold_items", []).append(
            {
                "name": item_name,
                "quantity": quantity,
                "value": value,
                "category": category,
            }
        )

    def reset_daily_log(self):
        self.daily_activity_log = {"sold_items": []}

    def __str__(self):
        return (
            f"{self.name} (Friendship: {self.friendship_level}, Inv: {self.inventory})"
        )
