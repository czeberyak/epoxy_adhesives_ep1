# scripts/generate_doe.py
import pandas as pd
from pyDOE2 import bbd

def generate_epoxy_doe():
    """
    Генерация матрицы Box-Behnken для эпоксидного конструкционного клея.
    """
    # 3 фактора: [r-ratio, %CTBN, Cure_Temp]
    design = bbd(3, center=(3,)) 
    
    # Маппинг кодированных значений (-1, 0, 1) на реальные физические
    mapping = {
        0: {'low': 0.85, 'mid': 0.95, 'high': 1.05}, # r-ratio
        1: {'low': 0.0,  'mid': 7.5,  'high': 15.0}, # % CTBN (phr)
        2: {'low': 100.0,'mid': 140.0,'high': 180.0}  # Cure Temp (°C)
    }
    
    df = pd.DataFrame(design, columns=['r_ratio', 'ctbn_phr', 'cure_temp'])
    for i, col in enumerate(df.columns):
        df[col] = df[col].map({-1: mapping[i]['low'], 0: mapping[i]['mid'], 1: mapping[i]['high']})
        
    # Добавляем расчет времени гелеобразования (Gel Time) как ограничивающий фактор
    # (Синтетический расчет на основе кинетики, чтобы отсечь "вскипание" шва)
    df['est_gel_time_min'] = 120 - (df['cure_temp'] - 100) * 0.8 - df['ctbn_phr'] * 0.5
        
    df.to_csv('reports/doe_epoxy_bbd_matrix.csv', index=False)
    print("✅ DOE Matrix generated: 15 runs (BBD) ready for lab.")

if __name__ == "__main__":
    generate_epoxy_doe()