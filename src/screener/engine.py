"""Configurable multi-criteria screener."""
from pathlib import Path
import sqlite3
import yaml
import numpy as np
import pandas as pd

def load_config(path):
    """Load YAML screener configuration."""
    return yaml.safe_load(Path(path).read_text())

def latest_universe(db_path):
    """Return latest-year company analytics joined to master data."""
    con=sqlite3.connect(db_path); r=pd.read_sql_query("select * from financial_ratios",con); c=pd.read_sql_query("select id,company_name from companies",con); s=pd.read_sql_query("select company_id,broad_sector,sub_sector from sectors",con); con.close()
    r=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).copy(); return r.merge(c,left_on="company_id",right_on="id").merge(s,on="company_id",how="left")

def apply_filters(df, filters):
    """Apply configured screening filters."""
    out=df.copy()
    mapping={"min_roe":"return_on_equity_pct","max_de":"debt_to_equity","min_fcf":"free_cash_flow_cr","min_revenue_cagr_5yr":"revenue_cagr_5yr","min_pat_cagr_5yr":"pat_cagr_5yr","max_pe":"pe_ratio","max_pb":"pb_ratio","min_dividend_yield":"dividend_yield_pct","max_dividend_payout":"dividend_payout_ratio_pct","min_revenue":"sales","min_revenue_cagr_3yr":"revenue_cagr_3yr"}
    for k,col in mapping.items():
        if k in filters and col in out:
            val=filters[k]; out=out[out[col].notna()]
            out=out[out[col]>=val] if k.startswith("min_") else out[out[col]<=val]
    if filters.get("debt_declining") and "debt_declining" in out: out=out[out.debt_declining.astype(bool)]
    return out

def composite_score(df):
    """Calculate a 0-100 latest-year composite score."""
    x=df.copy()
    def scale(s,inv=False):
        s=s.astype(float); lo=s.quantile(.1); hi=s.quantile(.9); z=s.clip(lo,hi); q=(z-lo)/(hi-lo)*100 if hi!=lo else pd.Series(50,index=s.index); return 100-q if inv else q
    x["composite_score"]=(.15*scale(x.return_on_equity_pct)+.10*scale(x.return_on_capital_employed_pct)+.10*scale(x.net_profit_margin_pct)+.15*scale(x.fcf_cagr_5yr)+.10*scale(x.cfo_pat_ratio)+.05*(x.free_cash_flow_cr>0)*100+.10*scale(x.revenue_cagr_5yr)+.10*scale(x.pat_cagr_5yr)+.10*scale(x.debt_to_equity,True)+.05*scale(x.interest_coverage)).round(2)
    return x

def run_all(db_path,config_path,output_path):
    """Run all six configured screeners and write an Excel workbook."""
    cfg=load_config(config_path); df=composite_score(latest_universe(db_path)); out_path=Path(output_path); out_path.parent.mkdir(parents=True,exist_ok=True); rows=[]
    with pd.ExcelWriter(out_path,engine="openpyxl") as w:
        for name,spec in cfg["presets"].items():
            sub=apply_filters(df,spec.get("filters",{})); sub=sub.sort_values(spec.get("ranking","composite_score"),ascending=False,na_position="last"); sub.to_excel(w,sheet_name=name[:31],index=False)
            sub.assign(preset=name).to_csv(out_path.parent/(name.lower().replace(" ","_")+".csv"),index=False); rows.append(sub.assign(preset=name))
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()
