load:
	python run_pipeline.py
ratios:
	python -c "from pathlib import Path; import sys; sys.path.insert(0,'.'); from src.analytics.ratios import compute_ratios; compute_ratios(Path('data/nifty100.db'))"
test:
	pytest -q
report:
	python run_pipeline.py
dashboard:
	streamlit run src/dashboard/app.py
api:
	uvicorn src.api.main:app --port 8000
clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
