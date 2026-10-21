import pandas as pd

def clean_scada_data(df):
    """
    Clean raw data and standardize time, weights, and motor status.
    """
    print("Preprocessing and cleaning data...")
    
    columns_to_drop = [
        'Label', 'Level_meter', 'MW', 'Vector_Data',
        'D_Sample_History_Buffer', 'D_CaCl_1_Silo_2_Discharge_Weight',
        'D_CaCl_1_Silo_2_Remaining_Weight', 'Emergency_Stop'
    ]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')

    if 'DW1' in df.columns:
        df['DW1_kg'] = df['DW1'] / 1_000_000.0
        
    if 'MF1' not in df.columns and 'DS1' in df.columns:
        df['MF1'] = df['DS1'].apply(lambda x: 1 if x == 1 else 0)

    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    else:
        df['datetime'] = pd.date_range(start="2025-01-01", periods=len(df), freq="5s")
        
    df['time_ms'] = df['datetime'].astype('int64') // 10**6
    
    return df