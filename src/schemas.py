from datetime import datetime
import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TopicTag(BaseModel):
    name: str
    slug: str


class QuestionNode(BaseModel):
    id: int
    questionFrontendId: str
    title: str
    titleSlug: str
    difficulty: str
    paidOnly: bool
    status: Optional[str] = None
    acRate: float
    topicTags: List[TopicTag] = Field(default_factory=list)

    @property
    def tag_slugs(self) -> List[str]:
        return [tag.slug for tag in self.topicTags]


class SubmissionRecord(BaseModel):
    id: str
    title: str
    titleSlug: str
    statusDisplay: str
    lang: str
    runtime_str: str = Field(alias="runtime")
    memory_str: str = Field(alias="memory")
    timestamp_raw: str = Field(alias="timestamp")

    runtime_ms: Optional[float] = None
    memory_mb: Optional[float] = None
    timestamp: Optional[datetime] = None

    @model_validator(mode="after")
    def parse_derived_fields(self) -> "SubmissionRecord":
        if self.runtime_str and self.runtime_str != "N/A":
            match = re.search(r"(\d+)", self.runtime_str)
            if match:
                self.runtime_ms = float(match.group(1))
        if self.memory_str and self.memory_str != "N/A":
            match = re.search(r"([\d\.]+)", self.memory_str)
            if match:
                self.memory_mb = float(match.group(1))
        if self.timestamp_raw and self.timestamp_raw.isdigit():
            self.timestamp = datetime.fromtimestamp(int(self.timestamp_raw))

        return self
