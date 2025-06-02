import random
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# --- Enums (could be in a shared 'enums.py' or defined here) ---
class TimeOfDay(Enum):
    """Enumeration of time periods affecting fish activity."""
    DAWN = "dawn"      # e.g., 04:00 - 06:59
    MORNING = "morning"  # e.g., 07:00 - 11:59
    AFTERNOON = "afternoon" # e.g., 12:00 - 16:59
    EVENING = "evening"  # e.g., 17:00 - 20:59
    NIGHT = "night"    # e.g., 21:00 - 03:59

class Season(Enum):
    """Enumeration of seasons."""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

class WeatherCondition(Enum):
    """Enumeration of weather conditions."""
    CLEAR = "clear" # Replaces Sunny for more neutrality
    CLOUDY = "cloudy"
    OVERCAST = "overcast" # Denser clouds than cloudy
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    STORM = "storm" # Thunder, lightning, heavy rain/wind
    FOGGY = "foggy"
    SNOWY = "snowy"
    BLIZZARD = "blizzard" # Heavy snow and wind
    HAIL = "hail"

# --- Weather System Class ---
class WeatherSystem(BaseModel):
    """
    Manages weather simulation with seasonal variations and time-based transitions.

    This class handles the progression of weather conditions, seasons, and time of day
    in a simulated environment. It provides realistic weather transitions based on
    current conditions and seasonal tendencies, along with temperature and precipitation
    calculations.

    Attributes:
        current_hour: Current hour of the day (0-23).
        current_day_in_season: Current day within the active season.
        current_season: Active season from Season enum.
        current_weather_condition: Active weather from WeatherCondition enum.
        days_per_season: Number of days in each season.
        total_days_simulated: Total number of days since simulation start.
        base_weather_transitions: Probability mappings for weather state transitions.
        seasonal_weather_tendencies: Season-specific weather probability multipliers.
        seasonal_avg_temperatures: Base temperature values for each season.
        weather_temperature_modifiers: Temperature adjustments based on weather conditions.
        weather_precipitation_intensity: Precipitation levels for each weather type.
    """
    current_hour: int = Field(default=6)  # 0-23
    current_day_in_season: int = Field(default=1)
    current_season: Season = Field(default=Season.SPRING)
    current_weather_condition: WeatherCondition = Field(default=WeatherCondition.CLOUDY)
    weather_icons: Dict[WeatherCondition, str] = Field(default_factory=lambda: {
        WeatherCondition.CLEAR: "☀️",
        WeatherCondition.CLOUDY: "☁️",
        WeatherCondition.OVERCAST: "🌥️",
        WeatherCondition.LIGHT_RAIN: "🌦️",
        WeatherCondition.HEAVY_RAIN: "🌧️",
        WeatherCondition.STORM: "⛈️",
        WeatherCondition.FOGGY: "🌫️",
        WeatherCondition.SNOWY: "❄️",
        WeatherCondition.BLIZZARD: "🌨️",
        WeatherCondition.HAIL: "🌩️"
    })

    season_icons: Dict[Season, str] = Field(default_factory=lambda: {
        Season.SPRING: "🌸",
        Season.SUMMER: "☀️",
        Season.AUTUMN: "🍂",
        Season.WINTER: "❄️"
    })
    
    days_per_season: int = Field(default=30) # Simplified from 90 for faster testing
    total_days_simulated: int = Field(default=0)

    # Probabilities for weather transitions: {current_weather: {next_weather: probability}}
    # These can be further refined by season.
    base_weather_transitions: Dict[WeatherCondition, Dict[WeatherCondition, float]] = Field(default_factory=lambda: {
        WeatherCondition.CLEAR: {WeatherCondition.CLEAR: 0.6, WeatherCondition.CLOUDY: 0.3, WeatherCondition.LIGHT_RAIN: 0.1},
        WeatherCondition.CLOUDY: {WeatherCondition.CLEAR: 0.2, WeatherCondition.CLOUDY: 0.4, WeatherCondition.OVERCAST: 0.2, WeatherCondition.LIGHT_RAIN: 0.1, WeatherCondition.FOGGY: 0.1},
        WeatherCondition.OVERCAST: {WeatherCondition.CLOUDY: 0.3, WeatherCondition.OVERCAST: 0.4, WeatherCondition.LIGHT_RAIN: 0.2, WeatherCondition.HEAVY_RAIN: 0.1},
        WeatherCondition.LIGHT_RAIN: {WeatherCondition.CLOUDY: 0.4, WeatherCondition.OVERCAST: 0.3, WeatherCondition.LIGHT_RAIN: 0.2, WeatherCondition.HEAVY_RAIN: 0.1},
        WeatherCondition.HEAVY_RAIN: {WeatherCondition.LIGHT_RAIN: 0.4, WeatherCondition.STORM: 0.3, WeatherCondition.OVERCAST: 0.2, WeatherCondition.HEAVY_RAIN: 0.1},
        WeatherCondition.STORM: {WeatherCondition.HEAVY_RAIN: 0.5, WeatherCondition.CLOUDY: 0.3, WeatherCondition.LIGHT_RAIN: 0.2},
        WeatherCondition.FOGGY: {WeatherCondition.CLOUDY: 0.5, WeatherCondition.FOGGY: 0.3, WeatherCondition.CLEAR: 0.2},
        WeatherCondition.SNOWY: {WeatherCondition.CLOUDY: 0.3, WeatherCondition.SNOWY: 0.5, WeatherCondition.BLIZZARD: 0.1, WeatherCondition.CLEAR: 0.1},
        WeatherCondition.BLIZZARD: {WeatherCondition.SNOWY: 0.6, WeatherCondition.CLOUDY: 0.3, WeatherCondition.BLIZZARD: 0.1},
        WeatherCondition.HAIL: {WeatherCondition.STORM: 0.4, WeatherCondition.HEAVY_RAIN: 0.3, WeatherCondition.CLOUDY: 0.3}
    })

    # How much each season influences the probability of certain weather types.
    # Values are multipliers for the base transition probabilities or direct likelihoods.
    seasonal_weather_tendencies: Dict[Season, Dict[WeatherCondition, float]] = Field(default_factory=lambda: {
        Season.SPRING: {WeatherCondition.LIGHT_RAIN: 1.5, WeatherCondition.CLEAR: 1.2, WeatherCondition.SNOWY: 0.2, WeatherCondition.STORM: 1.1},
        Season.SUMMER: {WeatherCondition.CLEAR: 1.8, WeatherCondition.STORM: 1.3, WeatherCondition.HEAVY_RAIN: 0.8, WeatherCondition.SNOWY: 0.01, WeatherCondition.FOGGY: 0.5},
        Season.AUTUMN: {WeatherCondition.CLOUDY: 1.3, WeatherCondition.FOGGY: 1.5, WeatherCondition.LIGHT_RAIN: 1.2, WeatherCondition.CLEAR: 0.8, WeatherCondition.SNOWY: 0.3},
        Season.WINTER: {WeatherCondition.SNOWY: 2.5, WeatherCondition.BLIZZARD: 1.5, WeatherCondition.CLOUDY: 1.2, WeatherCondition.OVERCAST: 1.2, WeatherCondition.CLEAR: 0.5, WeatherCondition.LIGHT_RAIN: 0.5, WeatherCondition.STORM: 0.3}
    })
    
    # Base temperatures for seasons, can be used by River or other entities
    seasonal_avg_temperatures: Dict[Season, float] = Field(default_factory=lambda: {
        Season.SPRING: 12.0, Season.SUMMER: 22.0, Season.AUTUMN: 14.0, Season.WINTER: 2.0
    })

    # Modifiers to temperature based on weather condition
    weather_temperature_modifiers: Dict[WeatherCondition, float] = Field(default_factory=lambda: {
        WeatherCondition.CLEAR: 2.0, WeatherCondition.CLOUDY: 0.0, WeatherCondition.OVERCAST: -1.0,
        WeatherCondition.LIGHT_RAIN: -1.5, WeatherCondition.HEAVY_RAIN: -2.0, WeatherCondition.STORM: -2.5,
        WeatherCondition.FOGGY: -0.5, WeatherCondition.SNOWY: -5.0, WeatherCondition.BLIZZARD: -8.0,
        WeatherCondition.HAIL: -3.0
    })
    
    # Precipitation intensity (0=none, 1=light, 2=medium, 3=heavy)
    weather_precipitation_intensity: Dict[WeatherCondition, float] = Field(default_factory=lambda: {
        WeatherCondition.CLEAR: 0.0, WeatherCondition.CLOUDY: 0.0, WeatherCondition.OVERCAST: 0.1, # Slight drizzle chance
        WeatherCondition.LIGHT_RAIN: 1.0, WeatherCondition.HEAVY_RAIN: 2.0, WeatherCondition.STORM: 3.0,
        WeatherCondition.FOGGY: 0.0, WeatherCondition.SNOWY: 1.5, # Snow equivalent
        WeatherCondition.BLIZZARD: 3.0, WeatherCondition.HAIL: 2.5
    })


    def get_time_of_day(self) -> TimeOfDay:
        """Determines the TimeOfDay enum based on the current_hour."""
        if 4 <= self.current_hour <= 6:
            return TimeOfDay.DAWN
        elif 7 <= self.current_hour <= 11:
            return TimeOfDay.MORNING
        elif 12 <= self.current_hour <= 16:
            return TimeOfDay.AFTERNOON
        elif 17 <= self.current_hour <= 20:
            return TimeOfDay.EVENING
        else: # 21-23 and 0-3
            return TimeOfDay.NIGHT

    def advance_hour(self) -> None:
        """Advances the simulation by one hour."""
        self.current_hour += 1
        if self.current_hour >= 24:
            self.current_hour = 0
            self.advance_day()

    def advance_day(self) -> None:
        """Advances the simulation by one day."""
        self.current_day_in_season += 1
        self.total_days_simulated += 1
        self._update_weather_condition()

        if self.current_day_in_season > self.days_per_season:
            self.current_day_in_season = 1
            self.advance_season()
        
        # print(f"Day {self.total_days_simulated}: Season: {self.current_season.value}, Day in Season: {self.current_day_in_season}, Weather: {self.current_weather_condition.value}")


    def advance_season(self) -> None:
        """Advances to the next season."""
        current_season_index = list(Season).index(self.current_season)
        next_season_index = (current_season_index + 1) % len(list(Season))
        self.current_season = list(Season)[next_season_index]
        # print(f"Season changed to {self.current_season.value}")


    def _update_weather_condition(self) -> None:
        """Updates the weather condition based on transitions and seasonal tendencies."""
        # Get base transitions for the current weather
        base_transitions = self.base_weather_transitions.get(self.current_weather_condition, {})
        if not base_transitions: # Fallback if current weather has no defined transitions
            self.current_weather_condition = random.choice(list(WeatherCondition))
            return

        # Get seasonal tendencies for the current season
        seasonal_tendencies = self.seasonal_weather_tendencies.get(self.current_season, {})

        # Adjust transition probabilities based on seasonal tendencies
        adjusted_transitions: Dict[WeatherCondition, float] = {}
        total_weight = 0.0

        for next_weather, base_prob in base_transitions.items():
            seasonal_multiplier = seasonal_tendencies.get(next_weather, 1.0)
            adjusted_prob = base_prob * seasonal_multiplier
            
            # Ensure SNOWY/BLIZZARD are very unlikely outside of WINTER, or turn into rain
            if next_weather in [WeatherCondition.SNOWY, WeatherCondition.BLIZZARD] and self.current_season != Season.WINTER:
                # Option 1: Drastically reduce probability
                # adjusted_prob *= 0.01
                # Option 2: Convert to a rain equivalent if conditions are not freezing
                # For simplicity, we'll just reduce probability here. A more complex model
                # would check temperature before allowing snow.
                if self.get_current_temperature_estimate() > 2: # If generally not freezing
                    adjusted_prob *= 0.01 # Very low chance
                    # Could add this probability to a rain type instead
                    
            # Ensure HAIL is less common and tied to STORM likelihood
            if next_weather == WeatherCondition.HAIL and self.current_weather_condition != WeatherCondition.STORM:
                adjusted_prob *= 0.1


            adjusted_transitions[next_weather] = adjusted_prob
            total_weight += adjusted_prob
        
        # Normalize probabilities if total_weight is not 0
        if total_weight > 0:
            for weather_cond in adjusted_transitions:
                adjusted_transitions[weather_cond] /= total_weight
        else: # Fallback if all adjusted probabilities become zero
            self.current_weather_condition = random.choice(list(WeatherCondition))
            return


        # Choose next weather based on adjusted probabilities
        rand_val = random.random()
        cumulative_prob = 0.0
        for next_weather, prob in adjusted_transitions.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                self.current_weather_condition = next_weather
                return
        
        # Fallback if something goes wrong (should not happen if probabilities are well-defined)
        if adjusted_transitions:
            self.current_weather_condition = random.choice(list(adjusted_transitions.keys()))
        else: # Ultimate fallback
             self.current_weather_condition = WeatherCondition.CLOUDY


    def get_current_temperature_estimate(self) -> float:
        """Estimates current air temperature based on season and weather."""
        base_seasonal_temp = self.seasonal_avg_temperatures.get(self.current_season, 15.0)
        weather_mod = self.weather_temperature_modifiers.get(self.current_weather_condition, 0.0)
        return base_seasonal_temp + weather_mod

    def get_current_precipitation_intensity(self) -> float:
        """Returns the intensity of precipitation for the current weather."""
        intensity = self.weather_precipitation_intensity.get(self.current_weather_condition, 0.0)
        # Snow in non-winter might be less intense or turn to rain
        if self.current_weather_condition in [WeatherCondition.SNOWY, WeatherCondition.BLIZZARD] and \
           self.current_season != Season.WINTER and self.get_current_temperature_estimate() > 1:
            return intensity * 0.5 # Less effective or melts
        return intensity

    def get_weather_overview(self) -> str:
        """Provides a string summary of the current weather and time."""
        temp_estimate = self.get_current_temperature_estimate()
        return (f"Time: {self.get_time_of_day().value} ({self.current_hour:02d}:00), "
                f"Season: {self.current_season.value} (Day {self.current_day_in_season}/{self.days_per_season}), "
                f"Weather: {self.current_weather_condition.value}, Est. Temp: {temp_estimate:.1f}°C")

