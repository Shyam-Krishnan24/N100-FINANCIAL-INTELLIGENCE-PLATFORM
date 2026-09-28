"""50+ financial KPI engine."""
from __future__ import annotations
import sqlite3, math
from pathlib import Path
import numpy as np
import pandas as pd
from .cagr import add_cagr_columns

BASE_COLS=["company_id","year","net_profit_margin_pct","operating_profit_margin_pct","return_on_equity_pct","debt_to_equity","interest_coverage","asset_turnover","free_cash_flow_cr","capex_cr","earnings_per_share","book_value_per_share","dividend_payout_ratio_pct","total_debt_cr","cash_from_operations_cr"]

def compute_ratios(db_path: Path):
    """Compute annual ratios, growth, cash quality, valuation and health metrics."""
    con=sqlite3.connect(db_path)
    pl=pd.read_sql_query("select * from profitandloss",con); bs=pd.read_sql_query("select * from balancesheet",con); cf=pd.read_sql_query("select * from cashflow",con)
    sec=pd.read_sql_query("select company_id,broad_sector from sectors",con); mc=pd.read_sql_query("select * from market_cap",con)
    con.close()
    for d in (pl,bs,cf): d["year_dt"]=pd.to_datetime(d.year+"-01",errors="coerce")
    d=pl.merge(bs,on=["company_id","year"],suffixes=("","_bs"),how="left").merge(cf,on=["company_id","year"],suffixes=("","_cf"),how="left")
    d=d.merge(sec,on="company_id",how="left")
    eq=d.equity_capital.fillna(0)+d.reserves.fillna(0)
    d["net_profit_margin_pct"]=np.where(d.sales!=0,d.net_profit/d.sales*100,np.nan)
    d["operating_profit_margin_pct"]=np.where(d.sales!=0,d.operating_profit/d.sales*100,np.nan)
    d["ebit_margin_pct"]=np.where(d.sales!=0,(d.operating_profit-d.depreciation)/d.sales*100,np.nan)
    d["return_on_equity_pct"]=np.where(eq>0,d.net_profit/eq*100,np.nan)
    d["return_on_assets_pct"]=np.where(d.total_assets!=0,d.net_profit/d.total_assets*100,np.nan)
    capital=eq+d.borrowings.fillna(0)
    d["return_on_capital_employed_pct"]=np.where(capital>0,(d.operating_profit-d.depreciation)/capital*100,np.nan)
    d["debt_to_equity"]=np.where(eq>0,d.borrowings.fillna(0)/eq,np.nan)
    d["interest_coverage"]=np.where(d.interest.fillna(0)!=0,(d.operating_profit+d.other_income.fillna(0))/d.interest,np.nan)
    d["asset_turnover"]=np.where(d.total_assets!=0,d.sales/d.total_assets,np.nan)
    d["fixed_asset_turnover"]=np.where(d.fixed_assets!=0,d.sales/d.fixed_assets,np.nan)
    d["working_capital_days"]=np.where(d.sales!=0,(d.other_asset.fillna(0)-d.other_liabilities.fillna(0))/d.sales*365,np.nan)
    d["free_cash_flow_cr"]=d.operating_activity.fillna(0)+d.investing_activity.fillna(0)
    d["capex_cr"]=d.investing_activity.abs()
    d["cfo_pat_ratio"]=np.where(d.net_profit!=0,d.operating_activity/d.net_profit,np.nan)
    d["capex_intensity_pct"]=np.where(d.sales!=0,d.capex_cr/d.sales*100,np.nan)
    d["fcf_conversion_rate_pct"]=np.where(d.operating_profit!=0,d.free_cash_flow_cr/d.operating_profit*100,np.nan)
    d["total_debt_cr"]=d.borrowings.fillna(0)
    d["cash_from_operations_cr"]=d.operating_activity.fillna(0)
    d["net_debt_cr"]=d.borrowings.fillna(0)-d.investments.fillna(0)
    d["eps"]=d.eps
    d["book_value_per_share"]=np.where(d.equity_capital!=0,eq/(d.equity_capital/1.0),np.nan)
    d["dividend_payout_ratio_pct"]=d.dividend_payout
    # 1.0 face-value approximation corrected later for exact face values in companies table
    con=sqlite3.connect(db_path); comp=pd.read_sql_query("select id,face_value from companies",con); con.close()
    face_map=comp.set_index("id")["face_value"]; d["face_value"]=d["company_id"].map(face_map); d["book_value_per_share"]=np.where(d.equity_capital!=0,eq/(d.equity_capital/d.face_value),np.nan)
    # market metrics by calendar year
    mc["year_cal"]=mc.year.astype(int); d["year_cal"]=d.year_dt.dt.year
    d=d.merge(mc[["company_id","year_cal","market_cap_crore","enterprise_value_crore","pe_ratio","pb_ratio","ev_ebitda","dividend_yield_pct"]],on=["company_id","year_cal"],how="left")
    d["fcf_yield_pct"]=np.where(d.market_cap_crore!=0,d.free_cash_flow_cr/d.market_cap_crore*100,np.nan)
    d["pe_computed"]=np.where(d.net_profit>0,d.market_cap_crore/d.net_profit,np.nan)
    d["pb_computed"]=np.where(eq>0,d.market_cap_crore/eq,np.nan)
    d["ev_ebitda_computed"]=np.where(d.operating_profit>0,d.enterprise_value_crore/d.operating_profit,np.nan)
    d["net_debt_to_ebitda"]=np.where(d.operating_profit>0,d.net_debt_cr/d.operating_profit,np.nan)
    d=add_cagr_columns(d,"sales","revenue")
    d=add_cagr_columns(d,"net_profit","pat")
    d=add_cagr_columns(d,"eps","eps")
    d["fcf_cagr_5yr"]=np.nan; d["fcf_cagr_10yr"]=np.nan
    temp=d[["company_id","year","year_dt","free_cash_flow_cr"]].copy(); temp=add_cagr_columns(temp,"free_cash_flow_cr","fcf")
    d=d.drop(columns=[c for c in ["fcf_cagr_3yr","fcf_cagr_3yr_flag","fcf_cagr_5yr","fcf_cagr_5yr_flag","fcf_cagr_10yr","fcf_cagr_10yr_flag"] if c in d])
    d=d.merge(temp[["company_id","year","fcf_cagr_5yr","fcf_cagr_5yr_flag","fcf_cagr_10yr","fcf_cagr_10yr_flag"]],on=["company_id","year"],how="left")
    # consecutive FCF flag
    d["fcf_positive"]=(d.free_cash_flow_cr>0).astype(int)
    d["fcf_positive_3yr"]=d.groupby("company_id").fcf_positive.transform(lambda s:s.rolling(3,min_periods=3).sum().eq(3))
    d["fcf_positive_5yr"]=d.groupby("company_id").fcf_positive.transform(lambda s:s.rolling(5,min_periods=5).sum().eq(5))
    d["debt_declining"]=d.groupby("company_id").borrowings.transform(lambda s:s.diff()<0).fillna(False)
    d["cfo_quality_score"]=np.select([d.cfo_pat_ratio>=1,d.cfo_pat_ratio<.5],[100,0],default=50)
    d["capital_allocation_pattern"]=d.apply(capital_pattern,axis=1)
    # sector-aware composite score at latest year
    d["composite_quality_score"]=np.nan
    latest=d.groupby("company_id").year_dt.transform("max").eq(d.year_dt)
    idx=d.index[latest]
    for sector,gidx in d.loc[latest].groupby("broad_sector").groups.items():
        ix=gidx
        def wins(col,ascending=True):
            s=d.loc[ix,col].astype(float); lo=s.quantile(.10); hi=s.quantile(.90); z=s.clip(lo,hi); scaled=(z-lo)/(hi-lo)*100 if hi!=lo else pd.Series(50,index=s.index); return scaled if ascending else 100-scaled
        prof=.15*wins("return_on_equity_pct")+.10*wins("return_on_capital_employed_pct")+.10*wins("net_profit_margin_pct")
        cash=.15*wins("fcf_cagr_5yr")+.10*wins("cfo_pat_ratio")+.05*(d.loc[ix,"free_cash_flow_cr"]>0).astype(int)*100
        growth=.10*wins("revenue_cagr_5yr")+.10*wins("pat_cagr_5yr")
        de=d.loc[ix,"debt_to_equity"].astype(float); de_score=np.select([de<=0,de<=.5,de<=1,de<=2,de>5],[100,85,70,50,0],default=25)
        icr=d.loc[ix,"interest_coverage"].astype(float).fillna(10); icr_score=np.select([icr>10,icr>=5,icr>=3,icr<1.5],[100,75,50,0],default=25)
        leverage=.10*de_score+.05*icr_score
        d.loc[ix,"composite_quality_score"]=(prof+cash+growth+leverage).round(2)
    d["financial_health_score"]=d["composite_quality_score"]
    d["health_band"]=pd.cut(d.financial_health_score,[-1,39.999,69.999,100.001],labels=["Needs Attention","Moderate","Strong"]).astype(str)
    keep=["company_id","year"]+[c for c in d.columns if c not in {"company_id","year","year_dt","company_id_bs","company_id_cf","year_bs","year_cf","year_cal","face_value","broad_sector","fcf_positive"} and not c.endswith("_flag")]
    # keep flags too
    keep=[c for c in keep if c in d.columns]
    ratios=d[keep].copy()
    # replace source-like fields with clean names and preserve broad sector
    ratios.to_sql("financial_ratios",sqlite3.connect(db_path),if_exists="replace",index=False)
    con=sqlite3.connect(db_path); d["capital_allocation_pattern"]=d["capital_allocation_pattern"].fillna("Unknown"); d[["company_id","year","operating_activity","investing_activity","financing_activity","capital_allocation_pattern"]].to_csv(Path(db_path).parent/"capital_allocation.csv",index=False); con.close()
    return ratios

def capital_pattern(r):
    """Classify CFO/CFI/CFF sign pattern."""
    cfo, cfi, cff = np.sign(r.operating_activity), np.sign(r.investing_activity), np.sign(r.financing_activity)
    if cfo>0 and cfi<0 and cff<0:
        return "Reinvestor / Returns"
    if cfo>0 and cfi<0 and cff>0:
        return "Growth Funded"
    if cfo>0 and cfi>0 and cff<0:
        return "Asset Monetiser"
    if cfo>0 and cfi>0 and cff>0:
        return "Cash Accumulator"
    if cfo<0 and cff>0:
        return "Distress Signal"
    if cfo<0 and cfi<0 and cff>0:
        return "Funding Growth"
    if cfo<0 and cfi>0 and cff<0:
        return "Restructuring"
    return "Mixed / Neutral"
