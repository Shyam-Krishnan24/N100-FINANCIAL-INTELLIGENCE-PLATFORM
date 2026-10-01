"""Streamlit dashboard entry point."""
import os, sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
ROOT=Path(__file__).resolve().parents[2]; DB=Path(os.getenv('DB_PATH',ROOT/'data/nifty100.db'))
@st.cache_data(ttl=600)
def read(sql,params=()):
    con=sqlite3.connect(DB); d=pd.read_sql_query(sql,con,params=params); con.close(); return d
st.set_page_config(page_title='Nifty 100 Financial Intelligence',layout='wide')
st.title('Nifty 100 Financial Intelligence Platform')
st.caption('Local analytical platform. Market-cap and stock-price supporting datasets are simulated per project specification.')
r=read('select * from financial_ratios'); c=read('select * from companies'); s=read('select * from sectors')
latest=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).merge(s,on='company_id').merge(c,left_on='company_id',right_on='id')
cols=st.columns(4); cols[0].metric('Companies',len(c)); cols[1].metric('Average ROE',f"{latest.return_on_equity_pct.mean():.1f}%"); cols[2].metric('Median P/E',f"{latest.pe_ratio.median():.1f}x"); cols[3].metric('Positive FCF',int((latest.free_cash_flow_cr>0).sum()))
fig=px.pie(latest,names='broad_sector',title='Companies by Sector'); st.plotly_chart(fig,use_container_width=True)
st.dataframe(latest[['company_id','company_name','broad_sector','return_on_equity_pct','debt_to_equity','free_cash_flow_cr','financial_health_score']].sort_values('financial_health_score',ascending=False),use_container_width=True)
