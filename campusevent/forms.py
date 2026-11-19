from datetime import datetime

MAX_TITLE = 100
MAX_CATEGORY = 40
MAX_LOCATION = 100
MAX_CAPACITY = 10000
VALID_POLICIES = ("direct", "review")


def validate_activity_form(form):
    title = (form.get("title") or "").strip()
    category = (form.get("category") or "").strip()
    start_at_raw = (form.get("start_at") or "").strip()
    location = (form.get("location") or "").strip()
    capacity_raw = (form.get("capacity") or "").strip()
    policy_type = (form.get("policy_type") or "").strip()

    data = {
        "title": title,
        "category": category,
        "start_at": start_at_raw,
        "location": location,
        "capacity": capacity_raw,
        "policy_type": policy_type,
    }
    errors = {}

    if not title:
        errors["title"] = "活动名称不能为空。"
    elif len(title) > MAX_TITLE:
        errors["title"] = f"活动名称不能超过 {MAX_TITLE} 个字符。"

    if not category:
        errors["category"] = "活动类型不能为空。"
    elif len(category) > MAX_CATEGORY:
        errors["category"] = f"活动类型不能超过 {MAX_CATEGORY} 个字符。"

    if not location:
        errors["location"] = "活动地点不能为空。"
    elif len(location) > MAX_LOCATION:
        errors["location"] = f"活动地点不能超过 {MAX_LOCATION} 个字符。"

    if not start_at_raw:
        errors["start_at"] = "活动开始时间不能为空。"
    else:
        try:
            start_at = datetime.strptime(start_at_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            errors["start_at"] = "活动开始时间格式不正确。"
        else:
            data["start_at"] = start_at.strftime("%Y-%m-%dT%H:%M")

    capacity = None
    if not capacity_raw:
        errors["capacity"] = "人数上限不能为空。"
    else:
        try:
            capacity = int(capacity_raw)
        except ValueError:
            errors["capacity"] = "人数上限必须是整数。"
        else:
            if capacity <= 0:
                errors["capacity"] = "人数上限必须大于 0。"
            elif capacity > MAX_CAPACITY:
                errors["capacity"] = f"人数上限不能超过 {MAX_CAPACITY}。"
            else:
                data["capacity"] = capacity

    if policy_type not in VALID_POLICIES:
        errors["policy_type"] = "报名方式必须是“直接报名”或“管理员审核”。"

    return data, errors


def activity_form_data(activity):
    if activity is None:
        return {
            "title": "",
            "category": "",
            "start_at": "",
            "location": "",
            "capacity": "",
            "policy_type": "direct",
        }
    return {
        "title": activity.title,
        "category": activity.category,
        "start_at": activity.start_at,
        "location": activity.location,
        "capacity": activity.capacity,
        "policy_type": activity.policy_type,
    }