import pytest
from src.etl.normaliser import normalize_year,normalize_ticker
@pytest.mark.parametrize('raw,expected',[('Mar-23','2023-03'),('Mar 23','2023-03'),('March-2023','2023-03'),(2023,'2023-03'),('FY23','2023-03'),('Dec-22','2022-12'),('Jun-23','2023-06'),('2023-03','2023-03'),('FY24','2024-03'),('Apr-24','2024-04'),('Jan-20','2020-01'),('Sep-19','2019-09'),('Oct-2022','2022-10'),('Nov-21','2021-11'),('Feb-2020','2020-02'),('Jul-18','2018-07'),('Aug-17','2017-08'),('May-16','2016-05'),('Mar-15','2015-03'),('garbage','PARSE_ERROR')])
def test_year(raw,expected): assert normalize_year(raw)==expected
@pytest.mark.parametrize('raw,expected',[('  TCS ','TCS'),('tcs','TCS'),('BAJAJ-AUTO','BAJAJ-AUTO'),('M&M','M&M'),(' INFY','INFY'),('RELIANCE ','RELIANCE'),('hdfcbank','HDFCBANK'),('ICICIBANK','ICICIBANK'),('sbIn','SBIN'),('TATAMOTORS','TATAMOTORS'),('  ABB  ','ABB'),('LTIM','LTIM'),('ONGC','ONGC'),('GAIL','GAIL'),('NESTLEIND','NESTLEIND')])
def test_ticker(raw,expected): assert normalize_ticker(raw)==expected
