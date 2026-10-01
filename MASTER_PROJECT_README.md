# Nifty 100 Financial Intelligence Platform — Master Project

This is the complete internship project package.

## Included

1. Complete working Python project and source code
2. Original datasets under `data/raw/` and `data/supporting/`
3. Separate cleaned datasets under `data/cleaned/`
4. SQLite database under `data/nifty100.db`
5. ETL, validation, analytics, screener, peer, sector and cash-flow modules
6. Streamlit dashboard
7. FastAPI service
8. Generated analytical outputs and reports
9. Automated tests
10. API/OpenAPI and Postman files
11. Final internship documentation under `documentation/`

## Run Order

### 1. Create and activate a virtual environment

Windows:

```text
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Run the pipeline

```text
python run_pipeline.py
```

This rebuilds the SQLite database from the project datasets.

### 3. Start the dashboard

```text
streamlit run src/dashboard/app.py
```

### 4. Start the API

```text
uvicorn src.api.main:app --reload
```

### 5. Run tests

```text
python -m pytest -q
```

## Data policy

The original source datasets are preserved. Cleaned datasets are stored separately in `data/cleaned/` so the raw source remains available for traceability.

## Documentation

Open:

`documentation/Nifty100_Financial_Intelligence_Internship_Report.pdf`
