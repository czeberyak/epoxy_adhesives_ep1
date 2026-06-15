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