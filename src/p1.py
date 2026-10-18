from datetime import datetime
from typing import Optional, List
import pandas as pd


def filter_dataset(
    df: pd.DataFrame,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    languages: Optional[List[str]] = None,
    status: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> pd.DataFrame:
    fdf = df.copy()

    if from_date:
        fdf = fdf[fdf["timestamp"] >= from_date]
    if to_date:
        fdf = fdf[fdf["timestamp"] <= to_date]
    if languages:
        fdf = fdf[fdf["lang"].isin(languages)]
    if status:
        fdf = fdf[fdf["statusDisplay"] == status]
    if difficulty:
        fdf = fdf[fdf["difficulty"] == difficulty.upper()]

    return fdf
