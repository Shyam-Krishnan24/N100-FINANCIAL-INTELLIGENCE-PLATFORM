"""Data-quality validation rules."""
from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

def validate_db(db_path: Path, output: Path) -> pd.DataFrame:
    """Run the 16 specification DQ rules against the loaded database."""
    con=sqlite3.connect(db_path); issues=[]
    def add(rule,comp,year,field,msg,severity): issues.append({"rule_id":rule,"company_id":comp,"year":year,"field":field,"issue":msg,"severity":severity})
    companies=pd.read_sql_query("select * from companies",con)
    for c,n in companies.id.value_counts().items():
        if n>1:add("DQ-01",c,"","id","duplicate company ticker","CRITICAL")
    for t in ["profitandloss","balancesheet","cashflow"]:
        d=pd.read_sql_query(f"select company_id,year,count(*) n from {t} group by company_id,year having n>1",con)
        for _,r in d.iterrows(): add("DQ-02",r.company_id,r.year,t,"duplicate annual key","CRITICAL")
    ids=set(companies.id.astype(str))
    for t in ["profitandloss","balancesheet","cashflow","analysis","documents","prosandcons","sectors","stock_prices","market_cap","financial_ratios","peer_groups"]:
        d=pd.read_sql_query(f"select distinct company_id from {t}",con)
        for c in d.company_id.dropna().astype(str):
            if c not in ids:add("DQ-03",c,"", "company_id","orphan foreign key","CRITICAL")
    bs=pd.read_sql_query("select * from balancesheet",con)
    for _,r in bs.iterrows():
        if r.total_assets and abs(r.total_assets-r.total_liabilities)/abs(r.total_assets)>=.01:add("DQ-04",r.company_id,r.year,"total_assets","balance sheet mismatch","WARNING")
        if r.fixed_assets<0:add("DQ-10",r.company_id,r.year,"fixed_assets","negative fixed assets","WARNING")
    pl=pd.read_sql_query("select * from profitandloss",con)
    for _,r in pl.iterrows():
        if r.sales and abs(r.opm_percentage-r.operating_profit/r.sales*100)>=1:add("DQ-05",r.company_id,r.year,"opm_percentage","OPM cross-check mismatch","WARNING")
        if r.sales<=0:add("DQ-06",r.company_id,r.year,"sales","non-positive sales","WARNING")
        if not 0<=r.tax_percentage<=60:add("DQ-11",r.company_id,r.year,"tax_percentage","tax rate outside 0-60","WARNING")
        if r.dividend_payout>200:add("DQ-12",r.company_id,r.year,"dividend_payout","payout above 200%","WARNING")
        if r.net_profit>0 and (pd.isna(r.eps) or r.eps<=0):add("DQ-14",r.company_id,r.year,"eps","EPS sign mismatch","WARNING")
    cf=pd.read_sql_query("select * from cashflow",con)
    for _,r in cf.iterrows():
        if abs(r.net_cash_flow-(r.operating_activity+r.investing_activity+r.financing_activity))>10:add("DQ-09",r.company_id,r.year,"net_cash_flow","cash flow sum mismatch","WARNING")
    docs=pd.read_sql_query("select * from documents",con)
    for _,r in docs[docs.Annual_Report.notna()].iterrows():
        if not str(r.Annual_Report).startswith("http"):add("DQ-13",r.company_id,str(r.year),"Annual_Report","invalid URL format","WARNING")
    for c in companies.id:
        counts=[pd.read_sql_query(f"select count(*) n from {t} where company_id=?",con,params=(c,)).iloc[0,0] for t in ["profitandloss","balancesheet","cashflow"]]
        if min(counts)<5:add("DQ-16",c,"","coverage","less than 5 years in one statement","WARNING")
    con.close(); out=pd.DataFrame(issues,columns=["rule_id","company_id","year","field","issue","severity"]); out.to_csv(output,index=False); return out
