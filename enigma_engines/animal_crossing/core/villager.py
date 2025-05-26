from typing import Any, Dict, Optional


class ACNHVillager:
    def __init__(self, name):
        self.name = name
        self.friendship_level = 25
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

    def add_to_inventory(self, item_name, quantity=1):
        self.inventory[item_name] = self.inventory.get(item_name, 0) + quantity

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
