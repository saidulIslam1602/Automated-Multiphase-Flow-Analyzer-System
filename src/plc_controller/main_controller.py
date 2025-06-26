"""
Main PLC Controller for Automated Multiphase Flow Analyzer System
Simulates industrial PLC programming with real-time control loops,
safety interlocks, and process automation.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import yaml
import json

from .pid_controller import PIDController
from .safety_system import SafetySystem
from .communication import ModbusServer, OPCUAServer
from ..data_management.data_logger import ProcessDataLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessVariables:
    """Process variables similar to PLC memory map"""
    # Input Variables (from field sensors)
    flow_rate: float = 0.0  # m³/h
    pressure_inlet: float = 0.0  # bar
    pressure_outlet: float = 0.0  # bar
    temperature: float = 20.0  # °C
    density_measurement: float = 850.0  # kg/m³
    
    # Calculated Variables
    gas_volume_fraction: float = 0.0  # %
    water_cut: float = 0.0  # %
    oil_in_water_ppm: float = 0.0  # ppm
    
    # Output Variables (to field devices)
    inlet_valve_position: float = 0.0  # % open
    outlet_valve_position: float = 0.0  # % open
    sample_valve_state: bool = False
    pump_speed: float = 0.0  # %
    
    # Control Setpoints
    flow_setpoint: float = 100.0  # m³/h
    pressure_setpoint: float = 25.0  # bar
    temperature_setpoint: float = 60.0  # °C
    
    # System Status
    system_running: bool = False
    emergency_stop: bool = False
    maintenance_mode: bool = False
    alarm_active: bool = False
    
    # Timestamps
    last_update: datetime = field(default_factory=datetime.now)

class PLCController:
    """
    Main PLC Controller class implementing industrial automation logic
    Similar to ladder logic programming in industrial PLCs
    """
    
    def __init__(self, config_file: str = "config/process_config.yaml"):
        self.config = self._load_config(config_file)
        self.pv = ProcessVariables()
        
        # Initialize control components
        self.flow_controller = PIDController(
            kp=self.config['controllers']['flow']['kp'],
            ki=self.config['controllers']['flow']['ki'],
            kd=self.config['controllers']['flow']['kd'],
            output_limits=(0, 100)
        )
        
        self.pressure_controller = PIDController(
            kp=self.config['controllers']['pressure']['kp'],
            ki=self.config['controllers']['pressure']['ki'],
            kd=self.config['controllers']['pressure']['kd'],
            output_limits=(0, 100)
        )
        
        self.safety_system = SafetySystem(self.config['safety'])
        self.data_logger = ProcessDataLogger()
        
        # Communication servers
        self.modbus_server = ModbusServer(port=502)
        self.opcua_server = OPCUAServer()
        
        # Control loop timing
        self.scan_time = self.config.get('scan_time', 0.1)  # 100ms scan time
        self.running = False
        
        logger.info("PLC Controller initialized successfully")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for the system"""
        return {
            'controllers': {
                'flow': {'kp': 1.5, 'ki': 0.3, 'kd': 0.1},
                'pressure': {'kp': 2.0, 'ki': 0.5, 'kd': 0.2}
            },
            'safety': {
                'max_pressure': 35.0,
                'min_pressure': 5.0,
                'max_temperature': 80.0,
                'max_flow_rate': 200.0
            },
            'scan_time': 0.1
        }
    
    async def start_controller(self):
        """Start the main PLC control loop"""
        self.running = True
        logger.info("Starting PLC Controller...")
        
        # Start communication servers
        await self.modbus_server.start()
        await self.opcua_server.start()
        
        # Main control loop
        while self.running:
            cycle_start = time.time()
            
            try:
                # Simulate PLC scan cycle
                await self._input_scan()
                await self._process_logic()
                await self._output_scan()
                await self._communication_update()
                
                # Log process data
                await self._log_data()
                
            except Exception as e:
                logger.error(f"Error in control loop: {e}")
                await self._handle_controller_fault()
            
            # Maintain scan time
            cycle_time = time.time() - cycle_start
            if cycle_time < self.scan_time:
                await asyncio.sleep(self.scan_time - cycle_time)
            else:
                logger.warning(f"Scan overrun: {cycle_time:.3f}s")
    
    async def _input_scan(self):
        """Simulate reading inputs from field devices"""
        # Simulate sensor readings (in real system, would read from hardware)
        import random
        
        if self.pv.system_running:
            # Simulate realistic process variations
            self.pv.flow_rate += random.uniform(-2, 2)
            self.pv.pressure_inlet += random.uniform(-0.5, 0.5)
            self.pv.temperature += random.uniform(-1, 1)
            
            # Keep values within realistic ranges
            self.pv.flow_rate = max(0, min(300, self.pv.flow_rate))
            self.pv.pressure_inlet = max(0, min(50, self.pv.pressure_inlet))
            self.pv.temperature = max(10, min(100, self.pv.temperature))
            
            # Calculate derived measurements
            self._calculate_multiphase_properties()
        
        self.pv.last_update = datetime.now()
    
    def _calculate_multiphase_properties(self):
        """Calculate gas volume fraction and water cut from density"""
        # Simplified multiphase flow calculations
        oil_density = 850  # kg/m³
        water_density = 1000  # kg/m³
        gas_density = 1.2  # kg/m³ at standard conditions
        
        measured_density = self.pv.density_measurement
        
        # Estimate gas volume fraction (simplified calculation)
        if measured_density < oil_density:
            self.pv.gas_volume_fraction = (oil_density - measured_density) / oil_density * 100
        else:
            self.pv.gas_volume_fraction = 0
        
        # Estimate water cut (simplified)
        liquid_density = measured_density * (1 - self.pv.gas_volume_fraction/100)
        if liquid_density > oil_density:
            self.pv.water_cut = (liquid_density - oil_density) / (water_density - oil_density) * 100
        else:
            self.pv.water_cut = 0
        
        # Oil-in-water calculation (simplified)
        if self.pv.water_cut > 50:
            self.pv.oil_in_water_ppm = (100 - self.pv.water_cut) * 10000  # Convert to ppm
        else:
            self.pv.oil_in_water_ppm = 0
    
    async def _process_logic(self):
        """Main process control logic (equivalent to ladder logic)"""
        
        # Safety checks first (similar to safety PLC)
        safety_ok = await self.safety_system.check_safety(self.pv)
        
        if not safety_ok or self.pv.emergency_stop:
            await self._emergency_shutdown()
            return
        
        # Normal operation logic
        if self.pv.system_running and not self.pv.maintenance_mode:
            
            # Flow control loop
            flow_error = self.pv.flow_setpoint - self.pv.flow_rate
            flow_output = self.flow_controller.update(flow_error, self.scan_time)
            self.pv.pump_speed = flow_output
            
            # Pressure control loop
            pressure_error = self.pv.pressure_setpoint - self.pv.pressure_inlet
            pressure_output = self.pressure_controller.update(pressure_error, self.scan_time)
            self.pv.inlet_valve_position = pressure_output
            
            # Automatic sampling logic
            await self._sampling_sequence()
            
            # Quality control checks
            await self._quality_control()
    
    async def _sampling_sequence(self):
        """Automated sampling sequence logic"""
        # Simplified sampling sequence
        current_time = datetime.now()
        
        # Sample every 30 seconds when system is stable
        if (hasattr(self, '_last_sample_time') and 
            (current_time - self._last_sample_time).seconds < 30):
            return
        
        # Check if conditions are stable for sampling
        flow_stable = abs(self.pv.flow_rate - self.pv.flow_setpoint) < 5
        pressure_stable = abs(self.pv.pressure_inlet - self.pv.pressure_setpoint) < 2
        
        if flow_stable and pressure_stable:
            logger.info("Starting automatic sampling sequence")
            
            # Open sample valve for 5 seconds
            self.pv.sample_valve_state = True
            await asyncio.sleep(5)
            self.pv.sample_valve_state = False
            
            self._last_sample_time = current_time
    
    async def _quality_control(self):
        """Quality control and alarm logic"""
        # Check for alarm conditions
        alarms = []
        
        if self.pv.oil_in_water_ppm > 1000:  # Environmental limit
            alarms.append("HIGH_OIL_IN_WATER")
        
        if self.pv.gas_volume_fraction > 95:  # Process limit
            alarms.append("HIGH_GAS_CONTENT")
        
        if self.pv.water_cut > 90:  # Process limit
            alarms.append("HIGH_WATER_CUT")
        
        self.pv.alarm_active = len(alarms) > 0
        
        if alarms:
            logger.warning(f"Process alarms active: {alarms}")
    
    async def _output_scan(self):
        """Write outputs to field devices"""
        # In real system, would write to hardware I/O
        # Here we just update the process variables
        
        # Clamp outputs to safe ranges
        self.pv.pump_speed = max(0, min(100, self.pv.pump_speed))
        self.pv.inlet_valve_position = max(0, min(100, self.pv.inlet_valve_position))
        self.pv.outlet_valve_position = max(0, min(100, self.pv.outlet_valve_position))
    
    async def _communication_update(self):
        """Update communication servers with current data"""
        data_dict = {
            'flow_rate': self.pv.flow_rate,
            'pressure_inlet': self.pv.pressure_inlet,
            'temperature': self.pv.temperature,
            'gas_volume_fraction': self.pv.gas_volume_fraction,
            'water_cut': self.pv.water_cut,
            'oil_in_water_ppm': self.pv.oil_in_water_ppm,
            'system_running': self.pv.system_running,
            'alarm_active': self.pv.alarm_active
        }
        
        await self.modbus_server.update_registers(data_dict)
        await self.opcua_server.update_variables(data_dict)
    
    async def _log_data(self):
        """Log process data to database"""
        await self.data_logger.log_process_data(self.pv)
    
    async def _emergency_shutdown(self):
        """Emergency shutdown sequence"""
        logger.critical("EMERGENCY SHUTDOWN ACTIVATED")
        
        self.pv.system_running = False
        self.pv.pump_speed = 0
        self.pv.sample_valve_state = False
        self.pv.inlet_valve_position = 0  # Close inlet valve
        self.pv.outlet_valve_position = 100  # Open outlet valve for depressurization
    
    async def _handle_controller_fault(self):
        """Handle controller faults"""
        logger.error("Controller fault detected, switching to safe state")
        await self._emergency_shutdown()
    
    def start_system(self):
        """Start the process system"""
        if not self.pv.emergency_stop and not self.pv.maintenance_mode:
            self.pv.system_running = True
            logger.info("Process system started")
    
    def stop_system(self):
        """Stop the process system"""
        self.pv.system_running = False
        logger.info("Process system stopped")
    
    def emergency_stop(self):
        """Activate emergency stop"""
        self.pv.emergency_stop = True
        logger.critical("EMERGENCY STOP ACTIVATED")
    
    def reset_emergency_stop(self):
        """Reset emergency stop"""
        self.pv.emergency_stop = False
        logger.info("Emergency stop reset")
    
    def get_process_data(self) -> Dict[str, Any]:
        """Get current process data for HMI"""
        return {
            'flow_rate': self.pv.flow_rate,
            'pressure_inlet': self.pv.pressure_inlet,
            'pressure_outlet': self.pv.pressure_outlet,
            'temperature': self.pv.temperature,
            'gas_volume_fraction': self.pv.gas_volume_fraction,
            'water_cut': self.pv.water_cut,
            'oil_in_water_ppm': self.pv.oil_in_water_ppm,
            'pump_speed': self.pv.pump_speed,
            'inlet_valve_position': self.pv.inlet_valve_position,
            'sample_valve_state': self.pv.sample_valve_state,
            'system_running': self.pv.system_running,
            'emergency_stop': self.pv.emergency_stop,
            'alarm_active': self.pv.alarm_active,
            'last_update': self.pv.last_update.isoformat()
        }
    
    async def shutdown(self):
        """Graceful shutdown of the controller"""
        logger.info("Shutting down PLC Controller...")
        self.running = False
        await self.modbus_server.stop()
        await self.opcua_server.stop()
        await self.data_logger.close()

# Main execution
async def main():
    """Main function for standalone execution"""
    controller = PLCController()
    
    try:
        await controller.start_controller()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await controller.shutdown()

if __name__ == "__main__":
    asyncio.run(main()) 