# src/data_collection/tds_parser_epoxy.py
from pydantic import BaseModel, Field, model_validator

class EpoxyTDSMetrics(BaseModel):
    lap_shear_strength_mpa: float = Field(description="Нахлесточная прочность, ISO 4587")
    t_g_c: float = Field(description="Температура стеклования, DSC")
    mix_ratio_by_weight: str = Field(description="Например, '100:35' или '2:1'")
    specific_gravity: float = Field(description="Плотность компонента А или смеси")
    
    @model_validator(mode='after')
    def validate_mix_ratio_physics(self) -> 'EpoxyTDSMetrics':
        """Физический валидатор: отсеиваем галлюцинации LLM"""
        if ':' in self.mix_ratio_by_weight:
            parts = self.mix_ratio_by_weight.split(':')
            ratio_val = float(parts[0]) / float(parts[1])
            # Для DGEBA + алифатический амин соотношение обычно от 2:1 до 5:1 по весу
            if not (1.5 <= ratio_val <= 10.0):
                raise ValueError(f"LLM Hallucination: Abnormal weight ratio {self.mix_ratio_by_weight}")
        return self