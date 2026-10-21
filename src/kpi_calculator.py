import pandas as pd
import joblib
import os

try:
    anomaly_model = joblib.load('models/anomaly_model.pkl')
    shift_encoder = joblib.load('models/shift_encoder.pkl')
except Exception as e:
    anomaly_model = None
    shift_encoder = None

CACHE_FILE = 'data/shift_metrics_cache.csv'

def get_shift_name(hour):
    if 6 <= hour < 14: return 'Morning'
    if 14 <= hour < 22: return 'Evening'
    return 'Night'
def update_metrics_cache(raw_df):
    os.makedirs('data', exist_ok=True)
    
    if os.path.exists(CACHE_FILE):
        cache_df = pd.read_csv(CACHE_FILE)
        if not cache_df.empty:
            # آخرین شیفت ثبت‌شده را حذف می‌کنیم تا با داده‌های کامل‌تر مجدداً محاسبه شود
            last_date = cache_df.iloc[-1]['Date']
            last_shift = cache_df.iloc[-1]['Shift']
            cache_df = cache_df[~((cache_df['Date'] == last_date) & (cache_df['Shift'] == last_shift))].copy()
    else:
        cache_df = pd.DataFrame(columns=['Date', 'Shift', 'Actual_Production', 'OEE'])

    # پیش‌پردازش رکوردهای ورودی
    raw_df['datetime'] = pd.to_datetime(raw_df['datetime'])
    raw_df['time_delta_sec'] = raw_df['datetime'].diff().dt.total_seconds().fillna(0)
    raw_df['RC_diff'] = raw_df['RC'].diff().fillna(0)
    raw_df['is_bag_release'] = (raw_df['DW1_kg'] > 500) & ((raw_df['DW1_kg'] - raw_df['DW1_kg'].shift(-1)) > 500)
    
    raw_df['Date'] = raw_df['datetime'].dt.date.astype(str)
    raw_df['Shift'] = raw_df['datetime'].dt.hour.apply(get_shift_name)
    
    # ساخت کلید یکتا برای چک کردن سریع وجود داشتن شیفت در کش
    existing_keys = set(zip(cache_df['Date'].astype(str), cache_df['Shift'].astype(str)))
    
    new_records = []
    for (date, shift), group in raw_df.groupby(['Date', 'Shift'], sort=False):
        if (str(date), str(shift)) in existing_keys:
            continue
            
        actual_production = group['RC_diff'][group['RC_diff'] > 0].sum()
        total_time = group['time_delta_sec'].sum()
        running_time = group[group['MF1'] == 1]['time_delta_sec'].sum()
        availability = running_time / total_time if total_time > 0 else 0
        
        running_data = group[group['MF1'] == 1]
        moving_data = running_data[running_data['NK'] > 0]
        performance = min((moving_data['NK'].mean() / 85.0), 1.0) if not moving_data.empty else 0
        
        final_weights = group[group['is_bag_release']]['DW1_kg']
        valid_cycles = len(final_weights[(final_weights >= 1050) & (final_weights <= 1110)])
        quality = valid_cycles / len(final_weights) if len(final_weights) > 0 else 1.0
        
        oee = availability * performance * quality * 100
        
        new_records.append({
            'Date': str(date), 
            'Shift': str(shift), 
            'Actual_Production': float(actual_production), 
            'OEE': float(oee)
        })
        
    if new_records:
        new_df = pd.DataFrame(new_records)
        cache_df = pd.concat([cache_df, new_df], ignore_index=True)
        cache_df.to_csv(CACHE_FILE, index=False)
        print(f"[{len(new_records)}] shifts processed and cache updated.")
        
    return cache_df

def calculate_final_scores(target_production, kpi_weight, vol_weight, time_range):
    """بخش فوق‌سریع: اعمال تنظیمات مدیر و فیلتر زمان روی کش آماده"""
    if not os.path.exists(CACHE_FILE):
        return []
        
    cache_df = pd.read_csv(CACHE_FILE)
    if cache_df.empty:
        return []
        
    # فیلتر هوشمند بازه زمانی
    cache_df['Date_dt'] = pd.to_datetime(cache_df['Date'])
    max_date = cache_df['Date_dt'].max() 
    
    try:
        days = int(time_range)
    except (ValueError, TypeError):
        days = 7
        
    start_date = max_date - pd.Timedelta(days=days - 1)
    cache_df = cache_df[cache_df['Date_dt'] >= start_date].copy()
    
    HARDCODED_KPI_THRESHOLD = 30.0
    HARDCODED_VOL_THRESHOLD = 70.0
    penalty_factor = 0.15 
    
    results = []
    for _, row in cache_df.iterrows():
        date = str(row['Date'])
        shift = str(row['Shift'])
        actual_production = float(row['Actual_Production'])
        oee = float(row['OEE'])
        
        achievement = min((actual_production / target_production) * 100, 100.0) if target_production > 0 else 0.0
        

        base_score = (oee * (kpi_weight / 100.0)) + (achievement * (vol_weight / 100.0))
        
        kpi_penalty = ((HARDCODED_KPI_THRESHOLD - oee) ** 2) * penalty_factor if oee < HARDCODED_KPI_THRESHOLD else 0
        vol_penalty = ((HARDCODED_VOL_THRESHOLD - achievement) ** 2) * penalty_factor if achievement < HARDCODED_VOL_THRESHOLD else 0
            
        shift_score = max(0.0, min(base_score - kpi_penalty - vol_penalty, 100.0))
        
        is_anomaly = 0
        if anomaly_model is not None and shift_encoder is not None:
            day_of_week = pd.to_datetime(date).dayofweek
            try:
                shift_encoded = shift_encoder.transform([shift])[0]
                features = [[day_of_week, shift_encoded, actual_production]]
                is_anomaly = int(anomaly_model.predict(features)[0])
            except Exception:
                is_anomaly = 0
            
        results.append({
            'Date': date,
            'Shift': shift,
            'Actual_Production': actual_production,
            'Score': round(shift_score, 2),
            'Is_Anomaly': is_anomaly,
            'OEE': round(oee, 2)
        })
        
    return results