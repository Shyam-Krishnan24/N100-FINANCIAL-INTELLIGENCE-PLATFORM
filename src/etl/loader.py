"""Excel-to-SQLite ETL loader."""
from __future__ import annotations
import logging, sqlite3, time
from pathlib import Path
import pandas as pd
from .normaliser import normalize_core_frame, normalize_ticker

logger=logging.getLogger(__name__)
CORE={
 "companies":"companies.xlsx","profitandloss":"profitandloss.xlsx","balancesheet":"balancesheet.xlsx","cashflow":"cashflow.xlsx","analysis":"analysis.xlsx","documents":"documents.xlsx","prosandcons":"prosandcons.xlsx"}
SUPPORT={"sectors":"sectors.xlsx","stock_prices":"stock_prices.xlsx","market_cap":"market_cap.xlsx","financial_ratios":"financial_ratios.xlsx","peer_groups":"peer_groups.xlsx"}

def read_source(path: Path, table: str) -> pd.DataFrame:
    """Read a source workbook with the specification's header rules."""
    header=1 if table in CORE else 0
    df=pd.read_excel(path, header=header)
    if table=="documents" and "Year" in df.columns: df=df.rename(columns={"Year":"year"})
    if table=="companies" and "id" in df.columns: df["id"]=df["id"].map(normalize_ticker)
    if "company_id" in df.columns: df["company_id"]=df["company_id"].map(normalize_ticker)
    if table in {"profitandloss","balancesheet","cashflow","analysis","financial_ratios"} and "year" in df.columns:
        df=normalize_core_frame(df)
    return df

def load_all(data_root: Path, db_path: Path):
    """Load all 12 datasets into SQLite and emit audit files."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    audits=[]; failures=[]; rejected_rows=[]
    for table,fn in {**CORE,**SUPPORT}.items():
        path=(data_root/"raw"/fn) if table in CORE else (data_root/"supporting"/fn)
        t=time.perf_counter(); rows_in=rows_out=rejected=0
        try:
            df=read_source(path,table); rows_in=len(df)
            if "company_id" in df.columns:
                df=df[df.company_id!="MISSING"]
                if table != "companies":
                    # Enforce the master-company universe; orphan rows are rejected and logged.
                    master = pd.read_excel(data_root/"raw"/CORE["companies"], header=1)
                    master_ids=set(master["id"].astype(str).str.strip().str.upper())
                    orphan=df[~df.company_id.isin(master_ids)]
                    for _,r in orphan.iterrows(): rejected_rows.append({"table":table,"company_id":r.get("company_id"),"year":r.get("year",""),"reason":"orphan company_id","severity":"CRITICAL"})
                    df=df[df.company_id.isin(master_ids)]
            if table not in {"companies","documents","analysis","prosandcons","sectors","stock_prices","market_cap","financial_ratios","peer_groups"} and "year" in df.columns:
                bad=df[df.year=="PARSE_ERROR"]
                for _,r in bad.iterrows(): failures.append({"company_id":r.get("company_id"),"year":r.get("year"),"field":"year","issue":"unparseable year","severity":"CRITICAL"})
                df=df[df.year!="PARSE_ERROR"]
            # remove exact duplicates on declared time-series keys
            if table in {"profitandloss","balancesheet","cashflow","financial_ratios","market_cap","documents"}: keys=["company_id","year"]
            elif table=="stock_prices": keys=["company_id","date"]
            elif table in {"analysis","sectors"}: keys=["company_id"]
            else: keys=["id"] if "id" in df.columns else (["company_id"] if "company_id" in df.columns else [])
            before=len(df); df=df.drop_duplicates(subset=keys,keep="last")
            rejected += before-len(df)
            df.to_sql(table,conn,if_exists="replace",index=False)
            rows_out=len(df)
            audits.append({"table":table,"rows_in":rows_in,"rows_out":rows_out,"rejected":rejected,"runtime_s":round(time.perf_counter()-t,4)})
        except Exception as e:
            logger.exception("Failed to load %s",table); audits.append({"table":table,"rows_in":rows_in,"rows_out":0,"rejected":rows_in,"runtime_s":round(time.perf_counter()-t,4)}); failures.append({"company_id":"","year":"","field":"table","issue":str(e),"severity":"CRITICAL"})
    # ensure indexes and FK-like checks even though pandas creates tables without constraints
    for sql in [
        "CREATE INDEX IF NOT EXISTS idx_pl_company_year ON profitandloss(company_id,year)",
        "CREATE INDEX IF NOT EXISTS idx_bs_company_year ON balancesheet(company_id,year)",
        "CREATE INDEX IF NOT EXISTS idx_cf_company_year ON cashflow(company_id,year)",
        "CREATE INDEX IF NOT EXISTS idx_ratios_company_year ON financial_ratios(company_id,year)",
    ]: conn.execute(sql)
    conn.commit(); conn.close()
    pd.DataFrame(audits).to_csv(data_root/"load_audit.csv",index=False)
    pd.DataFrame(failures,columns=["company_id","year","field","issue","severity"]).to_csv(data_root/"validation_failures.csv",index=False)
    pd.DataFrame(rejected_rows,columns=["table","company_id","year","reason","severity"]).to_csv(data_root/"rejected_rows.csv",index=False)
    return audits
