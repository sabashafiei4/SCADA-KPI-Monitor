import numpy as np

def simulate_conveyor_speed(df):
    """
    Simulate conveyor speed (NK) based on machine operational phases (bulk and fine feed).
    """
    print("Simulating conveyor speed (NK)...")
    
    noise = np.random.normal(loc=0, scale=2, size=len(df))
    
    conditions = [
        (df['DS1'] != 1),                                      # Machine stopped
        (df['DS1'] == 1) & (df['GG'] > 0),                     # Running - Bulk feed phase
        (df['DS1'] == 1) & (df['GG'] == 0) & (df['GG2'] == 1)  # Running - Fine feed phase
    ]
    
    choices = [
        0,
        np.random.uniform(75, 85, len(df)),
        np.random.uniform(15, 25, len(df))
    ]
    
    df['NK'] = np.select(conditions, choices, default=0)
    df['NK'] = np.where(df['NK'] > 0, df['NK'] + noise, 0)
    df['NK'] = np.clip(df['NK'], 0, 100)
    df['NK'] = df['NK'].round(2)
    
    return df