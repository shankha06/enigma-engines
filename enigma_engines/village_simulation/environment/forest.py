from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Tuple, Any # Any for WeatherSystem if not strictly typed yet
import random
import math

from enigma_engines.village_simulation.environment.weather import WeatherSystem, TimeOfDay, Season, WeatherCondition

class Forest(BaseModel):
    """
    Represents a forest in the village environment, with dynamic updates
    influenced by a WeatherSystem.
    """
    name: str
    size: float  # square kilometers
    weather_system: WeatherSystem # Should be WeatherSystem, using Any for flexibility if not strictly typed
    icon: str = "🌲"

    # Tree composition and density
    tree_types: Dict[str, float] = Field(default_factory=lambda: {
        "oak": 0.3, "pine": 0.25, "birch": 0.2, "maple": 0.15, "spruce": 0.1
    }) # Represents proportion of species
    
    # Tree populations by age category
    mature_trees: int = Field(default=1000) # Initial values, will be scaled by size
    young_trees: int = Field(default=500)
    saplings: int = Field(default=800)
    
    # Calculated dynamically
    tree_density: float = Field(default=0.0) # Overall tree density (0-1 scale)
    
    # Forest health and environmental state
    health: float = Field(default=0.8, ge=0.0, le=1.0) # Overall forest health
    moisture: float = Field(default=0.6, ge=0.0, le=1.0) # Soil and ground moisture
    soil_fertility: float = Field(default=0.7, ge=0.0, le=1.0)
    undergrowth_density: float = Field(default=0.5, ge=0.0, le=1.0) # Important for some wildlife & fire
    
    # Wildlife - now species-specific populations
    initial_wildlife_species: List[str] = Field(default_factory=lambda: [
        "deer", "rabbit", "fox", "bird", "squirrel", "boar"
    ])
    wildlife_populations: Dict[str, int] = Field(default_factory=dict)

    # Environmental risks
    fire_risk: float = Field(default=0.1, ge=0.0, le=1.0)
    disease_level: float = Field(default=0.05, ge=0.0, le=1.0) # General disease pressure
    pest_infestation: float = Field(default=0.1, ge=0.0, le=1.0) # General pest pressure
    
    # Usage tracking (reset daily)
    daily_trees_cut_count: int = 0 # Renamed for clarity
    
    # Configuration constants (can be tuned)
    MAX_TREES_PER_SQ_KM: int = 1500 # Max potential trees (all ages) for density calculation
    SAPLING_SPAWN_RATE_PER_MATURE_TREE: float = 0.02 # Base rate
    SAPLING_TO_YOUNG_MATURATION_RATE: float = 0.10
    YOUNG_TO_MATURE_MATURATION_RATE: float = 0.05
    BASE_TREE_MORTALITY_RATE: float = 0.005 # For mature trees due to age/natural causes
    WILDLIFE_CARRYING_CAPACITY_PER_SQ_KM: int = 200 # Base for total wildlife units
    WILDLIFE_BASE_REPRODUCTION_RATE: float = 0.15
    WILDLIFE_BASE_MORTALITY_RATE: float = 0.10

    class Config:
        arbitrary_types_allowed = True # To allow WeatherSystem type

    def model_post_init(self, __context: Any) -> None:
        """Initialize dynamic properties after Pydantic model creation."""
        # Scale initial tree counts by forest size for better starting point
        size_factor = self.size / 1.0 # Assuming defaults are for 1 sq km
        self.mature_trees = int(self.mature_trees * size_factor)
        self.young_trees = int(self.young_trees * size_factor)
        self.saplings = int(self.saplings * size_factor)
        
        # Initialize wildlife populations
        if not self.wildlife_populations:
            base_pop_per_species = int((self.WILDLIFE_CARRYING_CAPACITY_PER_SQ_KM * self.size) / len(self.initial_wildlife_species) * 0.5)
            for species in self.initial_wildlife_species:
                self.wildlife_populations[species] = max(5, int(base_pop_per_species * random.uniform(0.7,1.3))) # Ensure some starting pop
        
        self._update_tree_density()
        self.update_daily() # Perform an initial update to set all values based on initial weather

    def _get_current_weather_data(self) -> Tuple[Season, WeatherCondition, float, float]:
        """Helper to get data from WeatherSystem, with fallbacks."""
        if hasattr(self.weather_system, 'current_season'):
            season = self.weather_system.current_season
            condition = self.weather_system.current_weather_condition
            temp = self.weather_system.get_current_temperature_estimate()
            precip = self.weather_system.get_current_precipitation_intensity()
        else: # Fallback if weather_system is a placeholder or not fully equipped
            season = Season.SPRING
            condition = WeatherCondition.CLOUDY
            temp = 15.0
            precip = 0.0
        return season, condition, temp, precip

    def update_daily(self) -> None:
        """Update all forest conditions for a new day, driven by WeatherSystem."""
        season, condition, temperature, precipitation = self._get_current_weather_data()

        self._update_moisture_and_environmental_risks(precipitation, temperature, condition)
        self._update_tree_growth_and_mortality(season, temperature, condition)
        self._update_wildlife_dynamics(season, temperature, condition)
        self._update_disease_and_pests(season, temperature)
        
        self.health = self._calculate_forest_health()
        self._update_tree_density()
        self._update_undergrowth_density(season)

        # Reset daily counters
        self.daily_trees_cut_count = 0
        # self.daily_animals_hunted = 0 # Hunting is external

    def _update_moisture_and_environmental_risks(self, precipitation: float, temperature: float, condition: WeatherCondition) -> None:
        """Update soil moisture, fire risk."""
        # Moisture update
        self.moisture += precipitation * 0.1 # Precipitation effect (scaled)
        evaporation_rate = 0.01 + (max(0, temperature - 10) / 500) # Higher temp, more evaporation
        evaporation_rate *= (1.0 - self.tree_density * 0.5) # Trees provide shade, reduce evaporation
        self.moisture -= evaporation_rate
        self.moisture = max(0.0, min(1.0, self.moisture))

        # Fire Risk update
        dryness_factor = 1.0 - self.moisture
        temp_factor = max(0, temperature - 15) / 20 # Risk increases above 15°C
        undergrowth_factor = self.undergrowth_density * 0.5
        
        self.fire_risk = dryness_factor * 0.5 + temp_factor * 0.3 + undergrowth_factor * 0.2
        if condition == WeatherCondition.STORM: # Storms can initially douse, but lightning is a risk
            self.fire_risk *= 0.5 
            if random.random() < 0.05 : self.fire_risk += 0.3 # Lightning strike chance
        elif condition in [WeatherCondition.LIGHT_RAIN, WeatherCondition.HEAVY_RAIN, WeatherCondition.SNOWY]:
            self.fire_risk *= 0.2 # Rain/snow reduces risk significantly
        
        self.fire_risk = max(0.0, min(1.0, self.fire_risk + random.uniform(-0.05, 0.05)))


    def _update_tree_growth_and_mortality(self, season: Season, temperature: float, condition: WeatherCondition) -> None:
        """Update tree populations: growth, maturation, mortality."""
        
        # Growth season modifier
        growth_season_mod = 0.0
        if season == Season.SPRING: growth_season_mod = 1.0
        elif season == Season.SUMMER: growth_season_mod = 0.8
        elif season == Season.AUTUMN: growth_season_mod = 0.2 # Slowing down
        # Winter: growth_season_mod = 0.0 (dormant)

        # Temperature modifier for growth (optimal range e.g., 10-25°C)
        temp_mod = 0.0
        if 10 <= temperature <= 25: temp_mod = 1.0
        elif 5 <= temperature < 10 or 25 < temperature <= 30: temp_mod = 0.5
        # else: temp_mod = 0.0 (too cold or too hot)

        # Overall growth conditions modifier
        conditions_mod = (
            growth_season_mod * temp_mod * self.health * self.moisture * self.soil_fertility *
            (1.0 - self.tree_density * 0.3) * # Overcrowding penalty
            (1.0 - self.disease_level * 0.5) *
            (1.0 - self.pest_infestation * 0.5)
        )
        conditions_mod = max(0, conditions_mod)

        # 1. New Saplings (from mature trees' seeds)
        new_saplings_count = int(self.mature_trees * self.SAPLING_SPAWN_RATE_PER_MATURE_TREE * conditions_mod * random.uniform(0.8, 1.2))
        self.saplings += new_saplings_count

        # 2. Saplings maturing to Young Trees
        saplings_maturing = int(self.saplings * self.SAPLING_TO_YOUNG_MATURATION_RATE * conditions_mod * random.uniform(0.7, 1.3))
        saplings_maturing = min(saplings_maturing, self.saplings) # Cannot mature more than available
        self.saplings -= saplings_maturing
        self.young_trees += saplings_maturing

        # 3. Young Trees maturing to Mature Trees
        young_maturing = int(self.young_trees * self.YOUNG_TO_MATURE_MATURATION_RATE * conditions_mod * random.uniform(0.7, 1.3))
        young_maturing = min(young_maturing, self.young_trees)
        self.young_trees -= young_maturing
        self.mature_trees += young_maturing

        # 4. Tree Mortality
        # Base mortality + stress factors
        mature_mortality_rate = self.BASE_TREE_MORTALITY_RATE + (1.0 - self.health) * 0.01 + self.disease_level * 0.02 + self.pest_infestation * 0.02
        young_mortality_rate = mature_mortality_rate * 1.5 # Younger trees slightly more vulnerable
        sapling_mortality_rate = mature_mortality_rate * 2.0 # Saplings most vulnerable

        # Extreme weather impact on mortality (simplified)
        if condition == WeatherCondition.BLIZZARD or (season == Season.SUMMER and self.moisture < 0.1 and temperature > 30): # Drought/heatwave
            mature_mortality_rate *= 1.5
            young_mortality_rate *= 2.0
            sapling_mortality_rate *= 2.5
        if condition == WeatherCondition.STORM and random.random() < 0.1: # Chance of some trees falling
             mature_mortality_rate *= 1.2
             young_mortality_rate *= 1.5

        self.mature_trees -= min(self.mature_trees, int(self.mature_trees * mature_mortality_rate * random.uniform(0.8, 1.2)))
        self.young_trees -= min(self.young_trees, int(self.young_trees * young_mortality_rate * random.uniform(0.8, 1.2)))
        self.saplings -= min(self.saplings, int(self.saplings * sapling_mortality_rate * random.uniform(0.8, 1.2)))

        self.mature_trees = max(0, self.mature_trees)
        self.young_trees = max(0, self.young_trees)
        self.saplings = max(0, self.saplings)
        
        # Soil fertility impact from tree lifecycle
        self.soil_fertility -= 0.0001 # Slow degradation from nutrient use
        self.soil_fertility += (mature_mortality_rate * self.mature_trees * 0.00001) # Decomposition adds back
        self.soil_fertility = max(0.1, min(1.0, self.soil_fertility))


    def _update_tree_density(self) -> None:
        """Recalculate tree density."""
        # Weighted sum: mature trees count fully, young 0.5, saplings 0.1 for density
        effective_total_trees = self.mature_trees + self.young_trees * 0.5 + self.saplings * 0.1
        max_possible_trees = self.size * self.MAX_TREES_PER_SQ_KM
        if max_possible_trees > 0:
            self.tree_density = min(1.0, effective_total_trees / max_possible_trees)
        else:
            self.tree_density = 0.0
            
    def _update_undergrowth_density(self, season: Season) -> None:
        """Update undergrowth based on season, moisture, and tree density (light)."""
        growth_mod = 0.0
        if season == Season.SPRING: growth_mod = 0.1
        elif season == Season.SUMMER: growth_mod = 0.05
        elif season == Season.AUTUMN: growth_mod = -0.05
        elif season == Season.WINTER: growth_mod = -0.1
        
        light_factor = 1.0 - self.tree_density * 0.7 # More trees = less light for undergrowth
        
        self.undergrowth_density += (growth_mod * self.moisture * light_factor * self.soil_fertility * random.uniform(0.5, 1.5))
        self.undergrowth_density = max(0.05, min(1.0, self.undergrowth_density))


    def _update_wildlife_dynamics(self, season: Season, temperature: float, condition: WeatherCondition) -> None:
        """Update wildlife populations for each species."""
        # Overall carrying capacity based on forest size, health, and undergrowth (food)
        base_carrying_capacity = self.size * self.WILDLIFE_CARRYING_CAPACITY_PER_SQ_KM
        environmental_capacity_mod = self.health * self.undergrowth_density * (1.0 - self.pest_infestation * 0.3)
        
        # Seasonal impact on carrying capacity (e.g., less food in winter)
        seasonal_capacity_mod = 1.0
        if season == Season.WINTER: seasonal_capacity_mod = 0.4
        elif season == Season.AUTUMN: seasonal_capacity_mod = 0.8
        elif season == Season.SPRING: seasonal_capacity_mod = 1.2 # Abundance

        total_carrying_capacity = int(base_carrying_capacity * environmental_capacity_mod * seasonal_capacity_mod)

        for species_name in list(self.wildlife_populations.keys()):
            current_pop = self.wildlife_populations[species_name]
            if current_pop == 0: continue

            # Species-specific carrying capacity (proportional for now)
            species_carrying_capacity = int(total_carrying_capacity / len(self.wildlife_populations) if self.wildlife_populations else 0)
            species_carrying_capacity = max(1, species_carrying_capacity) # Min capacity if species exists

            # Reproduction rate modifiers
            reproduction_mod = 1.0
            if season == Season.SPRING: reproduction_mod = 1.5 # Breeding season
            elif season == Season.WINTER: reproduction_mod = 0.2 # Low reproduction in winter

            # Mortality rate modifiers
            mortality_mod = 1.0
            if season == Season.WINTER: mortality_mod = 1.8 # Harsher conditions
            if condition == WeatherCondition.BLIZZARD: mortality_mod *= 2.5
            elif condition == WeatherCondition.STORM: mortality_mod *= 1.5
            if self.moisture < 0.1 and temperature > 30 : mortality_mod *= 1.5 # Drought
            
            # Logistic growth: growth_rate * current_pop * (1 - current_pop / capacity)
            births = 0
            if current_pop < species_carrying_capacity:
                 births = int(current_pop * self.WILDLIFE_BASE_REPRODUCTION_RATE * reproduction_mod * (1.0 - current_pop / (species_carrying_capacity + 1)))
                 births = max(0, births)
            
            deaths = int(current_pop * self.WILDLIFE_BASE_MORTALITY_RATE * mortality_mod)
            deaths = max(0, min(current_pop, deaths)) # Cannot have negative population or more deaths than population

            self.wildlife_populations[species_name] = max(0, current_pop + births - deaths)


    def _update_disease_and_pests(self, season: Season, temperature: float) -> None:
        """Update disease and pest levels."""
        # Disease
        disease_spread_factor = self.tree_density * 0.01 * (1.0 - self.health * 0.5)
        if temperature > 5 and temperature < 28: # Favorable temps for many diseases
            self.disease_level += disease_spread_factor * random.uniform(0.5, 1.5)
        else: # Unfavorable temps might slow spread
            self.disease_level += disease_spread_factor * 0.2 * random.uniform(0.5, 1.5)
        
        natural_recovery_disease = 0.01 * self.health # Healthier forests recover faster
        self.disease_level -= natural_recovery_disease
        self.disease_level = max(0.0, min(1.0, self.disease_level))

        # Pests
        pest_activity_mod = 0.0
        if season == Season.SPRING or season == Season.SUMMER: pest_activity_mod = 1.0
        elif season == Season.AUTUMN: pest_activity_mod = 0.5
        # Winter: pest_activity_mod = 0.1 (many dormant)

        pest_spread_factor = (1.0 - self.health) * 0.02 * pest_activity_mod
        self.pest_infestation += pest_spread_factor * random.uniform(0.5, 1.5)
        
        # Natural pest control (e.g. birds, other insects) - simplified
        # More diverse wildlife (higher total pop for now) could mean better pest control
        total_wildlife = sum(self.wildlife_populations.values())
        max_possible_wildlife = self.size * self.WILDLIFE_CARRYING_CAPACITY_PER_SQ_KM
        wildlife_diversity_factor = (total_wildlife / (max_possible_wildlife +1) ) * 0.1

        natural_pest_reduction = 0.005 + wildlife_diversity_factor * 0.01
        self.pest_infestation -= natural_pest_reduction
        self.pest_infestation = max(0.0, min(1.0, self.pest_infestation))


    def _calculate_forest_health(self) -> float:
        """Calculate overall forest health based on multiple factors."""
        # Weighted average of positive and negative factors
        # Positive factors: moisture, soil fertility, healthy tree distribution, wildlife presence
        # Negative factors: disease, pests, extreme density (over or under), fire risk
        
        # Tree age distribution health (ideal is a mix, not too many old/dying, enough young for future)
        total_trees = self.mature_trees + self.young_trees + self.saplings
        if total_trees == 0: tree_dist_health = 0.1
        else:
            mature_ratio = self.mature_trees / total_trees
            young_ratio = self.young_trees / total_trees
            sapling_ratio = self.saplings / total_trees
            # Ideal might be ~0.4 mature, ~0.3 young, ~0.3 saplings. Penalize large deviations.
            tree_dist_health = 1.0 - (abs(mature_ratio - 0.4) + abs(young_ratio - 0.3) + abs(sapling_ratio - 0.3)) * 0.5
            tree_dist_health = max(0.1, tree_dist_health)

        moisture_factor = self.moisture * 1.5 # Moisture is very important
        fertility_factor = self.soil_fertility
        density_factor = (1.0 - abs(self.tree_density - 0.6)) # Ideal density around 0.6-0.7
        
        disease_impact = (1.0 - self.disease_level)
        pest_impact = (1.0 - self.pest_infestation)
        fire_safety = (1.0 - self.fire_risk * 0.5) # Fire risk has some impact on general stress

        # Wildlife as an indicator of ecosystem health
        total_wildlife_pop = sum(self.wildlife_populations.values())
        max_potential_wildlife = self.size * self.WILDLIFE_CARRYING_CAPACITY_PER_SQ_KM
        wildlife_health_indicator = (total_wildlife_pop / (max_potential_wildlife + 1)) * 0.5 + 0.5 # Scale 0.5 to 1.0
        wildlife_health_indicator = min(1.0, wildlife_health_indicator)


        # Combine factors (weights can be tuned)
        calculated_health = (
            tree_dist_health * 0.25 +
            moisture_factor * 0.20 +
            fertility_factor * 0.10 +
            density_factor * 0.10 +
            disease_impact * 0.10 +
            pest_impact * 0.10 +
            fire_safety * 0.05 +
            wildlife_health_indicator * 0.10
        )
        return max(0.05, min(1.0, calculated_health)) # Ensure health is between 0.05 and 1.0
    

    def cut_trees(self, amount_to_cut: int) -> Tuple[int, Dict[str, int]]:
        """
        Cut trees from the forest, prioritizing mature, then young.
        Returns the actual number of trees cut and an estimated breakdown by type.
        """
        if amount_to_cut <= 0:
            return 0, {}

        actually_cut = 0
        
        # Cut from mature trees first
        cut_from_mature = min(amount_to_cut, self.mature_trees)
        self.mature_trees -= cut_from_mature
        actually_cut += cut_from_mature
        
        # If more needed, cut from young trees
        if actually_cut < amount_to_cut:
            needed_from_young = amount_to_cut - actually_cut
            cut_from_young = min(needed_from_young, self.young_trees)
            self.young_trees -= cut_from_young
            actually_cut += cut_from_young
            
        self.daily_trees_cut_count += actually_cut
        self._update_tree_density() # Density changes after cutting
        
        # Estimate types of wood obtained based on current proportions
        # This is an estimation as we don't track types for each age category separately
        wood_yield_by_type: Dict[str, int] = {}
        if actually_cut > 0:
            for tree_type, proportion in self.tree_types.items():
                wood_yield_by_type[tree_type] = int(math.ceil(actually_cut * proportion)) # Ceil to ensure total adds up if proportions are exact

        # Cutting trees can slightly reduce soil fertility and health locally (simplified)
        self.soil_fertility = max(0.1, self.soil_fertility - 0.001 * actually_cut / (self.size * 100 +1))
        self.health = max(0.1, self.health - 0.0005 * actually_cut / (self.size * 100 + 1))

        return actually_cut, wood_yield_by_type

    def get_huntable_wildlife(self) -> Dict[str, int]:
        """Returns a dictionary of wildlife species and their current populations available for hunting."""
        # Could add logic here for minimum populations before a species is "huntable"
        # or if some species are protected/harder to find.
        # For now, just returns current populations.
        return self.wildlife_populations.copy()

    def record_animal_hunted(self, species_name: str, count: int = 1) -> bool:
        """
        Records that an animal of a specific species was hunted.
        This should be called by an external system (e.g., Villager action).
        Returns True if successful (species existed and count was positive), False otherwise.
        """
        if species_name in self.wildlife_populations and self.wildlife_populations[species_name] >= count and count > 0:
            self.wildlife_populations[species_name] -= count
            # self.daily_animals_hunted += count # If tracking total hunted daily
            return True
        return False

    def get_forest_overview(self) -> str:
        """Provides a string summary of the current forest state."""
        overview = (
            f"Forest: {self.name} ({self.size} sq km)\n"
            f"  Health: {self.health:.2f}, Moisture: {self.moisture:.2f}, Soil Fertility: {self.soil_fertility:.2f}\n"
            f"  Tree Density: {self.tree_density:.2f}, Undergrowth: {self.undergrowth_density:.2f}\n"
            f"  Trees: Mature={self.mature_trees}, Young={self.young_trees}, Saplings={self.saplings}\n"
            f"  Wildlife (sample): Deer={self.wildlife_populations.get('deer',0)}, Rabbit={self.wildlife_populations.get('rabbit',0)}\n"
            f"  Risks: Fire={self.fire_risk:.2f}, Disease={self.disease_level:.2f}, Pests={self.pest_infestation:.2f}"
        )
        return overview

# --- Example Usage (Illustrative) ---
if __name__ == "__main__":
    # In a real scenario, import the actual WeatherSystem
    # from weather_system import WeatherSystem, Season, WeatherCondition 
    
    # For this example, we use the placeholder if the actual class isn't in the same file
    world_weather = WeatherSystem() 
    # If WeatherSystem is defined in this file or imported, use:
    # world_weather = WeatherSystem()


    # Create a forest instance
    my_forest = Forest(
        name="Whispering Woods",
        size=5.0, # 5 square kilometers
        weather_system=world_weather,
        mature_trees=2000, # Initial counts before scaling by size in post_init
        young_trees=1000,
        saplings=1500
    )

    print("--- Initial Forest State ---")
    print(my_forest.get_forest_overview())
    if hasattr(world_weather, 'get_weather_overview'):
         print(world_weather.get_weather_overview())
    else: # Placeholder weather system
        print(f"Weather: Season: {world_weather.current_season.value}, Condition: {world_weather.current_weather_condition.value}")


    # Simulate a few days
    for day in range(1, 6):
        print(f"\n--- Day {day} ---")
        # Advance weather (if using the full WeatherSystem class)
        if hasattr(world_weather, 'advance_day'):
            world_weather.advance_day()
            if hasattr(world_weather, 'get_weather_overview'):
                 print(world_weather.get_weather_overview())

        my_forest.update_daily() # Forest updates based on (new) weather
        print(my_forest.get_forest_overview())

        if day == 2:
            print("\nChopping some trees...")
            cut, types = my_forest.cut_trees(50)
            print(f"Actually cut {cut} trees. Estimated types: {types}")
            print(f"Forest state after cutting: Mature={my_forest.mature_trees}, Young={my_forest.young_trees}")
        
        if day == 3 and 'deer' in my_forest.wildlife_populations:
            print("\nHunting a deer...")
            if my_forest.record_animal_hunted("deer", 1):
                print("Successfully recorded 1 deer hunted.")
            else:
                print("Failed to record deer hunt (not enough deer?).")
            print(f"Deer population: {my_forest.wildlife_populations.get('deer', 0)}")


    print("\n--- Simulating a harsher weather period (e.g., drought in summer) ---")
    if hasattr(world_weather, 'current_season'): # Check if full WeatherSystem
        world_weather.current_season = Season.SUMMER
        world_weather.current_weather_condition = WeatherCondition.CLEAR # Hot and clear
        # Manually set precipitation low for placeholder, or let WeatherSystem handle it
        if isinstance(world_weather, WeatherSystem): # if placeholder
             world_weather.get_current_precipitation_intensity = lambda: 0.001 # Very low precip
             world_weather.get_current_temperature_estimate = lambda: 30.0 # Hot

    for i in range(5): # 5 more days
        day +=1
        print(f"\n--- Day {day} (Drought Simulation) ---")
        if hasattr(world_weather, 'advance_day'):
            world_weather.advance_day() # This would normally change weather too
            # For controlled test, we might override weather condition each day if needed
            world_weather.current_weather_condition = WeatherCondition.CLEAR 
            if hasattr(world_weather, 'get_weather_overview'):
                 print(world_weather.get_weather_overview())
        
        my_forest.update_daily()
        print(my_forest.get_forest_overview())