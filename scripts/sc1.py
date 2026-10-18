import json
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

LEETCODE_SESSION = os.environ.get("LEETCODE_SESSION")
CSRF_TOKEN = os.environ.get("CSRF_TOKEN")

URL = "https://leetcode.com/graphql/"
COOKIES = {
    "LEETCODE_SESSION": LEETCODE_SESSION,
    "csrftoken": CSRF_TOKEN,
}
HEADERS = {
    "Content-Type": "application/json",
    "x-csrftoken": CSRF_TOKEN,
    "Referer": "https://leetcode.com/submissions/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

QUERY = """
query submissionList($offset: Int!, $limit: Int!) {
  submissionList(offset: $offset, limit: $limit) {
    hasNext
    submissions {
      id
      title
      titleSlug
      statusDisplay
      lang
      runtime
      timestamp
      memory
    }
  }
}
"""

all_submissions = []
offset = 0
limit = 20

print("Starting submission dump...")

while True:
    payload = {
        "query": QUERY,
        "variables": {"offset": offset, "limit": limit},
        "operationName": "submissionList",
    }

    try:
        response = requests.post(URL, json=payload, headers=HEADERS, cookies=COOKIES)
        if response.status_code != 200:
            print(response.text)
            break

        res_data = response.json()
        sub_data = res_data.get("data", {}).get("submissionList")

        if not sub_data:
            print(res_data)
            break

        subs = sub_data.get("submissions", [])
        if not subs:
            break

        all_submissions.extend(subs)

        if not sub_data.get("hasNext", False):
            break

        offset += limit
        time.sleep(0.35)

    except Exception as e:
        break

output_file = "../sample/subs.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_submissions, f, indent=4, ensure_ascii=False)
