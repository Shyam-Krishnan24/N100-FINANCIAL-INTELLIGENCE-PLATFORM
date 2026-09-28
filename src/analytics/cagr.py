"""CAGR calculations with turnaround edge-case handling."""
import numpy as np
import pandas as pd

def safe_cagr(start, end, years):
    """Return CAGR percent and a decision flag."""
    if years < 3: return np.nan,"INSUFFICIENT"
    if pd.isna(start) or pd.isna(end): return np.nan,"MISSING"
    if start == 0: return np.nan,"ZERO_BASE"
    if start < 0 and end > 0: return np.nan,"TURNAROUND"
    if start < 0 and end < 0: return np.nan,"BOTH_NEGATIVE"
    if start > 0 and end < 0: return np.nan,"DECLINE_TO_LOSS"
    return ((end/start)**(1/years)-1)*100,""

def add_cagr_columns(df, value_col, prefix):
    """Add 3/5/10-year CAGR columns to a company-year DataFrame."""
    out=df.copy().sort_values(["company_id","year_dt"])
    for n in (3,5,10):
        vals=[]; flags=[]
        for _,g in out.groupby("company_id",sort=False):
            idx={d.year_dt.year:d for d in g.itertuples()}
            for row in g.itertuples():
                target=idx.get(row.year_dt.year-n)
                if target is None: v,f=np.nan,"INSUFFICIENT"
                else: v,f=safe_cagr(getattr(target,value_col),getattr(row,value_col),n)
                vals.append((row.Index,v)); flags.append((row.Index,f))
        vm=dict(vals); fm=dict(flags)
        out[f"{prefix}_cagr_{n}yr"]=out.index.map(vm); out[f"{prefix}_cagr_{n}yr_flag"]=out.index.map(fm)
    return out
