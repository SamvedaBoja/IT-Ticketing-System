from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TicketStatus(str, Enum):
    new = "new"
    triaged = "triaged"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class TicketPriority(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class TicketBase(SQLModel):
    subject: str
    description: Optional[str] = None

class Ticket(TicketBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reporter_id: int 
    assignee_id: Optional[int] = None
    status: TicketStatus = TicketStatus.new
    priority: Optional[TicketPriority] = None
    assigned_team: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

class TicketCreate(TicketBase):
    pass

class TicketRead(TicketBase):
    id: int
    reporter_id: int
    status: TicketStatus
    priority: Optional[TicketPriority]
    assigned_team: Optional[str]
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime

class TicketTriageUpdate(SQLModel):
    priority: TicketPriority
    assigned_team: str
    assignee_id: Optional[int] = None

class TicketAssignUpdate(SQLModel):
    assignee_id: int

class TicketResolveUpdate(SQLModel):
    resolution_notes: str