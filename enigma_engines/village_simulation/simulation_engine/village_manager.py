import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel
from pydantic import Field as PydanticField

# Rich library imports (as provided by user)
from rich.console import Console as RichConsole
from rich.console import Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from enigma_engines.village_simulation.agents.villager import Villager
from enigma_engines.village_simulation.environment.army import Army
from enigma_engines.village_simulation.environment.field import Field
from enigma_engines.village_simulation.environment.forest import Forest
from enigma_engines.village_simulation.environment.river import River
from enigma_engines.village_simulation.environment.tannery import Tannery
from enigma_engines.village_simulation.environment.vendor import Garrick_Ironheart, Lyra, Mira_Greenleaf, Vendor
from enigma_engines.village_simulation.resources.food import Food, berries, bread, fish
from enigma_engines.village_simulation.resources.item import Item
from enigma_engines.village_simulation.resources.raw_material import (
    RawMaterial,
    leather,
    skin,
    wood,
)
from enigma_engines.village_simulation.environment.weather import WeatherSystem
from enigma_engines.village_simulation.utilities.id_generator import Gender, generate_medieval_villager_name
from enigma_engines.village_simulation.utilities.logger import backend_logger

# --- Rich Console Initialization ---
# Using a different name to avoid conflict if user has 'console' elsewhere
rich_console_instance = RichConsole()

# --- VillageManager Class ---
class VillageManager(BaseModel):
    village_id: UUID = PydanticField(default_factory=uuid4)
    name: str = "Greendale"
    current_date: datetime = PydanticField(default_factory=datetime.now)
    
    villagers: Dict[UUID, Villager] = PydanticField(default_factory=dict)
    weather_system: WeatherSystem = PydanticField(default_factory=WeatherSystem)
    forest: Optional[Forest] = None
    river: Optional[River] = None
    tannery: Optional[Tannery] = None
    fields: List[Field] = PydanticField(default_factory=list)
    vendors: List[Vendor] = PydanticField(default_factory=list)
    army: Optional[Army] = None

    treasury: float = 1000.0
    food_storage: Dict[Food, int] = PydanticField(default_factory=dict) # Village-level storage
    resource_storage: Dict[RawMaterial, int] = PydanticField(default_factory=dict)

    # Market & Migration
    external_market_prices: Dict[Item, float] = PydanticField(default_factory=dict) # Item -> price
    goods_for_export: Dict[Item, int] = PydanticField(default_factory=dict)
    needed_imports: Dict[Item, int] = PydanticField(default_factory=dict)
    village_attractiveness: float = 0.5 # 0.0 to 1.0
    days_since_last_migration: int = 0
    MIGRATION_CHECK_INTERVAL_DAYS: int = 7 # Check for migration weekly
    MIGRATION_COOLDOWN_DAYS: int = 30 # After an event, wait before another
    migration_cooldown: int = 0 # Cooldown for migration events

    # Stats
    total_population: int = 0
    average_happiness: float = 0.0
    average_health: float = 0.0

    daily_incidents: List[Tuple[str, str]] = PydanticField(default_factory=list) # (icon, message) or (category, message)
    master_log_for_summary: List[str] = PydanticField(default_factory=list) # Collects messages from villager actions

    class Config: arbitrary_types_allowed = True

    def log_incident(self, message: str, category: str = "general"):
        """Logs a notable event for the daily summary."""
        icon_map = {
            "death": "💀", "birth": "👶", "migration_in": "➡️🏘️", "migration_out": "🏘️⬅️",
            "trade": "⚖️", "discovery": "💡", "disaster": "🔥", "construction": "🏗️",
            "crime": "🔪", "celebration": "🎉", "illness": "🤢", "recovery": "💪",
            "activity": "🛠️", "crafting": "🔧", "farming": "🌾", "warning": "⚠️"
        }
        self.daily_incidents.append((icon_map.get(category, "ℹ️"), message))

    def initialize_village(self, num_villagers: int = 10, forest_size_sqkm: float = 2.0, river_name: str = "Clearwater River"):
        backend_logger.info(f"Initializing village: {self.name} on {self.current_date.strftime('%Y-%m-%d')}")
        self._create_environment(forest_size_sqkm, river_name)
        self._create_initial_population(num_villagers)
        self._create_vendors_and_buildings()
        self.army = Army(total_capacity=max(20, num_villagers // 2)) # Army size based on pop
        self._assign_initial_jobs()
        self._update_village_stats()
        self.initialize_market_prices()
        backend_logger.info(f"Village '{self.name}' initialized with {self.total_population} villagers.")

    def _create_environment(self, forest_size_sqkm: float, river_name: str):
        self.forest = Forest(name="The Wild Woods", size=forest_size_sqkm, weather_system=self.weather_system)
        self.river = River(
            name=river_name,
            length=forest_size_sqkm * 2,
            base_flow_rate= random.uniform(0.5, 2.0),  # Random flow rate for variety
            base_depth= random.uniform(1.0, 5.0),  # Random depth for variety
            weather_system=self.weather_system,
            fish_population={
                "trout": random.randint(10, 80),  # Random initial fish counts
                "salmon": random.randint(10, 40),
                "catfish": random.randint(10, 70),
                "minnow": random.randint(10, 50),
                "pike": random.randint(10, 20)
            }
        )
        self.fields.append(Field(
            name="Hilltop Farm",
            size=forest_size_sqkm * 0.15
        ))
        self.fields.append(Field(
            name="South Meadow",
            size=forest_size_sqkm * 0.25
        ))
        self.fields.append(Field(
            name="Seaside Pasture",
            size=forest_size_sqkm * 0.13
        ))
        backend_logger.info("Environment created (Forest, River, Field).")

    def _create_initial_population(self, count: int):
        occupations = ["Farmer", "Woodcutter", "Fisherman", "Forager", "Hunter", "Tanner"]
        for i in range(count):
            age = random.randint(18, 50)
            occupation = random.choice(occupations)
            # Assign basic skills based on occupation
            skills = {occupation.lower(): random.uniform(0.5, 2.0)}
            if occupation == "Hunter": skills["foraging"] = random.uniform(0.2,1.0)
            if occupation == "Tanner": skills["hunting"] = random.uniform(0.2,0.8) # Tanners might need to source hides
            gender = random.choice([Gender.MALE, Gender.FEMALE])
            villager = Villager(
                name=generate_medieval_villager_name(gender),
                gender = gender,
                age=age,
                occupation=occupation,
                skills=skills,
                money=random.uniform(10, 50), health=random.randint(70,100),
                happiness=random.randint(60,90), energy=random.randint(80,100),
                current_forest=self.forest, current_river=self.river, # Pass environment refs
                current_tannery=self.tannery, weather_system=self.weather_system
            )
            self.villagers[villager.name] = villager
        self.total_population = len(self.villagers)

    def _create_vendors_and_buildings(self):
        self.vendors.extend([Garrick_Ironheart, Mira_Greenleaf, Lyra])
        self.tannery = Tannery(name="The Rusty Hide") # Village owns the tannery building
        # Villagers with "Tanner" occupation will use self.tannery
        for v_id, villager in self.villagers.items():
            villager.current_tannery = self.tannery # Ensure tanners know where it is

        backend_logger.info("Vendors and Tannery created.")

    def _assign_initial_jobs(self): # Simple assignment, could be more complex
        # Already assigned occupation during creation. This could be for specific tasks.
        # For now, occupation dictates primary work type.
        pass

    def initialize_market_prices(self):
        # Example: Set some initial external market prices
        self.external_market_prices[wood] = 1.5
        self.external_market_prices[leather] = 20.0
        self.external_market_prices[fish] = 3.0
        self.external_market_prices[berries] = 0.8
        self.external_market_prices[skin] = 4.0

    def simulate_daily_tick(self):
        self.current_date += timedelta(days=1)
        backend_logger.info(f"\n===== SIMULATING DAY: {self.current_date.strftime('%Y-%m-%d')} =====")

        # 1. Weather System Update
        self.weather_system.advance_day()
        backend_logger.info(self.weather_system.get_weather_overview())

        # 2. Environment Updates (react to weather)
        if self.forest: self.forest.update_daily()
        if self.river: self.river.daily_river_update()
        # Fields would also update here (planting, growth, harvest)

        # 3. Villager Updates (plan and execute actions)
        world_knowledge = self.get_world_knowledge()
        villagers_to_remove = []
        for villager_id, villager in list(self.villagers.items()): # list() for safe removal
            if villager.is_alive:
                villager.daily_update_cycle(village_manager_ref=self, world_knowledge=world_knowledge)
                # Collect resources produced by villagers into village storage (optional)
                # For example, if a woodcutter produces logs, they might go to village storage or their inventory
            if not villager.is_alive:
                villagers_to_remove.append(villager_id)
        
        for v_id in villagers_to_remove:
            backend_logger.info(f"Villager {self.villagers[v_id].name} has died and is removed from the village.")
            del self.villagers[v_id]


        # 4. Village-level processes
        self._update_village_storage_from_villagers() # Consolidate goods
        self._handle_external_trade()
        self._handle_migration()
        
        # 5. Update Village Stats
        self._update_village_stats()
        backend_logger.info(f"End of Day Stats: Pop: {self.total_population}, Happiness: {self.average_happiness:.2f}, Treasury: {self.treasury:.2f}")
        backend_logger.info(f"Food Storage: {[(f.name,q) for f,q in self.food_storage.items()]}, Resource Storage: {[(r.name,q) for r,q in self.resource_storage.items()]}")

    def _update_village_storage_from_villagers(self):
        """ Collects a portion of gathered/produced goods from villagers to central storage, or they sell it."""
        # This is a complex economic decision. For now, assume villagers manage their own goods
        # and sell them via SELLING_GOODS action which interacts with vendors or external market.
        # Village could impose taxes or buy surplus.
        # Example: A portion of woods from woodcutters could go to village storage.
        for villager in self.villagers.values():
            if villager.occupation == "Woodcutter" and villager.inventory.get(wood, 0) > 5:
                transfer_amount = villager.inventory.get(wood,0) // 2
                villager.inventory[wood] -= transfer_amount
                self.resource_storage[wood] = self.resource_storage.get(wood,0) + transfer_amount
                backend_logger.info(f"{villager.name} contributed {transfer_amount} {wood.name} to village storage.")


    def get_world_knowledge(self) -> Dict[str, Any]:
        """Provides context for villager decision-making."""
        return {
            "vendors": self.vendors,
            "market_prices": self.external_market_prices, # Villagers might check this for selling
            "forest_health": self.forest.health if self.forest else 0.5,
            "river_fish_abundance": sum(self.river.fish_population.values()) if self.river else 0,
            # Add more as needed, e.g., job availability, village needs
        }

    def _calculate_village_attractiveness(self) -> float:
        # Factors: avg happiness, avg health, food security, wealth (treasury/capita), safety (army strength)
        food_security_score = 0.0
        total_food_units = sum(self.food_storage.values()) + sum(
            v.inventory.get(item,0) for v in self.villagers.values() for item in v.inventory if isinstance(item, Food)
        )
        if self.total_population > 0:
            food_per_capita = total_food_units / self.total_population
            food_security_score = min(1.0, food_per_capita / 10.0) # e.g. 10 units/person is secure
        
        safety_score = 0.0
        if self.army and self.total_population > 0:
            army_strength_ratio = sum(self.army.units.values()) / self.total_population
            safety_score = min(1.0, army_strength_ratio / 0.1) # e.g. 1 soldier per 10 pop is good

        wealth_score = min(1.0, (self.treasury / (self.total_population +1)) / 50.0) # e.g. 50 gold/person is wealthy

        attractiveness = (
            self.average_happiness * 0.3 +
            self.average_health * 0.2 +
            food_security_score * 0.25 +
            wealth_score * 0.15 +
            safety_score * 0.1
        )
        self.village_attractiveness = max(0.0, min(1.0, attractiveness))
        return self.village_attractiveness

    def _handle_migration(self):
        self.days_since_last_migration += 1
        if self.days_since_last_migration < self.MIGRATION_CHECK_INTERVAL_DAYS:
            return

        self.days_since_last_migration = 0 # Reset check timer
        if self.migration_cooldown > 0:
            self.migration_cooldown -= self.MIGRATION_CHECK_INTERVAL_DAYS
            return

        self._calculate_village_attractiveness()
        
        # Immigration
        if self.village_attractiveness > 0.7 and self.total_population < 1000: # Cap population
            num_new_migrants = random.randint(0, int(self.total_population * 0.05 * self.village_attractiveness)) # Up to 5% of pop based on score
            num_new_migrants = min(num_new_migrants, 5) # Max 5 per event
            if num_new_migrants > 0:
                backend_logger.info(f"Village is thriving! Attractiveness: {self.village_attractiveness:.2f}. {num_new_migrants} new villagers are migrating.")
                self._create_new_migrants(num_new_migrants)
                self.migration_cooldown = self.MIGRATION_COOLDOWN_DAYS

        # Emigration
        elif self.village_attractiveness < 0.3 and self.total_population > 5: # Min pop to have leavers
            import secrets
            max_leavers = int(self.total_population * 0.05 * (1.0 - self.village_attractiveness))
            num_leavers = secrets.randbelow(max_leavers + 1) if max_leavers > 0 else 0
            num_leavers = min(num_leavers, max(0,self.total_population - 5), 3) # Max 3 per event, don't drop below 5
            if num_leavers > 0:
                backend_logger.warning(f"Village is struggling! Attractiveness: {self.village_attractiveness:.2f}. {num_leavers} villagers are leaving.")
                self._remove_migrants(num_leavers)
                self.migration_cooldown = self.MIGRATION_COOLDOWN_DAYS
    
    def _create_new_migrants(self, count: int):
        # Similar to _create_initial_population but for migrants
        occupations = ["Farmer", "Woodcutter", "Fisherman", "Forager", "Laborer"] # Migrants might be general laborers
        for _ in range(count):
            if self.total_population >= 1000: break # Hard cap
            age = random.randint(18, 40)
            occupation = random.choice(occupations)
            skills = {occupation.lower(): random.uniform(0.1, 1.0)} # Migrants might have lower starting skills
            
            gender = random.choice([Gender.MALE, Gender.FEMALE])
            new_villager = Villager(
                name=generate_medieval_villager_name(gender),
                gender = gender, age=age, occupation=occupation, skills=skills,
                money=random.uniform(5, 20), health=random.randint(60,90), happiness=random.randint(50,80), energy=random.randint(70,100),
                current_forest=self.forest, current_river=self.river, current_tannery=self.tannery, weather_system=self.weather_system
            )
            self.villagers[new_villager.name] = new_villager
        self._update_village_stats() # Recalculate total_population

    def _remove_migrants(self, count: int):
        if count >= self.total_population:
            backend_logger.warning("Attempted to remove all villagers via emigration, leaving a minimum.")
            count = self.total_population - 1 if self.total_population > 0 else 0
        
        if count <= 0: return

        # Villagers with lowest happiness/health are more likely to leave
        sorted_villagers = sorted(list(self.villagers.values()), key=lambda v: v.happiness + v.health)
        
        for i in range(min(count, len(sorted_villagers))):
            villager_to_remove = sorted_villagers[i]
            backend_logger.info(f"{villager_to_remove.name} (Hap:{villager_to_remove.happiness}, Hea:{villager_to_remove.health}) has left the village.")
            del self.villagers[villager_to_remove.id]
        self._update_village_stats()


    def _handle_external_trade(self):
        """Simulate basic import/export with an external market."""
        # Export surplus goods
        for item, quantity in list(self.goods_for_export.items()): # list() for safe modification
            if item in self.resource_storage and self.resource_storage[item] >= quantity:
                market_price = self.external_market_prices.get(item, item.base_value * 0.7) # Default if no price
                revenue = market_price * quantity
                self.treasury += revenue
                self.resource_storage[item] -= quantity
                if self.resource_storage[item] == 0: del self.resource_storage[item]
                del self.goods_for_export[item]
                backend_logger.info(f"Exported {quantity} {item.name} for {revenue:.2f} gold.")
            elif item in self.food_storage and self.food_storage[item] >= quantity:
                market_price = self.external_market_prices.get(item, item.base_value * 0.7)
                revenue = market_price * quantity
                self.treasury += revenue
                self.food_storage[item] -= quantity
                if self.food_storage[item] == 0: del self.food_storage[item]
                del self.goods_for_export[item]
                backend_logger.info(f"Exported {quantity} {item.name} (food) for {revenue:.2f} gold.")


        # Import needed goods
        for item, quantity in list(self.needed_imports.items()):
            market_price = self.external_market_prices.get(item, item.base_value * 1.3) # Default import price
            cost = market_price * quantity
            if self.treasury >= cost:
                self.treasury -= cost
                if isinstance(item, Food):
                    self.food_storage[item] = self.food_storage.get(item, 0) + quantity
                elif isinstance(item, RawMaterial):
                     self.resource_storage[item] = self.resource_storage.get(item, 0) + quantity
                else: # Other items, maybe general village inventory or directly to who needs it
                    backend_logger.warning(f"Imported {item.name}, but no specific storage category.")

                del self.needed_imports[item]
                backend_logger.info(f"Imported {quantity} {item.name} for {cost:.2f} gold.")
            else:
                backend_logger.warning(f"Cannot import {quantity} {item.name}, not enough treasury (need {cost:.2f}).")
        
        # Dynamically adjust goods_for_export and needed_imports based on storage levels (simple example)
        # If wood storage is high, mark some for export
        if self.resource_storage.get(wood, 0) > 100 and wood not in self.goods_for_export:
            self.goods_for_export[wood] = 20
        # If food storage is low for bread, mark for import
        if self.food_storage.get(bread, 0) < 10 and self.total_population > 0 and bread not in self.needed_imports:
            self.needed_imports[bread] = 10 * (self.total_population // 5 +1) # Need more if more pop


    def _update_village_stats(self):
        self.total_population = len(self.villagers)
        if self.total_population > 0:
            self.average_happiness = sum(v.happiness for v in self.villagers.values()) / self.total_population
            self.average_health = sum(v.health for v in self.villagers.values()) / self.total_population
        else:
            self.average_happiness = 0.0
            self.average_health = 0.0

    def add_villager(self, villager: Villager): # For manual addition if needed
        if villager.id not in self.villagers:
            self.villagers[villager.id] = villager
            villager.current_forest = self.forest
            villager.current_river = self.river
            villager.current_tannery = self.tannery
            villager.weather_system = self.weather_system
            self._update_village_stats()
            backend_logger.info(f"Added {villager.name} to the village.")

    
    # --- Rich Panel Display Functions ---
    def _prepare_weather_panel_content(self) -> List[Any]:
        ws = self.weather_system
        temp = ws.get_current_temperature_estimate()
        weather_icon = ws.weather_icons.get(ws.current_weather_condition, "")
        season_icon = ws.season_icons.get(ws.current_season, "")
        
        elements = [
            Text(f"{season_icon} Season: {ws.current_season.value.capitalize()} (Day {ws.current_day_in_season}/{ws.days_per_season})", style="bold yellow"),
            Text(f"{weather_icon} Weather: {ws.current_weather_condition.value.replace('_',' ').capitalize()}", style="blue"),
            Text(f"🌡️ Temperature: {temp:.1f}°C", style="magenta"),
            Text(f"💧 Precipitation Intensity: {ws.get_current_precipitation_intensity():.2f}", style="cyan")
        ]
        return elements

    def _prepare_village_stats_panel_content(self) -> List[Any]:
        elements = [
            Text(f"👨‍👩‍👧‍👦 Population: {self.total_population}", style="bold green"),
            Text(f"😊 Avg Happiness: {self.average_happiness:.1f}/100", style="green" if self.average_happiness > 60 else ("yellow" if self.average_happiness > 40 else "red")),
            Text(f"❤️ Avg Health: {self.average_health:.1f}/100", style="green" if self.average_health > 60 else ("yellow" if self.average_health > 40 else "red")),
            Text(f"💰 Treasury: {self.treasury:.2f} gold", style="gold1"),
            Text(f"✨ Attractiveness: {self.village_attractiveness:.2f}/1.0", style="bright_blue")
        ]
        # Food Storage
        food_table = Table(title="🍏 Village Food Storage", show_header=True, header_style="bold magenta")
        food_table.add_column("Food Item", style="dim cyan", width=15)
        food_table.add_column("Quantity", justify="right")
        for food_item, qty in self.food_storage.items():
            if qty > 0: food_table.add_row(f"{food_item.icon} {food_item.name}", str(qty))
        if not self.food_storage or all(q == 0 for q in self.food_storage.values()): food_table.add_row("[italic gray50]Empty[/italic gray50]", "")
        elements.append(food_table)

        # Resource Storage
        resource_table = Table(title="🧱 Village Resources", show_header=True, header_style="bold blue")
        resource_table.add_column("Resource", style="dim cyan", width=15)
        resource_table.add_column("Quantity", justify="right")
        for res_item, qty in self.resource_storage.items():
            if qty > 0: resource_table.add_row(f"{res_item.icon} {res_item.name}", str(qty))
        if not self.resource_storage or all(q == 0 for q in self.resource_storage.values()): resource_table.add_row("[italic gray50]Empty[/italic gray50]", "")
        elements.append(resource_table)
        return elements

    def _prepare_incidents_panel_content(self) -> List[Any]:
        if not self.daily_incidents:
            return [Text("☀️ A calm day, no major incidents reported.", style="italic green")]
        
        incident_table = Table(title="📢 Major Incidents", show_header=False, show_edge=False, box=None)
        incident_table.add_column("Log")
        for icon, message in self.daily_incidents:
            incident_table.add_row(f"{icon} {message}")
        return [incident_table]

    def _prepare_leaderboard_panel_content(self) -> List[Any]:
        elements = []
        if not self.villagers:
            return [Text("No villagers to rank.", style="italic")]

        # Richest Villager
        richest = sorted(self.villagers.values(), key=lambda v: v.money, reverse=True)
        richest_table = Table(title="🏆 Richest Villagers", title_style="bold gold1", show_header=True, header_style="bold magenta")
        richest_table.add_column("Name", width=20); richest_table.add_column("Money 💰", justify="right")
        for v in richest[:3]: richest_table.add_row(v.name, f"{v.money:.2f}")
        elements.append(richest_table)

        # Most Skilled (example: Woodcutting)
        best_woodcutters = sorted([v for v in self.villagers.values() if v.get_skill("woodcutting") > 0], key=lambda v: v.get_skill("woodcutting"), reverse=True)
        if best_woodcutters:
            skill_table = Table(title="🌲 Top Woodcutters", title_style="bold green4", show_header=True, header_style="bold magenta")
            skill_table.add_column("Name", width=20); skill_table.add_column("Skill Level", justify="right")
            for v in best_woodcutters[:3]: skill_table.add_row(v.name, f"{v.get_skill('woodcutting'):.1f}")
            elements.append(skill_table)
        
        # Daily Earners (simple version)
        daily_earners = sorted([v for v in self.villagers.values() if v.daily_earnings > 0], key=lambda v: v.daily_earnings, reverse=True)
        if daily_earners:
            earn_table = Table(title="📈 Top Daily Earners", title_style="bold green", show_header=True, header_style="bold magenta")
            earn_table.add_column("Name", width=20); earn_table.add_column("Earned 🪙", justify="right")
            for v in daily_earners[:3]: earn_table.add_row(v.name, f"{v.daily_earnings:.2f}")
            elements.append(earn_table)

        return elements if elements else [Text("No specific leaderboard data for today.", style="italic")]


    def _print_day_summary_panel_rich(self, panel_title: str, info_elements: list):
        panel_content_renderables = []
        for item in info_elements:
            if hasattr(item, "__rich_console__"): 
                panel_content_renderables.append(item)
            else: 
                panel_content_renderables.append(Text(str(item)))
        content_group = Group(*panel_content_renderables)
        rich_console_instance.print(
            Panel(Padding(content_group, (1, 2)), title=panel_title, border_style="bold bright_blue", expand=False)
        )

    def _display_daily_report_rich(self):
        panel_title = (
            f":calendar: [bold cyan]Village Report for {self.name}[/] - [yellow]Day {self.weather_system.total_days_simulated}[/] "
            f"({self.current_date.strftime('%A, %B %d, %Y')}) :sparkles:"
        )
        
        all_info_elements = []
        
        # Section 1: Weather
        all_info_elements.append(Panel(Group(*self._prepare_weather_panel_content()), title="[b yellow]:sun_behind_cloud: Weather Update[/b yellow]", border_style="yellow"))
        
        # Section 2: Village Stats
        all_info_elements.append(Panel(Group(*self._prepare_village_stats_panel_content()), title="[b green]:chart_increasing: Village Statistics[/b green]", border_style="green"))

        # Section 3: Major Incidents
        all_info_elements.append(Panel(Group(*self._prepare_incidents_panel_content()), title="[b red]:loudspeaker: Daily Incidents[/b red]", border_style="red"))

        # Section 4: Leaderboards
        all_info_elements.append(Panel(Group(*self._prepare_leaderboard_panel_content()), title="[b magenta]:trophy: Leaderboards[/b magenta]", border_style="magenta"))

        # Section 5: Detailed Villager Action Log (Optional, can be very verbose)
        if self.master_log_for_summary:
            log_text = Text("\n".join(self.master_log_for_summary[-20:])) # Last 20 actions
            all_info_elements.append(Panel(log_text, title="[b bright_black]Recent Activities[/b bright_black]", border_style="bright_black"))


        self._print_day_summary_panel_rich(panel_title, all_info_elements)

# --- Main Simulation Example ---
# if __name__ == "__main__":
#     village_sim = VillageManager(name="Oakhaven")
#     village_sim.initialize_village(num_villagers=15, forest_size_sqkm=3.0, river_name="Silverstream")

#     for day_count in range(1, 31): # Simulate 30 days
#         village_sim.simulate_daily_tick()
#         if day_count % 5 == 0: # Log detailed villager status every 5 days
#             backend_logger.info(f"--- Villager Status Check - End of Day {day_count} ---")
#             if not village_sim.villagers: backend_logger.info("No villagers left."); break
#             for v_id, v in village_sim.villagers.items():
#                 inv_summary = {item.name: qty for item, qty in v.inventory.items()}
#                 backend_logger.info(
#                     f"  {v.name} ({v.occupation}, {v.age}yo): H:{v.health} E:{v.energy} Hap:{v.happiness} M:{v.money:.1f} Skills:{v.skills} Inv:{inv_summary} Alive:{v.is_alive}"
#                 )
#         if not village_sim.villagers:
#             backend_logger.error("All villagers have perished or left! Simulation ends.")
#             break
    
#     backend_logger.info("\n===== SIMULATION FINISHED =====")
#     backend_logger.info(f"Final Village State for '{village_sim.name}' on {village_sim.current_date.strftime('%Y-%m-%d')}:")
#     backend_logger.info(f"  Population: {village_sim.total_population}")
#     backend_logger.info(f"  Avg Happiness: {village_sim.average_happiness:.2f}, Avg Health: {village_sim.average_health:.2f}")
#     backend_logger.info(f"  Treasury: {village_sim.treasury:.2f}")
#     backend_logger.info(f"  Food Storage: {[(f.name,q) for f,q in village_sim.food_storage.items()]}")
#     backend_logger.info(f"  Resource Storage: {[(r.name,q) for r,q in village_sim.resource_storage.items()]}")
#     backend_logger.info(f"  Village Attractiveness: {village_sim.village_attractiveness:.2f}")

