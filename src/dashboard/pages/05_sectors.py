import sqlite3
from pathlib import Path
import pandas as pd,streamlit as st,plotly.express as px
ROOT=Path(__file__).resolve().parents[3]; con=sqlite3.connect(ROOT/'data/nifty100.db'); r=pd.read_sql_query('select * from financial_ratios',con); s=pd.read_sql_query('select * from sectors',con); con.close(); d=r.sort_values(['company_id','year']).groupby('company_id',as_index=False).tail(1).merge(s,on='company_id'); sec=st.selectbox('Sector',sorted(d.broad_sector.unique())); x=d[d.broad_sector==sec]; st.title(sec); st.plotly_chart(px.scatter(x,x='revenue_cagr_5yr',y='return_on_equity_pct',size='market_cap_crore',hover_name='company_id'),use_container_width=True); st.dataframe(x,use_container_width=True)
