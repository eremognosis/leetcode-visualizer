import json
import pydantic
from pathlib import Path
from .schemas import *
from typing import Optional, Tuple, List
from pandas import DataFrame, merge


def load_and_validate(
    sub_path: Path,
    ques_path: Path,
) -> Tuple[List[SubmissionRecord], List[QuestionNode]]:
    with open(sub_path, "r") as f:
        sr = json.load(f)
        if isinstance(sr, dict):  # for cases of only one
            sr = [sr]
        submissions = [SubmissionRecord.model_validate(item) for item in sr]

    with open(ques_path, "r") as f:
        qr = json.load(f)
        if isinstance(qr, dict):
            qr = [qr]
        questions = [QuestionNode.model_validate(item) for item in qr]

    return submissions, questions


def create_dataframe(
    submissions: List[SubmissionRecord], questions: List[QuestionNode]
) -> DataFrame:
    df_sub = DataFrame([s.model_dump() for s in submissions])
    df_ques = DataFrame([q.model_dump() for q in questions])

    df_ques["tag_slugs"] = [q.tag_slugs for q in questions]
    df_sub = df_sub.drop(columns=["runtime_str", "memory_str", "timestamp_raw"])

    merged_df = merge(
        df_sub, df_ques, on="titleSlug", how="inner", suffixes=("_sub", "_q")
    )

    return merged_df
