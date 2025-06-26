"""
Safety System for Multiphase Flow Analyzer
Implements safety interlocks and emergency procedures
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SafetyLimits:
    """Safety limits configuration"""
    max_pressure: float = 35.0  # bar
    min_pressure: float = 5.0   # bar
    max_temperature: float = 80.0  # °C
    max_flow_rate: float = 200.0  # m³/h
    max_oil_in_water: float = 1000.0  # ppm

class SafetySystem:
    """
    Safety system for industrial process control
    Implements safety interlocks and trip conditions
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.limits = SafetyLimits(**config)
        self.safety_violations = []
        self.trip_active = False
        
        logger.info("Safety System initialized")
    
    async def check_safety(self, process_variables) -> bool:
        """
        Check all safety conditions
        
        Args:
            process_variables: Current process data
            
        Returns:
            True if safe to operate, False if trip condition
        """
        violations = []
        
        # Pressure safety checks
        if process_variables.pressure_inlet > self.limits.max_pressure:
            violations.append(f"High inlet pressure: {process_variables.pressure_inlet:.1f} bar")
        
        if process_variables.pressure_inlet < self.limits.min_pressure:
            violations.append(f"Low inlet pressure: {process_variables.pressure_inlet:.1f} bar")
        
        # Temperature safety checks
        if process_variables.temperature > self.limits.max_temperature:
            violations.append(f"High temperature: {process_variables.temperature:.1f}°C")
        
        # Flow rate safety checks
        if process_variables.flow_rate > self.limits.max_flow_rate:
            violations.append(f"High flow rate: {process_variables.flow_rate:.1f} m³/h")
        
        # Environmental safety checks
        if process_variables.oil_in_water_ppm > self.limits.max_oil_in_water:
            violations.append(f"High oil in water: {process_variables.oil_in_water_ppm:.1f} ppm")
        
        # Update safety status
        if violations:
            self.safety_violations = violations
            self.trip_active = True
            logger.critical(f"SAFETY TRIP: {violations}")
            return False
        else:
            self.safety_violations = []
            self.trip_active = False
            return True
    
    def reset_safety_system(self):
        """Reset safety system after acknowledging trips"""
        self.safety_violations = []
        self.trip_active = False
        logger.info("Safety system reset")
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety system status"""
        return {
            'trip_active': self.trip_active,
            'violations': self.safety_violations,
            'limits': {
                'max_pressure': self.limits.max_pressure,
                'min_pressure': self.limits.min_pressure,
                'max_temperature': self.limits.max_temperature,
                'max_flow_rate': self.limits.max_flow_rate,
                'max_oil_in_water': self.limits.max_oil_in_water
            }
        } 