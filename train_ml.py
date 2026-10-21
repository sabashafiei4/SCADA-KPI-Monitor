import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

def create_and_train_model():
    print("1. Loading raw dataset...")
    df = pd.read_csv('data/Cleaned_Dataset.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['RC_diff'] = df['RC'].diff().fillna(0)
    
    df['Date'] = df['datetime'].dt.date
    df['DayOfWeek'] = df['datetime'].dt.dayofweek 
    df['Shift'] = df['datetime'].dt.hour.apply(
        lambda h: 'Morning' if 6 <= h < 14 else ('Evening' if 14 <= h < 22 else 'Night')
    )
    
    shift_data = df.groupby(['Date', 'DayOfWeek', 'Shift'])['RC_diff'].sum().reset_index()
    shift_data.rename(columns={'RC_diff': 'Actual_Production'}, inplace=True)
    
    print("2. Generating Anomaly Labels...")
    stats = shift_data.groupby(['DayOfWeek', 'Shift'])['Actual_Production'].agg(['mean', 'std']).reset_index()
    shift_data = pd.merge(shift_data, stats, on=['DayOfWeek', 'Shift'])
    
    shift_data['Is_Anomaly'] = np.where(
        shift_data['Actual_Production'] < (shift_data['mean'] - (1.5 * shift_data['std'])), 
        1, 0
    )
    
    le_shift = LabelEncoder()
    shift_data['Shift_Encoded'] = le_shift.fit_transform(shift_data['Shift'])
    
    X = shift_data[['DayOfWeek', 'Shift_Encoded', 'Actual_Production']]
    y = shift_data['Is_Anomaly']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("3. Training Machine Learning Model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    print("\n=======================================================")
    print(" 📊 کارنامه ارزیابی عملکرد هوش مصنوعی (روی داده‌های تست)")
    print("=======================================================")
    
    y_pred = model.predict(X_test)
    
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("=======================================================\n")
    
    print("4. Saving model weights and encoders...")
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/anomaly_model.pkl')
    joblib.dump(le_shift, 'models/shift_encoder.pkl')
    print("Model successfully saved!")

if __name__ == "__main__":
    create_and_train_model()