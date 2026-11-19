import hmac
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

bp = Blueprint("auth", __name__)

# Fixed demonstration accounts; there is deliberately no registration system.
DEMO_ACCOUNTS = {
    "student_a": {
        "password": "student123",
        "role": "student",
        "student_id": "S001",
        "display_name": "张同学",
    },
    "student_b": {
        "password": "student123",
        "role": "student",
        "student_id": "S002",
        "display_name": "李同学",
    },
    "student_c": {
        "password": "student123",
        "role": "student",
        "student_id": "S003",
        "display_name": "王同学",
    },
    "admin": {
        "password": "admin123",
        "role": "admin",
        "student_id": None,
        "display_name": "管理员",
    },
}

DEMO_LOGIN_HINTS = [
    ("student_a", "student123", "学生 A（张同学 / S001）"),
    ("student_b", "student123", "学生 B（李同学 / S002）"),
    ("student_c", "student123", "学生 C（王同学 / S003）"),
    ("admin", "admin123", "管理员"),
]


def current_user():
    if "username" not in session:
        return None
    return {
        "username": session["username"],
        "role": session["role"],
        "student_id": session.get("student_id"),
        "display_name": session["display_name"],
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect(url_for("auth.login"))
            if user["role"] != role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


@bp.route("/login", methods=("GET", "POST"))
def login():
    if current_user() is not None:
        return redirect(url_for("main.activities"))

    error = None
    username = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        account = DEMO_ACCOUNTS.get(username)
        if account is None or not hmac.compare_digest(account["password"], password):
            error = "用户名或密码错误。"
        else:
            session.clear()
            session["username"] = username
            session["role"] = account["role"]
            session["student_id"] = account["student_id"]
            session["display_name"] = account["display_name"]
            flash("登录成功。", "success")
            return redirect(url_for("main.activities"))

    return render_template("login.html", error=error, username=username, hints=DEMO_LOGIN_HINTS)


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("已退出登录。", "success")
    return redirect(url_for("auth.login"))


@bp.app_context_processor
def inject_user():
    user = current_user()
    return {"current_user": user, "is_admin": bool(user and user["role"] == "admin")}