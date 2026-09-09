from typing import List, Optional
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    task: str
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = "Medium"
    status: Optional[str] = "Pending"


class Participant(BaseModel):
    name: str
    role: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class MeetingIntelligence(BaseModel):
    summary: str

    key_points: List[str] = Field(
        default_factory=list
    )

    decisions: List[str] = Field(
        default_factory=list
    )

    action_items: List[ActionItem] = Field(
        default_factory=list
    )

    participants: List[Participant] = Field(
        default_factory=list
    )

    deadlines: List[str] = Field(
        default_factory=list
    )

    priorities: List[str] = Field(
        default_factory=list
    )