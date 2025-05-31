from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4

from enigma_engines.village_simulation.environment.villager import Villager
from enigma_engines.animal_crossing.resources.item import Item


class MilitaryRank(str, Enum):
    """Military ranks in hierarchical order."""

    RECRUIT = "recruit"
    PRIVATE = "private"
    CORPORAL = "corporal"
    SERGEANT = "sergeant"
    LIEUTENANT = "lieutenant"
    CAPTAIN = "captain"
    MAJOR = "major"
    COLONEL = "colonel"
    GENERAL = "general"


class UnitType(str, Enum):
    """Types of military units."""

    INFANTRY = "infantry"
    ARCHER = "archer"
    CAVALRY = "cavalry"
    SIEGE = "siege"
    MEDIC = "medic"
    SCOUT = "scout"


class CombatStatus(str, Enum):
    """Combat readiness status."""

    READY = "ready"
    ENGAGED = "engaged"
    RESTING = "resting"
    WOUNDED = "wounded"
    TRAINING = "training"


class Soldier(BaseModel):
    """Enhanced villager with military attributes."""

    villager: Villager
    soldier_id: UUID = Field(default_factory=uuid4)
    rank: MilitaryRank = Field(default=MilitaryRank.RECRUIT)
    unit_type: UnitType
    combat_experience: int = Field(default=0, ge=0)
    morale: float = Field(default=1.0, ge=0.0, le=1.0)
    fatigue: float = Field(default=0.0, ge=0.0, le=1.0)
    status: CombatStatus = Field(default=CombatStatus.READY)
    equipment: List[Item] = Field(default_factory=list)
    assigned_unit: Optional[str] = None
    enlistment_date: datetime = Field(default_factory=datetime.now)
    icon: str = "🪖"  # Default icon for soldier

    @property
    def combat_effectiveness(self) -> float:
        """Calculate soldier's combat effectiveness."""
        base_effectiveness = 0.5
        rank_bonus = list(MilitaryRank).index(self.rank) * 0.05
        experience_bonus = min(self.combat_experience / 100, 0.3)
        morale_factor = self.morale
        fatigue_penalty = 1 - (self.fatigue * 0.5)

        return (
            base_effectiveness
            + rank_bonus
            + experience_bonus * morale_factor * fatigue_penalty
        )

    def can_fight(self) -> bool:
        """Check if soldier is combat-ready."""
        return (
            self.status == CombatStatus.READY
            and self.fatigue < 0.8
            and self.morale > 0.2
        )


class MilitaryUnit(BaseModel):
    """Organizational unit within the army."""

    unit_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    unit_type: UnitType
    commander_id: Optional[UUID] = None
    soldiers: List[UUID] = Field(default_factory=list)
    max_size: int = Field(default=20)
    formation: str = Field(default="standard")

    def is_full(self) -> bool:
        """Check if unit has reached capacity."""
        return len(self.soldiers) >= self.max_size

    def get_strength(self) -> float:
        """Calculate unit strength as percentage."""
        return len(self.soldiers) / self.max_size


class Army(BaseModel):
    """
    Represents the army in the village simulation.
    Army can have different types of soldiers, each with specific roles and attributes.
    Each soldier is a Villager with enhanced combat skills and equipment.
    Army can be used for defense against threats or for offensive actions.
    """

    soldiers: Dict[UUID, Soldier] = Field(default_factory=dict)
    units: Dict[str, MilitaryUnit] = Field(default_factory=dict)
    reserve_pool: Set[UUID] = Field(default_factory=set)
    active_deployments: Dict[str, List[str]] = Field(default_factory=dict)
    supply_inventory: Dict[str, int] = Field(default_factory=dict)
    total_capacity: int = Field(default=100)
    training_queue: List[UUID] = Field(default_factory=list)

    @validator("total_capacity")
    def validate_capacity(cls, v):
        """Ensure army capacity is reasonable."""
        if v < 10:
            raise ValueError("Army capacity must be at least 10")
        if v > 10000:
            raise ValueError("Army capacity cannot exceed 10000")
        return v

    def enlist_villager(
        self, villager: Villager, unit_type: UnitType
    ) -> Optional[Soldier]:
        """Enlist a villager into the army."""
        if len(self.soldiers) >= self.total_capacity:
            return None

        if not self._is_eligible_for_service(villager):
            return None

        soldier = Soldier(villager=villager, unit_type=unit_type)

        self.soldiers[soldier.soldier_id] = soldier
        self.training_queue.append(soldier.soldier_id)

        return soldier

    def _is_eligible_for_service(self, villager: Villager) -> bool:
        """Check if villager meets enlistment criteria."""
        # Add age, health, and other checks based on Villager attributes
        return True  # Simplified for now

    def create_unit(
        self, name: str, unit_type: UnitType, max_size: int = 20
    ) -> Optional[MilitaryUnit]:
        """Create a new military unit."""
        if name in self.units:
            return None

        unit = MilitaryUnit(name=name, unit_type=unit_type, max_size=max_size)

        self.units[unit.unit_id] = unit
        return unit

    def assign_to_unit(self, soldier_id: UUID, unit_id: str) -> bool:
        """Assign a soldier to a specific unit."""
        if soldier_id not in self.soldiers or unit_id not in self.units:
            return False

        soldier = self.soldiers[soldier_id]
        unit = self.units[unit_id]

        if unit.is_full() or soldier.unit_type != unit.unit_type:
            return False

        # Remove from previous unit if assigned
        if soldier.assigned_unit:
            self._remove_from_unit(soldier_id, soldier.assigned_unit)

        soldier.assigned_unit = unit_id
        unit.soldiers.append(soldier_id)

        return True

    def _remove_from_unit(self, soldier_id: UUID, unit_id: str) -> None:
        """Remove soldier from a unit."""
        if unit_id in self.units:
            unit = self.units[unit_id]
            if soldier_id in unit.soldiers:
                unit.soldiers.remove(soldier_id)

    def promote_soldier(self, soldier_id: UUID) -> bool:
        """Promote a soldier to the next rank."""
        if soldier_id not in self.soldiers:
            return False

        soldier = self.soldiers[soldier_id]
        current_rank_index = list(MilitaryRank).index(soldier.rank)

        if current_rank_index >= len(MilitaryRank) - 1:
            return False

        if not self._meets_promotion_criteria(soldier):
            return False

        soldier.rank = list(MilitaryRank)[current_rank_index + 1]
        return True

    def _meets_promotion_criteria(self, soldier: Soldier) -> bool:
        """Check if soldier meets promotion requirements."""
        rank_experience_requirements = {
            MilitaryRank.RECRUIT: 0,
            MilitaryRank.PRIVATE: 10,
            MilitaryRank.CORPORAL: 25,
            MilitaryRank.SERGEANT: 50,
            MilitaryRank.LIEUTENANT: 100,
            MilitaryRank.CAPTAIN: 200,
            MilitaryRank.MAJOR: 400,
            MilitaryRank.COLONEL: 800,
            MilitaryRank.GENERAL: 1600,
        }

        next_rank_index = list(MilitaryRank).index(soldier.rank) + 1
        if next_rank_index >= len(MilitaryRank):
            return False

        next_rank = list(MilitaryRank)[next_rank_index]
        required_experience = rank_experience_requirements.get(next_rank, float("inf"))

        return soldier.combat_experience >= required_experience

    def deploy_unit(self, unit_id: str, location: str) -> bool:
        """Deploy a unit to a specific location."""
        if unit_id not in self.units:
            return False

        unit = self.units[unit_id]
        if not self._is_unit_deployable(unit):
            return False

        if location not in self.active_deployments:
            self.active_deployments[location] = []

        self.active_deployments[location].append(unit_id)
        self._update_unit_status(unit_id, CombatStatus.ENGAGED)

        return True

    def _is_unit_deployable(self, unit: MilitaryUnit) -> bool:
        """Check if unit can be deployed."""
        if unit.get_strength() < 0.5:  # Unit needs at least 50% strength
            return False

        ready_soldiers = sum(
            1
            for soldier_id in unit.soldiers
            if soldier_id in self.soldiers and self.soldiers[soldier_id].can_fight()
        )

        return ready_soldiers >= len(unit.soldiers) * 0.7

    def _update_unit_status(self, unit_id: str, status: CombatStatus) -> None:
        """Update status for all soldiers in a unit."""
        if unit_id not in self.units:
            return

        unit = self.units[unit_id]
        for soldier_id in unit.soldiers:
            if soldier_id in self.soldiers:
                self.soldiers[soldier_id].status = status

    def recall_unit(self, unit_id: str) -> bool:
        """Recall a deployed unit."""
        for location, units in self.active_deployments.items():
            if unit_id in units:
                units.remove(unit_id)
                if not units:
                    del self.active_deployments[location]

                self._update_unit_status(unit_id, CombatStatus.RESTING)
                return True

        return False

    def update_morale(self, morale_change: float) -> None:
        """Update morale for all soldiers."""
        for soldier in self.soldiers.values():
            soldier.morale = max(0.0, min(1.0, soldier.morale + morale_change))

    def rest_soldiers(self, duration_hours: float) -> None:
        """Rest soldiers to reduce fatigue."""
        fatigue_reduction = min(duration_hours * 0.1, 1.0)

        for soldier in self.soldiers.values():
            if soldier.status == CombatStatus.RESTING:
                soldier.fatigue = max(0.0, soldier.fatigue - fatigue_reduction)
                if soldier.fatigue < 0.2:
                    soldier.status = CombatStatus.READY

    def train_soldiers(self) -> Dict[UUID, int]:
        """Conduct training for soldiers in queue."""
        experience_gained = {}

        for soldier_id in self.training_queue[:]:
            if soldier_id in self.soldiers:
                soldier = self.soldiers[soldier_id]
                if soldier.status == CombatStatus.TRAINING:
                    exp_gain = self._calculate_training_experience(soldier)
                    soldier.combat_experience += exp_gain
                    experience_gained[soldier_id] = exp_gain

                    # Graduate from training after sufficient experience
                    if soldier.combat_experience >= 10:
                        soldier.status = CombatStatus.READY
                        self.training_queue.remove(soldier_id)

        return experience_gained

    def _calculate_training_experience(self, soldier: Soldier) -> int:
        """Calculate experience gained from training."""
        base_exp = 2
        rank_multiplier = 1 + (list(MilitaryRank).index(soldier.rank) * 0.1)
        return int(base_exp * rank_multiplier)

    def get_combat_strength(self) -> float:
        """Calculate total combat strength of the army."""
        total_strength = 0.0

        for soldier in self.soldiers.values():
            if soldier.can_fight():
                total_strength += soldier.combat_effectiveness

        return total_strength

    def get_army_statistics(self) -> Dict[str, any]:
        """Get comprehensive army statistics."""
        total_soldiers = len(self.soldiers)
        ready_soldiers = sum(1 for s in self.soldiers.values() if s.can_fight())

        rank_distribution = {}
        unit_type_distribution = {}

        for soldier in self.soldiers.values():
            rank_distribution[soldier.rank] = rank_distribution.get(soldier.rank, 0) + 1
            unit_type_distribution[soldier.unit_type] = (
                unit_type_distribution.get(soldier.unit_type, 0) + 1
            )

        return {
            "total_soldiers": total_soldiers,
            "ready_soldiers": ready_soldiers,
            "total_units": len(self.units),
            "deployed_units": sum(
                len(units) for units in self.active_deployments.values()
            ),
            "combat_strength": self.get_combat_strength(),
            "average_morale": (
                sum(s.morale for s in self.soldiers.values()) / total_soldiers
                if total_soldiers > 0
                else 0
            ),
            "rank_distribution": rank_distribution,
            "unit_type_distribution": unit_type_distribution,
            "capacity_utilization": total_soldiers / self.total_capacity,
        }

    def discharge_soldier(self, soldier_id: UUID) -> Optional[Villager]:
        """Discharge a soldier from service."""
        if soldier_id not in self.soldiers:
            return None

        soldier = self.soldiers[soldier_id]

        # Remove from unit if assigned
        if soldier.assigned_unit:
            self._remove_from_unit(soldier_id, soldier.assigned_unit)

        # Remove from training queue
        if soldier_id in self.training_queue:
            self.training_queue.remove(soldier_id)

        # Remove from reserves
        if soldier_id in self.reserve_pool:
            self.reserve_pool.remove(soldier_id)

        villager = soldier.villager
        del self.soldiers[soldier_id]

        return villager
