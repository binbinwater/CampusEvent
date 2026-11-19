import sqlite3
from datetime import datetime

from .db import transaction
from .events import RegistrationEventFactory
from .policies import policy_for
from .utils import parse_start_at


class ServiceError(Exception):
    """A user-facing business rule violation."""


class ActivityService:
    def __init__(self, activities):
        self.activities = activities

    def create(self, data):
        with transaction():
            return self.activities.insert(data)

    def update(self, activity_id, data):
        with transaction():
            activity = self.activities.get(activity_id)
            if activity is None:
                raise ServiceError("活动不存在。")
            approved = self.activities.approved_count(activity_id)
            if data["capacity"] < approved:
                raise ServiceError(
                    f"人数上限不能低于当前已通过人数（{approved} 人）。"
                )
            self.activities.update(activity_id, data)

    def delete(self, activity_id):
        with transaction():
            activity = self.activities.get(activity_id)
            if activity is None:
                raise ServiceError("活动不存在。")
            if self.activities.registration_count(activity_id) > 0:
                raise ServiceError("该活动已有报名记录，不能删除；可保留活动并停止报名。")
            try:
                self.activities.delete(activity_id)
            except sqlite3.IntegrityError as error:
                raise ServiceError("该活动已有报名记录，不能删除。") from error


class RegistrationService:
    def __init__(self, activities, registrations, publisher, now_provider):
        self.activities = activities
        self.registrations = registrations
        self.publisher = publisher
        self.now = now_provider

    def register(self, activity_id, student_id):
        with transaction():
            activity = self.activities.get(activity_id)
            if activity is None:
                raise ServiceError("活动不存在。")
            if self.now() >= parse_start_at(activity.start_at):
                raise ServiceError("活动已经开始，不能报名。")
            if self.registrations.get_active(activity_id, student_id) is not None:
                raise ServiceError("你已经报名该活动，不能重复提交。")

            approved = self.activities.approved_count(activity_id)
            if approved >= activity.capacity:
                raise ServiceError("名额已满，无法报名。")

            policy = policy_for(activity.policy_type)
            status = policy.initial_status()
            try:
                registration_id = self.registrations.insert(
                    activity_id, student_id, status
                )
            except sqlite3.IntegrityError as error:
                raise ServiceError("你已经报名该活动，不能重复提交。") from error

        event = RegistrationEventFactory.for_status(
            status, student_id, activity, registration_id
        )
        self.publisher.publish(event)
        return status

    def cancel(self, registration_id, student_id):
        with transaction():
            registration = self.registrations.get(registration_id)
            if registration is None:
                raise ServiceError("报名记录不存在。")
            if registration.student_id != student_id:
                raise ServiceError("只能取消自己的报名。")
            if registration.status not in ("pending", "approved"):
                raise ServiceError("只有待审核或已通过的报名可以取消。")

            activity = self.activities.get(registration.activity_id)
            self.registrations.update_status(registration_id, "cancelled")

        event = RegistrationEventFactory.for_status(
            "cancelled", student_id, activity, registration_id
        )
        self.publisher.publish(event)

    def approve(self, registration_id):
        with transaction():
            registration = self.registrations.get(registration_id)
            if registration is None:
                raise ServiceError("报名记录不存在。")
            if registration.status != "pending":
                raise ServiceError("只有待审核报名可以批准。")

            activity = self.activities.get(registration.activity_id)
            approved = self.activities.approved_count(registration.activity_id)
            if approved >= activity.capacity:
                raise ServiceError("名额已满，无法批准该报名。")

            self.registrations.update_status(registration_id, "approved")

        event = RegistrationEventFactory.for_status(
            "approved",
            registration.student_id,
            activity,
            registration_id,
        )
        self.publisher.publish(event)

    def reject(self, registration_id):
        with transaction():
            registration = self.registrations.get(registration_id)
            if registration is None:
                raise ServiceError("报名记录不存在。")
            if registration.status != "pending":
                raise ServiceError("只有待审核报名可以拒绝。")

            activity = self.activities.get(registration.activity_id)
            self.registrations.update_status(registration_id, "rejected")

        event = RegistrationEventFactory.for_status(
            "rejected",
            registration.student_id,
            activity,
            registration_id,
        )
        self.publisher.publish(event)