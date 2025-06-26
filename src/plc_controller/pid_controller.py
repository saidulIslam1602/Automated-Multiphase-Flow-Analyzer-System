"""
Industrial PID Controller Implementation
Professional-grade PID controller with anti-windup, filtering,
and tuning capabilities for process control applications.
"""

import time
import logging
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PIDParameters:
    """PID controller parameters with industrial features"""
    kp: float = 1.0  # Proportional gain
    ki: float = 0.0  # Integral gain
    kd: float = 0.0  # Derivative gain
    
    # Output limits
    output_min: float = 0.0
    output_max: float = 100.0
    
    # Anti-windup
    integral_limit: float = 100.0
    
    # Derivative filtering (seconds)
    derivative_filter_time: float = 0.1
    
    # Deadband (prevents oscillation around setpoint)
    deadband: float = 0.0
    
    # Sample time (seconds)
    sample_time: float = 0.1

class PIDController:
    """
    Industrial PID Controller with advanced features:
    - Anti-windup protection
    - Derivative filtering
    - Output limiting
    - Bumpless transfer
    - Manual/Auto mode switching
    """
    
    def __init__(self, kp: float = 1.0, ki: float = 0.0, kd: float = 0.0,
                 output_limits: Tuple[float, float] = (0, 100),
                 sample_time: float = 0.1):
        """
        Initialize PID controller
        
        Args:
            kp: Proportional gain
            ki: Integral gain  
            kd: Derivative gain
            output_limits: (min, max) output limits
            sample_time: Controller sample time in seconds
        """
        self.params = PIDParameters(
            kp=kp, ki=ki, kd=kd,
            output_min=output_limits[0],
            output_max=output_limits[1],
            sample_time=sample_time
        )
        
        # Internal state variables
        self._last_error = 0.0
        self._integral = 0.0
        self._last_derivative = 0.0
        self._last_time = None
        self._last_input = 0.0
        
        # Controller status
        self._auto_mode = True
        self._manual_output = 0.0
        self._initialized = False
        
        # Performance monitoring
        self._error_history = []
        self._output_history = []
        
        logger.info(f"PID Controller initialized: Kp={kp}, Ki={ki}, Kd={kd}")
    
    def update(self, error: float, dt: Optional[float] = None) -> float:
        """
        Update PID controller with new error value
        
        Args:
            error: Current error (setpoint - process_value)
            dt: Time step (if None, uses internal timing)
            
        Returns:
            Control output value
        """
        current_time = time.time()
        
        # Handle timing
        if dt is None:
            if self._last_time is None:
                dt = self.params.sample_time
            else:
                dt = current_time - self._last_time
        
        self._last_time = current_time
        
        # Initialize on first run
        if not self._initialized:
            self._last_error = error
            self._initialized = True
            return self._manual_output if not self._auto_mode else 0.0
        
        # Manual mode bypass
        if not self._auto_mode:
            return self._manual_output
        
        # Apply deadband
        if abs(error) < self.params.deadband:
            error = 0.0
        
        # Proportional term
        proportional = self.params.kp * error
        
        # Integral term with anti-windup
        if dt > 0:
            self._integral += error * dt
            
            # Anti-windup: limit integral term
            if self._integral > self.params.integral_limit:
                self._integral = self.params.integral_limit
            elif self._integral < -self.params.integral_limit:
                self._integral = -self.params.integral_limit
        
        integral = self.params.ki * self._integral
        
        # Derivative term with filtering
        if dt > 0:
            derivative_raw = (error - self._last_error) / dt
            
            # Apply first-order filter to derivative
            if self.params.derivative_filter_time > 0:
                alpha = dt / (self.params.derivative_filter_time + dt)
                derivative_filtered = alpha * derivative_raw + (1 - alpha) * self._last_derivative
                self._last_derivative = derivative_filtered
            else:
                derivative_filtered = derivative_raw
                self._last_derivative = derivative_filtered
        else:
            derivative_filtered = 0.0
        
        derivative = self.params.kd * derivative_filtered
        
        # Calculate total output
        output = proportional + integral + derivative
        
        # Apply output limits
        output_limited = self._apply_output_limits(output)
        
        # Integral windup protection (back-calculation)
        if output != output_limited and self.params.ki != 0:
            # Reduce integral term to prevent windup
            integral_correction = (output_limited - output) / self.params.ki
            self._integral += integral_correction * dt
        
        # Store for next iteration
        self._last_error = error
        
        # Performance monitoring
        self._update_performance_history(error, output_limited)
        
        return output_limited
    
    def _apply_output_limits(self, output: float) -> float:
        """Apply output limits with clamping"""
        if output > self.params.output_max:
            return self.params.output_max
        elif output < self.params.output_min:
            return self.params.output_min
        return output
    
    def _update_performance_history(self, error: float, output: float):
        """Update performance monitoring history"""
        max_history = 1000  # Keep last 1000 samples
        
        self._error_history.append(error)
        self._output_history.append(output)
        
        if len(self._error_history) > max_history:
            self._error_history.pop(0)
            self._output_history.pop(0)
    
    def set_parameters(self, kp: Optional[float] = None, 
                      ki: Optional[float] = None, 
                      kd: Optional[float] = None):
        """Update PID parameters"""
        if kp is not None:
            self.params.kp = kp
        if ki is not None:
            self.params.ki = ki
        if kd is not None:
            self.params.kd = kd
        
        logger.info(f"PID parameters updated: Kp={self.params.kp}, Ki={self.params.ki}, Kd={self.params.kd}")
    
    def set_output_limits(self, min_output: float, max_output: float):
        """Set output limits"""
        self.params.output_min = min_output
        self.params.output_max = max_output
        logger.info(f"Output limits set: [{min_output}, {max_output}]")
    
    def set_auto_mode(self, auto: bool, manual_output: float = 0.0):
        """
        Switch between automatic and manual mode
        
        Args:
            auto: True for automatic mode, False for manual
            manual_output: Output value to use in manual mode
        """
        if auto and not self._auto_mode:
            # Switching from manual to auto - bumpless transfer
            self._integral = manual_output / self.params.ki if self.params.ki != 0 else 0
            logger.info("Switched to AUTO mode")
        elif not auto and self._auto_mode:
            # Switching from auto to manual
            self._manual_output = manual_output
            logger.info(f"Switched to MANUAL mode, output={manual_output}")
        
        self._auto_mode = auto
    
    def reset(self):
        """Reset controller internal state"""
        self._last_error = 0.0
        self._integral = 0.0
        self._last_derivative = 0.0
        self._last_time = None
        self._initialized = False
        self._error_history.clear()
        self._output_history.clear()
        logger.info("PID controller reset")
    
    def get_components(self) -> Tuple[float, float, float]:
        """
        Get individual PID components for diagnostics
        
        Returns:
            (proportional, integral, derivative) terms
        """
        return (
            self.params.kp * self._last_error,
            self.params.ki * self._integral,
            self.params.kd * self._last_derivative
        )
    
    def get_performance_metrics(self) -> dict:
        """Get controller performance metrics"""
        if len(self._error_history) < 10:
            return {}
        
        import statistics
        
        recent_errors = self._error_history[-100:]  # Last 100 samples
        
        return {
            'mean_error': statistics.mean(recent_errors),
            'std_error': statistics.stdev(recent_errors),
            'max_error': max(recent_errors),
            'min_error': min(recent_errors),
            'rms_error': (sum(e**2 for e in recent_errors) / len(recent_errors))**0.5,
            'settling_time': self._estimate_settling_time(),
            'overshoot': self._calculate_overshoot()
        }
    
    def _estimate_settling_time(self) -> Optional[float]:
        """Estimate settling time (time to reach within 2% of setpoint)"""
        if len(self._error_history) < 20:
            return None
        
        tolerance = 0.02  # 2% tolerance
        recent_errors = self._error_history[-100:]
        
        for i in range(len(recent_errors) - 10):
            if all(abs(e) < tolerance for e in recent_errors[i:i+10]):
                return (len(recent_errors) - i) * self.params.sample_time
        
        return None
    
    def _calculate_overshoot(self) -> float:
        """Calculate maximum overshoot percentage"""
        if len(self._error_history) < 10:
            return 0.0
        
        # Find maximum negative error (overshoot)
        min_error = min(self._error_history)
        return abs(min_error) if min_error < 0 else 0.0
    
    def auto_tune(self, setpoint: float, process_variable_func, 
                  duration: float = 300.0) -> bool:
        """
        Auto-tune PID parameters using Ziegler-Nichols method
        
        Args:
            setpoint: Target setpoint for tuning
            process_variable_func: Function that returns current process variable
            duration: Tuning duration in seconds
            
        Returns:
            True if tuning successful, False otherwise
        """
        logger.info("Starting PID auto-tuning...")
        
        try:
            # Step 1: Find ultimate gain and period
            ku, tu = self._find_ultimate_parameters(setpoint, process_variable_func, duration)
            
            if ku is None or tu is None:
                logger.error("Auto-tuning failed: Could not determine ultimate parameters")
                return False
            
            # Step 2: Calculate PID parameters using Ziegler-Nichols
            kp = 0.6 * ku
            ki = 2.0 * kp / tu
            kd = kp * tu / 8.0
            
            # Step 3: Apply new parameters
            self.set_parameters(kp, ki, kd)
            
            logger.info(f"Auto-tuning complete: Kp={kp:.3f}, Ki={ki:.3f}, Kd={kd:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Auto-tuning failed: {e}")
            return False
    
    def _find_ultimate_parameters(self, setpoint: float, 
                                process_variable_func, 
                                duration: float) -> Tuple[Optional[float], Optional[float]]:
        """Find ultimate gain and period for Ziegler-Nichols tuning"""
        # This is a simplified implementation
        # In practice, this would involve more sophisticated oscillation detection
        
        # Save current parameters
        original_params = (self.params.kp, self.params.ki, self.params.kd)
        
        try:
            # Set to proportional-only control
            self.set_parameters(kp=1.0, ki=0.0, kd=0.0)
            
            # Gradually increase gain until oscillation
            gain = 1.0
            oscillation_detected = False
            
            while gain < 100.0 and not oscillation_detected:
                self.set_parameters(kp=gain)
                
                # Test for oscillation (simplified)
                oscillation_detected = self._test_for_oscillation(
                    setpoint, process_variable_func, 30.0
                )
                
                if not oscillation_detected:
                    gain *= 1.2
            
            if oscillation_detected:
                ku = gain
                tu = self._measure_oscillation_period()
                return ku, tu
            else:
                return None, None
                
        finally:
            # Restore original parameters
            self.set_parameters(*original_params)
    
    def _test_for_oscillation(self, setpoint: float, 
                            process_variable_func, 
                            test_duration: float) -> bool:
        """Test if the system is oscillating"""
        # Simplified oscillation detection
        # In practice, would use more sophisticated analysis
        
        measurements = []
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            pv = process_variable_func()
            error = setpoint - pv
            output = self.update(error)
            measurements.append(pv)
            time.sleep(self.params.sample_time)
        
        # Simple oscillation detection based on variance
        if len(measurements) < 10:
            return False
        
        import statistics
        variance = statistics.variance(measurements)
        mean_value = statistics.mean(measurements)
        
        # If coefficient of variation is high, assume oscillation
        cv = (variance ** 0.5) / abs(mean_value) if mean_value != 0 else 0
        
        return cv > 0.1  # 10% threshold
    
    def _measure_oscillation_period(self) -> float:
        """Measure the period of oscillation"""
        # Simplified period measurement
        # In practice, would use FFT or zero-crossing detection
        return 2.0 * self.params.sample_time * 50  # Rough estimate
    
    def get_status(self) -> dict:
        """Get controller status information"""
        p, i, d = self.get_components()
        
        return {
            'auto_mode': self._auto_mode,
            'manual_output': self._manual_output,
            'parameters': {
                'kp': self.params.kp,
                'ki': self.params.ki,
                'kd': self.params.kd
            },
            'components': {
                'proportional': p,
                'integral': i,
                'derivative': d
            },
            'integral_value': self._integral,
            'last_error': self._last_error,
            'output_limits': {
                'min': self.params.output_min,
                'max': self.params.output_max
            },
            'sample_time': self.params.sample_time,
            'initialized': self._initialized
        }

# Example usage and testing
if __name__ == "__main__":
    # Test the PID controller
    pid = PIDController(kp=1.0, ki=0.1, kd=0.05, output_limits=(0, 100))
    
    # Simulate a simple process
    setpoint = 50.0
    process_value = 0.0
    
    print("Testing PID Controller:")
    print("Time\tSetpoint\tPV\tError\tOutput")
    
    for i in range(100):
        error = setpoint - process_value
        output = pid.update(error, 0.1)
        
        # Simulate first-order process
        process_value += (output - process_value) * 0.1
        
        if i % 10 == 0:
            print(f"{i*0.1:.1f}\t{setpoint:.1f}\t{process_value:.1f}\t{error:.1f}\t{output:.1f}")
    
    # Show performance metrics
    metrics = pid.get_performance_metrics()
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.3f}") 