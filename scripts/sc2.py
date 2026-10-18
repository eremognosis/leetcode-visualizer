import time
import json
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
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"  # pretend
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

QUERY = """
query problemsetQuestionListV2(
  $filters: QuestionFilterInput
  $limit: Int
  $searchKeyword: String
  $skip: Int
  $sortBy: QuestionSortByInput
  $categorySlug: String
) {
  problemsetQuestionListV2(
    filters: $filters
    limit: $limit
    searchKeyword: $searchKeyword
    skip: $skip
    sortBy: $sortBy
    categorySlug: $categorySlug
  ) {
    totalLength
    finishedLength
    hasMore
    questions {
      id
      titleSlug
      title
      translatedTitle
      questionFrontendId
      paidOnly
      difficulty
      status
      isInMyFavorites
      frequency
      acRate
      contestPoint
      topicTags {
        name
        slug
        nameTranslated
      }
    }
  }
}

"""


all = []

offset = 0
limit = 100
filter_structure = {
    "filterCombineType": "ALL",
    "statusFilter": {"questionStatuses": [], "operator": "IS"},
    "difficultyFilter": {"difficulties": [], "operator": "IS"},
    "languageFilter": {"languageSlugs": [], "operator": "IS"},
    "topicFilter": {"topicSlugs": [], "operator": "IS"},
    "acceptanceFilter": {},
    "frequencyFilter": {},
    "frontendIdFilter": {},
    "lastSubmittedFilter": {},
    "publishedFilter": {},
    "companyFilter": {"companySlugs": [], "operator": "IS"},
    "positionFilter": {"positionSlugs": [], "operator": "IS"},
    "positionLevelFilter": {"positionLevelSlugs": [], "operator": "IS"},
    "contestPointFilter": {"contestPoints": [], "operator": "IS"},
    "premiumFilter": {"premiumStatus": [], "operator": "IS"},
}
has_more = True
skip = 0
while has_more:
    payload = {
        "query": QUERY,
        "variables": {
            "categorySlug": "all-code-essentials",
            "skip": skip,
            "limit": 100,
            "filters": filter_structure,
            "filtersV2": filter_structure,
            "sortBy": {"sortField": "CUSTOM", "sortOrder": "ASCENDING"},
        },
    }
    try:
        response = requests.post(URL, json=payload, headers=HEADERS, cookies=COOKIES)
        if response.status_code != 200:
            print(response.text)
            break

        res_data = response.json()
        sd = res_data["data"]["problemsetQuestionListV2"]
        questions = sd.get("questions", [])
        all.extend(questions)
        has_more = sd.get("hasMore", False)
        total = sd.get("totalLength", 0)
        skip += limit
        print(len(all), end="\r")
        time.sleep(0.44)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(e)
        break

with open("../sample/ques.json", "w") as f:
    json.dump(all, f, indent=4)

print(len(all))
