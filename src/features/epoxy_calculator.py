# src/features/epoxy_calculator.py
import pandas as pd
import numpy as np

def calculate_epoxy_stoichiometry(row: pd.Series) -> pd.Series:
    """
    Расчет стехиометрии и прокси-метрик для Tg и плотности сшивки.
    """
    eew = row['eew'] # Epoxy Equivalent Weight (g/eq), для DGEBA ~185-192
    ahew = row['ahew'] # Amine Hydrogen Equivalent Weight (g/eq)
    
    # Stoichiometric ratio (r)
    r_ratio = (row['mass_amine'] / ahew) / (row['mass_epoxy'] / eew)
    
    # Crosslink density proxy (Mc - molecular weight between crosslinks)
    f_epoxy = row.get('functionality_epoxy', 2.0) # DGEBA обычно 2
    f_amine = row.get('functionality_amine', 4.0)  # IPDA/DDM
    
    # Прокси для теоретического Tg (упрощенная зависимость от стехиометрии)
    # Пик Tg обычно при r = 0.95 - 1.0. При избытке амина (r < 0.85) Tg падает.
    tg_proxy = 150.0 * np.exp(-5.0 * (r_ratio - 1.0)**2) 
    
    return pd.Series({
        'r_ratio': round(r_ratio, 3),
        'tg_proxy': round(tg_proxy, 1)
    })