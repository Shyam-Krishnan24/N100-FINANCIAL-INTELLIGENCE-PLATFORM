"""Parse qualitative CAGR strings from analysis.xlsx."""
import re
import pandas as pd

def parse_analysis(path):
    """Extract period/value pairs from all CAGR text columns."""
    df=pd.read_excel(path,header=1); rows=[]
    for _,r in df.iterrows():
        for col in ["compounded_sales_growth","compounded_profit_growth","stock_price_cagr","roe"]:
            m=re.search(r"(\d+)\s*Years?:?\s*([\d.]+)%",str(r.get(col,"")))
            if m: rows.append({"company_id":str(r.company_id).strip().upper(),"metric_type":col,"period_years":int(m.group(1)),"value_pct":float(m.group(2))})
    return pd.DataFrame(rows)
