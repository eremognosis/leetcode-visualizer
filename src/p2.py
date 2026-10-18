import pandas as pd
import numpy as np


def compute_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"count": 0, "runtime": {}, "memory": {}}
    diff_sub_cnt = df["difficulty"].value_counts().to_dict()
    diff_ques_cnt = df.groupby("difficulty")["titleSlug"].nunique().to_dict()

    lang_sub_cnt = df["lang"].value_counts().to_dict()
    lang_ques_cnt = df.groupby("lang")["titleSlug"].nunique().to_dict()
    df["tag_slug"] = df["topicTags"].apply(lambda tags: [t["slug"] for t in tags or []])
    exp = df.explode("tag_slug")
    tag_summary = (
        exp.groupby("tag_slug")
        .agg(
            total_sub=("titleSlug", "count"),
            unique_questions=("titleSlug", "nunique"),
        )
        .reset_index()
        .sort_values("total_sub", ascending=False, ignore_index=True)
    ).to_dict(orient="records")

    dfs = df.sort_values(by=["titleSlug", "timestamp"], ascending=True)
    fatt = dfs.groupby("titleSlug").first().reset_index()
    tuniq = len(fatt)
    first_accept = (fatt["statusDisplay"] == "Accepted").sum()
    facc_rate = 0.0
    if tuniq > 0:
        facc_rate = 100.0 * first_accept / tuniq

    return {
        "count": len(df),
        "runtime": {
            "mean": float(df["runtime_ms"].mean()),
            "meadian": float(df["runtime_ms"].median()),
            "std": float(df["runtime_ms"].std()),
            "p5": float(df["runtime_ms"].quantile(0.05)),
            "p25": float(df["runtime_ms"].quantile(0.25)),
            "p75": float(df["runtime_ms"].quantile(0.75)),
            "p95": float(df["runtime_ms"].quantile(0.95)),
        },
        "memory": {
            "mean": float(df["memory_mb"].mean()),
            "meadian": float(df["memory_mb"].median()),
            "std": float(df["memory_mb"].std()),
            "p5": float(df["memory_mb"].quantile(0.05)),
            "p25": float(df["memory_mb"].quantile(0.25)),
            "p75": float(df["memory_mb"].quantile(0.75)),
            "p95": float(df["memory_mb"].quantile(0.95)),
        },
        "difficulty_sub": diff_sub_cnt,
        "difficulty_ques": diff_ques_cnt,
        "lang_sub": lang_sub_cnt,
        "lang_ques": lang_ques_cnt,
        "tags": tag_summary,
        "acceptance": {
            "overall_rate": float(
                100.0 * len(df[df["statusDisplay"] == "Accepted"]) / len(df)
            ),
            "easy_rate": float(
                100.0
                * len(
                    df[
                        (df["statusDisplay"] == "Accepted")
                        & (df["difficulty"] == "EASY")
                    ]
                )
                / len(df[df["difficulty"] == "EASY"])
            ),
            "med_rate": float(
                100.0
                * len(
                    df[
                        (df["statusDisplay"] == "Accepted")
                        & (df["difficulty"] == "MEDIUM")
                    ]
                )
                / len(df[df["difficulty"] == "MEDIUM"])
            ),
            "hard_rate": float(
                100.0
                * len(
                    df[
                        (df["statusDisplay"] == "Accepted")
                        & (df["difficulty"] == "HARD")
                    ]
                )
                / len(df[df["difficulty"] == "HARD"])
            ),
            "first_attempt": float(facc_rate),
        },  # for now lets assume div by zero wont occur
    }


def submission_timing(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    # df["timestamp"] of datetime()

    df = df.sort_values("timestamp")
    ts = df["timestamp"]
    dates = ts.dt.date

    first = ts.min()
    last = ts.max()

    total_active = int(dates.nunique())
    total_span = (last - first).days + 1
    hours = ts.dt.hour

    hcnt = ts.dt.hour.value_counts().reindex(range(24), fill_value=0)
    peak_hr = f"{(hcnt.idxmax()):02d}:00"

    dow_map = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }
    day_counts = ts.dt.dayofweek.map(dow_map).value_counts().to_dict()
    peak_day = ts.dt.dayofweek.map(dow_map).mode()[0] if not ts.empty else None
    hw = {f"{h:02d}:00": int(count) for h, count in hcnt.items()}
    return {
        "summary": {
            "first_sub": first.strftime("%Y-%m-%d %H:%M:%S"),
            "last_sub": last.strftime("%Y-%m-%d %H:%M:%S"),
            "total_active": total_active,
            "total_span": total_span,
            "activity_density_pct": float(100.00 * total_active / total_span),
            "avg_sub_pd": float(len(df) / total_active),
        },
        "hourwise": hw,
        "daywise": day_counts,
        "peaks": {"hour": peak_hr, "weekday": peak_day},
    }
