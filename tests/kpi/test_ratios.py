import pytest, numpy as np
from src.analytics.cagr import safe_cagr
from src.analytics.ratios import capital_pattern
@pytest.mark.parametrize('a,b,e',[(100,161,10),(100,121,10),(100,200,5),(100,110,3),(50,100,3),(100,90,3),(100,150,10),(10,20,3),(200,300,5),(100,133.1,3)])
def test_cagr_normal(a,b,e): assert abs(safe_cagr(a,b,e)[0]-((b/a)**(1/e)-1)*100)<1e-9
@pytest.mark.parametrize('a,b,flag',[(-100,200,'TURNAROUND'),(-100,-50,'BOTH_NEGATIVE'),(100,-50,'DECLINE_TO_LOSS'),(0,100,'ZERO_BASE'),(100,100,'')])
def test_cagr_edges(a,b,flag): assert safe_cagr(a,b,5)[1]==flag
@pytest.mark.parametrize('a,b,e,flag',[(100,161,5,''),(100,161,2,'INSUFFICIENT'),(None,10,5,'MISSING')])
def test_cagr_more(a,b,e,flag): assert safe_cagr(a,b,e)[1]==flag
@pytest.mark.parametrize('cfo,cfi,cff,label',[(1,-1,-1,'Reinvestor / Returns'),(1,-1,1,'Growth Funded'),(1,1,-1,'Asset Monetiser'),(1,1,1,'Cash Accumulator'),(-1,1,1,'Distress Signal'),(-1,-1,1,'Distress Signal'),(-1,1,-1,'Restructuring'),(-1,-1,-1,'Mixed / Neutral')])
def test_capital_pattern(cfo,cfi,cff,label):
    class R: pass
    r=R(); r.operating_activity=cfo;r.investing_activity=cfi;r.financing_activity=cff
    assert capital_pattern(r)==label
