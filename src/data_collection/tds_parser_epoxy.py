# src/data_collection/tds_parser_epoxy.py
import os
import re
import json
from pathlib import Path
from typing import Optional
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from loguru import logger

from .schemas import EpoxyTDSMetrics

load_dotenv()

class EpoxyTDSParser:
    """
    Каскадный парсер TDS эпоксидных клеев.
    Архитектура: Regex → pdfplumber → LLM → Physical Validator.
    """
    
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.model = "anthropic/claude-3.5-sonnet"  # Для structured output
        
    def _extract_text(self, pdf_path: Path) -> str:
        """Level 1+2: Извлечение текста и таблиц через pdfplumber"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                # Парсинг таблиц (часто там технические данные)
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            text += " | ".join([cell or "" for cell in row]) + "\n"
        return text
    
    def _regex_extract(self, text: str) -> dict:
        """Level 1: Быстрый regex-поиск явных паттернов"""
        patterns = {
            'mix_ratio_weight': r'(?:mix\s*ratio|mixing\s*ratio)[^\d]*(\d+\s*:\s*\d+)',
            'viscosity_a_mpa_s': r'(?:viscosity|visc\.?)[^\d]*(\d{3,6})\s*(?:mpa·?s|cps)',
            'pot_life_min_23c': r'(?:pot\s*life|working\s*time)[^\d]*(\d+)\s*(?:min|minutes)',
            't_g_c': r'(?:Tg|glass\s*transition)[^\d]*(\d+)\s*°?C',
            'lap_shear_steel_mpa': r'(?:lap\s*shear|tensile\s*shear)[^\d]*(\d+(?:\.\d+)?)\s*(?:MPa|N/mm²)',
        }
        
        results = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                results[key] = match.group(1)
        return results
    
    def _llm_extract(self, text: str, regex_hints: dict) -> EpoxyTDSMetrics:
        """Level 3: LLM с JSON-schema enforcement + regex hints"""
        
        prompt = f"""Ты — эксперт-химик по эпоксидным клеям. Извлеки технические характеристики из TDS.

REGEX HINTS (уже найденные значения, проверь их):
{json.dumps(regex_hints, indent=2)}

ПРАВИЛА:
1. Mix Ratio может быть указан как "100:32 by weight" или "2:1 by volume". 
   Нормализуй к формату "100:32".
2. Если VOC не указан явно, но указан solids content = 100%, то VOC = 0 g/L.
3. Cure schedule записывай как "24h @ 23°C + 2h @ 80°C".
4. Для конструкционных клеев lap shear обычно 15-35 MPa на стали.
5. Tg для отвержденных эпоксидок: 60-180°C (в зависимости от отвердителя).

Верни ТОЛЬКО валидный JSON по схеме EpoxyTDSMetrics."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a polymer chemist extracting TDS data."},
                {"role": "user", "content": f"{prompt}\n\nTDS TEXT:\n{text[:8000]}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        
        data = json.loads(response.choices[0].message.content)
        return EpoxyTDSMetrics(**data)  # Level 4: Pydantic validation
    
    def parse(self, pdf_path: Path) -> Optional[EpoxyTDSMetrics]:
        """Оркестрация каскадного парсинга"""
        logger.info(f"🕷️ Parsing: {pdf_path.name}")
        
        try:
            # Level 1+2: Extract text
            text = self._extract_text(pdf_path)
            logger.debug(f"Extracted {len(text)} chars")
            
            # Level 1: Regex hints
            regex_hints = self._regex_extract(text)
            logger.info(f"Regex found: {list(regex_hints.keys())}")
            
            # Level 3+4: LLM + Physical Validation
            metrics = self._llm_extract(text, regex_hints)
            
            # Level 4: Compute derived metrics
            ahev = metrics.compute_ahev(eew_resin=190.0)
            logger.success(f"✅ Parsed: {metrics.product_name} | AHEW={ahev} | VOC={metrics.voc_g_l} g/L")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to parse {pdf_path.name}: {e}")
            return None

def run_etl_pipeline():
    """Запуск полного ETL-пайплайна для папки с TDS"""
    raw_dir = Path("data/01_raw")
    interim_dir = Path("data/02_interim")
    interim_dir.mkdir(exist_ok=True)
    
    parser = EpoxyTDSParser()
    results = []
    
    # На старте — несколько синтетических TDS для теста
    pdf_files = list(raw_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("⚠️ No PDFs in data/01_raw/. Creating sample TDS for testing...")
        # TODO: Download TDS from Henkel, 3M, Sika websites
        return
    
    for pdf_file in pdf_files:
        metrics = parser.parse(pdf_file)
        if metrics:
            # Сохраняем interim JSON для аудита
            json_path = interim_dir / f"{pdf_file.stem}.json"
            with open(json_path, 'w') as f:
                json.dump(metrics.model_dump(), f, indent=2)
            
            # Добавляем в ML-ready таблицу
            row = metrics.model_dump()
            row['ahev_computed'] = metrics.compute_ahev()
            results.append(row)
    
    if results:
        df = pd.DataFrame(results)
        df.to_csv("data/03_processed/epoxy_tds_dataset.csv", index=False)
        logger.success(f"✅ ETL complete: {len(results)} TDS parsed → data/03_processed/")
    else:
        logger.error("❌ No successful parses. Check TDS format or LLM API.")

if __name__ == "__main__":
    run_etl_pipeline()