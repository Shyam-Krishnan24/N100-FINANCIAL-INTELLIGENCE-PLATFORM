import sqlite3
from pathlib import Path
import pandas as pd,streamlit as st
ROOT=Path(__file__).resolve().parents[3]; con=sqlite3.connect(ROOT/'data/nifty100.db'); c=pd.read_sql_query('select id,company_name from companies',con); d=pd.read_sql_query('select * from documents',con); con.close(); t=st.selectbox('Ticker',c.id); st.title('Annual Reports'); x=d[d.company_id==t].sort_values('year',ascending=False); st.dataframe(x,use_container_width=True)
