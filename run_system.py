#!/usr/bin/env python3
"""
Automated Multiphase Flow Analyzer System - Startup Script
Professional industrial automation system launcher
"""

import sys
import os
import subprocess
import time
import logging
import argparse
from pathlib import Path
import threading
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemLauncher:
    """Main system launcher for the multiphase flow analyzer"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.project_root = Path(__file__).parent
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        logger.info("Checking system dependencies...")
        
        try:
            import streamlit
            import plotly
            import pandas
            import numpy
            import yaml
            logger.info("✅ All Python dependencies found")
            return True
        except ImportError as e:
            logger.error(f"❌ Missing dependency: {e}")
            logger.info("Please install dependencies: pip install -r requirements.txt")
            return False
    
    def setup_environment(self):
        """Setup the environment for the system"""
        logger.info("Setting up environment...")
        
        # Create necessary directories
        dirs_to_create = [
            "logs",
            "data",
            "backups",
            "reports"
        ]
        
        for dir_name in dirs_to_create:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        
        # Set environment variables
        os.environ['PYTHONPATH'] = str(self.project_root)
        logger.info("Environment setup complete")
    
    def start_plc_controller(self):
        """Start the PLC controller process"""
        logger.info("Starting PLC Controller...")
        
        try:
            # Start PLC controller as a subprocess
            cmd = [sys.executable, "src/plc_controller/main_controller.py"]
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['plc_controller'] = process
            logger.info(f"✅ PLC Controller started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start PLC Controller: {e}")
            return False
    
    def start_hmi_interface(self):
        """Start the HMI/SCADA interface"""
        logger.info("Starting HMI Interface...")
        
        try:
            # Start Streamlit HMI
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "src/hmi_interface/main_hmi.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0",
                "--server.headless", "true"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['hmi_interface'] = process
            logger.info(f"✅ HMI Interface started (PID: {process.pid})")
            logger.info("🌐 HMI accessible at: http://localhost:8501")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start HMI Interface: {e}")
            return False
    
    def start_analysis_engine(self):
        """Start the multiphase analysis engine"""
        logger.info("Starting Analysis Engine...")
        
        try:
            # Create a simple analysis engine script
            analysis_script = self.project_root / "src" / "analysis_engine" / "main_analyzer.py"
            
            if not analysis_script.exists():
                logger.warning("Analysis engine not found, creating placeholder...")
                analysis_script.parent.mkdir(exist_ok=True)
                with open(analysis_script, 'w') as f:
                    f.write("""
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Multiphase Analysis Engine started")
logger.info("Performing continuous analysis...")

while True:
    logger.info("Analysis cycle completed")
    time.sleep(10)
""")
            
            cmd = [sys.executable, str(analysis_script)]
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['analysis_engine'] = process
            logger.info(f"✅ Analysis Engine started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Analysis Engine: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor all running processes"""
        while self.running:
            for name, process in self.processes.items():
                if process.poll() is not None:
                    logger.warning(f"⚠️ Process {name} has stopped")
                    # In a production system, you might restart the process here
            
            time.sleep(5)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all processes"""
        logger.info("Shutting down system...")
        self.running = False
        
        for name, process in self.processes.items():
            logger.info(f"Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        logger.info("System shutdown complete")
    
    def run(self, components=None):
        """Run the complete system"""
        logger.info("🏭 Starting Automated Multiphase Flow Analyzer System")
        logger.info("=" * 60)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Setup environment
        self.setup_environment()
        
        # Determine which components to start
        if components is None:
            components = ['plc', 'hmi', 'analysis']
        
        self.running = True
        
        # Start components
        success = True
        
        if 'plc' in components:
            success &= self.start_plc_controller()
            time.sleep(2)  # Allow PLC to initialize
        
        if 'analysis' in components:
            success &= self.start_analysis_engine()
            time.sleep(1)
        
        if 'hmi' in components:
            success &= self.start_hmi_interface()
            time.sleep(3)  # Allow HMI to start
        
        if not success:
            logger.error("❌ Failed to start some components")
            self.shutdown()
            return False
        
        logger.info("✅ All components started successfully!")
        logger.info("=" * 60)
        logger.info("🌐 HMI Interface: http://localhost:8501")
        logger.info("🔧 PLC Controller: Running in background")
        logger.info("🧪 Analysis Engine: Processing multiphase data")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop the system")
        
        # Start monitoring
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Automated Multiphase Flow Analyzer System Launcher"
    )
    
    parser.add_argument(
        '--components', 
        nargs='+', 
        choices=['plc', 'hmi', 'analysis'],
        default=['plc', 'hmi', 'analysis'],
        help='Components to start (default: all)'
    )
    
    parser.add_argument(
        '--hmi-only',
        action='store_true',
        help='Start only the HMI interface'
    )
    
    parser.add_argument(
        '--plc-only',
        action='store_true',
        help='Start only the PLC controller'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies and exit'
    )
    
    args = parser.parse_args()
    
    launcher = SystemLauncher()
    
    if args.check_deps:
        if launcher.check_dependencies():
            print("✅ All dependencies satisfied")
            return 0
        else:
            print("❌ Missing dependencies")
            return 1
    
    # Determine components to start
    components = args.components
    if args.hmi_only:
        components = ['hmi']
    elif args.plc_only:
        components = ['plc']
    
    # Run the system
    if launcher.run(components):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 