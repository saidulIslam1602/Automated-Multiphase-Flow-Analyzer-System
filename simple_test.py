import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Testing data structure that HMI expects...")

# Simulate what the real data integration creates
timestamps = pd.date_range(
    start=datetime.now() - timedelta(hours=1),
    end=datetime.now(),
    freq='5min'
)

# Create data with real integration column names
real_data = pd.DataFrame({
    'timestamp': timestamps,
    'flow_rate': np.random.normal(85, 5, len(timestamps)),
    'pressure_inlet': np.random.normal(25, 2, len(timestamps)),
    'pressure_outlet': np.random.normal(20, 1.5, len(timestamps)),
    'temperature': np.random.normal(65, 3, len(timestamps)),
    'gas_volume_fraction': np.random.normal(15, 2, len(timestamps)),
    'water_cut': np.random.normal(35, 5, len(timestamps)),
    'oil_in_water_ppm': np.random.normal(800, 100, len(timestamps))
})

print("\nReal data columns:", list(real_data.columns))

# Test column mapping like in HMI
df = real_data.copy()

if 'pressure_inlet' in df.columns and 'pressure' not in df.columns:
    df['pressure'] = df['pressure_inlet']
    print("✅ Mapped pressure_inlet -> pressure")

if 'gas_volume_fraction' in df.columns and 'gas_fraction' not in df.columns:
    df['gas_fraction'] = df['gas_volume_fraction']
    print("✅ Mapped gas_volume_fraction -> gas_fraction")

if 'oil_in_water_ppm' in df.columns and 'oil_in_water' not in df.columns:
    df['oil_in_water'] = df['oil_in_water_ppm']
    print("✅ Mapped oil_in_water_ppm -> oil_in_water")

required_columns = ['timestamp', 'flow_rate', 'pressure', 'gas_fraction', 'oil_in_water']
missing_columns = [col for col in required_columns if col not in df.columns]

print(f"\nRequired columns: {required_columns}")
print(f"Available columns after mapping: {list(df.columns)}")

if missing_columns:
    print(f"❌ Missing columns: {missing_columns}")
else:
    print("✅ All required columns available!")

print("\nTesting chart access:")
try:
    pressure_data = df['pressure']
    print("✅ Can access pressure column")
except KeyError as e:
    print(f"❌ KeyError accessing pressure: {e}")

try:
    gas_data = df['gas_fraction']
    print("✅ Can access gas_fraction column")
except KeyError as e:
    print(f"❌ KeyError accessing gas_fraction: {e}")

try:
    oil_data = df['oil_in_water']
    print("✅ Can access oil_in_water column")
except KeyError as e:
    print(f"❌ KeyError accessing oil_in_water: {e}") 