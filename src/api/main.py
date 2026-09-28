"""FastAPI service for the Nifty 100 intelligence platform."""
from pathlib import Path
import sqlite3, os
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
ROOT=Path(__file__).resolve().parents[2]; DB=Path(os.getenv("DB_PATH", str(ROOT/'data/nifty100.db'))); app=FastAPI(title="Nifty 100 Financial Intelligence API",version="1.0.0")

def df(sql,params=()):
    con=sqlite3.connect(DB); x=pd.read_sql_query(sql,con,params=params); con.close(); return x.replace({float("nan"):None}).to_dict(orient="records")
@app.get("/api/v1/health")
def health():
    try:
        con=sqlite3.connect(DB); tables=pd.read_sql_query("select name from sqlite_master where type='table'",con).name.tolist(); counts={t:int(pd.read_sql_query(f"select count(*) n from {t}",con).iloc[0,0]) for t in tables}; con.close(); return {"status":"ok","db_row_counts":counts,"version":"1.0.0"}
    except Exception as e: return {"status":"error","detail":str(e)}
@app.get("/api/v1/companies")
def companies(sector:str|None=None,search:str|None=None):
    sql="select c.*,s.broad_sector,s.sub_sector,r.return_on_equity_pct as roe_pct,r.return_on_capital_employed_pct as roce_pct from companies c left join sectors s on c.id=s.company_id left join financial_ratios r on c.id=r.company_id and r.year=(select max(r2.year) from financial_ratios r2 where r2.company_id=c.id) where 1=1"; p=[]
    if sector: sql+=" and s.broad_sector=?"; p.append(sector)
    if search: sql+=" and (c.id like ? or c.company_name like ?)"; p += [f"%{search}%",f"%{search}%"]
    return df(sql,p)
@app.get("/api/v1/companies/{ticker}")
def company(ticker:str):
    x=companies(search=ticker); x=[a for a in x if a["id"]==ticker.upper()];
    if not x:
        raise HTTPException(404,"Ticker not found")
    return x[0]
@app.get("/api/v1/companies/{ticker}/pl")
def pl(ticker:str,from_year:str|None=None,to_year:str|None=None): return _history("profitandloss",ticker,from_year,to_year)
@app.get("/api/v1/companies/{ticker}/bs")
def bs(ticker:str,from_year:str|None=None,to_year:str|None=None): return _history("balancesheet",ticker,from_year,to_year)
@app.get("/api/v1/companies/{ticker}/cashflow")
def cashflow(ticker:str,from_year:str|None=None,to_year:str|None=None): return _history("cashflow",ticker,from_year,to_year)
@app.get("/api/v1/companies/{ticker}/ratios")
def ratios(ticker:str,year:str|None=None): return df("select * from financial_ratios where company_id=? and (? is null or year=?) order by year",(ticker.upper(),year,year))
@app.get("/api/v1/companies/{ticker}/tearsheet")
def tearsheet(ticker:str):
    p=Path(__file__).resolve().parents[2]/"reports/tearsheets"/f"{ticker.upper()}_tearsheet.pdf";
    if not p.exists():
        raise HTTPException(404,"Tearsheet not found")
    return FileResponse(p,media_type="application/pdf",filename=p.name)
@app.get("/api/v1/screener")
def screener(min_roe:float|None=None,max_de:float|None=None,sector:str|None=None,min_fcf:float|None=None,min_rev_cagr_5yr:float|None=None,min_pat_cagr_5yr:float|None=None,max_pe:float|None=None):
    sql="select r.*,c.company_name,s.broad_sector from financial_ratios r join companies c on c.id=r.company_id left join sectors s on s.company_id=r.company_id where r.year=(select max(year) from financial_ratios)"; p=[]
    for col,op,val in [("return_on_equity_pct",">=",min_roe),("debt_to_equity","<=",max_de),("free_cash_flow_cr",">=",min_fcf),("revenue_cagr_5yr",">=",min_rev_cagr_5yr),("pat_cagr_5yr",">=",min_pat_cagr_5yr),("pe_ratio","<=",max_pe)]:
        if val is not None: sql+=f" and r.{col} {op} ?"; p.append(val)
    if sector: sql+=" and s.broad_sector=?"; p.append(sector)
    return df(sql,p)
@app.get("/api/v1/sectors")
def sectors(): return df("select s.broad_sector as sector_name,count(*) company_count,avg(r.return_on_equity_pct) median_roe,avg(r.pe_ratio) median_pe,avg(r.debt_to_equity) median_de from sectors s left join financial_ratios r on r.company_id=s.company_id and r.year=(select max(year) from financial_ratios) group by s.broad_sector")
@app.get("/api/v1/sectors/{sector}/companies")
def sector_companies(sector:str): return df("select c.id,c.company_name,r.* from companies c join sectors s on c.id=s.company_id left join financial_ratios r on r.company_id=c.id and r.year=(select max(year) from financial_ratios) where s.broad_sector=?",(sector,))
@app.get("/api/v1/peers/{group_name}")
def peers(group_name:str):
    return df("select p.peer_group_name,p.company_id,p.is_benchmark,pp.metric,pp.value,pp.percentile_rank,r.year,r.return_on_equity_pct,r.return_on_capital_employed_pct,r.net_profit_margin_pct,r.debt_to_equity,r.free_cash_flow_cr,r.revenue_cagr_5yr,r.pat_cagr_5yr,r.eps_cagr_5yr from peer_groups p left join peer_percentiles pp on pp.company_id=p.company_id and pp.peer_group=p.peer_group_name left join financial_ratios r on r.company_id=p.company_id and r.year=(select max(r2.year) from financial_ratios r2 where r2.company_id=p.company_id) where p.peer_group_name=?",(group_name,))
@app.get("/api/v1/companies/{ticker}/peers/compare")
def peer_compare(ticker:str): return df("select * from peer_percentiles where company_id=?",(ticker.upper(),))
@app.get("/api/v1/market-cap/{ticker}")
def market_cap(ticker:str,from_year:int|None=None,to_year:int|None=None): return _history("market_cap",ticker,from_year,to_year)
@app.get("/api/v1/portfolio/stats")
def portfolio_stats(): return df("select * from portfolio_stats")
@app.get("/api/v1/companies/{ticker}/documents")
def documents(ticker:str,from_year:int|None=None,to_year:int|None=None): return _history("documents",ticker,from_year,to_year)
def _history(table,ticker,from_year,to_year):
    wh="company_id=?"; p=[ticker.upper()]
    if from_year is not None: wh+=" and year>=?"; p.append(from_year)
    if to_year is not None: wh+=" and year<=?"; p.append(to_year)
    return df(f"select * from {table} where {wh} order by year",p)
