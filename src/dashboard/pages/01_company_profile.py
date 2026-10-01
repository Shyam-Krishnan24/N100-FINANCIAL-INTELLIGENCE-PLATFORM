import os,sqlite3
from pathlib import Path
import pandas as pd, streamlit as st, plotly.graph_objects as go
ROOT=Path(__file__).resolve().parents[3]; DB=Path(os.getenv('DB_PATH',ROOT/'data/nifty100.db'))
def q(sql,p=()):
 c=sqlite3.connect(DB); d=pd.read_sql_query(sql,c,params=p); c.close(); return d
c=q('select * from companies'); ticker=st.selectbox('Company',c.id); comp=c[c.id==ticker].iloc[0]; r=q('select * from financial_ratios where company_id=? order by year',(ticker,)); st.title(f'{ticker} — {comp.company_name}'); st.write(comp.about_company); metric_cols = st.columns(6)
latest = r.iloc[-1]
metric_names = ['return_on_equity_pct','return_on_capital_employed_pct','net_profit_margin_pct','debt_to_equity','free_cash_flow_cr','financial_health_score']
for i in range(len(metric_names)):
    col = metric_cols[i]
    label = metric_names[i]
    value = latest[label]
    col.metric(label.replace('_',' ').title(), f'{value:.2f}' if pd.notna(value) else 'N/A')
fig=go.Figure(); fig.add_bar(x=r.year,y=r.sales,name='Revenue'); fig.add_bar(x=r.year,y=r.net_profit,name='Net Profit'); st.plotly_chart(fig,use_container_width=True)
