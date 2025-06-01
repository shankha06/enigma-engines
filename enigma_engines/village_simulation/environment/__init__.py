"""
Environment module for village simulation.
Contains all environmental components like fields, rivers, forests, vendors, and army.
"""

from .field import Field
from .river import River
from .forest import Forest
from .vendor import Vendor
from .army import Army, UnitType

__all__ = ["Field", "River", "Forest", "Vendor", "Army", "UnitType"]