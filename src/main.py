import os
import pandas as pd
from preprocessing import clean_scada_data
from simulation import simulate_conveyor_speed
from kpi_calculator import calculate_production_kpis

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    input_file = os.path.join(base_dir, 'data', 'WebScadaFull.csv')
    output_file = os.path.join(base_dir, 'data', 'Cleaned_Dataset.csv')
    
    print("--- Starting SCADA Data Preparation Pipeline ---")
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return
        
    df_raw = pd.read_csv(input_file)
    
    df_cleaned = clean_scada_data(df_raw)
    
    df_final = simulate_conveyor_speed(df_cleaned)
    
    shift_results = calculate_production_kpis(
        df_final, 
        target_production=20000, 
        oee_weight=0.60, 
        achievement_weight=0.40
    )
    
    df_final.to_csv(output_file, index=False)
    print(f"--- Pipeline Successful! Final file saved at: {output_file} ---")
    
    print("\n" + "="*95)
    print(f"{'DATE':<12} | {'SHIFT':<8} | {'PROD':<6} | {'ACHIEV%':<8} | {'AVAIL%':<7} | {'PERF%':<6} | {'QUAL%':<6} | {'OEE%':<6} | {'SCORE':<6}")
    print("-" * 95)
    
    for r in shift_results:
        print(f"{r['Date']:<12} | {r['Shift']:<8} | {r['Actual_Production']:<6} | "
              f"{r['Achievement_%']:<8} | {r['Availability_%']:<7} | {r['Performance_%']:<6} | "
              f"{r['Quality_%']:<6} | {r['OEE_%']:<6} | {r['Shift_Score']:<6}")
              
    print("="*95 + "\n")

if __name__ == "__main__":
    main()