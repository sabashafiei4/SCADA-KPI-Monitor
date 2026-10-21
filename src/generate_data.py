import pandas as pd
import numpy as np

def generate_60_days_scada():
    print("Generating 60-day dynamic SCADA data with daily variance...")
    dates = pd.date_range(start="2025-01-01", periods=60*24*60*12, freq="5s")
    n = len(dates)
    
    df = pd.DataFrame({'datetime': dates})
    df['hour'] = df['datetime'].dt.hour
    
    daily_efficiency = np.random.uniform(0.4, 1.0, size=60) 
    day_indices = (df['datetime'] - df['datetime'].min()).dt.days
    day_indices = np.clip(day_indices, 0, 59)
    efficiency_col = daily_efficiency[day_indices]
    
    base_prob = 0.95 * efficiency_col
    night_mask = (df['hour'] >= 22) | (df['hour'] < 6)
    base_prob[night_mask] *= 0.6  # افت مضاعف در شب
    
    df['MF1'] = np.where(np.random.rand(n) < base_prob, 1, 0)
    
    rc_step = np.where(df['MF1'] == 1, 17 + np.random.randint(-2, 3, n), 0)
    df['RC'] = rc_step.cumsum() + 5000
    
    cycle_length = 10
    cycle_pos = np.arange(n) % cycle_length
    base_weight = (cycle_pos / (cycle_length - 1)) * 1.08e9
    
    df['DW1'] = np.where(cycle_pos == 0, 0, base_weight + np.random.normal(0, 1e5, n))
    df['DW1_kg'] = df['DW1'] / 1_000_000.0
    
    df['NK'] = np.where((cycle_pos == cycle_length - 1) & (df['MF1'] == 1), np.random.uniform(74, 85, n), 0.0)
    
    df.drop(columns=['hour'], inplace=True)
    df.to_csv('data/Cleaned_Dataset.csv', index=False)
    print("Dataset generated successfully!")

if __name__ == "__main__":
    generate_60_days_scada()