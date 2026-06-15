# src/features/epoxy_stoichiometry.py
from pydantic import BaseModel, Field, field_validator
import numpy as np
import math

class EpoxyComponent(BaseModel):
    name: str
    mass_g: float = Field(gt=0)
    eq_weight: float = Field(gt=0, description="EEW для смол, AHEW для аминов")
    functionality: float = Field(default=2.0, description="f - число функциональных групп на молекулу")
    density: float = Field(default=1.15, description="Плотность г/см3")

class FormulationCalculator:
    """
    Калькулятор стехиометрии и прокси-метрик для эпоксидных систем.
    """
    def __init__(self, resin: EpoxyComponent, hardener: EpoxyComponent, modifiers: list[EpoxyComponent] = None):
        self.resin = resin
        self.hardener = hardener
        self.modifiers = modifiers or []
        
    @property
    def r_ratio(self) -> float:
        """Stoichiometric ratio: eq_hardener / eq_resin. Идеал = 1.0"""
        eq_resin = self.resin.mass_g / self.resin.eq_weight
        eq_hard = self.hardener.mass_g / self.hardener.eq_weight
        return eq_hard / eq_resin

    @property
    def crosslink_density_proxy(self) -> float:
        """
        Прокси для плотности сшивки (Mc^-1). 
        Чем выше значение, тем выше Tg и модуль, но ниже ударная вязкость.
        Уравнение Флори-Ренера (упрощенное).
        """
        f_e = self.resin.functionality
        f_a = self.hardener.functionality
        
        # Если f=2 (линейные цепи, например DGEBA + диамин), сшивки нет (только удлинение).
        # Реальная сшивка начинается при f > 2 (например, Novolac f=3..5, или TETA f=5).
        if f_e <= 2.0 and f_a <= 2.0:
            return 0.0 
            
        r = self.r_ratio
        # Теоретическая плотность узлов сшивки
        nu_e = (r * (f_a - 2) + (f_e - 2)) / (self.resin.mass_g + self.hardener.mass_g)
        return max(0, nu_e * 1000) # Масштабирование для ML

    def get_ml_features(self) -> dict:
        return {
            "r_ratio": round(self.r_ratio, 3),
            "crosslink_proxy": round(self.crosslink_density_proxy, 4),
            "phr_hardener": round((self.hardener.mass_g / self.resin.mass_g) * 100, 1)
        }

# Пример использования
if __name__ == "__main__":
    dgeba = EpoxyComponent(name="DGEBA (Epikote 828)", mass_g=100, eq_weight=190, functionality=2.0)
    ipda = EpoxyComponent(name="IPDA", mass_g=23, eq_weight=42.5, functionality=4.0) # 2 первичных + 2 вторичных атома H
    
    calc = FormulationCalculator(resin=dgeba, hardener=ipda)
    print(f"✅ r-ratio: {calc.r_ratio:.3f} (Target: 0.95-1.05)")
    print(f"✅ Crosslink Proxy: {calc.crosslink_density_proxy:.4f}")