# Nifty 100 Financial Intelligence Platform

Production-style local analytics implementation based on the supplied Nifty 100 project specification and datasets.

## Included
- 12 Excel datasets loaded into SQLite
- ETL, normalisation, 16 DQ checks and audit outputs
- 50+ derived financial KPIs, CAGR and health scoring
- 6 configurable screeners
- Peer percentile analysis and radar charts
- Cash-flow intelligence
- Rule-based qualitative analysis
- KMeans clustering, portfolio statistics and outlier detection
- 92 company PDF tearsheets, sector reports and portfolio summary
- Streamlit dashboard with 8 analytical screens
- FastAPI service with 16 endpoints
- 60+ automated tests

Power BI and formal internship documentation are intentionally outside this implementation package.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
streamlit run src/dashboard/app.py
uvicorn src.api.main:app --port 8000
pytest -q
```

The source Excel files in `data/raw` and `data/supporting` are treated as source data and are not modified by the ETL.
