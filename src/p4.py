from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if pd.isna(value) if not isinstance(value, (list, dict)) else False:
        return None
    return value


def _tags(row: pd.Series) -> list[str]:
    tags = row.get("tag_slugs", [])
    if isinstance(tags, list):
        return [str(tag) for tag in tags]
    tags = row.get("topicTags", [])
    if isinstance(tags, list):
        return [
            str(tag.get("slug", tag)) if isinstance(tag, dict) else str(tag)
            for tag in tags
        ]
    return []


def tag_cooccurrence(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"tags": [], "matrix": {}, "communities": []}

    counts: dict[str, int] = {}
    edges: dict[tuple[str, str], int] = {}
    for _, row in df.drop_duplicates("titleSlug").iterrows():
        tags = sorted(set(_tags(row)))
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
        for left, right in combinations(tags, 2):
            edges[(left, right)] = edges.get((left, right), 0) + 1

    tags = sorted(counts)
    matrix = {tag: {other: 0 for other in tags} for tag in tags}
    for (left, right), count in edges.items():
        matrix[left][right] = count
        matrix[right][left] = count

    parent = {tag: tag for tag in tags}

    def find(tag: str) -> str:
        while parent[tag] != tag:
            parent[tag] = parent[parent[tag]]
            tag = parent[tag]
        return tag

    for (left, right), count in edges.items():
        if count > 0:
            root_left, root_right = find(left), find(right)
            if root_left != root_right:
                parent[root_right] = root_left
    communities: dict[str, list[str]] = {}
    for tag in tags:
        communities.setdefault(find(tag), []).append(tag)

    return {
        "tags": [{"tag": tag, "question_count": counts[tag]} for tag in tags],
        "matrix": matrix,
        "communities": sorted(
            communities.values(), key=lambda group: (-len(group), group)
        ),
    }


def survival_analysis(df: pd.DataFrame) -> dict:
    if df.empty or "timestamp" not in df:
        return {"observations": [], "kaplan_meier": [], "median_time_seconds": None}

    observations = []
    for slug, group in df.dropna(subset=["timestamp"]).groupby("titleSlug"):
        ordered = group.sort_values("timestamp")
        first_time = ordered["timestamp"].iloc[0]
        accepted = ordered[ordered["statusDisplay"].eq("Accepted")]
        end_time = (
            accepted["timestamp"].iloc[0]
            if not accepted.empty
            else ordered["timestamp"].iloc[-1]
        )
        observations.append(
            {
                "titleSlug": slug,
                "duration_seconds": float((end_time - first_time).total_seconds()),
                "event": int(not accepted.empty),
                "attempts": int(len(ordered)),
            }
        )

    durations = sorted({item["duration_seconds"] for item in observations})
    at_risk = len(observations)
    survival = 1.0
    curve = []
    for duration in durations:
        events = sum(
            item["event"] and item["duration_seconds"] == duration
            for item in observations
        )
        censored = sum(
            not item["event"] and item["duration_seconds"] == duration
            for item in observations
        )
        if at_risk and events:
            survival *= 1.0 - events / at_risk
        curve.append(
            {
                "time_seconds": duration,
                "survival_probability": float(survival),
                "at_risk": at_risk,
            }
        )
        at_risk -= events + censored

    median = next(
        (
            point["time_seconds"]
            for point in curve
            if point["survival_probability"] <= 0.5
        ),
        None,
    )
    return {
        "observations": observations,
        "kaplan_meier": curve,
        "median_time_seconds": median,
    }


def cox_attempt_model(df: pd.DataFrame) -> dict:
    if df.empty or "timestamp" not in df:
        return {"coefficients": {}, "sample_size": 0}
    work = df.copy()
    work["event"] = work["statusDisplay"].eq("Accepted").astype(float)
    work["acRate"] = pd.to_numeric(work["acRate"], errors="coerce").fillna(0.0)
    work["tag_count"] = work.apply(lambda row: len(_tags(row)), axis=1)
    difficulty = (
        work.get("difficulty", pd.Series(index=work.index, dtype=object))
        .map({"EASY": 1.0, "MEDIUM": 2.0, "HARD": 3.0})
        .fillna(2.0)
    )
    features = pd.DataFrame(
        {
            "acRate": work["acRate"],
            "tag_count": work["tag_count"],
            "difficulty": difficulty,
        },
        index=work.index,
    )
    work = work.dropna(subset=["timestamp"]).sort_values("timestamp")
    x = features.loc[work.index].to_numpy(dtype=float)
    x = (x - x.mean(axis=0)) / (x.std(axis=0) + 1e-9)
    times = work["timestamp"].astype("int64").to_numpy()
    events = work["event"].to_numpy(dtype=bool)
    beta = np.zeros(x.shape[1])
    for _ in range(30):
        linear = np.clip(x @ beta, -30, 30)
        risk_weight = np.exp(linear)
        gradient = np.zeros(x.shape[1])
        hessian = np.zeros((x.shape[1], x.shape[1]))
        for index in np.flatnonzero(events):
            risk = times >= times[index]
            weights = risk_weight[risk]
            risk_x = x[risk]
            total = weights.sum() + 1e-9
            mean_x = (weights[:, None] * risk_x).sum(axis=0) / total
            gradient += x[index] - mean_x
            second_moment = (
                weights[:, None, None] * risk_x[:, :, None] * risk_x[:, None, :]
            ).sum(axis=0) / total
            hessian -= second_moment - np.outer(mean_x, mean_x)
        beta += np.linalg.solve(-hessian + np.eye(x.shape[1]) * 1e-5, gradient)
    return {
        "coefficients": {
            name: float(value) for name, value in zip(features.columns, beta)
        },
        "sample_size": len(work),
        "events": int(events.sum()),
    }


def performance_analysis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"outliers": [], "language_benchmark": {}}
    work = df.copy()
    work["runtime_ms"] = pd.to_numeric(work["runtime_ms"], errors="coerce")
    work["memory_mb"] = pd.to_numeric(work["memory_mb"], errors="coerce")
    outliers = []
    for slug, group in work.groupby("titleSlug"):
        for metric in ("runtime_ms", "memory_mb"):
            valid = group.dropna(subset=[metric])
            if len(valid) < 2:
                continue
            median = valid[metric].median()
            deviation = (valid[metric] - median).abs().median()
            scale = 1.4826 * deviation if deviation else valid[metric].std()
            if not scale or pd.isna(scale):
                continue
            for index, row in valid.loc[
                (valid[metric] - median).abs() > 3 * scale
            ].iterrows():
                submission_id = row.get("id_sub", row.get("id"))
                if pd.isna(submission_id):
                    submission_id = row.get("id")
                outliers.append(
                    {
                        "titleSlug": slug,
                        "id": submission_id,
                        "metric": metric,
                        "value": row[metric],
                        "median": median,
                        "z_score": (row[metric] - median) / scale,
                    }
                )

    valid = work.dropna(subset=["runtime_ms", "lang"]).copy()
    if valid.empty:
        benchmark = {}
    else:
        valid["difficulty_score"] = (
            valid["difficulty"].map({"EASY": 1, "MEDIUM": 2, "HARD": 3}).fillna(2)
        )
        valid["log_runtime"] = np.log1p(valid["runtime_ms"])
        design = pd.get_dummies(
            valid[["difficulty_score", "lang"]], columns=["lang"], dtype=float
        )
        coefficients = np.linalg.lstsq(
            np.column_stack([np.ones(len(design)), design]),
            valid["log_runtime"],
            rcond=None,
        )[0]
        benchmark = {
            "coefficients": {
                "intercept": float(coefficients[0]),
                **{
                    str(name): float(value)
                    for name, value in zip(design.columns, coefficients[1:])
                },
            },
            "sample_size": len(valid),
        }
    return {
        "outliers": [_json_value(item) for item in outliers],
        "language_benchmark": benchmark,
    }


def habit_analysis(df: pd.DataFrame) -> dict:
    if df.empty or df["timestamp"].dropna().empty:
        return {"sessions": [], "streaks": [], "decay": {}}
    work = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    gaps = work["timestamp"].diff().dt.total_seconds().dropna()
    sessions = int((gaps > 2 * 3600).sum() + 1)
    active_dates = sorted(work["timestamp"].dt.date.unique())
    streaks, current = [], 1
    for previous, current_date in zip(active_dates, active_dates[1:]):
        if (current_date - previous).days == 1:
            current += 1
        else:
            streaks.append(current)
            current = 1
    streaks.append(current)
    work["accepted"] = work["statusDisplay"].eq("Accepted").astype(float)
    daily = (
        work.groupby(work["timestamp"].dt.date)["accepted"]
        .mean()
        .reset_index(name="acceptance_rate")
    )
    daily["day_index"] = np.arange(len(daily))
    decay = (
        float(np.polyfit(daily["day_index"], daily["acceptance_rate"], 1)[0])
        if len(daily) > 1
        else 0.0
    )
    short_gaps = gaps[gaps <= 2 * 3600]
    excitation = float(len(short_gaps) / len(gaps)) if not gaps.empty else 0.0
    return {
        "sessions": [
            {
                "session_count": sessions,
                "mean_gap_seconds": float(gaps.mean()) if not gaps.empty else 0.0,
                "poisson_rate_per_day": float(
                    len(work) / work["timestamp"].dt.date.nunique()
                ),
                "hawkes_excitation_proxy": excitation,
            }
        ],
        "streaks": sorted(streaks, reverse=True),
        "decay": {"daily_acceptance_slope": decay, "active_days": len(daily)},
    }


def irt_model(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"ability": 0.0, "problem_difficulty": {}, "sample_size": 0}
    work = df.copy()
    ac_rate = work["acRate"] if "acRate" in work else pd.Series(0.5, index=work.index)
    work["acRate"] = (
        pd.to_numeric(ac_rate, errors="coerce").fillna(0.5).clip(0.001, 0.999)
    )
    theta = 0.0
    difficulty = {
        slug: float(-np.log(rate / (1 - rate)))
        for slug, rate in work.groupby("titleSlug")["acRate"].first().items()
    }
    for _ in range(25):
        for _, row in work.iterrows():
            slug = row["titleSlug"]
            outcome = float(row["statusDisplay"] == "Accepted")
            probability = 1.0 / (
                1.0 + np.exp(np.clip(difficulty[slug] - theta, -30, 30))
            )
            error = outcome - probability
            theta += 0.03 * error
            difficulty[slug] -= 0.03 * error
    return {
        "ability": float(theta),
        "problem_difficulty": difficulty,
        "sample_size": len(work),
    }


def advanced_analytics(df: pd.DataFrame) -> dict:
    return _json_value(
        {
            "cooccurrence": tag_cooccurrence(df),
            "survival": survival_analysis(df),
            "cox_model": cox_attempt_model(df),
            "performance": performance_analysis(df),
            "habits": habit_analysis(df),
            "irt": irt_model(df),
        }
    )
