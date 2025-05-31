import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from enigma_engines.village_simulation.agents.villager import Villager
from enigma_engines.village_simulation.environment.vendor import Vendor
from enigma_engines.village_simulation.resources.clothing import (
    Clothing,
    daily_clothes,
    men_armor,
    women_wear,
)
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial,
    fabric,
    leather,
)
from enigma_engines.village_simulation.utilities import backend_logger


@dataclass
class ProductionOption:
    """Represents a clothing production option with profitability metrics."""

    item: Clothing
    max_possible: int
    profit_margin: float
    complexity: int
    material_cost: float


@dataclass
class WorkerStatus:
    """Represents a worker's current status and productivity."""

    employee: Villager
    productivity: float
    is_healthy: bool


class Tannery(BaseModel):
    """
    Represents a tannery in the village simulation.
    Tannery can process raw animal skins into leather, which can be used for crafting clothing and other items.

    Attributes:
        name (str): The name of the tannery.
        description (Optional[str]): A brief description of the tannery.
        inventory (Dict[RawMaterial, int]): A dictionary mapping raw materials to their quantities.
    """

    name: str
    description: Optional[str] = None
    inventory: Dict[RawMaterial, int] = {
        leather: 0,  # Processed leather
        fabric: 0,  # Processed fabric
    }

    manufactured_items: Dict[Clothing, int] = {
        daily_clothes: 0,
        women_wear: 0,
        men_armor: 0,
    }

    money: float = 0.0  # Balance for transactions
    employees: List[Villager] = []  # List of employees

    # Configuration constants
    MIN_HEALTH_TO_WORK: int = 20
    BASE_WAGE_PER_EMPLOYEE: float = 10.0
    ITEMS_PER_PRODUCTIVITY_POINT: int = 2
    OVERWORK_THRESHOLD: float = 0.8
    WORKPLACE_ACCIDENT_CHANCE: float = 0.01
    BASE_HEALTH_DECREASE: int = 5
    OVERWORK_HEALTH_PENALTY: int = 3
    ACCIDENT_HEALTH_PENALTY: int = 10

    def _can_craft(self, clothing_item: Clothing) -> bool:
        """Checks if there are enough materials in inventory to craft a clothing item."""
        if not clothing_item.required_materials:
            return False

        for material, required_qty in clothing_item.required_materials.items():
            if self.inventory.get(material, 0) < required_qty:
                return False
        return True

    def _craft_item(self, clothing_item: Clothing) -> bool:
        """Crafts one unit of a clothing item if materials are available."""
        if self._can_craft(clothing_item):
            for material, required_qty in clothing_item.required_materials.items():
                self.inventory[material] -= required_qty
                if self.inventory[material] == 0:  # Clean up inventory
                    del self.inventory[material]
            self.manufactured_items[clothing_item] = (
                self.manufactured_items.get(clothing_item, 0) + 1
            )
            return True
        return False

    def _assess_workforce(self) -> Tuple[List[WorkerStatus], float]:
        """
        Assess the health and productivity of all employees.

        Returns:
            Tuple of (worker_statuses, total_productivity)
        """
        worker_statuses = []
        total_productivity = 0.0

        for employee in self.employees:
            is_healthy = employee.health >= self.MIN_HEALTH_TO_WORK

            if is_healthy:
                productivity_modifier = (employee.health / 100) * (
                    employee.happiness / 100
                )
                skill_level = employee.skills.get("crafting", 1)
                productivity = skill_level * productivity_modifier
                total_productivity += productivity
            else:
                productivity = 0.0
                backend_logger.info(
                    f"{self.name}: {employee.name} is too sick to work today (health: {employee.health})."
                )

            worker_statuses.append(
                WorkerStatus(
                    employee=employee, productivity=productivity, is_healthy=is_healthy
                )
            )

        return worker_statuses, total_productivity

    def _calculate_production_options(self) -> List[ProductionOption]:
        """
        Calculate all possible clothing production options with profitability metrics.

        Returns:
            List of ProductionOption objects sorted by profit margin (descending)
        """
        options = []
        clothing_items = [men_armor, daily_clothes, women_wear]

        for clothing_item in clothing_items:
            if not clothing_item.required_materials:
                continue

            # Calculate maximum possible units
            max_possible = float("inf")
            for material, required_amount in clothing_item.required_materials.items():
                available = self.inventory.get(material, 0)
                max_possible = min(max_possible, available // required_amount)

            max_possible = int(max_possible)
            if max_possible <= 0:
                continue

            # Calculate financial metrics
            material_cost = sum(
                material.base_value * required_amount
                for material, required_amount in clothing_item.required_materials.items()
            )
            profit_margin = clothing_item.base_value - material_cost

            options.append(
                ProductionOption(
                    item=clothing_item,
                    max_possible=max_possible,
                    profit_margin=profit_margin,
                    complexity=len(clothing_item.required_materials),
                    material_cost=material_cost,
                )
            )

        # Sort by profit margin (highest first)
        options.sort(key=lambda x: x.profit_margin, reverse=True)
        return options

    def _manufacture_items(
        self, options: List[ProductionOption], max_capacity: int
    ) -> int:
        """
        Manufacture items based on production options and capacity.

        Args:
            options: List of production options sorted by profitability
            max_capacity: Maximum production capacity for the day

        Returns:
            Total number of items manufactured (adjusted for complexity)
        """
        items_manufactured = 0

        for option in options:
            if items_manufactured >= max_capacity:
                break

            # Adjust for complexity - complex items take more effort
            complexity_factor = 1 + (option.complexity * 0.2)
            remaining_capacity = max_capacity - items_manufactured
            items_to_make = min(
                option.max_possible, int(remaining_capacity / complexity_factor)
            )

            if items_to_make <= 0:
                continue

            # Produce the items
            for _ in range(items_to_make):
                if self._craft_item(option.item):
                    items_manufactured += complexity_factor
                else:
                    break  # Stop if we can't craft anymore

            actual_made = items_to_make  # Assuming all were successfully crafted
            revenue = option.item.base_value * actual_made
            backend_logger.info(
                f"{self.name}: Manufactured {actual_made} {option.item.name}(s) "
                f"for {revenue:.2f} potential revenue."
            )

        return int(items_manufactured)

    def _update_employee_conditions(
        self,
        worker_statuses: List[WorkerStatus],
        items_manufactured: int,
        max_capacity: int,
    ) -> None:
        """
        Update employee health, happiness, and skills based on work conditions.

        Args:
            worker_statuses: List of worker status objects
            items_manufactured: Number of items manufactured today
            max_capacity: Maximum production capacity
        """
        healthy_workers = [ws for ws in worker_statuses if ws.is_healthy]
        if not healthy_workers:
            return

        is_overworked = items_manufactured > max_capacity * self.OVERWORK_THRESHOLD

        for worker_status in healthy_workers:
            employee = worker_status.employee

            # Calculate health decrease
            health_decrease = self.BASE_HEALTH_DECREASE

            if is_overworked:
                health_decrease += self.OVERWORK_HEALTH_PENALTY
                employee.happiness = max(0, employee.happiness - 5)
                backend_logger.info(
                    f"{self.name}: {employee.name} feels overworked today."
                )

            # Check for workplace accidents
            if random.random() < self.WORKPLACE_ACCIDENT_CHANCE:
                health_decrease += self.ACCIDENT_HEALTH_PENALTY
                backend_logger.info(
                    f"{self.name}: {employee.name} had a minor workplace accident!"
                )

            # Apply health changes
            employee.health = max(0, employee.health - health_decrease)

            # Update skills
            if "crafting" in employee.skills and items_manufactured > 0:
                skill_improvement = min(
                    0.1 * (items_manufactured / len(healthy_workers)), 1.0
                )
                employee.skills["crafting"] += skill_improvement

            # Update happiness based on productivity
            if items_manufactured > 0:
                employee.happiness = min(100, employee.happiness + 2)
            else:
                employee.happiness = max(0, employee.happiness - 3)
                backend_logger.info(
                    f"{self.name}: {employee.name} is frustrated by lack of materials."
                )

    def _process_payroll(self, worker_statuses: List[WorkerStatus]) -> None:
        """
        Process employee wages and update happiness accordingly.

        Args:
            worker_statuses: List of worker status objects
        """
        healthy_workers = [ws for ws in worker_statuses if ws.is_healthy]
        if not healthy_workers:
            return

        total_wages = len(healthy_workers) * self.BASE_WAGE_PER_EMPLOYEE

        if self.money >= total_wages:
            self.money -= total_wages
            for worker_status in healthy_workers:
                employee = worker_status.employee
                employee.money += self.BASE_WAGE_PER_EMPLOYEE
                employee.happiness = min(100, employee.happiness + 1)
        else:
            backend_logger.info(
                f"{self.name}: Cannot afford to pay all employees today!"
            )
            for worker_status in healthy_workers:
                employee = worker_status.employee
                employee.happiness = max(0, employee.happiness - 10)

    def daily_work(self) -> None:
        """
        Execute daily work operations including manufacturing, employee management, and payroll.
        This method orchestrates all daily activities in the tannery.
        """
        if not self.employees:
            backend_logger.info(f"{self.name}: No employees available to work today.")
            return

        # Assess workforce
        worker_statuses, total_productivity = self._assess_workforce()
        healthy_workers = [ws for ws in worker_statuses if ws.is_healthy]

        if not healthy_workers:
            backend_logger.info(
                f"{self.name}: All employees are too sick to work today."
            )
            return

        # Calculate production capacity and options
        max_capacity = int(total_productivity * self.ITEMS_PER_PRODUCTIVITY_POINT)
        production_options = self._calculate_production_options()

        # Manufacture items
        items_manufactured = 0
        if production_options:
            items_manufactured = self._manufacture_items(
                production_options, max_capacity
            )

        # Update employee conditions
        self._update_employee_conditions(
            worker_statuses, items_manufactured, max_capacity
        )

        # Process payroll
        self._process_payroll(worker_statuses)

        # Daily summary
        if items_manufactured > 0:
            backend_logger.info(
                f"{self.name}: Daily work complete. {items_manufactured} items "
                f"manufactured by {len(healthy_workers)} employees."
            )
        else:
            backend_logger.info(
                f"{self.name}: No items could be manufactured today due to lack of materials."
            )

    def sell_inventory(self, vendor: Vendor) -> None:
        """Sells manufactured clothing and specified surplus raw materials to the vendor."""
        # Sell manufactured clothing first
        for clothing_item, quantity in list(self.manufactured_items.items()):
            if quantity > 0:
                sale_price = clothing_item.base_value
                if vendor.buy_item_from_producer(clothing_item, quantity, sale_price):
                    self.money += quantity * sale_price
                    del self.manufactured_items[clothing_item]

        # Sell surplus leather
        reserve_leather = 5
        if leather in self.inventory and self.inventory[leather] > reserve_leather:
            quantity_to_sell = self.inventory[leather] - reserve_leather
            sale_price = leather.base_value
            if vendor.buy_item_from_producer(leather, quantity_to_sell, sale_price):
                self.money += quantity_to_sell * sale_price
                self.inventory[leather] -= quantity_to_sell
                if self.inventory[leather] == 0:
                    del self.inventory[leather]

    def stock_inventory(
        self, item_to_buy: RawMaterial, quantity: int, vendor: Vendor
    ) -> None:
        """Buys a specified raw material from a vendor if affordable."""
        purchase_price_per_unit = item_to_buy.base_value
        total_cost = quantity * purchase_price_per_unit

        if self.money >= total_cost:
            if vendor.sell_item_to_customer(
                item_to_buy, quantity, purchase_price_per_unit
            ):
                self.money -= total_cost
                self.inventory[item_to_buy] = (
                    self.inventory.get(item_to_buy, 0) + quantity
                )

    def add_employee(self, villager: Villager) -> None:
        """Adds a villager as an employee to the tannery."""
        if (
            villager not in self.employees
            and villager.employer is None
            and villager.health > self.MIN_HEALTH_TO_WORK
        ):
            self.employees.append(villager)
            backend_logger.info(
                f"{villager.name} has been added as an employee at {self.name}."
            )
            villager.employer = self  # Set the villager's employer to this tannery
        else:
            backend_logger.info(
                f"{villager.name} is already an employee at {self.name}."
            )


tan_shop = Tannery(
    name="Local Tannery",
    description="A place where raw animal skins are crafted into clothing.",
    inventory={leather: 100, fabric: 100},
    manufactured_items={daily_clothes: 0, men_armor: 0, women_wear: 0},
    money=100.0,  # Initial money for transactions
    employees=[],  # Start with no employees
)
