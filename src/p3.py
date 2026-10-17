import pandas as pd


def markov(df: pd.DataFrame):
    if df.empty:
        return {}
    df_s = df.sort_values(["titleSlug", "timestamp"], ascending=True)
    df_s["next_st"] = df_s.groupby("titleSlug")["statusDisplay"].shift(-1)
    transition_counts = (
        df_s.dropna(subset=["next_st"])
        .groupby(["statusDisplay", "next_st"])
        .size()
        .unstack(fill_value=0)
    )
    stats = pd.DataFrame()
    if not transition_counts.empty:
        stats = transition_counts.div(transition_counts.sum(axis=1), axis=0) * 100.0
    return stats.transpose().to_dict()


def runtime_mem(df: pd.DataFrame):
    if df.empty:
        return {}
    df = df.copy()

    df["runtime_ms"] = pd.to_numeric(df["runtime_ms"], errors="coerce")
    df["memory_mb"] = pd.to_numeric(df["memory_mb"], errors="coerce")
    vdf = df.dropna(subset=["runtime_ms", "memory_mb"])
    if vdf.empty:
        return {}

    pearson_corr = vdf["runtime_ms"].corr(vdf["memory_mb"], method="pearson")
    spearman_corr = vdf["runtime_ms"].corr(vdf["memory_mb"], method="spearman")

    scd = vdf[["runtime_ms", "memory_mb", "difficulty"]].to_dict(orient="records")

    diff_g = vdf.groupby("difficulty").agg(
        sample_count=("runtime_ms", "count"),
            runtime_mean=("runtime_ms", "mean"),
            runtime_median=("runtime_ms", "median"),
            runtime_std=("runtime_ms", "std"),
            runtime_min=("runtime_ms", "min"),
            runtime_max=("runtime_ms", "max"),
            memory_mean=("memory_mb", "mean"),
            memory_median=("memory_mb", "median"),
            memory_std=("memory_mb", "std"),
            memory_min=("memory_mb", "min"),
            memory_max=("memory_mb", "max"),
    )

    diffs = (diff_g.fillna(0.0).to_dict(orient="index"))

    return {
        "corr" : {
            "pearson" : float(pearson_corr) if pd.notna(pearson_corr) else 0.0,
            "spearman" : float(spearman_corr) if pd.notna(spearman_corr) else 0.0,
            "sample_size" : len(vdf)
        },
        "diff_b" : diffs,
        # "scatter_pt" : scd
    }