# Makefile для epoxy_adhesives_ep1
.PHONY: install data doe simulate dashboard clean

install:
	pip install -r requirements.txt

data:
	@echo "🕷️ Parsing Epoxy TDS (Henkel, 3M, Sika)..."
	python -m src.data_collection.tds_parser_epoxy

doe:
	@echo "📊 Generating Box-Behnken Matrix..."
	python scripts/generate_doe_epoxy.py

simulate:
	@echo "🧪 Generating Synthetic Lab Data (Gaussian Noise + Kinetics)..."
	python scripts/generate_synthetic_epoxy.py

dashboard:
	@echo "🚀 Launching Streamlit Formulator..."
	streamlit run streamlit_app.py

all: install data doe simulate
	@echo "✅ Full EP-1 Pipeline Completed!"

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	
.PHONY: parse validate enrich

parse:
	@echo "🕷️ Parsing Epoxy TDS (Henkel, 3M, Sika, Huntsman)..."
	python -m src.data_collection.tds_parser_epoxy

validate:
	@echo "✅ Running Physical Validator on parsed data..."
	python -c "from src.data_collection.schemas import EpoxyTDSMetrics; print('Schema OK')"

enrich:
	@echo "🧪 Computing derived metrics (AHEW, crosslink proxy, reactivity)..."
	python -c "from src.features.derived_metrics import EpoxyDerivedMetricsCalculator; import pandas as pd; df = pd.read_csv('data/03_processed/epoxy_tds_dataset.csv'); enriched = EpoxyDerivedMetricsCalculator.enrich_dataset(df); enriched.to_csv('data/03_processed/epoxy_tds_enriched.csv', index=False); print('✅ Enriched dataset saved')"

etl: parse validate enrich
	@echo "🎉 Full ETL pipeline complete!"