"""Normalisation utilities for Nifty 100 source data."""
import re
from typing import Any
import pandas as pd

def normalize_ticker(value: Any) -> str:
    """Strip and uppercase an NSE ticker."""
    if pd.isna(value):
        return "MISSING"
    return str(value).strip().upper()

def normalize_year(value: Any) -> str:
    """Normalise financial year labels to YYYY-MM."""
    if pd.isna(value):
        return "PARSE_ERROR"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 1900 <= int(value) <= 2100:
            return f"{int(value):04d}-03"
    s = str(value).strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        return s
    m = re.fullmatch(r"FY\s*(\d{2,4})", s, re.I)
    if m:
        y = int(m.group(1)); y = y + 2000 if y < 100 else y
        return f"{y:04d}-03"
    m = re.fullmatch(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[- ](\d{2,4})", s, re.I)
    if m:
        mon = pd.to_datetime(m.group(1), format="%b").month
        y = int(m.group(2)); y = y + 2000 if y < 100 else y
        return f"{y:04d}-{mon:02d}"
    m = re.fullmatch(r"(\d{4})", s)
    if m:
        return f"{int(m.group(1)):04d}-03"
    return "PARSE_ERROR"

def normalize_core_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise common company and year fields."""
    out = df.copy()
    if "company_id" in out.columns:
        out["company_id"] = out["company_id"].map(normalize_ticker)
    if "year" in out.columns:
        out["year"] = out["year"].map(normalize_year)
    return out
