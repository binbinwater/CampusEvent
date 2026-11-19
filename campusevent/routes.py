from flask import (
    Blueprint,
    abort,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)

from .auth import current_user, login_required, role_required
from .db import get_db, transaction
from .events import EventPublisher, MessageNotificationObserver
from .forms import activity_form_data, validate_activity_form
from .repositories import (
    ActivityRepository,
    MessageRepository,
    NotificationFailureRepository,
    RegistrationRepository,
)
from .services import ActivityService, RegistrationService, ServiceError
from .utils import (
    current_datetime,
    format_datetime,
    format_timestamp,
    parse_start_at,
    policy_label,
    status_label,
)

bp = Blueprint("main", __name__)

STATUS_CLASS_MAP = {
    "pending": "status-pending",
    "approved": "status-approved",
    "rejected": "status-rejected",
    "cancelled": "status-cancelled",
}


def services():
    database = get_db()
    activities = ActivityRepository(database)
    registrations = RegistrationRepository(database)
    messages = MessageRepository(database)
    failures = NotificationFailureRepository(database)
    publisher = EventPublisher(
        [MessageNotificationObserver(messages)],
        failures,
    )
    return {
        "activities": activities,
        "registrations": registrations,
        "messages": messages,
        "activity_service": ActivityService(activities),
        "registration_service": RegistrationService(
            activities, registrations, publisher, current_datetime
        ),
    }


@bp.app_template_filter("status_label")
def filter_status_label(status):
    return status_label(status)


@bp.app_template_filter("status_class")
def filter_status_class(status):
    return STATUS_CLASS_MAP.get(status, "")


@bp.app_template_filter("policy_label")
def filter_policy_label(policy):
    return policy_label(policy)


@bp.app_template_filter("datetime_cn")
def filter_datetime_cn(value):
    return format_datetime(value)


@bp.app_template_filter("timestamp_cn")
def filter_timestamp_cn(value):
    return format_timestamp(value)


@bp.app_context_processor
def inject_unread_count():
    user = current_user()
    unread = 0
    if user and user["role"] == "student":
        unread = MessageRepository(get_db()).unread_count(user["student_id"])
    return {"unread_count": unread}


@bp.app_errorhandler(403)
def forbidden(_error):
    return (
        render_template(
            "error.html",
            code="403",
            title="没有访问权限",
            message="当前登录身份不能访问该页面。",
        ),
        403,
    )


@bp.app_errorhandler(404)
def not_found(_error):
    return (
        render_template(
            "error.html",
            code="404",
            title="页面不存在",
            message="活动或页面可能已被删除，或者地址输入有误。",
        ),
        404,
    )


def _get_activity_or_404(activity_id):
    activity = ActivityRepository(get_db()).get(activity_id)
    if activity is None:
        abort(404)
    return activity


def _safe_next(default):
    target = request.form.get("next") or request.args.get("next")
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return default


def _now_started(activity):
    return current_datetime() >= parse_start_at(activity.start_at)


@bp.route("/")
@login_required
def activities():
    query = (request.args.get("q") or "").strip()
    if len(query) > 100:
        query = query[:100]
    repo = ActivityRepository(get_db())
    activity_list = repo.list(query)
    registration_repo = RegistrationRepository(get_db())
    user = current_user()

    rows = []
    for activity in activity_list:
        my_registration = None
        if user["role"] == "student":
            my_registration = registration_repo.latest_for_student_activity(
                activity.id, user["student_id"]
            )
        rows.append(
            {
                "activity": activity,
                "my_registration": my_registration,
                "started": _now_started(activity),
            }
        )
    return render_template(
        "activities.html",
        rows=rows,
        query=query,
    )


@bp.route("/activities/<int:activity_id>")
@login_required
def activity_detail(activity_id):
    activity = _get_activity_or_404(activity_id)
    user = current_user()
    registration_repo = RegistrationRepository(get_db())
    my_registration = None
    registrations = []
    if user["role"] == "student":
        my_registration = registration_repo.latest_for_student_activity(
            activity_id, user["student_id"]
        )
    else:
        registrations = registration_repo.list_for_activity(activity_id)

    return render_template(
        "activity_detail.html",
        activity=activity,
        registrations=registrations,
        my_registration=my_registration,
        started=_now_started(activity),
    )


@bp.route("/activities/new", methods=("GET", "POST"))
@role_required("admin")
def activity_new():
    form_data = activity_form_data(None)
    errors = {}
    if request.method == "POST":
        form_data, errors = validate_activity_form(request.form)
        if not errors:
            activity_id = services()["activity_service"].create(form_data)
            flash("活动已创建。", "success")
            return redirect(url_for("main.activity_detail", activity_id=activity_id), 303)
    return (
        render_template(
            "activity_form.html",
            mode="create",
            activity=None,
            form=form_data,
            errors=errors,
        ),
        400 if errors else 200,
    )


@bp.route("/activities/<int:activity_id>/edit", methods=("GET", "POST"))
@role_required("admin")
def activity_edit(activity_id):
    activity = _get_activity_or_404(activity_id)
    form_data = activity_form_data(activity)
    errors = {}
    if request.method == "POST":
        form_data, errors = validate_activity_form(request.form)
        if not errors:
            try:
                services()["activity_service"].update(activity_id, form_data)
            except ServiceError as error:
                errors["capacity"] = str(error)
            else:
                flash("活动已更新。", "success")
                return redirect(
                    url_for("main.activity_detail", activity_id=activity_id), 303
                )
    return (
        render_template(
            "activity_form.html",
            mode="edit",
            activity=activity,
            form=form_data,
            errors=errors,
        ),
        400 if errors else 200,
    )


@bp.route("/activities/<int:activity_id>/delete", methods=("GET", "POST"))
@role_required("admin")
def activity_delete(activity_id):
    activity = _get_activity_or_404(activity_id)
    if request.method == "POST":
        try:
            services()["activity_service"].delete(activity_id)
        except ServiceError as error:
            flash(str(error), "error")
            return redirect(
                url_for("main.activity_detail", activity_id=activity_id), 303
            )
        flash("活动已删除。", "success")
        return redirect(url_for("main.activities"), 303)
    return render_template("delete_confirm.html", activity=activity)


@bp.post("/activities/<int:activity_id>/register")
@role_required("student")
def register(activity_id):
    activity = _get_activity_or_404(activity_id)
    user = current_user()
    try:
        status = services()["registration_service"].register(
            activity_id, user["student_id"]
        )
    except ServiceError as error:
        flash(str(error), "error")
    else:
        if status == "approved":
            flash("报名成功，已直接通过。", "success")
        else:
            flash("报名已提交，等待管理员审核。", "success")
    return redirect(
        _safe_next(url_for("main.activity_detail", activity_id=activity.id)), 303
    )


@bp.post("/registrations/<int:registration_id>/cancel")
@role_required("student")
def cancel(registration_id):
    user = current_user()
    try:
        services()["registration_service"].cancel(
            registration_id, user["student_id"]
        )
    except ServiceError as error:
        flash(str(error), "error")
    else:
        flash("报名已取消。", "success")
    return redirect(_safe_next(url_for("main.my_registrations")), 303)


@bp.post("/registrations/<int:registration_id>/approve")
@role_required("admin")
def approve(registration_id):
    try:
        services()["registration_service"].approve(registration_id)
    except ServiceError as error:
        flash(str(error), "error")
    else:
        flash("报名已批准，并已发送站内通知。", "success")
    return redirect(_safe_next(url_for("main.admin_dashboard")), 303)


@bp.post("/registrations/<int:registration_id>/reject")
@role_required("admin")
def reject(registration_id):
    try:
        services()["registration_service"].reject(registration_id)
    except ServiceError as error:
        flash(str(error), "error")
    else:
        flash("报名已拒绝，并已发送站内通知。", "success")
    return redirect(_safe_next(url_for("main.admin_dashboard")), 303)


@bp.route("/my/registrations")
@role_required("student")
def my_registrations():
    user = current_user()
    registrations = RegistrationRepository(get_db()).list_for_student(
        user["student_id"]
    )
    return render_template("my_registrations.html", registrations=registrations)


@bp.route("/messages")
@role_required("student")
def messages():
    user = current_user()
    service = services()
    message_list = service["messages"].list_for_student(user["student_id"])
    return render_template("messages.html", messages=message_list)


@bp.post("/messages/read")
@role_required("student")
def messages_read():
    user = current_user()
    with transaction():
        MessageRepository(get_db()).mark_all_read(user["student_id"])
    flash("站内消息已标记为已读。", "success")
    return redirect(url_for("main.messages"), 303)


@bp.route("/admin")
@role_required("admin")
def admin_dashboard():
    database = get_db()
    activity_repo = ActivityRepository(database)
    registration_repo = RegistrationRepository(database)
    activity_list = activity_repo.list()
    pending = registration_repo.list_pending()
    total_activities = len(activity_list)
    total_registrations = sum(a.registration_count for a in activity_list)
    approved_total = sum(a.approved_count for a in activity_list)
    return render_template(
        "admin_dashboard.html",
        activities=activity_list,
        pending=pending,
        total_activities=total_activities,
        total_registrations=total_registrations,
        approved_total=approved_total,
    )