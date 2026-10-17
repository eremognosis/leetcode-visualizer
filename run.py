from textwrap import indent

from src.io import *
import pandas as pd
from src.p1 import *
from src.p2 import *
from src.p3 import *

p, q = load_and_validate(Path("sample/subs.json"), Path("sample/ques.json"))
df = create_dataframe(p, q)
df = filter_dataset(df, from_date=datetime(month=9, day=1, year=2026))
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

d = compute_summary(df)

# for key, val in d.items():
#     print(key, val)

e = markov(df)
print({"0": d, "1": submission_timing(df), "2": e, "3" : runtime_mem(df)})
