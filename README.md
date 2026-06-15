# 🧪 Epoxy Structural Adhesives AI (EP-1)
> **Industrial AI Solutions Architect Portfolio Case #2**
> Data-driven formulation of 2-component epoxy structural adhesives (DGEBA + Amines).

## 🎯 Business Value (Для B2B клиентов)
- **Сокращение времени R&D** с 6 месяцев до 3 недель за счет Surrogate Modeling.
- **Автоматический FTO-анализ** патентов Henkel/3M для безопасного вывода продукта на рынок.
- **Оптимизация Tg и Lap Shear** без перерасхода дорогих модификаторов (CTBN, Core-Shell).

## 🗺️ Project Roadmap
- [x] **Phase 1: Data ETL & FTO** (TDS parsing, Patent Landscape analysis)
- [x] **Phase 2: Phys-Chem EDA** (Stoichiometry, Crosslink density mapping)
- [ ] **Phase 3: DOE & Lab Synthesis** (Box-Behnken execution, DSC & ASTM D1002 testing)
- [ ] **Phase 4: Surrogate ML** (XGBoost + RSM 3D surfaces)
- [ ] **Phase 5: Streamlit Client Demo** (Interactive Formulator App)

## 🚀 Quick Start
```bash
git clone <repo_url> && cd epoxy_adhesives_ep1
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make all