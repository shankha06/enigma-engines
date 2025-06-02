import random
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, model_validator
from pydantic import Field as PydanticField

from enigma_engines.village_simulation.agents.villager import Villager
from enigma_engines.village_simulation.environment.weather import Season, TimeOfDay, WeatherCondition, WeatherSystem
from enigma_engines.village_simulation.resources.food import Food, fish
from enigma_engines.village_simulation.resources.item import (
    Item,
    lost_locket,
    old_coin,
    rusty_sword,
    scraps,
    soggy_boot,
)


@dataclass
class FishSpecies:
    name: str
    food_item: Food
    rarity: float
    size_range: Tuple[float, float]
    preferred_depth_factor: float
    active_times: List[TimeOfDay]
    weather_preference: List[WeatherCondition] # Weather conditions it might be MORE active in
    temperature_range: Tuple[float, float]
    min_skill_required: int
    escape_chance: float
    icon: str

@dataclass
class FishingResult:
    success: bool
    catch: Optional[Food] = None
    quantity: int = 0
    special_item: Optional[Item] = None
    message: str = ""

@dataclass
class EnvironmentalFactorsForFishing: # Renamed for clarity
    """Environmental factors for a specific fishing attempt."""
    weather_condition: WeatherCondition
    time_of_day: TimeOfDay
    water_temperature: float
    water_clarity: float
    season_modifier: float # General fishing modifier for the season


class River(BaseModel):
    name: str
    length: int
    base_depth: float
    base_flow_rate: float
    weather_system: Union[Any, WeatherSystem] # Allow 'Any' for flexibility if WeatherSystem is complex or use placeholder

    # Dynamic state variables, influenced by WeatherSystem and river's own dynamics
    current_water_level_multiplier: float = PydanticField(default=1.0)  # Multiplier for base_depth
    current_water_temperature: float = PydanticField(default=15.0) # Celsius
    pollution_level: float = PydanticField(default=0.0)

    fish_population: Dict[str, int] = PydanticField(default_factory=dict)
    villagers_present: Optional[List[Villager]] = PydanticField(default=None)
    icon: str = "🌊"

    # River-specific configuration
    MIN_FISH_PERCENTAGE_OF_MAX: float = 0.10
    FISH_REPLENISH_RATE: float = 0.05
    POLLUTION_FROM_FISHING_FACTOR: float = 0.001
    NATURAL_POLLUTION_DISSIPATION_RATE: float = 0.02
    BASE_CATCH_CHANCE: float = 0.25
    SKILL_BONUS_PER_LEVEL: float = 0.05
    EQUIPMENT_BONUS: Dict[str, float] = PydanticField(default_factory=lambda: {"fishing rod": 0.15, "net": 0.25, "basic spear": 0.05})
    
    max_fish_population_factors: Dict[str, float] = PydanticField(default_factory=lambda: {
        "trout": 0.3, "salmon": 0.2, "catfish": 0.25, "minnow": 0.15, "pike": 0.1
    })
    
    # How river depth reacts to precipitation (multiplier on precipitation intensity)
    water_level_precipitation_sensitivity: float = PydanticField(default=0.05)
    # How river temperature reacts to air temperature (0-1, 1 means water temp = air temp quickly)
    water_temperature_sensitivity_to_air: float = PydanticField(default=0.3)
    base_water_temperature_offset: float = PydanticField(default=2.0) # River water often cooler than air in summer, warmer in winter near freezing

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any) -> None:
        if not self.fish_population:
            self._initialize_fish_populations()
        # Initial update based on weather system's starting state
        self.update_conditions_from_weather()


    def _initialize_fish_populations(self) -> None:
        max_pops = self._calculate_max_fish_population_per_species()
        for species_name, max_pop in max_pops.items():
            self.fish_population[species_name] = int(max_pop * random.uniform(0.7, 0.9))

    def update_conditions_from_weather(self) -> None:
        """Updates river's water level and temperature based on the WeatherSystem."""
        if not hasattr(self.weather_system, 'get_current_precipitation_intensity'):
            # print("Warning: WeatherSystem object is not fully featured. Using defaults.")
            # Fallback to avoid errors if a placeholder is used or weather_system is not fully initialized
            estimated_air_temp = 15.0
            precipitation_intensity = 0.0
            current_season = Season.SPRING # Default
        else:
            estimated_air_temp = self.weather_system.get_current_temperature_estimate()
            precipitation_intensity = self.weather_system.get_current_precipitation_intensity()
            current_season = self.weather_system.current_season


        # 1. Update Water Temperature
        # Water temperature moves towards air temperature, influenced by base offset and sensitivity
        temp_diff = estimated_air_temp - (self.current_water_temperature - self.base_water_temperature_offset)
        self.current_water_temperature += temp_diff * self.water_temperature_sensitivity_to_air
        # Clamp water temperature (e.g., 0 to 30 C)
        self.current_water_temperature = max(0.0, min(30.0, self.current_water_temperature))
        if current_season == Season.WINTER and estimated_air_temp < 0:
             self.current_water_temperature = max(-1.0, min(5.0, self.current_water_temperature)) # Allow near freezing

        # 2. Update Water Level
        # Base seasonal multiplier (e.g., spring melt, summer evaporation)
        seasonal_level_mod = {Season.SPRING: 1.05, Season.SUMMER: 0.95, Season.AUTUMN: 1.0, Season.WINTER: 0.98}.get(current_season, 1.0)
        
        precipitation_effect = precipitation_intensity * self.water_level_precipitation_sensitivity
        
        # Evaporation effect (stronger in clear/summer, weaker otherwise)
        evaporation_effect = 0.0
        if hasattr(self.weather_system, 'current_weather_condition') and \
           self.weather_system.current_weather_condition == WeatherCondition.CLEAR and \
           current_season == Season.SUMMER:
            evaporation_effect = -0.02
        
        self.current_water_level_multiplier = seasonal_level_mod + precipitation_effect + evaporation_effect
        self.current_water_level_multiplier = max(0.5, min(2.0, self.current_water_level_multiplier))


    def daily_river_update(self) -> None:
        """
        Called once per day (after WeatherSystem.advance_day()).
        Updates pollution and fish populations.
        Water level and temperature are updated via update_conditions_from_weather,
        which should be called after weather_system.advance_day() and before this.
        """
        self.update_conditions_from_weather() # Ensure river conditions reflect new day's weather

        # Pollution Dissipation
        self.pollution_level = max(0.0, self.pollution_level - self.NATURAL_POLLUTION_DISSIPATION_RATE)
        self.pollution_level = min(1.0, self.pollution_level)

        # Fish Population Replenishment
        max_pops_per_species = self._calculate_max_fish_population_per_species()
        for species_name, current_pop in list(self.fish_population.items()):
            max_pop_for_species = max_pops_per_species.get(species_name, 0)
            min_pop_for_species = int(max_pop_for_species * self.MIN_FISH_PERCENTAGE_OF_MAX)

            if current_pop < max_pop_for_species:
                growth = int(current_pop * self.FISH_REPLENISH_RATE * (1.0 - self.pollution_level * 0.5)) # Pollution impacts growth
                self.fish_population[species_name] = min(max_pop_for_species, current_pop + growth)
            
            if max_pop_for_species > 0 and self.fish_population[species_name] < min_pop_for_species:
                self.fish_population[species_name] = min(min_pop_for_species, max_pop_for_species)
            elif max_pop_for_species == 0:
                self.fish_population[species_name] = 0
        
        # print(f"River {self.name} updated: Water Temp: {self.current_water_temperature:.1f}°C, Water Level Multiplier: {self.current_water_level_multiplier:.2f}, Pollution: {self.pollution_level:.2f}")
        # print(f"  Fish populations: {self.fish_population}")


    def _get_fish_species_definitions(self) -> Dict[str, FishSpecies]:
        return {
            "trout": FishSpecies(name="trout", food_item=fish, rarity=0.7, size_range=(0.5, 2.0), preferred_depth_factor=0.4, active_times=[TimeOfDay.DAWN, TimeOfDay.EVENING], weather_preference=[WeatherCondition.CLOUDY, WeatherCondition.LIGHT_RAIN], temperature_range=(8.0, 18.0), min_skill_required=2, escape_chance=0.3, icon="🐟"),
            "salmon": FishSpecies(name="salmon", food_item=fish, rarity=0.5, size_range=(2.0, 8.0), preferred_depth_factor=0.6, active_times=[TimeOfDay.MORNING, TimeOfDay.EVENING], weather_preference=[WeatherCondition.CLOUDY, WeatherCondition.OVERCAST], temperature_range=(6.0, 16.0), min_skill_required=3, escape_chance=0.4, icon="🎣"),
            "catfish": FishSpecies(name="catfish", food_item=fish, rarity=0.6, size_range=(1.0, 5.0), preferred_depth_factor=0.8, active_times=[TimeOfDay.NIGHT, TimeOfDay.EVENING], weather_preference=[WeatherCondition.OVERCAST, WeatherCondition.LIGHT_RAIN, WeatherCondition.FOGGY], temperature_range=(15.0, 25.0), min_skill_required=2, escape_chance=0.25, icon="🐠"),
            "minnow": FishSpecies(name="minnow", food_item=fish, rarity=0.9, size_range=(0.01, 0.05), preferred_depth_factor=0.2, active_times=[TimeOfDay.MORNING, TimeOfDay.AFTERNOON], weather_preference=[WeatherCondition.CLEAR, WeatherCondition.CLOUDY], temperature_range=(10.0, 22.0), min_skill_required=1, escape_chance=0.5, icon="🦐"),
            "pike": FishSpecies(name="pike", food_item=fish, rarity=0.4, size_range=(1.5, 10.0), preferred_depth_factor=0.5, active_times=[TimeOfDay.MORNING, TimeOfDay.AFTERNOON], weather_preference=[WeatherCondition.CLOUDY, WeatherCondition.FOGGY, WeatherCondition.OVERCAST], temperature_range=(10.0, 20.0), min_skill_required=4, escape_chance=0.35, icon="🦈")
        }

    def _calculate_max_fish_population_per_species(self) -> Dict[str, int]:
        effective_flow = self.base_flow_rate * self.current_water_level_multiplier
        effective_depth = self.base_depth * self.current_water_level_multiplier
        pollution_modifier = (1.0 - self.pollution_level * 0.75)
        
        # Base capacity related to river volume and flow.
        base_capacity_metric = (self.length * effective_depth * effective_flow) / 100.0 # Base unit
        max_total_population = base_capacity_metric * pollution_modifier * 50 # Scaler, needs tuning
        max_total_population = max(0, max_total_population)

        max_indiv_species_pop = {}
        defined_species = self._get_fish_species_definitions()

        for species_name, species_def in defined_species.items():
            factor = self.max_fish_population_factors.get(species_name, 0.05)
            temp_suitability = 0.0
            min_temp, max_temp = species_def.temperature_range
            if min_temp <= self.current_water_temperature <= max_temp: temp_suitability = 1.0
            elif self.current_water_temperature < min_temp - 5 or self.current_water_temperature > max_temp + 5: temp_suitability = 0.0
            else: temp_suitability = 0.3
            
            species_max = int(max_total_population * factor * temp_suitability)
            max_indiv_species_pop[species_name] = species_max
        return max_indiv_species_pop

    def _get_environmental_factors_for_fishing(self, time_of_day_of_attempt: TimeOfDay) -> EnvironmentalFactorsForFishing:
        # Water clarity based on current water level, pollution, and weather
        base_clarity = 0.8
        weather_clarity_mod = { # Modifiers from WeatherCondition (from WeatherSystem)
            WeatherCondition.CLEAR: 1.0, WeatherCondition.CLOUDY: 0.9, WeatherCondition.OVERCAST: 0.8,
            WeatherCondition.LIGHT_RAIN: 0.6, WeatherCondition.HEAVY_RAIN: 0.4, WeatherCondition.STORM: 0.2,
            WeatherCondition.FOGGY: 0.7, WeatherCondition.SNOWY: 0.8, WeatherCondition.BLIZZARD: 0.5, WeatherCondition.HAIL: 0.3
        }.get(self.weather_system.current_weather_condition, 0.8)

        water_level_clarity_mod = 1.0
        if self.current_water_level_multiplier > 1.3: water_level_clarity_mod = 0.7 # High water = murky
        elif self.current_water_level_multiplier < 0.7: water_level_clarity_mod = 0.9 # Low water might be clearer

        water_clarity = base_clarity * weather_clarity_mod * (1.0 - self.pollution_level * 0.8) * water_level_clarity_mod
        water_clarity = max(0.1, min(1.0, water_clarity))

        season_mod = {
            Season.SPRING: 1.1, Season.SUMMER: 1.0, Season.AUTUMN: 1.2, Season.WINTER: 0.7
        }.get(self.weather_system.current_season, 1.0)

        return EnvironmentalFactorsForFishing(
            weather_condition=self.weather_system.current_weather_condition,
            time_of_day=time_of_day_of_attempt,
            water_temperature=self.current_water_temperature,
            water_clarity=water_clarity,
            season_modifier=season_mod,
        )

    def _check_fishing_prerequisites(self, villager: Villager) -> Tuple[bool, str]:
        # (Same as before, no direct weather dependency here)
        if self.villagers_present is None:
            return False, f"{villager.name} must be at the {self.name} to fish."
        if villager.health < 20:
            return False, f"{villager.name} is too weak to fish (health: {villager.health})."
        fishing_skill = villager.skills.get("fishing", 0)
        MIN_REQ_SKILL = 1 # General min skill
        if fishing_skill < MIN_REQ_SKILL: # General min skill
            return False, f"{villager.name} lacks basic fishing skills (requires level {MIN_REQ_SKILL})."
        return True, ""


    def _calculate_catch_probability(
        self, villager: Villager, target_species: FishSpecies, env_factors: EnvironmentalFactorsForFishing
    ) -> float:
        fishing_skill = villager.skills.get("fishing", 0)
        base_prob = self.BASE_CATCH_CHANCE
        skill_bonus = min(fishing_skill * self.SKILL_BONUS_PER_LEVEL, 0.4)

        equipment_bonus = 0.0
        for item_obj in villager.inventory.keys(): # Ensure item_obj is the Item object
             if isinstance(item_obj, Item) and item_obj.name.lower() in self.EQUIPMENT_BONUS:
                equipment_bonus = max(equipment_bonus, self.EQUIPMENT_BONUS[item_obj.name.lower()])
        
        time_bonus = 0.15 if env_factors.time_of_day in target_species.active_times else -0.1
        # Weather preference bonus: if current weather is in species preferred list
        weather_bonus = 0.15 if env_factors.weather_condition in target_species.weather_preference else -0.1
        
        min_temp, max_temp = target_species.temperature_range
        temp_suitability_bonus = 0.0
        if min_temp <= env_factors.water_temperature <= max_temp: temp_suitability_bonus = 0.1
        elif env_factors.water_temperature < min_temp - 3 or env_factors.water_temperature > max_temp + 3: temp_suitability_bonus = -0.2
        else: temp_suitability_bonus = -0.05

        clarity_impact = (env_factors.water_clarity - 0.5) * 0.2 # Max +/- 0.1
        rarity_factor = (1.0 - target_species.rarity) * 0.2
        pollution_penalty = self.pollution_level * 0.4

        total_prob = (
            base_prob + skill_bonus + equipment_bonus + time_bonus + weather_bonus +
            temp_suitability_bonus + clarity_impact - rarity_factor - pollution_penalty
        ) * env_factors.season_modifier
        return max(0.01, min(0.90, total_prob))

    def _attempt_special_catch(self, villager: Villager) -> Optional[Item]:
        special_catch_chance = 0.05 + (self.pollution_level * 0.15) + (villager.skills.get("fishing", 0) * 0.005)
        if random.random() < special_catch_chance:
            if self.pollution_level > 0.6 and random.random() < 0.7: return soggy_boot
            elif self.pollution_level > 0.3 and random.random() < 0.5: return rusty_sword
            elif villager.skills.get("fishing", 0) > 4 and random.random() < 0.3:
                return random.choice([lost_locket, scraps])
            elif random.random() < 0.2: return old_coin
        return None

    def _update_villager_state(self, villager: Villager, result: FishingResult) -> None:
        # (Same as before)
        health_cost = 3 
        if result.success and result.quantity > 0:
            villager.happiness = min(100, villager.happiness + result.quantity * 2)
            skill_gain = 0.05 + (0.02 * result.quantity) 
            current_skill = villager.skills.get("fishing", 0.0)
            villager.skills["fishing"] = round(current_skill + skill_gain, 2)
        else: 
            villager.happiness = max(0, villager.happiness - 1)
            health_cost += 1
        villager.health = max(0, villager.health - health_cost)
        if random.random() < 0.01: 
            accident_damage = random.randint(3, 10)
            villager.health = max(0, villager.health - accident_damage)

    def _update_river_state_post_fishing(self, species_caught_name: str, quantity_caught: int) -> None:
        # (Same as before)
        if species_caught_name in self.fish_population:
            self.fish_population[species_caught_name] = max(0, self.fish_population[species_caught_name] - quantity_caught)
        self.pollution_level = min(1.0, self.pollution_level + (self.POLLUTION_FROM_FISHING_FACTOR * quantity_caught))

    def attempt_fishing(self, villager: Villager, desired_species_name: str, time_of_day_of_attempt: TimeOfDay, hours_fishing: int = 1) -> FishingResult:
        can_fish, reason = self._check_fishing_prerequisites(villager)
        if not can_fish: return FishingResult(success=False, message=reason)

        all_species_defs = self._get_fish_species_definitions()
        if desired_species_name not in all_species_defs:
            return FishingResult(success=False, message=f"Unknown fish species: {desired_species_name}.")
        
        target_species = all_species_defs[desired_species_name]
        fishing_skill = villager.skills.get("fishing", 0)

        if fishing_skill < target_species.min_skill_required:
            return FishingResult(success=False, message=f"{villager.name} needs fishing skill {target_species.min_skill_required} for {desired_species_name}.")

        available_fish_count = self.fish_population.get(desired_species_name, 0)
        if available_fish_count == 0:
            return FishingResult(success=False, message=f"No {desired_species_name} currently in {self.name}.")

        env_factors = self._get_environmental_factors_for_fishing(time_of_day_of_attempt)
        catch_probability_per_hour = self._calculate_catch_probability(villager, target_species, env_factors)

        fish_caught_total = 0
        special_item_found: Optional[Item] = None
        
        MAX_CATCH_LIMIT = 10 # Villager's daily limit, should be tracked on villager
        for _ in range(hours_fishing):
            if random.random() < catch_probability_per_hour:
                if random.random() > target_species.escape_chance:
                    fish_caught_total += 1
                    if fish_caught_total > available_fish_count:
                        fish_caught_total = available_fish_count
                        break 
            if not special_item_found and random.random() < 0.1 * hours_fishing : # Increased chance over longer periods
                 special_item_found = self._attempt_special_catch(villager)
            if fish_caught_total >= MAX_CATCH_LIMIT: break
        
        final_result: FishingResult
        if fish_caught_total > 0:
            fish_food_item = target_species.food_item
            current_inv_count = villager.inventory.get(fish_food_item, 0)
            villager.inventory[fish_food_item] = current_inv_count + fish_caught_total
            msg = f"{villager.name} caught {fish_caught_total} {desired_species_name}(s)."
            if special_item_found:
                special_inv_count = villager.inventory.get(special_item_found, 0)
                villager.inventory[special_item_found] = special_inv_count + 1
                msg += f" Also found a {special_item_found.name}!"
            final_result = FishingResult(success=True, catch=fish_food_item, quantity=fish_caught_total, special_item=special_item_found, message=msg)
            self._update_river_state_post_fishing(desired_species_name, fish_caught_total)
        else:
            msg = f"{villager.name} fished for {desired_species_name} but caught none."
            if special_item_found:
                special_inv_count = villager.inventory.get(special_item_found, 0)
                villager.inventory[special_item_found] = special_inv_count + 1
                msg += f" However, they found a {special_item_found.name}!"
            final_result = FishingResult(success=False, quantity=0, special_item=special_item_found, message=msg)

        self._update_villager_state(villager, final_result)
        return final_result

    def add_villager(self, villager: Villager):
        if villager not in self.villagers_present: self.villagers_present.append(villager)
    def remove_villager(self, villager: Villager):
        if villager in self.villagers_present: self.villagers_present.remove(villager)