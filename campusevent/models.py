from dataclasses import dataclass, field


@dataclass
class Activity:
    id: int
    title: str
    category: str
    start_at: str
    location: str
    capacity: int
    policy_type: str
    created_at: str
    updated_at: str
    approved_count: int = 0
    pending_count: int = 0
    registration_count: int = 0

    @property
    def remaining(self):
        return max(self.capacity - self.approved_count, 0)

    @property
    def is_full(self):
        return self.remaining == 0

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        return cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            start_at=data["start_at"],
            location=data["location"],
            capacity=data["capacity"],
            policy_type=data["policy_type"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            approved_count=data.get("approved_count", 0) or 0,
            pending_count=data.get("pending_count", 0) or 0,
            registration_count=data.get("registration_count", 0) or 0,
        )


@dataclass
class Registration:
    id: int
    activity_id: int
    student_id: str
    status: str
    created_at: str
    updated_at: str
    activity_title: str = ""
    activity_start_at: str = ""
    activity_location: str = ""
    activity_policy_type: str = ""
    student_name: str = ""

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        return cls(
            id=data["id"],
            activity_id=data["activity_id"],
            student_id=data["student_id"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            activity_title=data.get("activity_title", "") or "",
            activity_start_at=data.get("activity_start_at", "") or "",
            activity_location=data.get("activity_location", "") or "",
            activity_policy_type=data.get("activity_policy_type", "") or "",
            student_name=data.get("student_name", "") or "",
        )


@dataclass
class Message:
    id: int
    student_id: str
    activity_id: int | None
    content: str
    created_at: str
    is_read: int
    activity_title: str = ""

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        return cls(
            id=data["id"],
            student_id=data["student_id"],
            activity_id=data.get("activity_id"),
            content=data["content"],
            created_at=data["created_at"],
            is_read=data["is_read"],
            activity_title=data.get("activity_title", "") or "",
        )


@dataclass
class Student:
    student_id: str
    name: str

    @classmethod
    def from_row(cls, row):
        return cls(student_id=row["student_id"], name=row["name"])