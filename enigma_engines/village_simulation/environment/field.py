"""
Field module for agricultural simulation in the village.
"""

from pydantic import BaseModel, Field as PydanticField
from typing import Optional, Dict, List
from datetime import datetime
import random


class Field(BaseModel):
    """Represents an agricultural field in the village."""
    
    # Basic properties
    name: str
    size: float  # hectares
    soil_quality: float = PydanticField(default=0.7, ge=0.0, le=1.0)
    soil_moisture: float = PydanticField(default=0.5, ge=0.0, le=1.0)
    
    # Crop properties
    crop_type: Optional[str] = None
    growth_stage: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    crop_health: float = PydanticField(default=1.0, ge=0.0, le=1.0)
    growth_rate: float = 0.05  # per day
    
    # Management
    fertilizer_level: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    pest_level: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    weed_level: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    
    # Economic
    maintenance_cost: float = 10.0  # per day
    last_harvest: Optional[datetime] = None
    total_yield: float = 0.0
    
    # Indoor flag for weather protection
    is_indoor: bool = False
    
    def plant_crop(self, crop_type: str) -> bool:
        """Plant a new crop in the field."""
        if self.growth_stage > 0.1:
            return False  # Field already has crops
        
        self.crop_type = crop_type
        self.growth_stage = 0.0
        self.crop_health = 1.0
        
        # Different crops have different growth rates
        crop_growth_rates = {
            "wheat": 0.04,
            "vegetables": 0.06,
            "fruits": 0.03,
            "corn": 0.05,
            "potatoes": 0.045
        }
        self.growth_rate = crop_growth_rates.get(crop_type, 0.05)
        
        return True
    
    def update_daily(self) -> None:
        """Update field conditions daily."""
        if self.crop_type and self.growth_stage < 1.0:
            # Growth affected by various factors
            growth_modifier = (
                self.soil_quality * 
                self.soil_moisture * 
                self.crop_health * 
                (1 + self.fertilizer_level * 0.3) *
                (1 - self.pest_level * 0.5) *
                (1 - self.weed_level * 0.3)
            )
            
            self.growth_stage = min(1.0, self.growth_stage + self.growth_rate * growth_modifier)
            
            # Natural degradation
            self.soil_moisture = max(0.0, self.soil_moisture - 0.05)
            self.fertilizer_level = max(0.0, self.fertilizer_level - 0.02)
            
            # Pest and weed growth
            self.pest_level = min(1.0, self.pest_level + random.uniform(0, 0.05))
            self.weed_level = min(1.0, self.weed_level + random.uniform(0, 0.03))
            
            # Crop health affected by conditions
            health_change = 0.0
            if self.soil_moisture < 0.3:
                health_change -= 0.05
            if self.pest_level > 0.5:
                health_change -= 0.03
            if self.weed_level > 0.7:
                health_change -= 0.02
                
            self.crop_health = max(0.0, min(1.0, self.crop_health + health_change))
    
    def apply_fertilizer(self, amount: float) -> None:
        """Apply fertilizer to the field."""
        self.fertilizer_level = min(1.0, self.fertilizer_level + amount)
        self.soil_quality = min(1.0, self.soil_quality + amount * 0.1)
    
    def irrigate(self, water_amount: float) -> None:
        """Irrigate the field."""
        self.soil_moisture = min(1.0, self.soil_moisture + water_amount)
    
    def pest_control(self, effectiveness: float) -> None:
        """Apply pest control measures."""
        self.pest_level = max(0.0, self.pest_level - effectiveness)
    
    def remove_weeds(self, effectiveness: float) -> None:
        """Remove weeds from the field."""
        self.weed_level = max(0.0, self.weed_level - effectiveness)
    
    def harvest(self) -> float:
        """Harvest the crops and return yield."""
        if self.growth_stage < 0.9:
            return 0.0  # Not ready for harvest
        
        # Calculate yield based on various factors
        base_yield = self.size * 1000  # kg per hectare
        yield_modifier = (
            self.crop_health *
            self.soil_quality *
            (1 + self.fertilizer_level * 0.2) *
            min(1.0, self.growth_stage)
        )
        
        # Different crops have different yields
        crop_yield_multipliers = {
            "wheat": 3.0,
            "vegetables": 2.5,
            "fruits": 2.0,
            "corn": 3.5,
            "potatoes": 4.0
        }
        
        crop_multiplier = crop_yield_multipliers.get(self.crop_type, 2.5)
        final_yield = base_yield * yield_modifier * crop_multiplier
        
        # Reset field after harvest
        self.growth_stage = 0.0
        self.crop_health = 1.0
        self.last_harvest = datetime.now()
        self.total_yield += final_yield
        
        # Soil quality decreases after harvest
        self.soil_quality = max(0.3, self.soil_quality - 0.05)
        
        return final_yield
    
    def get_status(self) -> Dict[str, any]:
        """Get current field status."""
        return {
            "name": self.name,
            "size": self.size,
            "crop": self.crop_type,
            "growth": f"{self.growth_stage * 100:.1f}%",
            "health": f"{self.crop_health * 100:.1f}%",
            "soil_quality": f"{self.soil_quality * 100:.1f}%",
            "moisture": f"{self.soil_moisture * 100:.1f}%",
            "pests": f"{self.pest_level * 100:.1f}%",
            "weeds": f"{self.weed_level * 100:.1f}%",
            "ready_to_harvest": self.growth_stage >= 0.9
        }