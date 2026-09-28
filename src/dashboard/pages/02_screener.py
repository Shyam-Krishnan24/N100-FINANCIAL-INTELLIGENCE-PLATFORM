from pathlib import Path
import sys,sqlite3
import pandas as pd,streamlit as st
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT)); from src.screener.engine import latest_universe,composite_score,apply_filters
DB=ROOT/'data/nifty100.db'; d=composite_score(latest_universe(DB)); st.title('Financial Screener'); preset=st.selectbox('Preset',['Custom','Quality Compounder','Value Pick','Growth Accelerator','Dividend Champion','Debt-Free Blue Chip','Turnaround Watch']);
filters={}
if preset=='Custom': filters={'min_roe':st.slider('Min ROE',-50.,100.,15.),'max_de':st.slider('Max D/E',0.,10.,2.)}
else:
 import yaml
 cfg=yaml.safe_load((ROOT/'config/screener_config.yaml').read_text()); filters=cfg['presets'][preset]['filters']
out=apply_filters(d,filters); st.download_button('Download CSV',out.to_csv(index=False),'screener.csv','text/csv'); st.dataframe(out.sort_values('composite_score',ascending=False),use_container_width=True)
