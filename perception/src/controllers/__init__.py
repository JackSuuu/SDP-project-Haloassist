"""
Controllers Module
Main system controllers for different hardware configurations
"""
from .hardware_integrated import HardwareIntegratedSystem
from .legacy_system import PerceptionSystem

__all__ = ['HardwareIntegratedSystem', 'PerceptionSystem']
