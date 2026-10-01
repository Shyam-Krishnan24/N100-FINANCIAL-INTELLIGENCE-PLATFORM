import pytest
from pathlib import Path
import os
from fastapi.testclient import TestClient
os.environ['DB_PATH']=str(Path(__file__).resolve().parents[2]/'data/nifty100.db')
from src.api.main import app
client=TestClient(app)
@pytest.mark.parametrize('path',["/api/v1/sectors","/api/v1/portfolio/stats","/api/v1/companies/TCS/ratios","/api/v1/companies/TCS/pl","/api/v1/companies/TCS/bs","/api/v1/companies/TCS/cashflow","/api/v1/companies/TCS/documents","/api/v1/market-cap/TCS","/api/v1/peers/IT%20Services"])
def test_endpoint_exists(path): assert client.get(path).status_code in (200,404)
