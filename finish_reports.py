from pathlib import Path
import sqlite3,pandas as pd
from src.reports.generate import company_pdf, sector_reports, portfolio_report
root=Path(__file__).resolve().parent; db=root/'data/nifty100.db'; con=sqlite3.connect(db); tickers=pd.read_sql_query('select id from companies',con).id.tolist(); con.close()
for t in tickers:
 p=root/'reports/tearsheets'/f'{t}_tearsheet.pdf'
 if not p.exists(): company_pdf(db,t,p,root/'reports/radar_charts'/f'{t}.png')
sector_reports(db,root/'reports/sector'); portfolio_report(db,root/'reports/portfolio/portfolio_summary.pdf'); print('done')
