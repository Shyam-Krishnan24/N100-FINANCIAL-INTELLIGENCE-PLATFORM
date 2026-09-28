"""Rule-based qualitative pros and cons generator."""
from pathlib import Path
import sqlite3
import pandas as pd

def generate(db_path):
    """Generate transparent KPI-triggered pros/cons with confidence scores."""
    con=sqlite3.connect(db_path); r=pd.read_sql_query("select * from financial_ratios",con); c=pd.read_sql_query("select id,company_name from companies",con); old=pd.read_sql_query("select * from prosandcons",con); con.close()
    latest=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).copy(); rows=[]
    for _,x in latest.iterrows():
        pros=[]; cons=[]
        def pro(text,conf): pros.append((text,conf))
        def con_(text,conf): cons.append((text,conf))
        if x.return_on_equity_pct>20: pro("ROE above 20% in the latest available year.",85)
        if x.free_cash_flow_cr>0: pro("Positive free cash flow in the latest available year.",75)
        if x.fcf_positive_5yr: pro("Free cash flow has remained positive for five consecutive years.",90)
        if x.debt_to_equity==0: pro("Debt-free balance sheet based on borrowings.",92)
        if x.revenue_cagr_5yr>15: pro("Revenue CAGR exceeds 15% over five years.",85)
        if x.pat_cagr_5yr>20: pro("Profit CAGR exceeds 20% over five years.",85)
        if x.cfo_pat_ratio>1: pro("Operating cash flow exceeds reported profit, supporting earnings quality.",82)
        if x.interest_coverage>5: pro("Interest coverage exceeds 5x.",80)
        if x.debt_to_equity>2: con_("Debt-to-equity exceeds 2x; leverage warrants attention.",88)
        if x.free_cash_flow_cr<0: con_("Free cash flow is negative in the latest available year.",78)
        if not x.fcf_positive_3yr: con_("Free cash flow is not positive across the latest three-year window.",72)
        if x.revenue_cagr_5yr<0: con_("Revenue CAGR is negative over five years.",82)
        if x.pat_cagr_5yr<0: con_("Profit CAGR is negative over five years.",82)
        if x.interest_coverage<1.5 and pd.notna(x.interest_coverage): con_("Interest coverage is below 1.5x.",90)
        if x.capex_intensity_pct>8: con_("Capital expenditure intensity exceeds 8% of sales.",70)
        if x.dividend_payout_ratio_pct>100: con_("Dividend payout exceeds 100% of reported profit.",88)
        if not pros: pro("No configured positive threshold was triggered; review the underlying KPIs.",61)
        if not cons: con_("No configured risk threshold was triggered; review the underlying KPIs.",61)
        for typ,items in [("pro",pros),("con",cons)]:
            for text,conf in items:
                if conf>60: rows.append({"company_id":x.company_id,"type":typ,"rule_triggered":"kpi_threshold","text":text,"confidence_pct":conf})
    return pd.DataFrame(rows)
