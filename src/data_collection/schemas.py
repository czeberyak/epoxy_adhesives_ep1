# src/data_collection/schemas.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
import re

class EpoxyTDSMetrics(BaseModel):
    """
    Схема для 2К эпоксидного конструкционного клея.
    Жесткие физические ограничения отсекают LLM-галлюцинации.
    """
    # Идентификация
    product_name: str
    manufacturer: Literal["Henkel", "3M", "Sika", "Huntsman", "MasterBond", "Other"]
    
    # Физические свойства компонентов
    component_a_density: float = Field(gt=0.9, lt=2.5, description="Плотность смолы, г/см³")
    component_b_density: float = Field(gt=0.8, lt=2.5, description="Плотность отвердителя, г/см³")
    
    # Стехиометрия
    mix_ratio_weight: str = Field(description="Формат '100:32' или '2:1'")
    mix_ratio_volume: Optional[str] = Field(default=None, description="Формат '2:1'")
    
    # Реология
    viscosity_a_mpa_s: Optional[float] = Field(default=None, gt=100, lt=1_000_000)
    viscosity_b_mpa_s: Optional[float] = Field(default=None, gt=10, lt=1_000_000)
    
    # Кинетика отверждения
    pot_life_min_23c: Optional[float] = Field(default=None, gt=5, lt=1440)
    cure_schedule: str = Field(description="Например: '24h @ 23°C + 2h @ 80°C'")
    
    # Термические свойства
    t_g_c: Optional[float] = Field(default=None, gt=20, lt=250, description="Tg по DSC/DMA")
    
    # Механические свойства (конструкционный клей)
    lap_shear_steel_mpa: Optional[float] = Field(default=None, gt=5, lt=50)
    lap_shear_aluminum_mpa: Optional[float] = Field(default=None, gt=5, lt=50)
    t_peel_n_mm: Optional[float] = Field(default=None, gt=0, lt=20)
    
    # Экология
    voc_g_l: Optional[float] = Field(default=None, ge=0, le=100)
    solids_content_pct: Optional[float] = Field(default=None, ge=50, le=100)
    
    @field_validator('mix_ratio_weight', mode='before')
    @classmethod
    def normalize_mix_ratio(cls, v: str) -> str:
        """Нормализация формата: '100 parts : 32 parts' → '100:32'"""
        if not v:
            return v
        v = str(v).strip().lower()
        # Извлекаем числа через regex
        numbers = re.findall(r'\d+(?:\.\d+)?', v)
        if len(numbers) >= 2:
            return f"{numbers[0]}:{numbers[1]}"
        return v
    
    @model_validator(mode='after')
    def compute_derived_metrics(self) -> 'EpoxyTDSMetrics':
        """
        🧪 ФИЗИЧЕСКИЙ ВАЛИДАТОР + вычисление скрытых параметров.
        Запускается ПОСЛЕ парсинга LLM.
        """
        # 1. Проверка консистентности Volume vs Weight ratio
        if self.mix_ratio_volume and self.mix_ratio_weight:
            vol_parts = list(map(float, self.mix_ratio_volume.split(':')))
            wgt_parts = list(map(float, self.mix_ratio_weight.split(':')))
            
            # Вычисление density ratio из volume/weight ratio
            # (V_A/V_B) = (W_A/ρ_A) / (W_B/ρ_B) = (W_A/W_B) * (ρ_B/ρ_A)
            implied_density_ratio = (vol_parts[0] / vol_parts[1]) / (wgt_parts[0] / wgt_parts[1])
            actual_density_ratio = self.component_b_density / self.component_a_density
            
            # Допуск 20% на погрешность TDS
            if abs(implied_density_ratio - actual_density_ratio) / actual_density_ratio > 0.2:
                raise ValueError(
                    f"❌ Inconsistent TDS: Volume/Weight ratios don't match densities. "
                    f"Implied: {implied_density_ratio:.2f}, Actual: {actual_density_ratio:.2f}"
                )
        
        # 2. Расчет VOC из solids content (если не указан явно)
        if self.voc_g_l is None and self.solids_content_pct is not None:
            # VOC (g/L) = (100 - solids%) * mixture_density * 10
            # Для 100% reactive эпоксидок VOC ≈ 0 (допуск на reactive diluents)
            mix_density = (self.component_a_density + self.component_b_density) / 2
            self.voc_g_l = round((100 - self.solids_content_pct) / 100 * mix_density * 1000, 1)
        
        # 3. Для 100% reactive систем VOC должен быть близок к 0
        if self.voc_g_l is None:
            # Для эпоксидок без растворителей по умолчанию 0
            self.voc_g_l = 0.0
        
        return self
    
    def compute_ahev(self, eew_resin: float = 190.0) -> float:
        """
        🔬 ВЫЧИСЛЕНИЕ СКРЫТОГО ПАРАМЕТРА: Amine Hydrogen Equivalent Weight.
        Из mix ratio + EEW смолы (для DGEBA обычно 185-192 г/экв).
        
        AHEW = (mass_hardener / mass_resin) * EEW_resin * (1 / r_ratio)
        При r=1 (стехиометрия): AHEW = phr_hardener * EEW_resin / 100
        """
        if not self.mix_ratio_weight or ':' not in self.mix_ratio_weight:
            return 0.0
        
        parts = list(map(float, self.mix_ratio_weight.split(':')))
        # Предполагаем формат "resin:hardener" (100:32)
        phr_hardener = (parts[1] / parts[0]) * 100
        
        # Для стехиометрической смеси (r=1.0)
        ahev = phr_hardener * eew_resin / 100
        return round(ahev, 1)