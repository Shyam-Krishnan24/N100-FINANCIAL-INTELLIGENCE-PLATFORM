"""Portfolio clustering, statistics and outlier detection."""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def run_clustering(db_path):
    """Create five financial-profile clusters and portfolio statistics."""
    con=sqlite3.connect(db_path); r=pd.read_sql_query("select * from financial_ratios",con); con.close(); r=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).copy()
    features=["return_on_equity_pct","debt_to_equity","revenue_cagr_5yr","fcf_cagr_5yr","operating_profit_margin_pct"]
    x=r[features].replace([np.inf,-np.inf],np.nan); x=x.fillna(x.median()); scaler=StandardScaler(); z=scaler.fit_transform(x)
    model=KMeans(n_clusters=5,random_state=42,n_init=20); labels=model.fit_predict(z)
    r["cluster_id"]=labels; centers=model.cluster_centers_
    names={}
    for k in range(5):
        g=r[r.cluster_id==k]; names[k]=["High-Quality Growth","Defensive / Cash Quality","Value Cyclicals","Distressed / Leveraged","Emerging Growth"][k]
    r["cluster_name"]=r.cluster_id.map(names); r["distance_from_centroid"]=[float(np.linalg.norm(z[i]-centers[labels[i]])) for i in range(len(r))]
    out=r[["company_id","cluster_id","cluster_name","distance_from_centroid"]]; base=Path(db_path).parent
    out.to_csv(base.parent/"output"/"cluster_labels.csv",index=False)
    stats=r[features].describe(percentiles=[.1,.25,.5,.75,.9]).T.rename(columns={"10%":"P10","25%":"P25","50%":"P50","75%":"P75","90%":"P90"}); stats.to_csv(base.parent/"output"/"portfolio_stats.csv")
    # correlation heatmap data
    corr=r[features].corr(); corr.to_csv(base.parent/"output"/"correlation_matrix.csv")
    # outliers by z score
    sec=pd.read_sql_query("select company_id,broad_sector from sectors",sqlite3.connect(db_path)); rr=r.merge(sec,on="company_id",how="left"); rows=[]
    for sector,g in rr.groupby("broad_sector"):
        for metric in features:
            s=g[metric].astype(float); sd=s.std(ddof=0)
            if not sd: continue
            zz=(s-s.mean())/sd
            for idx,val in zz.items():
                if abs(val)>3: rows.append({"company_id":g.loc[idx,"company_id"],"metric":metric,"value":g.loc[idx,metric],"z_score":val,"sector":sector,"sector_mean":s.mean(),"sector_std":sd})
    pd.DataFrame(rows).to_csv(base.parent/"output"/"outlier_report.csv",index=False)
    return out
