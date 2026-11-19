from dataclasses import dataclass
from typing import Protocol

from flask import current_app

from .db import transaction
from .repositories import MessageRepository, NotificationFailureRepository


@dataclass(frozen=True)
class RegistrationEvent:
    event_type: str
    student_id: str
    activity_id: int
    registration_id: int
    activity_title: str


class EventSubscriber(Protocol):
    def handle(self, event: RegistrationEvent) -> None:
        ...


MESSAGE_TEMPLATES = {
    "registration_approved": "报名成功：《{title}》已通过。",
    "registration_pending": "报名已提交：《{title}》等待管理员审核。",
    "registration_rejected": "报名未通过：《{title}》。",
    "registration_cancelled": "报名已取消：《{title}》。",
}


class MessageNotificationObserver:
    """Observer that writes one in-site message per published registration event."""

    def __init__(self, message_repository):
        self.messages = message_repository

    def handle(self, event):
        template = MESSAGE_TEMPLATES.get(event.event_type)
        if template is None:
            raise ValueError(f"未定义的通知事件：{event.event_type}")
        content = template.format(title=event.activity_title)
        with transaction():
            self.messages.add(event.student_id, event.activity_id, content)


class EventPublisher:
    """Decouples registration transactions from notification writing.

    Registrations are committed before publish() is called. A subscriber error is
    logged to notification_failures and to the application log, but never rolls
    back the already-committed registration.
    """

    def __init__(self, subscribers, failure_repository):
        self.subscribers = list(subscribers)
        self.failures = failure_repository

    def publish(self, event):
        for subscriber in self.subscribers:
            try:
                subscriber.handle(event)
            except Exception as error:  # notifications must not break registration
                current_app.logger.exception(
                    "通知发送失败 event=%s registration=%s",
                    event.event_type,
                    event.registration_id,
                )
                try:
                    with transaction():
                        self.failures.record(event, error)
                except Exception:
                    current_app.logger.exception("通知失败记录写入失败")
        return [event]


class RegistrationEventFactory:
    @staticmethod
    def for_status(status, student_id, activity, registration_id):
        if status == "approved":
            event_type = "registration_approved"
        elif status == "pending":
            event_type = "registration_pending"
        elif status == "rejected":
            event_type = "registration_rejected"
        elif status == "cancelled":
            event_type = "registration_cancelled"
        else:
            raise ValueError(f"未知报名状态：{status}")
        return RegistrationEvent(
            event_type=event_type,
            student_id=student_id,
            activity_id=activity.id,
            registration_id=registration_id,
            activity_title=activity.title,
        )