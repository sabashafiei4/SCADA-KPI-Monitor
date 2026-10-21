from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
import requests 
from datetime import datetime
import os
from src.kpi_calculator import update_metrics_cache, calculate_final_scores

app = FastAPI(title="SCADA BI Engine API")


EXTERNAL_PLC_API_URL = "http://webscada-backend.local/api/v1/plc-logs"
RAW_DATA_FILE = 'data/Cleaned_Dataset.csv'

def sync_plc_data():
    """
    وظیفه این تابع: استخراج زمان آخرین رکورد، درخواست داده‌های جدید از بک‌اند، 
    و چسباندن آن‌ها به فایل CSV اصلی
    """
    start_time = None
    if os.path.exists(RAW_DATA_FILE):
        df = pd.read_csv(RAW_DATA_FILE)
        if not df.empty and 'datetime' in df.columns:
           
            df['datetime'] = pd.to_datetime(df['datetime'])
            last_record = df['datetime'].max()
            start_time = last_record.strftime('%Y-%m-%dT%H:%M:%S')
    
    if not start_time:
        start_time = "2025-01-01T00:00:00"
        df = pd.DataFrame()
    
    end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    try:
        print(f"Fetching PLC data from {start_time} to {end_time}...")
        response = requests.get(
            EXTERNAL_PLC_API_URL, 
            params={
                "start_time": start_time,
                "end_time": end_time
            },
            timeout=10 
        )
        
        if response.status_code == 200:
            new_data = response.json()
            if new_data and len(new_data) > 0:
                new_df = pd.DataFrame(new_data)
                
           
                
                updated_df = pd.concat([df, new_df], ignore_index=True)
                updated_df.to_csv(RAW_DATA_FILE, index=False)
                print(f"✅ {len(new_df)} new records appended to PLC dataset.")
            else:
                print("No new data from PLC backend.")
        else:
            print(f"⚠️ Backend returned error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Failed to sync with WebSCADA backend: {str(e)}")


class KPIRequest(BaseModel):
    target_production: float = Field(..., description="Target production from UI")
    kpi_weight: float = Field(..., description="Weight for KPI/OEE (%)") 
    vol_weight: float = Field(..., description="Weight for Volume (%)")  
    time_range: str = Field(..., description="Selected time range")

class ShiftResult(BaseModel):
    Date: str
    Shift: str
    Actual_Production: float
    Score: float
    Is_Anomaly: int 
    OEE: float 
class KPIResponse(BaseModel):
    status: str = "success"
    results: List[ShiftResult]

@app.post("/api/calculate-kpi", response_model=KPIResponse)
async def get_kpi_calculations(payload: KPIRequest):
    try:
        sync_plc_data()
        
        # ۲. خواندن فایل که حالا (در صورت وجود دیتای جدید) آپدیت شده است
        raw_df = pd.read_csv(RAW_DATA_FILE)
        
        # ۳. آپدیت کش شاخص‌ها (فقط داده‌های جدیدِ اضافه شده، محاسبه می‌شوند)
        update_metrics_cache(raw_df)
        
        # ۴. اعمال تنظیمات اسلایدرها و فیلتر زمانی روی کش نهایی
        kpi_results = calculate_final_scores(
            target_production=payload.target_production,
            kpi_weight=payload.kpi_weight,
            vol_weight=payload.vol_weight,
            time_range=payload.time_range
        )
        
        return KPIResponse(status="success", results=kpi_results)
        
    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))