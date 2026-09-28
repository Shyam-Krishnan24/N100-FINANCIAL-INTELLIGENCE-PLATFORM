"""Generate company, sector and portfolio PDF reports plus charts."""
from pathlib import Path
import sqlite3, os, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

PAGE=A4; styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name="Small",parent=styles["BodyText"],fontSize=8,leading=10)); styles.add(ParagraphStyle(name="Tiny",parent=styles["BodyText"],fontSize=6.5,leading=8))
def fmt(v,d=1):
    return "N/A" if pd.isna(v) else f"{v:.{d}f}"

def q(db,sql,params=()):
    con=sqlite3.connect(db); d=pd.read_sql_query(sql,con,params=params); con.close(); return d

def valuation(db, out):
    """Create valuation summary and flags."""
    r=q(db,"select * from financial_ratios"); s=q(db,"select company_id,broad_sector from sectors"); c=q(db,"select id,company_name from companies")
    latest=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).copy().merge(s,on="company_id").merge(c,left_on="company_id",right_on="id")
    allm=r.merge(s,on="company_id"); med=allm.groupby(["broad_sector","year"]).pe_ratio.median().reset_index(name="sector_median_pe"); latest["year_cal"]=latest.year.str[:4].astype(int); latest=latest.merge(med.sort_values("year").groupby("broad_sector",as_index=False).tail(1)[["broad_sector","sector_median_pe"]],on="broad_sector",how="left")
    latest["valuation_flag"]=np.select([latest.pe_ratio>latest.sector_median_pe*1.5,latest.pe_ratio<latest.sector_median_pe*.7],["Caution","Discount"],default="Neutral")
    latest["fcf_yield_pct"]=latest.fcf_yield_pct
    cols=[c for c in ["company_id","company_name","broad_sector","pe_ratio","pb_ratio","ev_ebitda","dividend_yield_pct","sector_median_pe","fcf_yield_pct","valuation_flag"] if c in latest]
    latest[cols].to_excel(Path(out)/"valuation_summary.xlsx",index=False); latest[latest.valuation_flag!="Neutral"][cols].to_csv(Path(out)/"valuation_flags.csv",index=False)

def radar_charts(db, outdir):
    """Generate 92 peer radar charts where peer coverage exists."""
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True); r=q(db,"select * from financial_ratios"); pg=q(db,"select * from peer_groups"); latest=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1); metrics=["return_on_equity_pct","return_on_capital_employed_pct","net_profit_margin_pct","debt_to_equity","free_cash_flow_cr","pat_cagr_5yr","revenue_cagr_5yr","eps_cagr_5yr"]
    for _,row in latest.iterrows():
        ticker=row.company_id; groups=pg[pg.company_id==ticker].peer_group_name.tolist(); group=groups[0] if groups else None; members=pg[pg.peer_group_name==group].company_id.tolist() if group else []
        sub=latest[latest.company_id.isin(members)] if members else pd.DataFrame()
        vals=[]; avg=[]
        for m in metrics:
            x=float(row[m]) if pd.notna(row[m]) else 0; vals.append(x); avg.append(float(sub[m].median()) if not sub.empty else x)
        vals=np.array(vals); avg=np.array(avg); mx=np.maximum(np.abs(np.r_[vals,avg]),1); vals=vals/mx.max(); avg=avg/mx.max(); angles=np.linspace(0,2*np.pi,len(metrics),endpoint=False).tolist(); angles+=angles[:1]
        fig=plt.figure(figsize=(5,5)); ax=fig.add_subplot(111,polar=True); ax.plot(angles,np.r_[vals,vals[0]],label=ticker); ax.plot(angles,np.r_[avg,avg[0]],label="Peer median"); ax.set_xticks(angles[:-1]); ax.set_xticklabels([m.replace("_"," ")[:12] for m in metrics],fontsize=7); ax.legend(loc="upper right",bbox_to_anchor=(1.25,1.1),fontsize=7); fig.tight_layout(); fig.savefig(outdir/f"{ticker}.png",dpi=120); plt.close(fig)

def company_pdf(db,ticker,path,radar=None):
    """Create a compact two-page company tearsheet with KPI and trend tables."""
    c=q(db,"select * from companies where id=?",(ticker,)); r=q(db,"select * from financial_ratios where company_id=? order by year",(ticker,)); sec=q(db,"select * from sectors where company_id=?",(ticker,)); pros=q(db,"select * from pros_cons_generated where company_id=? and type='pro'",(ticker,)); cons=q(db,"select * from pros_cons_generated where company_id=? and type='con'",(ticker,))
    if c.empty: return
    c=c.iloc[0]; latest=r.iloc[-1]; sector=sec.iloc[0].broad_sector if not sec.empty else 'Unassigned'; subsec=sec.iloc[0].sub_sector if not sec.empty else '—'
    story=[Paragraph(f"<b>{ticker} — {c.company_name}</b>",styles["Title"]),Paragraph(f"Sector: {sector} | Sub-sector: {subsec}",styles["BodyText"]),Spacer(1,.15*cm),Paragraph(str(c.about_company or ""),styles["Small"]),Spacer(1,.2*cm)]
    kpis=[["ROE","ROCE","NPM","D/E","FCF (Cr)","Rev CAGR 5Y"],[fmt(latest.return_on_equity_pct)+"%",fmt(latest.return_on_capital_employed_pct)+"%",fmt(latest.net_profit_margin_pct)+"%",fmt(latest.debt_to_equity,2),"N/A" if pd.isna(latest.free_cash_flow_cr) else f"{latest.free_cash_flow_cr:,.0f}",fmt(latest.revenue_cagr_5yr)+"%" if pd.notna(latest.revenue_cagr_5yr) else "N/A"]]
    t=Table(kpis,colWidths=[2.7*cm]*6); t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("ALIGN",(0,0),(-1,-1),"CENTER"),("FONTSIZE",(0,0),(-1,-1),8)])); story += [t,Spacer(1,.2*cm),Paragraph("10-Year Financial Trend",styles["Heading2"])]
    trend=[["Year","Revenue","Profit","ROE","ROCE","FCF"]]
    for _,x in r.tail(10).iterrows(): trend.append([str(x.year),f"{x.sales:,.0f}",f"{x.net_profit:,.0f}",fmt(x.return_on_equity_pct),fmt(x.return_on_capital_employed_pct),"N/A" if pd.isna(x.free_cash_flow_cr) else f"{x.free_cash_flow_cr:,.0f}"])
    tt=Table(trend,repeatRows=1,colWidths=[2*cm,3*cm,3*cm,2.3*cm,2.3*cm,3*cm]); tt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.25,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("FONTSIZE",(0,0),(-1,-1),7)])); story.append(tt); story.append(Spacer(1,.2*cm)); story.append(Paragraph(f"Financial health score: {fmt(latest.financial_health_score)} | Band: {latest.health_band}",styles["BodyText"])); story.append(PageBreak())
    story += [Paragraph("Balance Sheet & Cash Flow Intelligence",styles["Heading1"])]
    bs=q(db,"select * from balancesheet where company_id=? order by year",(ticker,)).tail(5); cf=q(db,"select * from cashflow where company_id=? order by year",(ticker,)).tail(5)
    bdata=[["Year","Equity","Debt","Assets","Liabilities"]]+[[str(x.year),f"{x.equity_capital+x.reserves:,.0f}",f"{x.borrowings:,.0f}",f"{x.total_assets:,.0f}",f"{x.total_liabilities:,.0f}"] for _,x in bs.iterrows()]
    bt=Table(bdata,repeatRows=1,colWidths=[2.3*cm,3.2*cm,3.2*cm,3.2*cm,3.2*cm]); bt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.25,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("FONTSIZE",(0,0),(-1,-1),7)])); story += [Paragraph("Recent Balance Sheet",styles["Heading2"]),bt,Spacer(1,.2*cm)]
    cdata=[["Year","CFO","CFI","CFF","Net Cash"]]+[[str(x.year),f"{x.operating_activity:,.0f}",f"{x.investing_activity:,.0f}",f"{x.financing_activity:,.0f}",f"{x.net_cash_flow:,.0f}"] for _,x in cf.iterrows()]
    ct=Table(cdata,repeatRows=1,colWidths=[2.3*cm,3.2*cm,3.2*cm,3.2*cm,3.2*cm]); ct.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.25,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("FONTSIZE",(0,0),(-1,-1),7)])); story += [Paragraph("Recent Cash Flow",styles["Heading2"]),ct,Spacer(1,.15*cm),Paragraph(f"Capital allocation: <b>{latest.capital_allocation_pattern}</b>",styles["BodyText"]),Paragraph(f"CFO quality score: {fmt(latest.cfo_quality_score,0)} | CapEx intensity: {fmt(latest.capex_intensity_pct)}% | FCF conversion: {fmt(latest.fcf_conversion_rate_pct)}%",styles["Small"]),Spacer(1,.15*cm),Paragraph("Pros",styles["Heading3"]),Paragraph("; ".join(pros.text.head(5).tolist()) or "No configured positive rule triggered.",styles["Small"]),Paragraph("Cons",styles["Heading3"]),Paragraph("; ".join(cons.text.head(5).tolist()) or "No configured risk rule triggered.",styles["Small"])]
    if radar and Path(radar).exists(): story += [Spacer(1,.1*cm),Image(str(radar),width=7.5*cm,height=7.5*cm)]
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=1.2*cm,leftMargin=1.2*cm,topMargin=1.1*cm,bottomMargin=1.1*cm).build(story)

def sector_reports(db,outdir):
    """Generate one PDF per broad sector."""
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True); c=q(db,"select * from companies"); s=q(db,"select * from sectors"); r=q(db,"select * from financial_ratios")
    latest=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1)
    for sector in s.broad_sector.dropna().unique():
        sub=s[s.broad_sector==sector].merge(c,left_on="company_id",right_on="id").merge(latest,on="company_id",how="left"); story=[Paragraph(f"{sector} — Sector Report",styles["Title"]),Paragraph(f"Companies: {len(sub)} | Median ROE: {sub.return_on_equity_pct.median():.1f}% | Median P/E: {sub.pe_ratio.median():.1f}x",styles["BodyText"]),Spacer(1,.3*cm)]
        data=[["Ticker","Company","ROE","ROCE","NPM","D/E","P/E","FCF"]]+[[x.company_id,str(x.company_name)[:28],fmt(x.return_on_equity_pct),fmt(x.return_on_capital_employed_pct),f"{x.net_profit_margin_pct:.1f}",f"{x.debt_to_equity:.2f}",f"{x.pe_ratio:.1f}" if pd.notna(x.pe_ratio) else "N/A","N/A" if pd.isna(x.free_cash_flow_cr) else f"{x.free_cash_flow_cr:,.0f}"] for _,x in sub.sort_values("return_on_equity_pct",ascending=False).iterrows()]
        t=Table(data,repeatRows=1,colWidths=[1.6*cm,5.1*cm,1.4*cm,1.4*cm,1.4*cm,1.4*cm,1.4*cm,2.2*cm])
        t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.25,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        story.append(t)
        SimpleDocTemplate(str(outdir/f"{sector.replace('/','_').replace(' ','_')}_report.pdf"),pagesize=A4,rightMargin=1*cm,leftMargin=1*cm,topMargin=1*cm,bottomMargin=1*cm).build(story)

def portfolio_report(db,path):
    """Generate the all-company portfolio summary PDF."""
    c=q(db,"select * from companies"); s=q(db,"select * from sectors"); r=q(db,"select * from financial_ratios"); latest=r.sort_values(["company_id","year"]).groupby("company_id",as_index=False).tail(1).merge(s,on="company_id").merge(c,left_on="company_id",right_on="id")
    story=[]
    for _,x in latest.iterrows():
        story += [Paragraph(f"{x.company_id} — {x.company_name}",styles["Title"]),Paragraph(f"Sector: {x.broad_sector} | ROE {x.return_on_equity_pct:.1f}% | ROCE {x.return_on_capital_employed_pct:.1f}% | NPM {x.net_profit_margin_pct:.1f}% | D/E {x.debt_to_equity:.2f} | FCF {x.free_cash_flow_cr:,.0f} Cr",styles["BodyText"]),Spacer(1,.4*cm),Paragraph("Portfolio summary generated from the latest available analytical year. Refer to the underlying database for full history.",styles["Small"]),PageBreak()]
    if story: story.pop()
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=1.5*cm,leftMargin=1.5*cm,topMargin=1.5*cm,bottomMargin=1.5*cm).build(story)

def generate_all(db,project_root):
    """Generate all report deliverables."""
    root=Path(project_root); out=root/"output"; out.mkdir(exist_ok=True); valuation(db,out); radar_charts(db,root/"reports/radar_charts")
    c=q(db,"select id from companies");
    for ticker in c.id: company_pdf(db,ticker,root/f"reports/tearsheets/{ticker}_tearsheet.pdf",root/f"reports/radar_charts/{ticker}.png")
    sector_reports(db,root/"reports/sector"); portfolio_report(db,root/"reports/portfolio/portfolio_summary.pdf")
