from datetime import datetime, time
from pathlib import Path

from flask import Flask, render_template, request

from src.combine import combine_analyses
from src.io import create_dataframe, load_and_validate
from src.p1 import filter_dataset


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)

submissions, questions = load_and_validate(
    BASE_DIR / "sample/subs.json",
    BASE_DIR / "sample/ques.json",
)
DATAFRAME = create_dataframe(submissions, questions)


def _visuals(analysis: dict, filtered) -> dict:
    def counts(values: dict) -> dict:
        return {str(key): value for key, value in values.items()}

    markov = analysis["markov"]
    markov_columns = sorted({column for row in markov.values() for column in row})
    runtime_by_difficulty = analysis["runtime_memory"].get("diff_b", {})
    language_coefficients = (
        analysis["advanced"]["performance"]
        .get("language_benchmark", {})
        .get("coefficients", {})
    )
    language_coefficients = {
        key.removeprefix("lang_"): value
        for key, value in language_coefficients.items()
        if key.startswith("lang_")
    }

    return {
        "difficulty_sub": counts(analysis["summary"].get("difficulty_sub", {})),
        "difficulty_questions": counts(analysis["summary"].get("difficulty_ques", {})),
        "languages": counts(analysis["summary"].get("lang_sub", {})),
        "statuses": counts(filtered["statusDisplay"].value_counts().to_dict()),
        "hourwise": counts(analysis["timing"].get("hourwise", {})),
        "daywise": counts(analysis["timing"].get("daywise", {})),
        "markov": {
            "columns": markov_columns,
            "rows": [
                {
                    "label": label,
                    "values": [row.get(column, 0) for column in markov_columns],
                }
                for label, row in markov.items()
            ],
        },
        "runtime": {
            "labels": list(runtime_by_difficulty),
            "mean": [
                values.get("runtime_mean", 0)
                for values in runtime_by_difficulty.values()
            ],
            "median": [
                values.get("runtime_median", 0)
                for values in runtime_by_difficulty.values()
            ],
        },
        "survival": {
            "labels": [
                point["time_seconds"]
                for point in analysis["advanced"]["survival"].get("kaplan_meier", [])
            ],
            "values": [
                point["survival_probability"]
                for point in analysis["advanced"]["survival"].get("kaplan_meier", [])
            ],
        },
        "language_coefficients": language_coefficients,
        "outliers": analysis["advanced"]["performance"].get("outliers", []),
    }


def _date_value(name: str, end_of_day: bool = False) -> datetime | None:
    value = request.form.get(name, "").strip()
    if not value:
        return None
    parsed = datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.combine(parsed, time.max if end_of_day else time.min)


@app.route("/", methods=["GET", "POST"])
def dashboard():
    from_date = _date_value("from_date") if request.method == "POST" else None
    to_date = (
        _date_value("to_date", end_of_day=True) if request.method == "POST" else None
    )
    languages = request.form.getlist("languages") if request.method == "POST" else []
    status = request.form.get("status", "") if request.method == "POST" else ""
    difficulty = request.form.get("difficulty", "") if request.method == "POST" else ""

    filtered = filter_dataset(
        DATAFRAME,
        from_date=from_date,
        to_date=to_date,
        languages=languages or None,
        status=status or None,
        difficulty=difficulty or None,
    )
    analysis = combine_analyses(filtered)

    return render_template(
        "dashboard.html",
        analysis=analysis,
        visuals=_visuals(analysis, filtered),
        row_count=len(filtered),
        total_count=len(DATAFRAME),
        languages=sorted(DATAFRAME["lang"].dropna().unique().tolist()),
        statuses=sorted(DATAFRAME["statusDisplay"].dropna().unique().tolist()),
        difficulties=sorted(DATAFRAME["difficulty"].dropna().unique().tolist()),
        selected_languages=languages,
        selected_status=status,
        selected_difficulty=difficulty,
        selected_from=request.form.get("from_date", "")
        if request.method == "POST"
        else "",
        selected_to=request.form.get("to_date", "") if request.method == "POST" else "",
    )


if __name__ == "__main__":
    app.run(debug=True)
