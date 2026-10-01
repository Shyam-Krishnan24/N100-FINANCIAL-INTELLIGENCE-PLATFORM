"""Peer percentile engine."""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

def build_peer_percentiles(db_path: Path):
    """Build percentile ranks for peer groups and export comparison workbook."""
    con=sqlite3.connect(db_path); pg=pd.read_sql_query("select * from peer_groups",con); r=pd.read_sql_query("select * from financial_ratios",con); comp=pd.read_sql_query("select id,company_name from companies",con); con.close()
    r=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).copy(); latest_year=r.year.max(); metrics=["return_on_equity_pct","return_on_capital_employed_pct","net_profit_margin_pct","debt_to_equity","free_cash_flow_cr","pat_cagr_5yr","revenue_cagr_5yr","eps_cagr_5yr"]
    rows=[]
    for g,sub in pg.groupby("peer_group_name"):
        m=r.merge(sub[["company_id"]],on="company_id",how="inner")
        for metric in metrics:
            vals=m[metric]; ranks=vals.rank(pct=True,ascending=(metric!="debt_to_equity"),method="average")
            for i,company in enumerate(m.company_id): rows.append({"company_id":company,"peer_group":g,"metric":metric,"value":vals.iloc[i],"percentile_rank":ranks.iloc[i],"year":latest_year})
    out=pd.DataFrame(rows); out.to_sql("peer_percentiles",sqlite3.connect(db_path),if_exists="replace",index=False)
    xlsx=Path(db_path).parent.parent/"output"/"peer_comparison.xlsx"; xlsx.parent.mkdir(exist_ok=True)
    with pd.ExcelWriter(xlsx,engine="openpyxl") as w:
        for g in pg.peer_group_name.unique():
            sub=out[out.peer_group==g].pivot(index="company_id",columns="metric",values="percentile_rank").reset_index(); sub.to_excel(w,sheet_name=g[:31],index=False)
    return out
