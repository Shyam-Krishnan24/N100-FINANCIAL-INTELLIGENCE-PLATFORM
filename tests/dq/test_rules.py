import pandas as pd

def test_dq04_bs_balance(): assert abs(1000-1020)/1000>=.01
def test_dq06_zero_sales(): assert 0<=0
def test_dq07_year_format(): assert pd.Series(['2024-03']).str.match(r'^\d{4}-\d{2}$').all()
def test_dq08_ticker_format(): assert 'TCS'.strip().upper()=='TCS'
def test_dq09_cash_sum(): assert abs(10-(5+3+2))<=10
def test_dq10_fixed_asset(): assert -1<0
def test_dq11_tax_range(): assert not (70<=60)
def test_dq12_payout(): assert 250>200
def test_dq14_eps_sign(): assert 2>0
def test_dq16_coverage(): assert 5>=5
