import sqlite3
from pathlib import Path
import pandas as pd,streamlit as st,plotly.express as px
ROOT=Path(__file__).resolve().parents[3]; con=sqlite3.connect(ROOT/'data/nifty100.db'); pg=pd.read_sql_query('select * from peer_groups',con); pp=pd.read_sql_query('select * from peer_percentiles',con); con.close(); g=st.selectbox('Peer group',sorted(pg.peer_group_name.unique())); d=pp[pp.peer_group==g].pivot(index='company_id',columns='metric',values='percentile_rank'); st.title(g); st.dataframe(d,use_container_width=True)
