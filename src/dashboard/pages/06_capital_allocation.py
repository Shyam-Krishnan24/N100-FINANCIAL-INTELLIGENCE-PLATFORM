import sqlite3
from pathlib import Path
import pandas as pd,streamlit as st,plotly.express as px
ROOT=Path(__file__).resolve().parents[3]; con=sqlite3.connect(ROOT/'data/nifty100.db'); d=pd.read_sql_query('select * from capital_allocation',con); con.close(); y=st.selectbox('Year',sorted(d.year.unique(),reverse=True)); x=d[d.year==y]; st.title('Capital Allocation Map'); st.plotly_chart(px.treemap(x,path=['capital_allocation_pattern','company_id'],values='operating_activity'),use_container_width=True)
