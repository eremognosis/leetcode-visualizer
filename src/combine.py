from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .p2 import compute_summary, submission_timing
from .p3 import markov, runtime_mem
from .p4 import advanced_analytics


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return [_normalize(item) for item in value.tolist()]
    if pd.isna(value) if not isinstance(value, (list, dict)) else False:
        return None
    return value


def combine_analyses(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "summary": compute_summary(df),
            "timing": submission_timing(df),
            "markov": {},
            "runtime_memory": {},
            "advanced": advanced_analytics(df),
        }

    return _normalize(
        {
            "summary": compute_summary(df.copy()),
            "timing": submission_timing(df.copy()),
            "markov": markov(df.copy()),
            "runtime_memory": runtime_mem(df.copy()),
            "advanced": advanced_analytics(df.copy()),
        }
    )
