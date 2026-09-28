from pathlib import Path
import sqlite3, sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from src.etl.loader import load_all
from src.etl.validator import validate_db
from src.analytics.ratios import compute_ratios
from src.analytics.peer import build_peer_percentiles
from src.screener.engine import run_all
from src.nlp.parser import parse_analysis
from src.nlp.pros_cons_generator import generate
from src.analytics.clustering import run_clustering
from src.analytics.cashflow_kpis import build as build_cashflow
from src.reports.generate import generate_all

def main():
    db=ROOT/'data/nifty100.db'
    load_all(ROOT/'data',db)
    validate_db(db,ROOT/'validation_failures.csv')
    compute_ratios(db)
    # derived tables
    build_peer_percentiles(db)
    run_all(db,ROOT/'config/screener_config.yaml',ROOT/'output/screener_output.xlsx')
    parsed=parse_analysis(ROOT/'data/raw/analysis.xlsx'); parsed.to_csv(ROOT/'output/analysis_parsed.csv',index=False)
    pc=generate(db); pc.to_sql('pros_cons_generated',sqlite3.connect(db),if_exists='replace',index=False); pc.to_csv(ROOT/'output/pros_cons_generated.csv',index=False)
    run_clustering(db)
    build_cashflow(db)
    con=sqlite3.connect(db); import pandas as pd
    ps=pd.read_csv(ROOT/'output/portfolio_stats.csv'); ps.to_sql('portfolio_stats',con,if_exists='replace',index=False)
    ca=pd.read_csv(ROOT/'data'/'capital_allocation.csv'); ca.to_sql('capital_allocation',con,if_exists='replace',index=False)
    con.close()
    generate_all(db,ROOT)
    print('Pipeline complete:',db)
if __name__=='__main__': main()
