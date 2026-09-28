from pathlib import Path
import os
from fastapi.testclient import TestClient
os.environ['DB_PATH']=str(Path(__file__).resolve().parents[2]/'data/nifty100.db')
from src.api.main import app
client=TestClient(app)
def test_health_200():
 r=client.get('/api/v1/health'); assert r.status_code==200
def test_companies_count():
 r=client.get('/api/v1/companies'); assert r.status_code==200; assert len(r.json())==92
def test_invalid_ticker():
 r=client.get('/api/v1/companies/INVALID'); assert r.status_code==404
def test_screener_filter():
 r=client.get('/api/v1/screener?min_roe=15'); assert r.status_code==200; assert all((x.get('return_on_equity_pct') is None or x['return_on_equity_pct']>=15) for x in r.json())
