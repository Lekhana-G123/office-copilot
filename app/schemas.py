from pydantic import BaseModel


class MeetingRequestCreate(BaseModel):
    target_person_name: str
    reason: str
    date: str
    start_hour: int = 14
    end_hour: int = 15


class DraftEmailRequest(BaseModel):
    target_person_name: str
    reason: str
    date: str
    start_hour: int = 14
    end_hour: int = 15


class ChatRequest(BaseModel):
    message: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: str


class TaskAssignRequest(BaseModel):
    assignee_email: str
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str  # YYYY-MM-DD


class LeaveCreateRequest(BaseModel):
    user_email: str
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    leave_type: str = "leave"
    reason: str = ""


class LeaveApprovalRequest(BaseModel):
    leave_id: int
    action: str  # approve | decline
