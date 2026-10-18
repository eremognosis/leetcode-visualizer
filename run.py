from textwrap import indent
import json
from src.io import *
import pandas as pd
from src.p1 import *
from src.combine import combine_analyses

p, q = load_and_validate(Path("format/subs.json"), Path("format/ques.json"))
df = create_dataframe(p, q)
# df = filter_dataset(df, from_date=datetime(month=9, day=1, year=2026))
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

with open("format/output.json", "w") as f:
    json.dump(combine_analyses(df), fp = f, indent=4)