"""
Professional HMI/SCADA Interface for Multiphase Flow Analyzer
Industrial-style interface with P&ID graphics, real-time monitoring,
alarm management, and operator controls.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure page
st.set_page_config(
    page_title="Multiphase Flow Analyzer - HMI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Industrial color scheme
COLORS = {
    'primary': '#1f4e79',
    'secondary': '#2e75b6',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'background': '#2c3e50',
    'text': '#ffffff'
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HMIInterface:
    """Main HMI Interface class for the multiphase flow analyzer"""
    
    def __init__(self):
        self.init_session_state()
        self.setup_styling()
    
    def init_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'connected' not in st.session_state:
            st.session_state.connected = False
        if 'alarm_history' not in st.session_state:
            st.session_state.alarm_history = []
        if 'process_data' not in st.session_state:
            st.session_state.process_data = self.get_default_process_data()
        if 'historical_data' not in st.session_state:
            st.session_state.historical_data = pd.DataFrame()
    
    def setup_styling(self):
        """Apply industrial-style CSS"""
        st.markdown("""
        <style>
        /* Industrial Dark Theme */
        .main > div {
            background-color: #2c3e50;
            color: #ffffff;
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e75b6 100%);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        /* Process value styling */
        .process-value {
            background-color: #34495e;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            margin: 0.5rem 0;
        }
        
        .process-value.alarm {
            border-left-color: #e74c3c;
            background-color: #4a2c2a;
        }
        
        .process-value.warning {
            border-left-color: #f39c12;
            background-color: #4a3c2a;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }
        
        .stButton > button:hover {
            background-color: #2980b9;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #34495e;
        }
        
        /* Alarm styling */
        .alarm-critical {
            background-color: #e74c3c;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.2rem 0;
        }
        
        .alarm-warning {
            background-color: #f39c12;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.2rem 0;
        }
        
        /* Status indicators */
        .status-running {
            color: #27ae60;
            font-weight: bold;
        }
        
        .status-stopped {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .status-maintenance {
            color: #f39c12;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def get_default_process_data(self) -> Dict[str, Any]:
        """Get default process data structure"""
        return {
            'flow_rate': 85.2,
            'pressure_inlet': 24.8,
            'pressure_outlet': 18.5,
            'temperature': 58.7,
            'gas_volume_fraction': 12.3,
            'water_cut': 35.7,
            'oil_in_water_ppm': 850.0,
            'pump_speed': 75.5,
            'inlet_valve_position': 68.2,
            'outlet_valve_position': 45.8,
            'sample_valve_state': False,
            'system_running': True,
            'emergency_stop': False,
            'alarm_active': False,
            'last_update': datetime.now().isoformat()
        }
    
    def render_header(self):
        """Render the main header"""
        st.markdown("""
        <div class="main-header">
            <h1>🏭 Automated Multiphase Flow Analyzer System</h1>
            <h3>Professional Industrial Control Interface</h3>
            <p>Real-time monitoring and control of oil-gas-water separation process</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_system_status(self):
        """Render system status indicators"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "RUNNING" if st.session_state.process_data['system_running'] else "STOPPED"
            status_class = "status-running" if st.session_state.process_data['system_running'] else "status-stopped"
            st.markdown(f'<p class="{status_class}">🔄 System: {status}</p>', unsafe_allow_html=True)
        
        with col2:
            connection_status = "ONLINE" if st.session_state.connected else "OFFLINE"
            connection_class = "status-running" if st.session_state.connected else "status-stopped"
            st.markdown(f'<p class="{connection_class}">📡 Connection: {connection_status}</p>', unsafe_allow_html=True)
        
        with col3:
            alarm_status = "ACTIVE" if st.session_state.process_data['alarm_active'] else "NORMAL"
            alarm_class = "status-stopped" if st.session_state.process_data['alarm_active'] else "status-running"
            st.markdown(f'<p class="{alarm_class}">🚨 Alarms: {alarm_status}</p>', unsafe_allow_html=True)
        
        with col4:
            emergency_status = "ACTIVE" if st.session_state.process_data['emergency_stop'] else "NORMAL"
            emergency_class = "status-stopped" if st.session_state.process_data['emergency_stop'] else "status-running"
            st.markdown(f'<p class="{emergency_class}">🛑 E-Stop: {emergency_status}</p>', unsafe_allow_html=True)
    
    def render_process_overview(self):
        """Render P&ID-style process overview"""
        st.subheader("📊 Process Flow Diagram")
        
        # Create process flow visualization
        fig = go.Figure()
        
        # Add process equipment shapes
        # Inlet
        fig.add_shape(
            type="rect", x0=0, y0=0.4, x1=0.2, y1=0.6,
            line=dict(color="white", width=2), fillcolor="lightblue"
        )
        fig.add_annotation(x=0.1, y=0.5, text="INLET", showarrow=False, font=dict(color="black"))
        
        # Analyzer
        fig.add_shape(
            type="circle", x0=0.4, y0=0.3, x1=0.6, y1=0.7,
            line=dict(color="white", width=2), fillcolor="lightgreen"
        )
        fig.add_annotation(x=0.5, y=0.5, text="ANALYZER", showarrow=False, font=dict(color="black"))
        
        # Outlet
        fig.add_shape(
            type="rect", x0=0.8, y0=0.4, x1=1.0, y1=0.6,
            line=dict(color="white", width=2), fillcolor="lightcoral"
        )
        fig.add_annotation(x=0.9, y=0.5, text="OUTLET", showarrow=False, font=dict(color="black"))
        
        # Add flow lines
        fig.add_shape(type="line", x0=0.2, y0=0.5, x1=0.4, y1=0.5, line=dict(color="cyan", width=3))
        fig.add_shape(type="line", x0=0.6, y0=0.5, x1=0.8, y1=0.5, line=dict(color="cyan", width=3))
        
        # Add valves
        valve_inlet = "🟢" if st.session_state.process_data['inlet_valve_position'] > 50 else "🔴"
        valve_outlet = "🟢" if st.session_state.process_data['outlet_valve_position'] > 50 else "🔴"
        
        fig.add_annotation(x=0.3, y=0.55, text=valve_inlet, showarrow=False, font=dict(size=20))
        fig.add_annotation(x=0.7, y=0.55, text=valve_outlet, showarrow=False, font=dict(size=20))
        
        # Add process values
        fig.add_annotation(
            x=0.1, y=0.7, 
            text=f"Flow: {st.session_state.process_data['flow_rate']:.1f} m³/h", 
            showarrow=False, font=dict(color="white")
        )
        fig.add_annotation(
            x=0.5, y=0.8, 
            text=f"Pressure: {st.session_state.process_data['pressure_inlet']:.1f} bar", 
            showarrow=False, font=dict(color="white")
        )
        fig.add_annotation(
            x=0.9, y=0.7, 
            text=f"Temp: {st.session_state.process_data['temperature']:.1f}°C", 
            showarrow=False, font=dict(color="white")
        )
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_process_variables(self):
        """Render real-time process variables"""
        st.subheader("📈 Process Variables")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Flow & Pressure**")
            self.render_gauge("Flow Rate", st.session_state.process_data['flow_rate'], "m³/h", 0, 200)
            self.render_gauge("Inlet Pressure", st.session_state.process_data['pressure_inlet'], "bar", 0, 50)
            self.render_gauge("Outlet Pressure", st.session_state.process_data['pressure_outlet'], "bar", 0, 50)
        
        with col2:
            st.markdown("**Multiphase Analysis**")
            self.render_gauge("Gas Volume Fraction", st.session_state.process_data['gas_volume_fraction'], "%", 0, 100)
            self.render_gauge("Water Cut", st.session_state.process_data['water_cut'], "%", 0, 100)
            self.render_gauge("Oil in Water", st.session_state.process_data['oil_in_water_ppm'], "ppm", 0, 2000)
        
        with col3:
            st.markdown("**Control Outputs**")
            self.render_gauge("Pump Speed", st.session_state.process_data['pump_speed'], "%", 0, 100)
            self.render_gauge("Inlet Valve", st.session_state.process_data['inlet_valve_position'], "%", 0, 100)
            st.markdown(f"**Sample Valve:** {'🟢 OPEN' if st.session_state.process_data['sample_valve_state'] else '🔴 CLOSED'}")
    
    def render_gauge(self, title: str, value: float, unit: str, min_val: float, max_val: float):
        """Render a gauge chart for process variables"""
        # Determine color based on value range
        if value < 0.3 * max_val:
            color = "#27ae60"  # Green
        elif value < 0.7 * max_val:
            color = "#f39c12"  # Orange
        else:
            color = "#e74c3c"  # Red
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"{title} ({unit})"},
            gauge = {
                'axis': {'range': [None, max_val]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 0.3 * max_val], 'color': "lightgray"},
                    {'range': [0.3 * max_val, 0.7 * max_val], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.9 * max_val
                }
            }
        ))
        
        fig.update_layout(
            height=200,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_trend_charts(self):
        """Render historical trend charts"""
        st.subheader("📊 Historical Trends")
        
        # Generate sample historical data if empty
        if st.session_state.historical_data.empty:
            self.generate_sample_historical_data()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Flow Rate", "Pressure", "Gas Volume Fraction", "Water Cut"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        df = st.session_state.historical_data
        
        # Flow rate
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['flow_rate'], name="Flow Rate"),
            row=1, col=1
        )
        
        # Pressure
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['pressure_inlet'], name="Inlet Pressure"),
            row=1, col=2
        )
        
        # Gas Volume Fraction
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['gas_volume_fraction'], name="Gas Volume Fraction"),
            row=2, col=1
        )
        
        # Water Cut
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['water_cut'], name="Water Cut"),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def generate_sample_historical_data(self):
        """Generate sample historical data for demonstration"""
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(hours=2),
            end=datetime.now(),
            freq='1min'
        )
        
        np.random.seed(42)
        n_points = len(timestamps)
        
        data = {
            'timestamp': timestamps,
            'flow_rate': 80 + 10 * np.sin(np.linspace(0, 4*np.pi, n_points)) + np.random.normal(0, 2, n_points),
            'pressure_inlet': 25 + 3 * np.sin(np.linspace(0, 6*np.pi, n_points)) + np.random.normal(0, 0.5, n_points),
            'temperature': 60 + 5 * np.sin(np.linspace(0, 2*np.pi, n_points)) + np.random.normal(0, 1, n_points),
            'gas_volume_fraction': 15 + 5 * np.sin(np.linspace(0, 8*np.pi, n_points)) + np.random.normal(0, 1, n_points),
            'water_cut': 35 + 10 * np.sin(np.linspace(0, 3*np.pi, n_points)) + np.random.normal(0, 2, n_points),
            'oil_in_water_ppm': 800 + 200 * np.sin(np.linspace(0, 5*np.pi, n_points)) + np.random.normal(0, 50, n_points)
        }
        
        st.session_state.historical_data = pd.DataFrame(data)
    
    def render_alarm_panel(self):
        """Render alarm management panel"""
        st.subheader("🚨 Alarm Management")
        
        # Sample alarms
        active_alarms = [
            {"level": "WARNING", "message": "Oil in Water concentration approaching limit", "time": "10:15:32"},
            {"level": "INFO", "message": "Automatic sampling completed", "time": "10:10:15"}
        ]
        
        if st.session_state.process_data['alarm_active']:
            active_alarms.append({
                "level": "ALARM", 
                "message": "High gas volume fraction detected", 
                "time": datetime.now().strftime("%H:%M:%S")
            })
        
        for alarm in active_alarms:
            if alarm["level"] == "ALARM":
                st.markdown(f'<div class="alarm-critical">🚨 {alarm["time"]} - {alarm["message"]}</div>', unsafe_allow_html=True)
            elif alarm["level"] == "WARNING":
                st.markdown(f'<div class="alarm-warning">⚠️ {alarm["time"]} - {alarm["message"]}</div>', unsafe_allow_html=True)
            else:
                st.info(f"ℹ️ {alarm['time']} - {alarm['message']}")
    
    def render_control_panel(self):
        """Render operator control panel"""
        st.subheader("🎛️ Operator Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**System Control**")
            if st.button("▶️ START SYSTEM", disabled=st.session_state.process_data['system_running']):
                st.session_state.process_data['system_running'] = True
                st.success("System started")
                st.rerun()
            
            if st.button("⏹️ STOP SYSTEM", disabled=not st.session_state.process_data['system_running']):
                st.session_state.process_data['system_running'] = False
                st.info("System stopped")
                st.rerun()
            
            if st.button("🛑 EMERGENCY STOP"):
                st.session_state.process_data['emergency_stop'] = True
                st.session_state.process_data['system_running'] = False
                st.error("EMERGENCY STOP ACTIVATED!")
                st.rerun()
        
        with col2:
            st.markdown("**Setpoints**")
            flow_setpoint = st.number_input("Flow Setpoint (m³/h)", min_value=0.0, max_value=200.0, value=100.0, step=5.0)
            pressure_setpoint = st.number_input("Pressure Setpoint (bar)", min_value=0.0, max_value=50.0, value=25.0, step=1.0)
            temp_setpoint = st.number_input("Temperature Setpoint (°C)", min_value=20.0, max_value=100.0, value=60.0, step=2.0)
        
        with col3:
            st.markdown("**Manual Operations**")
            if st.button("🔄 Sample Now"):
                st.session_state.process_data['sample_valve_state'] = True
                st.success("Manual sampling initiated")
                # Auto-close after 5 seconds (in real system)
            
            if st.button("🔧 Reset Alarms"):
                st.session_state.process_data['alarm_active'] = False
                st.success("Alarms acknowledged")
                st.rerun()
            
            if st.button("🔓 Reset E-Stop"):
                st.session_state.process_data['emergency_stop'] = False
                st.success("Emergency stop reset")
                st.rerun()
    
    def render_sidebar(self):
        """Render sidebar with navigation and settings"""
        with st.sidebar:
            st.markdown("## 🏭 Navigation")
            
            # Connection status
            if st.button("🔌 Connect to PLC"):
                st.session_state.connected = True
                st.success("Connected to PLC")
            
            if st.button("🔌 Disconnect"):
                st.session_state.connected = False
                st.warning("Disconnected from PLC")
            
            st.markdown("---")
            
            # System information
            st.markdown("## ℹ️ System Info")
            st.markdown(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
            st.markdown(f"**Scan Rate:** 100 ms")
            st.markdown(f"**PLC Status:** {'Online' if st.session_state.connected else 'Offline'}")
            
            st.markdown("---")
            
            # Configuration
            st.markdown("## ⚙️ Settings")
            auto_refresh = st.checkbox("Auto Refresh", value=True)
            refresh_rate = st.slider("Refresh Rate (s)", min_value=1, max_value=10, value=2)
            
            if auto_refresh:
                time.sleep(refresh_rate)
                st.rerun()
            
            st.markdown("---")
            
            # Quick actions
            st.markdown("## 🚀 Quick Actions")
            if st.button("📊 Export Data"):
                st.download_button(
                    label="Download CSV",
                    data=st.session_state.historical_data.to_csv(index=False),
                    file_name=f"process_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            if st.button("📋 Generate Report"):
                st.info("Report generation initiated")
            
            if st.button("🔄 Simulate Data"):
                self.simulate_live_data()
                st.success("Data simulated")
    
    def simulate_live_data(self):
        """Simulate live process data changes"""
        import random
        
        # Add some realistic variations
        data = st.session_state.process_data
        
        if data['system_running']:
            data['flow_rate'] += random.uniform(-2, 2)
            data['pressure_inlet'] += random.uniform(-0.5, 0.5)
            data['temperature'] += random.uniform(-1, 1)
            data['gas_volume_fraction'] += random.uniform(-1, 1)
            data['water_cut'] += random.uniform(-2, 2)
            data['oil_in_water_ppm'] += random.uniform(-50, 50)
            
            # Keep values in realistic ranges
            data['flow_rate'] = max(0, min(200, data['flow_rate']))
            data['pressure_inlet'] = max(0, min(50, data['pressure_inlet']))
            data['temperature'] = max(20, min(100, data['temperature']))
            data['gas_volume_fraction'] = max(0, min(100, data['gas_volume_fraction']))
            data['water_cut'] = max(0, min(100, data['water_cut']))
            data['oil_in_water_ppm'] = max(0, min(2000, data['oil_in_water_ppm']))
            
            # Check for alarm conditions
            if data['oil_in_water_ppm'] > 1000 or data['gas_volume_fraction'] > 90:
                data['alarm_active'] = True
            else:
                data['alarm_active'] = False
        
        data['last_update'] = datetime.now().isoformat()
    
    def run(self):
        """Main application runner"""
        # Render the interface
        self.render_header()
        self.render_system_status()
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏭 Process Overview", 
            "📊 Live Data", 
            "📈 Trends", 
            "🚨 Alarms", 
            "🎛️ Controls"
        ])
        
        with tab1:
            self.render_process_overview()
            self.render_process_variables()
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Current Values")
                df_current = pd.DataFrame([st.session_state.process_data]).T
                df_current.columns = ['Value']
                df_current.index.name = 'Parameter'
                st.dataframe(df_current, use_container_width=True)
            
            with col2:
                st.subheader("🔄 Live Updates")
                if st.button("🔄 Refresh Data"):
                    self.simulate_live_data()
                    st.rerun()
                
                st.json(st.session_state.process_data)
        
        with tab3:
            self.render_trend_charts()
        
        with tab4:
            self.render_alarm_panel()
        
        with tab5:
            self.render_control_panel()
        
        # Render sidebar
        self.render_sidebar()

# Main application
def main():
    """Main application entry point"""
    hmi = HMIInterface()
    hmi.run()

if __name__ == "__main__":
    main() 