from pydantic import BaseModel
from typing import List, Tuple, Optional
from enigma_engines.village_simulation.agents.villager import Villager


class VillageManager(BaseModel):
    """
    Manages the village simulation, including villagers and their actions.

    """
