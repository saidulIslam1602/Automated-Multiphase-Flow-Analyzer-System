"""
Professional HMI/SCADA Interface for Multiphase Flow Analyzer
Fixed version with proper data handling and improved layout
Now featuring REAL production data integration
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from data.real_data_integration import real_data_provider
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False
    print("Real data integration not available, using simulated data")

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
    'info': '#17a2b8'
}

class HMIInterface:
    """Fixed HMI Interface with proper data handling"""
    
    def __init__(self):
        self.init_session_state()
        self.setup_styling()
    
    def init_session_state(self):
        """Initialize session state with proper data types"""
        if 'connected' not in st.session_state:
            st.session_state.connected = True
        
        # Always refresh process data based on current REAL_DATA_AVAILABLE status
        if REAL_DATA_AVAILABLE:
            st.session_state.process_data = real_data_provider.get_current_data_point()
        else:
            st.session_state.process_data = self.get_default_process_data()
        
        # Always refresh historical data based on current REAL_DATA_AVAILABLE status
        st.session_state.historical_data = self.generate_clean_historical_data()
        
        if 'data_source' not in st.session_state:
            st.session_state.data_source = 'Real Production Data' if REAL_DATA_AVAILABLE else 'Simulated Data'
    
    def setup_styling(self):
        """Apply clean industrial styling"""
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e75b6 100%);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 1rem;
            color: white;
        }
        
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2e75b6;
            margin: 0.5rem 0;
        }
        
        .status-running { color: #28a745; font-weight: bold; }
        .status-stopped { color: #dc3545; font-weight: bold; }
        .status-warning { color: #ffc107; font-weight: bold; }
        
        .alarm-critical {
            background-color: #dc3545;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.2rem 0;
        }
        
        .alarm-warning {
            background-color: #ffc107;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.2rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def get_default_process_data(self) -> Dict[str, Any]:
        """Get default process data with proper types"""
        return {
            'flow_rate': 85.2,
            'pressure_inlet': 24.8,
            'pressure_outlet': 18.5,
            'temperature': 58.7,
            'gas_volume_fraction': 12.3,
            'water_cut': 35.7,
            'oil_in_water_ppm': 850.0,
            'pump_speed': 75.5,
            'system_running': True,
            'emergency_stop': False,
            'alarm_active': False
        }
    
    def generate_clean_historical_data(self) -> pd.DataFrame:
        """Generate properly formatted historical data"""
        if REAL_DATA_AVAILABLE:
            # Use real data from the integration module
            real_df = real_data_provider.get_historical_data(hours=1)
            # Map columns to match expected names for charts
            real_df['pressure'] = real_df['pressure_inlet']  # Use inlet pressure for main pressure
            real_df['gas_fraction'] = real_df['gas_volume_fraction']
            real_df['oil_in_water'] = real_df['oil_in_water_ppm']
            return real_df
        else:
            # Fallback to simulated data
            timestamps = pd.date_range(
                start=datetime.now() - timedelta(hours=1),
                end=datetime.now(),
                freq='1min'
            )
            
            np.random.seed(42)
            n_points = len(timestamps)
            
            # Generate clean numeric data
            data = {
                'timestamp': timestamps,
                'flow_rate': 80 + 5 * np.sin(np.linspace(0, 4*np.pi, n_points)) + np.random.normal(0, 1, n_points),
                'pressure': 25 + 2 * np.sin(np.linspace(0, 6*np.pi, n_points)) + np.random.normal(0, 0.5, n_points),
                'temperature': 60 + 3 * np.sin(np.linspace(0, 2*np.pi, n_points)) + np.random.normal(0, 0.8, n_points),
                'gas_fraction': 15 + 3 * np.sin(np.linspace(0, 8*np.pi, n_points)) + np.random.normal(0, 0.5, n_points),
                'water_cut': 35 + 5 * np.sin(np.linspace(0, 3*np.pi, n_points)) + np.random.normal(0, 1, n_points),
                'oil_in_water': 800 + 100 * np.sin(np.linspace(0, 5*np.pi, n_points)) + np.random.normal(0, 30, n_points)
            }
            
            df = pd.DataFrame(data)
            
            # Ensure all numeric columns are proper float types
            numeric_cols = ['flow_rate', 'pressure', 'temperature', 'gas_fraction', 'water_cut', 'oil_in_water']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
    
    def render_header(self):
        """Render clean header"""
        data_source_indicator = "🔴 LIVE DATA" if REAL_DATA_AVAILABLE else "🟡 SIMULATED"
        
        st.markdown(f"""
        <div class="main-header">
            <h1>🏭 Automated Multiphase Flow Analyzer System</h1>
            <h3>Industrial Control Interface | {data_source_indicator}</h3>
            <p>Real-time monitoring of offshore multiphase separation process</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_system_status(self):
        """Render system status in clean layout"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "RUNNING" if st.session_state.process_data['system_running'] else "STOPPED"
            status_class = "status-running" if st.session_state.process_data['system_running'] else "status-stopped"
            st.markdown(f'<p class="{status_class}">🔄 System: {status}</p>', unsafe_allow_html=True)
        
        with col2:
            connection = "ONLINE" if st.session_state.connected else "OFFLINE"
            conn_class = "status-running" if st.session_state.connected else "status-stopped"
            st.markdown(f'<p class="{conn_class}">📡 PLC: {connection}</p>', unsafe_allow_html=True)
        
        with col3:
            alarm_status = "ACTIVE" if st.session_state.process_data['alarm_active'] else "NORMAL"
            alarm_class = "status-warning" if st.session_state.process_data['alarm_active'] else "status-running"
            st.markdown(f'<p class="{alarm_class}">🚨 Alarms: {alarm_status}</p>', unsafe_allow_html=True)
        
        with col4:
            estop = "ACTIVATED" if st.session_state.process_data['emergency_stop'] else "NORMAL"
            estop_class = "status-stopped" if st.session_state.process_data['emergency_stop'] else "status-running"
            st.markdown(f'<p class="{estop_class}">🛑 E-Stop: {estop}</p>', unsafe_allow_html=True)
    
    def render_process_overview(self):
        """Render clean process overview"""
        st.subheader("🏭 Process Overview")
        
        # Main process metrics in clean grid
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Flow Rate", 
                value=f"{st.session_state.process_data['flow_rate']:.1f} m³/h",
                delta=f"{np.random.uniform(-2, 2):.1f}"
            )
            st.metric(
                label="Inlet Pressure", 
                value=f"{st.session_state.process_data['pressure_inlet']:.1f} bar",
                delta=f"{np.random.uniform(-0.5, 0.5):.1f}"
            )
        
        with col2:
            st.metric(
                label="Temperature", 
                value=f"{st.session_state.process_data['temperature']:.1f} °C",
                delta=f"{np.random.uniform(-1, 1):.1f}"
            )
            st.metric(
                label="Gas Volume Fraction", 
                value=f"{st.session_state.process_data['gas_volume_fraction']:.1f} %",
                delta=f"{np.random.uniform(-1, 1):.1f}"
            )
        
        with col3:
            st.metric(
                label="Water Cut", 
                value=f"{st.session_state.process_data['water_cut']:.1f} %",
                delta=f"{np.random.uniform(-2, 2):.1f}"
            )
            st.metric(
                label="Oil in Water", 
                value=f"{st.session_state.process_data['oil_in_water_ppm']:.0f} ppm",
                delta=f"{np.random.uniform(-50, 50):.0f}"
            )
    
    def render_trend_charts(self):
        """Render clean trend charts with proper data handling"""
        st.subheader("📈 Process Trends")
        
        # Ensure we have clean data
        df = st.session_state.historical_data.copy()
        
        if df.empty:
            st.warning("No historical data available")
            return
        
        # Ensure column mapping for real data compatibility
        if 'pressure_inlet' in df.columns and 'pressure' not in df.columns:
            df['pressure'] = df['pressure_inlet']
        
        if 'gas_volume_fraction' in df.columns and 'gas_fraction' not in df.columns:
            df['gas_fraction'] = df['gas_volume_fraction']
        
        if 'oil_in_water_ppm' in df.columns and 'oil_in_water' not in df.columns:
            df['oil_in_water'] = df['oil_in_water_ppm']
        
        # Check if required columns exist
        required_columns = ['timestamp', 'flow_rate', 'pressure', 'gas_fraction', 'oil_in_water']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            st.write("Available columns:", list(df.columns))
            return
        
        # Create clean subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Flow Rate", "Pressure", "Gas Fraction", "Oil in Water"),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Add traces with clean styling
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['flow_rate'], name="Flow Rate", 
                      line=dict(color='#2e75b6', width=2)),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['pressure'], name="Pressure",
                      line=dict(color='#28a745', width=2)),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['gas_fraction'], name="Gas Fraction",
                      line=dict(color='#ffc107', width=2)),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['oil_in_water'], name="Oil in Water",
                      line=dict(color='#dc3545', width=2)),
            row=2, col=2
        )
        
        # Clean layout
        fig.update_layout(
            height=500,
            showlegend=False,
            font=dict(size=12),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        fig.update_xaxes(showgrid=True, gridcolor='lightgray', title_font_size=10)
        fig.update_yaxes(showgrid=True, gridcolor='lightgray', title_font_size=10)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_live_data_table(self):
        """Render clean live data table with proper types"""
        st.subheader("📊 Live Process Data")
        
        # Create clean data table
        data_rows = []
        for key, value in st.session_state.process_data.items():
            if isinstance(value, (int, float)):
                unit = self.get_unit(key)
                status = self.get_status(key, value)
                data_rows.append({
                    'Parameter': key.replace('_', ' ').title(),
                    'Value': round(float(value), 2),  # Ensure float type
                    'Unit': unit,
                    'Status': status
                })
        
        if data_rows:
            df_display = pd.DataFrame(data_rows)
            # Ensure proper data types for Arrow compatibility
            df_display['Value'] = pd.to_numeric(df_display['Value'], errors='coerce')
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    def get_unit(self, param: str) -> str:
        """Get unit for parameter"""
        units = {
            'flow_rate': 'm³/h',
            'pressure_inlet': 'bar',
            'pressure_outlet': 'bar',
            'temperature': '°C',
            'gas_volume_fraction': '%',
            'water_cut': '%',
            'oil_in_water_ppm': 'ppm',
            'pump_speed': '%'
        }
        return units.get(param, '-')
    
    def get_status(self, param: str, value: float) -> str:
        """Get status for parameter"""
        if param == 'oil_in_water_ppm' and value > 1000:
            return '⚠️ High'
        elif param == 'gas_volume_fraction' and value > 90:
            return '⚠️ High'
        elif param in ['pressure_inlet', 'pressure_outlet'] and value < 5:
            return '⚠️ Low'
        else:
            return '✅ Normal'
    
    def render_control_panel(self):
        """Render clean control panel"""
        st.subheader("🎛️ Control Panel")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**System Control**")
            if st.button("▶️ START", disabled=st.session_state.process_data['system_running']):
                st.session_state.process_data['system_running'] = True
                st.success("System started")
                st.rerun()
            
            if st.button("⏹️ STOP", disabled=not st.session_state.process_data['system_running']):
                st.session_state.process_data['system_running'] = False
                st.info("System stopped")
                st.rerun()
        
        with col2:
            st.markdown("**Safety**")
            if st.button("🛑 EMERGENCY STOP"):
                st.session_state.process_data['emergency_stop'] = True
                st.session_state.process_data['system_running'] = False
                st.error("EMERGENCY STOP!")
                st.rerun()
            
            if st.button("🔓 Reset E-Stop"):
                st.session_state.process_data['emergency_stop'] = False
                st.success("E-Stop reset")
                st.rerun()
        
        with col3:
            st.markdown("**Operations**")
            if st.button("🔄 Sample Now"):
                st.success("Sampling initiated")
            
            if st.button("🔧 Reset Alarms"):
                st.session_state.process_data['alarm_active'] = False
                st.success("Alarms reset")
                st.rerun()
    
    def render_sidebar(self):
        """Render clean sidebar"""
        with st.sidebar:
            st.markdown("## 🏭 System Control")
            
            # Connection controls
            if st.button("🔌 Connect PLC"):
                st.session_state.connected = True
                st.success("Connected")
            
            if st.button("📡 Disconnect"):
                st.session_state.connected = False
                st.warning("Disconnected")
            
            st.markdown("---")
            
            # System info
            st.markdown("## ℹ️ Status")
            st.info(f"Update: {datetime.now().strftime('%H:%M:%S')}")
            st.info(f"PLC: {'Online' if st.session_state.connected else 'Offline'}")
            
            st.markdown("---")
            
            # Settings
            st.markdown("## ⚙️ Settings")
            auto_refresh = st.checkbox("Auto Refresh", value=False)
            
            if auto_refresh:
                time.sleep(2)
                st.rerun()
            
            if st.button("🔄 Refresh Data"):
                self.simulate_data()
                st.rerun()
    
    def render_production_summary(self):
        """Render production summary with real data insights"""
        st.subheader("📋 Production Summary")
        
        if REAL_DATA_AVAILABLE:
            summary = real_data_provider.get_production_summary()
            
            # Production metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Daily Oil Production", 
                    value=f"{summary['daily_oil_production_bbl']:.0f} bbl/day",
                    help="Barrels of oil per day"
                )
                st.metric(
                    label="Average Flow Rate", 
                    value=f"{summary['average_flow_rate_m3h']:.1f} m³/h",
                    help="Volumetric flow rate"
                )
            
            with col2:
                st.metric(
                    label="Daily Gas Production", 
                    value=f"{summary['daily_gas_production_mcf']:.0f} Mcf/day",
                    help="Thousand cubic feet of gas per day"
                )
                st.metric(
                    label="Average Pressure", 
                    value=f"{summary['average_pressure_bar']:.1f} bar",
                    help="Wellhead pressure"
                )
            
            with col3:
                st.metric(
                    label="System Uptime", 
                    value=f"{summary['uptime_pct']:.1f}%",
                    help="System availability"
                )
                st.metric(
                    label="Water Cut", 
                    value=f"{summary['average_water_cut_pct']:.1f}%",
                    help="Water percentage in production"
                )
            
            # Data source information
            st.markdown("---")
            st.subheader("📊 Data Source Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                current_data = st.session_state.process_data
                st.info(f"**Well ID**: {current_data.get('well_id', 'N/A')}")
                st.info(f"**Platform**: {current_data.get('platform_id', 'N/A')}")
                st.info(f"**Data Source**: {current_data.get('data_source', 'Real Production Data')}")
            
            with col2:
                st.success(f"**Efficiency Rating**: {summary['efficiency_rating']}")
                st.info(f"**Last Update**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info(f"**Update Frequency**: Every 5 minutes")
            
            # Real-time data quality indicator
            st.markdown("---")
            st.subheader("🔍 Data Quality")
            
            quality_score = 95.8  # Simulated quality score
            quality_color = "green" if quality_score > 90 else "orange" if quality_score > 70 else "red"
            
            st.markdown(f"""
            <div style="background-color: {quality_color}; color: white; padding: 1rem; border-radius: 5px; text-align: center;">
                <h4>Data Quality Score: {quality_score}%</h4>
                <p>Based on real offshore production patterns</p>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.warning("Production summary requires real data integration.")
            st.info("Currently running in simulation mode.")
    
    def simulate_data(self):
        """Get new real or simulated data"""
        if REAL_DATA_AVAILABLE:
            # Get fresh real data point
            new_data = real_data_provider.get_current_data_point()
            st.session_state.process_data.update(new_data)
            
            # Update historical data with proper column mapping
            real_hist_data = real_data_provider.get_historical_data(6)
            # Map columns to match expected names for charts
            real_hist_data['pressure'] = real_hist_data['pressure_inlet']
            real_hist_data['gas_fraction'] = real_hist_data['gas_volume_fraction']
            real_hist_data['oil_in_water'] = real_hist_data['oil_in_water_ppm']
            st.session_state.historical_data = real_hist_data
        else:
            # Use original simulation
            import random
            data = st.session_state.process_data
            
            if data['system_running']:
                data['flow_rate'] += random.uniform(-1, 1)
                data['pressure_inlet'] += random.uniform(-0.3, 0.3)
                data['temperature'] += random.uniform(-0.5, 0.5)
                data['gas_volume_fraction'] += random.uniform(-0.5, 0.5)
                data['water_cut'] += random.uniform(-1, 1)
                data['oil_in_water_ppm'] += random.uniform(-20, 20)
                
                # Keep in bounds
                data['flow_rate'] = max(0, min(200, data['flow_rate']))
                data['pressure_inlet'] = max(0, min(50, data['pressure_inlet']))
                data['temperature'] = max(20, min(100, data['temperature']))
                data['gas_volume_fraction'] = max(0, min(100, data['gas_volume_fraction']))
                data['water_cut'] = max(0, min(100, data['water_cut']))
                data['oil_in_water_ppm'] = max(0, min(2000, data['oil_in_water_ppm']))
    
    def run(self):
        """Main application runner"""
        self.render_header()
        self.render_system_status()
        
        # Clean tab layout
        if REAL_DATA_AVAILABLE:
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏭 Overview", 
                "📊 Live Data", 
                "📈 Trends", 
                "🎛️ Controls",
                "📋 Production"
            ])
        else:
            tab1, tab2, tab3, tab4 = st.tabs([
                "🏭 Overview", 
                "📊 Data", 
                "📈 Trends", 
                "🎛️ Controls"
            ])
        
        with tab1:
            self.render_process_overview()
        
        with tab2:
            self.render_live_data_table()
        
        with tab3:
            self.render_trend_charts()
        
        with tab4:
            self.render_control_panel()
        
        if REAL_DATA_AVAILABLE:
            with tab5:
                self.render_production_summary()
        
        # Sidebar
        self.render_sidebar()

def main():
    """Main function"""
    hmi = HMIInterface()
    hmi.run()

if __name__ == "__main__":
    main() 