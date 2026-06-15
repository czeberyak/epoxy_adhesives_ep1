# src/features/derived_metrics.py
import pandas as pd
import numpy as np

class EpoxyDerivedMetricsCalculator:
    """
    Вычисление физико-химических признаков, которые НЕ указаны в TDS,
    но критичны для ML-моделирования эпоксидных систем.
    """
    
    @staticmethod
    def compute_crosslink_proxy(row: pd.Series) -> float:
        """
        Прокси для плотности сшивки (ν_e) на основе AHEW и функциональности.
        
        Теория: Чем ниже AHEW, тем больше узлов сшивки на грамм отвердителя.
        Для тетрафункциональных аминов (IPDA, DETA) ν_e выше, чем для дифункциональных.
        """
        ahev = row.get('ahev_computed', 40.0)
        
        # Эмпирическая формула (калибрована на DGEBA + амины)
        # AHEW 20-30 → высокая сшивка (например, DETA)
        # AHEW 80-120 → низкая сшивка (например, полиамиды)
        crosslink_proxy = 100.0 / ahev
        return round(crosslink_proxy, 3)
    
    @staticmethod
    def estimate_functionality(row: pd.Series) -> float:
        """
        Оценка средней функциональности отвердителя на основе AHEW.
        
        AHEW = M_w / f (где f — число активных атомов H)
        Для алифатических аминов: M_w ≈ 100-200, f = 4-6
        Для полиамидов: M_w ≈ 500-1000, f = 4-6 (но AHEW выше)
        """
        ahev = row.get('ahev_computed', 40.0)
        
        # Эвристика: низкий AHEW → многофункциональный амин
        if ahev < 30:
            return 5.0  # DETA, TETA
        elif ahev < 60:
            return 4.0  # IPDA, MXDA
        elif ahev < 100:
            return 3.0  # Некоторые циклоалифатические
        else:
            return 2.5  # Полиамиды, амидоамины
    
    @staticmethod
    def compute_reactivity_index(row: pd.Series) -> float:
        """
        Индекс реакционной способности на основе pot life и AHEW.
        
        Короткий pot life + низкий AHEW = высокая реакционность.
        Это коррелирует с exotherm peak и риском "вскипания" толстых швов.
        """
        pot_life = row.get('pot_life_min_23c', 60.0)
        ahev = row.get('ahev_computed', 40.0)
        
        # Нормализация: pot_life 30-180 мин, AHEW 20-100
        reactivity = (100.0 / pot_life) * (60.0 / ahev)
        return round(reactivity, 3)
    
    @classmethod
    def enrich_dataset(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Обогащение датасета вычисленными признаками для ML"""
        df = df.copy()
        
        df['crosslink_proxy'] = df.apply(cls.compute_crosslink_proxy, axis=1)
        df['est_functionality'] = df.apply(cls.estimate_functionality, axis=1)
        df['reactivity_index'] = df.apply(cls.compute_reactivity_index, axis=1)
        
        # Log-transform для признаков с большим разбросом (вязкость)
        if 'viscosity_a_mpa_s' in df.columns:
            df['log_viscosity_a'] = np.log10(df['viscosity_a_mpa_s'].fillna(10000))
        
        return df

if __name__ == "__main__":
    # Тест на синтетических данных
    sample_data = pd.DataFrame([{
        'product_name': 'Loctite EA 9466',
        'ahev_computed': 42.5,  # IPDA-подобный
        'pot_life_min_23c': 90,
        'viscosity_a_mpa_s': 25000,
    }])
    
    enriched = EpoxyDerivedMetricsCalculator.enrich_dataset(sample_data)
    print(enriched.T)