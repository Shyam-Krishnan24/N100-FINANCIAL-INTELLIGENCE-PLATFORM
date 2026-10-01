import sqlite3
from pathlib import Path
import pandas as pd,streamlit as st,plotly.express as px
ROOT=Path(__file__).resolve().parents[3]; con=sqlite3.connect(ROOT/'data/nifty100.db'); d=pd.read_sql_query('select * from market_cap',con); con.close(); t=st.selectbox('Ticker',sorted(d.company_id.unique())); x=d[d.company_id==t]; st.title('Valuation'); st.plotly_chart(px.line(x,x='year',y=['pe_ratio','pb_ratio','ev_ebitda']),use_container_width=True); st.dataframe(x,use_container_width=True)
