from datetime import datetime

from flask import current_app

STATUS_LABELS = {
    "pending": "待审核",
    "approved": "已通过",
    "rejected": "已拒绝",
    "cancelled": "已取消",
}
STATUS_CLASSES = {
    "pending": "status-pending",
    "approved": "status-approved",
    "rejected": "status-rejected",
    "cancelled": "status-cancelled",
}
POLICY_LABELS = {
    "direct": "直接报名",
    "review": "管理员审核",
}
POLICY_DESCRIPTIONS = {
    "direct": "报名后立即通过，仍会检查名额和活动开始时间。",
    "review": "报名后进入待审核，管理员批准时才占用名额。",
}


def current_datetime():
    """Return the injected test clock or the server's local wall clock."""
    override = current_app.config.get("NOW_OVERRIDE")
    if override is None:
        return datetime.now()
    if isinstance(override, datetime):
        return override
    return datetime.fromisoformat(str(override))


def parse_start_at(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


def format_datetime(value):
    if not value:
        return "—"
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value.replace("T", " ")


def format_timestamp(value):
    if not value:
        return "—"
    return value.replace("T", " ")


def status_label(status):
    return STATUS_LABELS.get(status, status)


def policy_label(policy):
    return POLICY_LABELS.get(policy, policy)


def is_started(start_at):
    return current_datetime() >= parse_start_at(start_at)