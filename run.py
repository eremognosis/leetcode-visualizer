from textwrap import indent

from src.io import *
import pandas as pd
from src.p1 import *
from src.combine import combine_analyses

p, q = load_and_validate(Path("sample/subs.json"), Path("sample/ques.json"))
df = create_dataframe(p, q)
df = filter_dataset(df, from_date=datetime(month=9, day=1, year=2026))
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

print(combine_analyses(df))
