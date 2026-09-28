"""Cash-flow intelligence export."""
from pathlib import Path
import sqlite3
import pandas as pd

def build(db_path):
    """Build cash-flow quality, FCF and distress analytics."""
    con=sqlite3.connect(db_path); r=pd.read_sql_query("select * from financial_ratios",con); con.close(); latest=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).copy()
    latest["deleveraging_flag"]=(latest.financing_activity if "financing_activity" in latest else 0)<0
    latest["distress_signal"]=(latest.operating_activity<0)&(latest.financing_activity>0) if "operating_activity" in latest else False
    latest["cfo_quality"]=(latest.cfo_pat_ratio>=1).map({True:"High Quality Earnings",False:"Review"})
    latest["capex_intensity_category"]=pd.cut(latest.capex_intensity_pct,[-1,3,8,999],labels=["Asset-light","Balanced","Capital intensive"])
    cols=[c for c in ["company_id","year","cash_from_operations_cr","free_cash_flow_cr","fcf_cagr_5yr","cfo_pat_ratio","cfo_quality_score","cfo_quality","capex_cr","capex_intensity_pct","capex_intensity_category","fcf_conversion_rate_pct","capital_allocation_pattern","debt_declining","distress_signal"] if c in latest]
    out=latest[cols]; base=Path(db_path).parent.parent; out.to_excel(base/"output"/"cashflow_intelligence.xlsx",index=False); out[out.distress_signal].to_csv(base/"output"/"distress_alerts.csv",index=False); return out
