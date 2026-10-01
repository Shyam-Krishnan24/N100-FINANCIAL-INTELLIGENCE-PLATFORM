import sqlite3
from pathlib import Path
import pandas as pd,streamlit as st,plotly.express as px
ROOT=Path(__file__).resolve().parents[3]; con=sqlite3.connect(ROOT/'data/nifty100.db'); c=pd.read_sql_query('select id,company_name from companies',con); r=pd.read_sql_query('select * from financial_ratios',con); con.close(); t=st.selectbox('Ticker',c.id); metric=st.selectbox('Metric',['sales','net_profit','eps','return_on_equity_pct','free_cash_flow_cr']); d=r[r.company_id==t]; st.title('Trend Analysis'); st.plotly_chart(px.line(d,x='year',y=metric,markers=True),use_container_width=True)
